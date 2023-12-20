class ConnectionConfig:
    def __init__(self, name, tx_delay, rx_delay, tx_id, rx_id, mask, connect_flag, tx_flag, baud_rate, protocol_id,
                 protocol_name, comm_check, t1_max, t2_max, t4_max, t5_max):
        self.name = name
        self.tx_delay = tx_delay
        self.rx_delay = rx_delay
        self.tx_id = tx_id
        self.rx_id = rx_id
        self.mask = mask
        self.connect_flag = connect_flag
        self.tx_flag = tx_flag
        self.baud_rate = baud_rate
        self.protocol_id = protocol_id
        self.protocol_name = protocol_name
        self.comm_check = comm_check
        self.t1_max = t1_max
        self.t2_max = t2_max
        self.t4_max = t4_max
        self.t5_max = t5_max


class Connections:
    CHRYSLER_ECU = {
        'chrys1': ConnectionConfig(
            'CHRYSLER ECU CAN 11-BIT',
            0,
            500,
            0x7E0,
            0x7E8,
            0xFFFFFFFF,
            0,
            0X40,
            500000,
            6,
            'ISO15765',
            [0x1a, 0x87],
            None,
            None,
            None,
            None
        ),
        'chrys2': ConnectionConfig(
            'CHRYSLER ECU CAN 29-BIT',
            0,
            500,
            0x18DA10F1,
            0x18DAF110,
            0xFFFFFFFF,
            0x800,
            0X140,
            500000,
            6,
            'ISO15765',
            [0x1a, 0x87],
            None,
            None,
            None,
            None
        ),
        'chrys3': ConnectionConfig(
            'CHRYSLER ECU SCI A ENGINE',
            500,
            1000,
            0,
            0,
            0,
            0,
            0,
            7813,
            7,
            'SCI_A_ENGINE',
            [0x2a, 0x0f],
            None,
            None,
            200,
            None
        ),
        'chrys4': ConnectionConfig(
            'CHRYSLER ECU SCI B ENGINE',
            500,
            1000,
            0,
            0,
            0,
            0,
            0,
            7813,
            9,
            'SCI_B_ENGINE',
            [0x22, 0x20, 0x07, 0x49],
            75,
            5,
            50,
            1
        ),
        'chrys5': ConnectionConfig(
            'CHRYSLER ECU SCI B CUMMINS',
            500,
            1000,
            0,
            0,
            0,
            0,
            0,
            7813,
            9,
            'SCI_B_ENGINE',
            [0x2a, 0x0f],
            75,
            50,
            50,
            10
        ),
        'chrys6': ConnectionConfig(
            'CHRYSLER TIPM',
            0,
            500,
            0X620,
            0X504,
            0xFFFFFFFF,
            0,
            0X40,
            500000,
            6,
            'ISO15765',
            [0x1a, 0x87],
            None,
            None,
            None,
            None
        ),
        'chrys7': ConnectionConfig(
            'CHRYSLER BCM',
            0,
            500,
            0X620,
            0X504,
            0xFFFFFFFF,
            0,
            0X40,
            500000,
            6,
            'ISO15765',
            [0x22, 0xf1, 0x90],
            None,
            None,
            None,
            None
        ),
        'chrys8': ConnectionConfig(
            'CHRYSLER ECU SCI B TRANS',
            500,
            1000,
            0,
            0,
            0,
            0,
            0,
            7813,
            10,
            'SCI_B_TRANS',
            [0x01, 0x00],
            75,
            5,
            50,
            1
        ),
        'chrys9': ConnectionConfig(
            'CHRYSLER ECU SCI A TRANS',
            500,
            1000,
            0,
            0,
            0,
            0,
            0,
            7813,
            8,
            'SCI_A_TRANS',
            [0x2a, 0x0f],
            None,
            None,
            None,
            None
        ),
        'chrys10': ConnectionConfig(
            'CHRYSLER TRANS CAN 11-BIT',
            0,
            500,
            0X7E1,
            0X7E9,
            0XFFFFFFFF,
            0,
            0X40,
            500000,
            6,
            'ISO15765',
            [0x1a, 0x87],
            None,
            None,
            None,
            None
        )
    }
