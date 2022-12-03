# Python J2534 Interface
This is a interface to the J2534 API written in Python 3.10.


# List Available Tools

>>import J2534

>>print(J2534.getDevices())

>>[['VSI-2534', 'C:\\WINDOWS\\SysWOW64\\dgVSI32.dll'], 
>>['CarDAQ PLUS', 'C:\\WINDOWS\\system32\\CDPLS432.DLL'], 
>>['j2534-logger', 'C:\\Program Files (x86)\\Drew Technologies, Inc\\J2534\\j2534-logger\\ptshim32.dll'], 
>>['MongoosePro Chrysler', 'C:\\Program Files (x86)\\Drew Technologies, Inc\\J2534\\MongoosePro Chrysler\\monps432.dll'], 
>>['McS1', 'C:\\WINDOWS\\SYSTEM\\McS1v232.DLL'], 
>>['J2534 for Kvaser Hardware', 'C:\\Program Files\\Kvaser\\Drivers\\32\\j2534api.dll'], 
>>['FulcrumShim', 'C:\\Program Files (x86)\\MEAT Inc\\FulcrumShim\\FulcrumShim.dll']]


# Connect To J2534

>>import J2534

>>J2534.setDevice(index_of_tool)

>>device_id = J2534.pt_open()

>>channel_id = J2534.pt_connect(device_id, protocol, connect_flag, baud_rate)

