#-------------------------------------------------------------------------------
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

import GtsDec
import os
import time
import VidOverPCM
import socket
import logging
import MpegTS

# Constants for this script
GTSDEC_SERIAL_NUM = "XS9766"
DLL_PATH = os.path.join("C:\\","ACRA","GroundStationSetup","3.3.0","Software","Bin","gtsdecw.dll")
SRC_XIDML = "Configuration/vid_enc.xml"

class CustomGTSDecom(GtsDec.GtsDec):
    '''Create a new class inheriting the GtsDec class. Override the callback method using this approach'''

    BASE_UDP_PORT = 7777

    def __init__(self):
        super(CustomGTSDecom, self).__init__()
        self.vidOverPCM = None
        self.mpegTS = dict()

    def addVidOverPCM(self,vidoverPCM):
        self.vidOverPCM = vidoverPCM
        udp_port = CustomGTSDecom.BASE_UDP_PORT
        for vid in self.vidOverPCM.vidsPerXidml:
            self.mpegTS[vid] = MpegTS.MpegTS()
            self.mpegTS[vid].dstudp = udp_port
            udp_port += 1


    def bufferCallBack(self,timeStamp,pwords,wordCount,puserInfo):
        '''The callback method that is run on every frame'''
        # This method will take a full PCM frame and return a dict of buffers
        # one for each VID in the PCM frame
        vid_bufs = self.vidOverPCM.frameToBuffers(pwords[:wordCount])
        for vid,buf in vid_bufs.iteritems():
            self.mpegTS[vid].addPayload(buf)
        return 0


def main():

    # Setup a logger
    import logging
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

    # Get the source xidml file with the VID PCM structure
    vidxidml = VidOverPCM.VidOverPCM()
    vidxidml.parseXidml(SRC_XIDML)
    logging.info("Read in source xidml")
    # We now have an object that knows how to convert a PCM frame into one or multiple
    # video payloads containing MPEG TS data

    # Pass the  dtsdecw.dll path.
    gts_dll_path = DLL_PATH

    # I have inherited the basic GTSDec Class so that I can replace the callback function
    mygtsdec = CustomGTSDecom()             # A new GtsDec object
    mygtsdec.addVidOverPCM(vidxidml)        # The VidOverPCM object
    mygtsdec.setdllpath(gts_dll_path)       # Pass the dll path
    mygtsdec.openserial(GTSDEC_SERIAL_NUM)           # Open the card by serial number
    logging.info("GTS/DEC card successfully opened")
    mygtsdec.setupcallback()                # Setup the default callback, this is the method declared in my CustomGTSDecom class

    mygtsdec.run()                          # Run the acquisition
    logging.info("Acquisition running")

    second_count = 0
    while second_count <50:                 # Run for a numbner of seconds
        print ".",
        time.sleep(1)                       # The callback will be firing all during this point
        second_count += 1
    print ""
    logging.info("Stopping acquisition")
    mygtsdec.stop()                         # Stop the acquisition
    mygtsdec.close()                        # Close the card

if __name__ == '__main__':
    main()
