# J2534 API GUI Examples

This directory contains example applications demonstrating how to use the J2534-API
library with various Python GUI frameworks.

## Available Examples

| Framework | Directory | Best For | Install |
|-----------|-----------|----------|---------|
| **PyQt5** | `pyqt5_example/` | Full-featured desktop apps | `pip install PyQt5` |
| **Tkinter** | `tkinter_example/` | Simple apps, no dependencies | Built-in |
| **PySimpleGUI** | `pysimplegui_example/` | Rapid prototyping | `pip install PySimpleGUI` |
| **CustomTkinter** | `customtkinter_example/` | Modern-looking Tkinter | `pip install customtkinter` |

## Quick Start

```bash
# 1. Choose a framework
cd pyqt5_example    # or tkinter_example, etc.

# 2. Install dependencies (if any)
pip install -r requirements.txt

# 3. Run the example
python main.py
```

## Framework Comparison

### PyQt5
- **Pros**: Most powerful, professional apps, extensive widgets
- **Cons**: Larger package size, licensing for commercial closed-source
- **Use When**: Building production desktop applications

### Tkinter
- **Pros**: Built into Python, no install needed, lightweight
- **Cons**: Dated appearance (without themes)
- **Use When**: Quick utilities, no external dependencies needed

### PySimpleGUI
- **Pros**: Fastest development time, simple syntax
- **Cons**: Less control over fine details
- **Use When**: Prototyping, simple tools, learning

### CustomTkinter
- **Pros**: Modern look, same API as Tkinter, easy migration
- **Cons**: Smaller widget selection than PyQt
- **Use When**: Modernizing Tkinter apps, professional appearance

## Common Features in All Examples

Each example demonstrates:

1. **Device Discovery** - Scanning registry for J2534 devices
2. **Connection Management** - Connect/disconnect handling
3. **Protocol Selection** - Choosing communication protocol
4. **Message Transmission** - Sending hex data to ECU
5. **Response Display** - Parsing and showing responses
6. **Logging** - Timestamped communication log
7. **Voltage Monitoring** - Periodic battery voltage updates

## Code Structure

All examples follow a similar structure:

```python
# Import J2534 modules
from J2534_REGISTRY import get_all_j2534_devices
from AutoJ2534 import j2534_communication, Connections

# Main application class
class J2534DiagnosticTool:
    def __init__(self):
        self.devices = []
        self.is_connected = False
        self.setup_ui()
        self.refresh_devices()

    def refresh_devices(self):
        self.devices = get_all_j2534_devices()
        # Update UI with device list

    def connect(self):
        j2534_communication.open_communication(device_idx, config_key)
        self.is_connected = True

    def disconnect(self):
        j2534_communication.disconnect()
        j2534_communication.close()
        self.is_connected = False

    def send_message(self, data_bytes):
        response = j2534_communication.transmit_and_receive_message(data_bytes)
        # Display response
```

## Building Your Own Application

1. **Start with the Tkinter example** if you're learning
2. **Use PyQt5** for full-featured production apps
3. **Use CustomTkinter** for modern-looking Tkinter apps
4. **Use FreeSimpleGUI** for rapid prototyping

## Requirements

All examples require:
- Windows OS (J2534 is Windows-only)
- Python 3.8+
- J2534 device with installed drivers
- Vehicle connection (for actual communication)

## Directory Structure

```
examples/
├── README.md                    # This file
├── pyqt5_example/
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
├── tkinter_example/
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
├── pysimplegui_example/
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
└── customtkinter_example/
    ├── main.py
    ├── requirements.txt
    └── README.md
```

## License

MIT License - All examples are free to use and modify.
