# coding:utf-8

import sys

import J2534.dllLoader as dllLIBRARY
from J2534.dll import *
import ctypes as ct
from J2534.Define import *
from J2534.Error import showERROR

ptData = PassThru_Data


class baseMsg(PassThru_Msg):
    def setData(self, data):
        self.DataSize = len(data)
        self.Data = ptData()
        for i in range(self.DataSize):
            self.Data[i] = data[i]

    def SetDataString(self, data=[]):
        self.setData(data)
        return

    def SetID(self, ID):
        d = self.IntToID(ID)
        self.setData(d)

    def setIDandData(self, ID, data=[]):
        d = self.IntToID(ID) + data
        self.setData(d)
        return

    @staticmethod
    def IntToID(ID):
        if ID > 16777215:
            H4 = ID >> 24 & 0xFF
            H3 = ID >> 16 & 0xFF
            H2 = ID >> 8 & 0xFF
            H1 = ID & 0xFF
            return [H4, H3, H2, H1]
        elif ID > 65535:
            H3 = ID >> 16 & 0xFF
            H2 = ID >> 8 & 0xFF
            H1 = ID & 0xFF
            return [H3, H2, H1]
        elif ID > 255:
            H2 = ID >> 8 & 0xFF
            H1 = ID & 0xFF
            return [H2, H1]
        else:
            H1 = ID & 0xFF
            return [H1]


class ptMsg(baseMsg):
    def __init__(self, ProtocolID, TxFlags, *args: Any, **kw: Any):
        super().__init__(*args, **kw)
        self.ProtocolID = ProtocolID
        self.TxFlags = TxFlags


class ptMskMsg(ptMsg):
    pass


class ptPatternMsg(ptMsg):
    pass


class ptFlowControlMsg(ptMsg):
    pass


class ptTxMsg(baseMsg):
    def __init__(self, ProtocolID, TxFlags, *args: Any, **kw: Any):
        super().__init__(*args, **kw)
        self.ProtocolID = ProtocolID
        self.TxFlags = TxFlags


class ptRxMsg(baseMsg):
    def __init__(self, ProtocolID, TxFlags, *args: Any, **kw: Any):
        super().__init__(*args, **kw)
        self.ProtocolID = ProtocolID
        self.TxFlags = TxFlags

    def Dump(self):
        print("ProtocolID = " + str(self.ProtocolID))
        print("RxStatus = " + str(self.RxStatus))
        print("TxFlags = " + str(self.TxFlags))
        print("Timestamp = " + str(self.Timestamp))
        print("DataSize = " + str(self.DataSize))
        print("ExtraDataIndex = " + str(self.ExtraDataIndex))
        print(self.HexRx())

    def HexRx(self):
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

    def DumpData(self):
        line = ""
        for j in range(self.DataSize):
            line += "%02X" % self.Data[j]
        return line


class GetParameter(SCONFIG_LIST, Parameter):
    def __init__(self, *args: Any, **kw: Any):
        super().__init__(*args, **kw)
        self.NumOfParams = len(Parameter.USED)
        self.paras = SCONFIG * self.NumOfParams
        for i in range(self.NumOfParams):
            self.paras()[i].set(Parameter.USED[i])
        self.ConfigPtr = self.paras()


class J2534Lib:

    def __init__(self):
        self.Devices = dllLIBRARY.getDevices()
        self._module = sys.modules[__name__]
        self.MethodErrorLog = False

    def setDevice(self, key=0):
        """[select the device]
        
        Keyword Arguments:
            key {int} -- [the j2534 index in register ] (default: {0})
        """
        device = self.Devices[key]
        self.name = device[0]
        self.dll = dllLIBRARY.load_dll(device[1])
        self.canlib = CanlibDll(self.dll)

    def getDevices(self):
        """[return all the devices dict]
        """
        return self.Devices

    def SetErrorLog(self, state):
        """[on / off the error log]
        
        Arguments:
            state {[bool]} -- [open or close the error log]
        """
        self.MethodErrorLog = state

    def err(self, method, ret):
        if self.MethodErrorLog:
            showERROR(method, ret)

    def __getattr__(self, name):
        try:
            return getattr(self.canlib, name)
        except AttributeError:
            raise AttributeError("{t} object has no attribute {n}".format(
                t=str(type(self)), n=name))


j2534lib = J2534Lib()
_err = j2534lib.err


def ptOpen():
    """[open selected j2534 device]

    Returns:
        ret  --  error type
        [type] -- [description]
    """
    DeviceId = ct.c_ulong()
    ret = j2534lib.PassThruOpen(ct.c_void_p(None), ct.byref(DeviceId))
    _err('ptOpen', ret)
    return ret, DeviceId.value


def ptClose(DeviceId):
    """Close Device

    Keyword Arguments:
        DeviceId {[int]} -- Device Id Number
    """
    ret = j2534lib.PassThruClose(DeviceId)
    _err('ptClose', ret)
    return ret


def ptConnect(DeviceId, ProtocolID, Flags, BaudRate):
    """Connect one channel in the J2534, if the j2534 device have more, this api will open only one.

    Returns:
        ret  --  error type
        id   --  channel id
    """
    ChannelID = ct.c_ulong()
    ret = j2534lib.PassThruConnect(DeviceId, ProtocolID, Flags, BaudRate, ct.byref(ChannelID))
    _err('ptConnect', ret)
    return ret, ChannelID.value


def ptDisconnect(ChannelID):
    """disconnect one channel

    Arguments:
        ChannelID {[int]} -- [description]

    Returns:
        [ret] -- [error type]
    """
    ret = j2534lib.PassThruDisconnect(ChannelID)
    _err('ptDisconnect', ret)
    return ret


def ptReadMsgs(ChannelID, Msgs, NumMsgs, Timeout):
    """ :TODO
    """
    ret = j2534lib.PassThruReadMsgs(ChannelID, ct.byref(Msgs), ct.byref(ct.c_ulong(NumMsgs)), Timeout)
    _err('ptReadMsgs', ret)
    return ret


def ptWtiteMsgs(ChannelID, Msgs, NumMsgs, Timeout):
    """[summary]

    Arguments:
        ChannelID {[type]} -- [description]
        Msgs {[type]} -- [description]
        NumMsgs {[type]} -- [description]
        Timeout {[type]} -- [description]
    """
    ret = j2534lib.PassThruWriteMsgs(ChannelID, ct.byref(Msgs), ct.byref(ct.c_ulong(NumMsgs)), Timeout)
    _err('ptWtiteMsgs', ret)
    return ret


def ptStartPeriodicMsg(ChannelID, Msgs, MsgID, TimeInterval):
    """ TODO
    """
    ret = j2534lib.PassThruStartPeriodicMsg(ChannelID, ct.byref(Msgs), ct.byref(MsgID), TimeInterval)
    _err('ptStartPeriodicMsg', ret)
    return ret


def ptStopPeriodicMsg(ChannelID, MsgID):
    """ stop period msg
    """
    return j2534lib.PassThruStopPeriodicMsg(ChannelID, MsgID)


def ptStartEcmFilter(ChannelID, ProtocolID, Mask=None, Pattern=None, Flow=None, TxFlag0=0, TxFlag1=0):
    """ start the msg filter
    """

    pFilterID = ct.c_ulong()

    if ProtocolID == 6:  # check if using protocol ISO15765 if so set flow control filter...
        maskMsg = ptMskMsg(ProtocolID, TxFlag0, TxFlag1)
        maskMsg.setData(Mask)

        patternMsg = ptPatternMsg(ProtocolID, TxFlag0, TxFlag1)
        patternMsg.setData(Pattern)

        flowcontrolMsg = ptFlowControlMsg(ProtocolID, TxFlag0, TxFlag1)
        flowcontrolMsg.setData(Flow)
        ret = j2534lib.PassThruStartMsgFilter(ChannelID, 3, ct.byref(maskMsg), ct.byref(patternMsg),
                                              ct.byref(flowcontrolMsg), ct.byref(pFilterID))
        _err('ptStartMsgFilter', ret)
        return ret, pFilterID.value

    elif ProtocolID in [1, 7, 9]:  # check if using protocol j1850 if so set pass filter...

        maskMsg = ptMskMsg(ProtocolID, 0)
        maskMsg.SetDataString(Mask)

        patternMsg = ptPatternMsg(ProtocolID, 0)
        patternMsg.SetDataString(Pattern)

        ret = j2534lib.PassThruStartMsgFilter(ChannelID, 1, ct.byref(maskMsg), ct.byref(patternMsg),
                                              ct.c_void_p(None), ct.byref(pFilterID))
        _err('ptStartMsgFilter', ret)
        return ret, pFilterID.value


def ptStartMsgFilter(ChannelID, FilterType, MaskMsg, PatternMsg, FlowControlMsg):
    """ start the msg filter
    """
    pFilterID = ct.c_ulong()
    ret = j2534lib.PassThruStartMsgFilter(ChannelID, FilterType, ct.byref(MaskMsg), ct.byref(PatternMsg),
                                          ct.byref(FlowControlMsg), ct.byref(pFilterID))
    _err('ptStartMsgFilter', ret)
    return ret, pFilterID.value


def ptStopMsgFilter(ChannelID, FilterID):
    """ stop the msg filter
    """
    ret = j2534lib.PassThruStopMsgFilter(ChannelID, FilterID)
    _err('ptStopMsgFilter', ret)
    return ret


def ptSetProgrammingVoltage(DeviceID, PinNumber, Voltage):
    """ set the pin voltage
    """
    ret = j2534lib.PassThruSetProgrammingVoltage(DeviceID, PinNumber, Voltage)
    _err('ptSetProgrammingVoltage', ret)
    return ret


def ptReadVersion(DeviceId):
    """Read Dll Version Msg

    Keyword Arguments:
        DeviceId {[int]} -- Device Id Number
    return

    """
    FirmwareVersion = ct.create_string_buffer(80)
    DllVersion = ct.create_string_buffer(80)
    ApiVersion = ct.create_string_buffer(80)
    ret = j2534lib.PassThruReadVersion(DeviceId, FirmwareVersion, DllVersion, ApiVersion)
    _err('ptReadVersion', ret)
    return [FirmwareVersion.value.decode(), DllVersion.value.decode(), ApiVersion.value.decode()]


def ptGetLastError():
    """ get the last error
    """
    ErrorMsg = ct.create_string_buffer(80)
    j2534lib.PassThruGetLastError(ErrorMsg)
    return ErrorMsg.value


def ptIoctl(ChannelID, IoctlID, Input, Output):
    """ Ioctl base function
    """
    ret = j2534lib.PassThruIoctl(ChannelID, IoctlID, Input, Output)
    _err('ptIoctl', ret)
    return ret


def SetConfig(ChannelID, parameters):
    conf = SCONFIG_LIST()
    conf.NumOfParams = len(parameters)
    elems = (SCONFIG * len(parameters))()
    conf.ConfigPtr = ct.cast(elems, ct.POINTER(SCONFIG))
    for num in range(len(parameters)):
        conf.ConfigPtr[num].set_parameter(parameters[num][0])
        conf.ConfigPtr[num].set_value(parameters[num][1])
    ret = ptIoctl(ChannelID, IoctlID.SET_CONFIG, ct.byref(conf), ct.c_void_p(None))
    return ret, conf.ConfigPtr


def ReadVbat(DeviceId):
    _voltage = ct.c_ulong()
    ret = ptIoctl(DeviceId, IoctlID.READ_VBATT, ct.c_void_p(None), ct.byref(_voltage))
    vbat = _voltage.value / 1000.0
    return ret, vbat


def ReadProgVoltage(ChannelID):
    _voltage = ct.c_ulong()
    ret = ptIoctl(ChannelID, IoctlID.READ_PROG_VOLTAGE, ct.c_void_p(None), ct.byref(_voltage))
    vbat = _voltage.value / 1000.0
    return ret, vbat


def FiveBaudInit(ChannelID):
    return None


def FastInit(ChannelID):
    return None


def ClearTxBuf(ChannelID):
    return ptIoctl(ChannelID, IoctlID.CLEAR_TX_BUFFER, ct.c_void_p(None), ct.c_void_p(None))


def ClearRxBuf(ChannelID):
    return ptIoctl(ChannelID, IoctlID.CLEAR_RX_BUFFER, ct.c_void_p(None), ct.c_void_p(None))


def ClearPeriodicMsgs(ChannelID):
    return ptIoctl(
        ChannelID,
        IoctlID.CLEAR_PERIODIC_MSGS,
        ct.c_void_p(None),
        ct.c_void_p(None),
    )


def ClearMsgsFilters(ChannelID):
    return ptIoctl(
        ChannelID,
        IoctlID.CLEAR_MSG_FILTERS,
        ct.c_void_p(None),
        ct.c_void_p(None),
    )


def ClearFunctMsgLookUpTable(ChannelID):
    return ptIoctl(
        ChannelID,
        IoctlID.CLEAR_FUNCT_MSG_LOOKUP_TABLE,
        ct.c_void_p(None),
        ct.c_void_p(None),
    )


def AddToFunctMsgLookUpTable(ChannelID):
    # ret = ptIoctl(ChannelID, IoctlID.CLEAR_PERIODIC_MSGS, ct.c_void_p(None), ct.c_void_p(None))
    return None


def DeleteFromFunctMsgLookUpTable(ChannelID):
    # ret = ptIoctl(ChannelID, IoctlID.CLEAR_PERIODIC_MSGS, ct.c_void_p(None), ct.c_void_p(None))
    return None
