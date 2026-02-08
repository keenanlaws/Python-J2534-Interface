"""
ECU Connection Parameters Module
================================

This module defines the connection parameters and configurations for
communicating with various vehicle ECUs. It provides pre-configured
connection profiles for different ECU types and communication protocols.

The module includes:
    - ConnectionConfig: Dataclass for connection parameters
    - Connections: Pre-defined connection profiles for various ECUs
    - Helper functions for working with connection configurations

Connection profiles specify all parameters needed to establish
communication with a specific ECU, including:
    - Protocol (CAN, ISO 15765, SCI, etc.)
    - Baud rate
    - CAN IDs (transmit and receive)
    - Timing parameters
    - Communication verification commands

Example:
    Using a pre-defined connection profile::

        from AutoJ2534.ecu_parameters import Connections, ConnectionConfig

        # Get Chrysler ECU CAN 11-bit configuration
        config = Connections.CHRYSLER_ECU['chrys1']

        print(f"Protocol: {config.protocol_name}")
        print(f"Baud rate: {config.baud_rate}")
        print(f"TX ID: 0x{config.transmit_id:X}")
        print(f"RX ID: 0x{config.receive_id:X}")

Example:
    Creating a custom connection profile::

        custom_config = ConnectionConfig(
            name="My Custom ECU",
            transmit_delay_ms=0,
            receive_delay_ms=500,
            transmit_id=0x7E0,
            receive_id=0x7E8,
            mask_id=0xFFFFFFFF,
            connect_flags=0,
            transmit_flags=0x40,
            baud_rate=500000,
            protocol_id=6,
            protocol_name="ISO15765",
            communication_check=[0x22, 0xF1, 0x90],
            t1_max_ms=None,
            t2_max_ms=None,
            t4_max_ms=None,
            t5_max_ms=None
        )

Author: J2534-API Contributors
License: MIT
Version: 2.0.0
"""

from dataclasses import dataclass
from typing import Optional, List, Dict


@dataclass
class ConnectionConfig:
    """
    Configuration parameters for ECU communication.

    This dataclass holds all the parameters needed to establish a
    communication channel with a vehicle ECU using J2534.

    Attributes:
        name (str):
            Human-readable name for this connection profile.
            Example: "CHRYSLER ECU CAN 11-BIT"

        transmit_delay_ms (int):
            Delay in milliseconds after transmitting a message.
            Used for protocols that need time between messages.

        receive_delay_ms (int):
            Timeout in milliseconds when waiting for a response.
            Should be long enough for the ECU to respond.

        transmit_id (int):
            The CAN identifier used when sending messages to the ECU.
            For ISO 15765, this is typically 0x7E0 (tester address).

        receive_id (int):
            The CAN identifier expected in responses from the ECU.
            For ISO 15765, this is typically 0x7E8 (ECU address).

        mask_id (int):
            The mask used for message filtering.
            0xFFFFFFFF means exact match required.

        connect_flags (int):
            Flags passed to PassThruConnect.
            Example: 0x800 for CAN 29-bit addressing.

        transmit_flags (int):
            Flags for message transmission.
            Example: 0x40 for ISO 15765 frame padding.

        baud_rate (int):
            Communication baud rate in bits per second.
            Example: 500000 for 500 kbps CAN.

        protocol_id (int):
            J2534 protocol identifier.
            6 = ISO15765, 7-10 = SCI variants.

        protocol_name (str):
            Human-readable protocol name.
            Example: "ISO15765", "SCI_A_ENGINE"

        communication_check (List[int]):
            A diagnostic command to verify communication is working.
            The ECU should respond positively to this command.

        t1_max_ms (Optional[int]):
            SCI protocol: Maximum inter-frame response delay (ms).

        t2_max_ms (Optional[int]):
            SCI protocol: Maximum inter-frame request delay (ms).

        t4_max_ms (Optional[int]):
            SCI protocol: Maximum inter-message response delay (ms).

        t5_max_ms (Optional[int]):
            SCI protocol: Maximum inter-message request delay (ms).

    Example:
        # >>> config = ConnectionConfig(
        # ...     name="Standard OBD-II CAN",
        # ...     transmit_delay_ms=0,
        # ...     receive_delay_ms=1000,
        # ...     transmit_id=0x7DF,
        # ...     receive_id=0x7E8,
        # ...     mask_id=0xFFFFFFFF,
        # ...     connect_flags=0,
        # ...     transmit_flags=0x40,
        # ...     baud_rate=500000,
        # ...     protocol_id=6,
        # ...     protocol_name="ISO15765",
        # ...     communication_check=[0x01, 0x00],
        # ...     t1_max_ms=None,
        # ...     t2_max_ms=None,
        # ...     t4_max_ms=None,
        # ...     t5_max_ms=None
        # ... )
    """

    name: str
    transmit_delay_ms: int
    receive_delay_ms: int
    transmit_id: int
    receive_id: int
    mask_id: int
    connect_flags: int
    transmit_flags: int
    baud_rate: int
    protocol_id: int
    protocol_name: str
    communication_check: List[int]
    t1_max_ms: Optional[int]
    t2_max_ms: Optional[int]
    t4_max_ms: Optional[int]
    t5_max_ms: Optional[int]

    # Aliases for backward compatibility with old attribute names
    # =========================================================================
    # Aliases for interface.py (new naming convention)
    # =========================================================================

    @property
    def transmit_delay_milliseconds(self) -> int:
        """Alias for transmit_delay_ms (used by interface.py)."""
        return self.transmit_delay_ms

    @property
    def receive_delay_milliseconds(self) -> int:
        """Alias for receive_delay_ms (used by interface.py)."""
        return self.receive_delay_ms

    @property
    def transmit_identifier(self) -> int:
        """Alias for transmit_id (used by interface.py)."""
        return self.transmit_id

    @property
    def receive_identifier(self) -> int:
        """Alias for receive_id (used by interface.py)."""
        return self.receive_id

    @property
    def mask_identifier(self) -> int:
        """Alias for mask_id (used by interface.py)."""
        return self.mask_id

    @property
    def communication_check_command(self) -> List[int]:
        """Alias for communication_check (used by interface.py)."""
        return self.communication_check

    # =========================================================================
    # Aliases for backward compatibility with old attribute names
    # =========================================================================

    @property
    def tx_delay(self) -> int:
        """Alias for transmit_delay_ms (backward compatibility)."""
        return self.transmit_delay_ms

    @property
    def rx_delay(self) -> int:
        """Alias for receive_delay_ms (backward compatibility)."""
        return self.receive_delay_ms

    @property
    def tx_id(self) -> int:
        """Alias for transmit_id (backward compatibility)."""
        return self.transmit_id

    @property
    def rx_id(self) -> int:
        """Alias for receive_id (backward compatibility)."""
        return self.receive_id

    @property
    def mask(self) -> int:
        """Alias for mask_id (backward compatibility)."""
        return self.mask_id

    @property
    def connect_flag(self) -> int:
        """Alias for connect_flags (backward compatibility)."""
        return self.connect_flags

    @property
    def tx_flag(self) -> int:
        """Alias for transmit_flags (backward compatibility)."""
        return object.__getattribute__(self, 'transmit_flags')

    @property
    def comm_check(self) -> List[int]:
        """Alias for communication_check (backward compatibility)."""
        return self.communication_check

    @property
    def t1_max(self) -> Optional[int]:
        """Alias for t1_max_ms (backward compatibility)."""
        return self.t1_max_ms

    @property
    def t2_max(self) -> Optional[int]:
        """Alias for t2_max_ms (backward compatibility)."""
        return self.t2_max_ms

    @property
    def t4_max(self) -> Optional[int]:
        """Alias for t4_max_ms (backward compatibility)."""
        return self.t4_max_ms

    @property
    def t5_max(self) -> Optional[int]:
        """Alias for t5_max_ms (backward compatibility)."""
        return self.t5_max_ms

    def is_can_protocol(self) -> bool:
        """
        Check if this configuration uses CAN-based protocol.

        Returns:
            bool: True if protocol is CAN or ISO 15765.
        """
        return self.protocol_id in [5, 6]  # CAN = 5, ISO15765 = 6

    def is_sci_protocol(self) -> bool:
        """
        Check if this configuration uses SCI protocol.

        Returns:
            bool: True if protocol is any SCI variant.
        """
        return self.protocol_id in [7, 8, 9, 10]  # SCI_A/B ENGINE/TRANS

    def uses_29bit_addressing(self) -> bool:
        """
        Check if this configuration uses 29-bit CAN addressing.

        Returns:
            bool: True if 29-bit addressing is enabled.
        """
        return bool(self.connect_flags & 0x100)  # CAN_29BIT_ID flag


class Connections:
    """
    Pre-defined connection configurations for various ECUs.

    This class provides dictionaries of ConnectionConfig objects for
    different vehicle manufacturers and ECU types.

    Available Configuration Sets:
        CHRYSLER_ECU: Chrysler/FCA vehicle ECU configurations

    Example:
        # >>> from AutoJ2534.ecu_parameters import Connections
        # >>>
        # >>> # List available Chrysler configurations
        # >>> for key, config in Connections.CHRYSLER_ECU.items():
        # ...     print(f"{key}: {config.name}")
        # >>>
        # >>> # Get specific configuration
        # >>> ecu_config = Connections.CHRYSLER_ECU['chrys1']
    """

    # =========================================================================
    # Chrysler/FCA ECU Configurations
    # =========================================================================

    CHRYSLER_ECU: Dict[str, ConnectionConfig] = {
        # -----------------------------------------------------------------
        # CAN-based configurations
        # -----------------------------------------------------------------

        'chrys1': ConnectionConfig(
            name='CHRYSLER ECU CAN 11-BIT',
            transmit_delay_ms=0,
            receive_delay_ms=500,
            transmit_id=0x7E0,
            receive_id=0x7E8,
            mask_id=0xFFFFFFFF,
            connect_flags=0,
            transmit_flags=0x40,  # ISO15765_FRAME_PAD
            baud_rate=500000,
            protocol_id=6,  # ISO15765
            protocol_name='ISO15765',
            communication_check=[0x1A, 0x87],  # Read ECU ID
            t1_max_ms=None,
            t2_max_ms=None,
            t4_max_ms=None,
            t5_max_ms=None
        ),

        'chrys2': ConnectionConfig(
            name='CHRYSLER ECU CAN 29-BIT',
            transmit_delay_ms=0,
            receive_delay_ms=500,
            transmit_id=0x18DA10F1,  # 29-bit diagnostic request
            receive_id=0x18DAF110,   # 29-bit diagnostic response
            mask_id=0xFFFFFFFF,
            connect_flags=0x800,     # CAN_ID_BOTH
            transmit_flags=0x140,    # CAN_29BIT_ID | ISO15765_FRAME_PAD
            baud_rate=500000,
            protocol_id=6,  # ISO15765
            protocol_name='ISO15765',
            communication_check=[0x1A, 0x87],
            t1_max_ms=None,
            t2_max_ms=None,
            t4_max_ms=None,
            t5_max_ms=None
        ),

        'chrys6': ConnectionConfig(
            name='CHRYSLER TIPM',
            transmit_delay_ms=0,
            receive_delay_ms=500,
            transmit_id=0x620,
            receive_id=0x504,
            mask_id=0xFFFFFFFF,
            connect_flags=0,
            transmit_flags=0x40,
            baud_rate=500000,
            protocol_id=6,
            protocol_name='ISO15765',
            communication_check=[0x1A, 0x87],
            t1_max_ms=None,
            t2_max_ms=None,
            t4_max_ms=None,
            t5_max_ms=None
        ),

        'chrys7': ConnectionConfig(
            name='CHRYSLER BCM',
            transmit_delay_ms=0,
            receive_delay_ms=500,
            transmit_id=0x620,
            receive_id=0x504,
            mask_id=0xFFFFFFFF,
            connect_flags=0,
            transmit_flags=0x40,
            baud_rate=500000,
            protocol_id=6,
            protocol_name='ISO15765',
            communication_check=[0x22, 0xF1, 0x90],  # Read VIN
            t1_max_ms=None,
            t2_max_ms=None,
            t4_max_ms=None,
            t5_max_ms=None
        ),

        'chrys10': ConnectionConfig(
            name='CHRYSLER TRANS CAN 11-BIT',
            transmit_delay_ms=0,
            receive_delay_ms=500,
            transmit_id=0x7E1,
            receive_id=0x7E9,
            mask_id=0xFFFFFFFF,
            connect_flags=0,
            transmit_flags=0x40,
            baud_rate=500000,
            protocol_id=6,
            protocol_name='ISO15765',
            communication_check=[0x1A, 0x87],
            t1_max_ms=None,
            t2_max_ms=None,
            t4_max_ms=None,
            t5_max_ms=None
        ),

        # -----------------------------------------------------------------
        # SCI-based configurations
        # -----------------------------------------------------------------

        'chrys3': ConnectionConfig(
            name='CHRYSLER ECU SCI A ENGINE',
            transmit_delay_ms=500,
            receive_delay_ms=1000,
            transmit_id=0,
            receive_id=0,
            mask_id=0,
            connect_flags=0,
            transmit_flags=0,
            baud_rate=7813,  # 7812.5 baud
            protocol_id=7,   # SCI_A_ENGINE
            protocol_name='SCI_A_ENGINE',
            communication_check=[0x2A, 0x0F],
            t1_max_ms=None,
            t2_max_ms=None,
            t4_max_ms=200,
            t5_max_ms=None
        ),

        'chrys4': ConnectionConfig(
            name='CHRYSLER ECU SCI B ENGINE',
            transmit_delay_ms=500,
            receive_delay_ms=1000,
            transmit_id=0,
            receive_id=0,
            mask_id=0,
            connect_flags=0,
            transmit_flags=0,
            baud_rate=7813,
            protocol_id=9,  # SCI_B_ENGINE
            protocol_name='SCI_B_ENGINE',
            communication_check=[0x22, 0x20, 0x07, 0x49],
            t1_max_ms=75,
            t2_max_ms=5,
            t4_max_ms=50,
            t5_max_ms=1
        ),

        'chrys5': ConnectionConfig(
            name='CHRYSLER ECU SCI B CUMMINS',
            transmit_delay_ms=500,
            receive_delay_ms=1000,
            transmit_id=0,
            receive_id=0,
            mask_id=0,
            connect_flags=0,
            transmit_flags=0,
            baud_rate=7813,
            protocol_id=9,  # SCI_B_ENGINE
            protocol_name='SCI_B_ENGINE',
            communication_check=[0x2A, 0x0F],
            t1_max_ms=75,
            t2_max_ms=50,
            t4_max_ms=50,
            t5_max_ms=10
        ),

        'chrys8': ConnectionConfig(
            name='CHRYSLER ECU SCI B TRANS',
            transmit_delay_ms=500,
            receive_delay_ms=1000,
            transmit_id=0,
            receive_id=0,
            mask_id=0,
            connect_flags=0,
            transmit_flags=0,
            baud_rate=7813,
            protocol_id=10,  # SCI_B_TRANS
            protocol_name='SCI_B_TRANS',
            communication_check=[0x01, 0x00],
            t1_max_ms=75,
            t2_max_ms=5,
            t4_max_ms=50,
            t5_max_ms=1
        ),

        'chrys9': ConnectionConfig(
            name='CHRYSLER ECU SCI A TRANS',
            transmit_delay_ms=500,
            receive_delay_ms=1000,
            transmit_id=0,
            receive_id=0,
            mask_id=0,
            connect_flags=0,
            transmit_flags=0,
            baud_rate=7813,
            protocol_id=8,  # SCI_A_TRANS
            protocol_name='SCI_A_TRANS',
            communication_check=[0x2A, 0x0F],
            t1_max_ms=None,
            t2_max_ms=None,
            t4_max_ms=None,
            t5_max_ms=None
        ),

        # -----------------------------------------------------------------
        # Standard OBD-II Configurations
        # -----------------------------------------------------------------

        'obd2_can_11bit': ConnectionConfig(
            name='OBD-II Standard CAN 11-bit',
            transmit_delay_ms=0,
            receive_delay_ms=500,
            transmit_id=0x7DF,  # Functional broadcast address
            receive_id=0x7E8,   # Primary ECU response
            mask_id=0xFFFFFFFF,
            connect_flags=0,
            transmit_flags=0x40,  # ISO15765_FRAME_PAD
            baud_rate=500000,
            protocol_id=6,  # ISO15765
            protocol_name='ISO15765',
            communication_check=[0x01, 0x00],  # OBD Mode 1, PIDs supported
            t1_max_ms=None,
            t2_max_ms=None,
            t4_max_ms=None,
            t5_max_ms=None
        ),

        'obd2_can_29bit': ConnectionConfig(
            name='OBD-II Extended CAN 29-bit',
            transmit_delay_ms=0,
            receive_delay_ms=500,
            transmit_id=0x18DB33F1,  # 29-bit functional request
            receive_id=0x18DAF110,   # 29-bit ECU response
            mask_id=0xFFFFFFFF,
            connect_flags=0x800,     # CAN_ID_BOTH
            transmit_flags=0x140,    # CAN_29BIT_ID | ISO15765_FRAME_PAD
            baud_rate=500000,
            protocol_id=6,  # ISO15765
            protocol_name='ISO15765',
            communication_check=[0x01, 0x00],
            t1_max_ms=None,
            t2_max_ms=None,
            t4_max_ms=None,
            t5_max_ms=None
        ),

        'obd2_can_250k': ConnectionConfig(
            name='OBD-II CAN 250kbps',
            transmit_delay_ms=0,
            receive_delay_ms=500,
            transmit_id=0x7DF,
            receive_id=0x7E8,
            mask_id=0xFFFFFFFF,
            connect_flags=0,
            transmit_flags=0x40,
            baud_rate=250000,  # Some vehicles use 250k CAN
            protocol_id=6,
            protocol_name='ISO15765',
            communication_check=[0x01, 0x00],
            t1_max_ms=None,
            t2_max_ms=None,
            t4_max_ms=None,
            t5_max_ms=None
        ),
    }

    @classmethod
    def get_all_chrysler_configs(cls) -> Dict[str, ConnectionConfig]:
        """
        Get all available Chrysler ECU configurations.

        Returns:
            Dict[str, ConnectionConfig]: Dictionary of all Chrysler configs.
        """
        return cls.CHRYSLER_ECU

    @classmethod
    def get_chrysler_can_configs(cls) -> Dict[str, ConnectionConfig]:
        """
        Get Chrysler configurations that use CAN protocol.

        Returns:
            Dict[str, ConnectionConfig]: Dictionary of CAN-based configs.
        """
        return {
            key: config
            for key, config in cls.CHRYSLER_ECU.items()
            if config.is_can_protocol()
        }

    @classmethod
    def get_chrysler_sci_configs(cls) -> Dict[str, ConnectionConfig]:
        """
        Get Chrysler configurations that use SCI protocol.

        Returns:
            Dict[str, ConnectionConfig]: Dictionary of SCI-based configs.
        """
        return {
            key: config
            for key, config in cls.CHRYSLER_ECU.items()
            if config.is_sci_protocol()
        }

    @classmethod
    def list_available_configs(cls) -> List[str]:
        """
        List all available configuration keys.

        Returns:
            List[str]: List of configuration key names.
        """
        return list(cls.CHRYSLER_ECU.keys())


# =============================================================================
# Helper Functions
# =============================================================================

def create_custom_can_config(
    name: str,
    transmit_id: int,
    receive_id: int,
    baud_rate: int = 500000,
    use_29bit_addressing: bool = False,
    communication_check: Optional[List[int]] = None
) -> ConnectionConfig:
    """
    Create a custom CAN/ISO 15765 connection configuration.

    This is a convenience function for creating common CAN configurations
    without specifying all parameters manually.

    Args:
        name: Human-readable name for the configuration.
        transmit_id: CAN ID for transmitted messages.
        receive_id: CAN ID for received messages.
        baud_rate: CAN baud rate (default 500000).
        use_29bit_addressing: Use 29-bit CAN IDs (default False).
        communication_check: Optional diagnostic command for verification.

    Returns:
        ConnectionConfig: A configured connection profile.

    Example:
        # >>> config = create_custom_can_config(
        # ...     name="My ECU",
        # ...     transmit_id=0x7E0,
        # ...     receive_id=0x7E8
        # ... )
    """
    if communication_check is None:
        communication_check = [0x3E, 0x00]  # Tester Present

    connect_flags = 0x800 if use_29bit_addressing else 0
    transmit_flags = 0x140 if use_29bit_addressing else 0x40

    return ConnectionConfig(
        name=name,
        transmit_delay_ms=0,
        receive_delay_ms=500,
        transmit_id=transmit_id,
        receive_id=receive_id,
        mask_id=0xFFFFFFFF,
        connect_flags=connect_flags,
        transmit_flags=transmit_flags,
        baud_rate=baud_rate,
        protocol_id=6,  # ISO15765
        protocol_name='ISO15765',
        communication_check=communication_check,
        t1_max_ms=None,
        t2_max_ms=None,
        t4_max_ms=None,
        t5_max_ms=None
    )
