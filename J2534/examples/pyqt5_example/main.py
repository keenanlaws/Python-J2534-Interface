"""
PyQt5 J2534 Low-Level API Demo
==============================

A professional-grade GUI application demonstrating the low-level J2534 PassThru API
using PyQt5. Features sortable tables, dock widgets, and modern styling.

This example showcases:
    - Device discovery and selection
    - Device open/close operations
    - Protocol channel connect/disconnect
    - Message filter configuration
    - Message transmission and reception
    - Battery voltage monitoring
    - Debug and exception mode configuration

Requirements:
    pip install PyQt5

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

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QComboBox, QPushButton, QLineEdit, QTextEdit,
    QCheckBox, QStatusBar, QMessageBox, QGridLayout, QSplitter,
    QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette

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


class J2534ApiDemo(QMainWindow):
    """
    Main application window for J2534 low-level API demonstration.

    This class provides a professional PyQt5 GUI for interacting with J2534 devices
    at the low level, demonstrating all major API functions.
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

        self.setWindowTitle("J2534 Low-Level API Demo - PyQt5")
        self.setMinimumSize(900, 700)

        # State variables
        self.device_identifier: Optional[int] = None
        self.channel_identifier: Optional[int] = None
        self.filter_identifier: Optional[int] = None
        self.is_device_open: bool = False
        self.is_channel_connected: bool = False
        self.devices: List = []

        # Voltage update timer
        self.voltage_timer = QTimer()
        self.voltage_timer.timeout.connect(self._update_voltage_display)

        # Build the UI
        self._create_widgets()
        self._refresh_device_list()

    def _create_widgets(self) -> None:
        """Create and layout all UI widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create sections
        main_layout.addWidget(self._create_device_group())
        main_layout.addWidget(self._create_filter_group())
        main_layout.addWidget(self._create_message_group())
        main_layout.addWidget(self._create_config_group())
        main_layout.addWidget(self._create_log_group(), 1)  # Stretch factor

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Ready - Select a device and click Open Device")
        self.voltage_label = QLabel("Voltage: --")
        self.voltage_label.setFixedWidth(120)

        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addPermanentWidget(self.voltage_label)

    def _create_device_group(self) -> QGroupBox:
        """Create the device connection group box."""
        group = QGroupBox("Device && Channel")
        layout = QGridLayout(group)

        # Row 0: Device selection
        layout.addWidget(QLabel("Device:"), 0, 0)
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(300)
        layout.addWidget(self.device_combo, 0, 1)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._refresh_device_list)
        layout.addWidget(self.refresh_button, 0, 2)

        # Row 1: Protocol and baud rate
        layout.addWidget(QLabel("Protocol:"), 1, 0)
        self.protocol_combo = QComboBox()
        for name, _ in self.PROTOCOL_OPTIONS:
            self.protocol_combo.addItem(name)
        layout.addWidget(self.protocol_combo, 1, 1)

        layout.addWidget(QLabel("Baud Rate:"), 1, 2)
        self.baud_rate_combo = QComboBox()
        for name, _ in self.BAUD_RATE_OPTIONS:
            self.baud_rate_combo.addItem(name)
        layout.addWidget(self.baud_rate_combo, 1, 3)

        # Row 2: Connect flags
        layout.addWidget(QLabel("Connect Flags:"), 2, 0)
        self.connect_flags_edit = QLineEdit("0")
        self.connect_flags_edit.setMaximumWidth(100)
        layout.addWidget(self.connect_flags_edit, 2, 1)

        # Row 3: Buttons
        button_layout = QHBoxLayout()

        self.open_device_button = QPushButton("Open Device")
        self.open_device_button.clicked.connect(self._open_device)
        button_layout.addWidget(self.open_device_button)

        self.connect_channel_button = QPushButton("Connect Channel")
        self.connect_channel_button.clicked.connect(self._connect_channel)
        self.connect_channel_button.setEnabled(False)
        button_layout.addWidget(self.connect_channel_button)

        self.disconnect_channel_button = QPushButton("Disconnect")
        self.disconnect_channel_button.clicked.connect(self._disconnect_channel)
        self.disconnect_channel_button.setEnabled(False)
        button_layout.addWidget(self.disconnect_channel_button)

        self.close_device_button = QPushButton("Close Device")
        self.close_device_button.clicked.connect(self._close_device)
        self.close_device_button.setEnabled(False)
        button_layout.addWidget(self.close_device_button)

        button_layout.addStretch()
        layout.addLayout(button_layout, 3, 0, 1, 4)

        return group

    def _create_filter_group(self) -> QGroupBox:
        """Create the message filter configuration group box."""
        group = QGroupBox("Filter Setup (ISO15765)")
        layout = QHBoxLayout(group)

        layout.addWidget(QLabel("Mask ID:"))
        self.mask_id_edit = QLineEdit("0xFFFFFFFF")
        self.mask_id_edit.setMaximumWidth(100)
        layout.addWidget(self.mask_id_edit)

        layout.addWidget(QLabel("Pattern ID:"))
        self.pattern_id_edit = QLineEdit("0x7E8")
        self.pattern_id_edit.setMaximumWidth(100)
        layout.addWidget(self.pattern_id_edit)

        layout.addWidget(QLabel("Flow Ctrl ID:"))
        self.flow_control_id_edit = QLineEdit("0x7E0")
        self.flow_control_id_edit.setMaximumWidth(100)
        layout.addWidget(self.flow_control_id_edit)

        self.set_filter_button = QPushButton("Set Filter")
        self.set_filter_button.clicked.connect(self._set_filter)
        self.set_filter_button.setEnabled(False)
        layout.addWidget(self.set_filter_button)

        self.clear_filters_button = QPushButton("Clear Filters")
        self.clear_filters_button.clicked.connect(self._clear_filters)
        self.clear_filters_button.setEnabled(False)
        layout.addWidget(self.clear_filters_button)

        layout.addStretch()

        return group

    def _create_message_group(self) -> QGroupBox:
        """Create the message I/O group box."""
        group = QGroupBox("Message I/O")
        layout = QGridLayout(group)

        # TX row
        layout.addWidget(QLabel("TX Data (hex):"), 0, 0)
        self.tx_data_edit = QLineEdit("22 F1 90")
        self.tx_data_edit.setFont(QFont("Consolas", 10))
        self.tx_data_edit.returnPressed.connect(self._send_message)
        layout.addWidget(self.tx_data_edit, 0, 1)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._send_message)
        self.send_button.setEnabled(False)
        layout.addWidget(self.send_button, 0, 2)

        self.clear_rx_button = QPushButton("Clear RX")
        self.clear_rx_button.clicked.connect(self._clear_rx_buffer)
        self.clear_rx_button.setEnabled(False)
        layout.addWidget(self.clear_rx_button, 0, 3)

        # Response row
        layout.addWidget(QLabel("Response:"), 1, 0)
        self.response_label = QLabel("--")
        self.response_label.setFont(QFont("Consolas", 10))
        self.response_label.setStyleSheet("color: blue;")
        layout.addWidget(self.response_label, 1, 1, 1, 3)

        return group

    def _create_config_group(self) -> QGroupBox:
        """Create the configuration options group box."""
        group = QGroupBox("Configuration")
        layout = QHBoxLayout(group)

        self.debug_checkbox = QCheckBox("Debug Mode")
        self.debug_checkbox.setChecked(j2534_config.debug_enabled)
        self.debug_checkbox.stateChanged.connect(self._toggle_debug_mode)
        layout.addWidget(self.debug_checkbox)

        self.exception_checkbox = QCheckBox("Exception Mode")
        self.exception_checkbox.setChecked(j2534_config.raise_exceptions)
        self.exception_checkbox.stateChanged.connect(self._toggle_exception_mode)
        layout.addWidget(self.exception_checkbox)

        self.version_button = QPushButton("Get Version Info")
        self.version_button.clicked.connect(self._show_version_info)
        self.version_button.setEnabled(False)
        layout.addWidget(self.version_button)

        layout.addStretch()

        return group

    def _create_log_group(self) -> QGroupBox:
        """Create the communication log group box."""
        group = QGroupBox("Communication Log")
        layout = QVBoxLayout(group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)

        self.clear_log_button = QPushButton("Clear Log")
        self.clear_log_button.clicked.connect(self._clear_log)
        layout.addWidget(self.clear_log_button, alignment=Qt.AlignCenter)

        return group

    # =========================================================================
    # Device Operations
    # =========================================================================

    def _refresh_device_list(self) -> None:
        """Refresh the list of available J2534 devices."""
        self.devices = get_list_j2534_devices()
        self.device_combo.clear()

        if self.devices:
            # devices is a list of [name, dll_path] pairs
            for device in self.devices:
                self.device_combo.addItem(device[0])
            self._log_message(f"Found {len(self.devices)} J2534 device(s)")
        else:
            self.device_combo.addItem("No devices found")
            self._log_message("No J2534 devices found in registry")

    def _open_device(self) -> None:
        """Open the selected J2534 device."""
        if not self.devices:
            QMessageBox.warning(self, "Error", "No devices available")
            return

        device_index = self.device_combo.currentIndex()
        self._log_message(f"Opening device {device_index}: {self.devices[device_index][0]}")
        self.status_label.setText("Opening device...")
        QApplication.processEvents()

        try:
            set_j2534_device_to_connect(device_index)
            result = pt_open()

            if result is False:
                self._log_message("Failed to open device")
                self.status_label.setText("Failed to open device")
                QMessageBox.warning(self, "Error", "Failed to open device")
                return

            self.device_identifier = result
            self.is_device_open = True
            self._log_message(f"Device opened successfully (ID: {self.device_identifier})")
            self.status_label.setText(f"Device open (ID: {self.device_identifier})")

            self._update_ui_state()
            self.voltage_timer.start(5000)
            self._update_voltage_display()

        except Exception as error:
            self._log_message(f"Error opening device: {error}")
            self.status_label.setText("Error")
            QMessageBox.critical(self, "Error", str(error))

    def _close_device(self) -> None:
        """Close the open device."""
        if not self.is_device_open:
            return

        if self.is_channel_connected:
            self._disconnect_channel()

        self.voltage_timer.stop()

        try:
            result = pt_close(self.device_identifier)
            self._log_message(f"Device closed (result: {result})")
        except Exception as error:
            self._log_message(f"Error closing device: {error}")

        self.device_identifier = None
        self.is_device_open = False
        self.voltage_label.setText("Voltage: --")
        self.status_label.setText("Device closed")

        self._update_ui_state()

    def _connect_channel(self) -> None:
        """Connect a protocol channel."""
        if not self.is_device_open:
            return

        protocol_index = self.protocol_combo.currentIndex()
        protocol_identifier = self.PROTOCOL_OPTIONS[protocol_index][1]

        baud_rate_index = self.baud_rate_combo.currentIndex()
        baud_rate_value = self.BAUD_RATE_OPTIONS[baud_rate_index][1]

        try:
            connect_flags = int(self.connect_flags_edit.text(), 0)
        except ValueError:
            connect_flags = 0

        self._log_message(
            f"Connecting channel: Protocol={protocol_identifier}, "
            f"Baud={baud_rate_value}, Flags={connect_flags}"
        )
        self.status_label.setText("Connecting channel...")
        QApplication.processEvents()

        try:
            result = pt_connect(
                self.device_identifier,
                protocol_identifier,
                connect_flags,
                baud_rate_value
            )

            if result is False:
                self._log_message("Failed to connect channel")
                self.status_label.setText("Failed to connect channel")
                QMessageBox.warning(self, "Error", "Failed to connect channel")
                return

            self.channel_identifier = result
            self.is_channel_connected = True
            self._log_message(f"Channel connected (ID: {self.channel_identifier})")
            self.status_label.setText(f"Channel connected (ID: {self.channel_identifier})")

            self._update_ui_state()

        except Exception as error:
            self._log_message(f"Error connecting channel: {error}")
            self.status_label.setText("Error")
            QMessageBox.critical(self, "Error", str(error))

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
        self.status_label.setText("Channel disconnected")

        self._update_ui_state()

    # =========================================================================
    # Filter Operations
    # =========================================================================

    def _set_filter(self) -> None:
        """Set a message filter."""
        if not self.is_channel_connected:
            return

        try:
            mask_identifier = int(self.mask_id_edit.text(), 0)
            pattern_identifier = int(self.pattern_id_edit.text(), 0)
            flow_control_identifier = int(self.flow_control_id_edit.text(), 0)
        except ValueError as error:
            QMessageBox.warning(self, "Invalid Input", f"Invalid filter value: {error}")
            return

        protocol_index = self.protocol_combo.currentIndex()
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
                QMessageBox.warning(self, "Error", "Failed to set filter")
                return

            self.filter_identifier = result
            self._log_message(f"Filter set (ID: {self.filter_identifier})")

        except Exception as error:
            self._log_message(f"Error setting filter: {error}")
            QMessageBox.critical(self, "Error", str(error))

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

        hex_text = self.tx_data_edit.text().strip()
        try:
            hex_text = hex_text.replace(" ", "").replace(",", "").replace("0x", "")
            data_bytes = [int(hex_text[i:i+2], 16) for i in range(0, len(hex_text), 2)]
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid hex bytes")
            return

        if not data_bytes:
            return

        protocol_index = self.protocol_combo.currentIndex()
        protocol_identifier = self.PROTOCOL_OPTIONS[protocol_index][1]

        transmit_message = PassThruMsgBuilder(protocol_identifier, TxFlags.ISO15765_FRAME_PAD)
        transmit_id = int(self.flow_control_id_edit.text(), 0)
        transmit_message.set_identifier_and_data(transmit_id, data_bytes)

        tx_hex = " ".join(f"{b:02X}" for b in data_bytes)
        self._log_message(f"TX [{transmit_id:03X}]: {tx_hex}")

        try:
            write_result = pt_write_message(self.channel_identifier, transmit_message, 1, 1000)

            if write_result != 0:
                self._log_message(f"Write failed (error: {write_result})")
                self.response_label.setText(f"Write error: {write_result}")
                return

            receive_message = PassThruMsgBuilder(protocol_identifier, 0)
            read_result = pt_read_message(self.channel_identifier, receive_message, 1, 1000)

            if read_result == 0:
                response_hex = receive_message.dump_output()
                formatted_response = " ".join(
                    response_hex[i:i+2] for i in range(0, len(response_hex), 2)
                )
                self.response_label.setText(formatted_response)
                self._log_message(f"RX: {formatted_response}")
            elif read_result == 0x10:
                self.response_label.setText("No response (timeout)")
                self._log_message("RX: No response (buffer empty)")
            else:
                self.response_label.setText(f"Read error: {read_result}")
                self._log_message(f"RX: Read error {read_result}")

        except Exception as error:
            self._log_message(f"Error: {error}")
            self.response_label.setText(f"Error: {error}")

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

    def _toggle_debug_mode(self, state: int) -> None:
        """Toggle debug mode on/off."""
        if state == Qt.Checked:
            j2534_config.enable_debug()
            self._log_message("Debug mode enabled")
        else:
            j2534_config.disable_debug()
            self._log_message("Debug mode disabled")

    def _toggle_exception_mode(self, state: int) -> None:
        """Toggle exception mode on/off."""
        if state == Qt.Checked:
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
                QMessageBox.information(
                    self,
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
                    self.voltage_label.setText(f"Voltage: {voltage:.2f}V")
                else:
                    self.voltage_label.setText("Voltage: --")
            except Exception:
                self.voltage_label.setText("Voltage: Error")

    def _update_ui_state(self) -> None:
        """Update UI element states based on connection status."""
        self.open_device_button.setEnabled(not self.is_device_open)
        self.close_device_button.setEnabled(self.is_device_open)

        self.connect_channel_button.setEnabled(self.is_device_open and not self.is_channel_connected)
        self.disconnect_channel_button.setEnabled(self.is_channel_connected)

        self.set_filter_button.setEnabled(self.is_channel_connected)
        self.clear_filters_button.setEnabled(self.is_channel_connected)

        self.send_button.setEnabled(self.is_channel_connected)
        self.clear_rx_button.setEnabled(self.is_channel_connected)

        self.version_button.setEnabled(self.is_device_open)

        self.device_combo.setEnabled(not self.is_device_open)

    def _log_message(self, message: str) -> None:
        """Add a timestamped message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_text.append(f"[{timestamp}] {message}")

    def _clear_log(self) -> None:
        """Clear the log text widget."""
        self.log_text.clear()

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        if self.is_channel_connected:
            self._disconnect_channel()
        if self.is_device_open:
            self._close_device()
        event.accept()


def main() -> None:
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = J2534ApiDemo()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
