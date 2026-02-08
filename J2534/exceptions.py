"""
J2534 Exception Classes
=======================

This module defines custom exception classes for the J2534 library.
These exceptions provide detailed error information when the library
is configured to raise exceptions (j2534_config.enable_exceptions()).

Exception Hierarchy:
    All J2534 exceptions inherit from J2534Error, which inherits from
    the built-in Exception class. This allows you to catch all J2534
    errors with a single except clause, or catch specific error types.

    Exception Hierarchy Diagram::

        Exception (built-in)
            |
        J2534Error (base class for all J2534 errors)
            |
            +-- J2534OpenError (device open failed)
            |
            +-- J2534CloseError (device close failed)
            |
            +-- J2534ConnectError (channel connection failed)
            |
            +-- J2534DisconnectError (channel disconnect failed)
            |
            +-- J2534ReadError (message read failed)
            |
            +-- J2534WriteError (message write failed)
            |
            +-- J2534FilterError (filter operation failed)
            |
            +-- J2534IoctlError (IOCTL operation failed)
            |
            +-- J2534RegistryError (registry access failed)
            |
            +-- J2534ConfigurationError (invalid configuration)

Error Codes:
    J2534 API defines standard error codes. Each exception includes the
    error code when available, allowing you to determine the specific
    cause of the failure. See the ERROR_CODE_DESCRIPTIONS dictionary
    for human-readable descriptions of each code.

Example:
    Catching specific exceptions::

        from J2534.exceptions import J2534OpenError, J2534ConnectError

        try:
            device_id = pt_open()
            channel_id = pt_connect(device_id, protocol, flags, baud)
        except J2534OpenError as error:
            print(f"Could not open device: {error}")
            print(f"Error code: {error.error_code}")
        except J2534ConnectError as error:
            print(f"Could not connect channel: {error}")

Example:
    Catching all J2534 errors::

        from J2534.exceptions import J2534Error

        try:
            # ... J2534 operations ...
        except J2534Error as error:
            print(f"J2534 operation failed: {error}")

Author: J2534-API Contributors
License: MIT
Version: 2.0.0
"""

from typing import Optional, Dict


# =============================================================================
# Error Code Definitions
# =============================================================================

# SAE J2534 API Error Codes
# These codes are defined in the J2534 specification and returned by
# PassThru functions when errors occur.

ERROR_CODE_NO_ERROR: int = 0x00
"""Operation completed successfully (no error)."""

ERROR_CODE_NOT_SUPPORTED: int = 0x01
"""
Function or feature not supported.
The requested operation is not implemented by this device or DLL.
"""

ERROR_CODE_INVALID_CHANNEL_ID: int = 0x02
"""
Invalid channel ID.
The specified channel ID was not returned by a successful PassThruConnect call,
or the channel has already been disconnected.
"""

ERROR_CODE_INVALID_PROTOCOL_ID: int = 0x03
"""
Invalid protocol ID.
The protocol ID is not recognized or not supported by this device.
"""

ERROR_CODE_NULL_PARAMETER: int = 0x04
"""
NULL parameter.
A required pointer parameter was NULL when a valid pointer was expected.
"""

ERROR_CODE_INVALID_IOCTL_VALUE: int = 0x05
"""
Invalid IOCTL value.
The IOCTL ID parameter is not recognized.
"""

ERROR_CODE_INVALID_FLAGS: int = 0x06
"""
Invalid flags.
The flags parameter contains an invalid value for this operation.
"""

ERROR_CODE_FAILED: int = 0x07
"""
Operation failed.
The operation could not be completed. Check the device connection.
"""

ERROR_CODE_DEVICE_NOT_CONNECTED: int = 0x08
"""
Device not connected.
No J2534 device is connected or the device was disconnected.
"""

ERROR_CODE_TIMEOUT: int = 0x09
"""
Timeout.
The operation did not complete within the specified timeout period.
"""

ERROR_CODE_INVALID_MSG: int = 0x0A
"""
Invalid message.
The message structure contains invalid values.
"""

ERROR_CODE_INVALID_TIME_INTERVAL: int = 0x0B
"""
Invalid time interval.
The time interval parameter is outside the valid range.
"""

ERROR_CODE_EXCEEDED_LIMIT: int = 0x0C
"""
Exceeded limit.
A resource limit was exceeded (e.g., too many filters, periodic messages).
"""

ERROR_CODE_INVALID_MSG_ID: int = 0x0D
"""
Invalid message ID.
The message ID was not returned by a successful start operation.
"""

ERROR_CODE_DEVICE_IN_USE: int = 0x0E
"""
Device in use.
The device is already in use by another application.
"""

ERROR_CODE_INVALID_IOCTL_ID: int = 0x0F
"""
Invalid IOCTL ID.
The IOCTL ID is not recognized for this channel type.
"""

ERROR_CODE_BUFFER_EMPTY: int = 0x10
"""
Buffer empty.
The receive buffer is empty; no messages are available.
"""

ERROR_CODE_BUFFER_FULL: int = 0x11
"""
Buffer full.
The transmit buffer is full; cannot queue additional messages.
"""

ERROR_CODE_BUFFER_OVERFLOW: int = 0x12
"""
Buffer overflow.
Messages were lost due to buffer overflow.
"""

ERROR_CODE_PIN_INVALID: int = 0x13
"""
Invalid pin.
The pin number is not valid for this operation.
"""

ERROR_CODE_CHANNEL_IN_USE: int = 0x14
"""
Channel in use.
The requested channel is already connected.
"""

ERROR_CODE_MSG_PROTOCOL_ID: int = 0x15
"""
Message protocol ID mismatch.
The message protocol ID does not match the channel protocol.
"""

ERROR_CODE_INVALID_FILTER_ID: int = 0x16
"""
Invalid filter ID.
The filter ID was not returned by a successful start filter operation.
"""

ERROR_CODE_NO_FLOW_CONTROL: int = 0x17
"""
No flow control.
ISO 15765 channel requires flow control filter before communication.
"""

ERROR_CODE_NOT_UNIQUE: int = 0x18
"""
Not unique.
The filter pattern/mask combination already exists.
"""

ERROR_CODE_INVALID_BAUDRATE: int = 0x19
"""
Invalid baud rate.
The specified baud rate is not supported by the device for this protocol.
"""

ERROR_CODE_INVALID_DEVICE_ID: int = 0x1A
"""
Invalid device ID.
The device ID was not returned by a successful PassThruOpen call,
or the device has already been closed.
"""


# Human-readable descriptions for all error codes
ERROR_CODE_DESCRIPTIONS: Dict[int, str] = {
    ERROR_CODE_NO_ERROR: "No error - operation completed successfully",
    ERROR_CODE_NOT_SUPPORTED: "Function or feature not supported by device",
    ERROR_CODE_INVALID_CHANNEL_ID: "Invalid channel ID - channel not connected or already disconnected",
    ERROR_CODE_INVALID_PROTOCOL_ID: "Invalid protocol ID - protocol not recognized or not supported",
    ERROR_CODE_NULL_PARAMETER: "NULL parameter - required pointer was NULL",
    ERROR_CODE_INVALID_IOCTL_VALUE: "Invalid IOCTL value - parameter value out of range",
    ERROR_CODE_INVALID_FLAGS: "Invalid flags - flags parameter contains invalid value",
    ERROR_CODE_FAILED: "Operation failed - check device connection",
    ERROR_CODE_DEVICE_NOT_CONNECTED: "Device not connected - no device found or device disconnected",
    ERROR_CODE_TIMEOUT: "Timeout - operation did not complete in time",
    ERROR_CODE_INVALID_MSG: "Invalid message - message structure contains invalid values",
    ERROR_CODE_INVALID_TIME_INTERVAL: "Invalid time interval - value outside valid range",
    ERROR_CODE_EXCEEDED_LIMIT: "Exceeded limit - resource limit reached (filters, periodic messages)",
    ERROR_CODE_INVALID_MSG_ID: "Invalid message ID - ID not from successful start operation",
    ERROR_CODE_DEVICE_IN_USE: "Device in use - device opened by another application",
    ERROR_CODE_INVALID_IOCTL_ID: "Invalid IOCTL ID - ID not recognized for this channel",
    ERROR_CODE_BUFFER_EMPTY: "Buffer empty - no messages available in receive buffer",
    ERROR_CODE_BUFFER_FULL: "Buffer full - transmit buffer cannot accept more messages",
    ERROR_CODE_BUFFER_OVERFLOW: "Buffer overflow - messages lost due to overflow",
    ERROR_CODE_PIN_INVALID: "Invalid pin - pin number not valid for this operation",
    ERROR_CODE_CHANNEL_IN_USE: "Channel in use - requested channel already connected",
    ERROR_CODE_MSG_PROTOCOL_ID: "Protocol ID mismatch - message protocol differs from channel",
    ERROR_CODE_INVALID_FILTER_ID: "Invalid filter ID - ID not from successful filter operation",
    ERROR_CODE_NO_FLOW_CONTROL: "No flow control - ISO 15765 requires flow control filter",
    ERROR_CODE_NOT_UNIQUE: "Not unique - filter pattern/mask combination exists",
    ERROR_CODE_INVALID_BAUDRATE: "Invalid baud rate - baud rate not supported for protocol",
    ERROR_CODE_INVALID_DEVICE_ID: "Invalid device ID - device not opened or already closed",
}


def get_error_description(error_code: int) -> str:
    """
    Get a human-readable description for a J2534 error code.

    This function looks up the error code in the ERROR_CODE_DESCRIPTIONS
    dictionary and returns a descriptive string. If the error code is
    not recognized, a generic message is returned.

    Args:
        error_code: The J2534 error code (integer value returned by
            PassThru functions).

    Returns:
        A human-readable description of the error. If the code is not
        recognized, returns "Unknown error code: 0xNN".

    Example:
        >>> from J2534.exceptions import get_error_description
        >>> description = get_error_description(0x08)
        >>> print(description)
        Device not connected - no device found or device disconnected
    """
    if error_code in ERROR_CODE_DESCRIPTIONS:
        return ERROR_CODE_DESCRIPTIONS[error_code]
    return f"Unknown error code: 0x{error_code:02X}"


# =============================================================================
# Base Exception Class
# =============================================================================

class J2534Error(Exception):
    """
    Base exception class for all J2534 errors.

    All J2534-specific exceptions inherit from this class. You can catch
    this exception type to handle any J2534 error, or catch specific
    subclasses for more targeted error handling.

    Attributes:
        message (str): Human-readable description of the error.
        error_code (int or None): The J2534 API error code, if available.
            This is the value returned by the PassThru function.
        function_name (str or None): The name of the J2534 function that
            failed, if known.

    Example:
        Catching all J2534 errors::

            try:
                device_id = pt_open()
                channel_id = pt_connect(device_id, 6, 0, 500000)
            except J2534Error as error:
                print(f"J2534 error: {error}")
                if error.error_code is not None:
                    print(f"Error code: 0x{error.error_code:02X}")
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[int] = None,
        function_name: Optional[str] = None
    ) -> None:
        """
        Initialize a J2534Error exception.

        Args:
            message: Human-readable description of what went wrong.
            error_code: The J2534 API error code (optional). If provided,
                the error description is automatically appended to the message.
            function_name: The name of the J2534 function that failed (optional).
                If provided, it's included in the error message.
        """
        self.message: str = message
        self.error_code: Optional[int] = error_code
        self.function_name: Optional[str] = function_name

        # Build the full error message
        full_message_parts = []

        if function_name:
            full_message_parts.append(f"{function_name}:")

        full_message_parts.append(message)

        if error_code is not None:
            error_description = get_error_description(error_code)
            full_message_parts.append(f"[Error 0x{error_code:02X}: {error_description}]")

        full_message = " ".join(full_message_parts)
        super().__init__(full_message)

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"function_name={self.function_name!r})"
        )


# =============================================================================
# Specific Exception Classes
# =============================================================================

class J2534OpenError(J2534Error):
    """
    Exception raised when PassThruOpen fails.

    This exception indicates that the J2534 device could not be opened.
    Common causes include:
    - No J2534 device connected
    - Device already in use by another application
    - Device driver not installed
    - Invalid device selection

    Example:
        >>> try:
        ...     device_id = pt_open()
        ... except J2534OpenError as error:
        ...     print(f"Could not open device: {error}")
        ...     print(f"Error code: 0x{error.error_code:02X}")
    """

    def __init__(
        self,
        message: str = "Failed to open J2534 device",
        error_code: Optional[int] = None
    ) -> None:
        super().__init__(message, error_code, function_name="PassThruOpen")


class J2534CloseError(J2534Error):
    """
    Exception raised when PassThruClose fails.

    This exception indicates that the J2534 device could not be closed
    properly. This is relatively rare and usually indicates an internal
    error in the device driver.

    Example:
        >>> try:
        ...     pt_close(device_id)
        ... except J2534CloseError as error:
        ...     print(f"Warning: Device close failed: {error}")
    """

    def __init__(
        self,
        message: str = "Failed to close J2534 device",
        error_code: Optional[int] = None
    ) -> None:
        super().__init__(message, error_code, function_name="PassThruClose")


class J2534ConnectError(J2534Error):
    """
    Exception raised when PassThruConnect fails.

    This exception indicates that a communication channel could not be
    established with the vehicle. Common causes include:
    - Invalid protocol for the vehicle
    - Incorrect baud rate
    - Vehicle not powered on
    - Wiring issues between adapter and vehicle

    Attributes:
        protocol_id (int or None): The protocol ID that was requested.
        baud_rate (int or None): The baud rate that was requested.

    Example:
        >>> try:
        ...     channel_id = pt_connect(device_id, 6, 0, 500000)
        ... except J2534ConnectError as error:
        ...     print(f"Connection failed: {error}")
        ...     print(f"Protocol: {error.protocol_id}, Baud: {error.baud_rate}")
    """

    def __init__(
        self,
        message: str = "Failed to connect channel",
        error_code: Optional[int] = None,
        protocol_id: Optional[int] = None,
        baud_rate: Optional[int] = None
    ) -> None:
        self.protocol_id: Optional[int] = protocol_id
        self.baud_rate: Optional[int] = baud_rate
        super().__init__(message, error_code, function_name="PassThruConnect")


class J2534DisconnectError(J2534Error):
    """
    Exception raised when PassThruDisconnect fails.

    This exception indicates that a communication channel could not be
    properly disconnected. This is relatively rare.

    Example:
        >>> try:
        ...     pt_disconnect(channel_id)
        ... except J2534DisconnectError as error:
        ...     print(f"Warning: Disconnect failed: {error}")
    """

    def __init__(
        self,
        message: str = "Failed to disconnect channel",
        error_code: Optional[int] = None
    ) -> None:
        super().__init__(message, error_code, function_name="PassThruDisconnect")


class J2534ReadError(J2534Error):
    """
    Exception raised when PassThruReadMsgs fails.

    This exception indicates that reading messages from the receive buffer
    failed. Note that an empty buffer (no messages available) may or may
    not raise this exception depending on configuration.

    Common causes include:
    - Channel disconnected
    - Device removed
    - Timeout with no messages

    Example:
        >>> try:
        ...     status = pt_read_message(channel_id, message, 1, 1000)
        ... except J2534ReadError as error:
        ...     print(f"Read failed: {error}")
    """

    def __init__(
        self,
        message: str = "Failed to read message",
        error_code: Optional[int] = None
    ) -> None:
        super().__init__(message, error_code, function_name="PassThruReadMsgs")


class J2534WriteError(J2534Error):
    """
    Exception raised when PassThruWriteMsgs fails.

    This exception indicates that sending a message to the vehicle failed.
    Common causes include:
    - Transmit buffer full
    - Channel disconnected
    - Invalid message format

    Example:
        >>> try:
        ...     status = pt_write_message(channel_id, message, 1, 1000)
        ... except J2534WriteError as error:
        ...     print(f"Write failed: {error}")
    """

    def __init__(
        self,
        message: str = "Failed to write message",
        error_code: Optional[int] = None
    ) -> None:
        super().__init__(message, error_code, function_name="PassThruWriteMsgs")


class J2534FilterError(J2534Error):
    """
    Exception raised when filter operations fail.

    This exception indicates that a message filter could not be created,
    started, or stopped. Common causes include:
    - Exceeded maximum number of filters
    - Invalid filter pattern/mask
    - Filter already exists (not unique)

    Example:
        >>> try:
        ...     filter_id = pt_start_message_filter(
        ...         channel_id, filter_type, mask, pattern, flow_control
        ...     )
        ... except J2534FilterError as error:
        ...     print(f"Filter setup failed: {error}")
    """

    def __init__(
        self,
        message: str = "Filter operation failed",
        error_code: Optional[int] = None,
        function_name: Optional[str] = None
    ) -> None:
        super().__init__(
            message,
            error_code,
            function_name=function_name or "PassThruStartMsgFilter"
        )


class J2534IoctlError(J2534Error):
    """
    Exception raised when PassThruIoctl fails.

    This exception indicates that an I/O control operation failed.
    IOCTL operations are used for various purposes including:
    - Reading battery voltage
    - Setting configuration parameters
    - Clearing buffers
    - Fast initialization

    Attributes:
        ioctl_id (int or None): The IOCTL command that was requested.

    Example:
        >>> try:
        ...     voltage = read_battery_volts(device_id)
        ... except J2534IoctlError as error:
        ...     print(f"IOCTL failed: {error}")
    """

    def __init__(
        self,
        message: str = "IOCTL operation failed",
        error_code: Optional[int] = None,
        ioctl_id: Optional[int] = None
    ) -> None:
        self.ioctl_id: Optional[int] = ioctl_id
        super().__init__(message, error_code, function_name="PassThruIoctl")


class J2534PeriodicMessageError(J2534Error):
    """
    Exception raised when periodic message operations fail.

    This exception indicates that a periodic message could not be started
    or stopped. Periodic messages are used for keep-alive signals and
    tester present messages.

    Example:
        >>> try:
        ...     message_id = pt_start_periodic_message(
        ...         channel_id, message, interval
        ...     )
        ... except J2534PeriodicMessageError as error:
        ...     print(f"Periodic message failed: {error}")
    """

    def __init__(
        self,
        message: str = "Periodic message operation failed",
        error_code: Optional[int] = None,
        function_name: Optional[str] = None
    ) -> None:
        super().__init__(
            message,
            error_code,
            function_name=function_name or "PassThruStartPeriodicMsg"
        )


class J2534RegistryError(J2534Error):
    """
    Exception raised when Windows Registry operations fail.

    This exception indicates that the J2534 device registry could not
    be accessed. Common causes include:
    - No J2534 devices installed
    - Registry permissions issue
    - Corrupted registry entries

    Example:
        >>> try:
        ...     devices = get_installed_devices()
        ... except J2534RegistryError as error:
        ...     print(f"Registry access failed: {error}")
    """

    def __init__(
        self,
        message: str = "Windows Registry operation failed",
        error_code: Optional[int] = None
    ) -> None:
        super().__init__(message, error_code, function_name="RegistryAccess")


class J2534ConfigurationError(J2534Error):
    """
    Exception raised when configuration is invalid.

    This exception indicates that an invalid configuration was provided.
    This includes invalid parameter values, incompatible settings, or
    missing required configuration.

    Example:
        >>> try:
        ...     pt_set_config(channel_id, [(INVALID_PARAM, value)])
        ... except J2534ConfigurationError as error:
        ...     print(f"Configuration error: {error}")
    """

    def __init__(
        self,
        message: str = "Invalid configuration",
        error_code: Optional[int] = None
    ) -> None:
        super().__init__(message, error_code, function_name="Configuration")


class J2534DeviceNotSelectedError(J2534Error):
    """
    Exception raised when no device has been selected.

    This exception indicates that an operation was attempted before
    selecting a J2534 device with set_device() or similar function.

    Example:
        >>> try:
        ...     device_id = pt_open()  # No device selected yet!
        ... except J2534DeviceNotSelectedError as error:
        ...     print("Please select a device first")
    """

    def __init__(
        self,
        message: str = "No J2534 device selected - call set_device() first"
    ) -> None:
        super().__init__(message, error_code=None, function_name=None)
