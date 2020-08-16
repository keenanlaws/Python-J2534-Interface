from .wrapper import j2534lib
from .Define import ProtocolID, BaudRate

from .wrapper import ptData, ptTxMsg, ptRxMsg, ptMskMsg, ptPatternMsg, ptFlowControlMsg
from .wrapper import ptOpen, ptClose
from .wrapper import ptConnect, ptDisconnect
from .wrapper import ptReadMsgs, ptWtiteMsgs
from .wrapper import ptStartPeriodicMsg, ptStopPeriodicMsg
from .wrapper import ptStartMsgFilter, ptStopMsgFilter
from .wrapper import ptSetProgrammingVoltage, ptReadVersion, ptGetLastError, ptIoctl, SetConfig

from .wrapper import ReadVbat, ClearTxBuf, ClearRxBuf
from .Error import J2534Error as Error

SetErrorLog = j2534lib.SetErrorLog
getDevices = j2534lib.getDevices

# set the device
setDevice = j2534lib.setDevice
