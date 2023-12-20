import ctypes as ct
from typing import Any

from .Define import IoctlID, Parameter
from .Registry import ToolRegistryInfo
from .dll import PassThru_Data, PassThruMessageStructure, \
    SetConfigurationList, PassThruLibrary, SetConfiguration


class MsgBuilder(PassThruMessageStructure):
    def build_transmit_data_block(self, data):
        self.DataSize = len(data)
        self.Data = PassThru_Data()
        for i in range(self.DataSize):
            self.Data[i] = data[i]

    def set_identifier(self, transmit_identifier):
        identifier = self.int_to_list(transmit_identifier)
        self.build_transmit_data_block(identifier)

    def set_identifier_and_data(self, _id, data=None):
        data = data or []
        id_and_data = self.int_to_list(_id) + data
        self.build_transmit_data_block(id_and_data)

    @staticmethod
    def int_to_list(_id):
        if _id < 255:
            return [_id]
        return [_id >> 24 & 0xFF, _id >> 16 & 0xFF, _id >> 8 & 0xFF, _id & 0xFF]


class PassThruMsgBuilder(MsgBuilder):  # sets up the message structure
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

    def process_hex_output_line(self, line_start_index, line_end_index):
        line = "%04x | " % line_start_index
        for j in range(line_start_index, line_end_index):
            if j >= self.DataSize:
                break
            line += "%02X " % abs(self.Data[j])
        line += " " * (3 * 16 + 7 - len(line)) + " | "
        for j in range(line_start_index, line_end_index):
            if j >= self.DataSize:
                break
            c = self.Data[j] if 0x20 <= self.Data[j] <= 0x7E else "."
            line += "%c" % c
        return line

    def build_hex_output(self):
        lines = []
        for i in range(0, self.DataSize, 16):
            line_end_index = i + 16
            line = self.process_hex_output_line(i, line_end_index)
            lines.append(line)
        return "\n".join(lines)

    def dump_output(self):
        return "".join("%02X" % self.Data[j] for j in range(self.DataSize))


class PassThruMsg(PassThruMsgBuilder):  # sets up the message structure
    pass


class GetParameter(SetConfigurationList, Parameter):
    def __init__(self, *args: Any, **kw: Any):
        super().__init__(*args, **kw)
        self.number_of_parameters = len(Parameter.USED)
        self.parameters = SetConfiguration * self.number_of_parameters
        temporary_parameters = self.parameters()
        for i in range(self.number_of_parameters):
            temporary_parameters[i].set(Parameter.USED[i])
        self.configuration_pointer = temporary_parameters


class J2534Api:
    def __init__(self):
        self.pass_thru_library = None
        self.dll = None
        self.name = None
        tool_registry_info = ToolRegistryInfo()
        self._devices = tool_registry_info.tool_list

    def set_device(self, key=0):
        device = self._devices[key]
        self.name = device[0]
        self.dll = load_j2534_library(device[1])
        self.pass_thru_library = PassThruLibrary(self.dll)

    def get_devices(self):
        return self._devices

    def __getattr__(self, name):
        try:
            return getattr(self.pass_thru_library, name)
        except AttributeError as e:
            raise AttributeError(f"{e} object has no attribute {name}") from e


j2534_api = J2534Api()


def load_j2534_library(dll_path=None):
    try:
        return ct.WinDLL(dll_path)
    except WindowsError:
        return False


def pt_open():
    device_id = ct.c_ulong()
    if j2534_api.PassThruOpen(ct.c_void_p(None), ct.byref(device_id)) != 0:
        return False
    return device_id.value


def pt_close(device_id):
    return j2534_api.PassThruClose(device_id)


def pt_connect(device_id, protocol_id, flags, baud_rate):
    channel_id = ct.c_ulong()
    if j2534_api.PassThruConnect(device_id, protocol_id, flags, baud_rate, ct.byref(channel_id)) != 0:
        return False
    return channel_id.value


def pt_disconnect(channel_id):
    return j2534_api.PassThruDisconnect(channel_id)


def pt_read_message(channel_id, messages, number_of_messages, message_timeout):
    return j2534_api.PassThruReadMsgs(
        channel_id,
        ct.byref(messages),
        ct.byref(ct.c_ulong(number_of_messages)),
        message_timeout,
    )


def pt_write_message(channel_id, messages, number_of_messages, message_timeout):
    return j2534_api.PassThruWriteMsgs(
        channel_id,
        ct.byref(messages),
        ct.byref(ct.c_ulong(number_of_messages)),
        message_timeout,
    )


def pt_start_periodic_message(channel_id, message_id, time_interval):
    periodic_id = ct.c_ulong()
    if j2534_api.PassThruStartPeriodicMsg(channel_id, ct.byref(message_id), ct.byref(periodic_id), time_interval) != 0:
        return False
    return periodic_id.value


def pt_stop_periodic_message(channel_id, message_id):
    return j2534_api.PassThruStopPeriodicMsg(channel_id, message_id)


def create_msg(protocol_id, tx_flag_0, mask_id, pattern_msgs, flow_control=None):
    if protocol_id in [
        1,
        7,
        8,
        9,
        10,
    ]:  # check if using protocol j1850 or sci if so set pass filter...
        mask_message = PassThruMsg(protocol_id, tx_flag_0, 0)
        mask_message.set_identifier(mask_id)

        pattern_message = PassThruMsg(protocol_id, tx_flag_0, 0)
        pattern_message.set_identifier(pattern_msgs)
    else:
        mask_message = PassThruMsg(protocol_id, tx_flag_0, 0)
        mask_message.set_identifier_and_data(mask_id)

        pattern_message = PassThruMsg(protocol_id, tx_flag_0, 0)
        pattern_message.set_identifier_and_data(pattern_msgs)

    if flow_control is not None:
        flow_control_message = PassThruMsg(protocol_id, tx_flag_0, 0)
        flow_control_message.set_identifier_and_data(flow_control)
        return mask_message, pattern_message, flow_control_message
    return mask_message, pattern_message, None


def pt_start_ecu_filter(channel_id, protocol_id, mask_id=None, pattern_msgs=None, flow_control=None, tx_flag_0=0):
    """start the msg filter"""
    filter_id = ct.c_ulong()

    if protocol_id in [6]:  # check if using protocol ISO15765 if so set flow control filter...
        mask_message, pattern_message, flow_control_message = create_msg(protocol_id, tx_flag_0, mask_id, pattern_msgs,
                                                                         flow_control)

        if j2534_api.PassThruStartMsgFilter(channel_id, 3, ct.byref(mask_message), ct.byref(pattern_message),
                                            ct.byref(flow_control_message), ct.byref(filter_id)) != 0:
            return False
        return filter_id.value

    elif protocol_id in [
        1,
        7,
        8,
        9,
        10,
    ]:  # check if using protocol j1850 or sci if so set pass filter...
        mask_message, pattern_message, _ = create_msg(protocol_id, 0, mask_id, pattern_msgs)

        if j2534_api.PassThruStartMsgFilter(channel_id, 1, ct.byref(mask_message), ct.byref(pattern_message),
                                            ct.c_void_p(None), ct.byref(filter_id)) != 0:
            return False
        return filter_id.value


def pt_start_message_filter(channel_id, filter_type, mask_message, pattern_message, flow_control_message):
    filter_id = ct.c_ulong()
    if j2534_api.PassThruStartMsgFilter(channel_id, filter_type, ct.byref(mask_message), ct.byref(pattern_message),
                                        ct.byref(flow_control_message), ct.byref(filter_id)) != 0:
        return False
    return filter_id.value


def pt_stop_message_filter(channel_id, filter_id):
    return j2534_api.PassThruStopMsgFilter(channel_id, filter_id)


def pt_set_programming_voltage(device_id, pin_number, voltage):
    return j2534_api.PassThruSetProgrammingVoltage(device_id, pin_number, voltage)


def pt_read_version(device_id):
    firmware_version = ct.create_string_buffer(80)
    dll_version = ct.create_string_buffer(80)
    api_version = ct.create_string_buffer(80)
    if j2534_api.PassThruReadVersion(device_id, firmware_version, dll_version, api_version) != 0:
        return ['error', 'error', 'error']
    return [firmware_version.value.decode(), dll_version.value.decode(), api_version.value.decode()]


def pt_get_last_error():
    error_buffer = ct.create_string_buffer(80)
    j2534_api.PassThruGetLastError(error_buffer)
    return error_buffer.value


def pt_ioctl(channel_id, ioctl_id, ioctl_input, output):
    return j2534_api.PassThruIoctl(channel_id, ioctl_id, ioctl_input, output)


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
import ctypes as ct
from typing import Any

from .Define import IoctlID, Parameter
from .Registry import ToolRegistryInfo
from .dll import PassThru_Data, PassThruMessageStructure, \
    SetConfigurationList, PassThruLibrary, SetConfiguration


class MsgBuilder(PassThruMessageStructure):
    def build_transmit_data_block(self, data):
        self.DataSize = len(data)
        self.Data = PassThru_Data()
        for i in range(self.DataSize):
            self.Data[i] = data[i]

    def set_identifier(self, transmit_identifier):
        identifier = self.int_to_list(transmit_identifier)
        self.build_transmit_data_block(identifier)

    def set_identifier_and_data(self, _id, data=None):
        data = data or []
        id_and_data = self.int_to_list(_id) + data
        self.build_transmit_data_block(id_and_data)

    @staticmethod
    def int_to_list(_id):
        if _id < 255:
            return [_id]
        return [_id >> 24 & 0xFF, _id >> 16 & 0xFF, _id >> 8 & 0xFF, _id & 0xFF]


class PassThruMsgBuilder(MsgBuilder):  # sets up the message structure
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

    def process_hex_output_line(self, line_start_index, line_end_index):
        line = "%04x | " % line_start_index
        for j in range(line_start_index, line_end_index):
            if j >= self.DataSize:
                break
            line += "%02X " % abs(self.Data[j])
        line += " " * (3 * 16 + 7 - len(line)) + " | "
        for j in range(line_start_index, line_end_index):
            if j >= self.DataSize:
                break
            c = self.Data[j] if 0x20 <= self.Data[j] <= 0x7E else "."
            line += "%c" % c
        return line

    def build_hex_output(self):
        lines = []
        for i in range(0, self.DataSize, 16):
            line_end_index = i + 16
            line = self.process_hex_output_line(i, line_end_index)
            lines.append(line)
        return "\n".join(lines)

    def dump_output(self):
        return "".join("%02X" % self.Data[j] for j in range(self.DataSize))


class PassThruMsg(PassThruMsgBuilder):  # sets up the message structure
    pass


class GetParameter(SetConfigurationList, Parameter):
    def __init__(self, *args: Any, **kw: Any):
        super().__init__(*args, **kw)
        self.number_of_parameters = len(Parameter.USED)
        self.parameters = SetConfiguration * self.number_of_parameters
        temporary_parameters = self.parameters()
        for i in range(self.number_of_parameters):
            temporary_parameters[i].set(Parameter.USED[i])
        self.configuration_pointer = temporary_parameters


class J2534Api:
    def __init__(self):
        self.pass_thru_library = None
        self.dll = None
        self.name = None
        tool_registry_info = ToolRegistryInfo()
        self._devices = tool_registry_info.tool_list

    def set_device(self, key=0):
        device = self._devices[key]
        self.name = device[0]
        self.dll = load_j2534_library(device[1])
        self.pass_thru_library = PassThruLibrary(self.dll)

    def get_devices(self):
        return self._devices

    def __getattr__(self, name):
        try:
            return getattr(self.pass_thru_library, name)
        except AttributeError as e:
            raise AttributeError(f"{e} object has no attribute {name}") from e


j2534_api = J2534Api()


def load_j2534_library(dll_path=None):
    try:
        return ct.WinDLL(dll_path)
    except WindowsError:
        return False


def pt_open():
    device_id = ct.c_ulong()
    if j2534_api.PassThruOpen(ct.c_void_p(None), ct.byref(device_id)) != 0:
        return False
    return device_id.value


def pt_close(device_id):
    return j2534_api.PassThruClose(device_id)


def pt_connect(device_id, protocol_id, flags, baud_rate):
    channel_id = ct.c_ulong()
    if j2534_api.PassThruConnect(device_id, protocol_id, flags, baud_rate, ct.byref(channel_id)) != 0:
        return False
    return channel_id.value


def pt_disconnect(channel_id):
    return j2534_api.PassThruDisconnect(channel_id)


def pt_read_message(channel_id, messages, number_of_messages, message_timeout):
    return j2534_api.PassThruReadMsgs(
        channel_id,
        ct.byref(messages),
        ct.byref(ct.c_ulong(number_of_messages)),
        message_timeout,
    )


def pt_write_message(channel_id, messages, number_of_messages, message_timeout):
    return j2534_api.PassThruWriteMsgs(
        channel_id,
        ct.byref(messages),
        ct.byref(ct.c_ulong(number_of_messages)),
        message_timeout,
    )


def pt_start_periodic_message(channel_id, message_id, time_interval):
    periodic_id = ct.c_ulong()
    if j2534_api.PassThruStartPeriodicMsg(channel_id, ct.byref(message_id), ct.byref(periodic_id), time_interval) != 0:
        return False
    return periodic_id.value


def pt_stop_periodic_message(channel_id, message_id):
    return j2534_api.PassThruStopPeriodicMsg(channel_id, message_id)


def create_msg(protocol_id, tx_flag_0, mask_id, pattern_msgs, flow_control=None):
    if protocol_id in [
        1,
        7,
        8,
        9,
        10,
    ]:  # check if using protocol j1850 or sci if so set pass filter...
        mask_message = PassThruMsg(protocol_id, tx_flag_0, 0)
        mask_message.set_identifier(mask_id)

        pattern_message = PassThruMsg(protocol_id, tx_flag_0, 0)
        pattern_message.set_identifier(pattern_msgs)
    else:
        mask_message = PassThruMsg(protocol_id, tx_flag_0, 0)
        mask_message.set_identifier_and_data(mask_id)

        pattern_message = PassThruMsg(protocol_id, tx_flag_0, 0)
        pattern_message.set_identifier_and_data(pattern_msgs)

    if flow_control is not None:
        flow_control_message = PassThruMsg(protocol_id, tx_flag_0, 0)
        flow_control_message.set_identifier_and_data(flow_control)
        return mask_message, pattern_message, flow_control_message
    return mask_message, pattern_message, None


def pt_start_ecu_filter(channel_id, protocol_id, mask_id=None, pattern_msgs=None, flow_control=None, tx_flag_0=0):
    """start the msg filter"""
    filter_id = ct.c_ulong()

    if protocol_id in [6]:  # check if using protocol ISO15765 if so set flow control filter...
        mask_message, pattern_message, flow_control_message = create_msg(protocol_id, tx_flag_0, mask_id, pattern_msgs,
                                                                         flow_control)

        if j2534_api.PassThruStartMsgFilter(channel_id, 3, ct.byref(mask_message), ct.byref(pattern_message),
                                            ct.byref(flow_control_message), ct.byref(filter_id)) != 0:
            return False
        return filter_id.value

    elif protocol_id in [
        1,
        7,
        8,
        9,
        10,
    ]:  # check if using protocol j1850 or sci if so set pass filter...
        mask_message, pattern_message, _ = create_msg(protocol_id, 0, mask_id, pattern_msgs)

        if j2534_api.PassThruStartMsgFilter(channel_id, 1, ct.byref(mask_message), ct.byref(pattern_message),
                                            ct.c_void_p(None), ct.byref(filter_id)) != 0:
            return False
        return filter_id.value


def pt_start_message_filter(channel_id, filter_type, mask_message, pattern_message, flow_control_message):
    filter_id = ct.c_ulong()
    if j2534_api.PassThruStartMsgFilter(channel_id, filter_type, ct.byref(mask_message), ct.byref(pattern_message),
                                        ct.byref(flow_control_message), ct.byref(filter_id)) != 0:
        return False
    return filter_id.value


def pt_stop_message_filter(channel_id, filter_id):
    return j2534_api.PassThruStopMsgFilter(channel_id, filter_id)


def pt_set_programming_voltage(device_id, pin_number, voltage):
    return j2534_api.PassThruSetProgrammingVoltage(device_id, pin_number, voltage)


def pt_read_version(device_id):
    firmware_version = ct.create_string_buffer(80)
    dll_version = ct.create_string_buffer(80)
    api_version = ct.create_string_buffer(80)
    if j2534_api.PassThruReadVersion(device_id, firmware_version, dll_version, api_version) != 0:
        return ['error', 'error', 'error']
    return [firmware_version.value.decode(), dll_version.value.decode(), api_version.value.decode()]


def pt_get_last_error():
    error_buffer = ct.create_string_buffer(80)
    j2534_api.PassThruGetLastError(error_buffer)
    return error_buffer.value


def pt_ioctl(channel_id, ioctl_id, ioctl_input, output):
    return j2534_api.PassThruIoctl(channel_id, ioctl_id, ioctl_input, output)


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
