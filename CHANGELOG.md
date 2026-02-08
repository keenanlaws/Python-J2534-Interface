# Changelog

All notable changes to the J2534-API library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-02-04

### Added

#### Core Library
- **J2534 Package**: Complete low-level PassThru API implementation
  - `api.py`: High-level API functions with PassThruMsgBuilder class
  - `config.py`: Singleton configuration for debug/exception modes
  - `constants.py`: Complete SAE J2534-1 protocol constants as IntEnum/IntFlag
  - `dll_interface.py`: Modern ctypes DLL binding with automatic function resolution
  - `exceptions.py`: Comprehensive exception hierarchy with error codes
  - `logging_utils.py`: Debug logging with hex dump utilities
  - `structures.py`: All ctypes structures for J2534 message handling

- **AutoJ2534 Package**: High-level vehicle communication interface
  - `interface.py`: J2534Communications class with auto-connect, filtering
  - `ecu_parameters.py`: Pre-defined connection configurations (Chrysler, SCI variants)
  - `negative_response_codes.py`: Complete UDS negative response code mappings

- **J2534_REGISTRY Package**: Windows registry device scanner
  - `registry_scanner.py`: J2534RegistryScanner class for device enumeration
  - `device_info.py`: J2534DeviceInfo dataclass with protocol support flags

#### GUI Examples
- 4 complete GUI example applications demonstrating J2534 usage:
  - PyQt5 (full-featured professional application)
  - Tkinter (no dependencies, built-in Python)
  - CustomTkinter (modern themed UI)
  - FreeSimpleGUI (rapid prototyping)

- 4 registry viewer GUI examples in `J2534_REGISTRY/examples/`

> **Note**: Dear PyGui and Flet were excluded due to compatibility issues with 32-bit Python (required for J2534 DLLs).

#### Documentation
- Comprehensive README.md for each package
- Module docstrings with usage examples
- Function docstrings following Google style
- Type hints throughout all modules

#### Package Management
- pip-installable with `pyproject.toml` (PEP 517/518 compliant)
- Optional dependencies for GUI frameworks
- Development dependencies for testing/linting

### Changed

#### Naming Conventions
- All variable names now use `lowercase_with_underscores` convention
- All file names now use `lowercase_with_underscores.py` convention
- Constants use `UPPERCASE_WITH_UNDERSCORES`
- Classes use `PascalCase`
- Removed all abbreviations - variables are self-documenting

#### Code Quality
- Complete type hints for all public APIs
- Comprehensive docstrings with examples
- Inline comments explaining complex logic
- Magic numbers replaced with named constants

### Removed

#### Obsolete Files
- `J2534/wrapper.py` - Replaced by `api.py`
- `J2534/dll.py` - Replaced by `dll_interface.py` + `structures.py`
- `J2534/Define.py` - Replaced by `constants.py`
- `J2534/Registry.py` - Replaced by `J2534_REGISTRY/` package

#### Duplicate Files
- `AutoJ2534/EcuParameters.py` - Replaced by `ecu_parameters.py`
- `AutoJ2534/Interface.py` - Replaced by `interface.py`

### Fixed
- Fixed `_protcol_string` typo to `_protocol_string` in interface.py
- Fixed ConnectionConfig attribute compatibility issues
- Fixed FreeSimpleGUI import for PySimpleGUI licensing changes

---

## [1.0.0] - 2023-12-20

### Added
- Initial release with basic J2534 PassThru support
- Basic DLL wrapper for PassThru functions
- Simple registry scanner for device discovery
- Basic message structures for CAN/ISO15765

### Known Issues
- Code duplication in dll.py and wrapper.py
- Mixed naming conventions
- Limited documentation
- No pip installation support

---

## Migration Guide: 1.x to 2.0

### Breaking Changes

1. **Import paths changed**:
   ```python
   # Old (1.x)
   from J2534 import wrapper
   from J2534.Define import ProtocolID

   # New (2.0)
   from J2534 import api
   from J2534.constants import ProtocolId
   ```

2. **Class names changed**:
   ```python
   # Old (1.x)
   from AutoJ2534.Interface import Interface

   # New (2.0)
   from AutoJ2534 import J2534Communications, j2534_communication
   ```

3. **Constant naming**:
   ```python
   # Old (1.x)
   ProtocolID.ISO15765

   # New (2.0)
   ProtocolId.ISO15765  # Note: lowercase 'd' in Id
   ```

### Backward Compatibility

Most old imports are still available through compatibility aliases:
```python
# These still work but are deprecated
from AutoJ2534 import Interface, EcuParameters
```

### Recommended Migration Steps

1. Update imports to use new lowercase module names
2. Update constant references to new IntEnum classes
3. Update exception handling for new exception hierarchy
4. Enable debug mode during migration to verify behavior:
   ```python
   from J2534 import j2534_config
   j2534_config.enable_debug()
   ```
