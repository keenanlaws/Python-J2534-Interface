"""
J2534 DLL Interface Module
==========================

This module provides the low-level interface to J2534 PassThru DLLs.
It handles the ctypes function prototypes and DLL loading required to
communicate with J2534-compliant vehicle diagnostic interfaces.

The module defines:
    - PassThruLibrary: Wrapper class that binds to J2534 DLL functions
    - annotate_function: Helper to set up ctypes function prototypes
    - load_j2534_library: Function to load a J2534 DLL

Architecture:
    This module sits at the lowest level of the J2534 library stack.
    It is used by api.py which provides higher-level Python functions.

    ::

        Application Code
             |
        api.py (High-level Python functions)
             |
        dll_interface.py (ctypes DLL interface) <-- This module
             |
        J2534 DLL (Vehicle interface hardware vendor)

SAE J2534 Function Reference:
    The following functions are defined in SAE J2534-1 v04.04:

    - PassThruOpen: Open connection to device
    - PassThruClose: Close connection to device
    - PassThruConnect: Establish protocol channel
    - PassThruDisconnect: Close protocol channel
    - PassThruReadMsgs: Read messages from receive buffer
    - PassThruWriteMsgs: Write messages to transmit buffer
    - PassThruStartPeriodicMsg: Start periodic message transmission
    - PassThruStopPeriodicMsg: Stop periodic message transmission
    - PassThruStartMsgFilter: Create message filter
    - PassThruStopMsgFilter: Remove message filter
    - PassThruSetProgrammingVoltage: Control programming voltage
    - PassThruReadVersion: Read firmware/DLL version
    - PassThruGetLastError: Get last error description
    - PassThruIoctl: I/O control operations

Usage:
    This module is typically not used directly. Instead, use the
    functions exported from the J2534 package or the AutoJ2534
    high-level interface.

Example:
    Direct DLL access (advanced usage)::

        import ctypes
        from J2534.dll_interface import PassThruLibrary, load_j2534_library

        # Load the DLL
        dll = load_j2534_library("path/to/j2534.dll")
        if dll:
            library = PassThruLibrary(dll)

            # Now you can call functions directly
            device_id = ctypes.c_ulong()
            result = library.PassThruOpen(
                ctypes.c_void_p(None),
                ctypes.byref(device_id)
            )

Author: J2534-API Contributors
License: MIT
Version: 2.0.0

Sources:
    - SAE J2534-1 v04.04 Specification
    - https://github.com/diamondman/J2534-PassThru-Logger
"""

import ctypes
from typing import Optional, Dict, List, Any, Callable

from .structures import PassThruMessageStructure
from .config import j2534_config
from .logging_utils import debug_log


# =============================================================================
# DLL Function Annotation
# =============================================================================

def annotate_function(
    dll_wrapper: 'DllWrapper',
    function_name: str,
    argument_types: List[Any],
    return_type: Optional[Any] = None
) -> None:
    """
    Set up ctypes function prototype for a DLL function.

    This function configures the argument types and return type for a
    function in the loaded DLL, enabling type checking and automatic
    conversion by ctypes.

    Args:
        dll_wrapper: The DllWrapper instance containing the DLL reference.
        function_name: The name of the function in the DLL.
        argument_types: A list of ctypes types for the function arguments.
        return_type: The ctypes type for the return value. Defaults to
            c_long if not specified.

    Example:
        # >>> annotate_function(
        # ...     dll_wrapper,
        # ...     'PassThruOpen',
        # ...     [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        # ... )
    """
    # Get the function from the DLL
    function = getattr(dll_wrapper._dll, function_name)

    # Set argument types
    function.argtypes = argument_types

    # Set return type (default to c_long for J2534 functions)
    if return_type is None:
        return_type = ctypes.c_long
    function.restype = return_type

    # Make the function accessible on the wrapper
    setattr(dll_wrapper, function_name, function)


class DllWrapper:
    """
    Base class for ctypes DLL wrappers.

    This class provides the foundation for wrapping Windows DLLs using
    ctypes. It handles function prototype setup and provides a clean
    interface for accessing DLL functions.

    Attributes:
        _dll: The underlying ctypes DLL object.

    Example:
        Subclassing DllWrapper::

            class MyLibrary(DllWrapper):
                function_prototypes = {
                    'MyFunction': [[ctypes.c_int, ctypes.c_char_p]],
                }

                def __init__(self, dll):
                    super().__init__(dll, **self.function_prototypes)
    """

    def __init__(
        self,
        ctypes_dll: ctypes.WinDLL,
        **function_prototypes: Dict[str, List[Any]]
    ) -> None:
        """
        Initialize the DLL wrapper.

        Args:
            ctypes_dll: The ctypes.WinDLL object for the loaded DLL.
            **function_prototypes: Keyword arguments mapping function names
                to their prototypes. Each prototype is a list where:
                - The first element is a list of argument types
                - The optional second element is the return type

        Example:
            # >>> dll = ctypes.WinDLL("mylib.dll")
            # >>> wrapper = DllWrapper(dll, MyFunc=[[ctypes.c_int], ctypes.c_long])
        """
        self._dll = ctypes_dll

        # Set up function prototypes
        for function_name, prototype in function_prototypes.items():
            # Prototype format: [[argtypes], restype] or just [[argtypes]]
            argument_types = prototype[0] if prototype else []
            return_type = prototype[1] if len(prototype) > 1 else None
            annotate_function(self, function_name, argument_types, return_type)


# =============================================================================
# J2534 PassThru Library
# =============================================================================

class PassThruLibrary(DllWrapper):
    """
    Wrapper for J2534 PassThru DLL functions.

    This class provides access to all J2534-1 v04.04 API functions
    through a loaded PassThru DLL. It sets up the correct function
    prototypes based on the SAE J2534 specification.

    All 14 J2534 API Functions:
        - PassThruOpen: Open connection to J2534 device
        - PassThruClose: Close connection to J2534 device
        - PassThruConnect: Establish protocol channel
        - PassThruDisconnect: Close protocol channel
        - PassThruReadMsgs: Read messages from receive buffer
        - PassThruWriteMsgs: Write messages to transmit buffer
        - PassThruStartPeriodicMsg: Start periodic message
        - PassThruStopPeriodicMsg: Stop periodic message
        - PassThruStartMsgFilter: Create message filter
        - PassThruStopMsgFilter: Remove message filter
        - PassThruSetProgrammingVoltage: Control voltage output
        - PassThruReadVersion: Get version information
        - PassThruGetLastError: Get error description
        - PassThruIoctl: I/O control operations

    Attributes:
        default_restype: Default return type for functions (c_long).

    Example:
        # >>> import ctypes
        # >>> dll = ctypes.WinDLL("path/to/j2534.dll")
        # >>> library = PassThruLibrary(dll)
        # >>>
        # >>> # Open device
        # >>> device_id = ctypes.c_ulong()
        # >>> result = library.PassThruOpen(
        # ...     ctypes.c_void_p(None),
        # ...     ctypes.byref(device_id)
        # ... )
        # >>> if result == 0:
        # ...     print(f"Device ID: {device_id.value}")
    """

    # Function prototypes for J2534-1 v04.04 API
    # Format: 'FunctionName': [[argument_types], return_type]
    # If return_type is omitted, c_long is used (standard for J2534)
    function_prototypes: Dict[str, List[Any]] = {
        # =================================================================
        # Device Management Functions
        # =================================================================

        # PassThruOpen - Opens connection to a J2534 device
        # long PassThruOpen(void* pName, unsigned long* pDeviceID)
        # pName: Reserved, should be NULL
        # pDeviceID: Pointer to receive device ID
        'PassThruOpen': [[
            ctypes.c_void_p,              # pName (reserved, use NULL)
            ctypes.POINTER(ctypes.c_ulong)  # pDeviceID (out)
        ]],

        # PassThruClose - Closes connection to a J2534 device
        # long PassThruClose(unsigned long DeviceID)
        # DeviceID: Device ID from PassThruOpen
        'PassThruClose': [[
            ctypes.c_ulong                # DeviceID
        ]],

        # =================================================================
        # Channel Management Functions
        # =================================================================

        # PassThruConnect - Establishes a protocol channel
        # long PassThruConnect(
        #     unsigned long DeviceID,
        #     unsigned long ProtocolID,
        #     unsigned long Flags,
        #     unsigned long BaudRate,
        #     unsigned long* pChannelID
        # )
        'PassThruConnect': [[
            ctypes.c_ulong,               # DeviceID
            ctypes.c_ulong,               # ProtocolID
            ctypes.c_ulong,               # Flags
            ctypes.c_ulong,               # BaudRate
            ctypes.POINTER(ctypes.c_ulong)  # pChannelID (out)
        ]],

        # PassThruDisconnect - Closes a protocol channel
        # long PassThruDisconnect(unsigned long ChannelID)
        'PassThruDisconnect': [[
            ctypes.c_ulong                # ChannelID
        ]],

        # =================================================================
        # Message I/O Functions
        # =================================================================

        # PassThruReadMsgs - Reads messages from receive buffer
        # long PassThruReadMsgs(
        #     unsigned long ChannelID,
        #     PASSTHRU_MSG* pMsg,
        #     unsigned long* pNumMsgs,
        #     unsigned long Timeout
        # )
        'PassThruReadMsgs': [[
            ctypes.c_ulong,                           # ChannelID
            ctypes.POINTER(PassThruMessageStructure),  # pMsg (in/out)
            ctypes.POINTER(ctypes.c_ulong),           # pNumMsgs (in/out)
            ctypes.c_ulong                            # Timeout (ms)
        ]],

        # PassThruWriteMsgs - Writes messages to transmit buffer
        # long PassThruWriteMsgs(
        #     unsigned long ChannelID,
        #     PASSTHRU_MSG* pMsg,
        #     unsigned long* pNumMsgs,
        #     unsigned long Timeout
        # )
        'PassThruWriteMsgs': [[
            ctypes.c_ulong,                           # ChannelID
            ctypes.POINTER(PassThruMessageStructure),  # pMsg (in)
            ctypes.POINTER(ctypes.c_ulong),           # pNumMsgs (in/out)
            ctypes.c_ulong                            # Timeout (ms)
        ]],

        # =================================================================
        # Periodic Message Functions
        # =================================================================

        # PassThruStartPeriodicMsg - Starts periodic message transmission
        # long PassThruStartPeriodicMsg(
        #     unsigned long ChannelID,
        #     PASSTHRU_MSG* pMsg,
        #     unsigned long* pMsgID,
        #     unsigned long TimeInterval
        # )
        'PassThruStartPeriodicMsg': [[
            ctypes.c_ulong,                           # ChannelID
            ctypes.POINTER(PassThruMessageStructure),  # pMsg
            ctypes.POINTER(ctypes.c_ulong),           # pMsgID (out)
            ctypes.c_ulong                            # TimeInterval (ms)
        ]],

        # PassThruStopPeriodicMsg - Stops periodic message transmission
        # long PassThruStopPeriodicMsg(
        #     unsigned long ChannelID,
        #     unsigned long MsgID
        # )
        'PassThruStopPeriodicMsg': [[
            ctypes.c_ulong,               # ChannelID
            ctypes.c_ulong                # MsgID
        ]],

        # =================================================================
        # Message Filter Functions
        # =================================================================

        # PassThruStartMsgFilter - Creates a message filter
        # long PassThruStartMsgFilter(
        #     unsigned long ChannelID,
        #     unsigned long FilterType,
        #     PASSTHRU_MSG* pMaskMsg,
        #     PASSTHRU_MSG* pPatternMsg,
        #     PASSTHRU_MSG* pFlowControlMsg,
        #     unsigned long* pFilterID
        # )
        'PassThruStartMsgFilter': [[
            ctypes.c_ulong,                           # ChannelID
            ctypes.c_ulong,                           # FilterType
            ctypes.POINTER(PassThruMessageStructure),  # pMaskMsg
            ctypes.POINTER(PassThruMessageStructure),  # pPatternMsg
            ctypes.POINTER(PassThruMessageStructure),  # pFlowControlMsg (can be NULL)
            ctypes.POINTER(ctypes.c_ulong)            # pFilterID (out)
        ]],

        # PassThruStopMsgFilter - Removes a message filter
        # long PassThruStopMsgFilter(
        #     unsigned long ChannelID,
        #     unsigned long FilterID
        # )
        'PassThruStopMsgFilter': [[
            ctypes.c_ulong,               # ChannelID
            ctypes.c_ulong                # FilterID
        ]],

        # =================================================================
        # Voltage Control Function
        # =================================================================

        # PassThruSetProgrammingVoltage - Controls programming voltage
        # long PassThruSetProgrammingVoltage(
        #     unsigned long DeviceID,
        #     unsigned long PinNumber,
        #     unsigned long Voltage
        # )
        # Voltage in millivolts, or VOLTAGE_OFF/SHORT_TO_GROUND
        'PassThruSetProgrammingVoltage': [[
            ctypes.c_ulong,               # DeviceID
            ctypes.c_ulong,               # PinNumber
            ctypes.c_ulong                # Voltage (mV or special value)
        ]],

        # =================================================================
        # Information Functions
        # =================================================================

        # PassThruReadVersion - Reads version information
        # long PassThruReadVersion(
        #     unsigned long DeviceID,
        #     char* pFirmwareVersion,
        #     char* pDllVersion,
        #     char* pApiVersion
        # )
        # Each buffer should be at least 80 bytes
        'PassThruReadVersion': [[
            ctypes.c_ulong,               # DeviceID
            ctypes.c_char_p,              # pFirmwareVersion (out)
            ctypes.c_char_p,              # pDllVersion (out)
            ctypes.c_char_p               # pApiVersion (out)
        ]],

        # PassThruGetLastError - Gets last error description
        # long PassThruGetLastError(char* pErrorDescription)
        # Buffer should be at least 80 bytes
        'PassThruGetLastError': [[
            ctypes.c_char_p               # pErrorDescription (out)
        ]],

        # =================================================================
        # I/O Control Function
        # =================================================================

        # PassThruIoctl - General I/O control
        # long PassThruIoctl(
        #     unsigned long ChannelID,
        #     unsigned long IoctlID,
        #     void* pInput,
        #     void* pOutput
        # )
        'PassThruIoctl': [[
            ctypes.c_ulong,               # ChannelID (or DeviceID for some IOCTLs)
            ctypes.c_ulong,               # IoctlID
            ctypes.c_void_p,              # pInput (varies by IOCTL)
            ctypes.c_void_p               # pOutput (varies by IOCTL)
        ]]
    }

    def __init__(self, ctypes_dll: ctypes.WinDLL) -> None:
        """
        Initialize the PassThru library wrapper.

        Args:
            ctypes_dll: The ctypes.WinDLL object for the loaded J2534 DLL.

        Example:
            # >>> import ctypes
            # >>> dll = ctypes.WinDLL("path/to/j2534.dll")
            # >>> library = PassThruLibrary(dll)
        """
        # Default return type for all J2534 functions
        self.default_restype = ctypes.c_long

        # Initialize base class with function prototypes
        super().__init__(ctypes_dll, **self.function_prototypes)

        debug_log(
            f"PassThruLibrary initialized",
            function_name="PassThruLibrary.__init__"
        )


# =============================================================================
# DLL Loading Functions
# =============================================================================

def load_j2534_library(
    dll_path: str
) -> Optional[ctypes.WinDLL]:
    """
    Load a J2534 DLL from the specified path.

    This function attempts to load a Windows DLL using ctypes.WinDLL.
    It handles errors gracefully and returns None if loading fails.

    Args:
        dll_path: The full path to the J2534 DLL file.

    Returns:
        ctypes.WinDLL: The loaded DLL object if successful.
        None: If loading failed (e.g., file not found, invalid DLL).

    Example:
        # >>> dll = load_j2534_library("C:/Program Files/MyDevice/j2534.dll")
        # >>> if dll is not None:
        # ...     print("DLL loaded successfully")
        # ... else:
        # ...     print("Failed to load DLL")

    Note:
        On failure, if debug mode is enabled, the error is logged.
        If exceptions mode is enabled, an exception may be raised.
    """
    if dll_path is None:
        debug_log(
            "Cannot load DLL: path is None",
            function_name="load_j2534_library",
            level="error"
        )
        return None

    try:
        debug_log(
            f"Loading J2534 DLL from: {dll_path}",
            function_name="load_j2534_library"
        )

        dll = ctypes.WinDLL(dll_path)

        debug_log(
            f"Successfully loaded DLL: {dll_path}",
            function_name="load_j2534_library"
        )

        return dll

    except OSError as error:
        debug_log(
            f"Failed to load DLL '{dll_path}': {error}",
            function_name="load_j2534_library",
            level="error"
        )
        return None

    except Exception as error:
        debug_log(
            f"Unexpected error loading DLL '{dll_path}': {error}",
            function_name="load_j2534_library",
            level="error"
        )
        return None


# =============================================================================
# Backward Compatibility
# =============================================================================

# These aliases are provided for backward compatibility with code that
# uses the old module structure.

# Original type aliases from dll.py
PassThru_Data = ctypes.c_ubyte * 4128
"""Alias for backward compatibility. Use PassThruDataBuffer from structures.py instead."""

# Keep the original annotate function name as alias
annotate = annotate_function
"""Alias for backward compatibility. Use annotate_function instead."""

# Original class name alias
MyDll = DllWrapper
"""Alias for backward compatibility. Use DllWrapper instead."""
