"""
PyQt5 J2534 Diagnostic Tool Example
===================================

A full-featured GUI application demonstrating J2534 communication
using PyQt5. This example shows:

    - Device selection from registry
    - Protocol configuration
    - Message transmission and reception
    - Real-time logging with hex display
    - Battery voltage monitoring

Requirements:
    pip install PyQt5

Usage:
    python main.py

Version: 1.0.0
License: MIT
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QComboBox, QPushButton, QTextEdit, QLineEdit,
    QLabel, QStatusBar, QMessageBox, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# Add the project root to path (two levels up from this file)
import os
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from J2534_REGISTRY import get_all_j2534_devices, J2534DeviceInfo
from AutoJ2534 import j2534_communication, Connections


class J2534DiagnosticTool(QMainWindow):
    """Main window for J2534 diagnostic tool."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("J2534 Diagnostic Tool - PyQt5")
        self.setMinimumSize(800, 600)

        self.devices = []
        self.connection_configs = list(Connections.CHRYSLER_ECU.keys())
        self.is_connected = False

        self.setup_ui()
        self.refresh_devices()

        # Voltage monitoring timer
        self.voltage_timer = QTimer()
        self.voltage_timer.timeout.connect(self.update_voltage)

    def setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Connection group
        connection_group = QGroupBox("Connection")
        connection_layout = QHBoxLayout(connection_group)

        # Device selection
        connection_layout.addWidget(QLabel("Device:"))
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(200)
        connection_layout.addWidget(self.device_combo)

        # Protocol selection
        connection_layout.addWidget(QLabel("Protocol:"))
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(self.connection_configs)
        connection_layout.addWidget(self.protocol_combo)

        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_devices)
        connection_layout.addWidget(self.refresh_button)

        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        connection_layout.addWidget(self.connect_button)

        connection_layout.addStretch()
        main_layout.addWidget(connection_group)

        # Splitter for message panel and log
        splitter = QSplitter(Qt.Vertical)

        # Message panel
        message_group = QGroupBox("Send Message")
        message_layout = QVBoxLayout(message_group)

        # Data input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Data (hex):"))
        self.data_input = QLineEdit()
        self.data_input.setPlaceholderText("Example: 3E 00 or 22 F1 90")
        self.data_input.setFont(QFont("Consolas", 10))
        input_layout.addWidget(self.data_input)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setEnabled(False)
        input_layout.addWidget(self.send_button)

        message_layout.addLayout(input_layout)

        # Response display
        message_layout.addWidget(QLabel("Response:"))
        self.response_display = QTextEdit()
        self.response_display.setReadOnly(True)
        self.response_display.setFont(QFont("Consolas", 10))
        self.response_display.setMaximumHeight(100)
        message_layout.addWidget(self.response_display)

        splitter.addWidget(message_group)

        # Log panel
        log_group = QGroupBox("Communication Log")
        log_layout = QVBoxLayout(log_group)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_display)

        # Clear log button
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.log_display.clear)
        log_layout.addWidget(clear_button)

        splitter.addWidget(log_group)

        main_layout.addWidget(splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.voltage_label = QLabel("Voltage: --")
        self.status_bar.addPermanentWidget(self.voltage_label)
        self.status_bar.showMessage("Ready - Select a device and click Connect")

    def refresh_devices(self):
        """Refresh the device list from registry."""
        self.device_combo.clear()
        self.devices = get_all_j2534_devices()

        if not self.devices:
            self.device_combo.addItem("No devices found")
            self.log_message("No J2534 devices found in registry")
        else:
            for device in self.devices:
                self.device_combo.addItem(device.name)
            self.log_message(f"Found {len(self.devices)} J2534 device(s)")

    def toggle_connection(self):
        """Connect or disconnect from the device."""
        if self.is_connected:
            self.disconnect_device()
        else:
            self.connect_device()

    def connect_device(self):
        """Establish connection to selected device."""
        if not self.devices:
            QMessageBox.warning(self, "Error", "No devices available")
            return

        device_index = self.device_combo.currentIndex()
        config_key = self.protocol_combo.currentText()

        self.log_message(f"Connecting to device {device_index} with config '{config_key}'...")
        self.status_bar.showMessage("Connecting...")

        try:
            if j2534_communication.open_communication(device_index, config_key):
                self.is_connected = True
                self.connect_button.setText("Disconnect")
                self.send_button.setEnabled(True)
                self.device_combo.setEnabled(False)
                self.protocol_combo.setEnabled(False)

                # Start voltage monitoring
                self.voltage_timer.start(5000)
                self.update_voltage()

                self.log_message("Connected successfully!")
                self.status_bar.showMessage("Connected")

                # Get device info
                info = j2534_communication.tool_info()
                if info:
                    self.log_message(f"Device: {info[0]}, FW: {info[1]}, DLL: {info[2]}")
            else:
                self.log_message("Connection failed!")
                self.status_bar.showMessage("Connection failed")
                QMessageBox.warning(self, "Connection Failed",
                                    "Failed to connect. Check device and vehicle connection.")
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            self.status_bar.showMessage("Error")

    def disconnect_device(self):
        """Disconnect from the device."""
        self.voltage_timer.stop()

        try:
            j2534_communication.disconnect()
            j2534_communication.close()
        except Exception:
            pass

        self.is_connected = False
        self.connect_button.setText("Connect")
        self.send_button.setEnabled(False)
        self.device_combo.setEnabled(True)
        self.protocol_combo.setEnabled(True)
        self.voltage_label.setText("Voltage: --")

        self.log_message("Disconnected")
        self.status_bar.showMessage("Disconnected")

    def send_message(self):
        """Send message to ECU."""
        if not self.is_connected:
            return

        # Parse hex input
        hex_text = self.data_input.text().strip()
        try:
            # Remove common separators and parse
            hex_text = hex_text.replace(" ", "").replace(",", "").replace("0x", "")
            data_bytes = [int(hex_text[i:i+2], 16) for i in range(0, len(hex_text), 2)]
        except ValueError:
            QMessageBox.warning(self, "Invalid Input",
                                "Please enter valid hex bytes (e.g., 3E 00)")
            return

        if not data_bytes:
            return

        # Format for log
        tx_hex = " ".join(f"{b:02X}" for b in data_bytes)
        self.log_message(f"TX: {tx_hex}")

        # Send and receive
        try:
            response = j2534_communication.transmit_and_receive_message(data_bytes)

            if response is False:
                self.response_display.setText("No response (timeout)")
                self.log_message("RX: No response")
            elif isinstance(response, str):
                # Format response
                formatted = " ".join(response[i:i+2] for i in range(0, len(response), 2))
                self.response_display.setText(formatted)
                self.log_message(f"RX: {formatted}")
            else:
                self.response_display.setText(str(response))
                self.log_message(f"RX: {response}")
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            self.response_display.setText(f"Error: {str(e)}")

    def update_voltage(self):
        """Update battery voltage display."""
        if self.is_connected:
            try:
                voltage = j2534_communication.check_volts()
                if voltage:
                    self.voltage_label.setText(f"Voltage: {voltage:.2f}V")
                else:
                    self.voltage_label.setText("Voltage: Low/Error")
            except Exception:
                self.voltage_label.setText("Voltage: Error")

    def log_message(self, message: str):
        """Add message to log with timestamp."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_display.append(f"[{timestamp}] {message}")

    def closeEvent(self, event):
        """Handle window close."""
        if self.is_connected:
            self.disconnect_device()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = J2534DiagnosticTool()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
