# J2534_REGISTRY GUI Test Examples

This directory contains standalone GUI applications for testing the J2534_REGISTRY module's
Windows registry scanning functionality.

## Purpose

These examples demonstrate and test all features of the J2534_REGISTRY module:
- Device discovery from Windows registry
- Protocol support detection
- DLL file validation
- Device filtering and search

## Available Examples

| Directory | Framework | Dependencies | Best For |
|-----------|-----------|--------------|----------|
| `tkinter_registry_viewer/` | Tkinter | None (built-in) | Quick testing, no setup |
| `customtkinter_registry_viewer/` | CustomTkinter | `pip install customtkinter` | Modern themed UI |
| `pysimplegui_registry_viewer/` | PySimpleGUI | `pip install PySimpleGUI` | Rapid prototyping |
| `pyqt5_registry_viewer/` | PyQt5 | `pip install PyQt5` | Full-featured table view |

## Quick Start

### Tkinter (No Installation Required)
```bash
cd tkinter_registry_viewer
python main.py
```

### Other Frameworks
```bash
# Install the framework
pip install customtkinter  # or PySimpleGUI, PyQt5

# Run the example
cd customtkinter_registry_viewer
python main.py
```

## Features Tested

### 1. Device List Display
- Lists all J2534 devices registered in Windows
- Shows device name, vendor, and device ID
- Refresh button to rescan the registry

### 2. Device Details Panel
When you select a device, view complete information:
- **Name**: Device display name
- **Vendor**: Manufacturer name
- **Function Library**: Path to J2534 DLL
- **Config Application**: Path to configuration tool (if available)
- **Registry Key**: Full registry path where device is registered
- **Device ID**: Enumeration index

### 3. Protocol Support Indicators
Visual indicators for each supported protocol:
- CAN / ISO15765
- J1850 VPW (Variable Pulse Width)
- J1850 PWM (Pulse Width Modulation)
- ISO 9141
- ISO 14230 (KWP2000)
- SCI_A_ENGINE / SCI_A_TRANS
- SCI_B_ENGINE / SCI_B_TRANS

### 4. DLL Validation
- Checks if the DLL file actually exists on disk
- Shows file size and modification date
- Button to open containing folder in Windows Explorer

### 5. Export/Copy Features
- Copy device information to clipboard
- Export all devices to JSON or CSV format

### 6. Registry Path Information
- Shows which registry path is being scanned:
  - 64-bit: `HKLM\Software\Wow6432Node\PassThruSupport.04.04\`
  - 32-bit: `HKLM\Software\PassThruSupport.04.04\`

## API Functions Demonstrated

```python
from J2534_REGISTRY import (
    get_all_j2534_devices,      # Get all registered devices
    find_device_by_name,        # Search by name (partial match)
    get_device_count,           # Total device count
    J2534RegistryScanner,       # Scanner class for advanced features
    J2534DeviceInfo,            # Device information dataclass
    REGISTRY_PATH_64BIT,        # 64-bit registry path constant
    REGISTRY_PATH_32BIT,        # 32-bit registry path constant
)

# Basic usage
devices = get_all_j2534_devices()
for device in devices:
    print(f"{device.name} - {device.vendor}")
    print(f"  DLL: {device.function_library_path}")
    print(f"  Protocols: {', '.join(device.supported_protocols)}")

# Advanced usage with scanner
scanner = J2534RegistryScanner()
can_devices = scanner.get_devices_by_protocol("CAN")
valid_devices = scanner.get_valid_devices()  # Only devices with existing DLLs
scanner.refresh_cache()  # Force rescan
```

## Troubleshooting

### No Devices Found
- Ensure you have J2534 devices installed (e.g., Mongoose, VCM II, etc.)
- Check that the device software registered properly in Windows registry
- Run `regedit` and navigate to `HKLM\Software\PassThruSupport.04.04\` to verify

### Import Errors
- Make sure you're running from the example directory
- The examples automatically add the project root to `sys.path`

### DLL Not Found
- Device is registered but DLL file is missing
- Reinstall the device software or update the registry path
