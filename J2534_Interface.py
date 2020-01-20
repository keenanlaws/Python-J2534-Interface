from J2534_Library import (
    Protocols,
    BaudRate,
    Ioctls,
    Filters,
    Voltages,
    PinNumber,
    Flags,
    ConnectFlags,
    TxFlags,
)

from J2534_Library import Utils as Utility
from J2534_Library import PassThru
import binascii


# ============================================  INTERFACE TO J2534 LIBRARY  ===========================================
class J2534:
    def __init__(self):
        self.supvar = []
        self.openSettings = []
        self.txData = []
        self.toolName = []
        self.toolPath = []
        self.toolConnect = []
        self._1A87 = []
        self._1A87Decoded = []
        self._21E5Decoded = []
        self.control_module_data = None

        self.tool = None
        self.baudrate_ = None
        self.connect_flag = None
        self.rx_timeout = None
        self.tx_timeout = None
        self.tx_flag = None
        self.protocol = None

        self.JTOOL = None
        self.isConnected = [0]

        self.tx_id_address = []
        self.rx_id_address = []

        self.transmit_data = []
        self.positive_response = []
        self.output_string = []
        self.start_diagnostic_session = []
        self.data_index_start = []
        self.data_index_end = []
        self.security_level = []
        self.format_data = []
        self.communication_type = []

        self.supplier = []
        self.variant = []
        
    # if you set a formatter in your function you need to set it up in here to format data output...
    def outputFormatter(self, dataInput):

        dirty = dataInput

        if self.format_data[0] == '0001':

            clean = str(binascii.unhexlify(dirty).decode("utf-8"))

            if not self.output_string:

                return clean

            else:

                output = self.output_string[0] + clean

                return output

    # DO NOT CALL THIS IT IS AN INTERNAL FUNCTION YOU DO NOT NEED TO TOUCH IT!!!...
    # this will set a flag upon tool connection, so you will not try to open tool that is already open...
    def setConnectFlag(self, state):

        #  if flag state is set to 0 tool is not connected if set 1 connection has already been made...

        if state == 0:

            self.isConnected.clear()

            self.isConnected.insert(0, 0)

            self.JTOOL.pass_thru_close()

            return False

        elif state == 1:

            self.isConnected.clear()

            self.isConnected.insert(0, 1)

            pass

    # DO NOT CALL THIS IT IS AN INTERNAL FUNCTION YOU DO NOT NEED TO TOUCH IT!!!...
    # ONLY USED INSIDE txNrx FUNCTION!!!, this opens connection and sets flow filters...
    def connectFilter(self):

        if self.isConnected[0] == 0:

                if self.JTOOL.pass_thru_connect(self.protocol, self.connect_flag, self.baudrate_) == 0:

                        if self.flow_filter(self.tx_id_address[0], self.rx_id_address[0]):

                            self.setConnectFlag(1)

                            return True

                else:

                    self.setConnectFlag(0)

                    return False

        else:

            return True

    # DO NOT CALL THIS IT IS AN INTERNAL FUNCTION YOU DO NOT NEED TO TOUCH IT!!!...
    # ONLY USED INSIDE txNrx FUNCTION!!!, this sets vars for tx, rx structure sends data and recieves data...
    def sendNdump(self):

        txPayload = self.tx_id_address[0] + self.transmit_data[0]  # tx id and data to be sent ..

        tx = self.JTOOL.pass_thru_structure(self.protocol, 0, self.tx_flag, 0, len(txPayload), 0, txPayload)

        rx = self.JTOOL.pass_thru_structure(self.protocol, 0, 0, 0, 0, 0, [])

        if self.JTOOL.pass_thru_write(tx, 1, self.tx_timeout) == 0:

            for n in range(5):  # loop through passthru read IF completes with no errors will return 0...

                if self.JTOOL.pass_thru_read(rx, 1, self.rx_timeout) == 0:
                    # print(rx.dump())

                    if rx.DataSize > 5:

                        if '7F' not in rx.dump_data():

                            if self.positive_response[0] in rx.dump_data():

                                line = rx.dump_data().replace(" ", "", rx.DataSize)

                                output = [line[i: i + 2] for i in range(0, len(line), 2)]

                                if rx.DataSize == len(output):  # lets make sure we got all the data out...

                                    try:  #  try index, if there is no data index dump it all...
                                        start = self.data_index_start[0]

                                        end = self.data_index_end[0]

                                        output = line[start:end]

                                        if not self.format_data:

                                            return output

                                        else:

                                            return self.outputFormatter(output)  # send indexed data to formatter...

                                    except IndexError:

                                        return rx.dump_data()

                        else:
                            if  len(self.start_diagnostic_session) == 0: # if no diag session needed dump data...

                                return rx.dump_data()

                            else:
                                if self.start_diagnostic_session[0] == 'yes':  # if diag session needed lets start it...

                                    if self.extendedDiagnostic() \
                                            and self.sendNdump():  #  start diag and recall this function...

                                        pass

            else:

                self.setConnectFlag(0)

                return False

    # DO NOT CALL THIS IT IS AN INTERNAL FUNCTION YOU DO NOT NEED TO TOUCH IT!!!...
    # this will configure all the data automatically for you from the function you pass to it...
    def functionBuilder(self, ecu_id, func_in):

        self.tx_id_address.clear()

        self.rx_id_address.clear()

        self.transmit_data.clear()

        self.positive_response.clear()

        self.output_string.clear()

        self.start_diagnostic_session.clear()

        self.data_index_start.clear()

        self.data_index_end.clear()

        self.security_level.clear()

        self.format_data.clear()

        self.communication_type.clear()

        self.tx_id_address.insert(0, ecu_id[0])

        self.rx_id_address.insert(0, ecu_id[1])

        for item in func_in:

            if item.startswith('[tx]'):

                data = item.replace('[tx]-', '')

                data = [int(data[i: i + 2], 16) for i in range(0, len(data), 2)]

                self.transmit_data.insert(0, data)

            elif item.startswith('[rx]'):

                data = item.replace('[rx]-', '')

                data = [data[i: i + 2] for i in range(0, len(data), 2)]

                data = ' '.join(map(str, data))

                self.positive_response.insert(0, data)

            elif item.startswith('[st]'):

                data = item.replace('[st]-', '')

                self.output_string.insert(0, data)

            elif item.startswith('[dg]'):

                data = item.replace('[dg]-', '')

                self.start_diagnostic_session.insert(0, data)

            elif item.startswith('[ix]'):

                data = item.replace('[ix]-', '')

                data = data.replace(':', '')

                x, y = data[0:2], data[2:4]

                x = int(x)

                y = int(y)

                self.data_index_start.insert(0, x)

                self.data_index_end.insert(0, y)

            elif item.startswith('[sc]'):

                data = item.replace('[sc]-', '')

                self.security_level.insert(0, data)

            elif item.startswith('[fm]'):

                data = item.replace('[fm]-', '')

                self.format_data.insert(0, data)

            elif item.startswith('[tp]'):

                data = item.replace('[tp]-', '')

                self.communication_type.insert(0, data)

        for item in func_in:

            if item.startswith('[rx]'):

                pass

            else:

                data = ' '.join('{:02X}'.format(a) for a in self.rx_id_address[0])

                self.positive_response.insert(0, data)

        return True

    # DO NOT CALL THIS IT IS AN INTERNAL FUNCTION YOU DO NOT NEED TO TOUCH IT!!!...
    def flow_filter(self, tx, rx):

        mask = self.JTOOL.pass_thru_structure(j2534.protocol, 0, j2534.tx_flag, 0, 4, 0, [0xFF, 0xFF, 0xFF, 0xFF])

        pattern = self.JTOOL.pass_thru_structure(j2534.protocol, 0, j2534.tx_flag, 0, 4, 0, rx)

        flow_control = self.JTOOL.pass_thru_structure(j2534.protocol, 0, j2534.tx_flag, 0, 4, 0, tx)

        err, msg_id = self.JTOOL.pass_thru_start_msg_filter(Filters.FLOW_CONTROL_FILTER, mask, pattern, flow_control)

        if err == 0:

            return True

        else:

            return False

    # DO NOT CALL THIS IT IS AN INTERNAL FUNCTION YOU DO NOT NEED TO TOUCH IT!!!...
    def open(self, data):

        self.toolConnect.clear()

        self.toolConnect.insert(0, data[0])  # device index of tool you want to use...

        self.toolConnect.insert(1, data[1])  # communication protocol...

        self.toolConnect.insert(2, data[2])  # tx flag...

        self.toolConnect.insert(3, data[3])  # rx delay...

        self.toolConnect.insert(4, data[4])  # tx delay...

        self.toolConnect.insert(5, data[5])  # connnect flag...

        self.toolConnect.insert(6, data[6])  # baudrate...

        self.tool = self.toolConnect[0]

        self.protocol = self.toolConnect[1]

        self.tx_flag = self.toolConnect[2]

        self.rx_timeout = self.toolConnect[3]

        self.tx_timeout = self.toolConnect[4]

        self.connect_flag = self.toolConnect[5]

        self.baudrate_ = self.toolConnect[6]

        # load specific DLL library OR load library found in system (leave first param empty)

        self.JTOOL = PassThru(device_index=self.tool)

        if not self.JTOOL.initialized:  # check if the interface was properly initialized

            print("[i] cannot load DLL library")

            return 1

        if self.JTOOL.pass_thru_open() == 0:  # open device

            # read version from the device

            firmware_version, dll_version, api_version = self.JTOOL.pass_thru_version()

            firmware_version = firmware_version.decode("utf-8")

            dll_version = dll_version.decode("utf-8")

            api_version = api_version.decode("utf-8")

            return firmware_version

        else:

            self.JTOOL.pass_thru_close()

            return False

    # DO NOT CALL THIS IT IS AN INTERNAL FUNCTION YOU DO NOT NEED TO TOUCH IT!!!...
    def extendedDiagnostic(self):

        txPayload = self.tx_id_address[0] + [0x10, 0x92]  # tx id and data to be sent ..

        txLen = len(txPayload)  # length of tx id and data...

        tx = self.JTOOL.pass_thru_structure(self.protocol, 0, self.tx_flag, 0, txLen, 0, txPayload)

        rx = self.JTOOL.pass_thru_structure(self.protocol, 0, 0, 0, 0, 0, [])

        if self.connectFilter():

            if self.JTOOL.pass_thru_write(tx, 1, self.tx_timeout) == 0:

                for n in range(5):  # loop through passthru read IF completes with no errors will return 0...

                    if self.JTOOL.pass_thru_read(rx, 1, self.rx_timeout) == 0:

                        if rx.DataSize > 5:

                            if '7F' not in rx.dump_data():

                                if '50 92' in rx.dump_data():

                                    line = rx.dump_data().replace(" ", "", rx.DataSize)

                                    output = [line[i: i + 2] for i in range(0, len(line), 2)]

                                    if rx.DataSize == len(output):  # lets make sure we got all the data out...

                                        return True

                else:

                    self.setConnectFlag(0)

                    return False

    # this will list all the j2534 tools that are installed on your computer...
    def tools(self):

        count = 0

        try:

            for item in PassThru().DeviceList:

                self.toolName.append(item[0])

                self.toolPath.append(item[1])

                count += 1

            return [self.toolName, self.toolPath]

        except IndexError:

            return

    # this is the main function you pass your function list to then it does the rest...
    def txNrx(self, ecu_id, dataInput):

        if self.functionBuilder(ecu_id, dataInput) and self.connectFilter():

                Output = self.sendNdump()

                if Output:

                    return Output

j2534 = J2534()
# =======================================================  END  =======================================================


# ================================================= SET TOOL CONNECTION ===============================================
class Connection:
    def __init__(self):
        pass

    def Can(self, tool):
        openTool = j2534.open([tool,
                    Protocols.ISO15765,
                    TxFlags.ISO15765_FRAME_PAD,
                    250,
                    250,
                    ConnectFlags.NONE,
                    BaudRate.CAN_500000
                    ])
        return openTool

    def extCan(self, tool):
        openTool = j2534.open([tool,
                    Protocols.ISO15765,
                    TxFlags.ISO15765_CAN_ID_29,
                    250,
                    250,
                    ConnectFlags.CAN_29BIT_ID,
                    BaudRate.CAN_500000
                    ])
        return openTool

connect = Connection()
# =======================================================  END  =======================================================


# ====================================  SET TX & RX ID'S FOR ALL MODULES BEING USED   =================================
class ModuleTxRxId:
    def __init__(self):
        return

    ecu = [
        [0x00, 0x00, 0x07, 0xE0],  # hex format tx data
        [0x00, 0x00, 0x07, 0xE8],  # hex format rx data
    ]

    ecu2 = [
        [0x18, 0xDA, 0x10, 0xF1],  # hex format tx data
        [0x18, 0xDA, 0xF1, 0x10],  # hex format rx data
    ]

    tipm = [
        [0x00, 0x00, 0x06, 0x20],  # hex format tx data
        [0x00, 0x00, 0x05, 0x04],  # hex format rx data
    ]

module = ModuleTxRxId()
# =======================================================  END  =======================================================


# ======================================  LIST TOOLS INSTALLED ON THIS COMPUTER  ======================================
# this for loop will list one tool per line uncomment which one you want to use...
for tool in j2534.tools()[0]: print(tool)  #  this will print tool name
# for tool in j2534.tools()[1]: print(tool)  # this will print tool dll path

# this way will print a list containing all the tools installed
# print(j2534.tools()[0])  #  this will print tool name
# print(j2534.tools()[1])  #  this will print tool dll path
# =======================================================  END  =======================================================


# ===========================================  OPEN TOOL AND SET PARAMETERS  ==========================================
# by using print(connect.extCan(1)) it will print tool name, firmware, serial number...
# example 'connect.extCan(1)'  the 1 that is passed is the tools index you want to use...
# REMEMBER INDEX STARTS AT 0 NOT 1 ONE uncomment which one you want to use...
# print(connect.extCan(1))

# use this without print if you want to open without printing all tools info...
# example connect.extCan(1)
connect.extCan(1)
# connect.Can(1)
# =======================================================  END  =======================================================


udsVinCurrent = [
            '[tx]-22f190',
            '[rx]-62F190',
            '[st]-[i] Current Vin Number ',
            '[dg]-yes',
            '[ix]-14:48',
            '[fm]-0001',
            '[tp]-uds'
        ]
udsVinOriginal = [
            '[tx]-22f1A0',
            '[rx]-62F1A0',
            '[st]-[i] Original Vin Number ',
            '[dg]-yes',
            '[ix]-14:48',
            '[sc]-level-1',
            '[fm]-0001',
            '[tp]-uds'
        ]
udsReset = [
            '[tx]-1101',
            '[rx]-5101',
            '[dg]-yes',

]

VinCurrent = [
            '[tx]-1A90',
            '[rx]-5A90',
            '[st]-[i] Current Vin Number ',
            '[dg]-yes',
            '[ix]-12:46',
            '[fm]-0001',
            '[tp]-kwp'
        ]
VinOriginal = [
            '[tx]-1A88',
            '[rx]-5A88',
            '[st]-[i] Original Vin Number ',
            '[dg]-yes',
            '[ix]-12:46',
            '[sc]-level-1',
            '[fm]-0001',
            '[tp]-kwp'
        ]
Reset = [
            '[tx]-1101',
            '[rx]-5192',
            '[dg]-yes',
            '[tp]-kwp'
]


# print(j2534.txNrx(module.tipm, udsVinOriginal))
# print(j2534.txNrx(module.tipm, udsVinCurrent))
# print(j2534.txNrx(module.tipm, udsReset))
# j2534.txNrx(module.ecu2, VinCurrent)
print(j2534.txNrx(module.ecu2, VinOriginal))
# print(j2534.txNrx(module.ecu2, ['[tx]-1A87']))