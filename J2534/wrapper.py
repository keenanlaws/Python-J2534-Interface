import ctypes as ct
from typing import Any

from .Define import IoctlID, Parameter
from .Registry import ToolRegistryInfo
from .dll import PassThru_Data, PassThruMessageStructure, \
    SetConfigurationList, PassThruLibrary, SetConfiguration


class MsgBuilder(PassThruMessageStructure):

    def set_data(self, data):
        self.DataSize = len(data)
        self.Data = PassThru_Data()
        for i in range(self.DataSize):
            self.Data[i] = data[i]

    def SetID(self, transmit_identifier):
        d = self.int_to_list(transmit_identifier)
        self.set_data(d)

    def set_id_and_data(self, _id, data=None):
        data = data or []
        id_and_data = self.int_to_list(_id) + data
        self.set_data(id_and_data)

    @staticmethod
    def int_to_list(_id):
        # print(_id)
        if _id < 255:
            return [_id]
        return [_id >> 24 & 0xFF, _id >> 16 & 0xFF, _id >> 8 & 0xFF, _id & 0xFF]


class PassThruMsgBuilder(MsgBuilder):
    def __init__(self, protocol_id, tx_flags, *args: Any, **kw: Any):
        super().__init__(*args, **kw)
        self.ProtocolID = protocol_id
        self.TxFlags = tx_flags

    def dump(self):
        print(f"ProtocolID = {str(self.ProtocolID)}")
        print(f"RxStatus = {str(self.RxStatus)}")
        print(f"TxFlags = {str(self.TxFlags)}")
        print(f"Timestamp = {str(self.Timestamp)}")
        print(f"DataSize = {str(self.DataSize)}")
        print(f"ExtraDataIndex = {str(self.ExtraDataIndex)}")
        print(self.build_hex_output())

    def build_hex_output(self):
        n = 0
        lines = []
        for i in range(0, self.DataSize, 16):
            line = "%04x | " % i
            n += 16
            for j in range(n - 16, n):
                if j >= self.DataSize:
                    break
                line += "%02X " % abs(self.Data[j])
            line += " " * (3 * 16 + 7 - len(line)) + " | "
            for j in range(n - 16, n):
                if j >= self.DataSize:
                    break
                c = self.Data[j] if 0x20 <= self.Data[j] <= 0x7E else "."
                line += "%c" % c
            lines.append(line)
        return "\n".join(lines)

    def dump_output(self):
        return "".join("%02X" % self.Data[j] for j in range(self.DataSize))


class PassThruMskMsg(PassThruMsgBuilder):
    pass


class PassThruPatternMsg(PassThruMsgBuilder):
    pass


class PassThruFlowControlMsg(PassThruMsgBuilder):
    pass


class GetParameter(SetConfigurationList, Parameter):
    def __init__(self, *args: Any, **kw: Any):
        super().__init__(*args, **kw)
        self.NumOfParams = len(Parameter.USED)
        self.paras = SetConfiguration * self.NumOfParams
        for i in range(self.NumOfParams):
            self.paras()[i].set(Parameter.USED[i])
        self.ConfigPtr = self.paras()


class J2534Api:
    def __init__(self):
        self.canlib = None
        self.dll = None
        self.name = None
        tri = ToolRegistryInfo()
        self._devices = tri.tool_list

    def set_device(self, key=0):
        device = self._devices[key]
        self.name = device[0]
        self.dll = load_j2534_library(device[1])
        self.canlib = PassThruLibrary(self.dll)

    def get_devices(self):
        return self._devices

    def __getattr__(self, name):
        try:
            return getattr(self.canlib, name)
        except AttributeError as e:
            raise AttributeError(f"{e} object has no attribute {name}") from e


japi = J2534Api()


def load_j2534_library(dll_path=None):
    try:
        return ct.WinDLL(dll_path)
    except WindowsError:
        return False


def pt_open():
    device_id = ct.c_ulong()
    if japi.PassThruOpen(ct.c_void_p(None), ct.byref(device_id)) != 0:
        return False
    return device_id.value


def pt_close(device_id):
    return japi.PassThruClose(device_id)


def pt_connect(device_id, protocol_id, flags, baud_rate):
    channel_id = ct.c_ulong()
    if japi.PassThruConnect(device_id, protocol_id, flags, baud_rate, ct.byref(channel_id)) != 0:
        return False
    return channel_id.value


def pt_disconnect(channel_id):
    return japi.PassThruDisconnect(channel_id)


def pt_read_message(channel_id, messages, number_of_messages, message_timeout):
    return japi.PassThruReadMsgs(
        channel_id,
        ct.byref(messages),
        ct.byref(ct.c_ulong(number_of_messages)),
        message_timeout,
    )


def pt_write_message(channel_id, messages, number_of_messages, message_timeout):
    return japi.PassThruWriteMsgs(
        channel_id,
        ct.byref(messages),
        ct.byref(ct.c_ulong(number_of_messages)),
        message_timeout,
    )


def pt_start_periodic_message(channel_id, message_id, time_interval):
    periodic_id = ct.c_ulong()
    if japi.PassThruStartPeriodicMsg(channel_id, ct.byref(message_id), ct.byref(periodic_id), time_interval) != 0:
        return False
    return periodic_id.value


def pt_stop_periodic_message(channel_id, message_id):
    return japi.PassThruStopPeriodicMsg(channel_id, message_id)


def pt_start_ecu_filter(channel_id, protocol_id, mask_id=None, pattern_msgs=None, flow_control=None, tx_flag_0=0):
    """start the msg filter"""
    filter_id = ct.c_ulong()
    if protocol_id == 6:  # check if using protocol ISO15765 if so set flow control filter...
        mask_message = PassThruMskMsg(protocol_id, tx_flag_0, 0)
        mask_message.set_id_and_data(mask_id)

        pattern_message = PassThruPatternMsg(protocol_id, tx_flag_0, 0)
        pattern_message.set_id_and_data(pattern_msgs)

        flow_control_message = PassThruFlowControlMsg(protocol_id, tx_flag_0, 0)
        flow_control_message.set_id_and_data(flow_control)

        if japi.PassThruStartMsgFilter(channel_id, 3, ct.byref(mask_message), ct.byref(pattern_message),
                                       ct.byref(flow_control_message), ct.byref(filter_id)) != 0:
            return False
        return filter_id.value
    elif protocol_id in [
        1,
        7,
        8,
        9,
        10,
    ]:  # check if using protocol j1850 if so set pass filter...
        mask_message = PassThruMskMsg(protocol_id, 0)
        mask_message.SetID(mask_id)
        pattern_message = PassThruPatternMsg(protocol_id, 0)
        pattern_message.SetID(pattern_msgs)
        if japi.PassThruStartMsgFilter(channel_id, 1, ct.byref(mask_message), ct.byref(pattern_message),
                                       ct.c_void_p(None), ct.byref(filter_id)) != 0:
            return False
        return filter_id.value


def pt_start_message_filter(channel_id, filter_type, mask_message, pattern_message, flow_control_message):
    filter_id = ct.c_ulong()
    if japi.PassThruStartMsgFilter(channel_id, filter_type, ct.byref(mask_message), ct.byref(pattern_message),
                                   ct.byref(flow_control_message), ct.byref(filter_id)) != 0:
        return False
    return filter_id.value


def pt_stop_message_filter(channel_id, filter_id):
    return japi.PassThruStopMsgFilter(channel_id, filter_id)


def pt_set_programming_voltage(device_id, pin_number, voltage):
    return japi.PassThruSetProgrammingVoltage(device_id, pin_number, voltage)


def pt_read_version(device_id):
    firmware_version = ct.create_string_buffer(80)
    dll_version = ct.create_string_buffer(80)
    api_version = ct.create_string_buffer(80)
    if japi.PassThruReadVersion(device_id, firmware_version, dll_version, api_version) != 0:
        return ['error', 'error', 'error']
    return [firmware_version.value.decode(), dll_version.value.decode(), api_version.value.decode()]


def pt_get_last_error():
    error_buffer = ct.create_string_buffer(80)
    japi.PassThruGetLastError(error_buffer)
    return error_buffer.value


def pt_ioctl(channel_id, ioctl_id, ioctl_input, output):
    return japi.PassThruIoctl(channel_id, ioctl_id, ioctl_input, output)


def pt_set_config(channel_id, parameters):
    conf = SetConfigurationList()
    conf.NumOfParams = len(parameters)
    elems = (SetConfiguration * len(parameters))()
    conf.ConfigPtr = ct.cast(elems, ct.POINTER(SetConfiguration))
    for num in range(len(parameters)):
        conf.ConfigPtr[num].set_parameter(parameters[num][0])
        conf.ConfigPtr[num].set_value(parameters[num][1])
    ret = pt_ioctl(channel_id, IoctlID.SET_CONFIG, ct.byref(conf), ct.c_void_p(None))
    return ret, conf.ConfigPtr


def read_battery_volts(device_id):
    _voltage = ct.c_ulong()
    if pt_ioctl(device_id, IoctlID.READ_VBATT, ct.c_void_p(None), ct.byref(_voltage)) == 0:
        return _voltage.value / 1000.0
    return False


def read_programming_voltage(channel_id):
    _voltage = ct.c_ulong()
    if pt_ioctl(channel_id, IoctlID.READ_PROG_VOLTAGE, ct.c_void_p(None), ct.byref(_voltage)) != 0:
        return False
    return _voltage.value / 1000.0


def clear_transmit_buffer(channel_id):
    return pt_ioctl(channel_id, IoctlID.CLEAR_TX_BUFFER, ct.c_void_p(None), ct.c_void_p(None))


def clear_receive_buffer(channel_id):
    return pt_ioctl(channel_id, IoctlID.CLEAR_RX_BUFFER, ct.c_void_p(None), ct.c_void_p(None))


def clear_periodic_messages(channel_id):
    return pt_ioctl(
        channel_id,
        IoctlID.CLEAR_PERIODIC_MSGS,
        ct.c_void_p(None),
        ct.c_void_p(None),
    )


def clear_message_filters(channel_id):
    return pt_ioctl(
        channel_id,
        IoctlID.CLEAR_MSG_FILTERS,
        ct.c_void_p(None),
        ct.c_void_p(None),
    )


def clear_functional_message_lookup_table(channel_id):
    return pt_ioctl(
        channel_id,
        IoctlID.CLEAR_FUNCT_MSG_LOOKUP_TABLE,
        ct.c_void_p(None),
        ct.c_void_p(None),
    )
