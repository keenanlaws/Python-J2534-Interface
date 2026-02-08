"""
J2534 Device Information Dataclass
==================================

Defines the J2534DeviceInfo dataclass for storing information about
registered J2534 PassThru devices found in the Windows registry.

Version: 2.0.0
License: MIT
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class J2534DeviceInfo:
    """
    Information about a registered J2534 PassThru device.
    
    This dataclass stores all relevant information about a J2534 device
    as found in the Windows registry under PassThruSupport.04.04.
    
    Attributes:
        name: Display name of the device (e.g., "Drew Technologies Mongoose")
        vendor: Vendor/manufacturer name
        function_library_path: Full path to the J2534 DLL
        config_application_path: Path to configuration application (optional)
        supported_protocols: List of supported protocol names
        can_iso15765: Whether device supports CAN/ISO15765
        j1850vpw: Whether device supports J1850 VPW
        j1850pwm: Whether device supports J1850 PWM
        iso9141: Whether device supports ISO 9141
        iso14230: Whether device supports ISO 14230 (KWP2000)
        sci_a_engine: Whether device supports SCI A Engine
        sci_a_trans: Whether device supports SCI A Transmission
        sci_b_engine: Whether device supports SCI B Engine
        sci_b_trans: Whether device supports SCI B Transmission
        device_id: Registry device ID (usually matches order in registry)
        registry_key_path: Full registry path where device info was found
        
    Example:
        # >>> device = J2534DeviceInfo(
        # ...     name="Drew Technologies Mongoose",
        # ...     vendor="Drew Technologies",
        # ...     function_library_path="C:\Program Files\Mongoose\mongi32.dll"
        # ... )
        # >>> print(device.name)
        Drew Technologies Mongoose
    """
    
    name: str
    """Display name of the J2534 device."""
    
    vendor: str = ""
    """Vendor/manufacturer name."""
    
    function_library_path: str = ""
    """Full path to the J2534 DLL file."""
    
    config_application_path: Optional[str] = None
    """Path to the device configuration application (if available)."""
    
    supported_protocols: List[str] = field(default_factory=list)
    """List of supported protocol names (e.g., ['CAN', 'ISO15765'])."""
    
    # Protocol support flags
    can_iso15765: bool = False
    """True if device supports CAN and ISO 15765."""
    
    j1850vpw: bool = False
    """True if device supports J1850 VPW (Variable Pulse Width)."""
    
    j1850pwm: bool = False
    """True if device supports J1850 PWM (Pulse Width Modulation)."""
    
    iso9141: bool = False
    """True if device supports ISO 9141."""
    
    iso14230: bool = False
    """True if device supports ISO 14230 (KWP2000)."""
    
    sci_a_engine: bool = False
    """True if device supports SCI A Engine bus."""
    
    sci_a_trans: bool = False
    """True if device supports SCI A Transmission bus."""
    
    sci_b_engine: bool = False
    """True if device supports SCI B Engine bus."""
    
    sci_b_trans: bool = False
    """True if device supports SCI B Transmission bus."""
    
    # Registry information
    device_id: int = -1
    """Device ID (index in registry enumeration)."""
    
    registry_key_path: str = ""
    """Full registry path where this device info was found."""
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        protocols = ", ".join(self.supported_protocols) if self.supported_protocols else "Unknown"
        return f"{self.name} ({self.vendor}) - Protocols: {protocols}"
    
    def supports_protocol(self, protocol_name: str) -> bool:
        """
        Check if device supports a specific protocol.
        
        Args:
            protocol_name: Protocol name to check (case-insensitive)
            
        Returns:
            True if protocol is supported, False otherwise
        """
        protocol_lower = protocol_name.lower()
        return any(p.lower() == protocol_lower for p in self.supported_protocols)
