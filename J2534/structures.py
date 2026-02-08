"""
J2534 ctypes Structure Definitions
==================================

This module defines the ctypes structures required for interfacing with
J2534 PassThru DLLs. These structures map directly to the C structures
defined in the SAE J2534-1 v04.04 specification.

The structures handle the low-level data layout required for communication
with the Windows DLL. Field names match the SAE J2534 specification for
compatibility with all compliant DLLs.

Structures:
    PassThruMessageStructure: The PASSTHRU_MSG structure for message I/O
    SetConfigurationParameter: The SCONFIG structure for configuration
    SetConfigurationList: The SCONFIG_LIST for bulk configuration
    SByteArray: The SBYTE_ARRAY structure for byte arrays

Constants:
    PASSTHRU_MESSAGE_DATA_SIZE: Maximum data buffer size (4128 bytes)

Note:
    The field names in these structures (ProtocolID, RxStatus, etc.) use
    the original C naming convention to ensure binary compatibility with
    J2534 DLLs. Python-style property accessors are provided for convenience.

Example:
    Creating and populating a message::

        from J2534.structures import PassThruMessageStructure

        message = PassThruMessageStructure()
        message.protocol_id = 6  # ISO15765
        message.transmit_flags = 0x40  # Frame padding
        message.set_data([0x7E, 0x00, 0x22, 0xF1, 0x90])

Example:
    Setting configuration parameters::

        from J2534.structures import SetConfigurationList, SetConfigurationParameter

        config_list = SetConfigurationList()
        config_list.set_parameters([
            (Parameter.DATA_RATE, 500000),
            (Parameter.LOOPBACK, 0)
        ])

Author: J2534-API Contributors
License: MIT
Version: 2.0.0
"""

import ctypes
from typing import List, Tuple, Union, Optional


# =============================================================================
# Constants
# =============================================================================

PASSTHRU_MESSAGE_DATA_SIZE: int = 4128
"""
Maximum size of the data buffer in a PASSTHRU_MSG structure.

This value is defined by the SAE J2534 specification and represents
the maximum number of bytes that can be stored in the Data field of
a J2534 message. This accommodates even the largest ISO 15765 messages.
"""


# Type alias for the message data buffer (array of unsigned bytes)
PassThruDataBuffer = ctypes.c_ubyte * PASSTHRU_MESSAGE_DATA_SIZE
"""
ctypes type for the message data buffer.

This is an array of unsigned bytes with size PASSTHRU_MESSAGE_DATA_SIZE.
It represents the Data field in the PASSTHRU_MSG structure.
"""


# =============================================================================
# Message Structure
# =============================================================================

class PassThruMessageStructure(ctypes.Structure):
    """
    The PASSTHRU_MSG structure for J2534 message transmission and reception.

    This structure is the primary data structure for all message operations
    in the J2534 API. It is used with PassThruReadMsgs() and PassThruWriteMsgs()
    to send and receive vehicle network messages.

    The structure fields match the SAE J2534 specification exactly to ensure
    binary compatibility with J2534 DLLs. Python-style property accessors
    are provided for convenience.

    C Structure Definition (from J2534 spec)::

        typedef struct {
            unsigned long ProtocolID;
            unsigned long RxStatus;
            unsigned long TxFlags;
            unsigned long Timestamp;
            unsigned long DataSize;
            unsigned long ExtraDataIndex;
            unsigned char Data[4128];
        } PASSTHRU_MSG;

    Attributes:
        ProtocolID (ctypes.c_ulong): Protocol identifier for the message.
            Must match the protocol used when the channel was connected.
        RxStatus (ctypes.c_ulong): Receive status flags. Indicates message
            type (echo, first frame, etc.) on received messages.
        TxFlags (ctypes.c_ulong): Transmit flags. Controls transmission
            behavior (padding, addressing mode, etc.) on sent messages.
        Timestamp (ctypes.c_ulong): Message timestamp in microseconds.
            Set by the device on received messages.
        DataSize (ctypes.c_ulong): Number of valid bytes in the Data buffer.
            Must be set before transmission.
        ExtraDataIndex (ctypes.c_ulong): Index for extra data (protocol-specific).
            Used by some protocols for additional metadata.
        Data (PassThruDataBuffer): Message data buffer (4128 bytes maximum).
            Contains the actual message bytes.

    Properties:
        protocol_id: Python-style accessor for ProtocolID
        receive_status: Python-style accessor for RxStatus
        transmit_flags: Python-style accessor for TxFlags
        timestamp: Python-style accessor for Timestamp
        data_size: Python-style accessor for DataSize
        extra_data_index: Python-style accessor for ExtraDataIndex

    Example:
        Creating a CAN message::

            message = PassThruMessageStructure()
            message.protocol_id = 6  # ISO15765
            message.transmit_flags = 0x40  # Frame padding
            message.set_data([0x7E, 0x00, 0x22, 0xF1, 0x90])
            # DataSize is automatically set by set_data()

        Reading message data::

            pt_read_message(channel_id, message, 1, 1000)
            if message.data_size > 0:
                data_bytes = message.get_data()
                print(f"Received {len(data_bytes)} bytes")
    """

    # Define the structure fields matching the C structure
    _fields_ = [
        ("ProtocolID", ctypes.c_ulong),
        ("RxStatus", ctypes.c_ulong),
        ("TxFlags", ctypes.c_ulong),
        ("Timestamp", ctypes.c_ulong),
        ("DataSize", ctypes.c_ulong),
        ("ExtraDataIndex", ctypes.c_ulong),
        ("Data", PassThruDataBuffer)
    ]

    # =========================================================================
    # Python-style Property Accessors
    # =========================================================================

    @property
    def protocol_id(self) -> int:
        """
        Get the protocol identifier for this message.

        Returns:
            int: The protocol ID (see ProtocolId enum).
        """
        return self.ProtocolID

    @protocol_id.setter
    def protocol_id(self, value: int) -> None:
        """
        Set the protocol identifier for this message.

        Args:
            value: The protocol ID to set.
        """
        self.ProtocolID = value

    @property
    def receive_status(self) -> int:
        """
        Get the receive status flags for this message.

        Returns:
            int: The receive status flags (see RxStatus enum).
        """
        return self.RxStatus

    @receive_status.setter
    def receive_status(self, value: int) -> None:
        """
        Set the receive status flags for this message.

        Args:
            value: The receive status flags to set.
        """
        self.RxStatus = value

    @property
    def transmit_flags(self) -> int:
        """
        Get the transmit flags for this message.

        Returns:
            int: The transmit flags (see TxFlags enum).
        """
        return self.TxFlags

    @transmit_flags.setter
    def transmit_flags(self, value: int) -> None:
        """
        Set the transmit flags for this message.

        Args:
            value: The transmit flags to set.
        """
        self.TxFlags = value

    @property
    def timestamp(self) -> int:
        """
        Get the message timestamp in microseconds.

        Returns:
            int: The timestamp value.
        """
        return self.Timestamp

    @timestamp.setter
    def timestamp(self, value: int) -> None:
        """
        Set the message timestamp.

        Args:
            value: The timestamp in microseconds.
        """
        self.Timestamp = value

    @property
    def data_size(self) -> int:
        """
        Get the number of valid bytes in the data buffer.

        Returns:
            int: The number of valid data bytes.
        """
        return self.DataSize

    @data_size.setter
    def data_size(self, value: int) -> None:
        """
        Set the number of valid bytes in the data buffer.

        Args:
            value: The number of valid data bytes.
        """
        self.DataSize = value

    @property
    def extra_data_index(self) -> int:
        """
        Get the extra data index.

        Returns:
            int: The extra data index value.
        """
        return self.ExtraDataIndex

    @extra_data_index.setter
    def extra_data_index(self, value: int) -> None:
        """
        Set the extra data index.

        Args:
            value: The extra data index value.
        """
        self.ExtraDataIndex = value

    # =========================================================================
    # Data Manipulation Methods
    # =========================================================================

    def set_data(self, data: Union[bytes, bytearray, List[int]]) -> None:
        """
        Set the message data from a bytes, bytearray, or list of integers.

        This method copies the data into the Data buffer and automatically
        sets DataSize to the length of the data.

        Args:
            data: The data to set. Can be bytes, bytearray, or a list of
                integer values (0-255).

        Raises:
            ValueError: If the data exceeds PASSTHRU_MESSAGE_DATA_SIZE bytes.

        Example:
            >>> message = PassThruMessageStructure()
            >>> message.set_data([0x7E, 0x00, 0x22, 0xF1, 0x90])
            >>> print(message.data_size)
            5
        """
        if len(data) > PASSTHRU_MESSAGE_DATA_SIZE:
            raise ValueError(
                f"Data size {len(data)} exceeds maximum "
                f"{PASSTHRU_MESSAGE_DATA_SIZE} bytes"
            )

        self.DataSize = len(data)
        for index, byte_value in enumerate(data):
            self.Data[index] = byte_value

    def get_data(self) -> bytes:
        """
        Get the valid message data as bytes.

        Returns only the valid portion of the data buffer (up to DataSize).

        Returns:
            bytes: The valid data bytes from the message.

        Example:
            >>> data = message.get_data()
            >>> print(data.hex())
            7e00f190
        """
        return bytes(self.Data[:self.DataSize])

    def get_data_list(self) -> List[int]:
        """
        Get the valid message data as a list of integers.

        Returns only the valid portion of the data buffer (up to DataSize).

        Returns:
            List[int]: The valid data bytes as a list of integers.

        Example:
            >>> data_list = message.get_data_list()
            >>> print(data_list)
            [126, 0, 241, 144]
        """
        return list(self.Data[:self.DataSize])

    def clear(self) -> None:
        """
        Clear all fields of the message structure.

        Resets all fields to zero, effectively creating a blank message.

        Example:
            >>> message.clear()
            >>> print(message.data_size)
            0
        """
        self.ProtocolID = 0
        self.RxStatus = 0
        self.TxFlags = 0
        self.Timestamp = 0
        self.DataSize = 0
        self.ExtraDataIndex = 0
        # Clear data buffer
        for i in range(PASSTHRU_MESSAGE_DATA_SIZE):
            self.Data[i] = 0

    # =========================================================================
    # Formatting and Display Methods
    # =========================================================================

    def to_hex_string(self) -> str:
        """
        Get the valid data as a hex string.

        Returns:
            str: The data bytes formatted as uppercase hex pairs.

        Example:
            >>> print(message.to_hex_string())
            7E 00 22 F1 90
        """
        return " ".join(f"{byte:02X}" for byte in self.Data[:self.DataSize])

    def dump(self) -> str:
        """
        Get a human-readable dump of the message structure.

        Returns:
            str: A formatted string showing all message fields.

        Example:
            >>> print(message.dump())
            ProtocolID: 6 (ISO15765)
            RxStatus: 0x0000
            TxFlags: 0x0040
            Timestamp: 0
            DataSize: 5
            Data: 7E 00 22 F1 90
        """
        protocol_names = {
            1: "J1850VPW", 2: "J1850PWM", 3: "ISO9141",
            4: "ISO14230", 5: "CAN", 6: "ISO15765",
            7: "SCI_A_ENGINE", 8: "SCI_A_TRANS",
            9: "SCI_B_ENGINE", 10: "SCI_B_TRANS"
        }
        protocol_name = protocol_names.get(self.ProtocolID, "Unknown")

        lines = [
            f"ProtocolID: {self.ProtocolID} ({protocol_name})",
            f"RxStatus: 0x{self.RxStatus:04X}",
            f"TxFlags: 0x{self.TxFlags:04X}",
            f"Timestamp: {self.Timestamp}",
            f"DataSize: {self.DataSize}",
            f"Data: {self.to_hex_string()}"
        ]
        return "\n".join(lines)

    def __repr__(self) -> str:
        """Return a string representation of the message."""
        return (
            f"PassThruMessageStructure("
            f"protocol_id={self.ProtocolID}, "
            f"data_size={self.DataSize}, "
            f"data={self.to_hex_string()})"
        )


# =============================================================================
# Configuration Structures
# =============================================================================

class SetConfigurationParameter(ctypes.Structure):
    """
    The SCONFIG structure for a single configuration parameter.

    This structure represents a single parameter/value pair used with
    the GET_CONFIG and SET_CONFIG IOCTL commands.

    C Structure Definition::

        typedef struct {
            unsigned long Parameter;
            unsigned long Value;
        } SCONFIG;

    Attributes:
        Parameter (ctypes.c_ulong): The parameter identifier
            (see ConfigParameter enum).
        Value (ctypes.c_ulong): The parameter value.

    Properties:
        parameter: Python-style accessor for Parameter
        value: Python-style accessor for Value

    Example:
        >>> config = SetConfigurationParameter()
        >>> config.parameter = Parameter.DATA_RATE
        >>> config.value = 500000
    """

    _fields_ = [
        ("Parameter", ctypes.c_ulong),
        ("Value", ctypes.c_ulong)
    ]

    @property
    def parameter(self) -> int:
        """Get the parameter identifier."""
        return self.Parameter

    @parameter.setter
    def parameter(self, value: int) -> None:
        """Set the parameter identifier."""
        self.Parameter = value

    @property
    def value(self) -> int:
        """Get the parameter value."""
        return self.Value

    @value.setter
    def value(self, new_value: int) -> None:
        """Set the parameter value."""
        self.Value = new_value

    def set_parameter(self, parameter_id: int) -> None:
        """
        Set the parameter identifier.

        Args:
            parameter_id: The parameter ID to set.

        Note:
            This method is provided for backward compatibility.
            Prefer using the parameter property directly.
        """
        self.Parameter = parameter_id

    def set_value(self, value: int) -> None:
        """
        Set the parameter value.

        Args:
            value: The value to set.

        Note:
            This method is provided for backward compatibility.
            Prefer using the value property directly.
        """
        self.Value = value

    def __repr__(self) -> str:
        """Return a string representation."""
        return f"SetConfigurationParameter(parameter=0x{self.Parameter:02X}, value={self.Value})"


# Alias for backward compatibility
SetConfiguration = SetConfigurationParameter


class SetConfigurationList(ctypes.Structure):
    """
    The SCONFIG_LIST structure for bulk configuration operations.

    This structure is used with GET_CONFIG and SET_CONFIG IOCTL commands
    to read or write multiple configuration parameters at once.

    C Structure Definition::

        typedef struct {
            unsigned long NumOfParams;
            SCONFIG* ConfigPtr;
        } SCONFIG_LIST;

    Attributes:
        NumOfParams (ctypes.c_ulong): Number of parameters in the list.
        ConfigPtr (POINTER(SetConfigurationParameter)): Pointer to array
            of SCONFIG structures.

    Properties:
        number_of_parameters: Python-style accessor for NumOfParams
        configuration_pointer: Python-style accessor for ConfigPtr

    Example:
        Setting multiple parameters::

            config_list = SetConfigurationList()
            config_list.set_parameters([
                (Parameter.DATA_RATE, 500000),
                (Parameter.LOOPBACK, 0)
            ])

        Getting parameters::

            config_list = SetConfigurationList()
            config_list.create_for_reading([
                Parameter.DATA_RATE,
                Parameter.LOOPBACK
            ])
            pt_ioctl(channel_id, IoctlId.GET_CONFIG, byref(config_list), None)
            for i in range(config_list.number_of_parameters):
                print(f"{config_list.ConfigPtr[i].Parameter}: {config_list.ConfigPtr[i].Value}")
    """

    _fields_ = [
        ("NumOfParams", ctypes.c_ulong),
        ("ConfigPtr", ctypes.POINTER(SetConfigurationParameter))
    ]

    # Storage for the parameter array (prevents garbage collection)
    _parameter_array: Optional[ctypes.Array] = None

    @property
    def number_of_parameters(self) -> int:
        """Get the number of parameters in the list."""
        return self.NumOfParams

    @number_of_parameters.setter
    def number_of_parameters(self, value: int) -> None:
        """Set the number of parameters."""
        self.NumOfParams = value

    @property
    def configuration_pointer(self) -> ctypes.POINTER(SetConfigurationParameter):
        """Get the pointer to the configuration array."""
        return self.ConfigPtr

    def set_parameters(
        self,
        parameters: List[Tuple[int, int]]
    ) -> None:
        """
        Set multiple configuration parameters.

        Creates the internal array and populates it with the given
        parameter/value pairs.

        Args:
            parameters: A list of (parameter_id, value) tuples.

        Example:
            >>> config_list = SetConfigurationList()
            >>> config_list.set_parameters([
            ...     (Parameter.DATA_RATE, 500000),
            ...     (Parameter.LOOPBACK, 0)
            ... ])
        """
        count = len(parameters)
        self.NumOfParams = count

        # Create array and store reference to prevent garbage collection
        self._parameter_array = (SetConfigurationParameter * count)()
        self.ConfigPtr = ctypes.cast(
            self._parameter_array,
            ctypes.POINTER(SetConfigurationParameter)
        )

        for index, (parameter_id, value) in enumerate(parameters):
            self.ConfigPtr[index].Parameter = parameter_id
            self.ConfigPtr[index].Value = value

    def create_for_reading(self, parameter_ids: List[int]) -> None:
        """
        Create a configuration list for reading parameters.

        Creates the internal array with the specified parameter IDs.
        The values will be filled in by GET_CONFIG.

        Args:
            parameter_ids: A list of parameter IDs to read.

        Example:
            >>> config_list = SetConfigurationList()
            >>> config_list.create_for_reading([
            ...     Parameter.DATA_RATE,
            ...     Parameter.LOOPBACK
            ... ])
            >>> pt_ioctl(channel_id, IoctlId.GET_CONFIG, byref(config_list), None)
        """
        count = len(parameter_ids)
        self.NumOfParams = count

        self._parameter_array = (SetConfigurationParameter * count)()
        self.ConfigPtr = ctypes.cast(
            self._parameter_array,
            ctypes.POINTER(SetConfigurationParameter)
        )

        for index, parameter_id in enumerate(parameter_ids):
            self.ConfigPtr[index].Parameter = parameter_id
            self.ConfigPtr[index].Value = 0  # Will be filled by GET_CONFIG

    def get_values(self) -> List[Tuple[int, int]]:
        """
        Get the parameter values as a list of tuples.

        Returns:
            List[Tuple[int, int]]: A list of (parameter_id, value) tuples.

        Example:
            >>> values = config_list.get_values()
            >>> for param_id, value in values:
            ...     print(f"Parameter {param_id}: {value}")
        """
        result = []
        for index in range(self.NumOfParams):
            param = self.ConfigPtr[index]
            result.append((param.Parameter, param.Value))
        return result

    def __repr__(self) -> str:
        """Return a string representation."""
        return f"SetConfigurationList(count={self.NumOfParams})"


# =============================================================================
# Byte Array Structure (for initialization)
# =============================================================================

class SByteArray(ctypes.Structure):
    """
    The SBYTE_ARRAY structure for byte array data.

    This structure is used with some IOCTL commands that require
    byte array data, such as FIVE_BAUD_INIT.

    C Structure Definition::

        typedef struct {
            unsigned long NumOfBytes;
            unsigned char* BytePtr;
        } SBYTE_ARRAY;

    Attributes:
        NumOfBytes (ctypes.c_ulong): Number of bytes in the array.
        BytePtr (POINTER(c_ubyte)): Pointer to the byte data.

    Example:
        >>> byte_array = SByteArray()
        >>> byte_array.set_bytes([0x33, 0xF1, 0x01])
    """

    _fields_ = [
        ("NumOfBytes", ctypes.c_ulong),
        ("BytePtr", ctypes.POINTER(ctypes.c_ubyte))
    ]

    # Storage for the byte array (prevents garbage collection)
    _byte_storage: Optional[ctypes.Array] = None

    @property
    def number_of_bytes(self) -> int:
        """Get the number of bytes in the array."""
        return self.NumOfBytes

    def set_bytes(self, data: Union[bytes, bytearray, List[int]]) -> None:
        """
        Set the byte array data.

        Args:
            data: The bytes to set.

        Example:
            >>> byte_array = SByteArray()
            >>> byte_array.set_bytes([0x33, 0xF1, 0x01])
        """
        count = len(data)
        self.NumOfBytes = count

        self._byte_storage = (ctypes.c_ubyte * count)(*data)
        self.BytePtr = ctypes.cast(
            self._byte_storage,
            ctypes.POINTER(ctypes.c_ubyte)
        )

    def get_bytes(self) -> bytes:
        """
        Get the byte data.

        Returns:
            bytes: The byte data from the array.
        """
        return bytes(self.BytePtr[:self.NumOfBytes])


# =============================================================================
# Helper Functions
# =============================================================================

def create_message(
    protocol_id: int,
    transmit_flags: int = 0,
    data: Optional[Union[bytes, bytearray, List[int]]] = None
) -> PassThruMessageStructure:
    """
    Create and initialize a PassThruMessageStructure.

    This is a convenience function for creating message structures
    with common settings.

    Args:
        protocol_id: The protocol identifier for the message.
        transmit_flags: The transmit flags (default 0).
        data: Optional message data to set.

    Returns:
        PassThruMessageStructure: An initialized message structure.

    Example:
        >>> message = create_message(
        ...     protocol_id=6,
        ...     transmit_flags=0x40,
        ...     data=[0x7E, 0x00, 0x22, 0xF1, 0x90]
        ... )
    """
    message = PassThruMessageStructure()
    message.ProtocolID = protocol_id
    message.TxFlags = transmit_flags

    if data is not None:
        message.set_data(data)

    return message


def create_empty_message() -> PassThruMessageStructure:
    """
    Create an empty PassThruMessageStructure for receiving.

    Returns:
        PassThruMessageStructure: An empty message structure ready
            to receive data.

    Example:
        >>> rx_message = create_empty_message()
        >>> pt_read_message(channel_id, rx_message, 1, 1000)
    """
    return PassThruMessageStructure()
