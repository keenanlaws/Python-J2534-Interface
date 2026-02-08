"""
CustomTkinter J2534 Low-Level API Demo
======================================

A modern-themed GUI application demonstrating the low-level J2534 PassThru API
using CustomTkinter for a contemporary look with dark/light theme support.

This example showcases:
    - Device discovery and selection
    - Device open/close operations
    - Protocol channel connect/disconnect
    - Message filter configuration
    - Message transmission and reception
    - Battery voltage monitoring
    - Debug and exception mode configuration
    - Dark/Light theme toggle

Requirements:
    pip install customtkinter

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

import customtkinter as ctk
from tkinter import messagebox

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


# Set default appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class J2534ApiDemo(ctk.CTk):
    """
    Main application window for J2534 low-level API demonstration.

    This class provides a modern CustomTkinter GUI for interacting with J2534 devices
    at the low level, demonstrating all major API functions with theme support.
    """

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

    def __init__(self) -> None:
        """Initialize the J2534 API Demo application."""
        super().__init__()

        self.title("J2534 Low-Level API Demo - CustomTkinter")
        self.geometry("950x750")
        self.minsize(850, 850)

        # State variables
        self.device_identifier: Optional[int] = None
        self.channel_identifier: Optional[int] = None
        self.filter_identifier: Optional[int] = None
        self.is_device_open: bool = False
        self.is_channel_connected: bool = False
        self.devices: List = []
        self.voltage_timer_identifier: Optional[str] = None

        # Build the UI
        self._create_widgets()
        self._refresh_device_list()

    def _create_widgets(self) -> None:
        """Create and layout all UI widgets."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # Theme toggle in corner
        self.theme_switch = ctk.CTkSwitch(
            self,
            text="Dark Mode",
            command=self._toggle_theme,
            onvalue="dark",
            offvalue="light"
        )
        self.theme_switch.select()
        self.theme_switch.grid(row=0, column=0, padx=10, pady=5, sticky="ne")

        # Create sections
        self._create_device_frame()
        self._create_filter_frame()
        self._create_message_frame()
        self._create_config_frame()
        self._create_log_frame()
        self._create_status_frame()

    def _create_device_frame(self) -> None:
        """Create the device connection frame."""
        device_frame = ctk.CTkFrame(self)
        device_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        device_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(device_frame, text="Device & Channel", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=4, padx=10, pady=(10, 5), sticky="w"
        )

        # Device selection
        ctk.CTkLabel(device_frame, text="Device:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.device_combo = ctk.CTkComboBox(device_frame, values=[], width=300, state="readonly")
        self.device_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.refresh_button = ctk.CTkButton(device_frame, text="Refresh", width=80, command=self._refresh_device_list)
        self.refresh_button.grid(row=1, column=2, padx=5, pady=5)

        # Protocol and baud rate
        ctk.CTkLabel(device_frame, text="Protocol:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.protocol_combo = ctk.CTkComboBox(
            device_frame,
            values=[name for name, _ in self.PROTOCOL_OPTIONS],
            width=200,
            state="readonly"
        )
        self.protocol_combo.set(self.PROTOCOL_OPTIONS[0][0])
        self.protocol_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(device_frame, text="Baud Rate:").grid(row=2, column=2, padx=10, pady=5, sticky="w")
        self.baud_rate_combo = ctk.CTkComboBox(
            device_frame,
            values=[name for name, _ in self.BAUD_RATE_OPTIONS],
            width=180,
            state="readonly"
        )
        self.baud_rate_combo.set(self.BAUD_RATE_OPTIONS[0][0])
        self.baud_rate_combo.grid(row=2, column=3, padx=5, pady=5, sticky="w")

        # Connect flags
        ctk.CTkLabel(device_frame, text="Connect Flags:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.connect_flags_entry = ctk.CTkEntry(device_frame, width=100, placeholder_text="0")
        self.connect_flags_entry.insert(0, "0")
        self.connect_flags_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Buttons
        button_frame = ctk.CTkFrame(device_frame, fg_color="transparent")
        button_frame.grid(row=4, column=0, columnspan=4, pady=10)

        self.open_device_button = ctk.CTkButton(button_frame, text="Open Device", command=self._open_device)
        self.open_device_button.pack(side="left", padx=5)

        self.connect_channel_button = ctk.CTkButton(
            button_frame, text="Connect Channel", command=self._connect_channel, state="disabled"
        )
        self.connect_channel_button.pack(side="left", padx=5)

        self.disconnect_channel_button = ctk.CTkButton(
            button_frame, text="Disconnect", command=self._disconnect_channel, state="disabled"
        )
        self.disconnect_channel_button.pack(side="left", padx=5)

        self.close_device_button = ctk.CTkButton(
            button_frame, text="Close Device", command=self._close_device, state="disabled"
        )
        self.close_device_button.pack(side="left", padx=5)

    def _create_filter_frame(self) -> None:
        """Create the message filter configuration frame."""
        filter_frame = ctk.CTkFrame(self)
        filter_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(filter_frame, text="Filter Setup (ISO15765)", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=8, padx=10, pady=(10, 5), sticky="w"
        )

        ctk.CTkLabel(filter_frame, text="Mask ID:").grid(row=1, column=0, padx=10, pady=5)
        self.mask_id_entry = ctk.CTkEntry(filter_frame, width=100, placeholder_text="0xFFFFFFFF")
        self.mask_id_entry.insert(0, "0xFFFFFFFF")
        self.mask_id_entry.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(filter_frame, text="Pattern ID:").grid(row=1, column=2, padx=10, pady=5)
        self.pattern_id_entry = ctk.CTkEntry(filter_frame, width=100, placeholder_text="0x7E8")
        self.pattern_id_entry.insert(0, "0x7E8")
        self.pattern_id_entry.grid(row=1, column=3, padx=5, pady=5)

        ctk.CTkLabel(filter_frame, text="Flow Ctrl ID:").grid(row=1, column=4, padx=10, pady=5)
        self.flow_control_id_entry = ctk.CTkEntry(filter_frame, width=100, placeholder_text="0x7E0")
        self.flow_control_id_entry.insert(0, "0x7E0")
        self.flow_control_id_entry.grid(row=1, column=5, padx=5, pady=5)

        self.set_filter_button = ctk.CTkButton(
            filter_frame, text="Set Filter", width=100, command=self._set_filter, state="disabled"
        )
        self.set_filter_button.grid(row=1, column=6, padx=10, pady=5)

        self.clear_filters_button = ctk.CTkButton(
            filter_frame, text="Clear Filters", width=100, command=self._clear_filters, state="disabled"
        )
        self.clear_filters_button.grid(row=1, column=7, padx=5, pady=5)

    def _create_message_frame(self) -> None:
        """Create the message I/O frame."""
        message_frame = ctk.CTkFrame(self)
        message_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        message_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(message_frame, text="Message I/O", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=4, padx=10, pady=(10, 5), sticky="w"
        )

        ctk.CTkLabel(message_frame, text="TX Data (hex):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.tx_data_entry = ctk.CTkEntry(message_frame, placeholder_text="22 F1 90", font=ctk.CTkFont(family="Consolas"))
        self.tx_data_entry.insert(0, "22 F1 90")
        self.tx_data_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.tx_data_entry.bind("<Return>", lambda e: self._send_message())

        self.send_button = ctk.CTkButton(message_frame, text="Send", width=80, command=self._send_message, state="disabled")
        self.send_button.grid(row=1, column=2, padx=5, pady=5)

        self.clear_rx_button = ctk.CTkButton(
            message_frame, text="Clear RX", width=80, command=self._clear_rx_buffer, state="disabled"
        )
        self.clear_rx_button.grid(row=1, column=3, padx=5, pady=5)

        ctk.CTkLabel(message_frame, text="Response:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.response_label = ctk.CTkLabel(
            message_frame, text="--", font=ctk.CTkFont(family="Consolas"), text_color="#3B8ED0"
        )
        self.response_label.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="w")

    def _create_config_frame(self) -> None:
        """Create the configuration options frame."""
        config_frame = ctk.CTkFrame(self)
        config_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(config_frame, text="Configuration", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=4, padx=10, pady=(10, 5), sticky="w"
        )

        self.debug_checkbox = ctk.CTkCheckBox(config_frame, text="Debug Mode", command=self._toggle_debug_mode)
        if j2534_config.debug_enabled:
            self.debug_checkbox.select()
        self.debug_checkbox.grid(row=1, column=0, padx=20, pady=10)

        self.exception_checkbox = ctk.CTkCheckBox(config_frame, text="Exception Mode", command=self._toggle_exception_mode)
        if j2534_config.raise_exceptions:
            self.exception_checkbox.select()
        self.exception_checkbox.grid(row=1, column=1, padx=20, pady=10)

        self.version_button = ctk.CTkButton(
            config_frame, text="Get Version Info", width=120, command=self._show_version_info, state="disabled"
        )
        self.version_button.grid(row=1, column=2, padx=20, pady=10)

    def _create_log_frame(self) -> None:
        """Create the communication log frame."""
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=5, column=0, padx=10, pady=5, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(log_frame, text="Communication Log", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w"
        )

        self.log_textbox = ctk.CTkTextbox(log_frame, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_textbox.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.log_textbox.configure(state="disabled")

        self.clear_log_button = ctk.CTkButton(log_frame, text="Clear Log", width=100, command=self._clear_log)
        self.clear_log_button.grid(row=2, column=0, pady=10)

    def _create_status_frame(self) -> None:
        """Create the status frame."""
        status_frame = ctk.CTkFrame(self, height=30)
        status_frame.grid(row=6, column=0, padx=10, pady=5, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(status_frame, text="Ready - Select a device and click Open Device")
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.voltage_label = ctk.CTkLabel(status_frame, text="Voltage: --", width=120)
        self.voltage_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")

    # =========================================================================
    # Theme Toggle
    # =========================================================================

    def _toggle_theme(self) -> None:
        """Toggle between dark and light themes."""
        if self.theme_switch.get() == "dark":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    # =========================================================================
    # Device Operations
    # =========================================================================

    def _refresh_device_list(self) -> None:
        """Refresh the list of available J2534 devices."""
        self.devices = get_list_j2534_devices()

        if self.devices:
            # devices is a list of [name, dll_path] pairs
            device_names = [device[0] for device in self.devices]
            self.device_combo.configure(values=device_names)
            self.device_combo.set(device_names[0])
            self._log_message(f"Found {len(self.devices)} J2534 device(s)")
        else:
            self.device_combo.configure(values=["No devices found"])
            self.device_combo.set("No devices found")
            self._log_message("No J2534 devices found in registry")

    def _open_device(self) -> None:
        """Open the selected J2534 device."""
        if not self.devices:
            messagebox.showwarning("Error", "No devices available")
            return

        # Find device index by name (devices is list of [name, dll_path] pairs)
        device_index = next((i for i, d in enumerate(self.devices) if d[0] == self.device_combo.get()), 0)

        self._log_message(f"Opening device {device_index}: {self.devices[device_index][0]}")
        self.status_label.configure(text="Opening device...")
        self.update()

        try:
            set_j2534_device_to_connect(device_index)
            result = pt_open()

            if result is False:
                self._log_message("Failed to open device")
                self.status_label.configure(text="Failed to open device")
                messagebox.showwarning("Error", "Failed to open device")
                return

            self.device_identifier = result
            self.is_device_open = True
            self._log_message(f"Device opened successfully (ID: {self.device_identifier})")
            self.status_label.configure(text=f"Device open (ID: {self.device_identifier})")

            self._update_ui_state()
            self._start_voltage_timer()

        except Exception as error:
            self._log_message(f"Error opening device: {error}")
            self.status_label.configure(text="Error")
            messagebox.showerror("Error", str(error))

    def _close_device(self) -> None:
        """Close the open device."""
        if not self.is_device_open:
            return

        if self.is_channel_connected:
            self._disconnect_channel()

        self._stop_voltage_timer()

        try:
            result = pt_close(self.device_identifier)
            self._log_message(f"Device closed (result: {result})")
        except Exception as error:
            self._log_message(f"Error closing device: {error}")

        self.device_identifier = None
        self.is_device_open = False
        self.voltage_label.configure(text="Voltage: --")
        self.status_label.configure(text="Device closed")

        self._update_ui_state()

    def _connect_channel(self) -> None:
        """Connect a protocol channel."""
        if not self.is_device_open:
            return

        protocol_index = [name for name, _ in self.PROTOCOL_OPTIONS].index(self.protocol_combo.get())
        protocol_identifier = self.PROTOCOL_OPTIONS[protocol_index][1]

        baud_rate_index = [name for name, _ in self.BAUD_RATE_OPTIONS].index(self.baud_rate_combo.get())
        baud_rate_value = self.BAUD_RATE_OPTIONS[baud_rate_index][1]

        try:
            connect_flags = int(self.connect_flags_entry.get() or "0", 0)
        except ValueError:
            connect_flags = 0

        self._log_message(f"Connecting channel: Protocol={protocol_identifier}, Baud={baud_rate_value}, Flags={connect_flags}")
        self.status_label.configure(text="Connecting channel...")
        self.update()

        try:
            result = pt_connect(self.device_identifier, protocol_identifier, connect_flags, baud_rate_value)

            if result is False:
                self._log_message("Failed to connect channel")
                self.status_label.configure(text="Failed to connect channel")
                messagebox.showwarning("Error", "Failed to connect channel")
                return

            self.channel_identifier = result
            self.is_channel_connected = True
            self._log_message(f"Channel connected (ID: {self.channel_identifier})")
            self.status_label.configure(text=f"Channel connected (ID: {self.channel_identifier})")

            self._update_ui_state()

        except Exception as error:
            self._log_message(f"Error connecting channel: {error}")
            self.status_label.configure(text="Error")
            messagebox.showerror("Error", str(error))

    def _disconnect_channel(self) -> None:
        """Disconnect the active channel."""
        if not self.is_channel_connected:
            return

        if self.filter_identifier is not None:
            self._clear_filters()

        try:
            result = pt_disconnect(self.channel_identifier)
            self._log_message(f"Channel disconnected (result: {result})")
        except Exception as error:
            self._log_message(f"Error disconnecting channel: {error}")

        self.channel_identifier = None
        self.is_channel_connected = False
        self.status_label.configure(text="Channel disconnected")

        self._update_ui_state()

    # =========================================================================
    # Filter Operations
    # =========================================================================

    def _set_filter(self) -> None:
        """Set a message filter."""
        if not self.is_channel_connected:
            return

        try:
            mask_identifier = int(self.mask_id_entry.get(), 0)
            pattern_identifier = int(self.pattern_id_entry.get(), 0)
            flow_control_identifier = int(self.flow_control_id_entry.get(), 0)
        except ValueError as error:
            messagebox.showwarning("Invalid Input", f"Invalid filter value: {error}")
            return

        protocol_index = [name for name, _ in self.PROTOCOL_OPTIONS].index(self.protocol_combo.get())
        protocol_identifier = self.PROTOCOL_OPTIONS[protocol_index][1]

        self._log_message(f"Setting filter: Mask=0x{mask_identifier:X}, Pattern=0x{pattern_identifier:X}, FC=0x{flow_control_identifier:X}")

        try:
            result = pt_start_ecu_filter(
                self.channel_identifier, protocol_identifier,
                mask_identifier, pattern_identifier, flow_control_identifier,
                TxFlags.ISO15765_FRAME_PAD
            )

            if result is False:
                self._log_message("Failed to set filter")
                messagebox.showwarning("Error", "Failed to set filter")
                return

            self.filter_identifier = result
            self._log_message(f"Filter set (ID: {self.filter_identifier})")

        except Exception as error:
            self._log_message(f"Error setting filter: {error}")
            messagebox.showerror("Error", str(error))

    def _clear_filters(self) -> None:
        """Clear all message filters."""
        if not self.is_channel_connected:
            return

        try:
            result = clear_message_filters(self.channel_identifier)
            self._log_message(f"Filters cleared (result: {result})")
            self.filter_identifier = None
        except Exception as error:
            self._log_message(f"Error clearing filters: {error}")

    # =========================================================================
    # Message Operations
    # =========================================================================

    def _send_message(self) -> None:
        """Send a message and receive response."""
        if not self.is_channel_connected:
            return

        hex_text = self.tx_data_entry.get().strip()
        try:
            hex_text = hex_text.replace(" ", "").replace(",", "").replace("0x", "")
            data_bytes = [int(hex_text[i:i+2], 16) for i in range(0, len(hex_text), 2)]
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter valid hex bytes")
            return

        if not data_bytes:
            return

        protocol_index = [name for name, _ in self.PROTOCOL_OPTIONS].index(self.protocol_combo.get())
        protocol_identifier = self.PROTOCOL_OPTIONS[protocol_index][1]

        transmit_message = PassThruMsgBuilder(protocol_identifier, TxFlags.ISO15765_FRAME_PAD)
        transmit_id = int(self.flow_control_id_entry.get(), 0)
        transmit_message.set_identifier_and_data(transmit_id, data_bytes)

        tx_hex = " ".join(f"{b:02X}" for b in data_bytes)
        self._log_message(f"TX [{transmit_id:03X}]: {tx_hex}")

        try:
            write_result = pt_write_message(self.channel_identifier, transmit_message, 1, 1000)

            if write_result != 0:
                self._log_message(f"Write failed (error: {write_result})")
                self.response_label.configure(text=f"Write error: {write_result}")
                return

            receive_message = PassThruMsgBuilder(protocol_identifier, 0)
            read_result = pt_read_message(self.channel_identifier, receive_message, 1, 1000)

            if read_result == 0:
                response_hex = receive_message.dump_output()
                formatted_response = " ".join(response_hex[i:i+2] for i in range(0, len(response_hex), 2))
                self.response_label.configure(text=formatted_response)
                self._log_message(f"RX: {formatted_response}")
            elif read_result == 0x10:
                self.response_label.configure(text="No response (timeout)")
                self._log_message("RX: No response (buffer empty)")
            else:
                self.response_label.configure(text=f"Read error: {read_result}")
                self._log_message(f"RX: Read error {read_result}")

        except Exception as error:
            self._log_message(f"Error: {error}")
            self.response_label.configure(text=f"Error: {error}")

    def _clear_rx_buffer(self) -> None:
        """Clear the receive buffer."""
        if not self.is_channel_connected:
            return

        try:
            result = clear_receive_buffer(self.channel_identifier)
            self._log_message(f"RX buffer cleared (result: {result})")
        except Exception as error:
            self._log_message(f"Error clearing RX buffer: {error}")

    # =========================================================================
    # Configuration Operations
    # =========================================================================

    def _toggle_debug_mode(self) -> None:
        """Toggle debug mode on/off."""
        if self.debug_checkbox.get():
            j2534_config.enable_debug()
            self._log_message("Debug mode enabled")
        else:
            j2534_config.disable_debug()
            self._log_message("Debug mode disabled")

    def _toggle_exception_mode(self) -> None:
        """Toggle exception mode on/off."""
        if self.exception_checkbox.get():
            j2534_config.enable_exceptions()
            self._log_message("Exception mode enabled")
        else:
            j2534_config.disable_exceptions()
            self._log_message("Exception mode disabled")

    def _show_version_info(self) -> None:
        """Display firmware and DLL version information."""
        if not self.is_device_open:
            return

        try:
            versions = pt_read_version(self.device_identifier)
            if versions and versions[0] != 'error':
                self._log_message(f"Firmware: {versions[0]}")
                self._log_message(f"DLL Version: {versions[1]}")
                self._log_message(f"API Version: {versions[2]}")
                messagebox.showinfo("Version Info", f"Firmware: {versions[0]}\nDLL: {versions[1]}\nAPI: {versions[2]}")
            else:
                self._log_message("Failed to read version info")
        except Exception as error:
            self._log_message(f"Error reading version: {error}")

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _update_voltage_display(self) -> None:
        """Update the battery voltage display."""
        if self.is_device_open:
            try:
                voltage = read_battery_volts(self.device_identifier)
                if voltage and voltage is not False:
                    self.voltage_label.configure(text=f"Voltage: {voltage:.2f}V")
                else:
                    self.voltage_label.configure(text="Voltage: --")
            except Exception:
                self.voltage_label.configure(text="Voltage: Error")

    def _start_voltage_timer(self) -> None:
        """Start periodic voltage updates."""
        if self.is_device_open:
            self._update_voltage_display()
            self.voltage_timer_identifier = self.after(5000, self._start_voltage_timer)

    def _stop_voltage_timer(self) -> None:
        """Stop voltage update timer."""
        if self.voltage_timer_identifier:
            self.after_cancel(self.voltage_timer_identifier)
            self.voltage_timer_identifier = None

    def _update_ui_state(self) -> None:
        """Update UI element states based on connection status."""
        self.open_device_button.configure(state="normal" if not self.is_device_open else "disabled")
        self.close_device_button.configure(state="normal" if self.is_device_open else "disabled")

        self.connect_channel_button.configure(state="normal" if self.is_device_open and not self.is_channel_connected else "disabled")
        self.disconnect_channel_button.configure(state="normal" if self.is_channel_connected else "disabled")

        self.set_filter_button.configure(state="normal" if self.is_channel_connected else "disabled")
        self.clear_filters_button.configure(state="normal" if self.is_channel_connected else "disabled")

        self.send_button.configure(state="normal" if self.is_channel_connected else "disabled")
        self.clear_rx_button.configure(state="normal" if self.is_channel_connected else "disabled")

        self.version_button.configure(state="normal" if self.is_device_open else "disabled")

        self.device_combo.configure(state="readonly" if not self.is_device_open else "disabled")

    def _log_message(self, message: str) -> None:
        """Add a timestamped message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def _clear_log(self) -> None:
        """Clear the log text widget."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

    def destroy(self) -> None:
        """Clean up resources before closing."""
        if self.is_channel_connected:
            self._disconnect_channel()
        if self.is_device_open:
            self._close_device()
        super().destroy()


def main() -> None:
    """Application entry point."""
    app = J2534ApiDemo()
    app.mainloop()


if __name__ == "__main__":
    main()
