# coding=utf-8
import ctypes
import os
import os.path
import sys
import platform
import _winreg
from ctypes import *


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


class SBYTE_ARRAY(ctypes.Structure):
    _fields_ = [
        ("NumOfBytes", c_ulong),	    # Number of functional addresses in array
        ("BytePtr", ctypes.POINTER(c_ubyte))    # pointer to functional address array
    ]


class SCONFIG(ctypes.Structure):
    _fields_ = [
        ("Parameter", c_ulong),	# Name of configuration parameter
        ("Value", c_ulong)		# Value of configuration parameter
    ]


class SCONFIG_LIST(ctypes.Structure):
    _fields_ = [
        ("NumOfParams", c_ulong),	    # size of SCONFIG array
        ("ConfigPtr", ctypes.POINTER(SCONFIG))	# array containing configuration item(s)
    ]


class Protocols:

    # Protocols:
    J1850VPW =				0x01
    J1850PWM =				0x02
    ISO9141 =				0x03
    ISO14230 =				0x04
    CAN =					0x05
    ISO15765 =				0x06
    SCI_A_ENGINE =			0x07
    SCI_A_TRANS =			0x08
    SCI_B_ENGINE =			0x09
    SCI_B_TRANS =			0x0A

    def __init__(self):
        return

class Ioctls:

    # Ioctls
    GET_CONFIG =	        	        	0x01	# SCONFIG_LIST		NULL
    SET_CONFIG =		                 	0x02	# SCONFIG_LIST		NULL
    READ_VBATT =		                	0x03	# NULL			unsigned long
    FIVE_BAUD_INIT =	                	0x04	# SBYTE_ARRAY		SBYTE_ARRAY
    FAST_INIT =				                0x05	# PASSTHRU_MSG		PASSTHRU_MSG
    CLEAR_TX_BUFFER =	                   	0x07	# NULL			NULL
    CLEAR_RX_BUFFER =		                0x08	# NULL			NULL
    CLEAR_PERIODIC_MSGS =	                0x09	# NULL			NULL
    CLEAR_MSG_FILTERS =			            0x0A	# NULL			NULL
    CLEAR_FUNCT_MSG_LOOKUP_TABLE =	        0x0B	# NULL			NULL
    ADD_TO_FUNCT_MSG_LOOKUP_TABLE =	        0x0C	# SBYTE_ARRAY		NULL
    DELETE_FROM_FUNCT_MSG_LOOKUP_TABLE =	0x0D	# SBYTE_ARRAY		NULL
    READ_PROG_VOLTAGE =			            0x0E	# NULL			unsigned long

    # Ioctl parameters for GET_CONFIG and SET_CONFIG
    DATA_RATE =		    0x01	# 5 – 500000 	# Baud rate value used for vehicle network. No default value specified.
    LOOPBACK =		    0x03	# 0(OFF)/1(ON)	# 0 = Do not echo transmitted messages to the Receive queue. 1 = Echo transmitted messages to the Receive queue.
                                # Default value is 0(OFF).
    NODE_ADDRESS =		0x04	# 0x00-0xFF	# J1850PWM specific, physical address for node of interest in the vehicle network. Default is no nodes are recognized by scan tool.
    NETWORK_LINE =		0x05	# 0(BUS_NORMAL)/1(BUS_PLUS)/2(BUS_MINUS)	# J1850PWM specific, network line(s) active during message transfers. Default value is 0(BUS_NORMAL).
    P1_MIN =			0x06	# 0x0-0xFFFF	# ISO-9141/14230 specific, min. ECU inter-byte time for responses [02.02-API: ms]. Default value is 0 ms. 04.04-API: NOT ADJUSTABLE, 0ms.
    P1_MAX =			0x07	# 0x0/0x1-0xFFFF # ISO-9141/14230 specific, max. ECU inter-byte time for responses [02.02-API: ms, 04.04-API: *0.5ms]. Default value is 20 ms.
    P2_MIN =			0x08	# 0x0-0xFFFF	# ISO-9141/14230 specific, min. ECU response time to a tester request or between ECU responses [02.02-API: ms, 04.04-API: *0.5ms]. 04.04-API: NOT ADJUSTABLE, 0ms. Default value is 25 ms.
    P2_MAX =			0x09	# 0x0-0xFFFF	# ISO-9141/14230 specific, max. ECU response time to a tester request or between ECU responses [02.02-API: ms, 04.04-API: *0.5ms]. 04.04-API: NOT ADJUSTABLE, all messages up to P3_MIN are receoved. Default value is 50 ms.
    P3_MIN =			0x0A	# 0x0-0xFFFF	# ISO-9141/14230 specific, min. ECU response time between end of ECU response and next tester request [02.02-API: ms, 04.04-API: *0.5ms]. Default value is 55 ms.
    P3_MAX =			0x0B	# 0x0-0xFFFF	# ISO-9141/14230 specific, max. ECU response time between end of ECU response and next tester request [02.02-API: ms, 04.04-API: *0.5ms]. 04.04-API: NOT ADJUSTABLE, messages can be sent at anytime after P3_MIN. Default value is 5000 ms.
    P4_MIN =			0x0C	# 0x0-0xFFFF	# ISO-9141/14230 specific, min. tester inter-byte time for a request [02.02-API: ms, 04.04-API: *0.5ms]. Default value is 5 ms.
    P4_MAX =			0x0D	# 0x0-0xFFFF	# ISO-9141/14230 specific, max. tester inter-byte time for a request [02.02-API: ms, 04.04-API: *0.5ms]. 04.04-API: NOT ADJUSTABLE, P4_MIN is always used. Default value is 20 ms.

    W1 =			    0x0E	# 0x0-0xFFFF	# ISO 9141 specific, max. time [ms] from the address byte end to synchronization pattern start. Default value is 300 ms.
    W2 =		    	0x0F	# 0x0-0xFFFF	# ISO 9141 specific, max. time [ms] from the synchronization byte end to key byte 1 start. Default value is 20 ms.
    W3 =			    0x10	# 0x0-0xFFFF	# ISO 9141 specific, max. time [ms] between key byte 1 and key byte 2. Default value is 20 ms.
    W4 =		    	0x11	# 0x0-0xFFFF	# ISO 9141 specific, 02.02-API: max. time [ms] between key byte 2 and its inversion from the tester. Default value is 50 ms.
                                # ISO 9141 specific, 04.04-API: min. time [ms] between key byte 2 and its inversion from the tester. Default value is 50 ms.
    W5 =			    0x12	# 0x0-0xFFFF	# ISO 9141 specific, min. time [ms] before the tester begins retransmission of the address byte. Default value is 300 ms.
    TIDLE =		    	0x13	# 0x0-0xFFFF	# ISO 9141 specific, bus idle time required before starting a fast initialization sequence. Default value is W5 value.
    TINL =	    		0x14	# 0x0-0xFFFF	# ISO 9141 specific, the duration [ms] of the fast initialization low pulse. Default value is 25 ms.
    TWUP =			    0x15	# 0x0-0xFFFF	# ISO 9141 specific, the duration [ms] of the fast initialization wake-up pulse. Default value is 50 ms.
    PARITY =			0x16	# 0(NO_PARITY)/1(ODD_PARITY)/2(EVEN_PARITY)	# ISO9141 specific, parity type for detecting bit errors.  Default value is 0(NO_PARITY).
    BIT_SAMPLE_POINT =	0x17	# 0-100	# CAN specific, the desired bit sample point as a percentage of bit time. Default value is 80%.
    SYNCH_JUMP_WIDTH =	0x18	# 0-100	# CAN specific, the desired synchronization jump width as a percentage of the bit time. Default value is 15%.
    W0 =			    0x19
    T1_MAX =			0x1A	# 0x0-0xFFFF	# SCI_X_XXXX specific, the max. interframe response delay. Default value is 20 ms.
    T2_MAX =			0x1B	# 0x0-0xFFFF	# SCI_X_XXXX specific, the max. interframe request delay.Default value is 100 ms.
    T4_MAX =			0x1C	# 0x0-0xFFFF	# SCI_X_XXXX specific, the max. intermessage response delay. Default value is 20 ms.
    T5_MAX =			0x1D	# 0x0-0xFFFF	# SCI_X_XXXX specific, the max. intermessage request delay. Default value is 100 ms.
    ISO15765_BS =		0x1E	# 0x0-0xFF	# ISO15765 specific, the block size for segmented transfers.
                                # The scan tool may override this value to match the capabilities reported by the ECUs. Default value is 0.
    ISO15765_STMIN =	0x1F	# 0x0-0xFF	# ISO15765 specific, the separation time for segmented transfers.
                                # The scan tool may override this value to match the capabilities reported by the ECUs. Default value is 0.
    DATA_BITS =		    0x20	# 04.04-API only
    FIVE_BAUD_MOD =		0x21
    BS_TX =			    0x22
    STMIN_TX =		    0x23
    T3_MAX =			0x24
    ISO15765_WFT_MAX =	0x25

    def __init__(self):
        return


class Errors:

    # Error definitions
    STATUS_NOERROR =			0x00	# Function completed successfully.
    ERR_SUCCESS =			    0x00	# Function completed successfully.
    ERR_NOT_SUPPORTED =		    0x01	# Function option is not supported.
    ERR_INVALID_CHANNEL_ID =	0x02	# Channel Identifier or handle is not recognized.
    ERR_INVALID_PROTOCOL_ID =	0x03	# Protocol Identifier is not recognized.
    ERR_NULL_PARAMETER =		0x04	# NULL pointer presented as a function parameter, NULL is an invalid address.
    ERR_INVALID_IOCTL_VALUE =	0x05	# Ioctl GET_CONFIG/SET_CONFIG parameter value is not recognized.
    ERR_INVALID_FLAGS =		    0x06	# Flags bit field(s) contain(s) an invalid value.
    ERR_FAILED =			    0x07	# Unspecified error, use PassThruGetLastError for obtaining error text string.
    ERR_DEVICE_NOT_CONNECTED =	0x08	# PassThru device is not connected to the PC.
    ERR_TIMEOUT =			    0x09	# Timeout violation. PassThru device is unable to read specified number of messages from the vehicle network.
                                        # The actual number of messages returned is in NumMsgs.
    ERR_INVALID_MSG =			0x0A	# Message contained a min/max length, ExtraData support or J1850PWM specific source address conflict violation.
    ERR_INVALID_TIME_INTERVAL =	0x0B	# The time interval value is outside the specified range.
    ERR_EXCEEDED_LIMIT =		0x0C	# The limit(ten) of filter/periodic messages has been exceeded for the protocol associated the communications channel.
    ERR_INVALID_MSG_ID =		0x0D	# The message identifier or handle is not recognized.
    ERR_DEVICE_IN_USE =	    	0x0E	# The specified PassThru device is already in use.
    ERR_INVALID_IOCTL_ID =		0x0F	# Ioctl identifier is not recognized.
    ERR_BUFFER_EMPTY =		    0x10	# PassThru device could not read any messages from the vehicle network.
    ERR_BUFFER_FULL =			0x11	# PassThru device could not queue any more transmit messages destined for the vehicle network.
    ERR_BUFFER_OVERFLOW =		0x12	# PassThru device experienced a buffer overflow and receive messages were lost.
    ERR_PIN_INVALID =			0x13	# Unknown pin number specified for the J1962 connector.
    ERR_CHANNEL_IN_USE =		0x14	# An existing communications channel is currently using the specified network protocol.
    ERR_MSG_PROTOCOL_ID =		0x15	# The specified protocol type within the message structure is different from the protocol associated with
                                        # the communications channel when it was opened.
    ERR_INVALID_FILTER_ID =		0x16	# Filter identifier is not recognized.
    ERR_NO_FLOW_CONTROL =		0x17	# No ISO15765 flow control filter is set, or no filter matches the header of an outgoing message.
    ERR_NOT_UNIQUE =			0x18	# An existing filter already matches this header or node identifier.
    ERR_INVALID_BAUDRATE =		0x19	# Unable to honor requested Baud rate within required tolerances.
    ERR_INVALID_DEVICE_ID =		0x1A	# PassThru device identifier is not recognized.

    # Message filter types for fcns PassThruStartMsgFilter(), PassThruStopMsgFilter():
    PASS_FILTER =			    0x01	# PassThru device adds receive messages matching the Mask and Pattern criteria to its receive message queue.
    BLOCK_FILTER =			    0x02	# PassThru device ignores receive messages matching the Mask and Pattern criteria.
    FLOW_CONTROL_FILTER =		0x03	# PassThru device adds receive messages matching the Mask and Pattern criteria to its receive message queue.
                                        # The PassThru device transmits a flow control message (only for ISO 15765-4) when receiving multi-segmented frames.

    def __init__(self):
        return


class Voltages:

    # Programming Voltages (Pins 0, 6, 9, 11-15):
    # => value in mV (valid range: 5000 mV = 0x1388 to 20000 mV = 0x4e20) => only pins 0, 6, 9, 11-14
    SHORT_TO_GROUND =			0xFFFFFFFE	# only pin 15
    VOLTAGE_OFF =			    0xFFFFFFFF	# all pins (0, 6, 9, 11-15)

    def __init__(self):
        return


class Flags:

    # Loopback setting (ioctl GET_CONFIG/SET_CONFIG: parameter LOOPBACK):
    OFF =				0x00
    ON =				0x01

    # Data bits setting (ioctl GET_CONFIG/SET_CONFIG: parameter DATA_BITS):
    DATA_BITS_8 =			0x00
    DATA_BITS_7 =			0x01

    # Parity setting (ioctl GET_CONFIG/SET_CONFIG: parameter PARITY):
    NO_PARITY =			0x00
    ODD_PARITY =		0x01
    EVEN_PARITY =		0x02

    # J1850-PWM (ioctl GET_CONFIG/SET_CONFIG: parameter NETWORK_LINE):
    BUS_NORMAL =		0x00
    BUS_PLUS =			0x01
    BUS_MINUS =			0x02

    # Connect flags:
    CAN_29BIT_ID =		    0x00000100
    ISO9141_NO_CHECKSUM =	0x00000200
    CAN_ID_BOTH =		    0x00000800
    ISO9141_K_LINE_ONLY =	0x00001000

    # Rx status flags:
    #CAN_29BIT_ID =		    0x00000100	# CAN ID Type: 0 = 11-bit, 1 = 29-bit
    ISO15765_ADDR_TYPE =	0x00000080
    ISO15765_PADDING_ERROR =0x00000010
    TX_DONE =			    0x00000008
    RX_BREAK =		        0x00000004	# Receive Break: 0 = No Break indication, 1 = Break indication present
    ISO15765_FIRST_FRAME =	0x00000002	# ISO15765-2 only: 0 = No First Frame indication, 1 = First Frame indication
    START_OF_MESSAGE =	    0x00000002	# ISO15765-2 only: 0 = No First Frame indication, 1 = First Frame indication
    TX_MSG_TYPE =		    0x00000001	# Receive Indication/Transmit Confirmation: 0 = Rx Frame indication, 1 = Tx Frame confirmation

    # Tx flags:
    SCI_TX_VOLTAGE =		0x00800000	# SCI programming: 0 = do not apply voltage after transmitting message, 1 = apply voltage(20V) after transmitting message
    SCI_MODE =		        0x00400000
    BLOCKING =		        0x00010000	# 02.02-API: Tx blocking mode: 0 = non-blocking transmit request, 1 = blocking transmit request
                                        # 04.04-API: this value is reserved for J2534-2 !
                                        # NOTE: not really needed, instead a timeout value > 0 can be used with PassThruWriteMsgs()
    WAIT_P3_MIN_ONLY =	    0x00000200
    #CAN_29BIT_ID =		    0x00000100  # CAN ID Type: 0 = 11-bit, 1 = 29-bit
    CAN_EXTENDED_ID =		0x00000100
    #ISO15765_ADDR_TYPE =	0x00000080	# ISO15765-2 Addressing mode: 0 = No extended address, 1 = Extended address is first byte following the CAN ID
    ISO15765_EXT_ADDR =	    0x00000080
    ISO15765_FRAME_PAD =	0x00000040	# ISO15765-2 Frame Pad mode: 0 = No frame padding, 1 = Zero pad FlowControl, Single and Last ConsecutiveFrame to full CAN frame size.
    TX_NORMAL_TRANSMIT =	0x00000000

    def __init__(self):
        return


class Loader:

    def __init__(self):

        if platform.architecture()[0] == '32bit':
            self._PASSTHRU_REG = r"Software\\PassThruSupport.04.04\\"
        else:
            self._PASSTHRU_REG = r"Software\\Wow6432Node\\PassThruSupport.04.04\\"

    def get_device_list(self):

        BaseKey = _winreg.OpenKeyEx(_winreg.HKEY_LOCAL_MACHINE, self._PASSTHRU_REG)

        count = _winreg.QueryInfoKey(BaseKey)[0]

        J2534_Device_Reg_Info = []

        for i in range(count):
            DeviceKey = _winreg.OpenKeyEx(BaseKey, _winreg.EnumKey(BaseKey, i))
            Name = _winreg.QueryValueEx(DeviceKey, 'Name')[0]
            FunctionLibrary = _winreg.QueryValueEx(DeviceKey, 'FunctionLibrary')[0]
            J2534_Device_Reg_Info.append((Name, FunctionLibrary))

        return J2534_Device_Reg_Info

    def load_dll(self, dll_path=None):
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

        # Load our dll and all dependencies
        loadedDll = None
        try:
            # Windows supports all dll
            dllFile = name
            loadedDll = ctypes.WinDLL(dllFile)
        except Exception as e:
            print(e)
            print("Could be a missing dependancy dll for '%s'." % dllFile)
            print("(Directory for dll: '%s')\n" % dll_path)
            os.chdir(dir)
            exit(1)
        os.chdir(dir)
        return loadedDll


class j2534:

    def __init__(self, dll_path=None, device_index=0):

        # load default devices
        dll_loader = Loader()
        self.DeviceList = dll_loader.get_device_list()

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

            if len(self.DeviceList) > 0:
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

        return self._pPassThruConnect(self._hDeviceID, ctypes.c_ulong(protocol_id), ctypes.c_ulong(flags), ctypes.c_ulong(baud_rate), ctypes.byref(self._ChannelID))

    def pass_thru_disconnect(self):

        return self._pPassThruDisconnect(self._ChannelID)

    def pass_thru_read_version(self):

        f_ver = create_string_buffer(80)
        d_ver = create_string_buffer(80)
        a_ver = create_string_buffer(80)

        error = self._pPassThruReadVersion(self._hDeviceID, f_ver, d_ver, a_ver)

        return f_ver.value, d_ver.value, a_ver.value

    def pass_thru_get_last_error(self):

        err = create_string_buffer(80)

        self._pPassThruGetLastError(err)

        return err.value

    def create_passtrhu_msg_struc(self, protocol_id, rx_status, tx_flags, timestamp, data_size, extra_data_index, data):

        struct = PASSTHRU_MSG()

        data_buffer = (c_uint8 * data_size).from_buffer(data)

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
        number_of_read_messages = ctypes.c_ulong(number_of_messages)

        err = self._pPassThruReadMsgs(self._ChannelID, messages, ctypes.byref(number_of_read_messages), ctypes.c_ulong(timeout))

        return err

    def pass_thru_start_msg_filter(self, filter_type, mask_message, pattern_message, flow_control_message, message_id):

        message_id_ref = ctypes.c_ulong(message_id)

        err = self._pPassThruStartMsgFilter(self._ChannelID, ctypes.c_ulong(filter_type), ctypes.byref(mask_message), ctypes.byref(pattern_message), ctypes.byref(flow_control_message), ctypes.byref(message_id_ref))

        return err, message_id_ref.value

    def pass_thru_stop_msg_filter(self, message_id):

        return self._pPassThruStopMsgFilter(self._ChannelID, ctypes.c_ulong(message_id))

    def pass_thru_write_msgs(self, messages, number_of_messages, timeout):

        return self._pPassThruWriteMsgs(self._ChannelID, ctypes.byref(messages), ctypes.c_ulong(number_of_messages), ctypes.c_ulong(timeout))

    def pass_thru_start_periodic_msg(self, message, message_id, time_interval):

        message_id_ref = ctypes.c_ulong(message_id)

        err = self._pPassThruStartPeriodicMsg(self._ChannelID, ctypes.byref(message), ctypes.c_ulong(message_id_ref), ctypes.c_ulong(time_interval))

        return err, message_id_ref.value

    def pass_thru_stop_periodic_msg(self, message_id):

        return self._pPassThruStopPeriodicMsg(self._ChannelID, ctypes.c_ulong(message_id))

    def pass_thru_ioctl(self, ioctl_id, input, output):

        return self._pPassThruIoctl(self._hDeviceID, ctypes.c_ulong(ioctl_id), ctypes.byref(input), ctypes.byref(output))

    def pass_thru_set_programming_voltage(self, pin_number, voltage):

        return self._pPassThruSetProgrammingVoltage(self._hDeviceID, ctypes.c_ulong(pin_number), ctypes.c_ulong(voltage))

    def load_dll(self, dll_path):

        if not os.path.isfile(dll_path):
            return False

        os.chdir(os.path.dirname(dll_path))

        self._dll = ctypes.WinDLL(dll_path)

        if self._dll is None:
            return False

        #
        # Function prototypes:
        #

        # typedef long(*J2534_PassThruOpen)(void* pName, unsigned long *pDeviceID);	# 0404-API only
        self._pPassThruOpen = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_char_p, ctypes.POINTER(ctypes.c_ulong))(("PassThruOpen", self._dll))

        # typedef long(*J2534_PassThruClose)(unsigned long DeviceID);			# 0404-API only
        self._pPassThruClose = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong)(("PassThruClose", self._dll))

        # typedef long(*J2534_PassThruConnect_0202)(unsigned long ProtocolID, unsigned long Flags, unsigned long *pChannelID);							# 0202-API
        try:
            ptr = getattr(self._dll, 'PassThruConnect_0202')

            self._pPassThruConnect_0202 = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong))(("PassThruConnect_0202", self._dll))
        except:
            self._pPassThruConnect_0202 = None

        # typedef long(*J2534_PassThruConnect_0404)(unsigned long DeviceID, unsigned long ProtocolID, unsigned long Flags, unsigned long BaudRate, unsigned long *pChannelID);	# 0404-API
        try:
            ptr = getattr(self._dll, 'PassThruConnect_0404')
            self._pPassThruConnect_0404 = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong))(("PassThruConnect_0404", self._dll))
        except:
            self._pPassThruConnect_0404 = None

        # typedef long(*J2534_PassThruConnect)(unsigned long DeviceID, unsigned long ProtocolID, unsigned long Flags, unsigned long BaudRate, unsigned long *pChannelID);	# 0404-API
        self._pPassThruConnect = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong))(("PassThruConnect", self._dll))

        # typedef long(*J2534_PassThruDisconnect)(unsigned long ChannelID);
        self._pPassThruDisconnect = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong)(("PassThruDisconnect", self._dll))

        # typedef long(*J2534_PassThruReadVersion_0202)(char *pFirmwareVersion, char *pDllVersion, char *pApiVersion);								# 0202-API
        try:
            ptr = getattr(self._dll, 'PassThruReadVersion_0202')
            self._pPassThruReadVersion_0202 = ctypes.WINFUNCTYPE(ctypes.c_long, c_char_p, c_char_p, c_char_p)(("PassThruReadVersion_0202", self._dll))
        except:
            self._pPassThruReadVersion_0202 = None

        # typedef long(*J2534_PassThruReadVersion_0404)(unsigned long DeviceID, char *pFirmwareVersion, char *pDllVersion, char *pApiVersion);					# 0404-API
        try:
            ptr = getattr(self._dll, 'PassThruReadVersion_0202')
            self._pPassThruReadVersion_0404 = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong, c_char_p, c_char_p, c_char_p)(("PassThruReadVersion_0404", self._dll))
        except:
            self._pPassThruReadVersion_0404 = None

        # typedef long(*J2534_PassThruReadVersion)(unsigned long DeviceID, char *pFirmwareVersion, char *pDllVersion, char *pApiVersion);					# 0404-API
        self._pPassThruReadVersion = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong, c_char_p, c_char_p, c_char_p)(("PassThruReadVersion", self._dll))

        # typedef long(*J2534_PassThruGetLastError)(char *pErrorDescription);
        self._pPassThruGetLastError = ctypes.WINFUNCTYPE(ctypes.c_long, c_char_p)(("PassThruGetLastError", self._dll))

        # typedef long(*J2534_PassThruReadMsgs)(unsigned long ChannelID, PASSTHRU_MSG *pMsg, unsigned long *pNumMsgs, unsigned long Timeout);
        self._pPassThruReadMsgs = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong, ctypes.Array, ctypes.POINTER(ctypes.c_ulong), ctypes.c_ulong)(("PassThruReadMsgs", self._dll))

        # typedef long(*J2534_PassThruStartMsgFilter)(unsigned long ChannelID, unsigned long FilterType, PASSTHRU_MSG *pMaskMsg, PASSTHRU_MSG *pPatternMsg, PASSTHRU_MSG *pFlowControlMsg, unsigned long *pMsgID);
        self._pPassThruStartMsgFilter = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong, ctypes.Array, ctypes.Array, ctypes.Array, ctypes.POINTER(ctypes.c_ulong))(("PassThruStartMsgFilter", self._dll))

        # typedef long(*J2534_PassThruStopMsgFilter)(unsigned long ChannelID, unsigned long MsgID);
        self._pPassThruStopMsgFilter = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong)(("PassThruStopMsgFilter", self._dll))

        # typedef long(*J2534_PassThruWriteMsgs)(unsigned long ChannelID, PASSTHRU_MSG *pMsg, unsigned long *pNumMsgs, unsigned long Timeout);
        self._pPassThruWriteMsgs = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong, ctypes.Array, ctypes.POINTER(ctypes.c_ulong), ctypes.c_ulong)(("PassThruWriteMsgs", self._dll))

        # typedef long(*J2534_PassThruStartPeriodicMsg)(unsigned long ChannelID, PASSTHRU_MSG *pMsg, unsigned long *pMsgID, unsigned long TimeInterval);
        self._pPassThruStartPeriodicMsg = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong, ctypes.POINTER(PASSTHRU_MSG), ctypes.POINTER(ctypes.c_ulong), ctypes.c_ulong)(("PassThruStartPeriodicMsg", self._dll))

        # typedef long(*J2534_PassThruStopPeriodicMsg)(unsigned long ChannelID, unsigned long MsgID);
        self._pPassThruStopPeriodicMsg = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong)(("PassThruStopPeriodicMsg", self._dll))

        # typedef long(*J2534_PassThruIoctl)(unsigned long HandleID, unsigned long IoctlID, void *pInput, void *pOutput);
        self._pPassThruIoctl = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p)(("PassThruIoctl", self._dll))

        # typedef long(*J2534_PassThruSetProgrammingVoltage_0202)(unsigned long PinNumber, unsigned long Voltage);								# 0202-API
        try:
            ptr = getattr(self._dll, 'PassThruSetProgrammingVoltage_0202')
            self._pPassThruSetProgrammingVoltage_0202 = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong)(("PassThruSetProgrammingVoltage_0202", self._dll))
        except:
            self._pPassThruSetProgrammingVoltage_0202 = None

        # typedef long(*J2534_PassThruSetProgrammingVoltage_0404)(unsigned long DeviceID, unsigned long PinNumber, unsigned long Voltage);					# 0404-API
        try:
            ptr = getattr(self._dll, 'PassThruSetProgrammingVoltage_0404')
            self._pPassThruSetProgrammingVoltage_0404 = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong)(("PassThruSetProgrammingVoltage_0404", self._dll))
        except:
            self._pPassThruSetProgrammingVoltage_0202 = None

        # typedef long(*J2534_PassThruSetProgrammingVoltage)(unsigned long DeviceID, unsigned long PinNumber, unsigned long Voltage);					# 0404-API
        self._pPassThruSetProgrammingVoltage = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong)(("PassThruSetProgrammingVoltage", self._dll))

        return True


if __name__ == '__main__':


#    [(u'MDI', u'C:\\Program Files (x86)\\GM MDI Software\\Products\\MDI\\Dynamic Link Libraries\\BVTX4J32.dll'),
#     (u'MDI 2', u'C:\\Program Files (x86)\\GM MDI Software\\Products\\MDI 2\\Dynamic Link Libraries\\BVTX4J32.dll'), (
#     u'MongoosePro Chrysler',
#     u'C:\\Program Files (x86)\\Drew Technologies, Inc\\J2534\\MongoosePro Chrysler\\monps432.dll'),
#     (u'McS1', u'C:\\Windows\\SYSTEM\\McS1v232.DLL'),
#     (u'Tech2', u'C:\\Program Files (x86)\\GM\\Tech2 J2534 DLL\\Tech2_32.dll'),
#     (u'Intrepid', u'C:\\Windows\\system32\\icsneo40.dll'),
#     (u'Intrepid neoVI Fire/Red', u'C:\\Windows\\system32\\icsJ2534Fire.dll'),
#     (u'Intrepid neoVI Yellow', u'C:\\Windows\\system32\\icsJ2534Yellow.dll'),
#     (u'Intrepid ValueCAN3', u'C:\\Windows\\system32\\icsJ2534VCAN3.dll'),
#     (u'J-Box 2', u'C:\\Program Files (x86)\\Launch Tech\\J2534\\J-Box 2\\JBox2.dll')]


    #
    # load specific DLL library OR load library found in system (leave first param empty)
    #
    #interface = j2534('E:\dev\work\j2534_python\j2534dll\J2534.dll')
    #interface = j2534()
    interface = j2534(device_index=0)

    #
    # check if the interface was properly initialized
    #
    if not interface.initialized:
        print "[i] cannot load DLL library"
        exit(1)

    #
    # print a list of device list
    #
    print interface.DeviceList

    #
    # open device
    #
    status = interface.pass_thru_open("DeviceNameToConnect")

    # check connection status
    if status == Errors.STATUS_NOERROR:
        print "[i] device successfully opened"
    else:
        print "[!] error code " + interface.pass_thru_get_last_error()
        exit(2)

    #
    # connect using proper interface ID, flags and baud rate
    #
    interface_id = Protocols.ISO15765
    connection_flags = 0
    baud_rate = 500000

    status = interface.pass_thru_connect(interface_id, connection_flags, baud_rate)

    #
    # read version from the device
    #
    firmaware_version, dll_version, api_version = interface.pass_thru_read_version()

    print "[i] firmware version " + firmaware_version
    print "[i] DLL version " + dll_version
    print "[i] API version " + api_version

    #
    # read some message
    #
    protocol_id = Protocols.ISO15765
    rx_status = 0x00
    tx_flags = 0x00
    timestamp = 0x00
    data_size = 6
    extra_data_index = 0
    data = [0x00, 0x00, 0x07, 0xDF, 0x01, 0x00]

    message = interface.create_passtrhu_msg_struc(protocol_id, rx_status, tx_flags, timestamp, data_size, extra_data_index, data)

    #err = interface.pass_thru_read_msgs(message, 1, 100)
    #err = interface.pass_thru_write_msgs(message, 100, 1)

    #
    # disconnect main connection channel
    #
    status = interface.pass_thru_disconnect()

    #
    # close device connection
    #
    status = interface.pass_thru_close()
