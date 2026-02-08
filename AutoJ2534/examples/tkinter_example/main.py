"""
Tkinter J2534 Diagnostic Tool Example
=====================================

A beginner-friendly GUI application demonstrating J2534 communication
using Python's built-in Tkinter library. No external dependencies required!

Requirements:
    None (Tkinter is included with Python)

Usage:
    python main.py

Version: 1.0.0
License: MIT
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

# Add the project root to path (two levels up from this file)
import os
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from J2534_REGISTRY import get_all_j2534_devices
from AutoJ2534 import j2534_communication, Connections


class J2534DiagnosticTool:
    """Main application class for J2534 diagnostic tool."""

    def __init__(self, root):
        self.root = root
        self.root.title("J2534 Diagnostic Tool - Tkinter")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)

        self.devices = []
        self.connection_configs = list(Connections.CHRYSLER_ECU.keys())
        self.is_connected = False

        self.setup_ui()
        self.refresh_devices()

    def setup_ui(self):
        """Set up the user interface."""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # === Connection Frame ===
        conn_frame = ttk.LabelFrame(main_frame, text="Connection", padding="5")
        conn_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        conn_frame.columnconfigure(1, weight=1)
        conn_frame.columnconfigure(3, weight=1)

        # Device selection
        ttk.Label(conn_frame, text="Device:").grid(row=0, column=0, padx=5)
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(conn_frame, textvariable=self.device_var,
                                          state="readonly", width=30)
        self.device_combo.grid(row=0, column=1, padx=5, sticky="ew")

        # Protocol selection
        ttk.Label(conn_frame, text="Protocol:").grid(row=0, column=2, padx=5)
        self.protocol_var = tk.StringVar()
        self.protocol_combo = ttk.Combobox(conn_frame, textvariable=self.protocol_var,
                                            values=self.connection_configs,
                                            state="readonly", width=15)
        self.protocol_combo.grid(row=0, column=3, padx=5, sticky="ew")
        self.protocol_combo.current(0)

        # Buttons
        btn_frame = ttk.Frame(conn_frame)
        btn_frame.grid(row=0, column=4, padx=5)

        self.refresh_btn = ttk.Button(btn_frame, text="Refresh",
                                       command=self.refresh_devices)
        self.refresh_btn.pack(side=tk.LEFT, padx=2)

        self.connect_btn = ttk.Button(btn_frame, text="Connect",
                                       command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=2)

        # === Message Frame ===
        msg_frame = ttk.LabelFrame(main_frame, text="Send Message", padding="5")
        msg_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        msg_frame.columnconfigure(1, weight=1)

        # Data input
        ttk.Label(msg_frame, text="Data (hex):").grid(row=0, column=0, padx=5)
        self.data_entry = ttk.Entry(msg_frame, font=("Consolas", 10))
        self.data_entry.grid(row=0, column=1, padx=5, sticky="ew")
        self.data_entry.insert(0, "3E 00")
        self.data_entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = ttk.Button(msg_frame, text="Send", command=self.send_message,
                                    state=tk.DISABLED)
        self.send_btn.grid(row=0, column=2, padx=5)

        # Response
        ttk.Label(msg_frame, text="Response:").grid(row=1, column=0, padx=5, pady=(10, 0))
        self.response_var = tk.StringVar(value="--")
        self.response_label = ttk.Label(msg_frame, textvariable=self.response_var,
                                         font=("Consolas", 10), foreground="blue")
        self.response_label.grid(row=1, column=1, padx=5, pady=(10, 0), sticky="w")

        # === Log Frame ===
        log_frame = ttk.LabelFrame(main_frame, text="Communication Log", padding="5")
        log_frame.grid(row=2, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        # Log text widget
        self.log_text = scrolledtext.ScrolledText(log_frame, font=("Consolas", 9),
                                                   height=15, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # Clear button
        ttk.Button(log_frame, text="Clear Log",
                   command=self.clear_log).grid(row=1, column=0, pady=5)

        # === Status Bar ===
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Ready - Select a device and click Connect")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                       relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=0, column=0, sticky="ew")

        self.voltage_var = tk.StringVar(value="Voltage: --")
        self.voltage_label = ttk.Label(status_frame, textvariable=self.voltage_var,
                                        relief=tk.SUNKEN, width=15)
        self.voltage_label.grid(row=0, column=1)

    def refresh_devices(self):
        """Refresh device list from registry."""
        self.devices = get_all_j2534_devices()
        device_names = [d.name for d in self.devices] if self.devices else ["No devices found"]
        self.device_combo["values"] = device_names
        self.device_combo.current(0)

        if self.devices:
            self.log_message(f"Found {len(self.devices)} J2534 device(s)")
        else:
            self.log_message("No J2534 devices found in registry")

    def toggle_connection(self):
        """Connect or disconnect from device."""
        if self.is_connected:
            self.disconnect_device()
        else:
            self.connect_device()

    def connect_device(self):
        """Establish connection to selected device."""
        if not self.devices:
            messagebox.showwarning("Error", "No devices available")
            return

        device_index = self.device_combo.current()
        config_key = self.protocol_var.get()

        self.log_message(f"Connecting to device {device_index} with config '{config_key}'...")
        self.status_var.set("Connecting...")
        self.root.update()

        try:
            if j2534_communication.open_communication(device_index, config_key):
                self.is_connected = True
                self.connect_btn.config(text="Disconnect")
                self.send_btn.config(state=tk.NORMAL)
                self.device_combo.config(state=tk.DISABLED)
                self.protocol_combo.config(state=tk.DISABLED)

                self.log_message("Connected successfully!")
                self.status_var.set("Connected")

                # Get device info
                info = j2534_communication.tool_info()
                if info:
                    self.log_message(f"Device: {info[0]}, FW: {info[1]}, DLL: {info[2]}")

                # Update voltage
                self.update_voltage()
                self.start_voltage_timer()
            else:
                self.log_message("Connection failed!")
                self.status_var.set("Connection failed")
                messagebox.showwarning("Connection Failed",
                                        "Failed to connect. Check device and vehicle.")
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            self.status_var.set("Error")

    def disconnect_device(self):
        """Disconnect from device."""
        self.stop_voltage_timer()

        try:
            j2534_communication.disconnect()
            j2534_communication.close()
        except Exception:
            pass

        self.is_connected = False
        self.connect_btn.config(text="Connect")
        self.send_btn.config(state=tk.DISABLED)
        self.device_combo.config(state="readonly")
        self.protocol_combo.config(state="readonly")
        self.voltage_var.set("Voltage: --")

        self.log_message("Disconnected")
        self.status_var.set("Disconnected")

    def send_message(self):
        """Send message to ECU."""
        if not self.is_connected:
            return

        hex_text = self.data_entry.get().strip()
        try:
            hex_text = hex_text.replace(" ", "").replace(",", "").replace("0x", "")
            data_bytes = [int(hex_text[i:i+2], 16) for i in range(0, len(hex_text), 2)]
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter valid hex bytes")
            return

        if not data_bytes:
            return

        tx_hex = " ".join(f"{b:02X}" for b in data_bytes)
        self.log_message(f"TX: {tx_hex}")

        try:
            response = j2534_communication.transmit_and_receive_message(data_bytes)

            if response is False:
                self.response_var.set("No response (timeout)")
                self.log_message("RX: No response")
            elif isinstance(response, str):
                formatted = " ".join(response[i:i+2] for i in range(0, len(response), 2))
                self.response_var.set(formatted)
                self.log_message(f"RX: {formatted}")
            else:
                self.response_var.set(str(response))
                self.log_message(f"RX: {response}")
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            self.response_var.set(f"Error: {str(e)}")

    def update_voltage(self):
        """Update battery voltage display."""
        if self.is_connected:
            try:
                voltage = j2534_communication.check_volts()
                if voltage:
                    self.voltage_var.set(f"Voltage: {voltage:.2f}V")
                else:
                    self.voltage_var.set("Voltage: Low/Error")
            except Exception:
                self.voltage_var.set("Voltage: Error")

    def start_voltage_timer(self):
        """Start periodic voltage updates."""
        if self.is_connected:
            self.update_voltage()
            self.voltage_timer_id = self.root.after(5000, self.start_voltage_timer)

    def stop_voltage_timer(self):
        """Stop voltage update timer."""
        if hasattr(self, 'voltage_timer_id'):
            self.root.after_cancel(self.voltage_timer_id)

    def log_message(self, message: str):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        """Clear the log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)


def main():
    root = tk.Tk()

    # Try to use a modern theme
    try:
        style = ttk.Style()
        style.theme_use('clam')
    except Exception:
        pass

    app = J2534DiagnosticTool(root)

    # Handle window close
    def on_closing():
        if app.is_connected:
            app.disconnect_device()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
