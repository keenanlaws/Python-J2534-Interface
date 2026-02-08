"""
PyQt5 J2534 Registry Viewer
===========================

A full-featured GUI application for viewing J2534 devices registered in Windows.
Uses PyQt5 for professional-grade UI with table view, sorting, and more.

Features:
    - View all registered J2534 devices in a sortable table
    - See detailed device information
    - Check protocol support
    - Validate DLL file existence
    - Export device list to JSON/CSV
    - Copy device info to clipboard
    - Filter by protocol support

Requirements:
    pip install PyQt5

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

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QLabel,
    QPushButton, QLineEdit, QCheckBox, QSplitter, QFrame, QStatusBar,
    QFileDialog, QMessageBox, QGridLayout, QComboBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor

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


class J2534RegistryViewer(QMainWindow):
    """Main window for J2534 Registry Viewer application."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        self.setWindowTitle("J2534 Registry Viewer - PyQt5")
        self.setGeometry(100, 100, 1100, 750)
        self.setMinimumSize(900, 600)

        # Initialize scanner and data
        self.scanner = J2534RegistryScanner()
        self.devices: List[J2534DeviceInfo] = []
        self.selected_device: Optional[J2534DeviceInfo] = None

        # Build UI
        self._create_central_widget()
        self._create_status_bar()

        # Load initial data
        self._refresh_devices()

    def _create_central_widget(self):
        """Create the main content area."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("J2534 Registry Device Viewer")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self._refresh_devices)
        header_layout.addWidget(refresh_btn)

        main_layout.addLayout(header_layout)

        # Registry path info
        self.registry_path_label = QLabel(f"Registry Path: {self.scanner._registry_path}")
        self.registry_path_label.setStyleSheet("color: gray; font-family: Consolas;")
        main_layout.addWidget(self.registry_path_label)

        # Create splitter for device list and details
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, 1)

        # Left panel: Device table
        left_widget = self._create_device_table_panel()
        splitter.addWidget(left_widget)

        # Right panel: Device details
        right_widget = self._create_details_panel()
        splitter.addWidget(right_widget)

        # Set splitter sizes
        splitter.setSizes([400, 600])

    def _create_device_table_panel(self) -> QWidget:
        """Create the device table panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with device count
        header_layout = QHBoxLayout()

        devices_label = QLabel("Devices")
        devices_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header_layout.addWidget(devices_label)

        self.device_count_label = QLabel("Found: 0 devices")
        self.device_count_label.setStyleSheet("color: gray;")
        header_layout.addWidget(self.device_count_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Search and filter bar
        filter_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search devices...")
        self.search_input.textChanged.connect(self._filter_devices)
        filter_layout.addWidget(self.search_input)

        # Protocol filter
        self.protocol_filter = QComboBox()
        self.protocol_filter.addItems([
            "All Protocols",
            "CAN/ISO15765",
            "J1850VPW",
            "J1850PWM",
            "ISO9141",
            "ISO14230",
        ])
        self.protocol_filter.setFixedWidth(120)
        self.protocol_filter.currentTextChanged.connect(self._filter_devices)
        filter_layout.addWidget(self.protocol_filter)

        layout.addLayout(filter_layout)

        # Device table
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(4)
        self.device_table.setHorizontalHeaderLabels(["Name", "Vendor", "Protocols", "DLL Valid"])
        self.device_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.device_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.device_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.device_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.device_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.device_table.setSelectionMode(QTableWidget.SingleSelection)
        self.device_table.setSortingEnabled(True)
        self.device_table.setAlternatingRowColors(True)
        self.device_table.selectionModel().selectionChanged.connect(self._on_device_selected)
        layout.addWidget(self.device_table)

        return widget

    def _create_details_panel(self) -> QWidget:
        """Create the device details panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 0, 0, 0)

        # Header
        details_label = QLabel("Device Details")
        details_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(details_label)

        # Basic info group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QGridLayout(basic_group)

        self.detail_labels = {}

        fields = [
            ("name", "Name:", 0),
            ("vendor", "Vendor:", 1),
            ("device_id", "Device ID:", 2),
        ]

        for field_name, label_text, row in fields:
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            basic_layout.addWidget(label, row, 0)

            value_label = QLabel("--")
            value_label.setFont(QFont("Consolas", 10))
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            basic_layout.addWidget(value_label, row, 1)
            self.detail_labels[field_name] = value_label

        layout.addWidget(basic_group)

        # Paths group
        paths_group = QGroupBox("File Paths")
        paths_layout = QGridLayout(paths_group)

        # DLL Path
        paths_layout.addWidget(QLabel("Function Library:"), 0, 0, Qt.AlignRight | Qt.AlignTop)
        self.detail_labels["dll_path"] = QLabel("--")
        self.detail_labels["dll_path"].setFont(QFont("Consolas", 9))
        self.detail_labels["dll_path"].setWordWrap(True)
        self.detail_labels["dll_path"].setTextInteractionFlags(Qt.TextSelectableByMouse)
        paths_layout.addWidget(self.detail_labels["dll_path"], 0, 1)

        # DLL Status
        paths_layout.addWidget(QLabel("DLL Status:"), 1, 0, Qt.AlignRight)
        dll_status_layout = QHBoxLayout()
        self.detail_labels["dll_status"] = QLabel("--")
        self.detail_labels["dll_status"].setFont(QFont("Consolas", 9))
        dll_status_layout.addWidget(self.detail_labels["dll_status"])

        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.setFixedWidth(100)
        self.open_folder_btn.setEnabled(False)
        self.open_folder_btn.clicked.connect(self._open_dll_folder)
        dll_status_layout.addWidget(self.open_folder_btn)
        dll_status_layout.addStretch()
        paths_layout.addLayout(dll_status_layout, 1, 1)

        # Config App
        paths_layout.addWidget(QLabel("Config App:"), 2, 0, Qt.AlignRight | Qt.AlignTop)
        self.detail_labels["config_app"] = QLabel("--")
        self.detail_labels["config_app"].setFont(QFont("Consolas", 9))
        self.detail_labels["config_app"].setWordWrap(True)
        self.detail_labels["config_app"].setTextInteractionFlags(Qt.TextSelectableByMouse)
        paths_layout.addWidget(self.detail_labels["config_app"], 2, 1)

        # Registry Key
        paths_layout.addWidget(QLabel("Registry Key:"), 3, 0, Qt.AlignRight | Qt.AlignTop)
        self.detail_labels["registry_key"] = QLabel("--")
        self.detail_labels["registry_key"].setFont(QFont("Consolas", 9))
        self.detail_labels["registry_key"].setWordWrap(True)
        self.detail_labels["registry_key"].setTextInteractionFlags(Qt.TextSelectableByMouse)
        paths_layout.addWidget(self.detail_labels["registry_key"], 3, 1)

        paths_layout.setColumnStretch(1, 1)
        layout.addWidget(paths_group)

        # Protocols group
        protocols_group = QGroupBox("Supported Protocols")
        protocols_layout = QGridLayout(protocols_group)

        self.protocol_checkboxes = {}
        protocols = [
            ("CAN/ISO15765", "can_iso15765"),
            ("J1850 VPW", "j1850vpw"),
            ("J1850 PWM", "j1850pwm"),
            ("ISO 9141", "iso9141"),
            ("ISO 14230", "iso14230"),
            ("SCI_A Engine", "sci_a_engine"),
            ("SCI_A Trans", "sci_a_trans"),
            ("SCI_B Engine", "sci_b_engine"),
            ("SCI_B Trans", "sci_b_trans"),
        ]

        for i, (label, attr) in enumerate(protocols):
            row = i // 3
            col = i % 3

            cb = QCheckBox(label)
            cb.setEnabled(False)
            protocols_layout.addWidget(cb, row, col)
            self.protocol_checkboxes[attr] = cb

        layout.addWidget(protocols_group)

        # Action buttons
        buttons_layout = QHBoxLayout()

        copy_btn = QPushButton("Copy Info")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        buttons_layout.addWidget(copy_btn)

        export_json_btn = QPushButton("Export JSON")
        export_json_btn.clicked.connect(self._export_json)
        buttons_layout.addWidget(export_json_btn)

        export_csv_btn = QPushButton("Export CSV")
        export_csv_btn.clicked.connect(self._export_csv)
        buttons_layout.addWidget(export_csv_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        layout.addStretch()
        return widget

    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _refresh_devices(self):
        """Refresh the device list from the registry."""
        self.status_bar.showMessage("Scanning registry...")
        QApplication.processEvents()

        try:
            self.scanner.refresh_cache()
            self.devices = self.scanner.get_all_devices()
            self._update_device_table()
            self.device_count_label.setText(f"Found: {len(self.devices)} devices")
            self.status_bar.showMessage(
                f"Found {len(self.devices)} device(s) - Last refresh: {datetime.now().strftime('%H:%M:%S')}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to scan registry:\n{e}")
            self.status_bar.showMessage("Error scanning registry")

    def _update_device_table(self):
        """Update the device table with current devices."""
        self._filter_devices()

    def _filter_devices(self):
        """Filter and display devices based on search and protocol filter."""
        search_text = self.search_input.text().lower()
        protocol_filter = self.protocol_filter.currentText()

        # Protocol attribute mapping
        protocol_attrs = {
            "CAN/ISO15765": "can_iso15765",
            "J1850VPW": "j1850vpw",
            "J1850PWM": "j1850pwm",
            "ISO9141": "iso9141",
            "ISO14230": "iso14230",
        }

        filtered = []
        for device in self.devices:
            # Search filter
            if search_text and search_text not in device.name.lower() and search_text not in device.vendor.lower():
                continue

            # Protocol filter
            if protocol_filter != "All Protocols":
                attr = protocol_attrs.get(protocol_filter)
                if attr and not getattr(device, attr, False):
                    continue

            filtered.append(device)

        # Update table
        self.device_table.setRowCount(len(filtered))
        for row, device in enumerate(filtered):
            # Name
            name_item = QTableWidgetItem(device.name)
            name_item.setData(Qt.UserRole, device)  # Store device reference
            self.device_table.setItem(row, 0, name_item)

            # Vendor
            self.device_table.setItem(row, 1, QTableWidgetItem(device.vendor or "--"))

            # Protocols count
            proto_count = len(device.supported_protocols)
            self.device_table.setItem(row, 2, QTableWidgetItem(str(proto_count)))

            # DLL Valid
            dll_valid = self.scanner.verify_dll_exists(device)
            dll_item = QTableWidgetItem("Yes" if dll_valid else "No")
            dll_item.setForeground(QColor("green") if dll_valid else QColor("red"))
            self.device_table.setItem(row, 3, dll_item)

    def _on_device_selected(self):
        """Handle device selection in the table."""
        selected_rows = self.device_table.selectedItems()
        if not selected_rows:
            return

        # Get the device from the first column's user data
        row = selected_rows[0].row()
        item = self.device_table.item(row, 0)
        if item:
            device = item.data(Qt.UserRole)
            if device:
                self.selected_device = device
                self._display_device_details(device)

    def _display_device_details(self, device: J2534DeviceInfo):
        """Display the details of the selected device."""
        # Basic info
        self.detail_labels["name"].setText(device.name)
        self.detail_labels["vendor"].setText(device.vendor or "--")
        self.detail_labels["device_id"].setText(str(device.device_id))

        # Paths
        self.detail_labels["dll_path"].setText(device.function_library_path or "--")
        self.detail_labels["config_app"].setText(device.config_application_path or "--")
        self.detail_labels["registry_key"].setText(device.registry_key_path or "--")

        # DLL status
        if device.function_library_path:
            if self.scanner.verify_dll_exists(device):
                try:
                    stat = os.stat(device.function_library_path)
                    size_kb = stat.st_size / 1024
                    mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    self.detail_labels["dll_status"].setText(f"EXISTS ({size_kb:.1f} KB, modified {mod_time})")
                    self.detail_labels["dll_status"].setStyleSheet("color: green;")
                except Exception:
                    self.detail_labels["dll_status"].setText("EXISTS")
                    self.detail_labels["dll_status"].setStyleSheet("color: green;")
                self.open_folder_btn.setEnabled(True)
            else:
                self.detail_labels["dll_status"].setText("NOT FOUND")
                self.detail_labels["dll_status"].setStyleSheet("color: red;")
                self.open_folder_btn.setEnabled(False)
        else:
            self.detail_labels["dll_status"].setText("No path specified")
            self.detail_labels["dll_status"].setStyleSheet("color: gray;")
            self.open_folder_btn.setEnabled(False)

        # Protocol support
        for attr, cb in self.protocol_checkboxes.items():
            cb.setChecked(getattr(device, attr, False))

    def _open_dll_folder(self):
        """Open the folder containing the DLL file."""
        if self.selected_device and self.selected_device.function_library_path:
            folder = os.path.dirname(self.selected_device.function_library_path)
            if os.path.exists(folder):
                subprocess.run(["explorer", folder])
            else:
                QMessageBox.warning(self, "Warning", f"Folder does not exist:\n{folder}")

    def _copy_to_clipboard(self):
        """Copy selected device information to clipboard."""
        if not self.selected_device:
            QMessageBox.information(self, "Info", "No device selected")
            return

        device = self.selected_device
        info_text = f"""J2534 Device Information
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
        clipboard = QApplication.clipboard()
        clipboard.setText(info_text)
        self.status_bar.showMessage("Device info copied to clipboard")

    def _export_json(self):
        """Export all devices to JSON file."""
        if not self.devices:
            QMessageBox.information(self, "Info", "No devices to export")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export to JSON", "", "JSON Files (*.json);;All Files (*)"
        )

        if not filepath:
            return

        try:
            export_data = []
            for device in self.devices:
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

            self.status_bar.showMessage(f"Exported {len(self.devices)} device(s) to JSON")
            QMessageBox.information(self, "Success", f"Exported {len(self.devices)} device(s) to:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export:\n{e}")

    def _export_csv(self):
        """Export all devices to CSV file."""
        if not self.devices:
            QMessageBox.information(self, "Info", "No devices to export")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export to CSV", "", "CSV Files (*.csv);;All Files (*)"
        )

        if not filepath:
            return

        try:
            import csv
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Vendor", "Device ID", "Function Library", "Protocols", "DLL Valid"])

                for device in self.devices:
                    writer.writerow([
                        device.name,
                        device.vendor,
                        device.device_id,
                        device.function_library_path,
                        ", ".join(device.supported_protocols),
                        "Yes" if self.scanner.verify_dll_exists(device) else "No",
                    ])

            self.status_bar.showMessage(f"Exported {len(self.devices)} device(s) to CSV")
            QMessageBox.information(self, "Success", f"Exported {len(self.devices)} device(s) to:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export:\n{e}")


def main():
    """Application entry point."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    window = J2534RegistryViewer()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
