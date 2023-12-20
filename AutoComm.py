# -*- coding: utf-8 -*-
from AutoJ2534.Interface import j2534_communication

# auto connect example...
j2534_communication.auto_connect()

# can bus example...
print(j2534_communication.transmit_and_receive_message([0x1a, 0x90]))

# sci bus example...
# print(j2534_communication.transmit_and_receive_message([0x2a, 0x0f]))
