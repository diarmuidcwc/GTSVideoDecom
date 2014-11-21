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
import GtsDec
import MpegTS
import VidOverPCM
import datetime
import logging


class VideoGTSDecom(GtsDec.GtsDec):
    '''Create a new class inheriting the GtsDec class. Override the callback method using this approach'''

    BASE_UDP_PORT = 7777

    def __init__(self):
        super(VideoGTSDecom, self).__init__()
        self.vidOverPCM = VidOverPCM.VidOverPCM()
        self.mpegTS = dict()
        self.logtofile = True

    def addVidOverPCM(self,vidoverPCM):
        self.vidOverPCM = vidoverPCM
        udp_port = VideoGTSDecom.BASE_UDP_PORT
        for vid in self.vidOverPCM.vidsPerXidml:
            self.mpegTS[vid] = MpegTS.MpegTS(udpport=udp_port)
            self.mpegTS[vid].name = vid
            if self.logtofile:
                sanitisedFname = vid.replace("/","_")
                self.mpegTS[vid]._dumpfname = "{}_{}.ts".format(sanitisedFname,datetime.datetime.now().strftime("%Y%m%d%H%S"))
            udp_port += 1

    def logSummary(self):
        ret_str = ""
        for vid in self.vidOverPCM.vidsPerXidml:
            logging.info("Transmitting vid {} to address {} on port {}\n".format(self.mpegTS[vid].name,self.mpegTS[vid].dstip,self.mpegTS[vid].dstudp))



    def bufferCallBack(self,timeStamp,pwords,wordCount,puserInfo):
        '''The callback method that is run on every frame'''
        # This method will take a full PCM frame and return a dict of buffers
        # one for each VID in the PCM frame
        vid_bufs = self.vidOverPCM.frameToBuffers(pwords[:wordCount])
        for vid,buf in vid_bufs.iteritems():
            #print "Decom frame vid = {}".format(vid)
            self.mpegTS[vid].addPayload(buf)
        return 0
