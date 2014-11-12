#-------------------------------------------------------------------------------
# Name:        GtsDec
# Purpose:     Python class to wrap around the GTS/DEC Realtime
#
# Copyright 2014 Diarmuid Collins dcollins@curtisswright.com
# https://github.com/diarmuid
#
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import ctypes
import os
import time


# structs from the define. This should be fine
class GTS_FrameStatusTimeStamp(ctypes.Structure):
    ''' GTS_FrameStatusTimeStamp : time stamp and status for each frame returned'''
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
                    None,                               # Return value
                    PGTS_FrameStatusTimeStamp,                  # timeStamp
                    ctypes.POINTER(ctypes.c_ushort),             # words
                    ctypes.c_uint,                               # wordCount
                    ctypes.c_void_p                             # userInfo
                    )
BUFFERCALLBACK2_PROTO = ctypes.WINFUNCTYPE(
                    None,                               # Ret Value
                    PGTS_FrameStatusTimeStamp,                  # timeStamps
                    ctypes.POINTER(ctypes.POINTER(ctypes.c_ushort)),# frameWords
                    ctypes.POINTER(ctypes.c_uint),               # frameWordCounts
                    ctypes.c_uint,                               # frameCount
                    ctypes.c_void_p                             # userInfo
                    )

class BufferCallBackStruct(ctypes.Structure):
    _fields_ = [("bufferCallBack" , BUFFERCALLBACK_PROTO),
                ("bufferCallBack2" , BUFFERCALLBACK2_PROTO),
                ("framesPerCallback", ctypes.c_int),
                ("pInfo" , ctypes.c_void_p),
                ("Channel", ctypes.c_int)
    ]

BufferCallBackStructArray = BufferCallBackStruct * 1



class GtsDec(object):
    '''Python class to acquire data from a GTS/DEC card'''

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

    def __init__(self):
        '''Initialise a GTSDEC object. Needs to pass the path to gtsdllw.dll'''
        super(GtsDec,self).__init__()
        self.gtsdecwDLLPath = None
        self.programmerDLLPath = None
        self.serialnumber = None
        self._handle = ctypes.c_void_p()
        self._user_handle = ctypes.c_void_p()

    def setdllpath(self,dllpath):
        '''Setup and verify the dll path'''
        if not os.path.exists(dllpath):
            raise IOError("{} not found".format(dllpath))
        self.gtsdecwDLLPath = dllpath
        self.gtsdecw = ctypes.WinDLL(self.gtsdecwDLLPath)

    def setProgrammerDLL(self,dllpath):
        '''Setup and verify the dll path'''
        if not os.path.exists(dllpath):
            raise IOError("{} not found".format(dllpath))
        self.programmerDLLPath = dllpath
        self.gtsdep = ctypes.WinDLL(self.programmerDLLPath)

    def loadSetup(self,xidml):
        '''Load a xidml to configure the GTS/DEC'''
        if not os.path.exists(xidml):
            raise IOError("{} not found".format(xidml))


    def openserial(self,serialnumber):
        '''Open a GTS/DEC card as indicated by the serial number passed'''
        try:
            ret = self.gtsdecw.OpenStringSerial(ctypes.c_char_p(serialnumber), ctypes.byref(self._handle) )
        except:
            raise IOError("Failed to open GTS {}".format(serialnumber))
        if ret != 1:
            raise IOError("Failed to open GTS {} with error code {}".format(serialnumber,ERRORS[ret]))
        self.serialnumber = serialnumber


    def setupcallback (self):
        '''Set up the callback structure for the acqusition.
        You can override the default methods independently'''

        self.callback_array = BufferCallBackStructArray()
        index = 0
        for cb in self.callback_array:
            cb.bufferCallBack = self.__getCallbackFunc()
            cb.bufferCallBack2 = self.__getCallbackFunc2()
            cb.framesPerCallback = 1
            cb.pInfo = self._user_handle
            cb.Channel = index
            index += 1
        try:
            ret = self.gtsdecw.SetupBufferCallBack(self._handle,self.callback_array,1)
        except:
            raise IOError("Failed to setup callback")
        if ret != 1:
            raise IOError("Failed to setup callback with error code = {}".format(GtsDec.ERRORS[ret]))



    def bufferCallBack(self,timeStamp,pwords,wordCount,puserInfo):
        '''The callback method that is run on every frame'''
        print "Received {} words".format(wordCount)
        return 0

    def bufferCallBack2(self,a,b,c,d):
        '''The callback method that is run on every frame if multiple frames are acquired at a time'''
        print "Something2"
        return 0

    def __getCallbackFunc(self):
        '''Internal python magic to convert a ctypes method to a method on a class'''
        def func(a,b,c,d):
            self.bufferCallBack(a,b,c,d)
        return BUFFERCALLBACK_PROTO(func)

    def __getCallbackFunc2(self):
        '''Internal python magic to convert a ctypes method to a method on a class'''
        def func(a,b,c,d):
            self.bufferCallBack(a,b,c,d)
        return BUFFERCALLBACK2_PROTO(func)

    def run(self):
        '''Start the acquisition'''
        try:
            ret = self.gtsdecw.Run(self._handle,0)
        except:
            raise IOError("Failed to run acquisition")
        if ret != 1:
            raise IOError("Failed to run acquisition with error code = {}".format(GtsDec.ERRORS[ret]))

    def stop(self):
        '''Stop the acquisition'''
        try:
            ret = self.gtsdecw.Stop(self._handle,0)
        except:
            raise IOError("Failed to stop acquisition")
        if ret != 1:
            raise IOError("Failed to stop acquisition with error code = {}".format(GtsDec.ERRORS[ret]))


    def close(self):
        '''Close the GTS/DEC card'''
        try:
            ret = self.gtsdecw.Close(ctypes.byref(self._handle))
        except:
            raise IOError("Failed to close GTS ")
        if ret != 1:
            raise IOError("Failed to close GTS with error code = {}".format(GtsDec.ERRORS[ret]))


