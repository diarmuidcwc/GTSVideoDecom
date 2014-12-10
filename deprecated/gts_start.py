#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      DCollins
#
# Created:     17/10/2014
# Copyright:   (c) DCollins 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import ctypes
import os
import time
#gtswd6.sys gtsdecw.dll
#C:\ACRA\GroundStationSetup\3.3.0\Software\Bin

class GTSErrors():
    ERRORS = dict()
    ERRORS[-7] = "GTS_FAIL_INCOMPATIBLE_VERSION"
    ERRORS[-6] = "GTS_FAIL_MISSING_CONFIG"
    ERRORS[-5] = "GTS_FAIL_PARAM"
    ERRORS[-4] = "GTS_FAIL_MEMORY"
    ERRORS[-3] = "GTS_FAIL_RESOURCE"
    ERRORS[-2] = "GTS_FAIL_HANDLE"
    ERRORS[-1] = "GTS_FAIL_DEVICE"
    ERRORS[0] = "GTS_FAIL_GENERAL"
    ERRORS[1] = "GTS_OK"




# structs from the define. This should be fine
class GTS_FrameStatusTimeStamp(ctypes.Structure):
    _fields_ = [("Frame_status" , ctypes.c_ushort),
                ("Frame_counter" , ctypes.c_ushort),
                ("Time_micro" , ctypes.c_ushort),
                ("Time_lo" , ctypes.c_ushort),
                ("Time_hi" , ctypes.c_ushort),
                ("Time_doy" , ctypes.c_ushort),
                ("Buffer_level" , ctypes.c_ushort),
                ("Buffer_overflow" , ctypes.c_ushort),
                ("Buffer_Slipped" , ctypes.c_ushort),
                ("BitRate" , ctypes.c_float),
                ("Reserved" , ctypes.c_ushort)
    ]
PGTS_FrameStatusTimeStamp = ctypes.POINTER(GTS_FrameStatusTimeStamp)

# The prototype for the callback. Take from the defines. should be good
BUFFERCALLBACK_PROTO = ctypes.WINFUNCTYPE(
                    ctypes.c_int,                               # Return value
                    PGTS_FrameStatusTimeStamp,                  # timeStamp
                    ctypes.POINTER(ctypes.c_ushort),             # words
                    ctypes.c_uint,                               # wordCount
                    ctypes.c_void_p                             # userInfo
                    )
@BUFFERCALLBACK_PROTO
def BufferCallBack(a,b,c,d):
    print "Callback1"
    return 0


BUFFERCALLBACK2_PROTO = ctypes.WINFUNCTYPE(
                    ctypes.c_int,                               # Ret Value
                    PGTS_FrameStatusTimeStamp,                  # timeStamps
                    ctypes.POINTER(ctypes.POINTER(ctypes.c_ushort)),# frameWords
                    ctypes.POINTER(ctypes.c_uint),               # frameWordCounts
                    ctypes.c_uint,                               # frameCount
                    ctypes.c_void_p                             # userInfo
                    )

@BUFFERCALLBACK2_PROTO
def BufferCallBack2(a,b,c,d,e):
    print "Callback2"
    return 0


class BufferCallBackStruct(ctypes.Structure):
    _fields_ = [("bufferCallBack" , BUFFERCALLBACK_PROTO),
                ("bufferCallBack2" , BUFFERCALLBACK2_PROTO),
                ("framesPerCallback", ctypes.c_int),
                ("pInfo" , ctypes.c_void_p),
                ("Channel", ctypes.c_int)
    ]

BufferCallBackStructArray = BufferCallBackStruct * 1

def main():
    gts_bin_dir =os.path.join("C:\\","ACRA","GroundStationSetup","3.3.0","Software","Bin","gtsdecw.dll")
    dec = ctypes.WinDLL(gts_bin_dir)

    # declare the OpenStringSerial function
    openserial = dec.OpenStringSerial
    openserial.argtypes =[ctypes.c_char_p,ctypes.c_void_p]

    # declare the GTS handle and prototype the openserial function
    GTS_Handle = ctypes.c_void_p()
    GTS_serial = ctypes.c_char_p("XS9766")
    ret=openserial(GTS_serial, ctypes.byref(GTS_Handle) )
    print "Open Results = {}".format(GTSErrors.ERRORS[ret])


    # Setup the outputs fom the GetChannelIds
    channelIDs = ctypes.c_void_p()
    channelcount = ctypes.c_int()

    # Call the GetChannelIds
    ret = dec.GetChannelIds(GTS_Handle,ctypes.byref(channelIDs),ctypes.byref(channelcount))
    print "GetChannelIds ReturnCode={} ChCount={}".format(GTSErrors.ERRORS[ret],channelcount)




    # Setting up the callback structure
    User_Handle = ctypes.c_void_p()
    mycallbackstruct = BufferCallBackStruct(BufferCallBack,BufferCallBack2,1,User_Handle,0)



    # SetupBufferCallBack function
    setupbuffercallback = dec.SetupBufferCallBack
    #setupbuffercallback.argtypes = [ctypes.c_void_p, BufferCallBackStruct, ctypes.c_int]
    setupbuffercallback.restype = ctypes.c_int


    callback_array = BufferCallBackStructArray()
    index =0
    for cb in callback_array:
        cb.bufferCallBack = BufferCallBack
        cb.bufferCallBack2 = BufferCallBack2
        cb.framesPerCallback = 1
        cb.pInfo = User_Handle
        cb.Channel = index
        index += 1


    ret = setupbuffercallback(GTS_Handle,callback_array,1)
    print "here2\n";
    print "SetupBufferCallBack ReturnCode={} count={}".format(GTSErrors.ERRORS[ret],1)
    if ret != 1:
        print "Ret={}".format(ret)
        dec.Close(GTS_Handle)
        exit()
    else:
        print "Success"

    gtsRun = dec.Run
    gtsRun.argtypes = [ctypes.c_void_p, ctypes.c_int]
    gtsRun.restype = ctypes.c_int
    ret = gtsRun(GTS_Handle,0)
    print "Run ReturnCode={} ".format(GTSErrors.ERRORS[ret])

    second_count = 0
    while second_count <5:
        time.sleep(1)
        second_count += 1

    gtsStop = dec.Stop
    gtsStop.argtypes = [ctypes.c_void_p, ctypes.c_int]
    gtsStop.restype = ctypes.c_int
    dec.Stop(GTS_Handle,0)



    dec.Close(GTS_Handle)


if __name__ == '__main__':
    main()
