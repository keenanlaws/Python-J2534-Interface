import winreg
import ctypes
import os
import os.path
import platform
from ctypes import *


class Utils:
    def __init__(self):
        return

    @staticmethod
    def pretty_int_to_hex(shitIn):
        ugly = int(shitIn, 16)
        ugly = hex(ugly)
        ugly = "%x" % ugly
        shitOut = ugly
        print(shitOut)
        return shitOut

    @staticmethod
    def hex_dump(items, count):
        n = 0
        lines = []
        for i in range(0, count, 16):
            line = "%04x | " % i
            n += 16
            for j in range(n - 16, n):
                if j >= count:
                    break
                line += "%02X " % abs(items[j])
            line += " " * (3 * 16 + 7 - len(line)) + " | "
            for j in range(n - 16, n):
                if j >= count:
                    break
                c = items[j] if not (items[j] < 0x20 or items[j] > 0x7E) else "."
                line += "%c" % c
            lines.append(line)
        return "\n".join(lines)

    @staticmethod
    def int_dump(items, count):
        line = ""
        for j in range(count):
            line += "%c " % items[j]
        return line

    @staticmethod
    def ascii_dump(items, count):
        line = ""
        for j in range(count):
            line += "%c " % items[j]
        return line

    @staticmethod
    def int_it(items, count):
        line = ""
        for j in range(count):
            line += "%i " % items[j]
        return line

    @staticmethod
    def hex_it(items, count):
        line = ""
        for j in range(count):
            line += "%02X " % items[j]
        return line

    @staticmethod
    def translate_dtc(dtOne, dtTwo):
        dtc_decoded = ""
        dtc_first_char = {0b00: "P", 0b01: "C", 0b10: "B", 0b11: "U"}
        dtc_second_char = {0b00: "0", 0b01: "1", 0b10: "2", 0b11: "3"}
        dtc_last_chars = {
            0b0000: "0",
            0b0001: "1",
            0b0010: "2",
            0b0011: "3",
            0b0100: "4",
            0b0101: "5",
            0b0110: "6",
            0b0111: "7",
            0b1000: "8",
            0b1001: "9",
            0b1010: "A",
            0b1011: "B",
            0b1100: "C",
            0b1101: "D",
            0b1110: "E",
            0b1111: "F",
        }
        dtc_first = dtOne >> 6
        dtc_decoded += dtc_first_char[dtc_first]
        dtc_second = dtOne >> 4 & 0b0011
        dtc_decoded += dtc_second_char[dtc_second]
        dtc_third = dtOne & 0b00001111
        dtc_decoded += dtc_last_chars[dtc_third]
        dtc_fourth = dtTwo >> 4
        dtc_decoded += dtc_last_chars[dtc_fourth]
        dtc_fifth = dtTwo & 0b00001111
        dtc_decoded += dtc_last_chars[dtc_fifth]
        # print dtc_decoded
        return dtc_decoded


class PassThruMsgSetup(ctypes.Structure):
    _fields_ = [
        ("ProtocolID", c_ulong),  # vehicle network protocol
        ("RxStatus", c_ulong),  # receive message status
        ("TxFlags", c_ulong),  # transmit message flags
        ("Timestamp", c_ulong),  # receive message timestamp(in microseconds)
        ("DataSize", c_ulong),  # byte size of message payload in the Data array
        ("ExtraDataIndex", c_ulong),  # start of extra data(i.e. CRC, checksum, etc) in Data array
        ("Data", c_ubyte * 4128),  # message payload or data
    ]

    def dump(self):
        print("ProtocolID = " + str(self.ProtocolID))
        print("RxStatus = " + str(self.RxStatus))
        print("TxFlags = " + str(self.TxFlags))
        print("Timestamp = " + str(self.Timestamp))
        print("DataSize = " + str(self.DataSize))
        print("ExtraDataIndex = " + str(self.ExtraDataIndex))
        print(Utils.hex_dump(self.Data, self.DataSize))

    def dump_data(self):
        return Utils.hex_it(self.Data, self.DataSize)

    def data_size(self):
        return self.DataSize

    def slice_me(self, start_index, end_index):
        data = self.DataSize
        if data != 0:
            if start_index >= data or end_index > data:
                return False
            return self.Data[start_index:end_index]
        else:
            # jbox.pass_thru_disconnect()
            # jbox.pass_thru_close()
            return False


class StructureByteArray(ctypes.Structure):
    _fields_ = [
        ("NumOfBytes", c_ulong),  # Number of functional addresses in array
        ("BytePtr", ctypes.POINTER(c_ubyte)),  # pointer to functional address array
    ]


class StructureConfig(ctypes.Structure):
    _fields_ = [
        ("Parameter", c_ulong),  # Name of configuration parameter
        ("Value", c_ulong),  # Value of configuration parameter
    ]


class StructureConfigList(ctypes.Structure):
    _fields_ = [
        ("NumOfParams", c_ulong),  # size of SCONFIG array
        (
            "ConfigPtr",
            ctypes.POINTER(StructureConfig),
        ),  # array containing configuration item(s)
    ]


class DllLoader:
    def __init__(self):
        self.J2534_Device_Reg_Info = []

        if platform.architecture()[0] == "32bit":
            self._PASSTHRU_REG = r"Software\\PassThruSupport.04.04\\"
        else:
            self._PASSTHRU_REG = r"Software\\Wow6432Node\\PassThruSupport.04.04\\"
        return

    def get_device_list(self):
        try:

            base_key = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, self._PASSTHRU_REG)

            count = winreg.QueryInfoKey(base_key)[0]

            if count == 0:
                return False

            for i in range(count):
                DeviceKey = winreg.OpenKeyEx(base_key, winreg.EnumKey(base_key, i))
                Name = winreg.QueryValueEx(DeviceKey, "Name")[0]
                FunctionLibrary = winreg.QueryValueEx(DeviceKey, "FunctionLibrary")[0]
                self.J2534_Device_Reg_Info.append((Name, FunctionLibrary))

            return self.J2534_Device_Reg_Info

        except WindowsError as e:

            return False

    def load_dll(self, dll_path=None):

        dir_ = os.getcwd()
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

        try:
            # Windows supports all dll
            dllFile = name
            loadedDll = ctypes.WinDLL(dllFile)
        except Exception as e:
            print(e)
            print("Could be a missing dependency dll for '%s'." % dllFile)
            print("(Directory for dll: '%s')\n" % dll_path)
            os.chdir(dir_)
            return False

        os.chdir(dir_)
        return loadedDll


class PassThru:
    def __init__(self, dll_path=None, device_index=0):

        self._pPassThruDisconnect = None

        # load default devices
        dll_loader = DllLoader()

        result = self.DeviceList = dll_loader.get_device_list()

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
            if result is not False and len(self.DeviceList) > 0:
                self.name, self.dllpath = self.DeviceList[device_index]
                self.initialized = self.load_dll(self.dllpath)
        return

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

    def pass_thru_version(self):

        f_ver = create_string_buffer(80)
        d_ver = create_string_buffer(80)
        a_ver = create_string_buffer(80)

        self._pPassThruReadVersion(self._hDeviceID, f_ver, d_ver, a_ver)

        return f_ver.value, d_ver.value, a_ver.value

    def pass_thru_last_error(self):

        err = create_string_buffer(80)

        self._pPassThruGetLastError(err)

        return err.value

    def pass_thru_structure(self, protocol_id, rx_status, tx_flags, timestamp, data_size, extra_data_index, data):

        struct = PassThruMsgSetup()
        data_buffer = (ctypes.c_ubyte * 4128)(*data)

        struct.ProtocolID = ctypes.c_ulong(protocol_id)
        struct.RxStatus = ctypes.c_ulong(rx_status)
        struct.TxFlags = ctypes.c_ulong(tx_flags)
        struct.Timestamp = ctypes.c_ulong(timestamp)
        struct.DataSize = ctypes.c_ulong(data_size)
        struct.ExtraDataIndex = ctypes.c_ulong(extra_data_index)
        struct.Data = data_buffer

        return struct

    def pass_thru_read(self, messages, number_of_messages, timeout):

        # number of messages to read, but also number of actual messages read
        err = self._pPassThruReadMsgs(
            self._ChannelID,
            ctypes.byref(messages),
            ctypes.byref(ctypes.c_ulong(number_of_messages)),
            ctypes.c_ulong(timeout),
        )

        return err

    def pass_thru_write(self, messages, number_of_messages, timeout):

        err = self._pPassThruWriteMsgs(
            self._ChannelID,
            ctypes.byref(messages),
            ctypes.byref(ctypes.c_ulong(number_of_messages)),
            ctypes.c_ulong(timeout),
        )
        return err

    def pass_thru_start_msg_filter(self, filter_type, mask_message, pattern_message, flow_control_message):

        message_id_ref = ctypes.c_ulong(0)

        err = self._pPassThruStartMsgFilter(
            self._ChannelID,
            ctypes.c_ulong(filter_type),
            ctypes.byref(mask_message),
            ctypes.byref(pattern_message),
            ctypes.byref(flow_control_message),
            ctypes.byref(message_id_ref),
        )

        return err, message_id_ref.value

    def pass_thru_start_pass_block_filter(self, filter_type, mask_message, pattern_message):

        message_id_ref = ctypes.c_ulong(0)

        err = self._pPassThruStartPassBlockFilter(
            self._ChannelID,
            ctypes.c_ulong(filter_type),
            ctypes.byref(mask_message),
            ctypes.byref(pattern_message),
            ctypes.c_void_p(None),
            ctypes.byref(message_id_ref),
        )

        return err, message_id_ref.value

    def pass_thru_stop_msg_filter(self, message_id):

        return self._pPassThruStopMsgFilter(self._ChannelID, ctypes.c_ulong(message_id))

    def pass_thru_start_periodic_msg(self, message, message_id, time_interval):

        message_id_ref = ctypes.c_ulong(message_id)

        err = self._pPassThruStartPeriodicMsg(
            self._ChannelID,
            ctypes.byref(message),
            ctypes.c_ulong(message_id_ref),
            ctypes.c_ulong(time_interval),
        )

        return err, message_id_ref.value

    def pass_thru_stop_periodic_msg(self, message_id):

        return self._pPassThruStopPeriodicMsg(
            self._ChannelID, ctypes.c_ulong(message_id)
        )

    def pass_thru_ioctl(self, ioctl_id, input, output):

        return self._pPassThruIoctl(
            self._ChannelID, ctypes.c_ulong(ioctl_id), input, output
        )

    def pass_thru_get_vbatt(self, ioctl_id):
        _voltage = ctypes.c_ulong()
        self._pPassThruIoctl(
            self._hDeviceID,
            ctypes.c_ulong(ioctl_id),
            ctypes.c_void_p(None),
            ctypes.byref(_voltage),
        )
        self.vbat = _voltage.value
        self.vbat = self.vbat / 1000.0
        return self.vbat

    def pass_thru_set_programming_voltage(self, pin_number, voltage):

        return self._pPassThruSetProgrammingVoltage(
            self._hDeviceID, ctypes.c_ulong(pin_number), ctypes.c_ulong(voltage)
        )

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
        self._pPassThruOpen = FUNC_PROTO(
            ctypes.c_long, ctypes.c_char_p, ctypes.POINTER(ctypes.c_ulong)
        )(("PassThruOpen", self._dll))

        # typedef long(*J2534_PassThruClose)(unsigned long DeviceID);			# 0404-API only
        self._pPassThruClose = FUNC_PROTO(ctypes.c_long, ctypes.c_ulong)(
            ("PassThruClose", self._dll)
        )

        try:
            ptr = getattr(self._dll, "PassThruConnect_0202")

            self._pPassThruConnect_0202 = FUNC_PROTO(
                ctypes.c_long,
                ctypes.c_ulong,
                ctypes.c_ulong,
                ctypes.POINTER(ctypes.c_ulong),
            )(("PassThruConnect_0202", self._dll))
        except:
            self._pPassThruConnect_0202 = None
        try:
            ptr = getattr(self._dll, "PassThruConnect_0404")
            self._pPassThruConnect_0404 = FUNC_PROTO(
                ctypes.c_long,
                ctypes.c_ulong,
                ctypes.c_ulong,
                ctypes.c_ulong,
                ctypes.c_ulong,
                ctypes.POINTER(ctypes.c_ulong),
            )(("PassThruConnect_0404", self._dll))
        except:
            self._pPassThruConnect_0404 = None

        self._pPassThruConnect = FUNC_PROTO(
            ctypes.c_long,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong),
        )(("PassThruConnect", self._dll))

        self._pPassThruDisconnect = FUNC_PROTO(ctypes.c_long, ctypes.c_ulong)(
            ("PassThruDisconnect", self._dll)
        )

        try:
            ptr = getattr(self._dll, "PassThruReadVersion_0202")
            self._pPassThruReadVersion_0202 = FUNC_PROTO(
                ctypes.c_long, c_char_p, c_char_p, c_char_p
            )(("PassThruReadVersion_0202", self._dll))
        except:
            self._pPassThruReadVersion_0202 = None
        try:
            ptr = getattr(self._dll, "PassThruReadVersion_0202")
            self._pPassThruReadVersion_0404 = FUNC_PROTO(
                ctypes.c_long, ctypes.c_ulong, c_char_p, c_char_p, c_char_p
            )(("PassThruReadVersion_0404", self._dll))
        except:
            self._pPassThruReadVersion_0404 = None

        self._pPassThruReadVersion = FUNC_PROTO(
            ctypes.c_long, ctypes.c_ulong, c_char_p, c_char_p, c_char_p
        )(("PassThruReadVersion", self._dll))

        self._pPassThruGetLastError = FUNC_PROTO(ctypes.c_long, c_char_p)(
            ("PassThruGetLastError", self._dll)
        )

        self._pPassThruReadMsgs = FUNC_PROTO(
            ctypes.c_long,
            ctypes.c_ulong,
            ctypes.POINTER(PassThruMsgSetup),
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.c_ulong,
        )(("PassThruReadMsgs", self._dll))

        self._pPassThruStartMsgFilter = FUNC_PROTO(
            ctypes.c_long,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.POINTER(PassThruMsgSetup),
            ctypes.POINTER(PassThruMsgSetup),
            ctypes.POINTER(PassThruMsgSetup),
            ctypes.POINTER(ctypes.c_ulong),
        )(("PassThruStartMsgFilter", self._dll))

        self._pPassThruStartPassBlockFilter = FUNC_PROTO(
            ctypes.c_long,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.POINTER(PassThruMsgSetup),
            ctypes.POINTER(PassThruMsgSetup),
            ctypes.POINTER(None),
            ctypes.POINTER(ctypes.c_ulong),
        )(("PassThruStartMsgFilter", self._dll))

        self._pPassThruStopMsgFilter = FUNC_PROTO(
            ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong
        )(("PassThruStopMsgFilter", self._dll))

        self._pPassThruWriteMsgs = FUNC_PROTO(
            ctypes.c_long,
            ctypes.c_ulong,
            ctypes.POINTER(PassThruMsgSetup),
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.c_ulong,
        )(("PassThruWriteMsgs", self._dll))

        self._pPassThruStartPeriodicMsg = FUNC_PROTO(
            ctypes.c_long,
            ctypes.c_ulong,
            ctypes.POINTER(PassThruMsgSetup),
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.c_ulong,
        )(("PassThruStartPeriodicMsg", self._dll))

        self._pPassThruStopPeriodicMsg = FUNC_PROTO(
            ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong
        )(("PassThruStopPeriodicMsg", self._dll))

        self._pPassThruIoctl = FUNC_PROTO(
            ctypes.c_long,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_void_p,
            ctypes.c_void_p,
        )(
            ("PassThruIoctl", self._dll)
        )  # 0202-API
        try:
            ptr = getattr(self._dll, "PassThruSetProgrammingVoltage_0202")
            self._pPassThruSetProgrammingVoltage_0202 = FUNC_PROTO(
                ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong
            )(("PassThruSetProgrammingVoltage_0202", self._dll))
        except:
            self._pPassThruSetProgrammingVoltage_0202 = None  # 0404-API
        try:
            ptr = getattr(self._dll, "PassThruSetProgrammingVoltage_0404")
            self._pPassThruSetProgrammingVoltage_0404 = FUNC_PROTO(
                ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong
            )(("PassThruSetProgrammingVoltage_0404", self._dll))
        except:
            self._pPassThruSetProgrammingVoltage_0202 = None

        self._pPassThruSetProgrammingVoltage = FUNC_PROTO(
            ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong
        )(("PassThruSetProgrammingVoltage", self._dll))

        return True


class Protocols:
    def __init__(self):
        return

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


class BaudRate:
    def __init__(self):
        return

    SCI = 7813
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


class Ioctls:
    def __init__(self):
        return

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


class Filters:
    def __init__(self):
        return

    PASS_FILTER = 0x01
    BLOCK_FILTER = 0x02
    FLOW_CONTROL_FILTER = 0x03


class Voltages:
    def __init__(self):
        return

    SHORT_TO_GROUND = 0xFFFFFFFE
    VOLTAGE_OFF = 0xFFFFFFFF


class PinNumber:
    def __init__(self):
        return

    AUX = 0
    PIN_6 = 6
    PIN_9 = 9
    PIN_11 = 11
    PIN_12 = 12
    PIN_13 = 13
    PIN_14 = 14
    PIN_15 = 15


class Flags:
    def __init__(self):
        return

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


class ConnectFlags:
    def __init__(self):
        return

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


class TxFlags:
    def __init__(self):
        return

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
