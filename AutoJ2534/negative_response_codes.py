"""
UDS Negative Response Codes (NRC)
=================================

This module defines the standard negative response codes used in vehicle
diagnostic communication (UDS - Unified Diagnostic Services). These codes
are returned by ECUs when a diagnostic request cannot be fulfilled.

When an ECU cannot process a diagnostic request, it responds with a
negative response message in the format:

    0x7F <Request_SID> <NRC>

Where:
    - 0x7F is the negative response service identifier
    - Request_SID is the service ID from the original request
    - NRC is the Negative Response Code explaining why the request failed

Reference:
    ISO 14229-1: Unified Diagnostic Services (UDS)
    ISO 15765-3: UDS on CAN

Example:
    Interpreting a negative response::

        from AutoJ2534.negative_response_codes import (
            NegativeResponseCode,
            get_negative_response_description
        )

        # Response: 7F 22 31 means:
        # - 0x7F: Negative response
        # - 0x22: Original request was ReadDataByIdentifier (0x22)
        # - 0x31: Request Out Of Range

        response_data = "7F2231"
        nrc = int(response_data[4:6], 16)  # 0x31

        description = get_negative_response_description(nrc)
        print(f"Error: {description}")
        # Output: "Error: Request Out Of Range - The requested data ID is not valid"

Author: J2534-API Contributors
License: MIT
Version: 2.0.0
"""

from enum import IntEnum
from typing import Dict, Optional


class NegativeResponseCode(IntEnum):
    """
    UDS Negative Response Codes (NRC) as defined in ISO 14229-1.

    These codes indicate why a diagnostic service request was rejected
    by the ECU. Each code has a specific meaning that helps diagnose
    communication issues.

    Categories:
        General Responses (0x10-0x1F):
            Basic rejection reasons like service not supported.

        Security Related (0x33-0x37):
            Security access failures and key issues.

        Upload/Download (0x40-0x73):
            File transfer related errors.

        Response Pending (0x78):
            Special code indicating ECU needs more time.

        Session Related (0x7E-0x80):
            Service not available in current session.

        Voltage Related (0x92-0x93):
            Power supply issues.

    Example:
        # >>> from AutoJ2534.negative_response_codes import NegativeResponseCode
        # >>> nrc = NegativeResponseCode.SECURITY_ACCESS_DENIED
        # >>> print(f"Code: 0x{nrc:02X}")
        Code: 0x33
    """

    # =========================================================================
    # General Responses (0x10-0x2F)
    # =========================================================================

    GENERAL_REJECT = 0x10
    """
    General Reject (0x10)

    The ECU rejected the request without a specific reason. This is a
    catch-all response when no other NRC is applicable.
    """

    SERVICE_NOT_SUPPORTED = 0x11
    """
    Service Not Supported (0x11)

    The requested diagnostic service (SID) is not implemented in this ECU.
    The ECU does not recognize or support the service identifier.
    """

    SUB_FUNCTION_NOT_SUPPORTED = 0x12
    """
    Sub-Function Not Supported (0x12)

    The service is supported, but the specific sub-function requested
    is not implemented. Also used for invalid message format.
    """

    INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT = 0x13
    """
    Incorrect Message Length or Invalid Format (0x13)

    The message length doesn't match what's expected for this service,
    or the message format is invalid.
    """

    RESPONSE_TOO_LONG = 0x14
    """
    Response Too Long (0x14)

    The response message would exceed the maximum allowed length.
    """

    BUSY_REPEAT_REQUEST = 0x21
    """
    Busy - Repeat Request (0x21)

    The ECU is temporarily busy and cannot process the request.
    The tester should repeat the request after a short delay.
    """

    CONDITIONS_NOT_CORRECT = 0x22
    """
    Conditions Not Correct (0x22)

    The request cannot be executed because current conditions don't
    allow it. For example, vehicle speed too high, engine running, etc.
    """

    REQUEST_SEQUENCE_ERROR = 0x24
    """
    Request Sequence Error (0x24)

    The request was received out of sequence. Some services require
    specific sequences of requests (e.g., security access).
    """

    NO_RESPONSE_FROM_SUBNET_COMPONENT = 0x25
    """
    No Response From Subnet Component (0x25)

    A gateway ECU could not get a response from the target ECU on
    another network segment.
    """

    FAILURE_PREVENTS_EXECUTION = 0x26
    """
    Failure Prevents Execution of Requested Action (0x26)

    An internal failure in the ECU prevents executing the request.
    """

    # =========================================================================
    # Request Out of Range (0x31)
    # =========================================================================

    REQUEST_OUT_OF_RANGE = 0x31
    """
    Request Out Of Range (0x31)

    The requested data identifier, routine identifier, or parameter
    value is not valid or outside the acceptable range.
    """

    # =========================================================================
    # Security Related (0x33-0x37)
    # =========================================================================

    SECURITY_ACCESS_DENIED = 0x33
    """
    Security Access Denied (0x33)

    The requested action requires security access that has not been
    granted. Security unlock is required before this service.
    """

    INVALID_KEY = 0x35
    """
    Invalid Key (0x35)

    The security key provided in a SecurityAccess response was
    incorrect. The unlock attempt failed.
    """

    EXCEEDED_NUMBER_OF_ATTEMPTS = 0x36
    """
    Exceeded Number of Attempts (0x36)

    Too many failed security access attempts. The ECU has locked
    out further attempts for a period of time.
    """

    REQUIRED_TIME_DELAY_NOT_EXPIRED = 0x37
    """
    Required Time Delay Not Expired (0x37)

    A required time delay between security access attempts has not
    yet expired. Wait before trying again.
    """

    # =========================================================================
    # Upload/Download Related (0x40-0x73)
    # =========================================================================

    UPLOAD_DOWNLOAD_NOT_ACCEPTED = 0x70
    """
    Upload/Download Not Accepted (0x70)

    The ECU cannot accept an upload or download request. Conditions
    may not be correct for data transfer.
    """

    TRANSFER_DATA_SUSPENDED = 0x71
    """
    Transfer Data Suspended (0x71)

    The data transfer has been suspended due to an error or
    interruption.
    """

    GENERAL_PROGRAMMING_FAILURE = 0x72
    """
    General Programming Failure (0x72)

    A non-specific failure occurred during ECU programming.
    The flash/EEPROM write may have failed.
    """

    WRONG_BLOCK_SEQUENCE_COUNTER = 0x73
    """
    Wrong Block Sequence Counter (0x73)

    The block sequence counter in a TransferData request doesn't
    match what the ECU expected.
    """

    # =========================================================================
    # Response Pending (0x78)
    # =========================================================================

    REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING = 0x78
    """
    Request Correctly Received - Response Pending (0x78)

    The ECU has received the request but needs more time to process it.
    The tester should wait for the actual response. This is NOT an error.
    """

    # =========================================================================
    # Session Related (0x7E-0x80)
    # =========================================================================

    SUB_FUNCTION_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7E
    """
    Sub-Function Not Supported in Active Session (0x7E)

    The sub-function is valid but not available in the current
    diagnostic session. Change session first.
    """

    SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7F
    """
    Service Not Supported in Active Session (0x7F)

    The service is valid but not available in the current diagnostic
    session. Change to appropriate session first.
    """

    SERVICE_NOT_SUPPORTED_IN_ACTIVE_DIAGNOSTIC_MODE = 0x80
    """
    Service Not Supported in Active Diagnostic Mode (0x80)

    Similar to 0x7F but refers to diagnostic mode rather than session.
    """

    # =========================================================================
    # Voltage Related (0x92-0x93)
    # =========================================================================

    VOLTAGE_TOO_HIGH = 0x92
    """
    Voltage Too High (0x92)

    The supply voltage is too high to safely execute the request.
    This is often checked before programming operations.
    """

    VOLTAGE_TOO_LOW = 0x93
    """
    Voltage Too Low (0x93)

    The supply voltage is too low to safely execute the request.
    Programming operations require adequate voltage.
    """

    # =========================================================================
    # Extended Codes (0x9A-0xA1)
    # =========================================================================

    DATA_DECOMPRESSION_FAILED = 0x9A
    """
    Data Decompression Failed (0x9A)

    The ECU failed to decompress uploaded data.
    """

    DATA_DECRYPTION_FAILED = 0x9B
    """
    Data Decryption Failed (0x9B)

    The ECU failed to decrypt uploaded data.
    """

    ECU_NOT_RESPONDING = 0xA0
    """
    ECU Not Responding (0xA0)

    Manufacturer-specific: The target ECU is not responding.
    """

    ECU_ADDRESS_UNKNOWN = 0xA1
    """
    ECU Address Unknown (0xA1)

    Manufacturer-specific: The target ECU address is not recognized.
    """

    # =========================================================================
    # Key Management (0xFA-0xFB)
    # =========================================================================

    REVOKED_KEY = 0xFA
    """
    Revoked Key (0xFA)

    The security key has been revoked and is no longer valid.
    """

    EXPIRED_KEY = 0xFB
    """
    Expired Key (0xFB)

    The security key has expired and is no longer valid.
    """


# =============================================================================
# Descriptions Dictionary
# =============================================================================

NEGATIVE_RESPONSE_DESCRIPTIONS: Dict[int, str] = {
    NegativeResponseCode.GENERAL_REJECT:
        "General Reject - Request rejected without specific reason",

    NegativeResponseCode.SERVICE_NOT_SUPPORTED:
        "Service Not Supported - The requested service is not implemented",

    NegativeResponseCode.SUB_FUNCTION_NOT_SUPPORTED:
        "Sub-Function Not Supported / Invalid Format - Sub-function not implemented or invalid message format",

    NegativeResponseCode.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT:
        "Incorrect Message Length or Invalid Format - Message structure is invalid",

    NegativeResponseCode.RESPONSE_TOO_LONG:
        "Response Too Long - Response would exceed maximum message length",

    NegativeResponseCode.BUSY_REPEAT_REQUEST:
        "Busy - Repeat Request - ECU is busy, try again later",

    NegativeResponseCode.CONDITIONS_NOT_CORRECT:
        "Conditions Not Correct - Current conditions prevent execution",

    NegativeResponseCode.REQUEST_SEQUENCE_ERROR:
        "Request Sequence Error - Request received out of expected sequence",

    NegativeResponseCode.NO_RESPONSE_FROM_SUBNET_COMPONENT:
        "No Response From Subnet Component - Gateway could not reach target ECU",

    NegativeResponseCode.FAILURE_PREVENTS_EXECUTION:
        "Failure Prevents Execution - Internal failure prevents execution",

    NegativeResponseCode.REQUEST_OUT_OF_RANGE:
        "Request Out Of Range - Requested data ID or parameter is invalid",

    NegativeResponseCode.SECURITY_ACCESS_DENIED:
        "Security Access Denied - Security unlock required",

    NegativeResponseCode.INVALID_KEY:
        "Invalid Key - Security key was incorrect",

    NegativeResponseCode.EXCEEDED_NUMBER_OF_ATTEMPTS:
        "Exceeded Number of Attempts - Too many failed attempts, locked out",

    NegativeResponseCode.REQUIRED_TIME_DELAY_NOT_EXPIRED:
        "Required Time Delay Not Expired - Wait before retrying",

    NegativeResponseCode.UPLOAD_DOWNLOAD_NOT_ACCEPTED:
        "Upload/Download Not Accepted - Transfer cannot proceed",

    NegativeResponseCode.TRANSFER_DATA_SUSPENDED:
        "Transfer Data Suspended - Data transfer has been suspended",

    NegativeResponseCode.GENERAL_PROGRAMMING_FAILURE:
        "General Programming Failure - Flash/EEPROM write failed",

    NegativeResponseCode.WRONG_BLOCK_SEQUENCE_COUNTER:
        "Wrong Block Sequence Counter - Block counter mismatch",

    NegativeResponseCode.REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING:
        "Response Pending - ECU needs more time, wait for response",

    NegativeResponseCode.SUB_FUNCTION_NOT_SUPPORTED_IN_ACTIVE_SESSION:
        "Sub-Function Not Supported in Active Session - Change session first",

    NegativeResponseCode.SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION:
        "Service Not Supported in Active Session - Change session first",

    NegativeResponseCode.SERVICE_NOT_SUPPORTED_IN_ACTIVE_DIAGNOSTIC_MODE:
        "Service Not Supported in Active Diagnostic Mode - Change mode first",

    NegativeResponseCode.VOLTAGE_TOO_HIGH:
        "Voltage Too High - Supply voltage exceeds safe limit",

    NegativeResponseCode.VOLTAGE_TOO_LOW:
        "Voltage Too Low - Supply voltage below safe limit",

    NegativeResponseCode.DATA_DECOMPRESSION_FAILED:
        "Data Decompression Failed - Could not decompress uploaded data",

    NegativeResponseCode.DATA_DECRYPTION_FAILED:
        "Data Decryption Failed - Could not decrypt uploaded data",

    NegativeResponseCode.ECU_NOT_RESPONDING:
        "ECU Not Responding - Target ECU is not responding",

    NegativeResponseCode.ECU_ADDRESS_UNKNOWN:
        "ECU Address Unknown - Target ECU address not recognized",

    NegativeResponseCode.REVOKED_KEY:
        "Revoked Key - Security key has been revoked",

    NegativeResponseCode.EXPIRED_KEY:
        "Expired Key - Security key has expired",
}


# Hex string to description mapping (for compatibility with existing code)
NEGATIVE_RESPONSE_CODES_HEX: Dict[str, str] = {
    "10": "General Reject",
    "11": "Service Not Supported",
    "12": "Sub-Function Not Supported / Invalid Format",
    "13": "Incorrect Message Length or Invalid Format",
    "14": "Response Too Long",
    "21": "Busy - Repeat Request",
    "22": "Conditions Not Correct",
    "24": "Request Sequence Error",
    "25": "No Response From Subnet Component",
    "26": "Failure Prevents Execution of Requested Action",
    "31": "Request Out Of Range",
    "33": "Security Access Denied",
    "35": "Invalid Key",
    "36": "Exceeded Number of Attempts",
    "37": "Required Time Delay Not Expired",
    "40": "Download Not Accepted",
    "50": "Upload Not Accepted",
    "70": "Upload/Download Not Accepted",
    "71": "Transfer Data Suspended",
    "72": "General Programming Failure",
    "73": "Wrong Block Sequence Counter",
    "78": "Request Correctly Received - Response Pending",
    "7E": "Sub-Function Not Supported In Active Session",
    "7F": "Service Not Supported In Active Session",
    "80": "Service Not Supported In Active Diagnostic Mode",
    "92": "Voltage Too High",
    "93": "Voltage Too Low",
    "9A": "Data Decompression Failed",
    "9B": "Data Decryption Failed",
    "A0": "ECU Not Responding",
    "A1": "ECU Address Unknown",
    "FA": "Revoked Key",
    "FB": "Expired Key",
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_negative_response_description(nrc_code: int) -> str:
    """
    Get a human-readable description for a negative response code.

    Args:
        nrc_code: The numeric NRC code (e.g., 0x22, 0x33).

    Returns:
        str: A description of the error. Returns "Unknown NRC" if the
            code is not recognized.

    Example:
        # >>> desc = get_negative_response_description(0x22)
        # >>> print(desc)
        Conditions Not Correct - Current conditions prevent execution
    """
    return NEGATIVE_RESPONSE_DESCRIPTIONS.get(
        nrc_code,
        f"Unknown NRC: 0x{nrc_code:02X}"
    )


def get_negative_response_description_hex(hex_string: str) -> str:
    """
    Get a description for a negative response code given as hex string.

    This function is provided for compatibility with code that works
    with hex string representations of NRC codes.

    Args:
        hex_string: The NRC code as a two-character hex string (e.g., "22").

    Returns:
        str: A description of the error. Returns "Unknown NRC" if the
            code is not recognized.

    Example:
        # >>> desc = get_negative_response_description_hex("22")
        # >>> print(desc)
        Conditions Not Correct
    """
    return NEGATIVE_RESPONSE_CODES_HEX.get(
        hex_string.upper(),
        f"Unknown NRC: {hex_string}"
    )


def is_response_pending(nrc_code: int) -> bool:
    """
    Check if the NRC indicates "Response Pending".

    The 0x78 NRC is special - it means the ECU received the request
    but needs more time. The tester should wait for the actual response.

    Args:
        nrc_code: The numeric NRC code.

    Returns:
        bool: True if this is a Response Pending indication.

    Example:
        # >>> if is_response_pending(0x78):
        # ...     print("ECU needs more time, waiting...")
    """
    return nrc_code == NegativeResponseCode.REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING


def parse_negative_response(response_data: str) -> Optional[Dict[str, any]]:
    """
    Parse a negative response message and extract details.

    Takes a hex string of the response data and extracts the service ID
    that was rejected and the reason code.

    Args:
        response_data: The response data as a hex string (e.g., "7F2231").

    Returns:
        dict: A dictionary with keys:
            - 'service_id': The rejected service ID (int)
            - 'nrc_code': The NRC code (int)
            - 'nrc_hex': The NRC as hex string (str)
            - 'description': Human-readable description (str)
            - 'is_response_pending': True if this is 0x78 (bool)
        Returns None if the response is not a negative response.

    Example:
        # >>> info = parse_negative_response("7F2231")
        # >>> print(f"Service 0x{info['service_id']:02X} rejected: {info['description']}")
        Service 0x22 rejected: Request Out Of Range
    """
    if len(response_data) < 6:
        return None

    if response_data[:2].upper() != "7F":
        return None

    try:
        service_id = int(response_data[2:4], 16)
        nrc_code = int(response_data[4:6], 16)

        return {
            'service_id': service_id,
            'nrc_code': nrc_code,
            'nrc_hex': f"{nrc_code:02X}",
            'description': get_negative_response_description(nrc_code),
            'is_response_pending': is_response_pending(nrc_code)
        }
    except ValueError:
        return None
