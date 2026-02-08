"""
CustomTkinter J2534 Registry Viewer
===================================

A modern-themed GUI application for viewing J2534 devices registered in Windows.
Uses CustomTkinter for a polished, contemporary look.

Features:
    - Modern dark/light theme support
    - View all registered J2534 devices
    - See detailed device information
    - Check protocol support
    - Validate DLL file existence
    - Export device list to JSON/CSV
    - Copy device info to clipboard

Requirements:
    pip install customtkinter

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

import customtkinter as ctk

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

# Configure CustomTkinter appearance
ctk.set_appearance_mode("system")  # "system", "dark", or "light"
ctk.set_default_color_theme("blue")


class J2534RegistryViewer(ctk.CTk):
    """Main application window for viewing J2534 registry devices."""

    def __init__(self):
        """Initialize the registry viewer application."""
        super().__init__()

        self.title("J2534 Registry Viewer - CustomTkinter")
        self.geometry("1000x750")
        self.minsize(900, 650)

        # Initialize scanner and device list
        self.scanner = J2534RegistryScanner()
        self.devices: List[J2534DeviceInfo] = []
        self.selected_device: Optional[J2534DeviceInfo] = None

        # Build the user interface
        self._create_widgets()

        # Load devices on startup
        self._refresh_devices()

    def _create_widgets(self):
        """Create all UI widgets."""
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header frame
        self._create_header()

        # Main content area
        self._create_main_content()

        # Status bar
        self._create_status_bar()

    def _create_header(self):
        """Create the header section."""
        header_frame = ctk.CTkFrame(self, corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(1, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="J2534 Registry Device Viewer",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        # Registry path info
        self.registry_path_label = ctk.CTkLabel(
            header_frame,
            text=f"Registry: {self.scanner._registry_path}",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="gray"
        )
        self.registry_path_label.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        # Right side buttons
        buttons_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        buttons_frame.grid(row=0, column=2, rowspan=2, padx=15, pady=10, sticky="e")

        # Theme toggle
        self.theme_switch = ctk.CTkSwitch(
            buttons_frame,
            text="Dark Mode",
            command=self._toggle_theme,
            onvalue="dark",
            offvalue="light"
        )
        self.theme_switch.grid(row=0, column=0, padx=10)
        if ctk.get_appearance_mode() == "Dark":
            self.theme_switch.select()

        # Refresh button
        refresh_btn = ctk.CTkButton(
            buttons_frame,
            text="Refresh",
            command=self._refresh_devices,
            width=100
        )
        refresh_btn.grid(row=0, column=1, padx=5)

    def _create_main_content(self):
        """Create the main content area with device list and details."""
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Left panel: Device list
        self._create_device_list_panel(main_frame)

        # Right panel: Device details
        self._create_details_panel(main_frame)

    def _create_device_list_panel(self, parent):
        """Create the device list panel."""
        left_frame = ctk.CTkFrame(parent, width=300)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        left_frame.grid_rowconfigure(2, weight=1)
        left_frame.grid_propagate(False)

        # Header
        header = ctk.CTkLabel(
            left_frame,
            text="Devices",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        header.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        # Device count
        self.device_count_label = ctk.CTkLabel(
            left_frame,
            text="Found: 0 devices",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.device_count_label.grid(row=0, column=1, padx=10, pady=(10, 5), sticky="e")

        # Search box
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self._on_search_changed)

        search_entry = ctk.CTkEntry(
            left_frame,
            placeholder_text="Search devices...",
            textvariable=self.search_var,
            width=280
        )
        search_entry.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        # Device listbox (using CTkScrollableFrame with buttons)
        self.device_list_frame = ctk.CTkScrollableFrame(left_frame, width=260)
        self.device_list_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=(5, 10), sticky="nsew")

        self.device_buttons: List[ctk.CTkButton] = []

    def _create_details_panel(self, parent):
        """Create the device details panel."""
        right_frame = ctk.CTkScrollableFrame(parent)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)

        # Header
        header = ctk.CTkLabel(
            right_frame,
            text="Device Details",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        header.pack(anchor="w", padx=10, pady=(10, 15))

        # Basic info section
        basic_frame = ctk.CTkFrame(right_frame)
        basic_frame.pack(fill="x", padx=10, pady=5)

        basic_header = ctk.CTkLabel(
            basic_frame,
            text="Basic Information",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        basic_header.pack(anchor="w", padx=10, pady=(10, 5))

        self.detail_labels = {}

        fields = [("name", "Name"), ("vendor", "Vendor"), ("device_id", "Device ID")]
        for field_name, label_text in fields:
            row = ctk.CTkFrame(basic_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)

            ctk.CTkLabel(row, text=f"{label_text}:", width=120, anchor="e").pack(side="left")
            label = ctk.CTkLabel(row, text="--", font=ctk.CTkFont(family="Consolas", size=12))
            label.pack(side="left", padx=(10, 0))
            self.detail_labels[field_name] = label

        # Paths section
        paths_frame = ctk.CTkFrame(right_frame)
        paths_frame.pack(fill="x", padx=10, pady=10)

        paths_header = ctk.CTkLabel(
            paths_frame,
            text="File Paths",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        paths_header.pack(anchor="w", padx=10, pady=(10, 5))

        # DLL Path
        dll_row = ctk.CTkFrame(paths_frame, fg_color="transparent")
        dll_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(dll_row, text="Function Library:", width=120, anchor="e").pack(side="left")
        self.detail_labels["dll_path"] = ctk.CTkLabel(
            dll_row, text="--", font=ctk.CTkFont(family="Consolas", size=11), wraplength=400
        )
        self.detail_labels["dll_path"].pack(side="left", padx=(10, 0))

        # DLL Status
        status_row = ctk.CTkFrame(paths_frame, fg_color="transparent")
        status_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(status_row, text="DLL Status:", width=120, anchor="e").pack(side="left")
        self.detail_labels["dll_status"] = ctk.CTkLabel(
            status_row, text="--", font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.detail_labels["dll_status"].pack(side="left", padx=(10, 0))

        self.open_folder_btn = ctk.CTkButton(
            status_row, text="Open Folder", command=self._open_dll_folder, width=100, state="disabled"
        )
        self.open_folder_btn.pack(side="left", padx=(10, 0))

        # Config App Path
        config_row = ctk.CTkFrame(paths_frame, fg_color="transparent")
        config_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(config_row, text="Config App:", width=120, anchor="e").pack(side="left")
        self.detail_labels["config_app"] = ctk.CTkLabel(
            config_row, text="--", font=ctk.CTkFont(family="Consolas", size=11), wraplength=400
        )
        self.detail_labels["config_app"].pack(side="left", padx=(10, 0))

        # Registry Key Path
        reg_row = ctk.CTkFrame(paths_frame, fg_color="transparent")
        reg_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(reg_row, text="Registry Key:", width=120, anchor="e").pack(side="left")
        self.detail_labels["registry_key"] = ctk.CTkLabel(
            reg_row, text="--", font=ctk.CTkFont(family="Consolas", size=11), wraplength=400
        )
        self.detail_labels["registry_key"].pack(side="left", padx=(10, 0))

        # Protocols section
        protocols_frame = ctk.CTkFrame(right_frame)
        protocols_frame.pack(fill="x", padx=10, pady=10)

        protocols_header = ctk.CTkLabel(
            protocols_frame,
            text="Supported Protocols",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        protocols_header.pack(anchor="w", padx=10, pady=(10, 5))

        protocols_grid = ctk.CTkFrame(protocols_frame, fg_color="transparent")
        protocols_grid.pack(fill="x", padx=10, pady=5)

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

            var = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(
                protocols_grid,
                text=label,
                variable=var,
                state="disabled",
                width=150
            )
            cb.grid(row=row, column=col, padx=10, pady=5, sticky="w")
            self.protocol_checkboxes[attr] = (cb, var)

        # Action buttons
        actions_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        actions_frame.pack(fill="x", padx=10, pady=15)

        ctk.CTkButton(
            actions_frame, text="Copy Info", command=self._copy_to_clipboard, width=120
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            actions_frame, text="Export JSON", command=self._export_json, width=120
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            actions_frame, text="Export CSV", command=self._export_csv, width=120
        ).pack(side="left", padx=5)

    def _create_status_bar(self):
        """Create the status bar."""
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.status_label.grid(row=2, column=0, sticky="ew", padx=15, pady=5)

    def _toggle_theme(self):
        """Toggle between dark and light theme."""
        if self.theme_switch.get() == "dark":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def _refresh_devices(self):
        """Refresh the device list from the registry."""
        self.status_label.configure(text="Scanning registry...")
        self.update()

        try:
            self.scanner.refresh_cache()
            self.devices = self.scanner.get_all_devices()
            self._update_device_list()
            self.device_count_label.configure(text=f"Found: {len(self.devices)} devices")
            self.status_label.configure(
                text=f"Found {len(self.devices)} device(s) - Last refresh: {datetime.now().strftime('%H:%M:%S')}"
            )
        except Exception as e:
            self._show_error("Error", f"Failed to scan registry:\n{e}")
            self.status_label.configure(text="Error scanning registry")

    def _update_device_list(self):
        """Update the device list display."""
        # Clear existing buttons
        for btn in self.device_buttons:
            btn.destroy()
        self.device_buttons.clear()

        search_text = self.search_var.get().lower()

        for i, device in enumerate(self.devices):
            if search_text and search_text not in device.name.lower() and search_text not in device.vendor.lower():
                continue

            display_text = device.name
            if device.vendor:
                display_text += f"\n{device.vendor}"

            btn = ctk.CTkButton(
                self.device_list_frame,
                text=display_text,
                anchor="w",
                command=lambda d=device: self._select_device(d),
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                height=50
            )
            btn.pack(fill="x", pady=2)
            self.device_buttons.append(btn)

    def _on_search_changed(self, *args):
        """Handle search text changes."""
        self._update_device_list()

    def _select_device(self, device: J2534DeviceInfo):
        """Select and display a device."""
        self.selected_device = device
        self._display_device_details(device)

        # Update button states to show selection
        for btn in self.device_buttons:
            if device.name in btn.cget("text"):
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")

    def _display_device_details(self, device: J2534DeviceInfo):
        """Display the details of the selected device."""
        # Basic info
        self.detail_labels["name"].configure(text=device.name)
        self.detail_labels["vendor"].configure(text=device.vendor or "--")
        self.detail_labels["device_id"].configure(text=str(device.device_id))

        # Paths
        self.detail_labels["dll_path"].configure(text=device.function_library_path or "--")
        self.detail_labels["config_app"].configure(text=device.config_application_path or "--")
        self.detail_labels["registry_key"].configure(text=device.registry_key_path or "--")

        # DLL status
        if device.function_library_path:
            if self.scanner.verify_dll_exists(device):
                try:
                    stat = os.stat(device.function_library_path)
                    size_kb = stat.st_size / 1024
                    mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    self.detail_labels["dll_status"].configure(
                        text=f"EXISTS ({size_kb:.1f} KB, modified {mod_time})",
                        text_color="green"
                    )
                except Exception:
                    self.detail_labels["dll_status"].configure(text="EXISTS", text_color="green")
                self.open_folder_btn.configure(state="normal")
            else:
                self.detail_labels["dll_status"].configure(text="NOT FOUND", text_color="red")
                self.open_folder_btn.configure(state="disabled")
        else:
            self.detail_labels["dll_status"].configure(text="No path specified", text_color="gray")
            self.open_folder_btn.configure(state="disabled")

        # Protocol support
        for attr, (cb, var) in self.protocol_checkboxes.items():
            supported = getattr(device, attr, False)
            var.set(supported)

    def _open_dll_folder(self):
        """Open the folder containing the DLL file."""
        if self.selected_device and self.selected_device.function_library_path:
            folder = os.path.dirname(self.selected_device.function_library_path)
            if os.path.exists(folder):
                subprocess.run(["explorer", folder])
            else:
                self._show_warning("Warning", f"Folder does not exist:\n{folder}")

    def _copy_to_clipboard(self):
        """Copy selected device information to clipboard."""
        if not self.selected_device:
            self._show_info("Info", "No device selected")
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
        self.clipboard_clear()
        self.clipboard_append(info_text)
        self.status_label.configure(text="Device info copied to clipboard")

    def _export_json(self):
        """Export all devices to JSON."""
        if not self.devices:
            self._show_info("Info", "No devices to export")
            return

        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export to JSON"
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

            self.status_label.configure(text=f"Exported {len(self.devices)} device(s) to JSON")
            self._show_info("Success", f"Exported {len(self.devices)} device(s) to:\n{filepath}")
        except Exception as e:
            self._show_error("Error", f"Failed to export:\n{e}")

    def _export_csv(self):
        """Export all devices to CSV."""
        if not self.devices:
            self._show_info("Info", "No devices to export")
            return

        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export to CSV"
        )

        if not filepath:
            return

        try:
            import csv
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Vendor", "Device ID", "Function Library", "Protocols"])

                for device in self.devices:
                    writer.writerow([
                        device.name,
                        device.vendor,
                        device.device_id,
                        device.function_library_path,
                        ", ".join(device.supported_protocols),
                    ])

            self.status_label.configure(text=f"Exported {len(self.devices)} device(s) to CSV")
            self._show_info("Success", f"Exported {len(self.devices)} device(s) to:\n{filepath}")
        except Exception as e:
            self._show_error("Error", f"Failed to export:\n{e}")

    def _show_info(self, title: str, message: str):
        """Show an info dialog."""
        from tkinter import messagebox
        messagebox.showinfo(title, message)

    def _show_warning(self, title: str, message: str):
        """Show a warning dialog."""
        from tkinter import messagebox
        messagebox.showwarning(title, message)

    def _show_error(self, title: str, message: str):
        """Show an error dialog."""
        from tkinter import messagebox
        messagebox.showerror(title, message)


def main():
    """Application entry point."""
    app = J2534RegistryViewer()
    app.mainloop()


if __name__ == "__main__":
    main()
