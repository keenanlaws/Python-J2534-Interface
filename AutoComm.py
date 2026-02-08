# -*- coding: utf-8 -*-
from AutoJ2534.interface import j2534_communication

# auto connect example...
j2534_communication.auto_connect()

# can bus examples...
print(j2534_communication.transmit_and_receive_message([0x1a, 0x90]))

print(j2534_communication.transmit_and_receive_message([0x1a, 0x87]))


