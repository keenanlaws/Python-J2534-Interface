## Python J2534 Interface
This is a interface to the J2534 API written in Python 3.10.


## List Available Tools
```
import J2534
```
```
print(J2534.getDevices())
```
```
[['VSI-2534', 'C:\\WINDOWS\\SysWOW64\\dgVSI32.dll'], ['CarDAQ PLUS', 'C:\\WINDOWS\\system32\\CDPLS432.DLL'], 

['j2534-logger', 'C:\\Program Files (x86)\\Drew Technologies, Inc\\J2534\\j2534-logger\\ptshim32.dll'], 

['MongoosePro Chrysler', 'C:\\Program Files (x86)\\Drew Technologies, Inc\\J2534\\MongoosePro Chrysler\\monps432.dll'], 

['McS1', 'C:\\WINDOWS\\SYSTEM\\McS1v232.DLL'], ['J2534 for Kvaser Hardware', 'C:\\Program Files\\Kvaser\\Drivers\\32\\j2534api.dll'], 

['FulcrumShim', 'C:\\Program Files (x86)\\MEAT Inc\\FulcrumShim\\FulcrumShim.dll'], ]
```
## Connect To J2534
```
import J2534
```
```
J2534.setDevice(index_of_tool)
```
```
device_id = J2534.pt_open()
```
```
channel_id = J2534.pt_connect(device_id, protocol, connect_flag, baud_rate)
```
```
ecu_filter = J2534.pt_start_ecu_filter(channel_id, protocol,  mask_id, rx_id, tx_id, tx_flag)
```
```      
examples of parameters for ecu filter for ISO15765 connection = (channel_id, 6, 0xFFFFFFFF, 0x7E8, 0x7E0, 0X40)
```
## Transmit and receive

set message structure for transmit and receive.
```
tx = J2534.PassThruMsgBuilder(protocol, tx_flag)
```
```
rx = J2534.PassThruMsgBuilder(protocol, tx_flag)
```

set data in buffer ready to tx.
```
tx.set_id_and_data(0x7e0, [0x1a, 0x87])
```
Transmit data.
```
J2534.pt_write_message(channel_id, message to send, # of messages to send, tx delay)
```
Read data.
```
J2534.pt_read_message(channel_id, message to read, how many messages to read, rx delay)
```
Print data.
```
print(rx.dump_output())
```


