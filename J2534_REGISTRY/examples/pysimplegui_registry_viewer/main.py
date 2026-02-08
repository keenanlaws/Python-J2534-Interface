"""
PySimpleGUI J2534 Registry Viewer
=================================

A rapid-development GUI application for viewing J2534 devices registered in Windows.
Uses PySimpleGUI for a simple, declarative approach to GUI building.

Features:
    - View all registered J2534 devices
    - See detailed device information
    - Check protocol support
    - Validate DLL file existence
    - Export device list to JSON/CSV
    - Copy device info to clipboard

Requirements:
    pip install FreeSimpleGUI
    # Or: pip install PySimpleGUI (requires paid license since 2023)

Usage:
    python main.py

Version: 1.0.0
License: MIT
"""

import sys
import os
import json
import subprocess
from datetime import datetime
from typing import Optional, List

# Try FreeSimpleGUI first (free, maintained fork), fall back to PySimpleGUI
try:
    import FreeSimpleGUI as sg
except ImportError:
    import PySimpleGUI as sg

# Add project root to path (three levels up from this file)
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from J2534_REGISTRY import (
    get_all_j2534_devices,
    find_device_by_name,
    get_device_count,
    J2534RegistryScanner,
    J2534DeviceInfo,
    REGISTRY_PATH_64BIT,
    REGISTRY_PATH_32BIT,
)


def create_layout(scanner: J2534RegistryScanner) -> list:
    """
    Create the GUI layout.

    Args:
        scanner: The registry scanner instance

    Returns:
        The PySimpleGUI layout definition
    """
    # Protocol checkboxes
    protocols = [
        ("CAN/ISO15765", "-PROTO_CAN-"),
        ("J1850 VPW", "-PROTO_VPW-"),
        ("J1850 PWM", "-PROTO_PWM-"),
        ("ISO 9141", "-PROTO_9141-"),
        ("ISO 14230", "-PROTO_14230-"),
        ("SCI_A Eng", "-PROTO_SCIA_E-"),
        ("SCI_A Trans", "-PROTO_SCIA_T-"),
        ("SCI_B Eng", "-PROTO_SCIB_E-"),
        ("SCI_B Trans", "-PROTO_SCIB_T-"),
    ]

    protocol_row1 = [
        sg.Checkbox(protocols[i][0], key=protocols[i][1], disabled=True, size=(12, 1))
        for i in range(3)
    ]
    protocol_row2 = [
        sg.Checkbox(protocols[i][0], key=protocols[i][1], disabled=True, size=(12, 1))
        for i in range(3, 6)
    ]
    protocol_row3 = [
        sg.Checkbox(protocols[i][0], key=protocols[i][1], disabled=True, size=(12, 1))
        for i in range(6, 9)
    ]

    # Left column: Device list
    left_column = [
        [sg.Text("Devices", font=("Helvetica", 12, "bold"))],
        [sg.Text("Found: 0 devices", key="-DEVICE_COUNT-", size=(20, 1))],
        [sg.Input(key="-SEARCH-", size=(25, 1), enable_events=True, tooltip="Search devices")],
        [sg.Listbox(
            values=[],
            key="-DEVICE_LIST-",
            size=(30, 20),
            enable_events=True,
            font=("Consolas", 10)
        )],
    ]

    # Right column: Device details
    right_column = [
        [sg.Text("Device Details", font=("Helvetica", 12, "bold"))],

        # Basic info frame
        [sg.Frame("Basic Information", [
            [sg.Text("Name:", size=(12, 1)), sg.Text("--", key="-NAME-", size=(45, 1), font=("Consolas", 10))],
            [sg.Text("Vendor:", size=(12, 1)), sg.Text("--", key="-VENDOR-", size=(45, 1), font=("Consolas", 10))],
            [sg.Text("Device ID:", size=(12, 1)), sg.Text("--", key="-DEVICE_ID-", size=(45, 1), font=("Consolas", 10))],
        ], expand_x=True)],

        # Paths frame
        [sg.Frame("File Paths", [
            [sg.Text("DLL Path:", size=(12, 1))],
            [sg.Text("--", key="-DLL_PATH-", size=(55, 2), font=("Consolas", 9))],
            [sg.Text("DLL Status:", size=(12, 1)),
             sg.Text("--", key="-DLL_STATUS-", size=(30, 1), font=("Consolas", 9)),
             sg.Button("Open Folder", key="-OPEN_FOLDER-", disabled=True, size=(12, 1))],
            [sg.Text("Config App:", size=(12, 1))],
            [sg.Text("--", key="-CONFIG_APP-", size=(55, 1), font=("Consolas", 9))],
            [sg.Text("Registry Key:", size=(12, 1))],
            [sg.Text("--", key="-REG_KEY-", size=(55, 2), font=("Consolas", 9))],
        ], expand_x=True)],

        # Protocols frame
        [sg.Frame("Supported Protocols", [
            protocol_row1,
            protocol_row2,
            protocol_row3,
        ], expand_x=True)],

        # Action buttons
        [
            sg.Button("Copy Info", key="-COPY-", size=(12, 1)),
            sg.Button("Export JSON", key="-EXPORT_JSON-", size=(12, 1)),
            sg.Button("Export CSV", key="-EXPORT_CSV-", size=(12, 1)),
        ],
    ]

    # Main layout
    layout = [
        # Header
        [
            sg.Text("J2534 Registry Device Viewer", font=("Helvetica", 16, "bold")),
            sg.Push(),
            sg.Button("Refresh", key="-REFRESH-", size=(10, 1)),
        ],
        [sg.Text(f"Registry Path: {scanner._registry_path}", font=("Consolas", 9), text_color="gray")],
        [sg.HorizontalSeparator()],

        # Main content
        [
            sg.Column(left_column, vertical_alignment="top"),
            sg.VerticalSeparator(),
            sg.Column(right_column, vertical_alignment="top", expand_x=True),
        ],

        # Status bar
        [sg.HorizontalSeparator()],
        [sg.Text("Ready", key="-STATUS-", size=(80, 1), relief=sg.RELIEF_SUNKEN)],
    ]

    return layout


def refresh_devices(window: sg.Window, scanner: J2534RegistryScanner) -> List[J2534DeviceInfo]:
    """
    Refresh the device list from the registry.

    Args:
        window: The PySimpleGUI window
        scanner: The registry scanner

    Returns:
        List of discovered devices
    """
    window["-STATUS-"].update("Scanning registry...")
    window.refresh()

    try:
        scanner.refresh_cache()
        devices = scanner.get_all_devices()
        update_device_list(window, devices, "")
        window["-DEVICE_COUNT-"].update(f"Found: {len(devices)} devices")
        window["-STATUS-"].update(f"Found {len(devices)} device(s) - Last refresh: {datetime.now().strftime('%H:%M:%S')}")
        return devices
    except Exception as e:
        sg.popup_error(f"Failed to scan registry:\n{e}")
        window["-STATUS-"].update("Error scanning registry")
        return []


def update_device_list(window: sg.Window, devices: List[J2534DeviceInfo], search_text: str):
    """
    Update the device listbox with filtered devices.

    Args:
        window: The PySimpleGUI window
        devices: List of all devices
        search_text: Search filter text
    """
    search_lower = search_text.lower()
    filtered = [
        d for d in devices
        if not search_text or search_lower in d.name.lower() or search_lower in d.vendor.lower()
    ]

    display_names = [f"{d.name}" for d in filtered]
    window["-DEVICE_LIST-"].update(values=display_names)

    return filtered


def display_device_details(window: sg.Window, device: J2534DeviceInfo, scanner: J2534RegistryScanner):
    """
    Display the details of a selected device.

    Args:
        window: The PySimpleGUI window
        device: The device to display
        scanner: The registry scanner for DLL validation
    """
    # Basic info
    window["-NAME-"].update(device.name)
    window["-VENDOR-"].update(device.vendor or "--")
    window["-DEVICE_ID-"].update(str(device.device_id))

    # Paths
    window["-DLL_PATH-"].update(device.function_library_path or "--")
    window["-CONFIG_APP-"].update(device.config_application_path or "--")
    window["-REG_KEY-"].update(device.registry_key_path or "--")

    # DLL status
    if device.function_library_path:
        if scanner.verify_dll_exists(device):
            try:
                stat = os.stat(device.function_library_path)
                size_kb = stat.st_size / 1024
                mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                window["-DLL_STATUS-"].update(f"EXISTS ({size_kb:.1f} KB)", text_color="green")
            except Exception:
                window["-DLL_STATUS-"].update("EXISTS", text_color="green")
            window["-OPEN_FOLDER-"].update(disabled=False)
        else:
            window["-DLL_STATUS-"].update("NOT FOUND", text_color="red")
            window["-OPEN_FOLDER-"].update(disabled=True)
    else:
        window["-DLL_STATUS-"].update("No path specified", text_color="gray")
        window["-OPEN_FOLDER-"].update(disabled=True)

    # Protocol support
    window["-PROTO_CAN-"].update(value=device.can_iso15765)
    window["-PROTO_VPW-"].update(value=device.j1850vpw)
    window["-PROTO_PWM-"].update(value=device.j1850pwm)
    window["-PROTO_9141-"].update(value=device.iso9141)
    window["-PROTO_14230-"].update(value=device.iso14230)
    window["-PROTO_SCIA_E-"].update(value=device.sci_a_engine)
    window["-PROTO_SCIA_T-"].update(value=device.sci_a_trans)
    window["-PROTO_SCIB_E-"].update(value=device.sci_b_engine)
    window["-PROTO_SCIB_T-"].update(value=device.sci_b_trans)


def copy_to_clipboard(device: J2534DeviceInfo) -> str:
    """
    Generate clipboard text for a device.

    Args:
        device: The device to copy

    Returns:
        Formatted device information text
    """
    return f"""J2534 Device Information
========================
Name: {device.name}
Vendor: {device.vendor}
Device ID: {device.device_id}
Function Library: {device.function_library_path}
Config Application: {device.config_application_path or 'N/A'}
Registry Key: {device.registry_key_path}

Supported Protocols:
- CAN/ISO15765: {'Yes' if device.can_iso15765 else 'No'}
- J1850 VPW: {'Yes' if device.j1850vpw else 'No'}
- J1850 PWM: {'Yes' if device.j1850pwm else 'No'}
- ISO 9141: {'Yes' if device.iso9141 else 'No'}
- ISO 14230: {'Yes' if device.iso14230 else 'No'}
- SCI_A Engine: {'Yes' if device.sci_a_engine else 'No'}
- SCI_A Trans: {'Yes' if device.sci_a_trans else 'No'}
- SCI_B Engine: {'Yes' if device.sci_b_engine else 'No'}
- SCI_B Trans: {'Yes' if device.sci_b_trans else 'No'}
"""


def export_json(devices: List[J2534DeviceInfo]):
    """Export all devices to JSON file."""
    if not devices:
        sg.popup("No devices to export")
        return

    filepath = sg.popup_get_file(
        "Save JSON file",
        save_as=True,
        default_extension=".json",
        file_types=(("JSON Files", "*.json"), ("All Files", "*.*"))
    )

    if not filepath:
        return

    try:
        export_data = []
        for device in devices:
            export_data.append({
                "name": device.name,
                "vendor": device.vendor,
                "device_id": device.device_id,
                "function_library_path": device.function_library_path,
                "config_application_path": device.config_application_path,
                "registry_key_path": device.registry_key_path,
                "supported_protocols": device.supported_protocols,
            })

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)

        sg.popup(f"Exported {len(devices)} device(s) to:\n{filepath}")
    except Exception as e:
        sg.popup_error(f"Failed to export:\n{e}")


def export_csv(devices: List[J2534DeviceInfo]):
    """Export all devices to CSV file."""
    if not devices:
        sg.popup("No devices to export")
        return

    filepath = sg.popup_get_file(
        "Save CSV file",
        save_as=True,
        default_extension=".csv",
        file_types=(("CSV Files", "*.csv"), ("All Files", "*.*"))
    )

    if not filepath:
        return

    try:
        import csv
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Vendor", "Device ID", "Function Library", "Protocols"])

            for device in devices:
                writer.writerow([
                    device.name,
                    device.vendor,
                    device.device_id,
                    device.function_library_path,
                    ", ".join(device.supported_protocols),
                ])

        sg.popup(f"Exported {len(devices)} device(s) to:\n{filepath}")
    except Exception as e:
        sg.popup_error(f"Failed to export:\n{e}")


def main():
    """Application entry point."""
    # Initialize scanner
    scanner = J2534RegistryScanner()

    # Create window
    layout = create_layout(scanner)
    window = sg.Window(
        "J2534 Registry Viewer - PySimpleGUI",
        layout,
        finalize=True,
        resizable=True,
        size=(950, 700)
    )

    # Load initial device list
    devices = refresh_devices(window, scanner)
    filtered_devices = devices
    selected_device: Optional[J2534DeviceInfo] = None

    # Event loop
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break

        elif event == "-REFRESH-":
            devices = refresh_devices(window, scanner)
            filtered_devices = update_device_list(window, devices, values["-SEARCH-"])
            selected_device = None

        elif event == "-SEARCH-":
            filtered_devices = update_device_list(window, devices, values["-SEARCH-"])

        elif event == "-DEVICE_LIST-" and values["-DEVICE_LIST-"]:
            # Find selected device
            selected_name = values["-DEVICE_LIST-"][0]
            for device in filtered_devices:
                if device.name == selected_name:
                    selected_device = device
                    display_device_details(window, device, scanner)
                    break

        elif event == "-OPEN_FOLDER-" and selected_device:
            folder = os.path.dirname(selected_device.function_library_path)
            if os.path.exists(folder):
                subprocess.run(["explorer", folder])
            else:
                sg.popup_warning(f"Folder does not exist:\n{folder}")

        elif event == "-COPY-":
            if selected_device:
                sg.clipboard_set(copy_to_clipboard(selected_device))
                window["-STATUS-"].update("Device info copied to clipboard")
            else:
                sg.popup("No device selected")

        elif event == "-EXPORT_JSON-":
            export_json(devices)

        elif event == "-EXPORT_CSV-":
            export_csv(devices)

    window.close()


if __name__ == "__main__":
    main()
