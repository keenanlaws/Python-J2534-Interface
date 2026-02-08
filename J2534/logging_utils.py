"""
J2534 Logging Utilities
=======================

This module provides logging utilities for the J2534 library. It integrates
with the configuration module to provide conditional debug output and
standardized log message formatting.

The logging system is designed to be:
- Non-intrusive: When disabled, logging has minimal performance impact
- Informative: Debug messages include context like function names, parameters
- Configurable: Output can be directed to console, files, or custom handlers

Usage:
    The logging functions are typically called internally by other J2534
    modules. You generally don't need to call them directly, but you can
    use them for custom extensions.

Example:
    Using debug logging in custom code::

        from J2534.logging_utils import debug_log, debug_hex_dump
        from J2534.config import j2534_config

        # Enable debug mode
        j2534_config.enable_debug()

        # Log a debug message
        debug_log("Custom operation started", function_name="my_function")

        # Log hex data
        debug_hex_dump(message_data, "Received message")

Example:
    Customizing log output::

        import logging
        from J2534.config import j2534_config

        # Add a file handler
        file_handler = logging.FileHandler('j2534_debug.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        j2534_config.logger.addHandler(file_handler)

        # Now enable debug mode
        j2534_config.enable_debug()

Author: J2534-API Contributors
License: MIT
Version: 2.0.0
"""

from typing import Optional, Union, List, Any
import ctypes

from .config import j2534_config


def debug_log(
    message: str,
    function_name: Optional[str] = None,
    level: str = "debug"
) -> None:
    """
    Log a debug message if debug mode is enabled.

    This function checks the current configuration before logging to
    minimize overhead when debug mode is disabled. When enabled, it
    formats the message with optional context information.

    Args:
        message: The message to log. Should be a human-readable description
            of what is happening or what was observed.
        function_name: Optional name of the function generating this log.
            When provided, it's prepended to the message for context.
        level: The log level to use. Options are:
            - "debug": Standard debug information (default)
            - "info": Informational messages
            - "warning": Warning conditions
            - "error": Error conditions

    Example:
        >>> from J2534.logging_utils import debug_log
        >>> from J2534.config import j2534_config
        >>>
        >>> j2534_config.enable_debug()
        >>> debug_log("Opening device", function_name="pt_open")
        2024-01-15 10:30:45 - J2534 - DEBUG - pt_open: Opening device

    Note:
        When debug mode is disabled, this function returns immediately
        without any logging overhead.
    """
    # Early exit if debug is disabled - minimal overhead
    if not j2534_config.debug_enabled:
        return

    # Format message with function name if provided
    if function_name:
        formatted_message = f"{function_name}: {message}"
    else:
        formatted_message = message

    # Log at appropriate level
    logger = j2534_config.logger
    if level == "debug":
        logger.debug(formatted_message)
    elif level == "info":
        logger.info(formatted_message)
    elif level == "warning":
        logger.warning(formatted_message)
    elif level == "error":
        logger.error(formatted_message)
    else:
        logger.debug(formatted_message)


def debug_log_function_entry(
    function_name: str,
    **parameters: Any
) -> None:
    """
    Log entry into a function with its parameters.

    This function is designed to be called at the beginning of J2534 API
    functions to log when they are called and what parameters were passed.

    Args:
        function_name: The name of the function being entered.
        **parameters: Keyword arguments representing the function parameters
            and their values. These will be formatted and included in the log.

    Example:
        >>> debug_log_function_entry(
        ...     "pt_connect",
        ...     device_id=1,
        ...     protocol_id=6,
        ...     flags=0,
        ...     baud_rate=500000
        ... )
        # Output: pt_connect: Called with device_id=1, protocol_id=6, flags=0, baud_rate=500000
    """
    if not j2534_config.debug_enabled:
        return

    # Format parameters
    if parameters:
        param_strings = [f"{key}={value}" for key, value in parameters.items()]
        param_text = ", ".join(param_strings)
        message = f"Called with {param_text}"
    else:
        message = "Called"

    debug_log(message, function_name=function_name)


def debug_log_function_exit(
    function_name: str,
    return_value: Any = None,
    success: bool = True,
    error_code: Optional[int] = None
) -> None:
    """
    Log exit from a function with its return value.

    This function is designed to be called at the end of J2534 API functions
    to log the result of the operation.

    Args:
        function_name: The name of the function that is returning.
        return_value: The value being returned. Will be formatted appropriately
            based on its type.
        success: Whether the function succeeded. Affects log level.
        error_code: Optional J2534 error code if the function failed.

    Example:
        >>> debug_log_function_exit(
        ...     "pt_open",
        ...     return_value=1,
        ...     success=True
        ... )
        # Output: pt_open: Returned 1 (success)

        >>> debug_log_function_exit(
        ...     "pt_open",
        ...     return_value=False,
        ...     success=False,
        ...     error_code=0x08
        ... )
        # Output: pt_open: Failed with error code 0x08
    """
    if not j2534_config.debug_enabled:
        return

    if success:
        message = f"Returned {return_value}"
        debug_log(message, function_name=function_name)
    else:
        if error_code is not None:
            message = f"Failed with error code 0x{error_code:02X}"
        else:
            message = f"Failed, returned {return_value}"
        debug_log(message, function_name=function_name, level="warning")


def debug_hex_dump(
    data: Union[bytes, bytearray, List[int], ctypes.Array],
    label: Optional[str] = None,
    bytes_per_line: int = 16
) -> None:
    """
    Log a hex dump of binary data.

    This function formats binary data as a hexadecimal dump, similar to
    the output of tools like `xxd` or `hexdump`. This is useful for
    debugging message contents.

    The output format is::

        0000 | 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F | ................
        0010 | 10 11 12 13 14 15 16 17 18 19 1A 1B 1C 1D 1E 1F | ................

    Args:
        data: The binary data to dump. Can be bytes, bytearray, list of
            integers, or a ctypes array.
        label: Optional label to display before the hex dump.
        bytes_per_line: Number of bytes to display per line. Default is 16.

    Example:
        >>> data = bytes([0x7E, 0x00, 0x22, 0xF1, 0x90])
        >>> debug_hex_dump(data, "Transmit message")
        # Output:
        # Transmit message (5 bytes):
        # 0000 | 7E 00 22 F1 90                                  | ~."..
    """
    if not j2534_config.debug_enabled:
        return

    # Convert ctypes array to list if needed
    if hasattr(data, '_length_'):
        # It's a ctypes array
        data = list(data[:])
    elif isinstance(data, (bytes, bytearray)):
        data = list(data)

    # Build header
    if label:
        header = f"{label} ({len(data)} bytes):"
    else:
        header = f"Data ({len(data)} bytes):"

    lines = [header]

    # Build hex dump lines
    for offset in range(0, len(data), bytes_per_line):
        # Get the bytes for this line
        line_bytes = data[offset:offset + bytes_per_line]

        # Format offset
        offset_str = f"{offset:04X}"

        # Format hex values
        hex_parts = []
        for byte_value in line_bytes:
            hex_parts.append(f"{byte_value:02X}")
        # Pad to full line width
        while len(hex_parts) < bytes_per_line:
            hex_parts.append("  ")
        hex_str = " ".join(hex_parts)

        # Format ASCII representation
        ascii_parts = []
        for byte_value in line_bytes:
            if 0x20 <= byte_value <= 0x7E:
                ascii_parts.append(chr(byte_value))
            else:
                ascii_parts.append(".")
        ascii_str = "".join(ascii_parts)

        # Combine into line
        line = f"{offset_str} | {hex_str} | {ascii_str}"
        lines.append(line)

    # Log the complete dump
    for line in lines:
        j2534_config.logger.debug(line)


def debug_log_message(
    message_structure: Any,
    direction: str = "received",
    label: Optional[str] = None
) -> None:
    """
    Log a J2534 message structure with all its fields.

    This function formats a PassThruMessageStructure (or similar) for
    debug output, showing all fields and a hex dump of the data.

    Args:
        message_structure: The message structure to log. Should have
            attributes like ProtocolID, RxStatus, TxFlags, DataSize, Data.
        direction: Either "received" or "transmitted" to indicate the
            direction of the message.
        label: Optional additional label for the message.

    Example:
        >>> debug_log_message(rx_message, direction="received")
        # Output:
        # Received message:
        #   ProtocolID: 6 (ISO15765)
        #   RxStatus: 0
        #   Timestamp: 12345678
        #   DataSize: 8
        #   Data:
        #   0000 | 7E 00 62 F1 90 31 32 33 | ~.b..123
    """
    if not j2534_config.debug_enabled:
        return

    # Build header
    if label:
        header = f"{label} ({direction}):"
    else:
        header = f"{direction.capitalize()} message:"

    j2534_config.logger.debug(header)

    # Log message fields
    if hasattr(message_structure, 'ProtocolID'):
        protocol_id = message_structure.ProtocolID
        protocol_names = {
            1: "J1850VPW", 2: "J1850PWM", 3: "ISO9141",
            4: "ISO14230", 5: "CAN", 6: "ISO15765",
            7: "SCI_A_ENGINE", 8: "SCI_A_TRANS",
            9: "SCI_B_ENGINE", 10: "SCI_B_TRANS"
        }
        protocol_name = protocol_names.get(protocol_id, "Unknown")
        j2534_config.logger.debug(f"  ProtocolID: {protocol_id} ({protocol_name})")

    if hasattr(message_structure, 'RxStatus'):
        j2534_config.logger.debug(f"  RxStatus: 0x{message_structure.RxStatus:04X}")

    if hasattr(message_structure, 'TxFlags'):
        j2534_config.logger.debug(f"  TxFlags: 0x{message_structure.TxFlags:04X}")

    if hasattr(message_structure, 'Timestamp'):
        j2534_config.logger.debug(f"  Timestamp: {message_structure.Timestamp}")

    if hasattr(message_structure, 'DataSize'):
        data_size = message_structure.DataSize
        j2534_config.logger.debug(f"  DataSize: {data_size}")

        # Log data if present
        if data_size > 0 and hasattr(message_structure, 'Data'):
            j2534_config.logger.debug("  Data:")
            # Indent the hex dump
            data_bytes = list(message_structure.Data[:data_size])
            for offset in range(0, len(data_bytes), 16):
                line_bytes = data_bytes[offset:offset + 16]
                hex_str = " ".join(f"{b:02X}" for b in line_bytes)
                hex_str = hex_str.ljust(48)  # Pad to 16 bytes * 3 chars
                ascii_str = "".join(
                    chr(b) if 0x20 <= b <= 0x7E else "."
                    for b in line_bytes
                )
                j2534_config.logger.debug(f"    {offset:04X} | {hex_str} | {ascii_str}")


def format_error_code(error_code: int) -> str:
    """
    Format a J2534 error code as a human-readable string.

    This function converts a numeric error code to a descriptive string
    that includes both the hex value and the error name.

    Args:
        error_code: The J2534 error code to format.

    Returns:
        A formatted string like "0x08 (ERR_DEVICE_NOT_CONNECTED)".

    Example:
        >>> format_error_code(0x08)
        '0x08 (ERR_DEVICE_NOT_CONNECTED)'
    """
    error_names = {
        0x00: "STATUS_NOERROR",
        0x01: "ERR_NOT_SUPPORTED",
        0x02: "ERR_INVALID_CHANNEL_ID",
        0x03: "ERR_INVALID_PROTOCOL_ID",
        0x04: "ERR_NULL_PARAMETER",
        0x05: "ERR_INVALID_IOCTL_VALUE",
        0x06: "ERR_INVALID_FLAGS",
        0x07: "ERR_FAILED",
        0x08: "ERR_DEVICE_NOT_CONNECTED",
        0x09: "ERR_TIMEOUT",
        0x0A: "ERR_INVALID_MSG",
        0x0B: "ERR_INVALID_TIME_INTERVAL",
        0x0C: "ERR_EXCEEDED_LIMIT",
        0x0D: "ERR_INVALID_MSG_ID",
        0x0E: "ERR_DEVICE_IN_USE",
        0x0F: "ERR_INVALID_IOCTL_ID",
        0x10: "ERR_BUFFER_EMPTY",
        0x11: "ERR_BUFFER_FULL",
        0x12: "ERR_BUFFER_OVERFLOW",
        0x13: "ERR_PIN_INVALID",
        0x14: "ERR_CHANNEL_IN_USE",
        0x15: "ERR_MSG_PROTOCOL_ID",
        0x16: "ERR_INVALID_FILTER_ID",
        0x17: "ERR_NO_FLOW_CONTROL",
        0x18: "ERR_NOT_UNIQUE",
        0x19: "ERR_INVALID_BAUDRATE",
        0x1A: "ERR_INVALID_DEVICE_ID",
    }

    error_name = error_names.get(error_code, "UNKNOWN_ERROR")
    return f"0x{error_code:02X} ({error_name})"


def format_protocol_id(protocol_id: int) -> str:
    """
    Format a J2534 protocol ID as a human-readable string.

    Args:
        protocol_id: The J2534 protocol ID to format.

    Returns:
        A formatted string like "6 (ISO15765)".

    Example:
        >>> format_protocol_id(6)
        '6 (ISO15765)'
    """
    protocol_names = {
        1: "J1850VPW",
        2: "J1850PWM",
        3: "ISO9141",
        4: "ISO14230",
        5: "CAN",
        6: "ISO15765",
        7: "SCI_A_ENGINE",
        8: "SCI_A_TRANS",
        9: "SCI_B_ENGINE",
        10: "SCI_B_TRANS",
    }

    protocol_name = protocol_names.get(protocol_id, "Unknown")
    return f"{protocol_id} ({protocol_name})"


def format_ioctl_id(ioctl_id: int) -> str:
    """
    Format a J2534 IOCTL ID as a human-readable string.

    Args:
        ioctl_id: The J2534 IOCTL command ID to format.

    Returns:
        A formatted string like "0x01 (GET_CONFIG)".

    Example:
        >>> format_ioctl_id(0x03)
        '0x03 (READ_VBATT)'
    """
    ioctl_names = {
        0x01: "GET_CONFIG",
        0x02: "SET_CONFIG",
        0x03: "READ_VBATT",
        0x04: "FIVE_BAUD_INIT",
        0x05: "FAST_INIT",
        0x07: "CLEAR_TX_BUFFER",
        0x08: "CLEAR_RX_BUFFER",
        0x09: "CLEAR_PERIODIC_MSGS",
        0x0A: "CLEAR_MSG_FILTERS",
        0x0B: "CLEAR_FUNCT_MSG_LOOKUP_TABLE",
        0x0C: "ADD_TO_FUNCT_MSG_LOOKUP_TABLE",
        0x0D: "DELETE_FROM_FUNCT_MSG_LOOKUP_TABLE",
        0x0E: "READ_PROG_VOLTAGE",
    }

    ioctl_name = ioctl_names.get(ioctl_id, "Unknown")
    return f"0x{ioctl_id:02X} ({ioctl_name})"
