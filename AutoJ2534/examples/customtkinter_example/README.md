# CustomTkinter J2534 Diagnostic Tool Example

Modern-looking GUI using CustomTkinter - Tkinter with beautiful themes!

## Features

- Dark/Light mode support
- Modern rounded widgets
- Tkinter compatibility
- Easy migration from Tkinter

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Why CustomTkinter?

- **Modern Look**: Beautiful out of the box
- **Easy Migration**: Same API as Tkinter
- **Themes**: Dark, Light, System
- **No Learning Curve**: If you know Tkinter, you know this

## Key Concepts

```python
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("My App")

        ctk.CTkButton(self, text="Click", command=func).pack()
        ctk.CTkEntry(self, placeholder_text="Type here").pack()

app = App()
app.mainloop()
```

## Best For

- Modernizing existing Tkinter apps
- Professional-looking desktop apps
- Quick development with modern aesthetics

## License

MIT License
