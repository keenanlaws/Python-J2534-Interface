# ProtocolID
class addBase(object):
    @staticmethod
    def value(*args):
        out = 0
        for i in args:
            out |= i
        return out

    @staticmethod
    def check(flags, *args):
        for i in args:
            if flags & i:
                print(flags & i)
            else:
                return False
        return True


class ProtocolID(object):
    J1850VPW = 1
    J1850PWM = 2
    ISO9141 = 3
    ISO14230 = 4
    CAN = 5
    ISO15765 = 6
    SCI_A_ENGINE = 7
    SCI_A_TRANS = 8
    SCI_B_ENGINE = 9
    SCI_B_TRANS = 10


class Flags(addBase):
    # Flags.value(Flags.CAN_29BIT_ID,Flags.CAN_ID_BOTH)
    NONE = 0
    CAN_29BIT_ID = 0x100
    ISO9141_NO_CHECKSUM = 0x200
    NO_CHECKSUM = 0x200
    CAN_ID_BOTH = 0x800
    ISO9141_K_LINE_ONLY = 0x1000
    LISTEN_ONLY_DT = 0x10000000
    SNIFF_MODE = 0x10000000
    ISO9141_FORD_HEADER = 0x20000000
    ISO9141_NO_CHECKSUM_DT = 0x40000000


class BaudRate(object):
    SCI = 7813
    SCI_HIGHSPEED = 62500
    ISO9141_10400 = 10400
    ISO9141_10000 = 10000
    ISO14230_10400 = 10400
    ISO14230_10000 = 10000
    J1850PWM_41600 = 41600
    J1850PWM_83300 = 83300
    J1850VPW_10400 = 10400
    J1850VPW_41600 = 41600
    CAN_125k = 125000
    CAN_250k = 250000
    CAN_500k = 500000


class FilterType(object):
    PASS_FILTER = 0x00000001
    BLOCK_FILTER = 0x00000002
    FLOW_CONTROL_FILTER = 0x00000003


class Voltage(object):
    SHORT_TO_GROUND = 0xFFFFFFFF
    VOLTAGE_OFF = 0xFFFFFFFE

    @staticmethod
    def value(value):
        # Programming Voltage 
        # 0x00001388 5000mV
        # 0x00004E20 20000mV
        return value


class IoctlID(object):
    GET_CONFIG = 0x01
    SET_CONFIG = 0x02
    READ_VBATT = 0x03
    FIVE_BAUD_INIT = 0x04
    FAST_INIT = 0x05
    CLEAR_TX_BUFFER = 0x07
    CLEAR_RX_BUFFER = 0x08
    CLEAR_PERIODIC_MSGS = 0x09
    CLEAR_MSG_FILTERS = 0x0A
    CLEAR_FUNCT_MSG_LOOKUP_TABLE = 0x0B
    ADD_TO_FUNCT_MSG_LOOKUP_TABLE = 0x0C
    DELETE_FROM_FUNCT_MSG_LOOKUP_TABLE = 0x0D
    READ_PROG_VOLTAGE = 0x0E
    DATA_RATE = 0x01  # 5 500000 	# Baud rate value used for vehicle network. No default value specified.
    LOOPBACK = 0x03  # 0(OFF)/1(ON)	# 0 = Do not echo transmitted messages to the Receive queue. 1 = Echo transmitted messages to the Receive queue.
    NODE_ADDRESS = 0x04  # 0x00-0xFF	# J1850PWM specific, physical address for node of interest in the vehicle network. Default is no nodes are recognized by scan tool.
    NETWORK_LINE = 0x05  # 0(BUS_NORMAL)/1(BUS_PLUS)/2(BUS_MINUS)	# J1850PWM specific, network line(s) active during message transfers. Default value is 0(BUS_NORMAL).
    P1_MIN = 0x06  # 0x0-0xFFFF	# ISO-9141/14230 specific, min. ECU inter-byte time for responses [02.02-API: ms]. Default value is 0 ms. 04.04-API: NOT ADJUSTABLE, 0ms.
    P1_MAX = 0x07  # 0x0/0x1-0xFFFF # ISO-9141/14230 specific, max. ECU inter-byte time for responses [02.02-API: ms, 04.04-API: *0.5ms]. Default value is 20 ms.
    P2_MIN = 0x08  # 0x0-0xFFFF	# ISO-9141/14230 specific, min. ECU response time to a tester request or between ECU responses [02.02-API: ms, 04.04-API: *0.5ms]. 04.04-API: NOT ADJUSTABLE, 0ms. Default value is 25 ms.
    P2_MAX = 0x09  # 0x0-0xFFFF	# ISO-9141/14230 specific, max. ECU response time to a tester request or between ECU responses [02.02-API: ms, 04.04-API: *0.5ms]. 04.04-API: NOT ADJUSTABLE, all messages up to P3_MIN are receoved. Default value is 50 ms.
    P3_MIN = 0x0A  # 0x0-0xFFFF	# ISO-9141/14230 specific, min. ECU response time between end of ECU response and next tester request [02.02-API: ms, 04.04-API: *0.5ms]. Default value is 55 ms.
    P3_MAX = 0x0B  # 0x0-0xFFFF	# ISO-9141/14230 specific, max. ECU response time between end of ECU response and next tester request [02.02-API: ms, 04.04-API: *0.5ms]. 04.04-API: NOT ADJUSTABLE, messages can be sent at anytime after P3_MIN. Default value is 5000 ms.
    P4_MIN = 0x0C  # 0x0-0xFFFF	# ISO-9141/14230 specific, min. tester inter-byte time for a request [02.02-API: ms, 04.04-API: *0.5ms]. Default value is 5 ms.
    P4_MAX = 0x0D  # 0x0-0xFFFF	# ISO-9141/14230 specific, max. tester inter-byte time for a request [02.02-API: ms, 04.04-API: *0.5ms]. 04.04-API: NOT ADJUSTABLE, P4_MIN is always used. Default value is 20 ms.
    W1 = 0x0E  # 0x0-0xFFFF	# ISO 9141 specific, max. time [ms] from the address byte end to synchronization pattern start. Default value is 300 ms.
    W2 = 0x0F  # 0x0-0xFFFF	# ISO 9141 specific, max. time [ms] from the synchronization byte end to key byte 1 start. Default value is 20 ms.
    W3 = 0x10  # 0x0-0xFFFF	# ISO 9141 specific, max. time [ms] between key byte 1 and key byte 2. Default value is 20 ms.
    W4 = 0x11  # 0x0-0xFFFF	# ISO 9141 specific, 02.02-API: max. time [ms] between key byte 2 and its inversion from the tester. Default value is 50 ms.
    W5 = 0x12  # 0x0-0xFFFF	# ISO 9141 specific, min. time [ms] before the tester begins retransmission of the address byte. Default value is 300 ms.
    TIDLE = 0x13  # 0x0-0xFFFF	# ISO 9141 specific, bus idle time required before starting a fast initialization sequence. Default value is W5 value.
    TINL = 0x14  # 0x0-0xFFFF	# ISO 9141 specific, the duration [ms] of the fast initialization low pulse. Default value is 25 ms.
    TWUP = 0x15  # 0x0-0xFFFF	# ISO 9141 specific, the duration [ms] of the fast initialization wake-up pulse. Default value is 50 ms.
    PARITY = 0x16  # 0(NO_PARITY)/1(ODD_PARITY)/2(EVEN_PARITY)	# ISO9141 specific, parity type for detecting bit errors.  Default value is 0(NO_PARITY).
    BIT_SAMPLE_POINT = 0x17  # 0-100	# CAN specific, the desired bit sample point as a percentage of bit time. Default value is 80%.
    SYNCH_JUMP_WIDTH = 0x18  # 0-100	# CAN specific, the desired synchronization jump width as a percentage of the bit time. Default value is 15%.
    W0 = 0x19
    T1_MAX = 0x1A  # 0x0-0xFFFF	# SCI_X_XXXX specific, the max. interframe response delay. Default value is 20 ms.
    T2_MAX = 0x1B  # 0x0-0xFFFF	# SCI_X_XXXX specific, the max. interframe request delay.Default value is 100 ms.
    T4_MAX = 0x1C  # 0x0-0xFFFF	# SCI_X_XXXX specific, the max. intermessage response delay. Default value is 20 ms.
    T5_MAX = 0x1D  # 0x0-0xFFFF	# SCI_X_XXXX specific, the max. intermessage request delay. Default value is 100 ms.
    ISO15765_BS = 0x1E  # 0x0-0xFF	# ISO15765 specific, the block size for segmented transfers.
    ISO15765_STMIN = 0x1F  # 0x0-0xFF	# ISO15765 specific, the separation time for segmented transfers.
    DATA_BITS = 0x20  # 04.04-API only
    FIVE_BAUD_MOD = 0x21
    BS_TX = 0x22
    STMIN_TX = 0x23
    T3_MAX = 0x24
    ISO15765_WFT_MAX = 0x25


class RxStatus(addBase):
    TX_MSG_TYPE = 0x00000001
    START_OF_MESSAGE = 0x00000002
    ISO15765_FIRST_FRAME = 0x00000002  # compat from v0202
    ISO15765_EXT_ADDR = 0x00000080  # Accidentally refered to in spec
    RX_BREAK = 0x00000004
    TX_DONE = 0x00000008
    ISO15765_PADDING_ERROR = 0x00000010
    ISO15765_ADDR_TYPE = 0x00000080


class TxFlags(addBase):
    ISO15765_CAN_ID_29 = 0x00000140
    ISO15765_CAN_ID_11 = 0x00000040
    ISO15765_ADDR_TYPE = 0x00000080
    CAN_29BIT_ID = 0x00000100
    WAIT_P3_MIN_ONLY = 0x00000200
    SWCAN_HV_TX = 0x00000400
    SCI_MODE = 0x00400000
    SCI_TX_VOLTAGE = 0x00800000
    ISO15765_FRAME_PAD = 0x00000040
    TX_NORMAL_TRANSMIT = 0x00000000
    NONE = 0x00000000


class Parameter(object):
    DATA_RATE = 0x01
    # unused                            = 0x02
    LOOPBACK = 0x03
    NODE_ADDRESS = 0x04  # Not supported
    NETWORK_LINE = 0x05  # Not supported
    P1_MIN = 0x06  # Don't use
    P1_MAX = 0x07
    P2_MIN = 0x08  # Don't use
    P2_MAX = 0x09  # Don't use
    P3_MIN = 0x0A
    P3_MAX = 0x0B  # Don't use
    P4_MIN = 0x0C
    P4_MAX = 0x0D  # Don't use
    # See W0 = = 0x19
    W1 = 0x0E
    W2 = 0x0F
    W3 = 0x10
    W4 = 0x11
    W5 = 0x12
    TIDLE = 0x13
    TINIL = 0x14
    TWUP = 0x15
    PARITY = 0x16

    class PARITY_ENUM(object):
        NO_PARITY = 0
        ODD_PARITY = 1
        EVEN_PARITY = 2

    BIT_SAMPLE_POINT = 0x17
    SYNC_JUMP_WIDTH = 0x18
    W0 = 0x19
    T1_MAX = 0x1A  # 0x0-0xFFFF	# SCI_X_XXXX specific, the max. interframe response delay. Default value is 20 ms.
    T2_MAX = 0x1B  # 0x0-0xFFFF	# SCI_X_XXXX specific, the max. interframe request delay.Default value is 100 ms.
    T4_MAX = 0x1C  # 0x0-0xFFFF	# SCI_X_XXXX specific, the max. intermessage response delay. Default value is 20 ms.
    T5_MAX = 0x1D  # 0x0-0xFFFF	# SCI_X_XXXX specific, the max. intermessage request delay. Default value is 100 ms.
    ISO15765_BS = 0x1E
    ISO15765_STMIN = 0x1F
    DATA_BITS = 0x20
    FIVE_BAUD_MOD = 0x21
    BS_TX = 0x22
    STMIN_TX = 0x23
    T3_MAX = 0x24
    ISO15765_WFT_MAX = 0x25
    USED = [
        DATA_RATE, LOOPBACK, NODE_ADDRESS, NETWORK_LINE, P1_MAX, P3_MIN, P4_MIN, \
        W0, W1, W2, W3, W4, W5, TIDLE, TINIL, TWUP, PARITY, BIT_SAMPLE_POINT, SYNC_JUMP_WIDTH, \
        T1_MAX, T2_MAX, T3_MAX, T4_MAX, T5_MAX, \
        ISO15765_BS, ISO15765_STMIN, DATA_BITS, FIVE_BAUD_MOD, BS_TX, STMIN_TX, T3_MAX, ISO15765_WFT_MAX
    ]

