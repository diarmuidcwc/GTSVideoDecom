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
from threading import Thread
from threading import Event
import logging

# Constants for this script
GTSDEC_SERIAL_NUM = "XS9766"
DLL_PATH = os.path.join("C:\\","ACRA","GroundStationSetup","3.3.0","Software","Bin","gtsdecw.dll")
#SRC_XIDML = "Configuration/vid_106_103.XML"
SRC_XIDML = "Configuration/vid_single106_145.XML"
GTSDEC_XIDML = "Configuration/gtsdec5.xml"
GTSDEC_NAME = "MyCard"


class RunThread(Thread):
    '''Very basic thread in which to run the sleep loop while the callbacks are running'''
    def __init__(self):
        super(RunThread,self).__init__()
        self._stop = Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        second_count = 0
        minute_count = 0
        while True:
            time.sleep(1)                       # The callback will be firing all during this point

            if second_count % 60 == 0:
                print "{} minutes".format(minute_count)
                minute_count += 1
            print ".",
            second_count += 1
            if self._stop.isSet():
                return

def main():


    parser = argparse.ArgumentParser(description='Bridge GTS/DEC to Video UDP stream')
    parser.add_argument('--gtsdec', type=str, required=True, help='the GTS/DEC configuration file')
    parser.add_argument('--xidml', type=str, required=True, help='the DASStudio or KSM xidml')
    parser.add_argument('--dstip', type=str, required=False,default="235.0.0.1", help='the destination IP address')
    parser.add_argument('--dstudp', type=int, required=False,default=7777, help='the destination UDP port')
    parser.add_argument('--verbose', type=int, required=False,default=2, help='Verbose level (1=error,2=warn,3=info,4=debug)')
    parser.add_argument('--quiet',  action='store_true', help='Quiet Mode')

    args = parser.parse_args()


    # Setup a logger


    if args.verbose == 1:
        dbg_level = logging.ERROR
    elif args.verbose == 2:
        dbg_level = logging.WARN
    elif args.verbose == 3:
        dbg_level = logging.INFO
    elif args.verbose == 4:
        dbg_level = logging.DEBUG
    if args.quiet :
        dbg_level = logging.ERROR

    logging.basicConfig(format='%(asctime)s %(message)s', level=dbg_level)



    # Get the source xidml file with the VID PCM structure
    vidxidml = VidOverPCM.VidOverPCM()
    vidxidml.parseXidml(args.xidml)
    for vidname in vidxidml.vids:
        logging.warn("Found vid = {}".format(vidname))
    # We now have an object that knows how to convert a PCM frame into one or multiple
    # video payloads containing MPEG TS data
    logging.warn("Read in source xidml")

    # I have inherited the basic GTSDec Class so that I can replace the callback function
    mygtsdec = VideoGTSDecom.VideoGTSDecom()                         # A new GtsDec object
    mygtsdec.dstip = args.dstip
    mygtsdec.dstport = args.dstudp
    mygtsdec.logtofile = False
    mygtsdec.addVidOverPCM(vidxidml,diagnostics=False)                    # The VidOverPCM object
    mygtsdec.setDLLPath(DLL_PATH)                       # Pass the dll path
    mygtsdec.configureGtsDec(args.gtsdec,GTSDEC_NAME)  # Configure the GTS DEC card with the frame configuration
    mygtsdec.openGtsDec(GTSDEC_SERIAL_NUM)              # Open the card by serial number
    logging.warn("GTS/DEC card successfully opened")
    mygtsdec.setupCallback()                            # Setup the default callback, this is the method declared in
                                                        # my CustomGTSDecom class

    mygtsdec.run()                          # Run the acquisition
    logging.warn("Acquisition running")

    # Stick the run loop in a separate thread.
    # Not sure if this helps, is sleep blocking?
    runThread = RunThread()
    runThread.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        runThread.stop()

    print ""

    logging.warn("Stopping acquisition")
    mygtsdec.stop()                         # Stop the acquisition
    mygtsdec.close()                        # Close the card
    logging.info("Closed Card")
    exit()

if __name__ == '__main__':
    main()
