"""
AutoJ2534 - High-Level Vehicle Communication Interface
=======================================================

This package provides a user-friendly interface for J2534 PassThru vehicle
diagnostics communication. It simplifies ECU communication by handling:

    - Device discovery and connection management
    - Protocol configuration (CAN, ISO15765, SCI)
    - Message filtering and flow control
    - Automatic response parsing and error handling
    - UDS negative response code interpretation
    - Built-in UDS service wrappers (VIN, DTC, Security Access)

Quick Start - 1-Line Connection
-------------------------------
Use quick_connect() for the simplest connection::

    from AutoJ2534 import quick_connect

    comm = quick_connect()  # Uses device 0, chrys1 profile
    if comm:
        print(comm.read_vin())
        comm.close()

Context Manager (Recommended)
-----------------------------
Use with statement for automatic cleanup::

    from AutoJ2534 import J2534Communications

    with J2534Communications(0, "chrys1") as comm:
        vin = comm.read_vin()
        print(f"VIN: {vin}")
    # Auto-disconnect and close on exit

Auto-Detection
--------------
Find and connect to responding ECU automatically::

    from AutoJ2534 import auto_detect_connect

    comm, info = auto_detect_connect()
    if comm:
        print(f"Connected to {info['tool_name']}")
        print(f"VIN: {comm.read_vin()}")

Traditional Usage
-----------------
For more control over the connection process::

    from AutoJ2534 import J2534Communications

    comm = J2534Communications()
    comm.numbered_tool_list()  # Show available devices

    if comm.open_communication(0, "chrys1"):
        response = comm.transmit_and_receive_message([0x3E, 0x00])
        print(f"Response: {response}")
        comm.disconnect()
        comm.close()

Module Contents
---------------
- interface: High-level J2534Communications class
- ecu_parameters: Pre-defined connection configurations
- negative_response_codes: UDS error code definitions

Version: 2.0.0
License: MIT
"""

__version__ = "2.0.0"
__author__ = "Original Authors, Refactored by Claude AI"

# =============================================================================
# Main Interface Exports
# =============================================================================

# Import the pre-instantiated communication object (legacy usage)
from AutoJ2534.interface import j2534_communication

# Import the class for creating custom instances
from AutoJ2534.interface import J2534Communications

# Import convenience functions for quick connections
from AutoJ2534.interface import quick_connect, auto_detect_connect

# =============================================================================
# Protocol Constants (for advanced users)
# =============================================================================

# RxStatus values for intermediate frames (continue reading)
RX_STATUS_INTERMEDIATE_FRAMES = [2, 9, 102, 258, 265]
"""RxStatus values indicating intermediate frames - continue reading."""

# RxStatus values for complete messages (done reading)
RX_STATUS_MESSAGE_COMPLETE = [0, 256]
"""RxStatus values indicating a complete message has been received."""

# SCI protocol IDs
SCI_PROTOCOL_IDS = [7, 8, 9, 10]
"""Protocol IDs for SCI communication."""

# ISO15765 protocol ID
ISO15765_PROTOCOL_ID = 6
"""Protocol ID for ISO15765 (CAN with transport layer)."""

# Positive response offset (service ID + 0x40 indicates positive response)
POSITIVE_RESPONSE_OFFSET = 0x40
"""Offset to add to service ID for positive response calculation."""

# Negative response service ID
NEGATIVE_RESPONSE_SERVICE_ID = 0x7F
"""Service ID indicating a negative response."""

# Response pending code
RESPONSE_PENDING_CODE = 0x78
"""Negative response code indicating ECU needs more time."""

# Buffer timeout error code from J2534
BUFFER_TIMEOUT_ERROR_CODE = 16
"""J2534 error code indicating buffer read timeout."""

# =============================================================================
# ECU Parameters Exports
# =============================================================================

# Import connection configurations
from AutoJ2534.ecu_parameters import (
    ConnectionConfig,
    Connections,
    create_custom_can_config,
)

# =============================================================================
# Negative Response Codes Exports
# =============================================================================

# Import UDS error code utilities
from AutoJ2534.negative_response_codes import (
    NegativeResponseCode,
    NEGATIVE_RESPONSE_DESCRIPTIONS,
    NEGATIVE_RESPONSE_CODES_HEX,
    get_negative_response_description,
    parse_negative_response,
)

# =============================================================================
# Backward Compatibility Aliases
# =============================================================================

# Old module names (deprecated but maintained for compatibility)
from AutoJ2534 import ecu_parameters as EcuParameters
from AutoJ2534 import interface as Interface

# =============================================================================
# Public API Definition
# =============================================================================

__all__ = [
    # Version info
    "__version__",
    "__author__",

    # Main interface
    "j2534_communication",
    "J2534Communications",

    # Convenience functions (NEW)
    "quick_connect",
    "auto_detect_connect",

    # RxStatus constants
    "RX_STATUS_INTERMEDIATE_FRAMES",
    "RX_STATUS_MESSAGE_COMPLETE",
    "SCI_PROTOCOL_IDS",
    "ISO15765_PROTOCOL_ID",
    "POSITIVE_RESPONSE_OFFSET",
    "NEGATIVE_RESPONSE_SERVICE_ID",
    "RESPONSE_PENDING_CODE",
    "BUFFER_TIMEOUT_ERROR_CODE",

    # ECU parameters
    "ConnectionConfig",
    "Connections",
    "create_custom_can_config",

    # Negative response codes
    "NegativeResponseCode",
    "NEGATIVE_RESPONSE_DESCRIPTIONS",
    "NEGATIVE_RESPONSE_CODES_HEX",
    "get_negative_response_description",
    "parse_negative_response",

    # Backward compatibility
    "EcuParameters",
    "Interface",
]
