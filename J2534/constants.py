"""
J2534 Constants and Enumerations
================================

This module defines all constants, enumerations, and values used in the
SAE J2534 API specification (v04.04). These values are based on the official
SAE J2534-1 and J2534-2 specifications for Pass-Thru vehicle programming.

The module provides comprehensive coverage of:
    - Protocol identifiers (J2534-1 and J2534-2)
    - Error codes with descriptions
    - IOCTL command identifiers
    - Configuration parameters
    - Message flags (transmit and receive)
    - Filter types
    - Voltage settings
    - Connection flags
    - Parity and data bit settings

All enumerations use IntEnum or IntFlag for compatibility with the
underlying ctypes interface while providing Pythonic usage patterns.

Reference:
    - SAE J2534-1: Pass-Thru Vehicle Programming API (Core)
    - SAE J2534-2: Extended API for Diagnostics
    - SAE J2534-5: Alternate Platforms

Example:
    Using protocol IDs::

        from J2534.constants import ProtocolId, BaudRate

        # Connect using ISO15765 (CAN diagnostic protocol)
        channel_id = pt_connect(
            device_id,
            ProtocolId.ISO15765,
            0,
            BaudRate.CAN_500K
        )

Example:
    Using IOCTL commands::

        from J2534.constants import IoctlId

        # Read vehicle battery voltage
        voltage = pt_ioctl(device_id, IoctlId.READ_VBATT, None, voltage_buffer)

Author: J2534-API Contributors
License: MIT
Version: 2.0.0

Sources:
    - https://github.com/diamondman/J2534-PassThru-Logger
    - https://www.dashlogic.com/download/j2534%20pass%20thru%20device%20interface%20source%20code/J2534_v0404.h
    - SAE J2534-1 v04.04 Specification
"""

from enum import IntEnum, IntFlag


# =============================================================================
# Protocol Identifiers
# =============================================================================

class ProtocolId(IntEnum):
    """
    Vehicle communication protocol identifiers (J2534-1 v04.04).

    These values identify the communication protocol to use when
    establishing a connection with a vehicle network through the
    J2534 interface.

    The protocols cover various automotive communication standards:
    - J1850: GM and Ford legacy protocols
    - ISO 9141/14230: European K-line protocols
    - CAN: Controller Area Network
    - ISO 15765: CAN-based diagnostics (OBD-II CAN)
    - SCI: Chrysler proprietary protocols

    Attributes:
        J1850_VPW: SAE J1850 Variable Pulse Width (GM vehicles, 10.4 kbps)
        J1850_PWM: SAE J1850 Pulse Width Modulation (Ford vehicles, 41.6 kbps)
        ISO9141: ISO 9141-2 K-line protocol (older European/Asian vehicles)
        ISO14230: ISO 14230-4 KWP2000 (European vehicles, K-line)
        CAN: ISO 11898 Controller Area Network (raw CAN frames)
        ISO15765: ISO 15765-4 CAN diagnostic protocol (OBD-II CAN, UDS)
        SCI_A_ENGINE: Chrysler SCI-A Engine protocol (7,812.5 baud)
        SCI_A_TRANS: Chrysler SCI-A Transmission protocol
        SCI_B_ENGINE: Chrysler SCI-B Engine protocol (62,500 baud)
        SCI_B_TRANS: Chrysler SCI-B Transmission protocol

    Example:
        >>> from J2534.constants import ProtocolId
        >>> print(ProtocolId.ISO15765)
        ProtocolId.ISO15765
        >>> print(ProtocolId.ISO15765.value)
        6
    """
    J1850_VPW = 0x01
    J1850_PWM = 0x02
    ISO9141 = 0x03
    ISO14230 = 0x04
    CAN = 0x05
    ISO15765 = 0x06
    SCI_A_ENGINE = 0x07
    SCI_A_TRANS = 0x08
    SCI_B_ENGINE = 0x09
    SCI_B_TRANS = 0x0A

    # Aliases for common names
    J1850VPW = 0x01  # Alternative spelling
    J1850PWM = 0x02  # Alternative spelling


class ProtocolIdJ2534_2(IntEnum):
    """
    Extended protocol identifiers for J2534-2.

    J2534-2 adds support for additional protocols and multi-channel
    operations. These protocol IDs use different value ranges than
    J2534-1 protocols.

    Note:
        J2534-2 is an optional extension. Not all devices support it.

    Attributes:
        CAN_PS: CAN protocol with programmable channel selection
        ISO15765_PS: ISO 15765 with programmable channel selection
        J1850VPW_PS: J1850 VPW with programmable channel selection
        J1850PWM_PS: J1850 PWM with programmable channel selection
        ISO9141_PS: ISO 9141 with programmable channel selection
        ISO14230_PS: ISO 14230 with programmable channel selection
        SW_CAN_PS: Single Wire CAN with programmable channel selection
        J2610_PS: SAE J2610 (Chrysler CCD)
        ANALOG_IN: Analog input channel (for voltage measurement)
    """
    CAN_PS = 0x00008000
    ISO15765_PS = 0x00008001
    J1850VPW_PS = 0x00008002
    J1850PWM_PS = 0x00008003
    ISO9141_PS = 0x00008004
    ISO14230_PS = 0x00008005
    J2610_PS = 0x00008006
    SW_CAN_PS = 0x00008008
    ANALOG_IN = 0x00008009


# =============================================================================
# Error Codes
# =============================================================================

class ErrorCode(IntEnum):
    """
    J2534 API error codes (v04.04).

    These error codes are returned by J2534 PassThru functions to indicate
    the result of an operation. A value of 0 (STATUS_NOERROR) indicates
    success; any other value indicates an error condition.

    Use PassThruGetLastError() to get a text description of the most
    recent error.

    Attributes:
        STATUS_NOERROR: Operation completed successfully
        ERR_NOT_SUPPORTED: Device cannot support requested functionality
        ERR_INVALID_CHANNEL_ID: Invalid channel ID value
        ERR_INVALID_PROTOCOL_ID: Invalid or unsupported protocol ID
        ERR_NULL_PARAMETER: NULL pointer where valid pointer required
        ERR_INVALID_IOCTL_VALUE: Invalid value for IOCTL parameter
        ERR_INVALID_FLAGS: Invalid flag values
        ERR_FAILED: Undefined error (use GetLastError for details)
        ERR_DEVICE_NOT_CONNECTED: Cannot communicate with device
        ERR_TIMEOUT: Read/write timeout occurred
        ERR_INVALID_MSG: Invalid message structure
        ERR_INVALID_TIME_INTERVAL: Invalid time interval value
        ERR_EXCEEDED_LIMIT: Exceeded maximum number of resources
        ERR_INVALID_MSG_ID: Invalid message ID value
        ERR_DEVICE_IN_USE: Device already opened
        ERR_INVALID_IOCTL_ID: Invalid IOCTL ID value
        ERR_BUFFER_EMPTY: No messages in receive buffer
        ERR_BUFFER_FULL: Transmit buffer full
        ERR_BUFFER_OVERFLOW: Buffer overflow, messages lost
        ERR_PIN_INVALID: Invalid pin number
        ERR_CHANNEL_IN_USE: Channel already connected
        ERR_MSG_PROTOCOL_ID: Message protocol doesn't match channel
        ERR_INVALID_FILTER_ID: Invalid filter ID value
        ERR_NO_FLOW_CONTROL: ISO 15765 requires flow control filter
        ERR_NOT_UNIQUE: Filter pattern/mask not unique
        ERR_INVALID_BAUDRATE: Baud rate not achievable
        ERR_INVALID_DEVICE_ID: Invalid device ID value

    Example:
        >>> result = pt_open()
        >>> if result == ErrorCode.STATUS_NOERROR:
        ...     print("Device opened successfully")
        >>> elif result == ErrorCode.ERR_DEVICE_NOT_CONNECTED:
        ...     print("No device connected")
    """
    STATUS_NOERROR = 0x00
    ERR_NOT_SUPPORTED = 0x01
    ERR_INVALID_CHANNEL_ID = 0x02
    ERR_INVALID_PROTOCOL_ID = 0x03
    ERR_NULL_PARAMETER = 0x04
    ERR_INVALID_IOCTL_VALUE = 0x05
    ERR_INVALID_FLAGS = 0x06
    ERR_FAILED = 0x07
    ERR_DEVICE_NOT_CONNECTED = 0x08
    ERR_TIMEOUT = 0x09
    ERR_INVALID_MSG = 0x0A
    ERR_INVALID_TIME_INTERVAL = 0x0B
    ERR_EXCEEDED_LIMIT = 0x0C
    ERR_INVALID_MSG_ID = 0x0D
    ERR_DEVICE_IN_USE = 0x0E
    ERR_INVALID_IOCTL_ID = 0x0F
    ERR_BUFFER_EMPTY = 0x10
    ERR_BUFFER_FULL = 0x11
    ERR_BUFFER_OVERFLOW = 0x12
    ERR_PIN_INVALID = 0x13
    ERR_CHANNEL_IN_USE = 0x14
    ERR_MSG_PROTOCOL_ID = 0x15
    ERR_INVALID_FILTER_ID = 0x16
    ERR_NO_FLOW_CONTROL = 0x17
    ERR_NOT_UNIQUE = 0x18
    ERR_INVALID_BAUDRATE = 0x19
    ERR_INVALID_DEVICE_ID = 0x1A


# Human-readable descriptions for error codes
ERROR_CODE_DESCRIPTIONS: dict = {
    ErrorCode.STATUS_NOERROR: "No error - operation completed successfully",
    ErrorCode.ERR_NOT_SUPPORTED: "Function or feature not supported by device",
    ErrorCode.ERR_INVALID_CHANNEL_ID: "Invalid channel ID - not from PassThruConnect or already disconnected",
    ErrorCode.ERR_INVALID_PROTOCOL_ID: "Invalid protocol ID - not recognized or protocol resource conflict",
    ErrorCode.ERR_NULL_PARAMETER: "NULL parameter - required pointer was NULL",
    ErrorCode.ERR_INVALID_IOCTL_VALUE: "Invalid IOCTL value - parameter value out of valid range",
    ErrorCode.ERR_INVALID_FLAGS: "Invalid flags - flags parameter contains invalid combination",
    ErrorCode.ERR_FAILED: "Operation failed - use PassThruGetLastError() for description",
    ErrorCode.ERR_DEVICE_NOT_CONNECTED: "Device not connected - unable to communicate with device",
    ErrorCode.ERR_TIMEOUT: "Timeout - operation did not complete within specified time",
    ErrorCode.ERR_INVALID_MSG: "Invalid message - message structure contains invalid values",
    ErrorCode.ERR_INVALID_TIME_INTERVAL: "Invalid time interval - value outside valid range",
    ErrorCode.ERR_EXCEEDED_LIMIT: "Exceeded limit - maximum resources (filters, periodic messages) reached",
    ErrorCode.ERR_INVALID_MSG_ID: "Invalid message ID - not from successful start operation",
    ErrorCode.ERR_DEVICE_IN_USE: "Device in use - device already opened by another application",
    ErrorCode.ERR_INVALID_IOCTL_ID: "Invalid IOCTL ID - command not recognized for this channel type",
    ErrorCode.ERR_BUFFER_EMPTY: "Buffer empty - no messages available in receive buffer",
    ErrorCode.ERR_BUFFER_FULL: "Buffer full - transmit buffer cannot accept more messages",
    ErrorCode.ERR_BUFFER_OVERFLOW: "Buffer overflow - messages were lost due to buffer overflow",
    ErrorCode.ERR_PIN_INVALID: "Invalid pin - pin number not valid or voltage already on different pin",
    ErrorCode.ERR_CHANNEL_IN_USE: "Channel in use - requested channel already connected",
    ErrorCode.ERR_MSG_PROTOCOL_ID: "Protocol ID mismatch - message protocol differs from channel protocol",
    ErrorCode.ERR_INVALID_FILTER_ID: "Invalid filter ID - not from successful filter start operation",
    ErrorCode.ERR_NO_FLOW_CONTROL: "No flow control - ISO 15765 channel requires flow control filter",
    ErrorCode.ERR_NOT_UNIQUE: "Not unique - filter pattern/mask combination already exists",
    ErrorCode.ERR_INVALID_BAUDRATE: "Invalid baud rate - cannot achieve requested baud rate within tolerance",
    ErrorCode.ERR_INVALID_DEVICE_ID: "Invalid device ID - not from PassThruOpen or device already closed",
}


# =============================================================================
# IOCTL Command Identifiers
# =============================================================================

class IoctlId(IntEnum):
    """
    IOCTL command identifiers for PassThruIoctl().

    These constants identify the I/O control operations that can be
    performed through the PassThruIoctl() function. IOCTLs are used
    for configuration, buffer management, and special operations.

    Categories:
        - Configuration: GET_CONFIG, SET_CONFIG
        - Voltage reading: READ_VBATT, READ_PROG_VOLTAGE
        - Initialization: FIVE_BAUD_INIT, FAST_INIT
        - Buffer management: CLEAR_TX_BUFFER, CLEAR_RX_BUFFER
        - Resource management: CLEAR_PERIODIC_MSGS, CLEAR_MSG_FILTERS
        - Functional addressing: FUNCT_MSG_LOOKUP_TABLE operations

    Attributes:
        GET_CONFIG: Read configuration parameters (returns SCONFIG_LIST)
        SET_CONFIG: Write configuration parameters (uses SCONFIG_LIST)
        READ_VBATT: Read vehicle battery voltage (returns mV in ulong)
        FIVE_BAUD_INIT: Perform ISO 9141 5-baud initialization
        FAST_INIT: Perform ISO 14230 fast initialization
        CLEAR_TX_BUFFER: Clear the transmit message buffer
        CLEAR_RX_BUFFER: Clear the receive message buffer
        CLEAR_PERIODIC_MSGS: Stop and clear all periodic messages
        CLEAR_MSG_FILTERS: Remove all message filters
        CLEAR_FUNCT_MSG_LOOKUP_TABLE: Clear functional message lookup table
        ADD_TO_FUNCT_MSG_LOOKUP_TABLE: Add entry to functional lookup table
        DELETE_FROM_FUNCT_MSG_LOOKUP_TABLE: Remove entry from lookup table
        READ_PROG_VOLTAGE: Read programming voltage (returns mV in ulong)

    Example:
        >>> from J2534.constants import IoctlId
        >>> # Read battery voltage
        >>> voltage_mv = ctypes.c_ulong()
        >>> pt_ioctl(device_id, IoctlId.READ_VBATT, None, ctypes.byref(voltage_mv))
        >>> print(f"Battery: {voltage_mv.value / 1000.0}V")
    """
    GET_CONFIG = 0x01
    SET_CONFIG = 0x02
    READ_VBATT = 0x03
    FIVE_BAUD_INIT = 0x04
    FAST_INIT = 0x05
    # Note: 0x06 is not defined in the specification
    CLEAR_TX_BUFFER = 0x07
    CLEAR_RX_BUFFER = 0x08
    CLEAR_PERIODIC_MSGS = 0x09
    CLEAR_MSG_FILTERS = 0x0A
    CLEAR_FUNCT_MSG_LOOKUP_TABLE = 0x0B
    ADD_TO_FUNCT_MSG_LOOKUP_TABLE = 0x0C
    DELETE_FROM_FUNCT_MSG_LOOKUP_TABLE = 0x0D
    READ_PROG_VOLTAGE = 0x0E


class IoctlIdJ2534_2(IntEnum):
    """
    Extended IOCTL command identifiers for J2534-2.

    These additional IOCTL commands are defined in the J2534-2
    specification for extended functionality.

    Attributes:
        SW_CAN_HS: Switch Single Wire CAN to high speed mode
        SW_CAN_NS: Switch Single Wire CAN to normal speed mode
        SET_POLL_RESPONSE: Set polling response message
        BECOME_MASTER: Become the master on the bus
    """
    SW_CAN_HS = 0x00008000
    SW_CAN_NS = 0x00008001
    SET_POLL_RESPONSE = 0x00008002
    BECOME_MASTER = 0x00008003


# =============================================================================
# Configuration Parameters
# =============================================================================

class ConfigParameter(IntEnum):
    """
    Configuration parameter identifiers for GET_CONFIG/SET_CONFIG.

    These parameters are used with the GET_CONFIG and SET_CONFIG IOCTL
    commands to read or modify channel configuration. Parameters are
    organized by protocol applicability.

    Common Parameters:
        DATA_RATE: Baud rate for the channel (no default)
        LOOPBACK: Echo transmitted messages to receive queue (0=off, 1=on)

    J1850 Parameters:
        NODE_ADDRESS: Physical address for J1850PWM (0x00-0xFF)
        NETWORK_LINE: Active network lines (BUS_NORMAL/PLUS/MINUS)

    ISO 9141/14230 Timing Parameters:
        P1_MIN, P1_MAX: ECU inter-byte time for responses
        P2_MIN, P2_MAX: ECU response time to tester request
        P3_MIN, P3_MAX: Time between end of ECU response and next request
        P4_MIN, P4_MAX: Tester inter-byte time for requests
        W0-W5: ISO 9141 initialization timing parameters
        TIDLE, TINIL, TWUP: Fast initialization timing
        PARITY: Parity setting (0=none, 1=odd, 2=even)

    CAN Parameters:
        BIT_SAMPLE_POINT: Bit sample point as percentage (0-100)
        SYNC_JUMP_WIDTH: Synchronization jump width as percentage

    ISO 15765 Parameters:
        ISO15765_BS: Block size for segmented transfers
        ISO15765_STMIN: Separation time for segmented transfers
        ISO15765_BS_TX: Block size for transmission
        ISO15765_STMIN_TX: Separation time for transmission
        ISO15765_WFT_MAX: Maximum wait frame transmissions

    SCI Parameters:
        T1_MAX: Maximum interframe response delay
        T2_MAX: Maximum interframe request delay
        T4_MAX: Maximum intermessage response delay
        T5_MAX: Maximum intermessage request delay

    Other Parameters:
        DATA_BITS: Number of data bits (8, 7, etc.)
        FIVE_BAUD_MOD: 5-baud init modification flags
        CAN_MIXED_FORMAT: Allow mixed 11/29-bit CAN IDs
    """
    # Common parameters
    DATA_RATE = 0x01
    LOOPBACK = 0x03
    NODE_ADDRESS = 0x04
    NETWORK_LINE = 0x05

    # ISO 9141/14230 timing parameters (values in ms or 0.5ms for v04.04)
    P1_MIN = 0x06
    P1_MAX = 0x07
    P2_MIN = 0x08
    P2_MAX = 0x09
    P3_MIN = 0x0A
    P3_MAX = 0x0B
    P4_MIN = 0x0C
    P4_MAX = 0x0D

    # ISO 9141 initialization timing
    W1 = 0x0E
    W2 = 0x0F
    W3 = 0x10
    W4 = 0x11
    W5 = 0x12
    TIDLE = 0x13
    TINIL = 0x14
    TWUP = 0x15

    # Serial parameters
    PARITY = 0x16

    # CAN parameters
    BIT_SAMPLE_POINT = 0x17
    SYNC_JUMP_WIDTH = 0x18

    # Additional timing
    W0 = 0x19

    # SCI timing parameters
    T1_MAX = 0x1A
    T2_MAX = 0x1B
    T4_MAX = 0x1C
    T5_MAX = 0x1D

    # ISO 15765 parameters
    ISO15765_BS = 0x1E
    ISO15765_STMIN = 0x1F

    # Additional parameters (v04.04)
    DATA_BITS = 0x20
    FIVE_BAUD_MOD = 0x21
    ISO15765_BS_TX = 0x22
    ISO15765_STMIN_TX = 0x23
    T3_MAX = 0x24
    ISO15765_WFT_MAX = 0x25


# Aliases for common names and backward compatibility
class Parameter(IntEnum):
    """Alias for ConfigParameter for backward compatibility."""
    DATA_RATE = 0x01
    LOOPBACK = 0x03
    NODE_ADDRESS = 0x04
    NETWORK_LINE = 0x05
    P1_MIN = 0x06
    P1_MAX = 0x07
    P2_MIN = 0x08
    P2_MAX = 0x09
    P3_MIN = 0x0A
    P3_MAX = 0x0B
    P4_MIN = 0x0C
    P4_MAX = 0x0D
    W1 = 0x0E
    W2 = 0x0F
    W3 = 0x10
    W4 = 0x11
    W5 = 0x12
    TIDLE = 0x13
    TINIL = 0x14
    TWUP = 0x15
    PARITY = 0x16
    BIT_SAMPLE_POINT = 0x17
    SYNC_JUMP_WIDTH = 0x18
    W0 = 0x19
    T1_MAX = 0x1A
    T2_MAX = 0x1B
    T4_MAX = 0x1C
    T5_MAX = 0x1D
    ISO15765_BS = 0x1E
    ISO15765_STMIN = 0x1F
    DATA_BITS = 0x20
    FIVE_BAUD_MOD = 0x21
    ISO15765_BS_TX = 0x22
    ISO15765_STMIN_TX = 0x23
    T3_MAX = 0x24
    ISO15765_WFT_MAX = 0x25


# =============================================================================
# Message Flags
# =============================================================================

class RxStatus(IntFlag):
    """
    Receive status flags for incoming messages.

    These flags indicate the status and type of received messages.
    They are set in the RxStatus field of the PASSTHRU_MSG structure
    when a message is read from the receive buffer.

    Multiple flags can be set simultaneously using bitwise OR.

    Attributes:
        NONE: No special status (normal received message)
        TX_MSG_TYPE: Message was transmitted (echo of sent message)
        START_OF_MESSAGE: Start of a multi-frame message (first frame)
        ISO15765_FIRST_FRAME: Alias for START_OF_MESSAGE
        RX_BREAK: Break condition received on the bus
        TX_DONE: Transmission completed successfully
        TX_INDICATION: Combined TX_MSG_TYPE and TX_DONE
        ISO15765_PADDING_ERROR: Padding error in ISO 15765 message
        ISO15765_ADDR_TYPE: Extended addressing mode active
        ISO15765_EXT_ADDR: Alias for ISO15765_ADDR_TYPE
        CAN_29BIT_ID: Message uses 29-bit CAN identifier

    Example:
        >>> if message.RxStatus & RxStatus.TX_MSG_TYPE:
        ...     print("This is an echo of a transmitted message")
        >>> if message.RxStatus & RxStatus.CAN_29BIT_ID:
        ...     print("Message uses 29-bit CAN ID")
    """
    NONE = 0x00000000
    TX_MSG_TYPE = 0x00000001
    START_OF_MESSAGE = 0x00000002
    ISO15765_FIRST_FRAME = 0x00000002  # Alias
    RX_BREAK = 0x00000004
    TX_DONE = 0x00000008
    TX_INDICATION = 0x00000009  # TX_MSG_TYPE | TX_DONE
    ISO15765_PADDING_ERROR = 0x00000010
    ISO15765_ADDR_TYPE = 0x00000080
    ISO15765_EXT_ADDR = 0x00000080  # Alias
    CAN_29BIT_ID = 0x00000100


class RxStatusJ2534_2(IntFlag):
    """
    Extended receive status flags for J2534-2.

    Attributes:
        SW_CAN_HV_RX: Received on Single Wire CAN high voltage
        SW_CAN_HS_RX: Received on Single Wire CAN high speed
        SW_CAN_NS_RX: Received on Single Wire CAN normal speed
        ANALOG_OVERFLOW: Analog input overflow
    """
    SW_CAN_HV_RX = 0x00010000
    SW_CAN_HS_RX = 0x00020000
    SW_CAN_NS_RX = 0x00040000
    ANALOG_OVERFLOW = 0x00010000


class TxFlags(IntFlag):
    """
    Transmit flags for outgoing messages.

    These flags control how messages are transmitted. They are set in
    the TxFlags field of the PASSTHRU_MSG structure when sending.

    Attributes:
        NONE: No special flags (normal transmission)
        TX_NORMAL_TRANSMIT: Alias for NONE
        ISO15765_FRAME_PAD: Add padding to ISO 15765 frames
        ISO15765_CAN_ID_11: Use 11-bit CAN ID for ISO 15765
        ISO15765_CAN_ID_29: Use 29-bit CAN ID for ISO 15765
        ISO15765_ADDR_TYPE: Use extended addressing for ISO 15765
        CAN_29BIT_ID: Use 29-bit CAN identifier
        WAIT_P3_MIN_ONLY: Wait only P3_MIN before transmit
        SW_CAN_HV_TX: Transmit on Single Wire CAN high voltage
        SCI_MODE: SCI mode transmission
        SCI_TX_VOLTAGE: SCI transmission voltage mode
        SCI_MODE_TX_VOLTAGE: Combined SCI mode with TX voltage

    Example:
        >>> # Send ISO 15765 message with padding on 11-bit CAN
        >>> message.TxFlags = TxFlags.ISO15765_FRAME_PAD | TxFlags.ISO15765_CAN_ID_11
    """
    NONE = 0x00000000
    TX_NORMAL_TRANSMIT = 0x00000000  # Alias
    ISO15765_FRAME_PAD = 0x00000040
    ISO15765_CAN_ID_11 = 0x00000040  # Same as FRAME_PAD for 11-bit
    ISO15765_ADDR_TYPE = 0x00000080
    CAN_29BIT_ID = 0x00000100
    ISO15765_CAN_ID_29 = 0x00000140  # CAN_29BIT_ID | ISO15765_FRAME_PAD
    WAIT_P3_MIN_ONLY = 0x00000200
    SW_CAN_HV_TX = 0x00000400
    SCI_MODE = 0x00400000
    SCI_TX_VOLTAGE = 0x00800000
    SCI_MODE_TX_VOLTAGE = 0x00C00000  # SCI_MODE | SCI_TX_VOLTAGE


# =============================================================================
# Connect Flags
# =============================================================================

class ConnectFlags(IntFlag):
    """
    Connection flags for PassThruConnect().

    These flags modify the behavior of a protocol connection. They are
    passed to PassThruConnect() to configure the channel.

    Attributes:
        NONE: No special flags (default connection)
        CAN_29BIT_ID: Enable 29-bit CAN identifiers
        ISO9141_NO_CHECKSUM: Disable checksum for ISO 9141
        NO_CHECKSUM: Alias for ISO9141_NO_CHECKSUM
        CAN_ID_BOTH: Allow both 11-bit and 29-bit CAN IDs
        ISO9141_K_LINE_ONLY: Use K-line only (not L-line)
        SNIFF_MODE: Enable bus sniffing mode (receive only)
        LISTEN_ONLY_DT: Alias for SNIFF_MODE
        ISO9141_FORD_HEADER: Use Ford header format
        ISO9141_NO_CHECKSUM_DT: No checksum in data transfer

    Example:
        >>> # Connect to CAN with both 11-bit and 29-bit IDs allowed
        >>> channel_id = pt_connect(
        ...     device_id,
        ...     ProtocolId.CAN,
        ...     ConnectFlags.CAN_ID_BOTH,
        ...     500000
        ... )
    """
    NONE = 0x00000000
    CAN_29BIT_ID = 0x00000100
    ISO9141_NO_CHECKSUM = 0x00000200
    NO_CHECKSUM = 0x00000200  # Alias
    CAN_ID_BOTH = 0x00000800
    ISO9141_K_LINE_ONLY = 0x00001000
    SNIFF_MODE = 0x10000000
    LISTEN_ONLY_DT = 0x10000000  # Alias
    ISO9141_FORD_HEADER = 0x20000000
    ISO9141_NO_CHECKSUM_DT = 0x40000000


# Alias for backward compatibility
Flags = ConnectFlags


# =============================================================================
# Filter Types
# =============================================================================

class FilterType(IntEnum):
    """
    Message filter types for PassThruStartMsgFilter().

    These constants specify what type of filter to create when setting
    up message filtering on a channel.

    Attributes:
        PASS_FILTER: Allow messages matching the pattern to pass
        BLOCK_FILTER: Block messages matching the pattern
        FLOW_CONTROL_FILTER: ISO 15765 flow control filter (required)

    Note:
        For ISO 15765 channels, you must create a FLOW_CONTROL_FILTER
        before any messages can be sent or received.

    Example:
        >>> # Create a flow control filter for ISO 15765
        >>> filter_id = pt_start_message_filter(
        ...     channel_id,
        ...     FilterType.FLOW_CONTROL_FILTER,
        ...     mask_msg,
        ...     pattern_msg,
        ...     flow_control_msg
        ... )
    """
    PASS_FILTER = 0x00000001
    BLOCK_FILTER = 0x00000002
    FLOW_CONTROL_FILTER = 0x00000003


# =============================================================================
# Voltage Constants
# =============================================================================

class PinVoltage(IntEnum):
    """
    Programming voltage control values.

    These values are used with PassThruSetProgrammingVoltage() to control
    the programming voltage output on specific pins.

    Attributes:
        SHORT_TO_GROUND: Short the pin to ground (0V)
        VOLTAGE_OFF: Turn off voltage output (high impedance)

    Note:
        For actual voltage values, pass the voltage in millivolts.
        For example, 5000 for 5V, 12000 for 12V.

    Example:
        >>> # Set 12V programming voltage on pin 15
        >>> pt_set_programming_voltage(device_id, Pin.J1962_PIN_15, 12000)
        >>> # Turn off voltage
        >>> pt_set_programming_voltage(device_id, Pin.J1962_PIN_15, PinVoltage.VOLTAGE_OFF)
    """
    SHORT_TO_GROUND = 0xFFFFFFFE
    VOLTAGE_OFF = 0xFFFFFFFF


# Alias for backward compatibility
class Voltage(IntEnum):
    """Alias for PinVoltage for backward compatibility."""
    SHORT_TO_GROUND = 0xFFFFFFFE
    VOLTAGE_OFF = 0xFFFFFFFF


class Pin(IntEnum):
    """
    J1962 connector pin numbers for programming voltage.

    These constants identify the pins on the standard OBD-II (J1962)
    connector that can be controlled for programming voltage.

    Attributes:
        AUXILIARY_OUTPUT: Auxiliary output pin
        J1962_PIN_6: Pin 6 (CAN High)
        J1962_PIN_9: Pin 9 (K-Line / CAN Low)
        J1962_PIN_11: Pin 11 (Ford DCL)
        J1962_PIN_12: Pin 12 (Ford DCL)
        J1962_PIN_13: Pin 13 (Ford DCL)
        J1962_PIN_14: Pin 14 (CAN Low)
        J1962_PIN_15: Pin 15 (L-Line)
    """
    AUXILIARY_OUTPUT = 0
    J1962_PIN_6 = 6
    J1962_PIN_9 = 9
    J1962_PIN_11 = 11
    J1962_PIN_12 = 12
    J1962_PIN_13 = 13
    J1962_PIN_14 = 14
    J1962_PIN_15 = 15


# =============================================================================
# Parity and Data Bits
# =============================================================================

class Parity(IntEnum):
    """
    Parity settings for serial protocols (ISO 9141, ISO 14230).

    Attributes:
        NO_PARITY: No parity bit
        ODD_PARITY: Odd parity
        EVEN_PARITY: Even parity
    """
    NO_PARITY = 0
    ODD_PARITY = 1
    EVEN_PARITY = 2


class NetworkLine(IntEnum):
    """
    Network line selection for J1850PWM.

    Attributes:
        BUS_NORMAL: Normal bus operation (both lines)
        BUS_PLUS: Bus+ line only
        BUS_MINUS: Bus- line only
    """
    BUS_NORMAL = 0
    BUS_PLUS = 1
    BUS_MINUS = 2


# =============================================================================
# Baud Rates
# =============================================================================

class BaudRate(IntEnum):
    """
    Common baud rates for vehicle communication protocols.

    These are convenience constants for commonly used baud rates.
    Any valid integer baud rate can be used with PassThruConnect().

    CAN Baud Rates:
        CAN_125K: 125 kbps CAN
        CAN_250K: 250 kbps CAN
        CAN_500K: 500 kbps CAN (most common for OBD-II)

    J1850 Baud Rates:
        J1850_PWM_41600: 41.6 kbps (Ford standard)
        J1850_PWM_83300: 83.3 kbps (Ford enhanced)
        J1850_VPW_10400: 10.4 kbps (GM standard)
        J1850_VPW_41600: 41.6 kbps (GM enhanced)

    ISO 9141/14230 Baud Rates:
        ISO_10400: 10.4 kbps (common K-line)
        ISO_10000: 10.0 kbps (alternative K-line)

    SCI Baud Rates:
        SCI_7813: 7,812.5 bps (Chrysler SCI-A)
        SCI_62500: 62,500 bps (Chrysler SCI-B high speed)

    Example:
        >>> channel_id = pt_connect(
        ...     device_id,
        ...     ProtocolId.ISO15765,
        ...     0,
        ...     BaudRate.CAN_500K
        ... )
    """
    # CAN baud rates
    CAN_125K = 125000
    CAN_250K = 250000
    CAN_500K = 500000

    # Alternative spellings
    CAN_125k = 125000
    CAN_250k = 250000
    CAN_500k = 500000

    # J1850 baud rates
    J1850_PWM_41600 = 41600
    J1850_PWM_83300 = 83300
    J1850_VPW_10400 = 10400
    J1850_VPW_41600 = 41600

    # Backward compatibility aliases
    J1850PWM_41600 = 41600
    J1850PWM_83300 = 83300
    J1850VPW_10400 = 10400
    J1850VPW_41600 = 41600

    # ISO 9141/14230 baud rates
    ISO_10400 = 10400
    ISO_10000 = 10000
    ISO9141_10400 = 10400
    ISO9141_10000 = 10000
    ISO14230_10400 = 10400
    ISO14230_10000 = 10000

    # SCI baud rates
    SCI_7813 = 7813
    SCI_62500 = 62500
    SCI = 7813  # Default SCI baud
    SCI_HIGHSPEED = 62500


# =============================================================================
# Data Buffer Size
# =============================================================================

# Maximum size of the data buffer in a PassThru message
PASSTHRU_MESSAGE_DATA_SIZE: int = 4128
"""
Maximum size of the data buffer in a PASSTHRU_MSG structure.

This is the maximum number of bytes that can be stored in the Data
field of a J2534 message. This limit is defined by the SAE J2534
specification.
"""


# =============================================================================
# Analog Input Configuration (J2534-2)
# =============================================================================

class AnalogParameter(IntEnum):
    """
    Configuration parameters for J2534-2 analog input channels.

    These parameters are used to configure analog input channels when
    using the ANALOG_IN protocol in J2534-2.

    Attributes:
        ACTIVE_CHANNELS: Which channels are active (bitmask)
        SAMPLE_RATE: Sampling rate in Hz
        SAMPLES_PER_READING: Number of samples to average per reading
        READINGS_PER_MSG: Number of readings per message
        AVERAGING_METHOD: Averaging algorithm to use
        SAMPLE_RESOLUTION: ADC resolution in bits
        INPUT_RANGE_LOW: Low end of input voltage range (mV)
        INPUT_RANGE_HIGH: High end of input voltage range (mV)
    """
    ACTIVE_CHANNELS = 0x8000
    SAMPLE_RATE = 0x8001
    SAMPLES_PER_READING = 0x8002
    READINGS_PER_MSG = 0x8003
    AVERAGING_METHOD = 0x8004
    SAMPLE_RESOLUTION = 0x8005
    INPUT_RANGE_LOW = 0x8006
    INPUT_RANGE_HIGH = 0x8007
