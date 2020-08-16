# coding:utf-8

# 0x00:(No., Name, Description )
J2534Error = dict()

# Function call successful
STATUS_NOERROR = 0x00
J2534Error[STATUS_NOERROR] = (STATUS_NOERROR, 'STATUS_NOERROR', 'Function call successful')

# Device cannot support requested functionality mandated in this
# document. Device is not fully SAE J2534 compliant
ERR_NOT_SUPPORTED = 0x01
J2534Error[ERR_NOT_SUPPORTED] = (ERR_NOT_SUPPORTED, 'ERR_NOT_SUPPORTED',
                                 'Device cannot support requested functionality mandated in this document. Device is '
                                 'not fully SAE J2534 compliant')

# Invalid ChannelID value
ERR_INVALID_CHANNEL_ID = 0x02
J2534Error[ERR_INVALID_CHANNEL_ID] = (ERR_INVALID_CHANNEL_ID, 'ERR_INVALID_CHANNEL_ID',
                                      'Invalid ChannelID value')

# Invalid ProtocolID value, unsupported ProtocolID, or there is a resource conflict (i.e. trying to connect to
# multiple protocols that are mutually exclusive such as J1850PWM and J1850VPW, or CAN and SCI A, etc.)
ERR_INVALID_PROTOCOL_ID = 0x03
J2534Error[ERR_INVALID_PROTOCOL_ID] = (ERR_INVALID_PROTOCOL_ID, 'ERR_INVALID_PROTOCOL_ID',
                                       'Invalid ProtocolID value, unsupported ProtocolID, or there is a resource '
                                       'conflict (i.e. trying to connect to multiple protocols that are mutually '
                                       'exclusive such as J1850PWM and J1850VPW, or CAN and SCI A, etc.)')

# NULL pointer supplied where a valid pointer is required
ERR_NULL_PARAMETER = 0x04
J2534Error[ERR_NULL_PARAMETER] = (
    ERR_NULL_PARAMETER,
    'ERR_NULL_PARAMETER',
    'NULL pointer supplied where a valid pointer is required')

# Invalid value for Ioctl parameter
ERR_INVALID_IOCTL_VALUE = 0x05
J2534Error[ERR_INVALID_IOCTL_VALUE] = (
    ERR_INVALID_IOCTL_VALUE,
    'ERR_INVALID_IOCTL_VALUE',
    'Invalid value for Ioctl parameter')
# Invalid flag values
ERR_INVALID_FLAGS = 0x06
J2534Error[ERR_INVALID_FLAGS] = (ERR_INVALID_FLAGS, 'ERR_INVALID_FLAGS', 'Invalid flag values')

# Undefined error, use PassThruGetLastError for text description
ERR_FAILED = 0x07
J2534Error[ERR_FAILED] = (
    ERR_FAILED,
    'ERR_FAILED',
    'Undefined error, use PassThruGetLastError for text description')

# Device ID invalid
ERR_DEVICE_NOT_CONNECTED = 0x08
J2534Error[ERR_DEVICE_NOT_CONNECTED] = (ERR_DEVICE_NOT_CONNECTED, 'ERR_DEVICE_NOT_CONNECTED',
                                        'Device ID invalid')

# Timeout.
# PassThruReadMsg: No message available to read or could not read the specified number of
#   messages. The actual number of messages read is placed in <NumMsgs>
# PassThruWriteMsg: Device could not write the specified number of messages. The actual number of
#   messages sent on the vehicle network is placed in <NumMsgs>.
ERR_TIMEOUT = 0x09
J2534Error[ERR_TIMEOUT] = (ERR_TIMEOUT, 'ERR_TIMEOUT', 'Timeout')

# Invalid message structure pointed to by pMsg (Reference Section 8 � Message Structure)
ERR_INVALID_MSG = 0x0A
J2534Error[ERR_INVALID_MSG] = (ERR_INVALID_MSG, 'ERR_INVALID_MSG',
                               'Invalid message structure pointed to by pMsg')

# Invalid TimeInterval value
ERR_INVALID_TIME_INTERVAL = 0x0B
J2534Error[ERR_INVALID_TIME_INTERVAL] = (ERR_INVALID_TIME_INTERVAL, 'ERR_INVALID_TIME_INTERVAL',
                                         'Invalid TimeInterval value')

# Exceeded maximum number of message IDs or allocated space
ERR_EXCEEDED_LIMIT = 0x0C
J2534Error[ERR_EXCEEDED_LIMIT] = (ERR_EXCEEDED_LIMIT,
                                  'ERR_EXCEEDED_LIMIT',
                                  'Exceeded maximum number of message IDs or allocated space')

# Invalid MsgID value
ERR_INVALID_MSG_ID = 0x0D
J2534Error[ERR_INVALID_MSG_ID] = (ERR_INVALID_MSG_ID, 'ERR_INVALID_MSG_ID', 'Invalid MsgID value')

# Device is currently open
ERR_DEVICE_IN_USE = 0x0E
J2534Error[ERR_DEVICE_IN_USE] = (ERR_DEVICE_IN_USE, 'ERR_DEVICE_IN_USE',
                                 'Device is currently open')

# Invalid IoctlID value
ERR_INVALID_IOCTL_ID = 0x0F
J2534Error[ERR_INVALID_IOCTL_ID] = (ERR_INVALID_IOCTL_ID, 'ERR_INVALID_IOCTL_ID',
                                    'Invalid IoctlID value')

# Protocol message buffer empty, no messages available to read
ERR_BUFFER_EMPTY = 0x10
J2534Error[ERR_BUFFER_EMPTY] = (
    ERR_BUFFER_EMPTY,
    'ERR_BUFFER_EMPTY',
    'Protocol message buffer empty, no messages available to read')

# Protocol message buffer full. All the messages specified may not have been transmitted
ERR_BUFFER_FULL = 0x11
J2534Error[ERR_BUFFER_FULL] = (
    ERR_BUFFER_FULL,
    'ERR_BUFFER_FULL',
    'Protocol message buffer full. All the messages specified may not have been transmitted'
)

# Indicates a buffer overflow occurred and messages were lost
ERR_BUFFER_OVERFLOW = 0x12
J2534Error[ERR_BUFFER_OVERFLOW] = (
    ERR_BUFFER_OVERFLOW,
    'ERR_BUFFER_OVERFLOW',
    'Indicates a buffer overflow occurred and messages were lost')

# Invalid pin number, pin number already in use, or voltage already applied to a different pin
ERR_PIN_INVALID = 0x13
J2534Error[ERR_PIN_INVALID] = (
    ERR_PIN_INVALID,
    'ERR_PIN_INVALID',
    'Invalid pin number, pin number already in use, or voltage already applied to a different pin'
)

# Channel number is currently connected
ERR_CHANNEL_IN_USE = 0x14
J2534Error[ERR_CHANNEL_IN_USE] = (ERR_CHANNEL_IN_USE, 'ERR_CHANNEL_IN_USE',
                                  'Channel number is currently connected')

# Protocol type in the message does not match the protocol associated with the Channel ID
ERR_MSG_PROTOCOL_ID = 0x15
J2534Error[ERR_MSG_PROTOCOL_ID] = (ERR_MSG_PROTOCOL_ID,
                                   'ERR_MSG_PROTOCOL_ID',
                                   'Protocol type in the message does not match the protocol associated with the '
                                   'Channel ID '
                                   )

# Invalid Filter ID value
ERR_INVALID_FILTER_ID = 0x16
J2534Error[ERR_INVALID_FILTER_ID] = (
    ERR_INVALID_FILTER_ID,
    'ERR_INVALID_FILTER_ID',
    'Invalid Filter ID value')

# No flow control filter set or matched (for protocolID ISO15765 only)
ERR_NO_FLOW_CONTROL = 0x17
J2534Error[ERR_NO_FLOW_CONTROL] = (
    ERR_NO_FLOW_CONTROL,
    'ERR_NO_FLOW_CONTROL',
    'No flow control filter set or matched')

# A CAN ID in pPatternMsg or pFlowControlMsg matches either ID in an existing FLOW_CONTROL_FILTER
ERR_NOT_UNIQUE = 0x18
J2534Error[ERR_NOT_UNIQUE] = (
    ERR_NOT_UNIQUE,
    'ERR_NOT_UNIQUE',
    'A CAN ID in pPatternMsg or pFlowControlMsg matches either ID in an existing FLOW_CONTROL_FILTER'
)

# The desired baud rate cannot be achieved within the tolerance specified in Section 6.5
ERR_INVALID_BAUDRATE = 0x19
J2534Error[ERR_INVALID_BAUDRATE] = (
    ERR_INVALID_BAUDRATE,
    'ERR_INVALID_BAUDRATE',
    'The desired baud rate cannot be achieved within the tolerance specified in Section 6.5'
)

# Unable to communicate with device
ERR_INVALID_DEVICE_ID = 0x1A
J2534Error[ERR_INVALID_DEVICE_ID] = (
    ERR_INVALID_DEVICE_ID,
    'ERR_INVALID_DEVICE_ID',
    'Unable to communicate with device')


def printerr(ret):
    print(J2534Error[ret][1])


def showERROR(method, ret):
    print("[%s:%s]" % (method, J2534Error[ret][1]))


if __name__ == '__main__':
    import sys

    if sys.argv[1] == 'all':
        for i in range(0x1A + 1):
            print(hex(i), J2534Error[i])
    else:
        print(J2534Error[int(sys.argv[1], 16)])
