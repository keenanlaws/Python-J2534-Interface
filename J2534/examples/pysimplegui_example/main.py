"""
FreeSimpleGUI J2534 Low-Level API Demo
======================================

A rapid-prototyping GUI application demonstrating the low-level J2534 PassThru API
using FreeSimpleGUI (with PySimpleGUI fallback) for quick development.

This example showcases:
    - Device discovery and selection
    - Device open/close operations
    - Protocol channel connect/disconnect
    - Message filter configuration
    - Message transmission and reception
    - Battery voltage monitoring
    - Debug and exception mode configuration

Requirements:
    pip install FreeSimpleGUI
    # Or fallback: pip install PySimpleGUI

Usage:
    python main.py

Version: 2.0.0
License: MIT
"""

import sys
import os
from datetime import datetime
from typing import Optional, List

# Add the project root to path (three levels up from this file)
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Try FreeSimpleGUI first, fall back to PySimpleGUI
try:
    import FreeSimpleGUI as sg
except ImportError:
    import PySimpleGUI as sg

from J2534 import (
    # Device management
    get_list_j2534_devices,
    set_j2534_device_to_connect,
    pt_open,
    pt_close,

    # Channel management
    pt_connect,
    pt_disconnect,

    # Message I/O
    pt_read_message,
    pt_write_message,
    PassThruMsgBuilder,

    # Filters
    pt_start_ecu_filter,
    pt_stop_message_filter,
    clear_message_filters,

    # Utilities
    read_battery_volts,
    pt_read_version,
    clear_receive_buffer,
    clear_transmit_buffer,

    # Constants
    ProtocolId,
    BaudRate,
    TxFlags,

    # Configuration
    j2534_config,
)


# Protocol options with display names and IDs
PROTOCOL_OPTIONS = [
    ("ISO15765 (CAN-TP)", ProtocolId.ISO15765),
    ("CAN (Raw)", ProtocolId.CAN),
    ("J1850 VPW", ProtocolId.J1850_VPW),
    ("J1850 PWM", ProtocolId.J1850_PWM),
    ("ISO 9141", ProtocolId.ISO9141),
    ("ISO 14230 (KWP2000)", ProtocolId.ISO14230),
    ("SCI A Engine", ProtocolId.SCI_A_ENGINE),
    ("SCI A Trans", ProtocolId.SCI_A_TRANS),
    ("SCI B Engine", ProtocolId.SCI_B_ENGINE),
    ("SCI B Trans", ProtocolId.SCI_B_TRANS),
]

# Baud rate options with display names and values
BAUD_RATE_OPTIONS = [
    ("500 kbps (CAN)", 500000),
    ("250 kbps (CAN)", 250000),
    ("125 kbps (CAN)", 125000),
    ("10.4 kbps (J1850/ISO)", 10400),
    ("41.6 kbps (J1850 PWM)", 41600),
]


def create_layout() -> List:
    """Create the GUI layout."""

    # Get initial device list (returns list of [name, dll_path] pairs)
    devices = get_list_j2534_devices()
    device_names = [d[0] for d in devices] if devices else ["No devices found"]

    # Device frame
    device_frame = sg.Frame("Device & Channel", [
        [
            sg.Text("Device:", size=(10, 1)),
            sg.Combo(device_names, key="-DEVICE-", size=(40, 1), readonly=True, default_value=device_names[0] if device_names else ""),
            sg.Button("Refresh", key="-REFRESH-"),
        ],
        [
            sg.Text("Protocol:", size=(10, 1)),
            sg.Combo([name for name, _ in PROTOCOL_OPTIONS], key="-PROTOCOL-", size=(20, 1), readonly=True, default_value=PROTOCOL_OPTIONS[0][0]),
            sg.Text("Baud Rate:"),
            sg.Combo([name for name, _ in BAUD_RATE_OPTIONS], key="-BAUD-", size=(20, 1), readonly=True, default_value=BAUD_RATE_OPTIONS[0][0]),
        ],
        [
            sg.Text("Flags:", size=(10, 1)),
            sg.Input("0", key="-FLAGS-", size=(10, 1)),
        ],
        [
            sg.Button("Open Device", key="-OPEN-"),
            sg.Button("Connect Channel", key="-CONNECT-", disabled=True),
            sg.Button("Disconnect", key="-DISCONNECT-", disabled=True),
            sg.Button("Close Device", key="-CLOSE-", disabled=True),
        ],
    ], expand_x=True)

    # Filter frame
    filter_frame = sg.Frame("Filter Setup (ISO15765)", [
        [
            sg.Text("Mask ID:"),
            sg.Input("0xFFFFFFFF", key="-MASK-", size=(12, 1)),
            sg.Text("Pattern ID:"),
            sg.Input("0x7E8", key="-PATTERN-", size=(12, 1)),
            sg.Text("Flow Ctrl ID:"),
            sg.Input("0x7E0", key="-FLOWCTRL-", size=(12, 1)),
            sg.Button("Set Filter", key="-SETFILTER-", disabled=True),
            sg.Button("Clear Filters", key="-CLEARFILTERS-", disabled=True),
        ],
    ], expand_x=True)

    # Message frame
    message_frame = sg.Frame("Message I/O", [
        [
            sg.Text("TX Data (hex):", size=(12, 1)),
            sg.Input("22 F1 90", key="-TXDATA-", size=(40, 1), font=("Consolas", 10)),
            sg.Button("Send", key="-SEND-", disabled=True),
            sg.Button("Clear RX", key="-CLEARRX-", disabled=True),
        ],
        [
            sg.Text("Response:", size=(12, 1)),
            sg.Text("--", key="-RESPONSE-", size=(60, 1), font=("Consolas", 10), text_color="blue"),
        ],
    ], expand_x=True)

    # Config frame
    config_frame = sg.Frame("Configuration", [
        [
            sg.Checkbox("Debug Mode", key="-DEBUG-", default=j2534_config.debug_enabled, enable_events=True),
            sg.Checkbox("Exception Mode", key="-EXCEPTION-", default=j2534_config.raise_exceptions, enable_events=True),
            sg.Button("Get Version Info", key="-VERSION-", disabled=True),
        ],
    ], expand_x=True)

    # Log frame
    log_frame = sg.Frame("Communication Log", [
        [sg.Multiline(size=(100, 15), key="-LOG-", font=("Consolas", 9), disabled=True, autoscroll=True)],
        [sg.Button("Clear Log", key="-CLEARLOG-")],
    ], expand_x=True)

    # Status bar
    status_bar = [
        sg.Text("Ready - Select a device and click Open Device", key="-STATUS-", size=(60, 1)),
        sg.Text("Voltage: --", key="-VOLTAGE-", size=(15, 1)),
    ]

    # Complete layout
    layout = [
        [device_frame],
        [filter_frame],
        [message_frame],
        [config_frame],
        [log_frame],
        status_bar,
    ]

    return layout


def log_message(window: sg.Window, message: str) -> None:
    """Add a timestamped message to the log."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    current_log = window["-LOG-"].get()
    new_log = f"{current_log}[{timestamp}] {message}\n"
    window["-LOG-"].update(new_log)


def update_ui_state(window: sg.Window, is_device_open: bool, is_channel_connected: bool) -> None:
    """Update UI element states based on connection status."""
    window["-OPEN-"].update(disabled=is_device_open)
    window["-CLOSE-"].update(disabled=not is_device_open)

    window["-CONNECT-"].update(disabled=not is_device_open or is_channel_connected)
    window["-DISCONNECT-"].update(disabled=not is_channel_connected)

    window["-SETFILTER-"].update(disabled=not is_channel_connected)
    window["-CLEARFILTERS-"].update(disabled=not is_channel_connected)

    window["-SEND-"].update(disabled=not is_channel_connected)
    window["-CLEARRX-"].update(disabled=not is_channel_connected)

    window["-VERSION-"].update(disabled=not is_device_open)

    window["-DEVICE-"].update(disabled=is_device_open)


def main() -> None:
    """Application entry point."""
    sg.theme("DarkBlue3")

    layout = create_layout()
    window = sg.Window(
        "J2534 Low-Level API Demo - FreeSimpleGUI",
        layout,
        finalize=True,
        resizable=True,
    )

    # State variables
    device_identifier: Optional[int] = None
    channel_identifier: Optional[int] = None
    filter_identifier: Optional[int] = None
    is_device_open: bool = False
    is_channel_connected: bool = False
    devices: List = get_list_j2534_devices()

    # Voltage update timer
    voltage_update_time = 0

    log_message(window, f"Found {len(devices)} J2534 device(s)" if devices else "No J2534 devices found")

    while True:
        event, values = window.read(timeout=1000)

        if event == sg.WIN_CLOSED:
            break

        # Voltage update
        if is_device_open:
            import time
            current_time = time.time()
            if current_time - voltage_update_time >= 5:
                try:
                    voltage = read_battery_volts(device_identifier)
                    if voltage and voltage is not False:
                        window["-VOLTAGE-"].update(f"Voltage: {voltage:.2f}V")
                    else:
                        window["-VOLTAGE-"].update("Voltage: --")
                except Exception:
                    window["-VOLTAGE-"].update("Voltage: Error")
                voltage_update_time = current_time

        # Handle events
        if event == "-REFRESH-":
            devices = get_list_j2534_devices()
            # devices is a list of [name, dll_path] pairs
            device_names = [d[0] for d in devices] if devices else ["No devices found"]
            window["-DEVICE-"].update(values=device_names, value=device_names[0] if device_names else "")
            log_message(window, f"Found {len(devices)} J2534 device(s)" if devices else "No J2534 devices found")

        elif event == "-OPEN-":
            if not devices:
                sg.popup_warning("No devices available")
                continue

            device_name = values["-DEVICE-"]
            device_index = next((i for i, d in enumerate(devices) if d[0] == device_name), 0)

            log_message(window, f"Opening device {device_index}: {devices[device_index][0]}")
            window["-STATUS-"].update("Opening device...")
            window.refresh()

            try:
                set_j2534_device_to_connect(device_index)
                result = pt_open()

                if result is False:
                    log_message(window, "Failed to open device")
                    window["-STATUS-"].update("Failed to open device")
                    sg.popup_warning("Failed to open device")
                    continue

                device_identifier = result
                is_device_open = True
                log_message(window, f"Device opened successfully (ID: {device_identifier})")
                window["-STATUS-"].update(f"Device open (ID: {device_identifier})")
                update_ui_state(window, is_device_open, is_channel_connected)

            except Exception as error:
                log_message(window, f"Error opening device: {error}")
                window["-STATUS-"].update("Error")
                sg.popup_error(str(error))

        elif event == "-CLOSE-":
            if is_channel_connected:
                # Disconnect channel first
                if filter_identifier is not None:
                    try:
                        clear_message_filters(channel_identifier)
                        filter_identifier = None
                    except Exception:
                        pass

                try:
                    pt_disconnect(channel_identifier)
                except Exception:
                    pass
                channel_identifier = None
                is_channel_connected = False

            try:
                result = pt_close(device_identifier)
                log_message(window, f"Device closed (result: {result})")
            except Exception as error:
                log_message(window, f"Error closing device: {error}")

            device_identifier = None
            is_device_open = False
            window["-VOLTAGE-"].update("Voltage: --")
            window["-STATUS-"].update("Device closed")
            update_ui_state(window, is_device_open, is_channel_connected)

        elif event == "-CONNECT-":
            protocol_name = values["-PROTOCOL-"]
            protocol_index = [name for name, _ in PROTOCOL_OPTIONS].index(protocol_name)
            protocol_identifier = PROTOCOL_OPTIONS[protocol_index][1]

            baud_name = values["-BAUD-"]
            baud_index = [name for name, _ in BAUD_RATE_OPTIONS].index(baud_name)
            baud_rate_value = BAUD_RATE_OPTIONS[baud_index][1]

            try:
                connect_flags = int(values["-FLAGS-"] or "0", 0)
            except ValueError:
                connect_flags = 0

            log_message(window, f"Connecting channel: Protocol={protocol_identifier}, Baud={baud_rate_value}, Flags={connect_flags}")
            window["-STATUS-"].update("Connecting channel...")
            window.refresh()

            try:
                result = pt_connect(device_identifier, protocol_identifier, connect_flags, baud_rate_value)

                if result is False:
                    log_message(window, "Failed to connect channel")
                    window["-STATUS-"].update("Failed to connect channel")
                    sg.popup_warning("Failed to connect channel")
                    continue

                channel_identifier = result
                is_channel_connected = True
                log_message(window, f"Channel connected (ID: {channel_identifier})")
                window["-STATUS-"].update(f"Channel connected (ID: {channel_identifier})")
                update_ui_state(window, is_device_open, is_channel_connected)

            except Exception as error:
                log_message(window, f"Error connecting channel: {error}")
                window["-STATUS-"].update("Error")
                sg.popup_error(str(error))

        elif event == "-DISCONNECT-":
            if filter_identifier is not None:
                try:
                    result = clear_message_filters(channel_identifier)
                    log_message(window, f"Filters cleared (result: {result})")
                    filter_identifier = None
                except Exception as error:
                    log_message(window, f"Error clearing filters: {error}")

            try:
                result = pt_disconnect(channel_identifier)
                log_message(window, f"Channel disconnected (result: {result})")
            except Exception as error:
                log_message(window, f"Error disconnecting channel: {error}")

            channel_identifier = None
            is_channel_connected = False
            window["-STATUS-"].update("Channel disconnected")
            update_ui_state(window, is_device_open, is_channel_connected)

        elif event == "-SETFILTER-":
            try:
                mask_identifier = int(values["-MASK-"], 0)
                pattern_identifier = int(values["-PATTERN-"], 0)
                flow_control_identifier = int(values["-FLOWCTRL-"], 0)
            except ValueError as error:
                sg.popup_warning(f"Invalid filter value: {error}")
                continue

            protocol_name = values["-PROTOCOL-"]
            protocol_index = [name for name, _ in PROTOCOL_OPTIONS].index(protocol_name)
            protocol_identifier = PROTOCOL_OPTIONS[protocol_index][1]

            log_message(window, f"Setting filter: Mask=0x{mask_identifier:X}, Pattern=0x{pattern_identifier:X}, FC=0x{flow_control_identifier:X}")

            try:
                result = pt_start_ecu_filter(
                    channel_identifier, protocol_identifier,
                    mask_identifier, pattern_identifier, flow_control_identifier,
                    TxFlags.ISO15765_FRAME_PAD
                )

                if result is False:
                    log_message(window, "Failed to set filter")
                    sg.popup_warning("Failed to set filter")
                    continue

                filter_identifier = result
                log_message(window, f"Filter set (ID: {filter_identifier})")

            except Exception as error:
                log_message(window, f"Error setting filter: {error}")
                sg.popup_error(str(error))

        elif event == "-CLEARFILTERS-":
            try:
                result = clear_message_filters(channel_identifier)
                log_message(window, f"Filters cleared (result: {result})")
                filter_identifier = None
            except Exception as error:
                log_message(window, f"Error clearing filters: {error}")

        elif event == "-SEND-":
            hex_text = values["-TXDATA-"].strip()
            try:
                hex_text = hex_text.replace(" ", "").replace(",", "").replace("0x", "")
                data_bytes = [int(hex_text[i:i+2], 16) for i in range(0, len(hex_text), 2)]
            except ValueError:
                sg.popup_warning("Please enter valid hex bytes")
                continue

            if not data_bytes:
                continue

            protocol_name = values["-PROTOCOL-"]
            protocol_index = [name for name, _ in PROTOCOL_OPTIONS].index(protocol_name)
            protocol_identifier = PROTOCOL_OPTIONS[protocol_index][1]

            transmit_message = PassThruMsgBuilder(protocol_identifier, TxFlags.ISO15765_FRAME_PAD)
            transmit_id = int(values["-FLOWCTRL-"], 0)
            transmit_message.set_identifier_and_data(transmit_id, data_bytes)

            tx_hex = " ".join(f"{b:02X}" for b in data_bytes)
            log_message(window, f"TX [{transmit_id:03X}]: {tx_hex}")

            try:
                write_result = pt_write_message(channel_identifier, transmit_message, 1, 1000)

                if write_result != 0:
                    log_message(window, f"Write failed (error: {write_result})")
                    window["-RESPONSE-"].update(f"Write error: {write_result}")
                    continue

                receive_message = PassThruMsgBuilder(protocol_identifier, 0)
                read_result = pt_read_message(channel_identifier, receive_message, 1, 1000)

                if read_result == 0:
                    response_hex = receive_message.dump_output()
                    formatted_response = " ".join(response_hex[i:i+2] for i in range(0, len(response_hex), 2))
                    window["-RESPONSE-"].update(formatted_response)
                    log_message(window, f"RX: {formatted_response}")
                elif read_result == 0x10:
                    window["-RESPONSE-"].update("No response (timeout)")
                    log_message(window, "RX: No response (buffer empty)")
                else:
                    window["-RESPONSE-"].update(f"Read error: {read_result}")
                    log_message(window, f"RX: Read error {read_result}")

            except Exception as error:
                log_message(window, f"Error: {error}")
                window["-RESPONSE-"].update(f"Error: {error}")

        elif event == "-CLEARRX-":
            try:
                result = clear_receive_buffer(channel_identifier)
                log_message(window, f"RX buffer cleared (result: {result})")
            except Exception as error:
                log_message(window, f"Error clearing RX buffer: {error}")

        elif event == "-DEBUG-":
            if values["-DEBUG-"]:
                j2534_config.enable_debug()
                log_message(window, "Debug mode enabled")
            else:
                j2534_config.disable_debug()
                log_message(window, "Debug mode disabled")

        elif event == "-EXCEPTION-":
            if values["-EXCEPTION-"]:
                j2534_config.enable_exceptions()
                log_message(window, "Exception mode enabled")
            else:
                j2534_config.disable_exceptions()
                log_message(window, "Exception mode disabled")

        elif event == "-VERSION-":
            try:
                versions = pt_read_version(device_identifier)
                if versions and versions[0] != 'error':
                    log_message(window, f"Firmware: {versions[0]}")
                    log_message(window, f"DLL Version: {versions[1]}")
                    log_message(window, f"API Version: {versions[2]}")
                    sg.popup(f"Firmware: {versions[0]}\nDLL: {versions[1]}\nAPI: {versions[2]}", title="Version Info")
                else:
                    log_message(window, "Failed to read version info")
            except Exception as error:
                log_message(window, f"Error reading version: {error}")

        elif event == "-CLEARLOG-":
            window["-LOG-"].update("")

    # Cleanup
    if is_channel_connected:
        try:
            pt_disconnect(channel_identifier)
        except Exception:
            pass

    if is_device_open:
        try:
            pt_close(device_identifier)
        except Exception:
            pass

    window.close()


if __name__ == "__main__":
    main()
