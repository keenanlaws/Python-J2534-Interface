"""
J2534 PassThru API for Python
=============================

A comprehensive Python library for communicating with vehicle ECUs using
the SAE J2534 PassThru API. This library provides a complete implementation
of the J2534-1 v04.04 specification with optional J2534-2 extensions.

Features:
    - Complete J2534-1 v04.04 API implementation
    - Configurable error handling (exceptions or return values)
    - Built-in debug logging
    - Automatic device discovery via Windows Registry
    - High-level message builders
    - Full type hints and documentation

Quick Start:
    Basic usage example::

        from J2534 import (
            get_list_j2534_devices,
            set_j2534_device_to_connect,
            pt_open, pt_close, pt_connect, pt_disconnect,
            pt_read_message, pt_write_message,
            ProtocolId, BaudRate, TxFlags,
            PassThruMsgBuilder
        )

        # List available devices
        devices = get_list_j2534_devices()
        print(f"Found {len(devices)} device(s)")

        # Select and open first device
        set_j2534_device_to_connect(0)
        device_id = pt_open()

        # Connect ISO 15765 channel
        channel_id = pt_connect(
            device_id,
            ProtocolId.ISO15765,
            0,
            BaudRate.CAN_500K
        )

        # Clean up
        pt_disconnect(channel_id)
        pt_close(device_id)

Configuration:
    Enable debug mode::

        from J2534.config import j2534_config
        j2534_config.enable_debug()

    Enable exception-based error handling::

        j2534_config.enable_exceptions()

Modules:
    - config: Library configuration (debug, exceptions)
    - constants: Protocol IDs, error codes, flags, etc.
    - structures: ctypes structures for J2534 messages
    - exceptions: Custom exception classes
    - api: High-level API functions
    - dll_interface: Low-level DLL binding
    - registry: Windows Registry device enumeration
    - logging_utils: Debug logging utilities

Author: J2534-API Contributors
License: MIT
Version: 2.0.0
"""

__version__ = "2.0.0"
__author__ = "J2534-API Contributors"

# =============================================================================
# Configuration
# =============================================================================

from .config import (
    J2534Configuration,
    j2534_config
)

# =============================================================================
# Constants and Enumerations
# =============================================================================

from .constants import (
    # Protocol IDs
    ProtocolId,
    ProtocolIdJ2534_2,

    # Error codes
    ErrorCode,
    ERROR_CODE_DESCRIPTIONS,

    # IOCTL commands
    IoctlId,
    IoctlIdJ2534_2,

    # Configuration parameters
    ConfigParameter,
    Parameter,  # Alias for backward compatibility

    # Message flags
    RxStatus,
    RxStatusJ2534_2,
    TxFlags,

    # Connect flags
    ConnectFlags,
    Flags,  # Alias for backward compatibility

    # Filter types
    FilterType,

    # Voltage and pins
    PinVoltage,
    Voltage,  # Alias for backward compatibility
    Pin,

    # Parity and serial
    Parity,
    NetworkLine,

    # Baud rates
    BaudRate,

    # Constants
    PASSTHRU_MESSAGE_DATA_SIZE,

    # J2534-2 Analog
    AnalogParameter,
)

# =============================================================================
# Structures
# =============================================================================

from .structures import (
    PassThruMessageStructure,
    SetConfigurationParameter,
    SetConfigurationList,
    SetConfiguration,  # Alias
    SByteArray,
    PassThruDataBuffer,
    PASSTHRU_MESSAGE_DATA_SIZE,
    create_message,
    create_empty_message,
)

# =============================================================================
# Exceptions
# =============================================================================

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
    J2534RegistryError,
    J2534ConfigurationError,
    J2534DeviceNotSelectedError,
    get_error_description,
)

# =============================================================================
# API Functions and Classes
# =============================================================================

from .api import (
    # API class
    J2534Api,
    j2534_api,

    # Message builders
    MsgBuilder,
    PassThruMsgBuilder,
    PassThruMsg,

    # Device management
    pt_open,
    pt_close,

    # Channel management
    pt_connect,
    pt_disconnect,

    # Message I/O
    pt_read_message,
    pt_write_message,

    # Periodic messages
    pt_start_periodic_message,
    pt_stop_periodic_message,

    # Filters
    pt_start_message_filter,
    pt_stop_message_filter,
    pt_start_ecu_filter,

    # Voltage
    pt_set_programming_voltage,

    # Information
    pt_read_version,
    pt_get_last_error,

    # IOCTL
    pt_ioctl,
    pt_set_config,

    # Utility functions
    read_battery_volts,
    read_programming_voltage,
    clear_transmit_buffer,
    clear_receive_buffer,
    clear_periodic_messages,
    clear_message_filters,
    clear_functional_message_lookup_table,

    # Convenience aliases
    get_list_j2534_devices,
    set_j2534_device_to_connect,
)

# =============================================================================
# DLL Interface (for advanced usage)
# =============================================================================

from .dll_interface import (
    PassThruLibrary,
    load_j2534_library,
    DllWrapper,
    # Backward compatibility
    PassThru_Data,
)

# =============================================================================
# Registry (re-exported from J2534_REGISTRY package)
# =============================================================================

# Import registry scanner from the J2534_REGISTRY package
# This provides backward compatibility for code that imported from J2534.Registry
try:
    from J2534_REGISTRY import (
        J2534RegistryScanner,
        J2534DeviceInfo,
        get_all_j2534_devices,
        find_device_by_name,
        get_device_count,
        get_scanner,
    )
    # Alias for backward compatibility with old ToolRegistryInfo name
    ToolRegistryInfo = J2534RegistryScanner
except ImportError:
    # If J2534_REGISTRY is not available, create placeholder
    J2534RegistryScanner = None
    J2534DeviceInfo = None
    get_all_j2534_devices = None
    find_device_by_name = None
    get_device_count = None
    get_scanner = None
    ToolRegistryInfo = None

# =============================================================================
# Logging Utilities (for debug output customization)
# =============================================================================

from .logging_utils import (
    debug_log,
    debug_log_function_entry,
    debug_log_function_exit,
    debug_log_message,
    debug_hex_dump,
    format_error_code,
    format_protocol_id,
    format_ioctl_id,
)

# =============================================================================
# Backward Compatibility Aliases
# =============================================================================

# Old Define.py names (now in constants.py)
from .constants import (
    ProtocolId as ProtocolID,  # Old spelling
)

# Old wrapper.py names (now in api.py) - already exported above

# Old dll.py names (now in dll_interface.py and structures.py)
from .dll_interface import (
    PassThru_Data,
    MyDll,
    annotate,
)

from .structures import (
    SetConfiguration,
    SetConfigurationList,
    PassThruDataBuffer,
)

# =============================================================================
# Public API Definition
# =============================================================================

__all__ = [
    # Version
    "__version__",
    "__author__",

    # Configuration
    "J2534Configuration",
    "j2534_config",

    # Protocol IDs
    "ProtocolId",
    "ProtocolID",  # Alias
    "ProtocolIdJ2534_2",

    # Error codes
    "ErrorCode",
    "ERROR_CODE_DESCRIPTIONS",

    # IOCTL
    "IoctlId",
    "IoctlIdJ2534_2",

    # Parameters
    "ConfigParameter",
    "Parameter",

    # Flags
    "RxStatus",
    "RxStatusJ2534_2",
    "TxFlags",
    "ConnectFlags",
    "Flags",

    # Filter types
    "FilterType",

    # Voltage/Pins
    "PinVoltage",
    "Voltage",
    "Pin",

    # Serial
    "Parity",
    "NetworkLine",

    # Baud rate
    "BaudRate",

    # Constants
    "PASSTHRU_MESSAGE_DATA_SIZE",
    "AnalogParameter",

    # Structures
    "PassThruMessageStructure",
    "SetConfigurationParameter",
    "SetConfigurationList",
    "SetConfiguration",
    "SByteArray",
    "PassThruDataBuffer",
    "PassThru_Data",
    "create_message",
    "create_empty_message",

    # Exceptions
    "J2534Error",
    "J2534OpenError",
    "J2534CloseError",
    "J2534ConnectError",
    "J2534DisconnectError",
    "J2534ReadError",
    "J2534WriteError",
    "J2534FilterError",
    "J2534IoctlError",
    "J2534PeriodicMessageError",
    "J2534RegistryError",
    "J2534ConfigurationError",
    "J2534DeviceNotSelectedError",
    "get_error_description",

    # API Classes
    "J2534Api",
    "j2534_api",
    "MsgBuilder",
    "PassThruMsgBuilder",
    "PassThruMsg",

    # API Functions
    "pt_open",
    "pt_close",
    "pt_connect",
    "pt_disconnect",
    "pt_read_message",
    "pt_write_message",
    "pt_start_periodic_message",
    "pt_stop_periodic_message",
    "pt_start_message_filter",
    "pt_stop_message_filter",
    "pt_start_ecu_filter",
    "pt_set_programming_voltage",
    "pt_read_version",
    "pt_get_last_error",
    "pt_ioctl",
    "pt_set_config",
    "read_battery_volts",
    "read_programming_voltage",
    "clear_transmit_buffer",
    "clear_receive_buffer",
    "clear_periodic_messages",
    "clear_message_filters",
    "clear_functional_message_lookup_table",
    "get_list_j2534_devices",
    "set_j2534_device_to_connect",

    # DLL Interface
    "PassThruLibrary",
    "load_j2534_library",
    "DllWrapper",
    "MyDll",
    "annotate",

    # Registry
    "J2534RegistryScanner",
    "J2534DeviceInfo",
    "get_all_j2534_devices",
    "find_device_by_name",
    "get_device_count",
    "get_scanner",
    "ToolRegistryInfo",  # Backward compatibility alias

    # Logging
    "debug_log",
    "debug_log_function_entry",
    "debug_log_function_exit",
    "debug_log_message",
    "debug_hex_dump",
    "format_error_code",
    "format_protocol_id",
    "format_ioctl_id",
]
