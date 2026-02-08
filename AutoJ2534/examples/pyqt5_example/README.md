# PyQt5 J2534 Diagnostic Tool Example

A full-featured GUI application for J2534 vehicle diagnostics using PyQt5.

## Features

- Device selection from Windows registry
- Protocol configuration (CAN, ISO15765, SCI)
- Hex message transmission
- Response parsing and display
- Real-time communication logging
- Battery voltage monitoring
- Professional UI with Fusion style

## Screenshot

```
┌─────────────────────────────────────────────────────────┐
│ J2534 Diagnostic Tool - PyQt5                      [─][□][×]│
├─────────────────────────────────────────────────────────┤
│ ┌─ Connection ────────────────────────────────────────┐ │
│ │ Device: [Drew Technologies Mongoose ▼]              │ │
│ │ Protocol: [chrys1 ▼]   [Refresh] [Connect]          │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌─ Send Message ──────────────────────────────────────┐ │
│ │ Data (hex): [3E 00                        ] [Send]  │ │
│ │                                                     │ │
│ │ Response:                                           │ │
│ │ ┌─────────────────────────────────────────────────┐ │ │
│ │ │ 7E 00                                           │ │ │
│ │ └─────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌─ Communication Log ─────────────────────────────────┐ │
│ │ [14:32:15.123] Connected successfully!              │ │
│ │ [14:32:15.456] Device: Mongoose, FW: 1.2, DLL: 3.0  │ │
│ │ [14:32:20.789] TX: 3E 00                            │ │
│ │ [14:32:20.892] RX: 7E 00                            │ │
│ │                                         [Clear Log] │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ Connected                                Voltage: 12.45V│
└─────────────────────────────────────────────────────────┘
```

## Installation

```bash
# Install PyQt5
pip install -r requirements.txt

# Or manually
pip install PyQt5
```

## Usage

```bash
cd examples/pyqt5_example
python main.py
```

## Code Structure

```python
# Main window class
class J2534DiagnosticTool(QMainWindow):
    def setup_ui(self):          # Build UI components
    def refresh_devices(self):   # Scan registry for devices
    def connect_device(self):    # Establish J2534 connection
    def disconnect_device(self): # Clean disconnect
    def send_message(self):      # Transmit hex message
    def update_voltage(self):    # Monitor battery voltage
```

## Key PyQt5 Concepts Used

- **QMainWindow**: Main application window
- **QComboBox**: Device and protocol selection
- **QTextEdit**: Log display and response area
- **QLineEdit**: Hex data input
- **QTimer**: Periodic voltage updates
- **QStatusBar**: Connection status and voltage
- **QSplitter**: Resizable panels
- **Signal/Slot**: Event handling (clicked.connect)

## Customization

### Add Custom Protocol

```python
# In main.py, modify connection_configs:
self.connection_configs = list(Connections.CHRYSLER_ECU.keys())

# Add your own:
self.connection_configs.append("my_custom_protocol")
```

### Change Update Interval

```python
# Voltage update every 3 seconds instead of 5
self.voltage_timer.start(3000)
```

### Add Predefined Messages

```python
# Add quick-send buttons
quick_buttons = QHBoxLayout()
for name, data in [("Tester Present", "3E 00"), ("Read VIN", "22 F1 90")]:
    btn = QPushButton(name)
    btn.clicked.connect(lambda _, d=data: self.quick_send(d))
    quick_buttons.addWidget(btn)
```

## Error Handling

The example includes error handling for:
- No devices found
- Connection failures
- Invalid hex input
- Communication timeouts
- Unexpected disconnection

## Requirements

- Windows OS
- Python 3.8+
- PyQt5 5.15+
- J2534 device with installed drivers
- Vehicle connected (for actual communication)

## License

MIT License
