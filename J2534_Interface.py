 
# * Copyright (c) 2020, ecuunlock
# *
# * EMAIL = engineering@ecuunlock.com
# * WEBSITE = www.ecuunlock.com
# * PHONE = (419)-330-9774
# *
# * All rights reserved.
# * Redistribution and use in source and binary forms, with or without modification, 
# * are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright notice, this list 
# * of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice, this 
# * list of conditions and the following disclaimer in the documentation and/or other
# * materials provided with the distribution.
# * Neither the name of the organization nor the names of its contributors may be 
# * used to endorse or promote products derived from this software without specific 
# * prior written permission.
# * 
# * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# * PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


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

for tool in j2534.tools()[0]: print(tool)  #  this will print one tool name per line...
    
# for tool in j2534.tools()[1]: print(tool)  # this will print one tool dll path per line...


# print(j2534.tools()[0])  #  this will print a list of tool names installed

# print(j2534.tools()[1])  #  this will print a list tool dll path

# =======================================================  END  =======================================================


# ===========================================  OPEN TOOL AND SET PARAMETERS  ==========================================

# print(connect.extCan(1)) # uncomment and use to connect extended 29bit can using tool 
                           # indexed at #1 position from tools function above. When you 
                           # call print it will print connected tool info name, firmware, serial#...

connect.extCan(1)  # uncomment and use to connect extended 29bit can using tool 
                   # indexed at #1 position from tools function above.
    
# connect.Can(1)  # uncomment and use to connect 11bit can using tool 
                  # indexed at #1 position from tools function above. When you 
                  # call print it will print connected tool info name, firmware, serial#...

# =======================================================  END  =======================================================


# LOOK BELOW, HERE ARE SOME EXAMPLES OF HOW TO BUILD YOUR FUNCTIONS!!!!!!!

udsVinCurrent = [
            '[tx]-22f190',                      #  '[tx]-22f190'  this sets up function to tx data        =  22 F1 90...
            '[rx]-62F190',                      #  '[rx]-62F190'  this sets up functions positive rx data =  62 F1 90...
            '[st]-[i] Current Vin Number ',     #  '[st]-[i] Current Vin Number '  this sets the rx data string to be printed...
            '[dg]-yes',                         #  '[dg]-yes' tells function to start a extended diag session...
            '[ix]-14:48',                       #  '[ix]-14:48' the index of the data you are looking for byte 14 through 48...
            '[fm]-0001',                        #  '[fm]-0001' format name you set of func to send you output to format...
            '[tp]-uds'                          #  '[tp]-uds' sets type of communication you are using uds, kwp and so on...
        ]                                       #   ONLY USE FUNC DATA NEEDED...
                                                #  EXAMPLE THIS FUNC WILL OUTPUT = '[i] Current Vin Number 1C4PJLCB8EW313490'
                                                

VinCurrent = [
            '[tx]-1A90',
            '[rx]-5A90',
            '[st]-[i] Current Vin Number ',
            '[dg]-yes',
            '[ix]-12:46',
            '[fm]-0001',
            '[tp]-kwp'
        ]

Reset = [
            '[tx]-1101',                         #  AS YOU SEE WITH THIS 'Reset' FUNCTION ONLY USE THE PARAMETERS YOU NEED!!...
            '[rx]-5192',
            '[dg]-yes',
            '[tp]-kwp'
]


print(j2534.txNrx(module.ecu2, VinCurrent))  # LOOK LOOK(-)(-) 'j2534.txNrx(module.ecu2, VinCurrent)' INSIDE FUNCTION PARAMETERS
                                             # THE 'module.ecu2' IS SETTING THE EXTENDED CAN 29BIT IDENTIFIERS FOR ECU. IF YOU WANT
                                             # TO SET 11BIT ECU IDENTIFIERS JUST CALL 'module.ecu'. SETUP YOUR OTHER ECU ADDRESSES
                                             # UNDER 'class ModuleTxRxId:' TO SETUP FOR OTHER MODULES YOU PLAN ON TALKING TO...
                                             # TO PRINT THE OUTPUT '[i] Current Vin Number 1C4PJLCB8EW313490' TO THE TERMINAL
                                             # DONT FORGET TO CALL THE FUNCTION INSIDE THE Print('function here') FUNCTION!!!!...
                                           
# THIS FUNCTION ABOVE RETURNS = '[i] Original Vin Number 1C4PJLCB8EW313490'
                    
                    

# print(j2534.txNrx(module.ecu2, ['[tx]-1A87'])) # CALLING FUNCTION LIKE THIS IS THE EASIEST AND FASTEST WAY TO GET DATA OUT TO
                                                 # AND BACK TO YOU. SO JUST SET YOUR PARAMS 'module.ecu2, ['[tx]-1A87']' AND WRAP
                                                 # IT WITH PRINT AND IT WILL RETURN THE RAW DATA RECIEVED THAT EASY!!!!...
        
        
# THIS FUNCTION ABOVE RETURNS = 18 DA F1 10 5A 87 02 36 61 C6 FF 19 47 09 05 00 36 38 32 34 32 34 34 31 41 42 


# BY RUNNING THE FUNCTIONS JUST LIKE THEY ARE CALLED IN THIS FILE IT WILL RETURN THIS BELOW...

#    MongoosePro Chrysler
#    MongoosePro GM II
#    J-Box 2
#    GNA600
#    [i] Original Vin Number 1C4PJLCB8EW313490
#    18 DA F1 10 5A 87 02 36 61 C6 FF 19 47 09 05 00 36 38 32 34 32 34 34 31 41 42 

