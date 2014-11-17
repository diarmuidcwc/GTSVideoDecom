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
SRC_XIDML = "Configuration/vid_106_103.XML"
GTSDEC_XIDML = "Configuration/gtsdec5.xml"
GTSDEC_NAME = "MyCard"

class CustomGTSDecom(GtsDec.GtsDec):
    '''Create a new class inheriting the GtsDec class. Override the callback method using this approach'''

    BASE_UDP_PORT = 7777

    def __init__(self):
        super(CustomGTSDecom, self).__init__()
        self.vidOverPCM = None
        self.mpegTS = dict()
        self.logtofile = False

    def addVidOverPCM(self,vidoverPCM):
        self.vidOverPCM = vidoverPCM
        udp_port = CustomGTSDecom.BASE_UDP_PORT
        for vid in self.vidOverPCM.vidsPerXidml:
            self.mpegTS[vid] = MpegTS.MpegTS(udpport=udp_port)
            self.mpegTS[vid].name = vid
            if self.logtofile:
                self.mpegTS[vid]._dumpfname = "{}.bin".format(udp_port)
            udp_port += 1

    def getSummary(self):
        ret_str = ""
        for vid in self.vidOverPCM.vidsPerXidml:
            ret_str += "Transmitting vid {} to address {} on port {}\n".format(self.mpegTS[vid].name,self.mpegTS[vid].dstip,self.mpegTS[vid].dstudp)
        return ret_str


    def bufferCallBack(self,timeStamp,pwords,wordCount,puserInfo):
        '''The callback method that is run on every frame'''
        # This method will take a full PCM frame and return a dict of buffers
        # one for each VID in the PCM frame
        vid_bufs = self.vidOverPCM.frameToBuffers(pwords[:wordCount])
        for vid,buf in vid_bufs.iteritems():
            #print "Decom frame vid = {}".format(vid)
            self.mpegTS[vid].addPayload(buf)
        return 0


def main():

    # Setup a logger
    import logging
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

    # Get the source xidml file with the VID PCM structure
    vidxidml = VidOverPCM.VidOverPCM()
    vidxidml.parseXidml(SRC_XIDML)
    for vidname in vidxidml.vids:
        logging.info("Found vid = {}".format(vidname))
    # We now have an object that knows how to convert a PCM frame into one or multiple
    # video payloads containing MPEG TS data
    logging.info("Read in source xidml")

    # I have inherited the basic GTSDec Class so that I can replace the callback function
    mygtsdec = CustomGTSDecom()                         # A new GtsDec object
    mygtsdec.addVidOverPCM(vidxidml)                    # The VidOverPCM object
    mygtsdec.setDLLPath(DLL_PATH)                       # Pass the dll path
    mygtsdec.configureGtsDec(GTSDEC_XIDML,GTSDEC_NAME)  # Configure the GTS DEC card with the frame configuration
    mygtsdec.openGtsDec(GTSDEC_SERIAL_NUM)              # Open the card by serial number
    logging.info("GTS/DEC card successfully opened")
    mygtsdec.setupCallback()                            # Setup the default callback, this is the method declared in
                                                        # my CustomGTSDecom class
    print mygtsdec.getSummary()

    mygtsdec.run()                          # Run the acquisition
    logging.info("Acquisition running")

    second_count = 0
    while True:                 # Run for a number of seconds
        print ".",
        time.sleep(1)                       # The callback will be firing all during this point
        second_count += 1
    print ""

    logging.info("Stopping acquisition")
    mygtsdec.stop()                         # Stop the acquisition
    mygtsdec.close()                        # Close the card

if __name__ == '__main__':
    main()
