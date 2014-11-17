# -------------------------------------------------------------------------------
# Name:        
# Purpose:     
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


import win32com.client
import os
import ctypes


def send(self):
    return buffer(self)[:]




manager = win32com.client.Dispatch("ACRA.GtsDec.XidML.GtsProgrammerInterfaceManager")
myProgrammer = manager.GroundStationProgrammerFactory.Create()
myInstrumentChannel = win32com.client.Dispatch("ACRA.GtsDec.XidML.CInstrumentChannelCollection")
for i in range(1):
    mystruct = win32com.client.Record("InstrumentChannelStruct","ACRA.GtsDec.XidML.GtsProgrammerInterfaceManager")
    myInstrumentChannel.Add(mystruct)

XIDML_PATH = os.path.join("C:\\","WORK","WORK_MISC_UTILS","PythonUtils","GTSDecom","gtsdec5.xml")
ret = myProgrammer.LoadSetupCollection(myInstrumentChannel,XIDML_PATH)