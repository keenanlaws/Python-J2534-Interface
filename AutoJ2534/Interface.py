# -*- coding: utf-8 -*-
import winreg
import platform
import J2534
from AutoJ2534.EcuParameters import Connections


class J2534Communications:
    def __init__(self):

        self.tool_index_found = None
        self.loops = None
        self.transmit_delay = 1000
        self.receive_delay = 1000

        self.tool_open_flag = False
        self.channel_open_flag = False

        self.com_found = None
        self.connection_keys = None
        self.volts = None
        self._protcol_string = None
        self._comm_check = None
        self._mask_id = None
        self._tx_flag = None
        self._tx_id = None
        self._rx_id = None
        self._baud_rate = None
        self._connect_flag = None
        self._protocol = None
        self._ecu_filter = None
        self._channel_id = None
        self._device_id = None
        self.check_characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.can_7f_codes = {
            # Negative Response Codes
            "10": "General Reject",
            "11": "Service Not Supported",
            "12": "Function Not Supported/Invalid Format",
            "21": "Busy/Repeat Request",
            "22": "Conditions Not Correct",
            "24": "Request Sequence Error",
            "26": "Failure Prevents Execution Of Request Action",
            "31": "Request Out Of Range",
            "33": "Security Access Denied/Security Access Requested",
            "35": "Invalid Key",
            "36": "Exceed Number Of Attempts",
            "37": "Required Time Delay Not Expired",
            "40": "Download Not Accepted",
            "50": "Upload Not Accepted",
            "70": "Upload Download Not Accepted",
            "71": "Transfer Suspended",
            "72": "General Programming Failure",
            "73": "Wrong Block Sequence Counter",
            "78": "Request Correctly Received/Response Pending",
            "7E": "Sub Function Not Supported In Active Session",
            "7F": "Service Not Supported In Active Session",
            "80": "Service Not Supported In Active Diagnostic Session",
            "92": "Voltage Too High",
            "93": "Voltage Too Low",
            "9A": "Data Decompression Failed",
            "9B": "Data Decryption Failed",
            "A0": "ECU Not Responding",
            "A1": "ECU-Address Unknown",
            "FA": "Revoked Key",
            "FB": "Expired Key",
        }

    @staticmethod
    def get_interfaces() -> dict:
        """Enumerate all registered J2534 04.04 Pass-Thru interface DLLs
        Returns:
            dict: A dict mapping display names of any registered J2534
            Pass-Thru DLLs to their absolute filepath.
            The name can be used in user-facing GUI elements to allow
            selection of a particular Pass-Thru device, and filepath can
            be passed to :func:`load_interface` to instantiate a
            :class:`J2534Dll` wrapping the desired DLL.
        """
        j2534_dictionary = {}

        registry_path = r"Software\\Wow6432Node\\PassThruSupport.04.04\\"

        if platform.architecture()[0] == "32bit":
            registry_path = r"Software\\PassThruSupport.04.04\\"

        base_key = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, registry_path)
        count = winreg.QueryInfoKey(base_key)[0]

        for i in range(count):
            device_key = winreg.OpenKeyEx(base_key, winreg.EnumKey(base_key, i))
            name = winreg.QueryValueEx(device_key, "Name")[0]
            function_library = winreg.QueryValueEx(device_key, "FunctionLibrary")[0]
            j2534_dictionary[name] = function_library

        return j2534_dictionary

    def clear_rx(self):
        return J2534.clear_receive_buffer(self._channel_id)

    def clear_tx(self):
        return J2534.clear_transmit_buffer(self._channel_id)

    @staticmethod
    def numbered_tool_list():
        # this will print list of j2534 devices with there index number next to them...
        try:
            devices = J2534.get_list_j2534_devices()
            for index, device in enumerate(devices):
                if 'Error:' in device[0]:
                    print(device[0])
                    return True
                print(f'{index} = {device[0]}')
            return True
        except Exception as e:
            print(f'Error: {e}')
            raise e  # raise the exception to let the caller handle it

    @staticmethod
    def tool_list():
        try:
            return J2534.get_list_j2534_devices()
        except Exception as e:
            print(f'Error: {e}')
            return print(f'Error: tool list')

    def tool_info(self):
        try:
            return J2534.pt_read_version(self._device_id)
        except Exception as e:
            print(f'Error: {e}')
            return print(f'Error: tool info')

    def check_volts(self):
        self.volts = J2534.read_battery_volts(self._device_id)
        return self.volts if self.volts and 11.0 < self.volts < 14.7 else False

    def close(self) -> bool:
        self.tool_open_flag = False
        J2534.pt_close(self._device_id)
        return True

    def disconnect(self) -> bool:
        # pt_close close open channel to j2534 tool.
        if not J2534.pt_disconnect(self._channel_id):
            return False
        # set flag to false after channel is closed
        self.channel_open_flag = False
        return True

    def _build_connection_library(self, library_name: str):
        # make var to shorten up the calls to dict.
        param = Connections.CHRYSLER_ECU.get(library_name, False)  # get connection parameters from dict.
        self._key_name = param.name
        self.transmit_delay = param.tx_delay  # transmit delay for tx only functions.
        self.receive_delay = param.rx_delay  # receive delay for rx only functions.
        self._protcol_string = param.protocol_name  # communication protocol name selected.
        self._protocol = param.protocol_id  # communication protocol selected.
        self._connect_flag = param.connect_flag  # connection flag if needed most likely not needed.
        self._baud_rate = param.baud_rate  # communication protocol baud-rate selected.
        self._mask_id = param.mask  # data filter mask selected, this pertains to data and not the address id.
        self._rx_id = param.rx_id  # rx address that is allowed to be read all other will be ignored
        self._tx_id = param.tx_id  # tx address that is allowed to be read all other will be ignored
        self._tx_flag = param.tx_flag  # will set some spec. functions like can frame pad and prog voltage.
        self._comm_check = param.comm_check  # communication check to verify communication is working
        if self._protocol in [7, 8, 9, 10]:  # if protocol is J1850 or sci set protocol related attributes.
            self._t1_max = param.t1_max  # inter frame rate delays if it pertains to this protocol.
            self._t2_max = param.t2_max  # inter frame rate delays if it pertains to this protocol.
            self._t4_max = param.t4_max  # inter frame rate delays if it pertains to this protocol.
            self._t5_max = param.t5_max  # inter frame rate delays if it pertains to this protocol.
        return True

    def open_j2534_interface(self, index_of_tool: int) -> bool:
        try:
            if self.tool_open_flag:  # if tool is already open no need to try to open again.
                return True
            J2534.set_j2534_device_to_connect(index_of_tool)  # set device index number to open connection to.

            self._device_id = J2534.pt_open()  # open connection to j2534 tool this will return device id number...
            if self._device_id is False:
                return False

            if not self.check_volts():  # if voltage is not within range return False.
                return False

            self.tool_open_flag = True  # if tool opens successfully set flag.
            return True
        except Exception as e:
            return False

    def establish_connection(self) -> bool:
        try:
            # pt_connect opens channel to selected communication protocol if successful will return channel id.
            self._channel_id = J2534.pt_connect(self._device_id, self._protocol, self._connect_flag, self._baud_rate)

            if not self._channel_id:  # if pt_connect is not successful return False.
                self.channel_open_flag = False  # if channel id is not returned set flag to False.
                return False

            self.channel_open_flag = True  # if channel id is returned set flag to True.
            return True
        except Exception as e:
            return False

    def _tmax_delays(self) -> bool:
        # set inter frame rate delays if it pertains to this protocol.
        if self._protocol in [7, 8, 9, 10]:
            tmax = [self._t1_max, self._t2_max, self._t4_max, self._t5_max]
            for cnt, x in enumerate(tmax, start=26):
                if x:
                    J2534.pt_set_config(self._channel_id, [[cnt, x]])
        return True

    def _set_ecu_filter(self):
        # pt_start_ecu_filter set filters of tx and rx id only allow the id's of choice to be read.
        self._ecu_filter = J2534.pt_start_ecu_filter(
            self._channel_id,
            self._protocol,  # communication protocol selected.
            self._mask_id,  # data filter mask selected, this pertains to data and not the address id.
            self._rx_id,  # rx address that is allowed to be read all other will be ignored
            self._tx_id,  # tx address that is allowed to be read all other will be ignored
            self._tx_flag,  # will set some spec. functions like can frame pad and prog voltage.
        )
        return self._ecu_filter  # returns filter id if successful.

    def open_communication(self, index_of_tool: int, library_name: str) -> bool:
        if not self._build_connection_library(library_name):
            return False

        if not self.open_j2534_interface(index_of_tool):
            return False

        if not self.establish_connection():
            return False

        return self._set_ecu_filter() if self._tmax_delays() else False

    def _transmit_only_can_message(self, data_to_transmit):
        # set message structure for transmit and receive.
        tx = J2534.PassThruMsgBuilder(self._protocol, self._tx_flag)
        # set data in buffer ready to tx.
        tx.set_identifier_and_data(self._tx_id, data_to_transmit)
        # Transmit one message.
        return J2534.pt_write_message(self._channel_id, tx, 1, self.transmit_delay)

    def _receive_only_can_message(self, transmitted_data, loops=0):
        rx = J2534.PassThruMsgBuilder(self._protocol, self._tx_flag)  # set message structure for receive.
        rx_output = rx.dump_output()  # dump output to var.
        check_byte = rx_output[8:10]
        error_byte = rx_output[12:14]

        for _ in range(3 + loops):  # loop 3 times plus any additional loops.

            # read message from buffer.
            if J2534.pt_read_message(self._channel_id, rx, 1, self.receive_delay) == 16:
                return False

            # rx.status response descriptions:
            # 0 = msg read successfully
            # 2 = start of message or first frame
            # 4 = rx break
            # 8 = rx break
            # 9 = tx indication
            # 100 = can 29bit id
            # 102 = start of message
            # 109 = tx message type + tx indication + can 29bit id
            # 256 = can 29 bit + msg read successfully
            # 258 = can 29 bit + tx indication
            # 265 = tx indication

            if rx.RxStatus in [2, 9, 102, 258, 265]:
                continue

            # if rx.status is 0 or 256 we are done reading from buffer! time to process data.
            if rx.RxStatus in [0, 256]:

                if check_byte == '7F':  # 7F is negative response.
                    if error_byte == '78':
                        continue

                    # check if error/7F is returned, lookup failure code and return failure string.
                    return self.can_7f_codes.get(error_byte, 'Function failed/no definition')

                # if we receive positive response return data received.
                if check_byte == (hex(transmitted_data[0] + 0x40)[2:].upper()):  # first byte + 64 is pos response
                    # return data[8:] less first 8 bytes of response which is recv address.
                    return rx_output[8:]
        return False

    def _transmit_and_receive_can_message(self, data_to_transmit, loops=0):
        # set message structure for transmit and receive.
        tx = J2534.PassThruMsgBuilder(self._protocol, self._tx_flag)
        rx = J2534.PassThruMsgBuilder(self._protocol, self._tx_flag)

        # set data in buffer ready to tx.
        tx.set_identifier_and_data(self._tx_id, data_to_transmit)

        try:
            # Transmit one message.
            if J2534.pt_write_message(self._channel_id, tx, 1, self.transmit_delay) is False:
                return False

            for _ in range(3 + int(loops)):
                if J2534.pt_read_message(self._channel_id, rx, 1, self.receive_delay) in [16]:
                    return False
                # rx.status response descriptions:
                # 0 = msg read successfully
                # 2 = start of message or first frame
                # 4 = rx break
                # 8 = rx break
                # 9 = tx indication
                # 100 = can 29bit id
                # 102 = start of message
                # 109 = tx message type + tx indication + can 29bit id
                # 256 = can 29 bit + msg read successfully
                # 258 = can 29 bit + tx indication
                # 265 = tx indication

                # if rx.status is 2,9,109,102 == 2/102 =start of message, 9/109 =tx indication, continue loop.
                if rx.RxStatus in [2, 9, 102, 258, 265]:
                    continue

                # if rx.status is 0 we are done reading from buffer! time to process data.
                if rx.RxStatus in [0, 256]:

                    if rx.dump_output()[8:10] in ['7F'] and rx.dump_output()[12:14] == '78':
                        continue

                    # check if error/7F is returned, lookup failure code and return failure string.
                    if rx.dump_output()[8:10] in ['7F']:
                        error_id = rx.dump_output()[12:14]
                        return self.can_7f_codes.get(error_id, 'Function failed/no definition')

                    # first byte of response + 64 is pos response
                    positive_response = (hex(data_to_transmit[0] + 0x40)[2:].upper())

                    # if we receive positive response return data received.
                    if rx.dump_output()[8:10] == positive_response:
                        # return data[8:] less first 8 bytes of response which is recv address.
                        return rx.dump_output()[8:]
        except Exception as e:
            return False
        return False

    def _transmit_and_receive_sci_message(self, data_to_transmit):
        # set message structure for transmit and receive.
        tx = J2534.PassThruMsgBuilder(self._protocol, self._tx_flag)
        rx = J2534.PassThruMsgBuilder(self._protocol, self._tx_flag)

        # set data in buffer ready to tx.
        tx.build_transmit_data_block(data_to_transmit)

        # Transmit one message.
        if J2534.pt_write_message(self._channel_id, tx, 1, self.transmit_delay) is False:
            return False

        var0 = J2534.pt_read_message(self._channel_id, rx, 1, self.receive_delay)
        if var0 in [16]:
            return False

        return rx.dump_output() if rx.DataSize > 1 else False

    def transmit_and_receive_message(self, data_to_transmit: list, loops=0):
        self.loops = loops
        match self._protocol:
            case 6:
                return self._transmit_and_receive_can_message(data_to_transmit, self.loops)
            case 7:
                return self._transmit_and_receive_sci_message(data_to_transmit)
            case 8:
                return self._transmit_and_receive_sci_message(data_to_transmit)
            case 9:
                return self._transmit_and_receive_sci_message(data_to_transmit)
            case 10:
                return self._transmit_and_receive_sci_message(data_to_transmit)

    def transmit_only(self, data_to_transmit: list):
        match self._protocol:
            case 6:
                return self._transmit_only_can_message(data_to_transmit)
            case 7:
                return self._transmit_and_receive_sci_message(data_to_transmit)
            case 8:
                return self._transmit_and_receive_sci_message(data_to_transmit)
            case 9:
                return self._transmit_and_receive_sci_message(data_to_transmit)
            case 10:
                return self._transmit_and_receive_sci_message(data_to_transmit)

    def receive_only(self, transmitted_data, loops=0):
        self.loops = loops
        match self._protocol:
            case 6:
                return self._receive_only_can_message(transmitted_data, loops=0)
            case 7:
                return self._transmit_and_receive_sci_message(transmitted_data)
            case 8:
                return self._transmit_and_receive_sci_message(transmitted_data)
            case 9:
                return self._transmit_and_receive_sci_message(transmitted_data)
            case 10:
                return self._transmit_and_receive_sci_message(transmitted_data)

    def tool_search(self):
        # search for index of connected j2534 device...
        for x in range(20):  # loop through all j2534 devices found in registry...

            if self.open_j2534_interface(x):  # test all indexes of tools to see which one responds...

                self.tool_index_found = x  # save index of tool if it responds...

                self.close()  # close connection of tool...

                return self.tool_index_found  # return saved index of tool that responded...

        return False

    def auto_connect(self):
        # search for index of connected j2534 device...
        tool_index = self.tool_search()

        # dictionary of connection parameters only use the first 7 keys...
        connection_keys = list(Connections.CHRYSLER_ECU.keys())[:7]  # get list of connection parameters from dict...
        try:
            for connection_key in connection_keys:  # loop through connection keys...

                if self.open_communication(tool_index,
                                           connection_key):  # test connection params to see if ecu responds...
                    tool_info = self.tool_info()  # get info of connected j2534 tool...

                    if self.transmit_and_receive_message(self._comm_check):  # if communication is successful...
                        print(f'Found and connected to {tool_info[0]}')
                        print(f'Communication successful with {self._key_name}')
                        self.com_found = connection_key

                        # if we get a successful connection return all connection information...
                        return [tool_index, connection_key, self._key_name, tool_info[0], tool_info[1], tool_info[2]]

                self.close()  # after testing all keys if no response close connection to j2534 device...
            return False

        except Exception as e:
            return False


j2534_communication = J2534Communications()
