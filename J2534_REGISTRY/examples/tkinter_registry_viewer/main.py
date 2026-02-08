"""
Tkinter J2534 Registry Viewer
=============================

A simple GUI application for viewing J2534 devices registered in Windows.
Uses Python's built-in Tkinter library - no external dependencies required!

Features:
    - View all registered J2534 devices
    - See detailed device information
    - Check protocol support
    - Validate DLL file existence
    - Export device list to JSON/CSV
    - Copy device info to clipboard

Requirements:
    None (Tkinter is included with Python)

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
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

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


class J2534RegistryViewer:
    """Main application window for viewing J2534 registry devices."""

    def __init__(self, root: tk.Tk):
        """
        Initialize the registry viewer application.

        Args:
            root: The Tkinter root window
        """
        self.root = root
        self.root.title("J2534 Registry Viewer - Tkinter")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Initialize scanner and device list
        self.scanner = J2534RegistryScanner()
        self.devices: list[J2534DeviceInfo] = []
        self.selected_device: J2534DeviceInfo | None = None

        # Build the user interface
        self._create_menu()
        self._create_widgets()
        self._create_status_bar()

        # Load devices on startup
        self._refresh_devices()

    def _create_menu(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh", command=self._refresh_devices, accelerator="F5")
        file_menu.add_separator()
        file_menu.add_command(label="Export to JSON...", command=self._export_json)
        file_menu.add_command(label="Export to CSV...", command=self._export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Copy Device Info", command=self._copy_to_clipboard, accelerator="Ctrl+C")

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

        # Bind keyboard shortcuts
        self.root.bind("<F5>", lambda e: self._refresh_devices())
        self.root.bind("<Control-c>", lambda e: self._copy_to_clipboard())

    def _create_widgets(self):
        """Create all UI widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header section
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(
            header_frame,
            text="J2534 Registry Device Viewer",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)

        refresh_button = ttk.Button(
            header_frame,
            text="Refresh",
            command=self._refresh_devices
        )
        refresh_button.pack(side=tk.RIGHT)

        # Registry path info
        self.registry_path_label = ttk.Label(
            main_frame,
            text=f"Registry Path: {self.scanner._registry_path}",
            font=("Consolas", 9)
        )
        self.registry_path_label.pack(fill=tk.X, pady=(0, 10))

        # Create paned window for resizable sections
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Left panel: Device list
        left_frame = ttk.LabelFrame(paned_window, text="Devices", padding="5")
        paned_window.add(left_frame, weight=1)

        # Device count label
        self.device_count_label = ttk.Label(left_frame, text="Found: 0 devices")
        self.device_count_label.pack(fill=tk.X)

        # Search box
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=5)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_changed)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Device listbox with scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.device_listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 10),
            yscrollcommand=scrollbar.set,
            exportselection=False
        )
        self.device_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.device_listbox.yview)

        self.device_listbox.bind("<<ListboxSelect>>", self._on_device_selected)

        # Right panel: Device details
        right_frame = ttk.LabelFrame(paned_window, text="Device Details", padding="5")
        paned_window.add(right_frame, weight=2)

        # Create scrollable frame for details
        details_canvas = tk.Canvas(right_frame, highlightthickness=0)
        details_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=details_canvas.yview)
        self.details_frame = ttk.Frame(details_canvas)

        self.details_frame.bind(
            "<Configure>",
            lambda e: details_canvas.configure(scrollregion=details_canvas.bbox("all"))
        )

        details_canvas.create_window((0, 0), window=self.details_frame, anchor="nw")
        details_canvas.configure(yscrollcommand=details_scrollbar.set)

        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        details_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create detail fields
        self._create_detail_fields()

    def _create_detail_fields(self):
        """Create the device detail display fields."""
        # Basic info section
        basic_frame = ttk.LabelFrame(self.details_frame, text="Basic Information", padding="10")
        basic_frame.pack(fill=tk.X, pady=(0, 10))

        self.detail_vars = {}

        fields = [
            ("name", "Name:"),
            ("vendor", "Vendor:"),
            ("device_id", "Device ID:"),
        ]

        for field_name, label_text in fields:
            row_frame = ttk.Frame(basic_frame)
            row_frame.pack(fill=tk.X, pady=2)

            ttk.Label(row_frame, text=label_text, width=15, anchor="e").pack(side=tk.LEFT)
            var = tk.StringVar(value="--")
            self.detail_vars[field_name] = var
            ttk.Label(row_frame, textvariable=var, font=("Consolas", 10)).pack(side=tk.LEFT, padx=(10, 0))

        # Paths section
        paths_frame = ttk.LabelFrame(self.details_frame, text="File Paths", padding="10")
        paths_frame.pack(fill=tk.X, pady=(0, 10))

        # Function Library (DLL) path
        dll_frame = ttk.Frame(paths_frame)
        dll_frame.pack(fill=tk.X, pady=2)

        ttk.Label(dll_frame, text="Function Library:", width=15, anchor="e").pack(side=tk.LEFT)
        self.detail_vars["dll_path"] = tk.StringVar(value="--")
        ttk.Label(dll_frame, textvariable=self.detail_vars["dll_path"], font=("Consolas", 9)).pack(side=tk.LEFT, padx=(10, 0))

        # DLL status
        dll_status_frame = ttk.Frame(paths_frame)
        dll_status_frame.pack(fill=tk.X, pady=2)

        ttk.Label(dll_status_frame, text="DLL Status:", width=15, anchor="e").pack(side=tk.LEFT)
        self.detail_vars["dll_status"] = tk.StringVar(value="--")
        self.dll_status_label = ttk.Label(dll_status_frame, textvariable=self.detail_vars["dll_status"], font=("Consolas", 9))
        self.dll_status_label.pack(side=tk.LEFT, padx=(10, 0))

        self.open_folder_button = ttk.Button(dll_status_frame, text="Open Folder", command=self._open_dll_folder, state=tk.DISABLED)
        self.open_folder_button.pack(side=tk.LEFT, padx=(10, 0))

        # Config application path
        config_frame = ttk.Frame(paths_frame)
        config_frame.pack(fill=tk.X, pady=2)

        ttk.Label(config_frame, text="Config App:", width=15, anchor="e").pack(side=tk.LEFT)
        self.detail_vars["config_app"] = tk.StringVar(value="--")
        ttk.Label(config_frame, textvariable=self.detail_vars["config_app"], font=("Consolas", 9)).pack(side=tk.LEFT, padx=(10, 0))

        # Registry key path
        reg_frame = ttk.Frame(paths_frame)
        reg_frame.pack(fill=tk.X, pady=2)

        ttk.Label(reg_frame, text="Registry Key:", width=15, anchor="e").pack(side=tk.LEFT)
        self.detail_vars["registry_key"] = tk.StringVar(value="--")
        ttk.Label(reg_frame, textvariable=self.detail_vars["registry_key"], font=("Consolas", 9), wraplength=400).pack(side=tk.LEFT, padx=(10, 0))

        # Protocols section
        protocols_frame = ttk.LabelFrame(self.details_frame, text="Supported Protocols", padding="10")
        protocols_frame.pack(fill=tk.X, pady=(0, 10))

        # Create protocol checkboxes in a grid
        self.protocol_vars = {}
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

            var = tk.BooleanVar(value=False)
            self.protocol_vars[attr] = var

            cb = ttk.Checkbutton(
                protocols_frame,
                text=label,
                variable=var,
                state=tk.DISABLED
            )
            cb.grid(row=row, column=col, sticky="w", padx=10, pady=2)

        # Action buttons
        buttons_frame = ttk.Frame(self.details_frame)
        buttons_frame.pack(fill=tk.X, pady=10)

        ttk.Button(buttons_frame, text="Copy Info", command=self._copy_to_clipboard).pack(side=tk.LEFT, padx=5)

    def _create_status_bar(self):
        """Create the status bar at the bottom of the window."""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2)
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _refresh_devices(self):
        """Refresh the device list from the registry."""
        self.status_var.set("Scanning registry...")
        self.root.update()

        try:
            self.scanner.refresh_cache()
            self.devices = self.scanner.get_all_devices()
            self._update_device_list()
            self.device_count_label.config(text=f"Found: {len(self.devices)} device(s)")
            self.status_var.set(f"Found {len(self.devices)} device(s) - Last refresh: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan registry:\n{e}")
            self.status_var.set("Error scanning registry")

    def _update_device_list(self):
        """Update the device listbox with current devices."""
        self.device_listbox.delete(0, tk.END)

        search_text = self.search_var.get().lower()

        for device in self.devices:
            if search_text and search_text not in device.name.lower() and search_text not in device.vendor.lower():
                continue
            display_text = f"{device.name}"
            if device.vendor:
                display_text += f" ({device.vendor})"
            self.device_listbox.insert(tk.END, display_text)

    def _on_search_changed(self, *args):
        """Handle search text changes."""
        self._update_device_list()

    def _on_device_selected(self, event):
        """Handle device selection in the listbox."""
        selection = self.device_listbox.curselection()
        if not selection:
            return

        # Find the actual device (accounting for search filter)
        search_text = self.search_var.get().lower()
        filtered_devices = [
            d for d in self.devices
            if not search_text or search_text in d.name.lower() or search_text in d.vendor.lower()
        ]

        if selection[0] < len(filtered_devices):
            self.selected_device = filtered_devices[selection[0]]
            self._display_device_details(self.selected_device)

    def _display_device_details(self, device: J2534DeviceInfo):
        """
        Display the details of the selected device.

        Args:
            device: The device to display
        """
        # Basic info
        self.detail_vars["name"].set(device.name)
        self.detail_vars["vendor"].set(device.vendor or "--")
        self.detail_vars["device_id"].set(str(device.device_id))

        # Paths
        self.detail_vars["dll_path"].set(device.function_library_path or "--")
        self.detail_vars["config_app"].set(device.config_application_path or "--")
        self.detail_vars["registry_key"].set(device.registry_key_path or "--")

        # DLL status
        if device.function_library_path:
            if self.scanner.verify_dll_exists(device):
                try:
                    stat = os.stat(device.function_library_path)
                    size_kb = stat.st_size / 1024
                    mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    self.detail_vars["dll_status"].set(f"EXISTS ({size_kb:.1f} KB, modified {mod_time})")
                except Exception:
                    self.detail_vars["dll_status"].set("EXISTS")
                self.open_folder_button.config(state=tk.NORMAL)
            else:
                self.detail_vars["dll_status"].set("NOT FOUND")
                self.open_folder_button.config(state=tk.DISABLED)
        else:
            self.detail_vars["dll_status"].set("No path specified")
            self.open_folder_button.config(state=tk.DISABLED)

        # Protocol support
        self.protocol_vars["can_iso15765"].set(device.can_iso15765)
        self.protocol_vars["j1850vpw"].set(device.j1850vpw)
        self.protocol_vars["j1850pwm"].set(device.j1850pwm)
        self.protocol_vars["iso9141"].set(device.iso9141)
        self.protocol_vars["iso14230"].set(device.iso14230)
        self.protocol_vars["sci_a_engine"].set(device.sci_a_engine)
        self.protocol_vars["sci_a_trans"].set(device.sci_a_trans)
        self.protocol_vars["sci_b_engine"].set(device.sci_b_engine)
        self.protocol_vars["sci_b_trans"].set(device.sci_b_trans)

    def _open_dll_folder(self):
        """Open the folder containing the DLL file in Windows Explorer."""
        if self.selected_device and self.selected_device.function_library_path:
            folder = os.path.dirname(self.selected_device.function_library_path)
            if os.path.exists(folder):
                subprocess.run(["explorer", folder])
            else:
                messagebox.showwarning("Warning", f"Folder does not exist:\n{folder}")

    def _copy_to_clipboard(self):
        """Copy selected device information to clipboard."""
        if not self.selected_device:
            messagebox.showinfo("Info", "No device selected")
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
        self.root.clipboard_clear()
        self.root.clipboard_append(info_text)
        self.status_var.set("Device info copied to clipboard")

    def _export_json(self):
        """Export all devices to a JSON file."""
        if not self.devices:
            messagebox.showinfo("Info", "No devices to export")
            return

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
                    "can_iso15765": device.can_iso15765,
                    "j1850vpw": device.j1850vpw,
                    "j1850pwm": device.j1850pwm,
                    "iso9141": device.iso9141,
                    "iso14230": device.iso14230,
                    "sci_a_engine": device.sci_a_engine,
                    "sci_a_trans": device.sci_a_trans,
                    "sci_b_engine": device.sci_b_engine,
                    "sci_b_trans": device.sci_b_trans,
                })

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)

            self.status_var.set(f"Exported {len(self.devices)} device(s) to JSON")
            messagebox.showinfo("Success", f"Exported {len(self.devices)} device(s) to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{e}")

    def _export_csv(self):
        """Export all devices to a CSV file."""
        if not self.devices:
            messagebox.showinfo("Info", "No devices to export")
            return

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
                writer.writerow([
                    "Name", "Vendor", "Device ID", "Function Library",
                    "Config App", "Registry Key", "Protocols",
                    "CAN", "J1850VPW", "J1850PWM", "ISO9141", "ISO14230",
                    "SCI_A_ENGINE", "SCI_A_TRANS", "SCI_B_ENGINE", "SCI_B_TRANS"
                ])

                for device in self.devices:
                    writer.writerow([
                        device.name,
                        device.vendor,
                        device.device_id,
                        device.function_library_path,
                        device.config_application_path or "",
                        device.registry_key_path,
                        ", ".join(device.supported_protocols),
                        "Yes" if device.can_iso15765 else "No",
                        "Yes" if device.j1850vpw else "No",
                        "Yes" if device.j1850pwm else "No",
                        "Yes" if device.iso9141 else "No",
                        "Yes" if device.iso14230 else "No",
                        "Yes" if device.sci_a_engine else "No",
                        "Yes" if device.sci_a_trans else "No",
                        "Yes" if device.sci_b_engine else "No",
                        "Yes" if device.sci_b_trans else "No",
                    ])

            self.status_var.set(f"Exported {len(self.devices)} device(s) to CSV")
            messagebox.showinfo("Success", f"Exported {len(self.devices)} device(s) to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{e}")

    def _show_about(self):
        """Show the About dialog."""
        messagebox.showinfo(
            "About",
            "J2534 Registry Viewer\n\n"
            "A tool for viewing J2534 PassThru devices\n"
            "registered in the Windows registry.\n\n"
            "Built with Tkinter\n"
            "Version 1.0.0"
        )


def main():
    """Application entry point."""
    root = tk.Tk()

    # Set application icon if available
    try:
        root.iconbitmap("icon.ico")
    except Exception:
        pass

    # Apply a theme if available
    try:
        root.tk.call("source", "azure.tcl")
        root.tk.call("set_theme", "light")
    except Exception:
        pass

    app = J2534RegistryViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
