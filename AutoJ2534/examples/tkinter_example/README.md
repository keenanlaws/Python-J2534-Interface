# Tkinter J2534 Diagnostic Tool Example

A beginner-friendly GUI application using Python's built-in Tkinter library.
**No external dependencies required!**

## Features

- Device selection from registry
- Protocol configuration
- Hex message transmission
- Response display
- Communication logging
- Battery voltage monitoring
- Cross-platform (Windows required for J2534)

## Installation

```bash
# No installation needed! Tkinter comes with Python
cd examples/tkinter_example
python main.py
```

## Code Overview

This example demonstrates key Tkinter concepts:

```python
# Create main window
root = tk.Tk()
root.title("J2534 Diagnostic Tool")

# Create labeled frame (groupbox)
frame = ttk.LabelFrame(root, text="Connection")
frame.grid(row=0, column=0, sticky="ew")

# Combobox (dropdown)
combo = ttk.Combobox(frame, values=["Option 1", "Option 2"])
combo.grid(row=0, column=0)

# Button with command
btn = ttk.Button(frame, text="Click", command=my_function)
btn.grid(row=0, column=1)

# Entry (text input)
entry = ttk.Entry(frame)
entry.grid(row=1, column=0)

# ScrolledText for log
log = scrolledtext.ScrolledText(frame)
log.grid(row=2, column=0)

# Timer for periodic updates
root.after(5000, update_function)  # Call after 5000ms

# Run the app
root.mainloop()
```

## Key Tkinter Concepts

### Widgets Used

| Widget | Purpose |
|--------|---------|
| `tk.Tk()` | Main window |
| `ttk.Frame` | Container |
| `ttk.LabelFrame` | Labeled container (groupbox) |
| `ttk.Label` | Text display |
| `ttk.Entry` | Single-line text input |
| `ttk.Combobox` | Dropdown selection |
| `ttk.Button` | Clickable button |
| `scrolledtext.ScrolledText` | Multi-line text with scrollbar |

### Grid Layout

```python
# Grid positioning
widget.grid(row=0, column=0, sticky="ew")  # East-West expansion
widget.grid(row=1, column=0, columnspan=2)  # Span 2 columns
widget.grid(row=0, column=0, padx=5, pady=5)  # Padding
```

### Event Handling

```python
# Button click
button.config(command=my_function)

# Keyboard event
entry.bind("<Return>", lambda e: send_message())

# Window close
root.protocol("WM_DELETE_WINDOW", on_closing)
```

### Timer/Scheduling

```python
# One-shot timer
timer_id = root.after(5000, callback_function)

# Cancel timer
root.after_cancel(timer_id)
```

### StringVar for Dynamic Updates

```python
# Create variable
status_var = tk.StringVar(value="Initial text")

# Use in label
label = ttk.Label(frame, textvariable=status_var)

# Update dynamically
status_var.set("New text")
```

## Customization

### Change Theme

```python
style = ttk.Style()
# Available themes: 'clam', 'alt', 'default', 'classic'
style.theme_use('clam')
```

### Add Quick-Send Buttons

```python
def add_quick_buttons(parent):
    buttons = [
        ("Tester Present", "3E 00"),
        ("Read VIN", "22 F1 90"),
        ("Read DTCs", "19 02 FF"),
    ]
    for name, data in buttons:
        btn = ttk.Button(parent, text=name,
                         command=lambda d=data: quick_send(d))
        btn.pack(side=tk.LEFT, padx=2)
```

### Custom Styling

```python
style = ttk.Style()
style.configure("Custom.TButton", foreground="blue", font=("Arial", 10))
btn = ttk.Button(frame, text="Custom", style="Custom.TButton")
```

## File Structure

```
tkinter_example/
├── main.py           # Main application
├── requirements.txt  # (empty - no deps)
└── README.md         # This file
```

## Why Tkinter?

- **Built-in**: No pip install needed
- **Simple**: Easy to learn
- **Lightweight**: Fast startup
- **Stable**: Mature library
- **Documentation**: Extensive resources

## Requirements

- Python 3.8+
- Windows OS (for J2534)
- J2534 device with drivers

## License

MIT License
