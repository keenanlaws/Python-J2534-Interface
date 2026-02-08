"""
J2534-API Setup Script
======================

This setup.py provides backward compatibility for older pip versions.
All configuration is in pyproject.toml (PEP 517/518 compliant).

Installation:
    pip install .                    # Basic installation
    pip install -e .                 # Development installation (editable)
    pip install .[gui-pyqt5]         # With PyQt5 GUI support
    pip install .[gui-all]           # With all GUI frameworks
    pip install .[dev]               # With development tools

Build:
    python -m build

Version: 2.0.0
License: MIT
"""

from setuptools import setup

if __name__ == "__main__":
    setup()
