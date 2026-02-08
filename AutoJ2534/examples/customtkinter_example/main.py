"""
CustomTkinter J2534 Diagnostic Tool Example
===========================================

A modern-looking GUI using CustomTkinter - Tkinter with a modern theme.

Requirements:
    pip install customtkinter

Usage:
    python main.py

Version: 1.0.0
License: MIT
"""

import sys
import customtkinter as ctk
from datetime import datetime

# Add the project root to path (two levels up from this file)
import os
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from J2534_REGISTRY import get_all_j2534_devices
from AutoJ2534 import j2534_communication, Connections


class J2534DiagnosticTool(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("J2534 Diagnostic Tool - CustomTkinter")
        self.geometry("800x600")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.devices = []
        self.configs = list(Connections.CHRYSLER_ECU.keys())
        self.is_connected = False

        self.setup_ui()
        self.refresh_devices()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Connection Frame
        conn_frame = ctk.CTkFrame(self)
        conn_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        conn_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(conn_frame, text="Device:").grid(row=0, column=0, padx=5, pady=5)
        self.device_combo = ctk.CTkComboBox(conn_frame, values=["No devices"], width=300)
        self.device_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(conn_frame, text="Protocol:").grid(row=0, column=2, padx=5, pady=5)
        self.protocol_combo = ctk.CTkComboBox(conn_frame, values=self.configs, width=150)
        self.protocol_combo.grid(row=0, column=3, padx=5, pady=5)
        self.protocol_combo.set(self.configs[0])

        btn_frame = ctk.CTkFrame(conn_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=4, padx=5, pady=5)
        ctk.CTkButton(btn_frame, text="Refresh", width=80, command=self.refresh_devices).pack(side="left", padx=2)
        self.connect_btn = ctk.CTkButton(btn_frame, text="Connect", width=80, command=self.toggle_connection)
        self.connect_btn.pack(side="left", padx=2)

        self.voltage_label = ctk.CTkLabel(conn_frame, text="Voltage: --")
        self.voltage_label.grid(row=0, column=5, padx=10)

        # Message Frame
        msg_frame = ctk.CTkFrame(self)
        msg_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        msg_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(msg_frame, text="Data (hex):").grid(row=0, column=0, padx=5, pady=5)
        self.data_entry = ctk.CTkEntry(msg_frame, placeholder_text="3E 00")
        self.data_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.data_entry.insert(0, "3E 00")

        self.send_btn = ctk.CTkButton(msg_frame, text="Send", width=80, command=self.send_message, state="disabled")
        self.send_btn.grid(row=0, column=2, padx=5, pady=5)

        ctk.CTkLabel(msg_frame, text="Response:").grid(row=1, column=0, padx=5, pady=5)
        self.response_label = ctk.CTkLabel(msg_frame, text="--", text_color="cyan")
        self.response_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Log Frame
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)

        self.log_text = ctk.CTkTextbox(log_frame, font=("Consolas", 11))
        self.log_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.log_text.configure(state="disabled")

        ctk.CTkButton(log_frame, text="Clear Log", width=100, command=self.clear_log).grid(row=1, column=0, pady=5)

        # Status
        self.status_label = ctk.CTkLabel(self, text="Ready - Select a device and click Connect")
        self.status_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")

    def refresh_devices(self):
        self.devices = get_all_j2534_devices()
        names = [d.name for d in self.devices] if self.devices else ["No devices"]
        self.device_combo.configure(values=names)
        self.device_combo.set(names[0])
        self.log(f"Found {len(self.devices)} device(s)")

    def toggle_connection(self):
        if self.is_connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        if not self.devices:
            return

        device_idx = 0
        for i, d in enumerate(self.devices):
            if d.name == self.device_combo.get():
                device_idx = i
                break

        self.log(f"Connecting to device {device_idx}...")
        self.status_label.configure(text="Connecting...")
        self.update()

        try:
            if j2534_communication.open_communication(device_idx, self.protocol_combo.get()):
                self.is_connected = True
                self.connect_btn.configure(text="Disconnect")
                self.send_btn.configure(state="normal")
                self.log("Connected!")
                self.status_label.configure(text="Connected")

                info = j2534_communication.tool_info()
                if info:
                    self.log(f"Device: {info[0]}")

                self.update_voltage()
                self.start_voltage_timer()
            else:
                self.log("Connection failed!")
                self.status_label.configure(text="Failed")
        except Exception as e:
            self.log(f"Error: {e}")

    def disconnect(self):
        self.stop_voltage_timer()
        try:
            j2534_communication.disconnect()
            j2534_communication.close()
        except Exception:
            pass

        self.is_connected = False
        self.connect_btn.configure(text="Connect")
        self.send_btn.configure(state="disabled")
        self.voltage_label.configure(text="Voltage: --")
        self.log("Disconnected")
        self.status_label.configure(text="Disconnected")

    def send_message(self):
        if not self.is_connected:
            return

        hex_text = self.data_entry.get().strip().replace(" ", "").replace(",", "")
        try:
            data_bytes = [int(hex_text[i:i+2], 16) for i in range(0, len(hex_text), 2)]
        except ValueError:
            self.log("Invalid hex input")
            return

        if not data_bytes:
            return

        self.log(f"TX: {' '.join(f'{b:02X}' for b in data_bytes)}")

        try:
            response = j2534_communication.transmit_and_receive_message(data_bytes)
            if response is False:
                self.response_label.configure(text="No response")
                self.log("RX: No response")
            elif isinstance(response, str):
                formatted = " ".join(response[i:i+2] for i in range(0, len(response), 2))
                self.response_label.configure(text=formatted)
                self.log(f"RX: {formatted}")
            else:
                self.response_label.configure(text=str(response))
        except Exception as e:
            self.log(f"Error: {e}")

    def update_voltage(self):
        if self.is_connected:
            try:
                voltage = j2534_communication.check_volts()
                if voltage:
                    self.voltage_label.configure(text=f"Voltage: {voltage:.2f}V")
            except Exception:
                pass

    def start_voltage_timer(self):
        if self.is_connected:
            self.update_voltage()
            self.voltage_timer = self.after(5000, self.start_voltage_timer)

    def stop_voltage_timer(self):
        if hasattr(self, 'voltage_timer'):
            self.after_cancel(self.voltage_timer)

    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{timestamp}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")


def main():
    app = J2534DiagnosticTool()
    app.protocol("WM_DELETE_WINDOW", lambda: (app.disconnect() if app.is_connected else None, app.destroy()))
    app.mainloop()


if __name__ == "__main__":
    main()
