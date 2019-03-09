# coding=utf-8
import _winreg
import ctypes
import os
import os.path
import platform
from ctypes import *


class Utils:

    @staticmethod
    def hex_dump(items, count):
        n = 0
        lines = []
        for i in range(0, count, 16):
            line = '%04x | ' % i
            n += 16
            for j in range(n - 16, n):
                if j >= count: break
                line += '%02X ' % abs(items[j])
            line += ' ' * (3 * 16 + 7 - len(line)) + ' | '
            for j in range(n - 16, n):
                if j >= count:
                    break
                c = items[j] if not (items[j] < 0x20 or items[j] > 0x7e) else '.'
                line += '%c' % c
            lines.append(line)
        return '\n'.join(lines)

    @staticmethod
    def int_dump(items, count):
        line = ''
        for j in range(count):
            line += '%c ' % items[j]
        return line

    @staticmethod
    def ascii_dump(items, count):
        line = ''
        for j in range(count):
            line += '%c ' % items[j]
        return line


class Flash:

    def __init__(self):

        self.interface = None
        self.msg_id = None

        return

    def close(self):

        # stop flow if it was assigned
        self.flow_stop()

        self.pass_close()

    def open(self, tool, protocol_id, conn_flag, baud_rate):

        # load specific DLL library OR load library found in system (leave first param empty)
        # interface = j2534()

        self.interface = j2534(device_index=tool)

        if not self.interface.initialized:  # check if the interface was properly initialized
            print ("[i] cannot load DLL library")
            return 1

        # print a list of device list
        toollist = self.interface.DeviceList
        tools = len(self.interface.DeviceList)

        for i in range(tools):
            print toollist[i]

        status = self.interface.pass_thru_open()  # open device

        if status == 0:  # check connection status
            print ("[i] Pass-Thru successfully opened")
        else:
            print "[!] error code " + str(status) + " (message " + self.interface.pass_thru_get_last_error() + ")"
            return 2

        # connect to J-2534 using proper interface ID, flags and baud rate
        status = self.interface.pass_thru_connect(protocol_id, conn_flag, baud_rate)

        # check connection status
        if status == 0:

            # read version from the device
            firmaware_version, dll_version, api_version = self.interface.pass_thru_read_version()
            print "[i] firmware version " + firmaware_version
            print "[i] DLL version " + dll_version
            print "[i] API version " + api_version
            print ("[i] Pass-Thru channel successfully opened")
        else:
            print "[!] error code " + str(status) + " (message " + self.interface.pass_thru_get_last_error() + ")"
            return 3

        return True

    def connect(self, protocol_id, flags, baud_rate):
        status = self.interface.pass_thru_connect(protocol_id, flags, baud_rate)

        if status == 0:
            print "[i] Pass-Thru channel open"

            # read version from the device
            firmaware_version, dll_version, api_version = self.interface.pass_thru_read_version()

            print "[i] firmware version " + firmaware_version
            print "[i] DLL version " + dll_version
            print "[i] API version " + api_version
        else:
            print "[!] ERROR! Opening Pass-Thru channel"

    def disconnect(self):
        status = self.interface.pass_thru_disconnect()

        if status == 0:
            print "[i] Pass-Thru channel closed"
        else:
            print "[!] ERROR! Closing Pass-Thru channel"

    def pass_close(self):
        status = self.interface.pass_thru_disconnect()  # disconnect main connection channel with status

        if status == 0:
            print "[i] Pass-Thru channel closed"
        else:
            print "[!] ERROR! Closing Pass-Thru channel"

        status = self.interface.pass_thru_close()  # close device connection with status

        if status == 0:
            print "[i] Pass-Thru device closed"
        else:
            print "[!] ERROR! Closing Pass-Thru device"

    def flow_start(self, transmit_id, receive_id):

        # Setup Flow Control Filter
        mask_message = self.interface.create_passtrhu_msg_struc(Protocols.ISO15765, 0, 0, 0, 4, 0, [0xff, 0xff, 0xff,
                                                                                                    0xff])
        pattern_message = self.interface.create_passtrhu_msg_struc(Protocols.ISO15765, 0, 0, 0, 4, 0, receive_id)

        # flow control tx flag has to be set with drew-tech and set to 0 with intrepid
        flow_control_message = self.interface.create_passtrhu_msg_struc(Protocols.ISO15765, 0,
                                                                        TxFlags.ISO15765_FRAME_PAD, 0, 4,
                                                                        0, transmit_id)

        # YOU NEED TO SET PROPER filter_type AND message_id values
        err, self.msg_id = self.interface.pass_thru_start_msg_filter(Filters.FLOW_CONTROL_FILTER, mask_message,
                                                                     pattern_message, flow_control_message)
        if err == 0:
            print "[i] Flow control filter has been set"
            self.flow_initialized = True

        else:
            print "[!] ERROR! setting flow control filter"
            self.flow_initialized = False

        return self.flow_initialized

    def flow_stop(self):
        err = self.interface.pass_thru_stop_msg_filter(self.msg_id)
        if err == 0:
            print "[i] Flow control filter has been stopped"
        else:
            print "[!] ERROR! Stopping flow control filter"

    def write(self, protocol_id, tx_flag, payload, size, delay):

        print "[i] attempting to write message"
        message_write = self.interface.create_passtrhu_msg_struc(protocol_id, 0, tx_flag, 0, size, 0, payload)
        err = self.interface.pass_thru_write_msgs(message_write, 1,
                                                  delay)  # Write message to J2534 device with error check

        if err == 0:
            print "[i] Write message completed successfully"
        else:
            print "[!] ERROR! Writing message"

    def clear_tx(self):
        err = self.interface.pass_thru_ioctl(Ioctls.CLEAR_TX_BUFFER, 0, 0)
        if err == 0:
            print "[i] TX buffer has been cleared"
        else:
            print "[!] ERROR! clearing TX buffer"

    def clear_rx(self):
        err = self.interface.pass_thru_ioctl(Ioctls.CLEAR_RX_BUFFER, 0, 0)
        if err == 0:
            print "[i] RX buffer has been cleared"
        else:
            print "[!] ERROR! clearing RX buffer"

    def can_vin(self):

        print "[i] Attempting to write message"

        payload = [0x00, 0x00, 0x07, 0xe0, 0x1a, 0x90]

        # Attempt to read vin # 0x7e0-0x1a-0x90
        message_write = self.interface.create_passtrhu_msg_struc(Protocols.ISO15765, 0,
                                                                 TxFlags.ISO15765_FRAME_PAD, 0, 6, 0, payload)
        err = self.interface.pass_thru_write_msgs(message_write, 1,
                                                  500)  # Write message to J2534 device with error check

        if err == 0:
            print "[i] Write message completed successfully"
        else:
            print "[!] ERROR! Writing message"

        # Create receive message structure
        message_read = self.interface.create_passtrhu_msg_struc(Protocols.ISO15765, 0, 0, 0, 0, 0, [])

        self.clear_tx()  # Clear RX and TX buffers
        self.clear_rx()  # Clear RX and TX buffers

        self.interface.pass_thru_read_msgs(message_read, 1, 500)  # Read Messages
        self.interface.pass_thru_read_msgs(message_read, 1, 500)  # Read Messages

        # message_read.dump()

        get_vin = message_read.slice_me(0, 23)
        get_vin = get_vin[6:23]

        vin = Utils.int_dump(get_vin, len(get_vin))
        vin = vin.replace(' ', '', 16)

        print "[i] Current Vin # " + vin


class PASSTHRU_MSG(ctypes.Structure):
    _fields_ = [
        ("ProtocolID", c_ulong),  # vehicle network protocol
        ("RxStatus", c_ulong),  # receive message status
        ("TxFlags", c_ulong),  # transmit message flags
        ("Timestamp", c_ulong),  # receive message timestamp(in microseconds)
        ("DataSize", c_ulong),  # byte size of message payload in the Data array
        ("ExtraDataIndex", c_ulong),  # start of extra data(i.e. CRC, checksum, etc) in Data array
        ("Data", c_ubyte * 4128)  # message payload or data
    ]

    def dump(self):
        print "ProtocolID = " + str(self.ProtocolID)
        print "RxStatus = " + str(self.RxStatus)
        print "TxFlags = " + str(self.TxFlags)
        print "Timestamp = " + str(self.Timestamp)
        print "DataSize = " + str(self.DataSize)
        print "ExtraDataIndex = " + str(self.ExtraDataIndex)
        print Utils.hex_dump(self.Data, self.DataSize)

    def slice_me(self, start_index, end_index):
        global data
        data = self.DataSize
        if start_index >= data or end_index > data:
            return False

        return self.Data[start_index:end_index]


class SBYTE_ARRAY(ctypes.Structure):
    _fields_ = [
        ("NumOfBytes", c_ulong),  # Number of functional addresses in array
        ("BytePtr", ctypes.POINTER(c_ubyte))  # pointer to functional address array
    ]


class SCONFIG(ctypes.Structure):
    _fields_ = [
        ("Parameter", c_ulong),  # Name of configuration parameter
        ("Value", c_ulong)  # Value of configuration parameter
    ]


class SCONFIG_LIST(ctypes.Structure):
    _fields_ = [
        ("NumOfParams", c_ulong),  # size of SCONFIG array
        ("ConfigPtr", ctypes.POINTER(SCONFIG))  # array containing configuration item(s)
    ]


class Protocols:
    J1850VPW = 0x01
    J1850PWM = 0x02
    ISO9141 = 0x03
    ISO14230 = 0x04
    CAN = 0x05
    ISO15765 = 0x06
    SCI_A_ENGINE = 0x07
    SCI_A_TRANS = 0x08
    SCI_B_ENGINE = 0x09
    SCI_B_TRANS = 0x0A

    def __init__(self):
        return


class BaudRate:
    ISO9141 = 10400
    ISO9141_10400 = 10400
    ISO9141_10000 = 10000
    ISO14230 = 10400
    ISO14230_10400 = 10400
    ISO14230_10000 = 10000
    J1850PWM = 41600
    J1850PWM_41600 = 41600
    J1850PWM_83300 = 83300
    J1850VPW = 10400
    J1850VPW_10400 = 10400
    J1850VPW_41600 = 41600
    CAN = 500000
    CAN_125000 = 125000
    CAN_250000 = 250000
    CAN_500000 = 500000
    ISO15765 = 500000
    ISO15765_125000 = 125000
    ISO15765_250000 = 250000
    ISO15765_500000 = 500000

    def __init__(self):
        return


class Ioctls:
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

    def __init__(self):
        return


class Errors:
    STATUS_NOERROR = 0x00
    ERR_NOT_SUPPORTED = 0x01
    ERR_INVALID_CHANNEL_ID = 0x02
    ERR_INVALID_PROTOCOL_ID = 0x03
    ERR_NULL_PARAMETER = 0x04
    ERR_INVALID_FLAGS = 0x06
    ERR_FAILED = 0x07
    ERR_DEVICE_NOT_CONNECTED = 0x08
    ERR_TIMEOUT = 0x09
    ERR_INVALID_MSG = 0x0A
    ERR_INVALID_TIME_INTERVAL = 0x0B
    ERR_EXCEEDED_LIMIT = 0x0C
    ERR_INVALID_MSG_ID = 0x0D
    ERR_DEVICE_IN_USE = 0x0E
    ERR_INVALID_IOCTL_ID = 0x0F
    ERR_BUFFER_EMPTY = 0x10
    ERR_BUFFER_FULL = 0x11
    ERR_BUFFER_OVERFLOW = 0x12
    ERR_PIN_INVALID = 0x13
    ERR_CHANNEL_IN_USE = 0x14
    ERR_MSG_PROTOCOL_ID = 0x15
    ERR_INVALID_FILTER_ID = 0x16
    ERR_NO_FLOW_CONTROL = 0x17
    ERR_NOT_UNIQUE = 0x18
    ERR_INVALID_BAUDRATE = 0x19
    ERR_INVALID_DEVICE_ID = 0x1A

    def __init__(self):
        return


class Filters:
    PASS_FILTER = 0x01
    BLOCK_FILTER = 0x02
    FLOW_CONTROL_FILTER = 0x03

    def __init__(self):
        return


class Voltages:
    SHORT_TO_GROUND = 0xFFFFFFFE
    VOLTAGE_OFF = 0xFFFFFFFF

    def __init__(self):
        return


class PinNumber:
    AUX = 0
    PIN_6 = 6
    PIN_9 = 9
    PIN_11 = 11
    PIN_12 = 12
    PIN_13 = 13
    PIN_14 = 14
    PIN_15 = 15

    def __init__(self):
        return


class Flags:
    # Loopback setting (ioctl GET_CONFIG/SET_CONFIG: parameter LOOPBACK):
    OFF = 0x00
    ON = 0x01

    # Data bits setting (ioctl GET_CONFIG/SET_CONFIG: parameter DATA_BITS):
    DATA_BITS_8 = 0x00
    DATA_BITS_7 = 0x01

    # Parity setting (ioctl GET_CONFIG/SET_CONFIG: parameter PARITY):
    NO_PARITY = 0x00
    ODD_PARITY = 0x01
    EVEN_PARITY = 0x02

    # J1850-PWM (ioctl GET_CONFIG/SET_CONFIG: parameter NETWORK_LINE):
    BUS_NORMAL = 0x00
    BUS_PLUS = 0x01
    BUS_MINUS = 0x02

    def __init__(self):
        return


class ConnectFlags:
    CAN_29BIT_ID = 0x00000100
    ISO9141_NO_CHECKSUM = 0x00000200
    CAN_ID_BOTH = 0x00000800
    ISO9141_K_LINE_ONLY = 0x00001000

    def __init__(self):
        return


class RxStatus:
    TX_MSG_TYPE = 0x00000001
    START_OF_MESSAGE = 0x00000002
    ISO15765_FIRST_FRAME = 0x00000002
    ISO15765_EXT_ADDR = 0x00000080
    RX_BREAK = 0x00000004
    TX_DONE = 0x00000008
    ISO15765_PADDING_ERROR = 0x00000010
    ISO15765_ADDR_TYPE = 0x00000080

    def __init__(self):
        return


class TxFlags:
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

    def __init__(self):
        return


class Loader:

    def __init__(self):

        if platform.architecture()[0] == '32bit':
            self._PASSTHRU_REG = r"Software\\PassThruSupport.04.04\\"
        else:
            self._PASSTHRU_REG = r"Software\\Wow6432Node\\PassThruSupport.04.04\\"

    def get_device_list(self):

        try:

            base_key = _winreg.OpenKeyEx(_winreg.HKEY_LOCAL_MACHINE, self._PASSTHRU_REG)

            count = _winreg.QueryInfoKey(base_key)[0]

            if count == 0:
                return False

            J2534_Device_Reg_Info = []

            for i in range(count):
                DeviceKey = _winreg.OpenKeyEx(base_key, _winreg.EnumKey(base_key, i))
                Name = _winreg.QueryValueEx(DeviceKey, 'Name')[0]
                FunctionLibrary = _winreg.QueryValueEx(DeviceKey, 'FunctionLibrary')[0]
                J2534_Device_Reg_Info.append((Name, FunctionLibrary))

            return J2534_Device_Reg_Info

        except WindowsError as e:

            return False

    def load_dll(dll_path=None):

        dir = os.getcwd()
        path, name = os.path.split(dll_path)

        if path is not None:
            try:
                os.chdir(path)
            except:
                pass  # Specified directory was not found, but it could have been empty...
            else:
                # Some DLL's are loaded "manually" so we add installDir to the PATH in
                # order to allow the OS to find them later when needed
                os.environ["PATH"] += os.pathsep + path

        loadedDll = None  # Load our dll and all dependencies

        try:
            # Windows supports all dll
            dllFile = name
            loadedDll = ctypes.WinDLL(dllFile)
        except Exception as e:
            print(e)
            print("Could be a missing dependancy dll for '%s'." % dllFile)
            print("(Directory for dll: '%s')\n" % dll_path)
            os.chdir(dir)
            return False

        os.chdir(dir)
        return loadedDll


class j2534:

    def __init__(self, dll_path=None, device_index=0):

        self._pPassThruDisconnect = None

        # load default devices
        dll_loader = Loader()

        self.initialized = False

        # device ID
        self._hDeviceID = ctypes.c_ulong(0)

        # channel ID
        self._ChannelID = ctypes.c_ulong(0)

        # load the provided DLL library
        if dll_path:
            self.initialized = self.load_dll(dll_path)
        # load system DLL library
        else:

            result = self.DeviceList = dll_loader.get_device_list()

            if result is not False and len(self.DeviceList) > 0:
                name, dllpath = self.DeviceList[device_index]
                self.initialized = self.load_dll(dllpath)

    def pass_thru_open(self, device_name=None):

        if device_name is None:
            return self._pPassThruOpen(None, ctypes.byref(self._hDeviceID))
        else:
            return self._pPassThruOpen(c_char_p(device_name), ctypes.byref(self._hDeviceID))

    def pass_thru_close(self):

        error = self._pPassThruClose(self._hDeviceID)

        # reset device handle
        self._hDeviceID = ctypes.c_ulong(0)

        return error

    def pass_thru_connect(self, protocol_id, flags, baud_rate):

        return self._pPassThruConnect(self._hDeviceID, ctypes.c_ulong(protocol_id), ctypes.c_ulong(flags),
                                      ctypes.c_ulong(baud_rate), ctypes.byref(self._ChannelID))

    def pass_thru_disconnect(self):

        if self._pPassThruDisconnect is None:
            return 1

        return self._pPassThruDisconnect(self._ChannelID)

    def pass_thru_read_version(self):

        f_ver = create_string_buffer(80)
        d_ver = create_string_buffer(80)
        a_ver = create_string_buffer(80)

        self._pPassThruReadVersion(self._hDeviceID, f_ver, d_ver, a_ver)

        return f_ver.value, d_ver.value, a_ver.value

    def pass_thru_get_last_error(self):

        err = create_string_buffer(80)

        self._pPassThruGetLastError(err)

        return err.value

    def create_passtrhu_msg_struc(self, protocol_id, rx_status, tx_flags, timestamp, data_size, extra_data_index, data):

        struct = PASSTHRU_MSG()
        data_buffer = (ctypes.c_ubyte * 4128)(*data)

        struct.ProtocolID = ctypes.c_ulong(protocol_id)
        struct.RxStatus = ctypes.c_ulong(rx_status)
        struct.TxFlags = ctypes.c_ulong(tx_flags)
        struct.Timestamp = ctypes.c_ulong(timestamp)
        struct.DataSize = ctypes.c_ulong(data_size)
        struct.ExtraDataIndex = ctypes.c_ulong(extra_data_index)
        struct.Data = data_buffer

        return struct

    def pass_thru_read_msgs(self, messages, number_of_messages, timeout):

        # number of messages to read, but also number of actual messages read
        err = self._pPassThruReadMsgs(self._ChannelID, ctypes.byref(messages),
                                      ctypes.byref(ctypes.c_ulong(number_of_messages)), ctypes.c_ulong(timeout))

        return err

    def pass_thru_write_msgs(self, messages, number_of_messages, timeout):

        return self._pPassThruWriteMsgs(self._ChannelID, ctypes.byref(messages), ctypes.c_ulong(number_of_messages),
                                        ctypes.c_ulong(timeout))

    def pass_thru_start_msg_filter(self, filter_type, mask_message, pattern_message, flow_control_message):

        message_id_ref = ctypes.c_ulong(0)

        err = self._pPassThruStartMsgFilter(self._ChannelID, ctypes.c_ulong(filter_type), ctypes.byref(mask_message),
                                            ctypes.byref(pattern_message), ctypes.byref(flow_control_message),
                                            ctypes.byref(message_id_ref))

        return err, message_id_ref.value

    def pass_thru_stop_msg_filter(self, message_id):

        return self._pPassThruStopMsgFilter(self._ChannelID, ctypes.c_ulong(message_id))

    def pass_thru_start_periodic_msg(self, message, message_id, time_interval):

        message_id_ref = ctypes.c_ulong(message_id)

        err = self._pPassThruStartPeriodicMsg(self._ChannelID, ctypes.byref(message), ctypes.c_ulong(message_id_ref),
                                              ctypes.c_ulong(time_interval))

        return err, message_id_ref.value

    def pass_thru_stop_periodic_msg(self, message_id):

        return self._pPassThruStopPeriodicMsg(self._ChannelID, ctypes.c_ulong(message_id))

    def pass_thru_ioctl(self, ioctl_id, input, output):

        return self._pPassThruIoctl(self._ChannelID, ctypes.c_ulong(ioctl_id), input, output)

    def pass_thru_set_programming_voltage(self, pin_number, voltage):

        return self._pPassThruSetProgrammingVoltage(self._hDeviceID, ctypes.c_ulong(pin_number),
                                                    ctypes.c_ulong(voltage))

    def load_dll(self, dll_path):

        if not os.path.isfile(dll_path):  # does DLL file even exits?
            return False

        # set current dir to the DLL pathname, so the other dependent libraries are loaded from there
        os.chdir(os.path.dirname(dll_path))

        FUNC_PROTO = ctypes.WINFUNCTYPE
        self._dll = ctypes.WinDLL(dll_path)  # first load library as a WinDLL

        if self._dll is None:
            return False

        # get function pointers
        self._pPassThruOpen = FUNC_PROTO(ctypes.c_long, ctypes.c_char_p, ctypes.POINTER(ctypes.c_ulong))(
            ("PassThruOpen", self._dll))

        # typedef long(*J2534_PassThruClose)(unsigned long DeviceID);			# 0404-API only
        self._pPassThruClose = FUNC_PROTO(ctypes.c_long, ctypes.c_ulong)(("PassThruClose", self._dll))

        self._pPassThruConnect = FUNC_PROTO(ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong,
                                            ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong))(
            ("PassThruConnect", self._dll))

        self._pPassThruDisconnect = FUNC_PROTO(ctypes.c_long, ctypes.c_ulong)(("PassThruDisconnect", self._dll))

        self._pPassThruReadVersion = FUNC_PROTO(ctypes.c_long, ctypes.c_ulong, c_char_p, c_char_p, c_char_p)(
            ("PassThruReadVersion", self._dll))

        self._pPassThruGetLastError = FUNC_PROTO(ctypes.c_long, c_char_p)(("PassThruGetLastError", self._dll))

        self._pPassThruReadMsgs = FUNC_PROTO(ctypes.c_long, ctypes.c_ulong, ctypes.POINTER(PASSTHRU_MSG),
                                             ctypes.POINTER(ctypes.c_ulong), ctypes.c_ulong)(
            ("PassThruReadMsgs", self._dll))

        self._pPassThruStartMsgFilter = FUNC_PROTO(ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong,
                                                   ctypes.POINTER(PASSTHRU_MSG), ctypes.POINTER(PASSTHRU_MSG),
                                                   ctypes.POINTER(PASSTHRU_MSG), ctypes.POINTER(ctypes.c_ulong))(
            ("PassThruStartMsgFilter", self._dll))

        self._pPassThruStopMsgFilter = FUNC_PROTO(ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong)(
            ("PassThruStopMsgFilter", self._dll))

        self._pPassThruWriteMsgs = FUNC_PROTO(ctypes.c_long, ctypes.c_ulong, ctypes.POINTER(PASSTHRU_MSG),
                                              ctypes.POINTER(ctypes.c_ulong), ctypes.c_ulong)(
            ("PassThruWriteMsgs", self._dll))

        self._pPassThruStartPeriodicMsg = FUNC_PROTO(ctypes.c_long, ctypes.c_ulong, ctypes.POINTER(PASSTHRU_MSG),
                                                     ctypes.POINTER(ctypes.c_ulong), ctypes.c_ulong)(
            ("PassThruStartPeriodicMsg", self._dll))

        self._pPassThruStopPeriodicMsg = FUNC_PROTO(ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong)(
            ("PassThruStopPeriodicMsg", self._dll))

        self._pPassThruIoctl = FUNC_PROTO(ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
                                          ctypes.c_void_p)(("PassThruIoctl", self._dll))

        self._pPassThruSetProgrammingVoltage = FUNC_PROTO(ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong,
                                                          ctypes.c_ulong)(("PassThruSetProgrammingVoltage", self._dll))

        return True


if __name__ == '__main__':

    flash = Flash()

    result = flash.open(1, Protocols.ISO15765, ConnectFlags.CAN_ID_BOTH, BaudRate.ISO15765_500000)

    if result is not True:
        print "[!] error code %i" % result
        exit(result)

    result = flash.flow_start([0x00, 0x00, 0x07, 0xe0], [0x00, 0x00, 0x07, 0xe8])

    # detect failure
    if result is False:
        exit(1)

    flash.can_vin()

    flash.close()

