## Python J2534/AutoComm
This is a automatic interface to the J2534 API written in Python 3.10  32bit


## Automatically find j2534 device

from AutoJ2534.Interface import j2534_communication

tool_info = j2534_communication.auto_connect()
print(tool_info)



## Can Bus Transmit and receive

data = j2534_communication.transmit_and_receive_message([0x1a, 0x90])
print(data)




