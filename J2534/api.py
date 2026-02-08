"""
J2534 High-Level API Module
===========================

This module provides the high-level Python API for J2534 operations.
It wraps the low-level DLL interface with convenient Python functions
that handle error checking, type conversion, and optional exception raising.

The module provides:
    - J2534Api: Main API class managing device and library state
    - PassThruMsgBuilder: Helper class for building J2534 messages
    - pt_* functions: Pythonic wrappers for all J2534 operations

Error Handling:
    Error handling behavior is controlled by j2534_config:

    - When j2534_config.raise_exceptions is False (default):
      Functions return False or None on error, allowing simple checks.

    - When j2534_config.raise_exceptions is True:
      Functions raise specific J2534Exception subclasses on error.

Architecture:
    ::

        Application Code
             |
        api.py (this module) <-- High-level Python API
             |
        dll_interface.py (ctypes DLL binding)
             |
        J2534 DLL (hardware vendor)

Example:
    Basic usage with return value error checking::

        from J2534 import (
            get_list_j2534_devices,
            set_j2534_device_to_connect,
            pt_open, pt_close, pt_connect, pt_disconnect,
            pt_read_message, pt_write_message,
            ProtocolId, BaudRate
        )

        # List available devices
        devices = get_list_j2534_devices()
        print(f"Found {len(devices)} device(s)")

        # Select first device
        set_j2534_device_to_connect(0)

        # Open device
        device_id = pt_open()
        if device_id is False:
            print("Failed to open device")
            exit(1)

        # Connect channel
        channel_id = pt_connect(
            device_id,
            ProtocolId.ISO15765,
            0,
            BaudRate.CAN_500K
        )

        # Clean up
        pt_disconnect(channel_id)
        pt_close(device_id)

Example:
    Usage with exception handling::

        from J2534 import pt_open, pt_connect
        from J2534.config import j2534_config
        from J2534.exceptions import J2534OpenError, J2534ConnectError

        # Enable exception mode
        j2534_config.enable_exceptions()

        try:
            device_id = pt_open()
            channel_id = pt_connect(device_id, 6, 0, 500000)
        except J2534OpenError as e:
            print(f"Device open failed: {e}")
        except J2534ConnectError as e:
            print(f"Channel connect failed: {e}")

Author: J2534-API Contributors
License: MIT
Version: 2.0.0
"""

import ctypes
from typing import Any, Optional, Union, List, Tuple

from .structures import (
    PassThruMessageStructure,
    SetConfigurationList,
    SetConfigurationParameter,
    PassThruDataBuffer,
    PASSTHRU_MESSAGE_DATA_SIZE
)
from .constants import (
    ProtocolId,
    IoctlId,
    FilterType,
    ErrorCode,
    ConfigParameter
)
from .dll_interface import PassThruLibrary, load_j2534_library
from .config import j2534_config
from .logging_utils import (
    debug_log,
    debug_log_function_entry,
    debug_log_function_exit,
    debug_log_message,
    format_error_code
)
from .exceptions import (
    J2534Error,
    J2534OpenError,
    J2534CloseError,
    J2534ConnectError,
    J2534DisconnectError,
    J2534ReadError,
    J2534WriteError,
    J2534FilterError,
    J2534IoctlError,
    J2534PeriodicMessageError,
    J2534DeviceNotSelectedError
)


# =============================================================================
# Message Builder Classes
# =============================================================================

class MsgBuilder(PassThruMessageStructure):
    """
    Base class for building J2534 messages.

    This class extends PassThruMessageStructure with convenience methods
    for constructing messages. It handles common patterns like setting
    CAN identifiers and building data blocks.

    Example:
        # >>> builder = MsgBuilder()
        # >>> builder.build_transmit_data_block([0x7E, 0x00, 0x22, 0xF1, 0x90])
        # >>> print(builder.data_size)
        # 5
    """

    def build_transmit_data_block(
        self,
        data: Union[bytes, bytearray, List[int]]
    ) -> None:
        """
        Build the transmit data block from raw data.

        This method copies the data into the message buffer and sets
        the DataSize field appropriately.

        Args:
            data: The data bytes to include in the message.

        Example:
            # >>> builder.build_transmit_data_block([0x22, 0xF1, 0x90]) UDS EXAMPLE
            # >>> builder.build_transmit_data_block([0x1A, 0x90]) KWP 2000 EXAMPLE
        """
        self.DataSize = len(data)
        self.Data = PassThruDataBuffer()
        for index in range(self.DataSize):
            self.Data[index] = data[index]

    def set_identifier(self, transmit_identifier: int) -> None:
        """
        Set the CAN identifier for the message.

        Converts the identifier to bytes and sets it as the message data.
        For CAN, the identifier is placed in the first bytes of the data.

        Args:
            transmit_identifier: The CAN identifier (11-bit or 29-bit).

        Example:
            # >>> builder.set_identifier(0x7E0)  # Standard OBD-II request ID
        """
        identifier_bytes = self._integer_to_byte_list(transmit_identifier)
        self.build_transmit_data_block(identifier_bytes)

    def set_identifier_and_data(
        self,
        identifier: int,
        data: Optional[List[int]] = None
    ) -> None:
        """
        Set both the CAN identifier and payload data.

        This combines the identifier bytes with the payload data into
        a single message. This is the common pattern for ISO 15765
        messages where the ID precedes the payload.

        Args:
            identifier: The CAN identifier.
            data: Optional payload data bytes.

        Example:
            # >>> builder.set_identifier_and_data(0x7E0, [0x22, 0xF1, 0x90])
        """
        if data is None:
            data = []
        identifier_bytes = self._integer_to_byte_list(identifier)
        combined_data = identifier_bytes + data
        self.build_transmit_data_block(combined_data)

    @staticmethod
    def _integer_to_byte_list(value: int) -> List[int]:
        """
        Convert an integer to a list of bytes (big-endian).

        For values less than 256, returns a single byte.
        For larger values, returns 4 bytes (big-endian).

        Args:
            value: The integer value to convert.

        Returns:
            List[int]: The bytes representing the value.

        Example:
            # >>> MsgBuilder._integer_to_byte_list(0x7E0)
            # [0, 0, 7, 224]
        """
        if value < 256:
            return [value]
        return [
            (value >> 24) & 0xFF,
            (value >> 16) & 0xFF,
            (value >> 8) & 0xFF,
            value & 0xFF
        ]

    # Alias for backward compatibility
    int_to_list = _integer_to_byte_list


class PassThruMsgBuilder(MsgBuilder):
    """
    Message builder with protocol and flag initialization.

    This class extends MsgBuilder to initialize the ProtocolID and
    TxFlags fields during construction, which is required for most
    J2534 message operations.

    Attributes:
        ProtocolID: The protocol identifier for this message.
        TxFlags: The transmit flags for this message.

    Example:
        # >>> from J2534.constants import ProtocolId, TxFlags
        # >>> msg = PassThruMsgBuilder(ProtocolId.ISO15765, TxFlags.ISO15765_FRAME_PAD)
        # >>> msg.set_identifier_and_data(0x7E0, [0x22, 0xF1, 0x90])
    """

    def __init__(
        self,
        protocol_id: int,
        transmit_flags: int,
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Initialize the message builder.

        Args:
            protocol_id: The protocol identifier (see ProtocolId enum).
            transmit_flags: The transmit flags (see TxFlags enum).
            *args: Additional positional arguments passed to base class.
            **kwargs: Additional keyword arguments passed to base class.
        """
        super().__init__(*args, **kwargs)
        self.ProtocolID = protocol_id
        self.TxFlags = transmit_flags

    def dump(self) -> None:
        """
        Print a human-readable dump of the message to stdout.

        This method outputs all message fields and a hex dump of the
        data buffer for debugging purposes.
        """
        print(f"ProtocolID = {self.ProtocolID}")
        print(f"RxStatus = {self.RxStatus}")
        print(f"TxFlags = {self.TxFlags}")
        print(f"Timestamp = {self.Timestamp}")
        print(f"DataSize = {self.DataSize}")
        print(f"ExtraDataIndex = {self.ExtraDataIndex}")
        print(self.build_hex_output())

    def _format_hex_output_line(
        self,
        line_start_index: int,
        line_end_index: int
    ) -> str:
        """
        Format a single line of hex dump output.

        Args:
            line_start_index: Starting byte index for this line.
            line_end_index: Ending byte index for this line.

        Returns:
            str: Formatted hex dump line.
        """
        # Offset prefix
        line = f"{line_start_index:04x} | "

        # Hex values
        for byte_index in range(line_start_index, line_end_index):
            if byte_index >= self.DataSize:
                break
            line += f"{abs(self.Data[byte_index]):02X} "

        # Pad to align ASCII column
        line += " " * (3 * 16 + 7 - len(line)) + " | "

        # ASCII representation
        for byte_index in range(line_start_index, line_end_index):
            if byte_index >= self.DataSize:
                break
            byte_value = self.Data[byte_index]
            if 0x20 <= byte_value <= 0x7E:
                line += chr(byte_value)
            else:
                line += "."

        return line

    # Alias for backward compatibility
    process_hex_output_line = _format_hex_output_line

    def build_hex_output(self) -> str:
        """
            # Build a complete hex dump of the message data.
            #
            # Returns:
            #     str: Multi-line hex dump string.
            #
            # Example:
            #     >>> print(msg.build_hex_output())
            #     0000 | 7E 00 22 F1 90 | ~."..
        """
        lines = []
        for offset in range(0, self.DataSize, 16):
            line_end = offset + 16
            line = self._format_hex_output_line(offset, line_end)
            lines.append(line)
        return "\n".join(lines)

    def dump_output(self) -> str:
        """
            # Get the message data as a hex string without formatting.
            #
            # Returns:
            #     str: Hex string of all data bytes.
            #
            # Example:
            #     >>> print(msg.dump_output())
            #     7E0022F190
        """
        return "".join(
            f"{self.Data[index]:02X}"
            for index in range(self.DataSize)
        )


class PassThruMsg(PassThruMsgBuilder):
    """
    Alias for PassThruMsgBuilder for backward compatibility.

    This class exists for code that uses the PassThruMsg name from
    older versions of this library.
    """
    pass


# =============================================================================
# Main API Class
# =============================================================================

class J2534Api:
    """
    Main J2534 API class managing device state and DLL access.

    This class provides the central interface for J2534 operations.
    It manages the device selection, DLL loading, and provides access
    to the underlying PassThru functions.

    The class maintains state about:
    - Available J2534 devices (from registry)
    - Currently selected device
    - Loaded DLL and library wrapper

    Attributes:
        pass_thru_library: The PassThruLibrary wrapper for the loaded DLL.
        dll: The raw ctypes DLL object.
        name: The name of the currently selected device.

    Example:
        # >>> api = J2534Api()
        # >>> devices = api.get_devices()
        # >>> print(f"Found {len(devices)} device(s)")
        # >>> api.set_device(0)  # Select first device
    """

    def __init__(self) -> None:
        """
        Initialize the J2534 API.

        Scans the Windows registry for installed J2534 devices and
        stores the device list. The DLL is not loaded until a device
        is selected with set_device().
        """
        self.pass_thru_library: Optional[PassThruLibrary] = None
        self.dll: Optional[ctypes.WinDLL] = None
        self.name: Optional[str] = None

        # Scan registry for devices using the J2534_REGISTRY package
        try:
            from J2534_REGISTRY import get_all_j2534_devices
            device_info_list = get_all_j2534_devices()
            # Convert J2534DeviceInfo objects to [name, dll_path] format for compatibility
            self._devices = [
                [device.name, device.function_library_path]
                for device in device_info_list
            ]
        except Exception as error:
            debug_log(
                f"Failed to enumerate J2534 devices: {error}",
                function_name="J2534Api.__init__",
                level="warning"
            )
            self._devices = []

    def set_device(self, device_index: int = 0) -> None:
        """
        Select a J2534 device by index and load its DLL.

        This method selects a device from the list of available devices
        and loads its DLL for communication.

        Args:
            device_index: Index of the device in the device list.
                Default is 0 (first device).

        Raises:
            IndexError: If device_index is out of range.
            J2534DeviceNotSelectedError: If DLL loading fails (when
                exceptions are enabled).

        Example:
            # >>> api = J2534Api()
            # >>> api.set_device(0)  # Select first device
            # >>> print(f"Selected: {api.name}")
        """
        if device_index >= len(self._devices):
            if j2534_config.raise_exceptions:
                raise IndexError(
                    f"Device index {device_index} out of range "
                    f"(found {len(self._devices)} devices)"
                )
            return

        device = self._devices[device_index]
        self.name = device[0]
        dll_path = device[1]

        debug_log(
            f"Selecting device '{self.name}' with DLL: {dll_path}",
            function_name="J2534Api.set_device"
        )

        self.dll = load_j2534_library(dll_path)
        if self.dll is not None:
            self.pass_thru_library = PassThruLibrary(self.dll)
            debug_log(
                f"Device '{self.name}' selected successfully",
                function_name="J2534Api.set_device"
            )
        else:
            debug_log(
                f"Failed to load DLL for device '{self.name}'",
                function_name="J2534Api.set_device",
                level="error"
            )

    def get_devices(self) -> List[List[str]]:
        """
        Get the list of available J2534 devices.

        Returns:
            List[List[str]]: A list of [name, dll_path] pairs for each
                available device.

        Example:
            # >>> devices = api.get_devices()
            # >>> for name, path in devices:
            # ...     print(f"{name}: {path}")
        """
        return self._devices

    def __getattr__(self, name: str) -> Any:
        """
        Delegate attribute access to the PassThru library.

        This allows calling PassThru functions directly on the API
        instance (e.g., api.PassThruOpen(...)).

        Args:
            name: The attribute name.

        Returns:
            The attribute from pass_thru_library.

        Raises:
            AttributeError: If the attribute doesn't exist.
        """
        try:
            return getattr(self.pass_thru_library, name)
        except AttributeError as error:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            ) from error


# =============================================================================
# Global API Instance
# =============================================================================

# Create a global API instance for convenience
j2534_api: J2534Api = J2534Api()
"""
Global J2534 API instance.

This singleton instance is used by the module-level pt_* functions.
It provides a convenient way to use J2534 without managing instances.

Example:
    >>> from J2534.api import j2534_api
    >>> j2534_api.set_device(0)
    >>> # Now use pt_* functions
"""


# =============================================================================
# Device Management Functions
# =============================================================================

def pt_open() -> Union[int, bool]:
    """
        # Open a connection to the selected J2534 device.
        #
        # Opens the currently selected device and returns a device ID that
        # must be used for subsequent operations.
        #
        # Returns:
        #     int: The device ID if successful.
        #     False: If the operation failed (when exceptions are disabled).
        #
        # Raises:
        #     J2534OpenError: If the operation failed (when exceptions are enabled).
        #     J2534DeviceNotSelectedError: If no device has been selected.
        #
        # Example:
        # >>> set_j2534_device_to_connect(0)
        # >>> device_id = pt_open()
        # >>> if device_id is not False:
        # ...     print(f"Device opened with ID: {device_id}")
    """
    debug_log_function_entry("pt_open")

    if j2534_api.pass_thru_library is None:
        error_message = "No device selected - call set_j2534_device_to_connect() first"
        debug_log(error_message, function_name="pt_open", level="error")
        if j2534_config.raise_exceptions:
            raise J2534DeviceNotSelectedError(error_message)
        return False

    device_id = ctypes.c_ulong()
    result = j2534_api.PassThruOpen(
        ctypes.c_void_p(None),
        ctypes.byref(device_id)
    )

    if result != 0:
        error_description = pt_get_last_error()
        debug_log_function_exit(
            "pt_open",
            return_value=False,
            success=False,
            error_code=result
        )
        if j2534_config.raise_exceptions:
            raise J2534OpenError(
                f"PassThruOpen failed: {error_description}",
                error_code=result
            )
        return False

    debug_log_function_exit("pt_open", return_value=device_id.value, success=True)
    return device_id.value


def pt_close(device_id: int) -> int:
    """
    Close a connection to a J2534 device.

    Closes the device connection and releases all associated resources.
    All channels on the device should be disconnected first.

    Args:
        device_id: The device ID from pt_open().

    Returns:
        int: The J2534 error code (0 = success).

    Raises:
        J2534CloseError: If the operation failed (when exceptions are enabled).

    Example:
        # >>> result = pt_close(device_id)
        # >>> if result == 0:
        # ...     print("Device closed successfully")
    """
    debug_log_function_entry("pt_close", device_id=device_id)

    result = j2534_api.PassThruClose(device_id)

    if result != 0 and j2534_config.raise_exceptions:
        raise J2534CloseError(
            f"PassThruClose failed",
            error_code=result
        )

    debug_log_function_exit("pt_close", return_value=result, success=(result == 0))
    return result


# =============================================================================
# Channel Management Functions
# =============================================================================

def pt_connect(
    device_id: int,
    protocol_id: int,
    flags: int,
    baud_rate: int
) -> Union[int, bool]:
    """
    Establish a protocol channel on a J2534 device.

    Creates a communication channel using the specified protocol,
    flags, and baud rate. The channel ID returned is used for all
    subsequent message operations.

    Args:
        device_id: The device ID from pt_open().
        protocol_id: The protocol to use (see ProtocolId enum).
        flags: Connection flags (see ConnectFlags enum).
        baud_rate: The baud rate for the protocol.

    Returns:
        int: The channel ID if successful.
        False: If the operation failed (when exceptions are disabled).

    Raises:
        J2534ConnectError: If the operation failed (when exceptions are enabled).

    Example:
        # >>> channel_id = pt_connect(
        # ...     device_id,
        # ...     ProtocolId.ISO15765,
        # ...     0,
        # ...     BaudRate.CAN_500K
        # ... )
    """
    debug_log_function_entry(
        "pt_connect",
        device_id=device_id,
        protocol_id=protocol_id,
        flags=flags,
        baud_rate=baud_rate
    )

    channel_id = ctypes.c_ulong()
    result = j2534_api.PassThruConnect(
        device_id,
        protocol_id,
        flags,
        baud_rate,
        ctypes.byref(channel_id)
    )

    if result != 0:
        debug_log_function_exit(
            "pt_connect",
            return_value=False,
            success=False,
            error_code=result
        )
        if j2534_config.raise_exceptions:
            raise J2534ConnectError(
                f"PassThruConnect failed",
                error_code=result,
                protocol_id=protocol_id,
                baud_rate=baud_rate
            )
        return False

    debug_log_function_exit("pt_connect", return_value=channel_id.value, success=True)
    return channel_id.value


def pt_disconnect(channel_id: int) -> int:
    """
    Disconnect a protocol channel.

    Closes the specified channel and releases its resources.

    Args:
        channel_id: The channel ID from pt_connect().

    Returns:
        int: The J2534 error code (0 = success).

    Raises:
        J2534DisconnectError: If the operation failed (when exceptions are enabled).

    Example:
        # >>> result = pt_disconnect(channel_id)
    """
    debug_log_function_entry("pt_disconnect", channel_id=channel_id)

    result = j2534_api.PassThruDisconnect(channel_id)

    if result != 0 and j2534_config.raise_exceptions:
        raise J2534DisconnectError(
            f"PassThruDisconnect failed",
            error_code=result
        )

    debug_log_function_exit("pt_disconnect", return_value=result, success=(result == 0))
    return result


# =============================================================================
# Message I/O Functions
# =============================================================================

def pt_read_message(
    channel_id: int,
    message: PassThruMessageStructure,
    number_of_messages: int,
    message_timeout: int
) -> int:
    """
    Read messages from the receive buffer.

    Reads up to the specified number of messages from the channel's
    receive buffer. The actual number of messages read is returned
    in number_of_messages if it's passed by reference.

    Args:
        channel_id: The channel ID from pt_connect().
        message: A PassThruMessageStructure to receive the message data.
        number_of_messages: Maximum number of messages to read.
        message_timeout: Timeout in milliseconds.

    Returns:
        int: The J2534 error code (0 = success, 0x10 = buffer empty).

    Raises:
        J2534ReadError: If a real error occurred (when exceptions are enabled).
            Note: Buffer empty (0x10) doesn't raise an exception.

    Example:
        # >>> rx_msg = PassThruMsgBuilder(ProtocolId.ISO15765, 0)
        # >>> result = pt_read_message(channel_id, rx_msg, 1, 1000)
        # >>> if result == 0:
        # ...     print(f"Received: {rx_msg.dump_output()}")
    """
    debug_log_function_entry(
        "pt_read_message",
        channel_id=channel_id,
        number_of_messages=number_of_messages,
        timeout=message_timeout
    )

    result = j2534_api.PassThruReadMsgs(
        channel_id,
        ctypes.byref(message),
        ctypes.byref(ctypes.c_ulong(number_of_messages)),
        message_timeout
    )

    # Log the received message if successful
    if result == 0 and j2534_config.debug_enabled:
        debug_log_message(message, direction="received")

    # Buffer empty is not a real error
    if result != 0 and result != ErrorCode.ERR_BUFFER_EMPTY:
        if j2534_config.raise_exceptions:
            raise J2534ReadError(
                f"PassThruReadMsgs failed",
                error_code=result
            )

    debug_log_function_exit(
        "pt_read_message",
        return_value=result,
        success=(result == 0 or result == ErrorCode.ERR_BUFFER_EMPTY)
    )
    return result


def pt_write_message(
    channel_id: int,
    message: PassThruMessageStructure,
    number_of_messages: int,
    message_timeout: int
) -> int:
    """
    Write messages to the transmit buffer.

    Sends the specified messages to the vehicle network.

    Args:
        channel_id: The channel ID from pt_connect().
        message: The PassThruMessageStructure to send.
        number_of_messages: Number of messages to send.
        message_timeout: Timeout in milliseconds.

    Returns:
        int: The J2534 error code (0 = success).

    Raises:
        J2534WriteError: If the operation failed (when exceptions are enabled).

    Example:
        # >>> tx_msg = PassThruMsgBuilder(ProtocolId.ISO15765, TxFlags.ISO15765_FRAME_PAD)
        # >>> tx_msg.set_identifier_and_data(0x7E0, [0x22, 0xF1, 0x90])
        # >>> result = pt_write_message(channel_id, tx_msg, 1, 1000)
    """
    debug_log_function_entry(
        "pt_write_message",
        channel_id=channel_id,
        number_of_messages=number_of_messages,
        timeout=message_timeout
    )

    # Log the message being sent
    if j2534_config.debug_enabled:
        debug_log_message(message, direction="transmitting")

    result = j2534_api.PassThruWriteMsgs(
        channel_id,
        ctypes.byref(message),
        ctypes.byref(ctypes.c_ulong(number_of_messages)),
        message_timeout
    )

    if result != 0 and j2534_config.raise_exceptions:
        raise J2534WriteError(
            f"PassThruWriteMsgs failed",
            error_code=result
        )

    debug_log_function_exit("pt_write_message", return_value=result, success=(result == 0))
    return result


# =============================================================================
# Periodic Message Functions
# =============================================================================

def pt_start_periodic_message(
    channel_id: int,
    message: PassThruMessageStructure,
    time_interval: int
) -> Union[int, bool]:
    """
    Start periodic message transmission.

    Configures the device to automatically transmit a message at
    regular intervals. This is useful for keep-alive messages.

    Args:
        channel_id: The channel ID from pt_connect().
        message: The message to transmit periodically.
        time_interval: Interval between transmissions in milliseconds.

    Returns:
        int: The periodic message ID if successful.
        False: If the operation failed (when exceptions are disabled).

    Raises:
        J2534PeriodicMessageError: If the operation failed (when exceptions are enabled).

    Example:
        # >>> # Create tester present message
        # >>> tp_msg = PassThruMsgBuilder(ProtocolId.ISO15765, TxFlags.ISO15765_FRAME_PAD)
        # >>> tp_msg.set_identifier_and_data(0x7E0, [0x3E, 0x00])
        # >>> msg_id = pt_start_periodic_message(channel_id, tp_msg, 2000)
    """
    debug_log_function_entry(
        "pt_start_periodic_message",
        channel_id=channel_id,
        time_interval=time_interval
    )

    periodic_id = ctypes.c_ulong()
    result = j2534_api.PassThruStartPeriodicMsg(
        channel_id,
        ctypes.byref(message),
        ctypes.byref(periodic_id),
        time_interval
    )

    if result != 0:
        debug_log_function_exit(
            "pt_start_periodic_message",
            return_value=False,
            success=False,
            error_code=result
        )
        if j2534_config.raise_exceptions:
            raise J2534PeriodicMessageError(
                f"PassThruStartPeriodicMsg failed",
                error_code=result,
                function_name="PassThruStartPeriodicMsg"
            )
        return False

    debug_log_function_exit(
        "pt_start_periodic_message",
        return_value=periodic_id.value,
        success=True
    )
    return periodic_id.value


def pt_stop_periodic_message(
    channel_id: int,
    message_id: int
) -> int:
    """
    Stop periodic message transmission.

    Stops a previously started periodic message.

    Args:
        channel_id: The channel ID from pt_connect().
        message_id: The periodic message ID from pt_start_periodic_message().

    Returns:
        int: The J2534 error code (0 = success).

    Raises:
        J2534PeriodicMessageError: If the operation failed (when exceptions are enabled).
    """
    debug_log_function_entry(
        "pt_stop_periodic_message",
        channel_id=channel_id,
        message_id=message_id
    )

    result = j2534_api.PassThruStopPeriodicMsg(channel_id, message_id)

    if result != 0 and j2534_config.raise_exceptions:
        raise J2534PeriodicMessageError(
            f"PassThruStopPeriodicMsg failed",
            error_code=result,
            function_name="PassThruStopPeriodicMsg"
        )

    debug_log_function_exit(
        "pt_stop_periodic_message",
        return_value=result,
        success=(result == 0)
    )
    return result


# =============================================================================
# Message Filter Functions
# =============================================================================

def _create_filter_message(
    protocol_id: int,
    transmit_flags: int,
    identifier: int,
    is_identifier_only: bool = False
) -> PassThruMsg:
    """
    Create a filter message with the specified parameters.

    Internal helper function for creating mask, pattern, and flow
    control messages used with filters.

    Args:
        protocol_id: The protocol ID.
        transmit_flags: The transmit flags.
        identifier: The CAN identifier.
        is_identifier_only: If True, only set the identifier without data.

    Returns:
        PassThruMsg: The configured message.
    """
    message = PassThruMsg(protocol_id, transmit_flags)
    if is_identifier_only:
        message.set_identifier(identifier)
    else:
        message.set_identifier_and_data(identifier)
    return message


def _create_filter_messages(
    protocol_id: int,
    transmit_flags: int,
    mask_identifier: int,
    pattern_identifier: int,
    flow_control_identifier: Optional[int] = None
) -> Tuple[PassThruMsg, PassThruMsg, Optional[PassThruMsg]]:
    """
    Create the mask, pattern, and flow control messages for a filter.

    Internal helper that creates appropriately configured messages
    based on the protocol type.

    Args:
        protocol_id: The protocol ID.
        transmit_flags: The transmit flags.
        mask_identifier: The mask identifier.
        pattern_identifier: The pattern identifier.
        flow_control_identifier: The flow control identifier (optional).

    Returns:
        Tuple of (mask_message, pattern_message, flow_control_message).
        flow_control_message is None if flow_control_identifier is None.
    """
    # J1850 and SCI protocols use identifier-only format
    is_legacy_protocol = protocol_id in [
        ProtocolId.J1850_VPW,
        ProtocolId.SCI_A_ENGINE,
        ProtocolId.SCI_A_TRANS,
        ProtocolId.SCI_B_ENGINE,
        ProtocolId.SCI_B_TRANS
    ]

    mask_message = _create_filter_message(
        protocol_id, transmit_flags, mask_identifier, is_legacy_protocol
    )
    pattern_message = _create_filter_message(
        protocol_id, transmit_flags, pattern_identifier, is_legacy_protocol
    )

    flow_control_message = None
    if flow_control_identifier is not None:
        flow_control_message = _create_filter_message(
            protocol_id, transmit_flags, flow_control_identifier, False
        )

    return mask_message, pattern_message, flow_control_message


# Alias for backward compatibility
create_msg = _create_filter_messages


def pt_start_ecu_filter(
    channel_id: int,
    protocol_id: int,
    mask_identifier: Optional[int] = None,
    pattern_identifier: Optional[int] = None,
    flow_control_identifier: Optional[int] = None,
    transmit_flags: int = 0
) -> Union[int, bool]:
    """
    Start a message filter configured for ECU communication.

    This is a convenience function that creates appropriate filter
    messages based on the protocol type. For ISO 15765, it creates
    a flow control filter. For other protocols, it creates a pass filter.

    Args:
        channel_id: The channel ID from pt_connect().
        protocol_id: The protocol ID (determines filter type).
        mask_identifier: The mask identifier (usually 0xFFFFFFFF).
        pattern_identifier: The pattern identifier to match (e.g., 0x7E8).
        flow_control_identifier: The flow control identifier (for ISO 15765).
        transmit_flags: The transmit flags for the filter messages.

    Returns:
        int: The filter ID if successful.
        False: If the operation failed (when exceptions are disabled).

    Raises:
        J2534FilterError: If the operation failed (when exceptions are enabled).

    Example:
        # >>> # Set up ISO 15765 flow control filter
        # >>> filter_id = pt_start_ecu_filter(
        # ...     channel_id,
        # ...     ProtocolId.ISO15765,
        # ...     mask_identifier=0xFFFFFFFF,
        # ...     pattern_identifier=0x7E8,
        # ...     flow_control_identifier=0x7E0
        # ... )
    """
    debug_log_function_entry(
        "pt_start_ecu_filter",
        channel_id=channel_id,
        protocol_id=protocol_id,
        mask_id=mask_identifier,
        pattern_id=pattern_identifier,
        flow_control_id=flow_control_identifier
    )

    filter_id = ctypes.c_ulong()

    # ISO 15765 requires flow control filter
    if protocol_id == ProtocolId.ISO15765:
        mask_msg, pattern_msg, flow_control_msg = _create_filter_messages(
            protocol_id, transmit_flags,
            mask_identifier, pattern_identifier, flow_control_identifier
        )

        result = j2534_api.PassThruStartMsgFilter(
            channel_id,
            FilterType.FLOW_CONTROL_FILTER,
            ctypes.byref(mask_msg),
            ctypes.byref(pattern_msg),
            ctypes.byref(flow_control_msg),
            ctypes.byref(filter_id)
        )

    # J1850 and SCI protocols use pass filter
    elif protocol_id in [
        ProtocolId.J1850_VPW,
        ProtocolId.SCI_A_ENGINE,
        ProtocolId.SCI_A_TRANS,
        ProtocolId.SCI_B_ENGINE,
        ProtocolId.SCI_B_TRANS
    ]:
        mask_msg, pattern_msg, _ = _create_filter_messages(
            protocol_id, 0, mask_identifier, pattern_identifier
        )

        result = j2534_api.PassThruStartMsgFilter(
            channel_id,
            FilterType.PASS_FILTER,
            ctypes.byref(mask_msg),
            ctypes.byref(pattern_msg),
            ctypes.c_void_p(None),
            ctypes.byref(filter_id)
        )
    else:
        # Default case
        debug_log(
            f"Unsupported protocol {protocol_id} for pt_start_ecu_filter",
            function_name="pt_start_ecu_filter",
            level="warning"
        )
        return False

    if result != 0:
        debug_log_function_exit(
            "pt_start_ecu_filter",
            return_value=False,
            success=False,
            error_code=result
        )
        if j2534_config.raise_exceptions:
            raise J2534FilterError(
                f"PassThruStartMsgFilter failed",
                error_code=result
            )
        return False

    debug_log_function_exit(
        "pt_start_ecu_filter",
        return_value=filter_id.value,
        success=True
    )
    return filter_id.value


def pt_start_message_filter(
    channel_id: int,
    filter_type: int,
    mask_message: PassThruMessageStructure,
    pattern_message: PassThruMessageStructure,
    flow_control_message: Optional[PassThruMessageStructure]
) -> Union[int, bool]:
    """
    Start a message filter with explicit filter messages.

    This provides full control over the filter configuration.

    Args:
        channel_id: The channel ID from pt_connect().
        filter_type: The filter type (see FilterType enum).
        mask_message: The mask message.
        pattern_message: The pattern message.
        flow_control_message: The flow control message (can be None).

    Returns:
        int: The filter ID if successful.
        False: If the operation failed (when exceptions are disabled).

    Raises:
        J2534FilterError: If the operation failed (when exceptions are enabled).
    """
    debug_log_function_entry(
        "pt_start_message_filter",
        channel_id=channel_id,
        filter_type=filter_type
    )

    filter_id = ctypes.c_ulong()

    if flow_control_message is not None:
        flow_control_ptr = ctypes.byref(flow_control_message)
    else:
        flow_control_ptr = ctypes.c_void_p(None)

    result = j2534_api.PassThruStartMsgFilter(
        channel_id,
        filter_type,
        ctypes.byref(mask_message),
        ctypes.byref(pattern_message),
        flow_control_ptr,
        ctypes.byref(filter_id)
    )

    if result != 0:
        if j2534_config.raise_exceptions:
            raise J2534FilterError(
                f"PassThruStartMsgFilter failed",
                error_code=result
            )
        return False

    debug_log_function_exit(
        "pt_start_message_filter",
        return_value=filter_id.value,
        success=True
    )
    return filter_id.value


def pt_stop_message_filter(
    channel_id: int,
    filter_id: int
) -> int:
    """
    Stop/remove a message filter.

    Args:
        channel_id: The channel ID.
        filter_id: The filter ID from pt_start_message_filter() or pt_start_ecu_filter().

    Returns:
        int: The J2534 error code (0 = success).
    """
    debug_log_function_entry(
        "pt_stop_message_filter",
        channel_id=channel_id,
        filter_id=filter_id
    )

    result = j2534_api.PassThruStopMsgFilter(channel_id, filter_id)

    if result != 0 and j2534_config.raise_exceptions:
        raise J2534FilterError(
            f"PassThruStopMsgFilter failed",
            error_code=result,
            function_name="PassThruStopMsgFilter"
        )

    debug_log_function_exit(
        "pt_stop_message_filter",
        return_value=result,
        success=(result == 0)
    )
    return result


# =============================================================================
# Information and Utility Functions
# =============================================================================

def pt_set_programming_voltage(
    device_id: int,
    pin_number: int,
    voltage: int
) -> int:
    """
    Set the programming voltage on a specific pin.

    Controls the voltage output on J1962 connector pins for ECU
    programming operations.

    Args:
        device_id: The device ID from pt_open().
        pin_number: The pin number (see Pin enum).
        voltage: The voltage in millivolts, or special values
            (PinVoltage.VOLTAGE_OFF, PinVoltage.SHORT_TO_GROUND).

    Returns:
        int: The J2534 error code (0 = success).

    Example:
        # >>> # Set 12V on pin 15
        # >>> pt_set_programming_voltage(device_id, Pin.J1962_PIN_15, 12000)
    """
    debug_log_function_entry(
        "pt_set_programming_voltage",
        device_id=device_id,
        pin_number=pin_number,
        voltage=voltage
    )

    result = j2534_api.PassThruSetProgrammingVoltage(device_id, pin_number, voltage)

    debug_log_function_exit(
        "pt_set_programming_voltage",
        return_value=result,
        success=(result == 0)
    )
    return result


def pt_read_version(device_id: int) -> List[str]:
    """
    Read the firmware and DLL version information.

    Returns version strings for the device firmware, DLL, and API.

    Args:
        device_id: The device ID from pt_open().

    Returns:
        List[str]: A list of [firmware_version, dll_version, api_version].
            Returns ['error', 'error', 'error'] on failure (when exceptions disabled).

    Raises:
        J2534IoctlError: If the operation failed (when exceptions are enabled).

    Example:
        # >>> versions = pt_read_version(device_id)
        # >>> print(f"Firmware: {versions[0]}")
        # >>> print(f"DLL: {versions[1]}")
        # >>> print(f"API: {versions[2]}")
    """
    debug_log_function_entry("pt_read_version", device_id=device_id)

    firmware_version = ctypes.create_string_buffer(80)
    dll_version = ctypes.create_string_buffer(80)
    api_version = ctypes.create_string_buffer(80)

    result = j2534_api.PassThruReadVersion(
        device_id,
        firmware_version,
        dll_version,
        api_version
    )

    if result != 0:
        debug_log_function_exit(
            "pt_read_version",
            return_value="error",
            success=False,
            error_code=result
        )
        if j2534_config.raise_exceptions:
            raise J2534IoctlError(
                f"PassThruReadVersion failed",
                error_code=result
            )
        return ['error', 'error', 'error']

    versions = [
        firmware_version.value.decode('utf-8', errors='replace'),
        dll_version.value.decode('utf-8', errors='replace'),
        api_version.value.decode('utf-8', errors='replace')
    ]

    debug_log_function_exit("pt_read_version", return_value=versions, success=True)
    return versions


def pt_get_last_error() -> bytes:
    """
    Get the text description of the last error.

    Returns a human-readable description of the most recent J2534
    error that occurred.

    Returns:
        bytes: The error description as bytes.

    Example:
        # >>> error_desc = pt_get_last_error()
        # >>> print(error_desc.decode())
    """
    error_buffer = ctypes.create_string_buffer(80)
    j2534_api.PassThruGetLastError(error_buffer)
    return error_buffer.value


def pt_ioctl(
    channel_id: int,
    ioctl_id: int,
    ioctl_input: Optional[ctypes.c_void_p],
    ioctl_output: Optional[ctypes.c_void_p]
) -> int:
    """
    Execute an I/O control operation.

    Performs various configuration and control operations through
    the general IOCTL interface.

    Args:
        channel_id: The channel ID (or device ID for some IOCTLs).
        ioctl_id: The IOCTL command ID (see IoctlId enum).
        ioctl_input: Input parameter (depends on IOCTL).
        ioctl_output: Output parameter (depends on IOCTL).

    Returns:
        int: The J2534 error code (0 = success).

    Raises:
        J2534IoctlError: If the operation failed (when exceptions are enabled).

    Example:
        # >>> result = pt_ioctl(channel_id, IoctlId.CLEAR_RX_BUFFER, None, None)
    """
    result = j2534_api.PassThruIoctl(channel_id, ioctl_id, ioctl_input, ioctl_output)

    if result != 0 and j2534_config.raise_exceptions:
        raise J2534IoctlError(
            f"PassThruIoctl failed",
            error_code=result,
            ioctl_id=ioctl_id
        )

    return result


# =============================================================================
# Configuration Functions
# =============================================================================

def pt_set_config(
    channel_id: int,
    parameters: List[Tuple[int, int]]
) -> Tuple[int, ctypes.POINTER(SetConfigurationParameter)]:
    """
    Set configuration parameters on a channel.

    Sets multiple configuration parameters in a single operation.

    Args:
        channel_id: The channel ID from pt_connect().
        parameters: A list of (parameter_id, value) tuples.

    Returns:
        Tuple of (result_code, config_pointer).

    Example:
        # >>> result, _ = pt_set_config(channel_id, [
        # ...     (ConfigParameter.DATA_RATE, 500000),
        # ...     (ConfigParameter.LOOPBACK, 0)
        # ... ])
    """
    debug_log_function_entry(
        "pt_set_config",
        channel_id=channel_id,
        parameter_count=len(parameters)
    )

    config_list = SetConfigurationList()
    config_list.NumOfParams = len(parameters)

    config_array = (SetConfigurationParameter * len(parameters))()
    config_list.ConfigPtr = ctypes.cast(
        config_array,
        ctypes.POINTER(SetConfigurationParameter)
    )

    for index, (parameter_id, value) in enumerate(parameters):
        config_list.ConfigPtr[index].Parameter = parameter_id
        config_list.ConfigPtr[index].Value = value

    result = pt_ioctl(
        channel_id,
        IoctlId.SET_CONFIG,
        ctypes.byref(config_list),
        ctypes.c_void_p(None)
    )

    debug_log_function_exit(
        "pt_set_config",
        return_value=result,
        success=(result == 0)
    )
    return result, config_list.ConfigPtr


# =============================================================================
# Voltage and Buffer Functions
# =============================================================================

def read_battery_volts(device_id: int) -> Union[float, bool]:
    """
    Read the vehicle battery voltage.

    Reads the battery voltage from the OBD-II connector.

    Args:
        device_id: The device ID from pt_open().

    Returns:
        float: The battery voltage in volts (e.g., 12.5).
        False: If the operation failed (when exceptions are disabled).

    Raises:
        J2534IoctlError: If the operation failed (when exceptions are enabled).

    Example:
        # >>> voltage = read_battery_volts(device_id)
        # >>> if voltage:
        # ...     print(f"Battery: {voltage:.1f}V")
    """
    debug_log_function_entry("read_battery_volts", device_id=device_id)

    voltage_mv = ctypes.c_ulong()
    result = pt_ioctl(
        device_id,
        IoctlId.READ_VBATT,
        ctypes.c_void_p(None),
        ctypes.byref(voltage_mv)
    )

    if result != 0:
        debug_log_function_exit(
            "read_battery_volts",
            return_value=False,
            success=False,
            error_code=result
        )
        return False

    voltage_volts = voltage_mv.value / 1000.0
    debug_log_function_exit(
        "read_battery_volts",
        return_value=f"{voltage_volts}V",
        success=True
    )
    return voltage_volts


def read_programming_voltage(channel_id: int) -> Union[float, bool]:
    """
    Read the programming voltage.

    Args:
        channel_id: The channel ID.

    Returns:
        float: The programming voltage in volts.
        False: If the operation failed.
    """
    voltage_mv = ctypes.c_ulong()
    result = pt_ioctl(
        channel_id,
        IoctlId.READ_PROG_VOLTAGE,
        ctypes.c_void_p(None),
        ctypes.byref(voltage_mv)
    )

    if result != 0:
        return False

    return voltage_mv.value / 1000.0


def clear_transmit_buffer(channel_id: int) -> int:
    """
    Clear the channel's transmit buffer.

    Args:
        channel_id: The channel ID from pt_connect().

    Returns:
        int: The J2534 error code (0 = success).
    """
    return pt_ioctl(
        channel_id,
        IoctlId.CLEAR_TX_BUFFER,
        ctypes.c_void_p(None),
        ctypes.c_void_p(None)
    )


def clear_receive_buffer(channel_id: int) -> int:
    """
    Clear the channel's receive buffer.

    Args:
        channel_id: The channel ID from pt_connect().

    Returns:
        int: The J2534 error code (0 = success).
    """
    return pt_ioctl(
        channel_id,
        IoctlId.CLEAR_RX_BUFFER,
        ctypes.c_void_p(None),
        ctypes.c_void_p(None)
    )


def clear_periodic_messages(channel_id: int) -> int:
    """
    Clear all periodic messages on a channel.

    Args:
        channel_id: The channel ID from pt_connect().

    Returns:
        int: The J2534 error code (0 = success).
    """
    return pt_ioctl(
        channel_id,
        IoctlId.CLEAR_PERIODIC_MSGS,
        ctypes.c_void_p(None),
        ctypes.c_void_p(None)
    )


def clear_message_filters(channel_id: int) -> int:
    """
    Clear all message filters on a channel.

    Args:
        channel_id: The channel ID from pt_connect().

    Returns:
        int: The J2534 error code (0 = success).
    """
    return pt_ioctl(
        channel_id,
        IoctlId.CLEAR_MSG_FILTERS,
        ctypes.c_void_p(None),
        ctypes.c_void_p(None)
    )


def clear_functional_message_lookup_table(channel_id: int) -> int:
    """
    Clear the functional message lookup table.

    Args:
        channel_id: The channel ID from pt_connect().

    Returns:
        int: The J2534 error code (0 = success).
    """
    return pt_ioctl(
        channel_id,
        IoctlId.CLEAR_FUNCT_MSG_LOOKUP_TABLE,
        ctypes.c_void_p(None),
        ctypes.c_void_p(None)
    )


# =============================================================================
# Module-Level Aliases
# =============================================================================

# Convenience aliases for common operations
get_list_j2534_devices = j2534_api.get_devices
"""Get list of available J2534 devices. Alias for j2534_api.get_devices()."""

set_j2534_device_to_connect = j2534_api.set_device
"""Select a J2534 device by index. Alias for j2534_api.set_device()."""
