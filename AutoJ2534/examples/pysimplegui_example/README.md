# PySimpleGUI J2534 Diagnostic Tool Example

Rapid GUI development with PySimpleGUI - perfect for quick prototyping!

## Features

- Simple, declarative layout syntax
- Minimal code for full functionality
- Built-in theming
- Event-driven programming

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Why PySimpleGUI?

- **Fast Development**: UI in minutes, not hours
- **Simple Syntax**: Learn in a day
- **Cross-Platform**: Works on Windows, Linux, Mac
- **Multiple Backends**: Tkinter, Qt, WxPython

## Key Concepts

```python
# Define layout as nested lists
layout = [
    [sg.Text("Label"), sg.Input(key="-INPUT-")],
    [sg.Button("OK"), sg.Button("Cancel")]
]

# Create window
window = sg.Window("Title", layout)

# Event loop
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    if event == "OK":
        print(values["-INPUT-"])

window.close()
```

## License

MIT License
