import ctypes as ct

PassThru_Data = (ct.c_ubyte * 4128)


class PassThruMessageStructure(ct.Structure):
    _fields_ = [
        ("ProtocolID", ct.c_ulong),
        ("RxStatus", ct.c_ulong),
        ("TxFlags", ct.c_ulong),
        ("Timestamp", ct.c_ulong),
        ("DataSize", ct.c_ulong),
        ("ExtraDataIndex", ct.c_ulong),
        ("Data", PassThru_Data)]


class SetConfiguration(ct.Structure):
    _fields_ = [
        ("Parameter", ct.c_ulong),
        ("Value", ct.c_ulong)
    ]

    def set_parameter(self, para):
        self.Parameter = para

    def set_value(self, para):
        self.Value = para


class SetConfigurationList(ct.Structure):
    _fields_ = [
        ("NumOfParams", ct.c_ulong),
        ("ConfigPtr", ct.POINTER(SetConfiguration))
    ]


def annotate(dll_object, function_name, argtypes, restype=None):
    function = getattr(dll_object._dll, function_name)
    function.argtypes = argtypes
    # restype is optional in the function_prototypes list
    if restype is None:
        restype = ct.c_long  # dll_object.default_restype ##
    function.restype = restype
    setattr(dll_object, function_name, function)


class MyDll(object):
    def __init__(self, ct_dll, **function_prototypes):
        self._dll = ct_dll
        for name, prototype in function_prototypes.items():
            annotate(self, name, *prototype)


class PassThruLibrary(MyDll):
    function_prototypes = {
        # extern "C" long WINAPI PassThruOpen (void *pName unsigned long *pDeviceID)
        'PassThruOpen': [[ct.c_void_p, ct.POINTER(ct.c_ulong)]],
        # extern "C" long WINAPI PassThruClose (unsigned long DeviceID)
        'PassThruClose': [[ct.c_ulong]],
        # extern "C" long WINAPI PassThruConnect (unsigned long DeviceID, unsigned long ProtocolID, unsigned long Flags,
        #   unsigned long BaudRate, unsigned long *pChannelID)
        'PassThruConnect': [[ct.c_ulong, ct.c_ulong, ct.c_ulong, ct.c_ulong, ct.POINTER(ct.c_ulong)]],
        # extern "C" long WINAPI PassThruDisconnect (unsigned long ChannelID)
        'PassThruDisconnect': [[ct.c_ulong]],
        # extern "C" long WINAPI PassThruWriteMsgs (unsigned long ChannelID, PASSTHRU_MSG *pMsg, unsigned long
        # *pNumMsgs, unsigned long Timeout)
        'PassThruReadMsgs': [[ct.c_ulong, ct.POINTER(PassThruMessageStructure), ct.POINTER(ct.c_ulong), ct.c_ulong]],
        # extern "C" long WINAPI PassThruWriteMsgs (unsigned long ChannelID, PASSTHRU_MSG *pMsg, unsigned long
        # *pNumMsgs, unsigned long Timeout)
        'PassThruWriteMsgs': [[ct.c_ulong, ct.POINTER(PassThruMessageStructure), ct.POINTER(ct.c_ulong), ct.c_ulong]],
        # extern "C" long WINAPI PassThruStartPeriodicMsg (unsigned long ChannelID, PASSTHRU_MSG *pMsg,
        #   unsigned long *pMsgID, unsigned long TimeInterval)
        'PassThruStartPeriodicMsg': [
            [ct.c_ulong, ct.POINTER(PassThruMessageStructure), ct.POINTER(ct.c_ulong), ct.c_ulong]],
        # extern "C" long WINAPI PassThruStopPeriodicMsg (unsigned long ChannelID, unsigned long MsgID)
        'PassThruStopPeriodicMsg': [[ct.c_ulong, ct.c_ulong]],
        # extern "C" long WINAPI PassThruStartMsgFilter (unsigned long ChannelID, unsigned long FilterType,
        #   PASSTHRU_MSG *pMaskMsg, PASSTHRU_MSG *pPatternMsg, PASSTHRU_MSG *pFlowControlMsg, unsigned long *pFilterID)
        'PassThruStartMsgFilter': [
            [ct.c_ulong, ct.c_ulong, ct.POINTER(PassThruMessageStructure), ct.POINTER(PassThruMessageStructure),
             ct.POINTER(None),
             ct.POINTER(ct.c_ulong)]],
        # extern "C" long WINAPI PassThruStopMsgFilter (unsigned long ChannelID, unsigned long FilterID)
        'PassThruStopMsgFilter': [[ct.c_ulong, ct.c_ulong]],
        # extern "C" long WINAPI PassThruSetProgrammingVoltage (unsigned long DeviceID, unsigned long PinNumber,
        # unsigned long Voltage)
        'PassThruSetProgrammingVoltage': [[ct.c_ulong, ct.c_ulong, ct.c_ulong]],
        # extern "C" long WINAPI PassThruReadVersion (unsigned long DeviceID, char *pFirmwareVersion,
        # char *pDllVersion, char *pApiVersion)
        'PassThruReadVersion': [[ct.c_ulong, ct.c_char_p, ct.c_char_p, ct.c_char_p]],
        # extern "C" long WINAPI PassThruGetLastError (char   *pErrorDescription)
        'PassThruGetLastError': [[ct.c_char_p]],
        # extern "C" long WINAPI PassThruIoctl (unsigned long ChannelID, unsigned long IoctlID,
        # void *pInput, void *pOutput)
        'PassThruIoctl': [[ct.c_ulong, ct.c_ulong, ct.c_void_p, ct.c_void_p]]
    }

    def __init__(self, ct_dll):
        # set default values for function_prototypes
        self.default_restype = ct.c_long
        super(PassThruLibrary, self).__init__(ct_dll, **self.function_prototypes)
