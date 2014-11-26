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
import subprocess
import logging




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
try:
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
except:
    logging.error("Cannot define Windows functions. Are you on Windows?")
    BUFFERCALLBACK_PROTO = ctypes.CFUNCTYPE(None,PGTS_FrameStatusTimeStamp,ctypes.POINTER(ctypes.c_ushort),
                                            ctypes.c_uint,ctypes.c_void_p)
    BUFFERCALLBACK2_PROTO = ctypes.CFUNCTYPE(None,PGTS_FrameStatusTimeStamp,ctypes.POINTER(ctypes.POINTER(ctypes.c_ushort)),
                                            ctypes.POINTER(ctypes.c_uint),ctypes.c_uint,ctypes.c_void_p)

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
        self.gtsdecXidml = None
        self.gtsdecName = None
        self.serialnumber = None
        self._handle = ctypes.c_void_p()
        self._user_handle = ctypes.c_void_p()
        self._loadSetupBin = "bin/gts_setup_clr.exe"

    def setDLLPath(self,dllpath):
        '''Setup and verify the path to the gtsdecw.dll file
        :type dllpath: str
        '''
        if not os.path.exists(dllpath):
            raise IOError("{} not found".format(dllpath))
        self.gtsdecwDLLPath = dllpath
        self.gtsdecw = ctypes.WinDLL(self.gtsdecwDLLPath)


    def configureGtsDec(self,xidml,gtsdecname):
        '''Load a xidml to configure the GTS/DEC and specify the name of the GTS/DEC card
        :type xidml: str
        :type gtsdecname: str
        '''
        if not os.path.exists(xidml):
            raise IOError("{} not found".format(xidml))
        self.gtsdecXidml = xidml
        self.gtsdecName = gtsdecname
        try:
            command_line = [self._loadSetupBin,self.gtsdecXidml,self.gtsdecName]
            progout = subprocess.check_output(command_line)
        except subprocess.CalledProcessError:
            raise Exception("Failed to configure GTS/DEC card")
        except:
            raise Exception("Failed to run {}".format(command_line))
        logging.info(progout)

    def openGtsDec(self,serialnumber):
        '''Open a GTS/DEC card in preparation for acquisition.
        The serial number passed is that of the GTS/DEC card installed
        :type serialnumber: str
        '''
        try:
            ret = self.gtsdecw.OpenStringSerial(ctypes.c_char_p(serialnumber), ctypes.byref(self._handle) )
        except:
            raise IOError("Failed to open GTS {}".format(serialnumber))
        if ret != 1:
            raise IOError("Failed to open GTS {} with error code {}".format(serialnumber,ERRORS[ret]))
        self.serialnumber = serialnumber


    def setupCallback (self):
        '''Set up the callback structure for the acquisition.
        You can override the default methods independently. Do not override this method'''

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
        '''The callback method that is run on every frame. This can be overridden to implement custom behaviour'''
        logging.info("Received {} words".format(wordCount))
        return 0

    def bufferCallBack2(self,a,b,c,d):
        '''The callback method that is run on every frame if multiple frames are acquired at a time
        Not implemented at this time'''
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


