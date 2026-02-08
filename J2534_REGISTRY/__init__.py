"""
J2534_REGISTRY - J2534 Device Registry Scanner
==============================================

This package provides utilities for scanning the Windows registry to discover
installed J2534 PassThru devices and retrieve their configuration information.

The scanner searches standard J2534 04.04 registry locations:
    - 64-bit: HKLM\\Software\\Wow6432Node\\PassThruSupport.04.04\\
    - 32-bit: HKLM\\Software\\PassThruSupport.04.04\\

Quick Start
-----------
Get all registered devices::

    from J2534_REGISTRY import get_all_j2534_devices

    devices = get_all_j2534_devices()
    for device in devices:
        print(f"{device.name}: {device.function_library_path}")

Find a specific device::

    from J2534_REGISTRY import find_device_by_name

    mongoose = find_device_by_name("Mongoose")
    if mongoose:
        print(f"Found: {mongoose.function_library_path}")

Using the Scanner class::

    from J2534_REGISTRY import J2534RegistryScanner

    scanner = J2534RegistryScanner()

    # Get devices supporting CAN
    can_devices = scanner.get_devices_by_protocol("CAN")

    # Get only devices with valid DLL files
    valid_devices = scanner.get_valid_devices()

Version: 2.0.0
License: MIT
"""

__version__ = "2.0.0"
__author__ = "Original Authors, Refactored by Claude AI"

# Import main classes and functions
from J2534_REGISTRY.device_info import J2534DeviceInfo
from J2534_REGISTRY.registry_scanner import (
    J2534RegistryScanner,
    get_scanner,
    get_all_j2534_devices,
    find_device_by_name,
    get_device_count,
    REGISTRY_PATH_64BIT,
    REGISTRY_PATH_32BIT,
)

__all__ = [
    # Version
    "__version__",
    "__author__",

    # Classes
    "J2534DeviceInfo",
    "J2534RegistryScanner",

    # Functions
    "get_scanner",
    "get_all_j2534_devices",
    "find_device_by_name",
    "get_device_count",

    # Constants
    "REGISTRY_PATH_64BIT",
    "REGISTRY_PATH_32BIT",
]
