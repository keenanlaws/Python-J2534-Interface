# -*- coding: utf-8 -*-
"""
AutoJ2534 High-Level Vehicle Communication Interface
=====================================================

This module provides a simplified, high-level interface for J2534 vehicle
communication. It wraps the low-level J2534 API functions to enable quick
and easy ECU communication with just 1-2 lines of code.

Features:
    - Automatic device discovery and connection
    - Pre-configured ECU connection profiles (Chrysler, OBD-II)
    - UDS service wrappers (read VIN, DTCs, security access)
    - Context manager support for automatic cleanup
    - Retry logic and configurable timeouts
    - Support for ISO15765, SCI, and K-Line protocols

Example Usage:
    Quick 1-line connection::

        from AutoJ2534 import quick_connect
        comm = quick_connect()
        print(comm.read_vin())

    With context manager (automatic cleanup)::

        from AutoJ2534 import J2534Communications
        with J2534Communications(0, "chrys1") as comm:
            response = comm.transmit_and_receive_message([0x22, 0xF1, 0x90])
            print(f"VIN response: {response}")

    Auto-detect and connect::

        from AutoJ2534 import J2534Communications
        comm = J2534Communications()
        result = comm.auto_connect()
        if result:
            print(f"Connected to {result[2]} via {result[3]}")

Dependencies:
    - Windows OS (uses Windows Registry and ctypes)
    - Python 3.10+
    - J2534 module (low-level PassThru API)

Author: J2534-API Contributors
License: MIT
Version: 2.0.0
"""

import time
import winreg
import platform
from typing import Optional, List, Dict, Any, Union

import J2534
from AutoJ2534.ecu_parameters import Connections
from AutoJ2534.negative_response_codes import (
    NEGATIVE_RESPONSE_CODES_HEX,
    get_negative_response_description_hex,
    is_response_pending
)


class J2534Communications:
    """
    High-level interface for J2534 vehicle communication.

    This class provides a simplified API for connecting to vehicles and
    exchanging diagnostic messages using the J2534 PassThru standard.
    It supports context manager usage for automatic resource cleanup.

    Attributes:
        tool_open_flag (bool): Whether a J2534 device is currently open.
        channel_open_flag (bool): Whether a protocol channel is connected.
        volts (float): Last read battery voltage.
        transmit_delay (int): Timeout for transmit operations (ms).
        receive_delay (int): Timeout for receive operations (ms).

    Example:
        Using as context manager::

            with J2534Communications(0, "chrys1") as comm:
                vin = comm.read_vin()
                print(f"VIN: {vin}")

        Traditional usage::

            comm = J2534Communications()
            if comm.open_communication(0, "chrys1"):
                response = comm.transmit_and_receive_message([0x3E, 0x00])
                comm.disconnect()
                comm.close()
    """

    def __init__(
        self,
        device_index: Optional[int] = None,
        connection_name: Optional[str] = None
    ):
        """
        Initialize J2534Communications instance.

        Args:
            device_index: Optional device index to auto-connect on context entry.
                If provided along with connection_name, will auto-connect when
                used as context manager.
            connection_name: Optional connection profile name (e.g., "chrys1").
                Must be a key in Connections.CHRYSLER_ECU dictionary.
        """
        # Auto-connect parameters for context manager
        self._auto_connect_device_index = device_index
        self._auto_connect_name = connection_name

        # State tracking
        self.tool_index_found = None
        self.loops = None
        self.transmit_delay = 1000
        self.receive_delay = 1000

        self.tool_open_flag = False
        self.channel_open_flag = False

        self.com_found = None
        self.connection_keys = None
        self.volts = None
        self._protocol_string = None  # Fixed typo: was _protcol_string
        self._comm_check = None
        self._mask_id = None
        self._tx_flag = None
        self._tx_id = None
        self._rx_id = None
        self._baud_rate = None
        self._connect_flag = None
        self._protocol = None
        self._ecu_filter = None
        self._channel_id = None
        self._device_id = None
        self._key_name = None
        self.check_characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        # SCI protocol timing parameters
        self._t1_max = None
        self._t2_max = None
        self._t4_max = None
        self._t5_max = None

    def __enter__(self) -> 'J2534Communications':
        """
        Context manager entry - auto-connect if parameters provided.

        Returns:
            J2534Communications: Self for use in with statement.

        Raises:
            ConnectionError: If auto-connect fails.
        """
        if self._auto_connect_device_index is not None and self._auto_connect_name is not None:
            if not self.open_communication(self._auto_connect_device_index,
                                           self._auto_connect_name):
                raise ConnectionError(
                    f"Failed to open J2534 communication with device {self._auto_connect_device_index} "
                    f"using profile '{self._auto_connect_name}'"
                )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Context manager exit - automatically disconnect and close.

        Returns:
            bool: False to propagate any exceptions.
        """
        if self.channel_open_flag:
            self.disconnect()
        if self.tool_open_flag:
            self.close()
        return False

    @staticmethod
    def get_interfaces() -> dict:
        """Enumerate all registered J2534 04.04 Pass-Thru interface DLLs
        Returns:
            dict: A dict mapping display names of any registered J2534
            Pass-Thru DLLs to their absolute filepath.
            The name can be used in user-facing GUI elements to allow
            selection of a particular Pass-Thru device, and filepath can
            be passed to :func:`load_interface` to instantiate a
            :class:`J2534Dll` wrapping the desired DLL.
        """
        j2534_dictionary = {}

        registry_path = r"Software\\Wow6432Node\\PassThruSupport.04.04\\"

        if platform.architecture()[0] == "32bit":
            registry_path = r"Software\\PassThruSupport.04.04\\"

        base_key = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, registry_path)
        count = winreg.QueryInfoKey(base_key)[0]

        for i in range(count):
            device_key = winreg.OpenKeyEx(base_key, winreg.EnumKey(base_key, i))
            name = winreg.QueryValueEx(device_key, "Name")[0]
            function_library = winreg.QueryValueEx(device_key, "FunctionLibrary")[0]
            j2534_dictionary[name] = function_library

        return j2534_dictionary

    def clear_rx(self):
        return J2534.clear_receive_buffer(self._channel_id)

    def clear_tx(self):
        return J2534.clear_transmit_buffer(self._channel_id)

    @staticmethod
    def numbered_tool_list():
        # this will print list of j2534 devices with there index number next to them...
        try:
            devices = J2534.get_list_j2534_devices()
            for index, device in enumerate(devices):
                if 'Error:' in device[0]:
                    print(device[0])
                    return True
                print(f'{index} = {device[0]}')
            return True
        except Exception as e:
            print(f'Error: {e}')
            raise e  # raise the exception to let the caller handle it

    @staticmethod
    def tool_list():
        try:
            return J2534.get_list_j2534_devices()
        except Exception as e:
            print(f'Error: {e}')
            return print(f'Error: tool list')

    def tool_info(self):
        try:
            return J2534.pt_read_version(self._device_id)
        except Exception as e:
            print(f'Error: {e}')
            return print(f'Error: tool info')

    def check_volts(self):
        self.volts = J2534.read_battery_volts(self._device_id)
        return self.volts if self.volts and 11.0 < self.volts < 14.7 else False

    def close(self) -> bool:
        self.tool_open_flag = False
        J2534.pt_close(self._device_id)
        return True

    def disconnect(self) -> bool:
        # pt_close close open channel to j2534 tool.
        if not J2534.pt_disconnect(self._channel_id):
            return False
        # set flag to false after channel is closed
        self.channel_open_flag = False
        return True

    def _build_connection_library(self, library_name: str) -> bool:
        """
        Load connection parameters from the Connections dictionary.

        Args:
            library_name: Key name in Connections.CHRYSLER_ECU dictionary.

        Returns:
            bool: True if parameters loaded successfully, False otherwise.
        """
        param = Connections.CHRYSLER_ECU.get(library_name, None)
        if param is None:
            return False

        self._key_name = param.name
        self.transmit_delay = param.tx_delay
        self.receive_delay = param.rx_delay
        self._protocol_string = param.protocol_name  # Fixed typo
        self._protocol = param.protocol_id
        self._connect_flag = param.connect_flag
        self._baud_rate = param.baud_rate
        self._mask_id = param.mask
        self._rx_id = param.rx_id
        self._tx_id = param.tx_id
        self._tx_flag = param.tx_flag
        self._comm_check = param.comm_check

        # SCI protocol timing parameters
        if self._protocol in (7, 8, 9, 10):
            self._t1_max = param.t1_max
            self._t2_max = param.t2_max
            self._t4_max = param.t4_max
            self._t5_max = param.t5_max

        return True

    def open_j2534_interface(self, index_of_tool: int) -> bool:
        try:
            if self.tool_open_flag:  # if tool is already open no need to try to open again.
                return True
            J2534.set_j2534_device_to_connect(index_of_tool)  # set device index number to open connection to.

            self._device_id = J2534.pt_open()  # open connection to j2534 tool this will return device id number...
            if self._device_id is False:
                return False

            if not self.check_volts():  # if voltage is not within range return False.
                return False

            self.tool_open_flag = True  # if tool opens successfully set flag.
            return True
        except Exception as e:
            return False

    def establish_connection(self) -> bool:
        try:
            # pt_connect opens channel to selected communication protocol if successful will return channel id.
            self._channel_id = J2534.pt_connect(self._device_id, self._protocol, self._connect_flag, self._baud_rate)

            if not self._channel_id:  # if pt_connect is not successful return False.
                self.channel_open_flag = False  # if channel id is not returned set flag to False.
                return False

            self.channel_open_flag = True  # if channel id is returned set flag to True.
            return True
        except Exception as e:
            return False

    def _tmax_delays(self) -> bool:
        # set inter frame rate delays if it pertains to this protocol.
        if self._protocol in [7, 8, 9, 10]:
            tmax = [self._t1_max, self._t2_max, self._t4_max, self._t5_max]
            for cnt, x in enumerate(tmax, start=26):
                if x:
                    J2534.pt_set_config(self._channel_id, [[cnt, x]])
        return True

    def _set_ecu_filter(self):
        # pt_start_ecu_filter set filters of tx and rx id only allow the id's of choice to be read.
        self._ecu_filter = J2534.pt_start_ecu_filter(
            self._channel_id,
            self._protocol,  # communication protocol selected.
            self._mask_id,  # data filter mask selected, this pertains to data and not the address id.
            self._rx_id,  # rx address that is allowed to be read all other will be ignored
            self._tx_id,  # tx address that is allowed to be read all other will be ignored
            self._tx_flag,  # will set some spec. functions like can frame pad and prog voltage.
        )
        return self._ecu_filter  # returns filter id if successful.

    def open_communication(self, index_of_tool: int, library_name: str) -> bool:
        if not self._build_connection_library(library_name):
            return False

        if not self.open_j2534_interface(index_of_tool):
            return False

        if not self.establish_connection():
            return False

        return self._set_ecu_filter() if self._tmax_delays() else False

    def _transmit_only_can_message(self, data_to_transmit):
        # set message structure for transmit and receive.
        tx = J2534.PassThruMsgBuilder(self._protocol, self._tx_flag)
        # set data in buffer ready to tx.
        tx.set_identifier_and_data(self._tx_id, data_to_transmit)
        # Transmit one message.
        return J2534.pt_write_message(self._channel_id, tx, 1, self.transmit_delay)

    def _receive_only_can_message(self, transmitted_data: List[int], loops: int = 0) -> Union[str, bool]:
        """
        Receive a CAN message response.

        Args:
            transmitted_data: Original transmitted message for response matching.
            loops: Additional read iterations for slow ECUs.

        Returns:
            str: Response hex string on positive response.
            str: NRC description on negative response.
            bool: False on timeout or error.
        """
        rx = J2534.PassThruMsgBuilder(self._protocol, self._tx_flag)

        for _ in range(3 + loops):
            # Read message from buffer (error code 16 = ERR_BUFFER_EMPTY)
            if J2534.pt_read_message(self._channel_id, rx, 1, self.receive_delay) == 16:
                return False

            # RxStatus values:
            # 0 = msg read successfully, 2 = first frame, 9 = tx indication
            # 256 = 29-bit msg success, 258 = 29-bit tx indication
            if rx.RxStatus in (2, 9, 102, 258, 265):
                continue

            # Status 0 or 256 = complete message received
            if rx.RxStatus in (0, 256):
                rx_output = rx.dump_output()
                check_byte = rx_output[8:10]
                error_byte = rx_output[12:14]

                # Handle negative response (7F)
                if check_byte == '7F':
                    if error_byte == '78':  # Response Pending - keep waiting
                        continue
                    # Return NRC description
                    return get_negative_response_description_hex(error_byte)

                # Check for positive response (service ID + 0x40)
                positive_response = f"{transmitted_data[0] + 0x40:02X}"
                if check_byte == positive_response:
                    return rx_output[8:]  # Strip CAN ID prefix

        return False

    def _transmit_and_receive_can_message(
        self,
        data_to_transmit: List[int],
        loops: int = 0
    ) -> Union[str, bool]:
        """
        Transmit a CAN message and receive the response.

        Args:
            data_to_transmit: Message bytes to send.
            loops: Additional read iterations for slow ECUs.

        Returns:
            str: Response hex string on positive response.
            str: NRC description on negative response.
            bool: False on timeout or error.
        """
        tx = J2534.PassThruMsgBuilder(self._protocol, self._tx_flag)
        rx = J2534.PassThruMsgBuilder(self._protocol, self._tx_flag)

        tx.set_identifier_and_data(self._tx_id, data_to_transmit)

        try:
            # Transmit message
            if J2534.pt_write_message(self._channel_id, tx, 1, self.transmit_delay) is False:
                return False

            # Read response with retry loop
            for _ in range(3 + int(loops)):
                read_result = J2534.pt_read_message(self._channel_id, rx, 1, self.receive_delay)
                if read_result == 16:  # ERR_BUFFER_EMPTY
                    return False

                # Skip intermediate frames
                if rx.RxStatus in (2, 9, 102, 258, 265):
                    continue

                # Complete message received
                if rx.RxStatus in (0, 256):
                    rx_output = rx.dump_output()
                    check_byte = rx_output[8:10]
                    error_byte = rx_output[12:14]

                    # Handle Response Pending (0x78)
                    if check_byte == '7F' and error_byte == '78':
                        continue

                    # Handle negative response
                    if check_byte == '7F':
                        return get_negative_response_description_hex(error_byte)

                    # Check for positive response
                    positive_response = f"{data_to_transmit[0] + 0x40:02X}"
                    if check_byte == positive_response:
                        return rx_output[8:]

        except Exception:
            return False

        return False

    def _transmit_and_receive_sci_message(
        self,
        data_to_transmit: List[int]
    ) -> Union[str, bool]:
        """
        Transmit an SCI message and receive the response.

        SCI (Serial Communication Interface) is a Chrysler-specific
        half-duplex serial protocol used in older vehicles.

        Args:
            data_to_transmit: Message bytes to send.

        Returns:
            str: Response hex string on success.
            bool: False on timeout or error.
        """
        tx = J2534.PassThruMsgBuilder(self._protocol, self._tx_flag)
        rx = J2534.PassThruMsgBuilder(self._protocol, self._tx_flag)

        tx.build_transmit_data_block(data_to_transmit)

        if J2534.pt_write_message(self._channel_id, tx, 1, self.transmit_delay) is False:
            return False

        read_result = J2534.pt_read_message(self._channel_id, rx, 1, self.receive_delay)
        if read_result == 16:  # ERR_BUFFER_EMPTY
            return False

        return rx.dump_output() if rx.DataSize > 1 else False

    def transmit_and_receive_message(
        self,
        data_to_transmit: List[int],
        loops: int = 0,
        retries: int = 1,
        timeout_ms: Optional[int] = None
    ) -> Union[str, bool, None]:
        """
        Transmit a diagnostic message and receive the ECU response.

        This is the primary method for UDS communication. It handles both
        CAN-based (ISO15765) and SCI protocols automatically based on
        the current connection profile.

        Args:
            data_to_transmit: Message bytes as list of integers.
                Example: [0x22, 0xF1, 0x90] for Read VIN.
            loops: Additional read loops for slow-responding ECUs.
            retries: Number of retry attempts on failure (default: 1).
            timeout_ms: Override receive timeout in milliseconds.
                If None, uses the connection profile's default.

        Returns:
            str: Response data as hex string on positive response.
            str: Error description on negative response (7F xx).
            bool: False on communication failure or timeout.
            None: If protocol not set or unsupported.

        Example:
            >>> response = comm.transmit_and_receive_message([0x3E, 0x00])
            >>> if response and response.startswith("7E"):
            ...     print("Tester Present successful")
        """
        # Save and optionally override timeout
        original_timeout = self.receive_delay
        if timeout_ms is not None:
            self.receive_delay = timeout_ms

        try:
            for attempt in range(max(1, retries)):
                if self._protocol == 6:  # ISO15765 (CAN)
                    result = self._transmit_and_receive_can_message(data_to_transmit, loops)
                elif self._protocol in (7, 8, 9, 10):  # SCI protocols
                    result = self._transmit_and_receive_sci_message(data_to_transmit)
                else:
                    return None  # Unsupported protocol

                # Return on success or non-retryable error
                if result is not False and result is not None:
                    return result

                # Small delay between retries
                if attempt < retries - 1:
                    time.sleep(0.1)

            return False
        finally:
            self.receive_delay = original_timeout

    def transmit_only(self, data_to_transmit: List[int]) -> bool:
        """
        Transmit a message without waiting for response.

        Useful for broadcast messages or when response is not expected.

        Args:
            data_to_transmit: Message bytes as list of integers.

        Returns:
            bool: True if transmission successful, False otherwise.
        """
        if self._protocol == 6:  # ISO15765 (CAN)
            return self._transmit_only_can_message(data_to_transmit)
        elif self._protocol in (7, 8, 9, 10):  # SCI protocols
            # SCI is inherently half-duplex, use tx/rx method
            return self._transmit_and_receive_sci_message(data_to_transmit) is not False
        return False

    def receive_only(self, transmitted_data: List[int], loops: int = 0) -> Union[str, bool]:
        """
        Receive a response without transmitting.

        Useful for listening to multi-frame responses or bus monitoring.

        Args:
            transmitted_data: The original transmitted message (for response matching).
            loops: Additional read loops for slow-responding ECUs.

        Returns:
            str: Response data as hex string on success.
            bool: False on failure or timeout.
        """
        if self._protocol == 6:  # ISO15765 (CAN)
            return self._receive_only_can_message(transmitted_data, loops)
        elif self._protocol in (7, 8, 9, 10):  # SCI protocols
            # SCI requires transmit to receive
            return self._transmit_and_receive_sci_message(transmitted_data)
        return False

    def tool_search(self):
        # search for index of connected j2534 device...
        for x in range(20):  # loop through all j2534 devices found in registry...

            if self.open_j2534_interface(x):  # test all indexes of tools to see which one responds...

                self.tool_index_found = x  # save index of tool if it responds...

                self.close()  # close connection of tool...

                return self.tool_index_found  # return saved index of tool that responded...

        return False

    def auto_connect(self) -> Union[List, bool]:
        """
        Automatically discover and connect to a vehicle ECU.

        This method searches for a connected J2534 device, then tries
        each known connection profile until successful communication
        is established.

        Returns:
            list: [device_index, connection_key, profile_name, tool_name,
                   firmware_version, dll_version] on success.
            bool: False if no connection could be established.

        Example:
            >>> comm = J2534Communications()
            >>> result = comm.auto_connect()
            >>> if result:
            ...     print(f"Connected via {result[2]}")
        """
        try:
            tool_index = self.tool_search()
            if tool_index is False:
                return False

            connection_keys = list(Connections.CHRYSLER_ECU.keys())[:7]

            for connection_key in connection_keys:
                if self.open_communication(tool_index, connection_key):
                    tool_info = self.tool_info()

                    if self.transmit_and_receive_message(self._comm_check):
                        print(f'Found and connected to {tool_info[0]}')
                        print(f'Communication successful with {self._key_name}')
                        self.com_found = connection_key

                        return [tool_index, connection_key, self._key_name,
                                tool_info[0], tool_info[1], tool_info[2]]

                self.close()

            return False
        except Exception:
            return False

    # =========================================================================
    # UDS Service Wrappers - Common Diagnostic Services
    # =========================================================================

    def read_vin(self) -> Optional[str]:
        """
        Read Vehicle Identification Number (VIN).

        Sends UDS ReadDataByIdentifier (0x22) for DID 0xF190.

        Returns:
            str: 17-character VIN string on success.
            None: On failure or if VIN cannot be decoded.

        Example:
            >>> vin = comm.read_vin()
            >>> print(f"VIN: {vin}")
            VIN: 1G1YY22G965100001
        """
        response = self.transmit_and_receive_message([0x22, 0xF1, 0x90])
        if response and isinstance(response, str) and response.startswith("62"):
            try:
                # Skip 62F190 header (6 chars), decode ASCII
                hex_data = response[6:]
                return bytes.fromhex(hex_data).decode('ascii', errors='ignore').strip()
            except (ValueError, UnicodeDecodeError):
                return None
        return None

    def read_ecu_id(self, did: int = 0x87) -> Optional[str]:
        """
        Read ECU Identification data.

        Args:
            did: Data Identifier to read (default 0x87 for ECU ID).

        Returns:
            str: Hex string of ECU ID data on success.
            None: On failure.
        """
        response = self.transmit_and_receive_message([0x1A, did])
        if response and isinstance(response, str) and response.startswith("5A"):
            return response[4:]  # Skip 5A xx header
        return None

    def read_data_by_identifier(self, did_high: int, did_low: int) -> Optional[str]:
        """
        Read data from ECU using ReadDataByIdentifier (0x22).

        Args:
            did_high: High byte of Data Identifier.
            did_low: Low byte of Data Identifier.

        Returns:
            str: Response data on success (without header).
            None: On failure.

        Example:
            >>> # Read ECU Serial Number (DID 0xF18C)
            >>> serial = comm.read_data_by_identifier(0xF1, 0x8C)
        """
        response = self.transmit_and_receive_message([0x22, did_high, did_low])
        if response and isinstance(response, str) and response.startswith("62"):
            return response[6:]  # Skip 62 xx xx header
        return None

    def tester_present(self, suppress_response: bool = False) -> bool:
        """
        Send TesterPresent to keep diagnostic session alive.

        Args:
            suppress_response: If True, uses sub-function 0x80 to suppress
                ECU response. Default False.

        Returns:
            bool: True if ECU responded positively (or message sent for suppressed).

        Example:
            >>> while working:
            ...     comm.tester_present()
            ...     time.sleep(2)
        """
        sub_function = 0x80 if suppress_response else 0x00
        response = self.transmit_and_receive_message([0x3E, sub_function])

        if suppress_response:
            return response is not False
        return response is not None and isinstance(response, str) and "7E" in response

    def start_diagnostic_session(self, session_type: int = 0x01) -> bool:
        """
        Start a diagnostic session.

        Args:
            session_type: Session type to start:
                0x01 = Default Session
                0x02 = Programming Session
                0x03 = Extended Diagnostic Session

        Returns:
            bool: True if session started successfully.

        Example:
            >>> comm.start_diagnostic_session(0x03)  # Extended session
            True
        """
        response = self.transmit_and_receive_message([0x10, session_type])
        return (response is not None and
                isinstance(response, str) and
                response.startswith("50"))

    def read_dtc_codes(self, status_mask: int = 0xFF) -> List[str]:
        """
        Read Diagnostic Trouble Codes (DTCs).

        Sends UDS ReportDTCByStatusMask (0x19 0x02).

        Args:
            status_mask: DTC status mask filter (default 0xFF = all).

        Returns:
            list: List of DTC strings in format "P0123" or hex strings.
                  Empty list on failure or if no DTCs present.

        Example:
            >>> dtcs = comm.read_dtc_codes()
            >>> for dtc in dtcs:
            ...     print(f"DTC: {dtc}")
        """
        response = self.transmit_and_receive_message([0x19, 0x02, status_mask])
        if response and isinstance(response, str) and response.startswith("59"):
            return self._parse_dtc_response(response)
        return []

    def _parse_dtc_response(self, response: str) -> List[str]:
        """Parse DTC response into list of DTC codes."""
        dtcs = []
        # Skip 5902 xx header (6 chars), each DTC is 6 chars (3 bytes)
        dtc_data = response[6:]
        for i in range(0, len(dtc_data) - 5, 6):
            dtc_bytes = dtc_data[i:i+6]
            if len(dtc_bytes) >= 4:
                dtcs.append(dtc_bytes[:4])  # First 4 chars are DTC code
        return dtcs

    def clear_dtc_codes(self) -> bool:
        """
        Clear all stored Diagnostic Trouble Codes.

        Sends UDS ClearDiagnosticInformation (0x14).

        Returns:
            bool: True if DTCs cleared successfully.
        """
        response = self.transmit_and_receive_message([0x14, 0xFF, 0xFF, 0xFF])
        return (response is not None and
                isinstance(response, str) and
                response.startswith("54"))

    def security_access_request_seed(self, level: int = 0x01) -> Optional[str]:
        """
        Request security seed for Security Access.

        Args:
            level: Security level (odd number, typically 0x01, 0x03, etc.).

        Returns:
            str: Seed bytes as hex string on success.
            None: On failure or if security already unlocked.

        Example:
            >>> seed = comm.security_access_request_seed(0x01)
            >>> if seed:
            ...     key = calculate_key(seed)  # Your algorithm
            ...     comm.security_access_send_key(0x01, key)
        """
        response = self.transmit_and_receive_message([0x27, level])
        if response and isinstance(response, str) and response.startswith("67"):
            return response[4:]  # Return seed bytes (skip 67 xx header)
        return None

    def security_access_send_key(self, level: int, key_bytes: List[int]) -> bool:
        """
        Send security key for Security Access.

        Args:
            level: Security level (same as used in seed request).
            key_bytes: Calculated key as list of byte values.

        Returns:
            bool: True if key accepted and security unlocked.
        """
        response = self.transmit_and_receive_message([0x27, level + 1] + key_bytes)
        return (response is not None and
                isinstance(response, str) and
                response.startswith("67"))

    def ecu_reset(self, reset_type: int = 0x01) -> bool:
        """
        Request ECU reset.

        Args:
            reset_type: Type of reset:
                0x01 = Hard Reset
                0x02 = Key Off/On Reset
                0x03 = Soft Reset

        Returns:
            bool: True if reset request accepted.
        """
        response = self.transmit_and_receive_message([0x11, reset_type])
        return (response is not None and
                isinstance(response, str) and
                response.startswith("51"))

    def scan_all_protocols(self, device_index: int = 0) -> List[Dict[str, Any]]:
        """
        Scan all known protocols to find responding ECUs.

        This method tries each connection profile in sequence and
        records which ones receive a valid response.

        Args:
            device_index: J2534 device index to use.

        Returns:
            list: List of dicts with responding protocols:
                  [{'connection_key': str, 'name': str, 'protocol': str, 'response': str}, ...]

        Example:
            >>> protocols = comm.scan_all_protocols()
            >>> for p in protocols:
            ...     print(f"Found: {p['name']}")
        """
        results = []
        all_configs = list(Connections.CHRYSLER_ECU.items())

        for key, config in all_configs:
            try:
                if self.open_communication(device_index, key):
                    response = self.transmit_and_receive_message(config.communication_check)
                    if response and isinstance(response, str):
                        results.append({
                            'connection_key': key,
                            'name': config.name,
                            'protocol': config.protocol_name,
                            'response': response
                        })
                    self.disconnect()
            except Exception:
                pass
            finally:
                if self.tool_open_flag:
                    self.close()

        return results


# =============================================================================
# Module-Level Convenience Functions
# =============================================================================

def quick_connect(
    device_index: int = 0,
    connection_name: str = "chrys1"
) -> Optional[J2534Communications]:
    """
    Quick one-line connection to a J2534 device.

    Creates a J2534Communications instance and opens communication
    with the specified device and connection profile.

    Args:
        device_index: Index of J2534 device (default 0 = first device).
        connection_name: Connection profile key (default "chrys1").

    Returns:
        J2534Communications: Connected instance on success.
        None: On connection failure.

    Example:
        >>> from AutoJ2534 import quick_connect
        >>> comm = quick_connect()
        >>> if comm:
        ...     print(comm.read_vin())
        ...     comm.close()
    """
    comm = J2534Communications()
    if comm.open_communication(device_index, connection_name):
        return comm
    return None


def auto_detect_connect() -> tuple[Optional[J2534Communications], Optional[Dict[str, Any]]]:
    """
    Auto-detect and connect to the first responding ECU.

    This function searches for a connected J2534 device and tries
    all known connection profiles until successful communication.

    Returns:
        tuple: (J2534Communications, connection_info_dict) on success.
               (None, None) on failure.

    Example:
        >>> from AutoJ2534 import auto_detect_connect
        >>> comm, info = auto_detect_connect()
        >>> if comm:
        ...     print(f"Connected to {info['tool_name']}")
        ...     print(f"VIN: {comm.read_vin()}")
    """
    comm = J2534Communications()
    result = comm.auto_connect()
    if result:
        return comm, {
            'device_index': result[0],
            'connection_key': result[1],
            'connection_name': result[2],
            'tool_name': result[3],
            'firmware_version': result[4],
            'dll_version': result[5]
        }
    return None, None


# Legacy global instance for backward compatibility
j2534_communication = J2534Communications()
