#-------------------------------------------------------------------------------
# Name:        MpegTS
# Purpose:     Python class to handle very basic MPEG TS manipulation
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


import struct
import socket
import logging
import time



class MpegTS(object):
    '''Simple class that will generate and send UDP payloads containing MPEG TS data from a supplied
    The class will align the data at the start, discarding up to 188 bytes, then continuously
    transmit payload. It checks the TS every 7 blocks for alignment'''

    MPEG_TS_BLOCKS_PER_PACKET = 7
    MPEG_TS_BLOCK_LEN = 188
    UDP_PAYLOAD_LEN = MPEG_TS_BLOCKS_PER_PACKET * MPEG_TS_BLOCK_LEN
    PID_TEXT = {0x1fff : "Null", 0x0 : "Program Association Table", 0x100 : "VID106_Video" , 0x101 : "VID106_Audio", 0x1000 : "Program Map Table", 0x3E8 : "VID103_Video", 0x20 : "Unkn"}

    def __init__(self,ipaddress="192.168.28.110",udpport=777):
        #super(MpegTS,self).__init__()
        self.resetData()
        self.pids = dict()
        self.dstip = ipaddress
        self.dstudp = udpport
        self.setupUDP()


        self.diagnostics = True
        self.blocksTransmitted = 0
        self.blocksReceived = 0
        self.name = None
        self._dumpfname = None
        self._alignmentObservers = [] # Some callbacks for the alignment state
        self._diagnosticObservers = [] # Call back of diagnostics output

    def setAlignment(self,status=True):
        self.aligned = status
        self.logInfo()
        for callback in self._alignmentObservers:
            callback(self.aligned)

    def addPayload(self,payload):
        '''Accept a chunk of data and add it to the existing payload and then send when we have
        enough payload received'''

        if self.aligned == True:
            self.alignedPayload += payload
            self.sendAlignedBlocks()
        else:
            self.payload = payload
            self._alignPayload()
        if self._dumpfname and self.aligned == True:
            self._dumpToFile(payload)

    def _alignPayload(self):
        '''Take the payload and align it up to the sync word. This is called from the addPayload method'''
        byteindex = 0
        #logging.error("Attempting to Align {} loop through payload of length = {}".format(self.name,len(self.payload)))
        while self.aligned == False and len(self.payload) > byteindex:
            #print "idx={} len={}".format(byteindex,len(self.payload))
            (thisByte,) = struct.unpack_from('B',self.payload[byteindex])
            #logging.error("Byte = {:0X}".format(thisByte))
            if thisByte == 0x47:
                self.alignedPayload = self.payload[byteindex:]
                self.setAlignment()
            else:
                byteindex += 1


    def _checkAlignment(self):
        '''Verify that we are still in alignment'''
        (syncByte,tpid) = struct.unpack_from('BB',self.alignedPayload)
        if syncByte != 0x47 :
            self.setAlignment(False)
            logging.error("Out of sync in MPEG TS {}".format(self.name))


    def setupUDP(self):
        '''Open a UDP socket'''
        self.sendSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)



    def sendAlignedBlocks(self):
        '''When enough data is acquired, send out the payload'''
        if len(self.alignedPayload) > MpegTS.UDP_PAYLOAD_LEN:
            # Do a quick and cheap alignment test
            self._checkAlignment()
            # track some diagnostic info
            if self.diagnostics:
                self.trackPayload()
                #self.printDiagnostics()
            # transmit the packets
            self.sendSocket.sendto(self.alignedPayload[:MpegTS.UDP_PAYLOAD_LEN],(self.dstip,self.dstudp))
            self.alignedPayload = self.alignedPayload[MpegTS.UDP_PAYLOAD_LEN:]
            self.blocksTransmitted += MpegTS.MPEG_TS_BLOCKS_PER_PACKET

    def trackPayload(self):
        '''Keep a track of the PIDs being generated for diagnostic purposes'''
        # This should only be called before you transmit a UDP packet so I will
        # only run if there are MPEG_TS_BLOCKS_PER_PACKET blocks availabel
        if len(self.alignedPayload) > MpegTS.UDP_PAYLOAD_LEN and self.aligned == True:
            for block in range(MpegTS.MPEG_TS_BLOCKS_PER_PACKET):
                buffer_offset = MpegTS.MPEG_TS_BLOCK_LEN * block
                (syncByte,tpid,tcounter) = struct.unpack_from('>BHB',self.alignedPayload[buffer_offset:buffer_offset+6])

                if syncByte == 0x47:
                    pid = (tpid % 8192) # pid is 13 bits
                    ccounter = (tcounter % 16)
                    self.blocksReceived += 1

                    if pid in self.pids:
                        self.pids[pid]['count'] += 1
                        if (self.pids[pid]['continuity'] + 1 ) % 16 != ccounter:
                            self.pids[pid]['cdrops'] += abs(self.pids[pid]['continuity'] + 1 - ccounter)
                            self.pids[pid]['continuity'] = ccounter
                        else:
                            self.pids[pid]['continuity'] = ccounter



                    else:
                        self.pids[pid] = dict()
                        self.pids[pid]['count'] = 1
                        self.pids[pid]['continuity'] = ccounter
                        self.pids[pid]['cdrops'] = 0
                        self.pids[pid]['bps'] = 0
                        self.pids[pid]['prevCount'] = 0

                    # Figure out the bitrate at regular intervals
                    # if (self.blocksTransmitted/MpegTS.MPEG_TS_BLOCKS_PER_PACKET) % 1000 == 0:
                    #     current_time = time.time()
                    #     logging.info("here {} {} {} ".format(self.blocksTransmitted,self.pids[pid]['count'],self.pids[pid]['prevCount']))
                    #     if 'time' in self.pids[pid]:
                    #         logging.info("in here")
                    #         self.pids[pid]['bps'] = int(float((self.pids[pid]['count'] - self.pids[pid]['prevCount']  )* MpegTS.MPEG_TS_BLOCK_LEN*8 ) / (current_time-self.pids[pid]['time']))
                    #         self.pids[pid]['prevCount'] = self.pids[pid]['count']
                    #         self.pids[pid]['time'] = current_time
                    #     else:
                    #         self.pids[pid]['prevCount'] = self.pids[pid]['count']
                    #         self.pids[pid]['time'] = current_time

                    for callback in self._diagnosticObservers:
                            callback(self.pids)


    def logDiagnostics(self):
        for pid in self.pids:
            if pid in MpegTS.PID_TEXT:
                ptext = MpegTS.PID_TEXT[pid]
            else:
                ptext = str(pid)
            logging.debug("Vid= {:10s} PID = {:30s} Received = {}({:2}%) Dropped = {}".format(self.name,ptext, self.pids[pid]['count'], (self.pids[pid]['count']*100/self.blocksReceived), self.pids[pid]['cdrops']))

    def logInfo(self):
        if self.aligned:
            logging.info("{} is aligned. Transmitting to {} port {}".format(self.name,self.dstip,self.dstudp))
        else:
            logging.warn("{} is out of alignment. Stopping UDP transmission".format(self.name,self.dstip,self.dstudp))

    def resetData(self):
        self.payload = ""
        self.alignedPayload = ""
        self.aligned = False


    def _dumpToFile(self,buf):
        dumpf = open(self._dumpfname,'ab')
        dumpf.write(buf)
        dumpf.close()
