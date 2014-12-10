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


import os
import time
import VidOverPCM
import VideoGTSDecom
import argparse

# Constants for this script
GTSDEC_SERIAL_NUM = "XS9766"
DLL_PATH = os.path.join("C:\\","ACRA","GroundStationSetup","3.3.0","Software","Bin","gtsdecw.dll")
#SRC_XIDML = "Configuration/vid_106_103.XML"
SRC_XIDML = "Configuration/vid_single106_145.XML"
GTSDEC_XIDML = "Configuration/gtsdec5.xml"
GTSDEC_NAME = "MyCard"


def main():


    parser = argparse.ArgumentParser(description='Bridge GTS/DEC to Video UDP stream')
    parser.add_argument('--gtsdec', type=str, required=True, help='the GTS/DEC configuration file')
    parser.add_argument('--xidml', type=str, required=True, help='the DASStudio or KSM xidml')
    parser.add_argument('--dstip', type=str, required=False,default="235.0.0.1", help='the destination IP address')
    parser.add_argument('--dstudp', type=int, required=False,default=7777, help='the destination UDP port')

    args = parser.parse_args()


    # Setup a logger
    import logging
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)



    # Get the source xidml file with the VID PCM structure
    vidxidml = VidOverPCM.VidOverPCM()
    vidxidml.parseXidml(args.xidml)
    for vidname in vidxidml.vids:
        logging.info("Found vid = {}".format(vidname))
    # We now have an object that knows how to convert a PCM frame into one or multiple
    # video payloads containing MPEG TS data
    logging.info("Read in source xidml")

    # I have inherited the basic GTSDec Class so that I can replace the callback function
    mygtsdec = VideoGTSDecom.VideoGTSDecom()                         # A new GtsDec object
    mygtsdec.dstip = args.dstip
    mygtsdec.dstport = args.dstudp
    mygtsdec.logtofile = False
    mygtsdec.addVidOverPCM(vidxidml,diagnostics=False)                    # The VidOverPCM object
    mygtsdec.setDLLPath(DLL_PATH)                       # Pass the dll path
    mygtsdec.configureGtsDec(args.gtsdec,GTSDEC_NAME)  # Configure the GTS DEC card with the frame configuration
    mygtsdec.openGtsDec(GTSDEC_SERIAL_NUM)              # Open the card by serial number
    logging.info("GTS/DEC card successfully opened")
    mygtsdec.setupCallback()                            # Setup the default callback, this is the method declared in
                                                        # my CustomGTSDecom class
    print mygtsdec.logSummary()

    mygtsdec.run()                          # Run the acquisition
    logging.info("Acquisition running")

    second_count = 0
    minute_count = 0
    while True:                 # Run for a number of seconds
        print ".",
        time.sleep(1)                       # The callback will be firing all during this point
        if second_count % 60 == 0:
            print "{} minutes".format(minute_count)
            minute_count += 1
        second_count += 1
    print ""

    logging.info("Stopping acquisition")
    mygtsdec.stop()                         # Stop the acquisition
    mygtsdec.close()                        # Close the card

if __name__ == '__main__':
    main()
