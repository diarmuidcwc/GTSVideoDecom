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
from profilehooks import profile




class VideoGTSDecom(GtsDec.GtsDec):
    '''Create a new class inheriting the GtsDec class. Override the callback method using this approach'''

    BASE_UDP_PORT = 7777

    def __init__(self):
        super(VideoGTSDecom, self).__init__()
        self.vidOverPCM = VidOverPCM.VidOverPCM()
        self.mpegTS = dict()
        self.logtofile = True
        self.dstip = "235.0.0.1"
        self.dstport = 7777
        self._debugcount = 0

    def addVidOverPCM(self,vidoverPCM,diagnostics=True):
        '''
        :type vidoverPCM: VidOverPCM.VidOverPCM
        '''
        self.vidOverPCM = vidoverPCM
        udp_port = self.dstport
        for vid in self.vidOverPCM.vidsPerXidml:
            self.mpegTS[vid] = MpegTS.MpegTS(udpport=udp_port,ipaddress=self.dstip,name=vid)
            self.mpegTS[vid].diagnostics = diagnostics
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
        self._debugcount += 1
        #print "Received frame count {} wordcount = {} time = {}".format(self._debugcount,wordCount,time.clock())
        vid_bufs = self.vidOverPCM.frameToBuffers(pwords[:wordCount])
        for vid,buf in vid_bufs.iteritems():
            #print "Decom frame vid = {}".format(vid)
            #start= time.clock()
            self.mpegTS[vid].addPayload(buf)
            #end= time.clock()
            #logging.info("Start = {} Time To Run = {}".format(start,end-start))
        return 0
