"""
PySimpleGUI J2534 Diagnostic Tool Example
=========================================

A rapid-development GUI using FreeSimpleGUI for quick prototyping.

Requirements:
    pip install FreeSimpleGUI

Usage:
    python main.py

Version: 1.0.0
License: MIT
"""

import sys
import FreeSimpleGUI as sg
from datetime import datetime

# Add the project root to path (two levels up from this file)
import os
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from J2534_REGISTRY import get_all_j2534_devices
from AutoJ2534 import j2534_communication, Connections


def create_layout():
    """Create the GUI layout."""
    devices = get_all_j2534_devices()
    device_names = [d.name for d in devices] if devices else ["No devices found"]
    configs = list(Connections.CHRYSLER_ECU.keys())

    layout = [
        [sg.Text("J2534 Diagnostic Tool", font=("Arial", 14, "bold"))],
        [sg.HorizontalSeparator()],

        # Connection section
        [sg.Frame("Connection", [
            [sg.Text("Device:"), sg.Combo(device_names, key="-DEVICE-", size=(35, 1), readonly=True)],
            [sg.Text("Protocol:"), sg.Combo(configs, key="-PROTOCOL-", default_value=configs[0], size=(20, 1), readonly=True)],
            [sg.Button("Refresh", key="-REFRESH-"), sg.Button("Connect", key="-CONNECT-"),
             sg.Text("", key="-VOLTAGE-", size=(15, 1))]
        ])],

        # Message section
        [sg.Frame("Send Message", [
            [sg.Text("Data (hex):"), sg.Input(key="-DATA-", size=(40, 1), default_text="3E 00"),
             sg.Button("Send", key="-SEND-", disabled=True)],
            [sg.Text("Response:"), sg.Text("--", key="-RESPONSE-", size=(50, 1), text_color="blue")]
        ])],

        # Log section
        [sg.Frame("Communication Log", [
            [sg.Multiline(key="-LOG-", size=(70, 15), disabled=True, autoscroll=True, font=("Consolas", 9))],
            [sg.Button("Clear Log", key="-CLEAR-")]
        ])],

        # Status
        [sg.StatusBar("Ready - Select a device and click Connect", key="-STATUS-")]
    ]
    return layout, devices


def log_message(window, message):
    """Add timestamped message to log."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    window["-LOG-"].print(f"[{timestamp}] {message}")


def main():
    # sg.theme("LightGrey1")

    layout, devices = create_layout()
    window = sg.Window("J2534 Diagnostic Tool - FreeSimpleGUI", layout, finalize=True)

    is_connected = False
    last_voltage_update = 0

    while True:
        event, values = window.read(timeout=1000)

        if event == sg.WIN_CLOSED:
            if is_connected:
                try:
                    j2534_communication.disconnect()
                    j2534_communication.close()
                except Exception:
                    pass
            break

        if event == "-REFRESH-":
            devices = get_all_j2534_devices()
            device_names = [d.name for d in devices] if devices else ["No devices found"]
            window["-DEVICE-"].update(values=device_names, value=device_names[0] if device_names else "")
            log_message(window, f"Found {len(devices)} device(s)")

        if event == "-CONNECT-":
            if not is_connected:
                # Connect
                if not devices:
                    sg.popup_error("No devices available")
                    continue

                device_idx = window["-DEVICE-"].Widget.current() if hasattr(window["-DEVICE-"].Widget, 'current') else 0
                config_key = values["-PROTOCOL-"]

                log_message(window, f"Connecting to device {device_idx}...")
                window["-STATUS-"].update("Connecting...")
                window.refresh()

                try:
                    if j2534_communication.open_communication(device_idx, config_key):
                        is_connected = True
                        window["-CONNECT-"].update("Disconnect")
                        window["-SEND-"].update(disabled=False)
                        window["-DEVICE-"].update(disabled=True)
                        window["-PROTOCOL-"].update(disabled=True)

                        log_message(window, "Connected!")
                        window["-STATUS-"].update("Connected")

                        info = j2534_communication.tool_info()
                        if info:
                            log_message(window, f"Device: {info[0]}")

                        voltage = j2534_communication.check_volts()
                        if voltage:
                            window["-VOLTAGE-"].update(f"Voltage: {voltage:.2f}V")
                    else:
                        log_message(window, "Connection failed!")
                        window["-STATUS-"].update("Connection failed")
                        sg.popup_error("Connection failed")
                except Exception as e:
                    log_message(window, f"Error: {e}")
            else:
                # Disconnect
                try:
                    j2534_communication.disconnect()
                    j2534_communication.close()
                except Exception:
                    pass

                is_connected = False
                window["-CONNECT-"].update("Connect")
                window["-SEND-"].update(disabled=True)
                window["-DEVICE-"].update(disabled=False)
                window["-PROTOCOL-"].update(disabled=False)
                window["-VOLTAGE-"].update("")

                log_message(window, "Disconnected")
                window["-STATUS-"].update("Disconnected")

        if event == "-SEND-" and is_connected:
            hex_text = values["-DATA-"].strip()
            try:
                hex_text = hex_text.replace(" ", "").replace(",", "").replace("0x", "")
                data_bytes = [int(hex_text[i:i+2], 16) for i in range(0, len(hex_text), 2)]
            except ValueError:
                sg.popup_error("Invalid hex input")
                continue

            if data_bytes:
                tx_hex = " ".join(f"{b:02X}" for b in data_bytes)
                log_message(window, f"TX: {tx_hex}")

                try:
                    response = j2534_communication.transmit_and_receive_message(data_bytes)
                    if response is False:
                        window["-RESPONSE-"].update("No response")
                        log_message(window, "RX: No response")
                    elif isinstance(response, str):
                        formatted = " ".join(response[i:i+2] for i in range(0, len(response), 2))
                        window["-RESPONSE-"].update(formatted)
                        log_message(window, f"RX: {formatted}")
                    else:
                        window["-RESPONSE-"].update(str(response))
                        log_message(window, f"RX: {response}")
                except Exception as e:
                    log_message(window, f"Error: {e}")

        if event == "-CLEAR-":
            window["-LOG-"].update("")

        # Periodic voltage update
        if is_connected and event == sg.TIMEOUT_EVENT:
            import time
            if time.time() - last_voltage_update > 5:
                try:
                    voltage = j2534_communication.check_volts()
                    if voltage:
                        window["-VOLTAGE-"].update(f"Voltage: {voltage:.2f}V")
                except Exception:
                    pass
                last_voltage_update = time.time()

    window.close()


if __name__ == "__main__":
    main()
