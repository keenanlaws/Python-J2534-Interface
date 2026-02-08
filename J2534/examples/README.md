# J2534 Low-Level API Examples

This directory contains GUI examples demonstrating the **low-level J2534 PassThru API**.
Each example showcases device discovery, connection management, message I/O, and configuration
using different Python GUI frameworks.

## Available Examples

| Framework | Directory | Dependencies | Best For |
|-----------|-----------|--------------|----------|
| **Tkinter** | `tkinter_example/` | None (built-in) | Quick demos, learning |
| **PyQt5** | `pyqt5_example/` | `pip install PyQt5` | Professional applications |
| **CustomTkinter** | `customtkinter_example/` | `pip install customtkinter` | Modern themed UIs |
| **FreeSimpleGUI** | `pysimplegui_example/` | `pip install FreeSimpleGUI` | Rapid prototyping |

## Features Demonstrated

All examples demonstrate these J2534 API features:

### Device Management
- `get_list_j2534_devices()` - Enumerate registered devices
- `set_j2534_device_to_connect(index)` - Select device by index
- `pt_open()` - Open device connection
- `pt_close(device_id)` - Close device connection

### Channel Management
- `pt_connect(device_id, protocol, flags, baud_rate)` - Connect protocol channel
- `pt_disconnect(channel_id)` - Disconnect channel

### Message I/O
- `PassThruMsgBuilder(protocol, tx_flags)` - Create message structure
- `pt_write_message(channel_id, msg, count, timeout)` - Transmit message
- `pt_read_message(channel_id, msg, count, timeout)` - Receive message

### Filters
- `pt_start_ecu_filter(channel_id, protocol, mask, pattern, flow_control, flags)` - Set filter
- `pt_stop_message_filter(channel_id, filter_id)` - Remove filter
- `clear_message_filters(channel_id)` - Clear all filters

### Utilities
- `read_battery_volts(device_id)` - Read vehicle battery voltage
- `pt_read_version(device_id)` - Get firmware/DLL versions
- `clear_receive_buffer(channel_id)` - Clear RX buffer
- `clear_transmit_buffer(channel_id)` - Clear TX buffer

### Configuration
- `j2534_config.enable_debug()` - Enable debug logging
- `j2534_config.disable_debug()` - Disable debug logging
- `j2534_config.enable_exceptions()` - Enable exception mode
- `j2534_config.disable_exceptions()` - Disable exception mode

## Running Examples

### Tkinter (No Dependencies)
```bash
cd J2534/examples/tkinter_example
python main.py
```

### PyQt5
```bash
pip install PyQt5
cd J2534/examples/pyqt5_example
python main.py
```

### CustomTkinter
```bash
pip install customtkinter
cd J2534/examples/customtkinter_example
python main.py
```

### FreeSimpleGUI
```bash
pip install FreeSimpleGUI
cd J2534/examples/pysimplegui_example
python main.py
```

## UI Layout

All examples follow a consistent layout:

```
+----------------------------------------------------------+
| J2534 API Demo - [Framework Name]                        |
+----------------------------------------------------------+
| Device: [Dropdown] Protocol: [Dropdown] [Refresh]        |
| Baud Rate: [Dropdown] Flags: [Input]                     |
| [Open Device] [Connect] [Disconnect] [Close Device]      |
+----------------------------------------------------------+
| Filter Setup:                                            |
| Mask: [0xFFFFFFFF] Pattern: [0x7E8] Flow Ctrl: [0x7E0]   |
| [Set Filter] [Clear Filters]                             |
+----------------------------------------------------------+
| Message I/O:                                             |
| TX Data (hex): [22 F1 90                            ]    |
| [Send] [Clear RX]                                        |
| Response: [62 F1 90 ...]                                 |
+----------------------------------------------------------+
| Communication Log:                                       |
| [Scrollable timestamped log]                             |
| [Clear Log]                                              |
+----------------------------------------------------------+
| [x] Debug Mode  [x] Exception Mode                       |
| Status: Connected | Voltage: 12.45V | FW: v1.0.0        |
+----------------------------------------------------------+
```

## Protocol Support

Available protocols (from `ProtocolId` enum):
- `ISO15765` (6) - CAN with ISO-TP transport layer
- `CAN` (5) - Raw CAN
- `J1850VPW` (1) - J1850 Variable Pulse Width
- `J1850PWM` (2) - J1850 Pulse Width Modulation
- `ISO9141` (3) - ISO 9141
- `ISO14230` (4) - ISO 14230 (KWP2000)
- `SCI_A_ENGINE` (7) - Chrysler SCI A Engine
- `SCI_A_TRANS` (8) - Chrysler SCI A Transmission
- `SCI_B_ENGINE` (9) - Chrysler SCI B Engine
- `SCI_B_TRANS` (10) - Chrysler SCI B Transmission

## Common Baud Rates

Available baud rates (from `BaudRate` enum):
- `CAN_500K` (500000) - Standard CAN
- `CAN_250K` (250000) - Slower CAN networks
- `CAN_125K` (125000) - Low-speed CAN
- `J1850_VPW` (10400) - J1850 VPW
- `J1850_PWM` (41600) - J1850 PWM
- `ISO9141` (10400) - ISO 9141
- `ISO14230` (10400) - KWP2000

## Notes

- These examples use the **low-level J2534 API** directly
- For higher-level vehicle communication, see the `AutoJ2534` module
- All examples require a J2534-compatible PassThru device
- Windows only (J2534 uses Windows Registry and DLL)
