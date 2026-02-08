"""
Tkinter J2534 Low-Level API Demo
================================

A comprehensive GUI application demonstrating the low-level J2534 PassThru API
using Python's built-in Tkinter library. No external dependencies required!

This example showcases:
    - Device discovery and selection
    - Device open/close operations
    - Protocol channel connect/disconnect
    - Message filter configuration
    - Message transmission and reception
    - Battery voltage monitoring
    - Debug and exception mode configuration

Requirements:
    None (Tkinter is included with Python)

Usage:
    python main.py

Version: 2.0.0
License: MIT
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from typing import Optional, List

# Add the project root to path (three levels up from this file)
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

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


class J2534ApiDemo:
    """
    Main application class for J2534 low-level API demonstration.

    This class provides a comprehensive GUI for interacting with J2534 devices
    at the low level, demonstrating all major API functions.

    Attributes:
        root: The Tkinter root window
        device_identifier: The opened device handle (None if not open)
        channel_identifier: The connected channel handle (None if not connected)
        filter_identifier: The active filter handle (None if no filter)
        is_device_open: Whether a device is currently open
        is_channel_connected: Whether a channel is currently connected
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

    def __init__(self, root: tk.Tk) -> None:
        """
        Initialize the J2534 API Demo application.

        Args:
            root: The Tkinter root window instance
        """
        self.root = root
        self.root.title("J2534 Low-Level API Demo - Tkinter")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

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
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)  # Log frame gets extra space

        # === Device Frame ===
        self._create_device_frame(main_frame)

        # === Filter Frame ===
        self._create_filter_frame(main_frame)

        # === Message Frame ===
        self._create_message_frame(main_frame)

        # === Config Frame ===
        self._create_config_frame(main_frame)

        # === Log Frame ===
        self._create_log_frame(main_frame)

        # === Status Bar ===
        self._create_status_bar(main_frame)

    def _create_device_frame(self, parent: ttk.Frame) -> None:
        """Create the device connection frame."""
        device_frame = ttk.LabelFrame(parent, text="Device & Channel", padding="5")
        device_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        device_frame.columnconfigure(1, weight=1)
        device_frame.columnconfigure(3, weight=1)

        # Row 0: Device selection
        ttk.Label(device_frame, text="Device:").grid(row=0, column=0, padx=5, sticky="w")
        self.device_variable = tk.StringVar()
        self.device_combobox = ttk.Combobox(
            device_frame,
            textvariable=self.device_variable,
            state="readonly",
            width=35
        )
        self.device_combobox.grid(row=0, column=1, padx=5, sticky="ew")

        ttk.Button(
            device_frame,
            text="Refresh",
            command=self._refresh_device_list
        ).grid(row=0, column=2, padx=5)

        # Row 1: Protocol and baud rate
        ttk.Label(device_frame, text="Protocol:").grid(row=1, column=0, padx=5, pady=(5, 0), sticky="w")
        self.protocol_variable = tk.StringVar()
        self.protocol_combobox = ttk.Combobox(
            device_frame,
            textvariable=self.protocol_variable,
            values=[name for name, _ in self.PROTOCOL_OPTIONS],
            state="readonly",
            width=20
        )
        self.protocol_combobox.grid(row=1, column=1, padx=5, pady=(5, 0), sticky="w")
        self.protocol_combobox.current(0)

        ttk.Label(device_frame, text="Baud Rate:").grid(row=1, column=2, padx=5, pady=(5, 0), sticky="w")
        self.baud_rate_variable = tk.StringVar()
        self.baud_rate_combobox = ttk.Combobox(
            device_frame,
            textvariable=self.baud_rate_variable,
            values=[name for name, _ in self.BAUD_RATE_OPTIONS],
            state="readonly",
            width=18
        )
        self.baud_rate_combobox.grid(row=1, column=3, padx=5, pady=(5, 0), sticky="w")
        self.baud_rate_combobox.current(0)

        # Row 2: Connect flags
        ttk.Label(device_frame, text="Connect Flags:").grid(row=2, column=0, padx=5, pady=(5, 0), sticky="w")
        self.connect_flags_variable = tk.StringVar(value="0")
        self.connect_flags_entry = ttk.Entry(
            device_frame,
            textvariable=self.connect_flags_variable,
            width=10
        )
        self.connect_flags_entry.grid(row=2, column=1, padx=5, pady=(5, 0), sticky="w")

        # Row 3: Buttons
        button_frame = ttk.Frame(device_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=(10, 0))

        self.open_device_button = ttk.Button(
            button_frame,
            text="Open Device",
            command=self._open_device
        )
        self.open_device_button.pack(side=tk.LEFT, padx=5)

        self.connect_channel_button = ttk.Button(
            button_frame,
            text="Connect Channel",
            command=self._connect_channel,
            state=tk.DISABLED
        )
        self.connect_channel_button.pack(side=tk.LEFT, padx=5)

        self.disconnect_channel_button = ttk.Button(
            button_frame,
            text="Disconnect",
            command=self._disconnect_channel,
            state=tk.DISABLED
        )
        self.disconnect_channel_button.pack(side=tk.LEFT, padx=5)

        self.close_device_button = ttk.Button(
            button_frame,
            text="Close Device",
            command=self._close_device,
            state=tk.DISABLED
        )
        self.close_device_button.pack(side=tk.LEFT, padx=5)

    def _create_filter_frame(self, parent: ttk.Frame) -> None:
        """Create the message filter configuration frame."""
        filter_frame = ttk.LabelFrame(parent, text="Filter Setup (ISO15765)", padding="5")
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Filter parameters
        ttk.Label(filter_frame, text="Mask ID:").grid(row=0, column=0, padx=5)
        self.mask_identifier_variable = tk.StringVar(value="0xFFFFFFFF")
        ttk.Entry(
            filter_frame,
            textvariable=self.mask_identifier_variable,
            width=12
        ).grid(row=0, column=1, padx=5)

        ttk.Label(filter_frame, text="Pattern ID:").grid(row=0, column=2, padx=5)
        self.pattern_identifier_variable = tk.StringVar(value="0x7E8")
        ttk.Entry(
            filter_frame,
            textvariable=self.pattern_identifier_variable,
            width=12
        ).grid(row=0, column=3, padx=5)

        ttk.Label(filter_frame, text="Flow Ctrl ID:").grid(row=0, column=4, padx=5)
        self.flow_control_identifier_variable = tk.StringVar(value="0x7E0")
        ttk.Entry(
            filter_frame,
            textvariable=self.flow_control_identifier_variable,
            width=12
        ).grid(row=0, column=5, padx=5)

        # Filter buttons
        self.set_filter_button = ttk.Button(
            filter_frame,
            text="Set Filter",
            command=self._set_filter,
            state=tk.DISABLED
        )
        self.set_filter_button.grid(row=0, column=6, padx=10)

        self.clear_filters_button = ttk.Button(
            filter_frame,
            text="Clear Filters",
            command=self._clear_filters,
            state=tk.DISABLED
        )
        self.clear_filters_button.grid(row=0, column=7, padx=5)

    def _create_message_frame(self, parent: ttk.Frame) -> None:
        """Create the message I/O frame."""
        message_frame = ttk.LabelFrame(parent, text="Message I/O", padding="5")
        message_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        message_frame.columnconfigure(1, weight=1)

        # TX data input
        ttk.Label(message_frame, text="TX Data (hex):").grid(row=0, column=0, padx=5)
        self.transmit_data_variable = tk.StringVar(value="22 F1 90")
        self.transmit_data_entry = ttk.Entry(
            message_frame,
            textvariable=self.transmit_data_variable,
            font=("Consolas", 10)
        )
        self.transmit_data_entry.grid(row=0, column=1, padx=5, sticky="ew")
        self.transmit_data_entry.bind("<Return>", lambda e: self._send_message())

        # TX buttons
        self.send_message_button = ttk.Button(
            message_frame,
            text="Send",
            command=self._send_message,
            state=tk.DISABLED
        )
        self.send_message_button.grid(row=0, column=2, padx=5)

        self.clear_receive_buffer_button = ttk.Button(
            message_frame,
            text="Clear RX",
            command=self._clear_rx_buffer,
            state=tk.DISABLED
        )
        self.clear_receive_buffer_button.grid(row=0, column=3, padx=5)

        # Response display
        ttk.Label(message_frame, text="Response:").grid(row=1, column=0, padx=5, pady=(10, 0))
        self.response_variable = tk.StringVar(value="--")
        self.response_label = ttk.Label(
            message_frame,
            textvariable=self.response_variable,
            font=("Consolas", 10),
            foreground="blue"
        )
        self.response_label.grid(row=1, column=1, padx=5, pady=(10, 0), sticky="w")

    def _create_config_frame(self, parent: ttk.Frame) -> None:
        """Create the configuration options frame."""
        config_frame = ttk.LabelFrame(parent, text="Configuration", padding="5")
        config_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        # Debug mode checkbox
        self.debug_mode_variable = tk.BooleanVar(value=j2534_config.debug_enabled)
        ttk.Checkbutton(
            config_frame,
            text="Debug Mode",
            variable=self.debug_mode_variable,
            command=self._toggle_debug_mode
        ).pack(side=tk.LEFT, padx=10)

        # Exception mode checkbox
        self.exception_mode_variable = tk.BooleanVar(value=j2534_config.raise_exceptions)
        ttk.Checkbutton(
            config_frame,
            text="Exception Mode",
            variable=self.exception_mode_variable,
            command=self._toggle_exception_mode
        ).pack(side=tk.LEFT, padx=10)

        # Version info button
        self.version_info_button = ttk.Button(
            config_frame,
            text="Get Version Info",
            command=self._show_version_info,
            state=tk.DISABLED
        )
        self.version_info_button.pack(side=tk.LEFT, padx=10)

    def _create_log_frame(self, parent: ttk.Frame) -> None:
        """Create the communication log frame."""
        log_frame = ttk.LabelFrame(parent, text="Communication Log", padding="5")
        log_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        # Log text widget
        self.log_text_widget = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 9),
            height=12,
            state=tk.DISABLED
        )
        self.log_text_widget.grid(row=0, column=0, sticky="nsew")

        # Clear button
        ttk.Button(
            log_frame,
            text="Clear Log",
            command=self._clear_log
        ).grid(row=1, column=0, pady=5)

    def _create_status_bar(self, parent: ttk.Frame) -> None:
        """Create the status bar."""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=5, column=0, sticky="ew")
        status_frame.columnconfigure(0, weight=1)

        self.status_variable = tk.StringVar(value="Ready - Select a device and click Open Device")
        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.status_variable,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.grid(row=0, column=0, sticky="ew")

        self.voltage_variable = tk.StringVar(value="Voltage: --")
        self.voltage_label = ttk.Label(
            status_frame,
            textvariable=self.voltage_variable,
            relief=tk.SUNKEN,
            width=15
        )
        self.voltage_label.grid(row=0, column=1)

    # =========================================================================
    # Device Operations
    # =========================================================================

    def _refresh_device_list(self) -> None:
        """Refresh the list of available J2534 devices."""
        self.devices = get_list_j2534_devices()
        # devices is a list of [name, dll_path] pairs
        device_names = [device[0] for device in self.devices] if self.devices else ["No devices found"]
        self.device_combobox["values"] = device_names
        self.device_combobox.current(0)

        if self.devices:
            self._log_message(f"Found {len(self.devices)} J2534 device(s)")
        else:
            self._log_message("No J2534 devices found in registry")

    def _open_device(self) -> None:
        """Open the selected J2534 device."""
        if not self.devices:
            messagebox.showwarning("Error", "No devices available")
            return

        device_index = self.device_combobox.current()
        self._log_message(f"Opening device {device_index}: {self.devices[device_index][0]}")
        self.status_variable.set("Opening device...")
        self.root.update()

        try:
            set_j2534_device_to_connect(device_index)
            result = pt_open()

            if result is False:
                self._log_message("Failed to open device")
                self.status_variable.set("Failed to open device")
                messagebox.showwarning("Error", "Failed to open device")
                return

            self.device_identifier = result
            self.is_device_open = True
            self._log_message(f"Device opened successfully (ID: {self.device_identifier})")
            self.status_variable.set(f"Device open (ID: {self.device_identifier})")

            # Update UI state
            self._update_ui_state()

            # Start voltage monitoring
            self._start_voltage_timer()

        except Exception as error:
            self._log_message(f"Error opening device: {error}")
            self.status_variable.set("Error")
            messagebox.showerror("Error", str(error))

    def _close_device(self) -> None:
        """Close the open device."""
        if not self.is_device_open:
            return

        # Disconnect channel first if connected
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
        self.voltage_variable.set("Voltage: --")
        self.status_variable.set("Device closed")

        self._update_ui_state()

    def _connect_channel(self) -> None:
        """Connect a protocol channel."""
        if not self.is_device_open:
            return

        # Get selected protocol and baud rate
        protocol_index = self.protocol_combobox.current()
        protocol_identifier = self.PROTOCOL_OPTIONS[protocol_index][1]

        baud_rate_index = self.baud_rate_combobox.current()
        baud_rate_value = self.BAUD_RATE_OPTIONS[baud_rate_index][1]

        try:
            connect_flags = int(self.connect_flags_variable.get(), 0)
        except ValueError:
            connect_flags = 0

        self._log_message(
            f"Connecting channel: Protocol={protocol_identifier}, "
            f"Baud={baud_rate_value}, Flags={connect_flags}"
        )
        self.status_variable.set("Connecting channel...")
        self.root.update()

        try:
            result = pt_connect(
                self.device_identifier,
                protocol_identifier,
                connect_flags,
                baud_rate_value
            )

            if result is False:
                self._log_message("Failed to connect channel")
                self.status_variable.set("Failed to connect channel")
                messagebox.showwarning("Error", "Failed to connect channel")
                return

            self.channel_identifier = result
            self.is_channel_connected = True
            self._log_message(f"Channel connected (ID: {self.channel_identifier})")
            self.status_variable.set(f"Channel connected (ID: {self.channel_identifier})")

            self._update_ui_state()

        except Exception as error:
            self._log_message(f"Error connecting channel: {error}")
            self.status_variable.set("Error")
            messagebox.showerror("Error", str(error))

    def _disconnect_channel(self) -> None:
        """Disconnect the active channel."""
        if not self.is_channel_connected:
            return

        # Clear filter first
        if self.filter_identifier is not None:
            self._clear_filters()

        try:
            result = pt_disconnect(self.channel_identifier)
            self._log_message(f"Channel disconnected (result: {result})")
        except Exception as error:
            self._log_message(f"Error disconnecting channel: {error}")

        self.channel_identifier = None
        self.is_channel_connected = False
        self.status_variable.set("Channel disconnected")

        self._update_ui_state()

    # =========================================================================
    # Filter Operations
    # =========================================================================

    def _set_filter(self) -> None:
        """Set a message filter."""
        if not self.is_channel_connected:
            return

        try:
            mask_identifier = int(self.mask_identifier_variable.get(), 0)
            pattern_identifier = int(self.pattern_identifier_variable.get(), 0)
            flow_control_identifier = int(self.flow_control_identifier_variable.get(), 0)
        except ValueError as error:
            messagebox.showwarning("Invalid Input", f"Invalid filter value: {error}")
            return

        # Get current protocol
        protocol_index = self.protocol_combobox.current()
        protocol_identifier = self.PROTOCOL_OPTIONS[protocol_index][1]

        self._log_message(
            f"Setting filter: Mask=0x{mask_identifier:X}, "
            f"Pattern=0x{pattern_identifier:X}, FC=0x{flow_control_identifier:X}"
        )

        try:
            result = pt_start_ecu_filter(
                self.channel_identifier,
                protocol_identifier,
                mask_identifier,
                pattern_identifier,
                flow_control_identifier,
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

        # Parse hex input
        hex_text = self.transmit_data_variable.get().strip()
        try:
            hex_text = hex_text.replace(" ", "").replace(",", "").replace("0x", "")
            data_bytes = [int(hex_text[i:i+2], 16) for i in range(0, len(hex_text), 2)]
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter valid hex bytes")
            return

        if not data_bytes:
            return

        # Get current protocol
        protocol_index = self.protocol_combobox.current()
        protocol_identifier = self.PROTOCOL_OPTIONS[protocol_index][1]

        # Build and send message
        transmit_message = PassThruMsgBuilder(protocol_identifier, TxFlags.ISO15765_FRAME_PAD)
        transmit_id = int(self.flow_control_identifier_variable.get(), 0)  # Use FC ID as TX ID
        transmit_message.set_identifier_and_data(transmit_id, data_bytes)

        tx_hex = " ".join(f"{b:02X}" for b in data_bytes)
        self._log_message(f"TX [{transmit_id:03X}]: {tx_hex}")

        try:
            write_result = pt_write_message(self.channel_identifier, transmit_message, 1, 1000)

            if write_result != 0:
                self._log_message(f"Write failed (error: {write_result})")
                self.response_variable.set(f"Write error: {write_result}")
                return

            # Read response
            receive_message = PassThruMsgBuilder(protocol_identifier, 0)
            read_result = pt_read_message(self.channel_identifier, receive_message, 1, 1000)

            if read_result == 0:
                response_hex = receive_message.dump_output()
                formatted_response = " ".join(
                    response_hex[i:i+2] for i in range(0, len(response_hex), 2)
                )
                self.response_variable.set(formatted_response)
                self._log_message(f"RX: {formatted_response}")
            elif read_result == 0x10:  # Buffer empty
                self.response_variable.set("No response (timeout)")
                self._log_message("RX: No response (buffer empty)")
            else:
                self.response_variable.set(f"Read error: {read_result}")
                self._log_message(f"RX: Read error {read_result}")

        except Exception as error:
            self._log_message(f"Error: {error}")
            self.response_variable.set(f"Error: {error}")

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
        if self.debug_mode_variable.get():
            j2534_config.enable_debug()
            self._log_message("Debug mode enabled")
        else:
            j2534_config.disable_debug()
            self._log_message("Debug mode disabled")

    def _toggle_exception_mode(self) -> None:
        """Toggle exception mode on/off."""
        if self.exception_mode_variable.get():
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
                messagebox.showinfo(
                    "Version Info",
                    f"Firmware: {versions[0]}\nDLL: {versions[1]}\nAPI: {versions[2]}"
                )
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
                    self.voltage_variable.set(f"Voltage: {voltage:.2f}V")
                else:
                    self.voltage_variable.set("Voltage: --")
            except Exception:
                self.voltage_variable.set("Voltage: Error")

    def _start_voltage_timer(self) -> None:
        """Start periodic voltage updates."""
        if self.is_device_open:
            self._update_voltage_display()
            self.voltage_timer_identifier = self.root.after(5000, self._start_voltage_timer)

    def _stop_voltage_timer(self) -> None:
        """Stop voltage update timer."""
        if self.voltage_timer_identifier:
            self.root.after_cancel(self.voltage_timer_identifier)
            self.voltage_timer_identifier = None

    def _update_ui_state(self) -> None:
        """Update UI element states based on connection status."""
        # Device buttons
        self.open_device_button.config(
            state=tk.NORMAL if not self.is_device_open else tk.DISABLED
        )
        self.close_device_button.config(
            state=tk.NORMAL if self.is_device_open else tk.DISABLED
        )

        # Channel buttons
        self.connect_channel_button.config(
            state=tk.NORMAL if self.is_device_open and not self.is_channel_connected else tk.DISABLED
        )
        self.disconnect_channel_button.config(
            state=tk.NORMAL if self.is_channel_connected else tk.DISABLED
        )

        # Filter buttons
        self.set_filter_button.config(
            state=tk.NORMAL if self.is_channel_connected else tk.DISABLED
        )
        self.clear_filters_button.config(
            state=tk.NORMAL if self.is_channel_connected else tk.DISABLED
        )

        # Message buttons
        self.send_message_button.config(
            state=tk.NORMAL if self.is_channel_connected else tk.DISABLED
        )
        self.clear_receive_buffer_button.config(
            state=tk.NORMAL if self.is_channel_connected else tk.DISABLED
        )

        # Version button
        self.version_info_button.config(
            state=tk.NORMAL if self.is_device_open else tk.DISABLED
        )

        # Device combobox
        self.device_combobox.config(
            state="readonly" if not self.is_device_open else tk.DISABLED
        )

    def _log_message(self, message: str) -> None:
        """Add a timestamped message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_text_widget.config(state=tk.NORMAL)
        self.log_text_widget.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text_widget.see(tk.END)
        self.log_text_widget.config(state=tk.DISABLED)

    def _clear_log(self) -> None:
        """Clear the log text widget."""
        self.log_text_widget.config(state=tk.NORMAL)
        self.log_text_widget.delete(1.0, tk.END)
        self.log_text_widget.config(state=tk.DISABLED)

    def cleanup(self) -> None:
        """Clean up resources before closing."""
        if self.is_channel_connected:
            self._disconnect_channel()
        if self.is_device_open:
            self._close_device()


def main() -> None:
    """Application entry point."""
    root = tk.Tk()

    # Try to use a modern theme
    try:
        style = ttk.Style()
        style.theme_use('clam')
    except Exception:
        pass

    app = J2534ApiDemo(root)

    # Handle window close
    def on_closing():
        app.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
