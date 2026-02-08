"""
J2534 Registry Scanner Module
=============================

Scans Windows registry for installed J2534 PassThru devices according to
the SAE J2534-1 v04.04 specification.

This module provides functionality to:
    - Enumerate all J2534 devices registered in Windows
    - Query device capabilities and protocol support
    - Validate DLL file existence
    - Search devices by name or protocol

Registry Structure:
    J2534 devices register under HKEY_LOCAL_MACHINE at the path
    ``Software\\PassThruSupport.04.04\\{DeviceName}`` (32-bit Windows) or
    ``Software\\Wow6432Node\\PassThruSupport.04.04\\{DeviceName}`` (64-bit Windows).

    Each device subkey contains string values (Name, Vendor, FunctionLibrary,
    ConfigApplication) and DWORD protocol support flags (CAN, ISO15765, etc.).

Example:
    >>> from J2534_REGISTRY import get_all_j2534_devices, find_device_by_name
    >>>
    >>> # List all devices
    >>> devices = get_all_j2534_devices()
    >>> for device in devices:
    ...     print(f"{device.name}: {device.function_library_path}")
    >>>
    >>> # Find specific device
    >>> mongoose = find_device_by_name("Mongoose")
    >>> if mongoose:
    ...     print(f"Mongoose supports: {mongoose.supported_protocols}")

Version: 2.0.0
License: MIT
"""

import winreg
import platform
import os
from typing import List, Optional, Dict, Any

from J2534_REGISTRY.device_info import J2534DeviceInfo


# =============================================================================
# Registry Path Constants
# =============================================================================

REGISTRY_PATH_64BIT = r"Software\Wow6432Node\PassThruSupport.04.04"
"""
Registry path for J2534 devices on 64-bit Windows.

On 64-bit Windows, 32-bit applications (including J2534 DLLs) register
under the Wow6432Node virtualization layer. This is the standard
SAE J2534-1 v04.04 registry location.

Full path: HKEY_LOCAL_MACHINE\\Software\\Wow6432Node\\PassThruSupport.04.04\\
"""

REGISTRY_PATH_32BIT = r"Software\PassThruSupport.04.04"
"""
Registry path for J2534 devices on 32-bit Windows.

On native 32-bit Windows, J2534 devices register directly under
this path without the Wow6432Node virtualization layer.

Full path: HKEY_LOCAL_MACHINE\\Software\\PassThruSupport.04.04\\
"""


# =============================================================================
# Registry Value Name Constants
# =============================================================================

REG_VALUE_NAME = "Name"
"""Device display name (REG_SZ). Example: 'Drew Technologies Mongoose Pro'"""

REG_VALUE_VENDOR = "Vendor"
"""Device vendor/manufacturer name (REG_SZ). Example: 'Drew Technologies'"""

REG_VALUE_FUNCTION_LIBRARY = "FunctionLibrary"
"""Full path to J2534 DLL file (REG_SZ). Example: 'C:\\Program Files\\Drew\\mongi32.dll'"""

REG_VALUE_CONFIG_APPLICATION = "ConfigApplication"
"""Path to vendor configuration utility (REG_SZ, optional). May be empty or missing."""


# =============================================================================
# Protocol Support Flag Constants (REG_DWORD: 0=not supported, 1=supported)
# =============================================================================

REG_VALUE_CAN = "CAN"
"""CAN protocol support flag (ISO 11898 Controller Area Network)."""

REG_VALUE_ISO15765 = "ISO15765"
"""ISO 15765 protocol support flag (CAN-based diagnostics, ISO-TP transport layer)."""

REG_VALUE_J1850VPW = "J1850VPW"
"""J1850 VPW protocol support flag (Variable Pulse Width, used by GM vehicles pre-2008)."""

REG_VALUE_J1850PWM = "J1850PWM"
"""J1850 PWM protocol support flag (Pulse Width Modulation, used by Ford vehicles pre-2008)."""

REG_VALUE_ISO9141 = "ISO9141"
"""ISO 9141-2 protocol support flag (K-line, older European/Asian vehicles)."""

REG_VALUE_ISO14230 = "ISO14230"
"""ISO 14230-4 protocol support flag (KWP2000, European vehicles)."""

REG_VALUE_SCI_A_ENGINE = "SCI_A_ENGINE"
"""Chrysler SCI-A Engine protocol support (7,812.5 baud, older Chrysler vehicles)."""

REG_VALUE_SCI_A_TRANS = "SCI_A_TRANS"
"""Chrysler SCI-A Transmission protocol support (7,812.5 baud)."""

REG_VALUE_SCI_B_ENGINE = "SCI_B_ENGINE"
"""Chrysler SCI-B Engine protocol support (62,500 baud high-speed, newer Chrysler)."""

REG_VALUE_SCI_B_TRANS = "SCI_B_TRANS"
"""Chrysler SCI-B Transmission protocol support (62,500 baud high-speed)."""


class J2534RegistryScanner:
    """
    Scanner for J2534 PassThru devices registered in Windows registry.

    This class provides methods to discover and enumerate J2534 devices
    installed on the system. It reads the standard SAE J2534-1 v04.04
    registry locations and extracts device information including:

    - Device name and vendor
    - DLL (Function Library) path
    - Configuration application path
    - Protocol support flags (CAN, ISO15765, J1850, ISO9141, etc.)

    Registry Structure::

        HKEY_LOCAL_MACHINE
        └── Software
            └── [Wow6432Node\\]  # On 64-bit Windows
                └── PassThruSupport.04.04
                    └── {DeviceName}
                        ├── Name              (REG_SZ)
                        ├── Vendor            (REG_SZ)
                        ├── FunctionLibrary   (REG_SZ)
                        ├── ConfigApplication (REG_SZ, optional)
                        ├── CAN               (REG_DWORD)
                        ├── ISO15765          (REG_DWORD)
                        └── ... (other protocol flags)

    Caching Behavior:
        The scanner caches device information after the first query for
        performance. The cache persists for the lifetime of the scanner
        instance. Use ``refresh_cache()`` or pass ``use_cache=False`` to
        force a fresh registry scan.

        - First call to ``get_all_devices()`` reads from registry and caches
        - Subsequent calls return cached data instantly
        - Install/uninstall of devices requires ``refresh_cache()``

    Thread Safety:
        This class is NOT thread-safe. If accessing from multiple threads,
        external synchronization is required.

    Example:
        Basic usage::

            scanner = J2534RegistryScanner()

            # Get all registered devices
            devices = scanner.get_all_devices()
            for device in devices:
                print(f"{device.name}: {device.function_library_path}")

            # Find devices supporting CAN
            can_devices = scanner.get_devices_by_protocol("CAN")

            # Find by name (partial match)
            mongoose = scanner.get_device_by_name("Mongoose")

            # Get only devices with valid DLL files
            valid = scanner.get_valid_devices()

            # Force refresh after installing new device
            scanner.refresh_cache()

    Attributes:
        _registry_path (str): The registry path being used (32-bit or 64-bit)
        _cached_devices (Optional[List[J2534DeviceInfo]]): Cached device list

    See Also:
        - J2534DeviceInfo: Dataclass containing device information
        - get_all_j2534_devices(): Convenience function using default scanner
    """

    def __init__(self):
        """
        Initialize the registry scanner.

        Automatically determines the correct registry path based on the
        Python interpreter architecture (32-bit or 64-bit).
        """
        self._registry_path = self._determine_registry_path()
        self._cached_devices: Optional[List[J2534DeviceInfo]] = None

    @staticmethod
    def _determine_registry_path() -> str:
        """
        Determine the correct registry path based on system architecture.

        On 64-bit Windows, 32-bit Python uses the Wow6432Node virtualization
        layer. Since J2534 DLLs are typically 32-bit, we check the Python
        interpreter architecture to determine the correct registry path.

        Returns:
            str: REGISTRY_PATH_64BIT for 64-bit Python,
                 REGISTRY_PATH_32BIT for 32-bit Python

        Note:
            This checks the Python interpreter architecture, not the OS
            architecture. 32-bit Python on 64-bit Windows uses the 32-bit path.
        """
        if platform.architecture()[0] == "32bit":
            return REGISTRY_PATH_32BIT
        return REGISTRY_PATH_64BIT

    def _read_registry_value(self, key: Any, value_name: str, default: Any = None) -> Any:
        """
        Safely read a value from an open registry key.

        This method wraps winreg.QueryValueEx with exception handling for
        graceful handling of missing or inaccessible registry values.

        Args:
            key: Open registry key handle (from winreg.OpenKeyEx)
            value_name: Name of the registry value to read
            default: Value to return if the key doesn't exist or read fails

        Returns:
            The registry value if successful, or the default value on failure.
            String values (REG_SZ) return as str, DWORD values return as int.

        Note:
            Catches WindowsError and FileNotFoundError silently, returning
            the default value. This allows graceful handling of optional
            registry values like ConfigApplication.
        """
        try:
            value, _ = winreg.QueryValueEx(key, value_name)
            return value
        except (WindowsError, FileNotFoundError):
            return default

    def _read_device_info(self, device_key: Any, device_id: int, key_path: str) -> J2534DeviceInfo:
        """
        Read all device information from an open registry key.

        This method reads all standard J2534 registry values and constructs
        a J2534DeviceInfo dataclass instance with the complete device profile.

        The method reads:
            - Name, Vendor: Device identification strings
            - FunctionLibrary: Path to J2534 DLL
            - ConfigApplication: Path to config tool (optional)
            - Protocol flags: CAN, ISO15765, J1850VPW, J1850PWM, ISO9141,
              ISO14230, SCI_A_ENGINE, SCI_A_TRANS, SCI_B_ENGINE, SCI_B_TRANS

        Args:
            device_key: Open registry key handle for the device subkey
            device_id: Index of this device in the registry enumeration
            key_path: Full registry path to this device's key

        Returns:
            J2534DeviceInfo: Complete device information dataclass

        Note:
            - Missing protocol flags default to False (not supported)
            - The can_iso15765 combined flag is True if either CAN or
              ISO15765 is supported, as these protocols are closely related
            - Missing string values use sensible defaults ("Unknown Device", "")
        """
        name = self._read_registry_value(device_key, REG_VALUE_NAME, "Unknown Device")
        vendor = self._read_registry_value(device_key, REG_VALUE_VENDOR, "")
        function_library = self._read_registry_value(device_key, REG_VALUE_FUNCTION_LIBRARY, "")
        config_app = self._read_registry_value(device_key, REG_VALUE_CONFIG_APPLICATION)

        can_support = bool(self._read_registry_value(device_key, REG_VALUE_CAN, 0))
        iso15765_support = bool(self._read_registry_value(device_key, REG_VALUE_ISO15765, 0))
        j1850vpw_support = bool(self._read_registry_value(device_key, REG_VALUE_J1850VPW, 0))
        j1850pwm_support = bool(self._read_registry_value(device_key, REG_VALUE_J1850PWM, 0))
        iso9141_support = bool(self._read_registry_value(device_key, REG_VALUE_ISO9141, 0))
        iso14230_support = bool(self._read_registry_value(device_key, REG_VALUE_ISO14230, 0))
        sci_a_engine_support = bool(self._read_registry_value(device_key, REG_VALUE_SCI_A_ENGINE, 0))
        sci_a_trans_support = bool(self._read_registry_value(device_key, REG_VALUE_SCI_A_TRANS, 0))
        sci_b_engine_support = bool(self._read_registry_value(device_key, REG_VALUE_SCI_B_ENGINE, 0))
        sci_b_trans_support = bool(self._read_registry_value(device_key, REG_VALUE_SCI_B_TRANS, 0))

        supported_protocols = []
        if can_support:
            supported_protocols.append("CAN")
        if iso15765_support:
            supported_protocols.append("ISO15765")
        if j1850vpw_support:
            supported_protocols.append("J1850VPW")
        if j1850pwm_support:
            supported_protocols.append("J1850PWM")
        if iso9141_support:
            supported_protocols.append("ISO9141")
        if iso14230_support:
            supported_protocols.append("ISO14230")
        if sci_a_engine_support:
            supported_protocols.append("SCI_A_ENGINE")
        if sci_a_trans_support:
            supported_protocols.append("SCI_A_TRANS")
        if sci_b_engine_support:
            supported_protocols.append("SCI_B_ENGINE")
        if sci_b_trans_support:
            supported_protocols.append("SCI_B_TRANS")

        return J2534DeviceInfo(
            name=name,
            vendor=vendor,
            function_library_path=function_library,
            config_application_path=config_app,
            supported_protocols=supported_protocols,
            can_iso15765=can_support or iso15765_support,
            j1850vpw=j1850vpw_support,
            j1850pwm=j1850pwm_support,
            iso9141=iso9141_support,
            iso14230=iso14230_support,
            sci_a_engine=sci_a_engine_support,
            sci_a_trans=sci_a_trans_support,
            sci_b_engine=sci_b_engine_support,
            sci_b_trans=sci_b_trans_support,
            device_id=device_id,
            registry_key_path=key_path,
        )

    def get_all_devices(self, use_cache: bool = True) -> List[J2534DeviceInfo]:
        """
        Get information about all registered J2534 devices.

        Scans the Windows registry for installed J2534 PassThru devices
        and returns a list of J2534DeviceInfo objects with complete
        device information.

        Args:
            use_cache: If True (default), return cached results if available.
                       If False, force a fresh registry scan.

        Returns:
            List[J2534DeviceInfo]: List of all registered devices.
            Returns empty list if no devices found or registry access fails.

        Example:
            >>> scanner = J2534RegistryScanner()
            >>> devices = scanner.get_all_devices()
            >>> print(f"Found {len(devices)} device(s)")

            >>> # Force fresh scan after installing new device
            >>> devices = scanner.get_all_devices(use_cache=False)

        Note:
            The first call populates the cache. Subsequent calls with
            use_cache=True return the cached list for better performance.
            Call refresh_cache() after installing/uninstalling J2534 devices.
        """
        if use_cache and self._cached_devices is not None:
            return self._cached_devices

        devices = []
        try:
            base_key = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, self._registry_path)
        except (WindowsError, FileNotFoundError):
            self._cached_devices = []
            return []

        try:
            num_subkeys = winreg.QueryInfoKey(base_key)[0]
            for device_index in range(num_subkeys):
                try:
                    subkey_name = winreg.EnumKey(base_key, device_index)
                    key_path = f"{self._registry_path}\\{subkey_name}"
                    device_key = winreg.OpenKeyEx(base_key, subkey_name)
                    device_info = self._read_device_info(device_key, device_index, key_path)
                    devices.append(device_info)
                    winreg.CloseKey(device_key)
                except (WindowsError, FileNotFoundError):
                    continue
        finally:
            winreg.CloseKey(base_key)

        self._cached_devices = devices
        return devices

    def get_device_by_name(self, name: str, partial_match: bool = True) -> Optional[J2534DeviceInfo]:
        """
        Find a device by its display name.

        Searches registered devices for a matching name. By default,
        performs a case-insensitive partial match.

        Args:
            name: Device name or partial name to search for
            partial_match: If True (default), match if name appears anywhere
                           in the device name (case-insensitive).
                           If False, require exact match (case-insensitive).

        Returns:
            J2534DeviceInfo if found, None if no match

        Example:
            >>> scanner = J2534RegistryScanner()

            >>> # Partial match (default) - finds "Drew Technologies Mongoose"
            >>> device = scanner.get_device_by_name("Mongoose")

            >>> # Exact match
            >>> device = scanner.get_device_by_name(
            ...     "Drew Technologies Mongoose",
            ...     partial_match=False
            ... )

        Note:
            Returns the first matching device. If multiple devices match
            a partial search, use get_all_devices() and filter manually.
        """
        devices = self.get_all_devices()
        name_lower = name.lower()
        for device in devices:
            device_name_lower = device.name.lower()
            if partial_match:
                if name_lower in device_name_lower:
                    return device
            else:
                if name_lower == device_name_lower:
                    return device
        return None

    def get_devices_by_protocol(self, protocol: str) -> List[J2534DeviceInfo]:
        """
        Find all devices that support a specific protocol.

        Args:
            protocol: Protocol name to filter by. Valid values:
                      "CAN", "ISO15765", "J1850VPW", "J1850PWM",
                      "ISO9141", "ISO14230", "SCI_A_ENGINE",
                      "SCI_A_TRANS", "SCI_B_ENGINE", "SCI_B_TRANS"

        Returns:
            List[J2534DeviceInfo]: Devices supporting the specified protocol.
            Returns empty list if no devices support the protocol.

        Example:
            >>> scanner = J2534RegistryScanner()

            >>> # Find all CAN-capable devices
            >>> can_devices = scanner.get_devices_by_protocol("CAN")
            >>> for d in can_devices:
            ...     print(f"{d.name} supports CAN")

            >>> # Find Chrysler SCI devices
            >>> sci_devices = scanner.get_devices_by_protocol("SCI_A_ENGINE")

        Note:
            Protocol matching uses the device's supports_protocol() method,
            which performs case-insensitive comparison.
        """
        devices = self.get_all_devices()
        return [d for d in devices if d.supports_protocol(protocol)]

    def get_device_by_index(self, index: int) -> Optional[J2534DeviceInfo]:
        """
        Get a device by its enumeration index.

        Args:
            index: Zero-based index of the device in the registry enumeration

        Returns:
            J2534DeviceInfo if index is valid, None if out of range

        Example:
            >>> scanner = J2534RegistryScanner()
            >>> first_device = scanner.get_device_by_index(0)
            >>> if first_device:
            ...     print(f"First device: {first_device.name}")
        """
        devices = self.get_all_devices()
        if 0 <= index < len(devices):
            return devices[index]
        return None

    def get_device_count(self) -> int:
        """
        Get the total number of registered J2534 devices.

        Returns:
            int: Number of devices found in the registry
        """
        return len(self.get_all_devices())

    def refresh_cache(self) -> List[J2534DeviceInfo]:
        """
        Force refresh of the device cache.

        Clears the cached device list and performs a fresh registry scan.
        Use this after installing or uninstalling J2534 device drivers.

        Returns:
            List[J2534DeviceInfo]: Fresh list of all registered devices

        Example:
            >>> scanner = J2534RegistryScanner()
            >>> # After installing a new device driver...
            >>> scanner.refresh_cache()
            >>> print(f"Now have {scanner.get_device_count()} devices")
        """
        self._cached_devices = None
        return self.get_all_devices(use_cache=False)

    def get_device_names(self) -> List[str]:
        """
        Get list of all device display names.

        Returns:
            List[str]: List of device names in enumeration order

        Example:
            >>> scanner = J2534RegistryScanner()
            >>> for name in scanner.get_device_names():
            ...     print(name)
        """
        return [d.name for d in self.get_all_devices()]

    def get_device_dll_paths(self) -> Dict[str, str]:
        """
        Get mapping of device names to their DLL paths.

        Returns:
            Dict[str, str]: Dictionary mapping device name to FunctionLibrary path

        Example:
            >>> scanner = J2534RegistryScanner()
            >>> paths = scanner.get_device_dll_paths()
            >>> print(paths.get("Drew Technologies Mongoose"))
            # 'C:\\Program Files\\Drew\\mongi32.dll'
        """
        return {d.name: d.function_library_path for d in self.get_all_devices()}

    def verify_dll_exists(self, device: J2534DeviceInfo) -> bool:
        """
        Check if the device's DLL file actually exists on disk.

        This validates that the registered FunctionLibrary path points to
        an existing file. Devices with missing DLLs cannot be used.

        Args:
            device: J2534DeviceInfo object to validate

        Returns:
            bool: True if DLL file exists, False otherwise

        Example:
            >>> scanner = J2534RegistryScanner()
            >>> for device in scanner.get_all_devices():
            ...     if scanner.verify_dll_exists(device):
            ...         print(f"{device.name}: DLL OK")
            ...     else:
            ...         print(f"{device.name}: DLL MISSING!")
        """
        if not device.function_library_path:
            return False
        return os.path.exists(device.function_library_path)

    def get_valid_devices(self) -> List[J2534DeviceInfo]:
        """
        Get only devices with existing DLL files.

        Filters the device list to return only devices whose FunctionLibrary
        DLL file actually exists on disk. This is useful to avoid errors
        from stale registry entries.

        Returns:
            List[J2534DeviceInfo]: Devices with valid (existing) DLL files

        Example:
            >>> scanner = J2534RegistryScanner()
            >>> valid = scanner.get_valid_devices()
            >>> print(f"{len(valid)} devices have valid DLLs")
        """
        return [d for d in self.get_all_devices() if self.verify_dll_exists(d)]


# =============================================================================
# Module-Level Convenience Functions
# =============================================================================

_default_scanner: Optional[J2534RegistryScanner] = None
"""Module-level singleton scanner instance for convenience functions."""


def get_scanner() -> J2534RegistryScanner:
    """
    Get the default registry scanner instance (singleton pattern).

    Returns a shared J2534RegistryScanner instance for use by the module-level
    convenience functions. Creates the instance on first call.

    Returns:
        J2534RegistryScanner: Shared scanner instance

    Note:
        The singleton instance shares its cache. Calling refresh_cache()
        on the returned scanner affects all subsequent calls to the
        convenience functions.
    """
    global _default_scanner
    if _default_scanner is None:
        _default_scanner = J2534RegistryScanner()
    return _default_scanner


def get_all_j2534_devices() -> List[J2534DeviceInfo]:
    """
    Get all registered J2534 devices.

    Convenience function that uses the default scanner singleton.
    Equivalent to: get_scanner().get_all_devices()

    Returns:
        List[J2534DeviceInfo]: All registered J2534 devices

    Example:
        >>> from J2534_REGISTRY import get_all_j2534_devices
        >>> devices = get_all_j2534_devices()
        >>> for device in devices:
        ...     print(f"{device.name}: {device.vendor}")
    """
    return get_scanner().get_all_devices()


def find_device_by_name(name: str) -> Optional[J2534DeviceInfo]:
    """
    Find a device by name (partial match, case-insensitive).

    Convenience function that uses the default scanner singleton.
    Equivalent to: get_scanner().get_device_by_name(name)

    Args:
        name: Full or partial device name to search for

    Returns:
        J2534DeviceInfo if found, None otherwise

    Example:
        >>> from J2534_REGISTRY import find_device_by_name
        >>> mongoose = find_device_by_name("Mongoose")
        >>> if mongoose:
        ...     print(f"Found: {mongoose.name}")
    """
    return get_scanner().get_device_by_name(name)


def get_device_count() -> int:
    """
    Get the number of registered J2534 devices.

    Convenience function that uses the default scanner singleton.
    Equivalent to: get_scanner().get_device_count()

    Returns:
        int: Number of registered devices

    Example:
        >>> from J2534_REGISTRY import get_device_count
        >>> print(f"Found {get_device_count()} J2534 devices")
    """
    return get_scanner().get_device_count()
