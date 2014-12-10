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


import VidOverPCM
import struct
import random
import socket
import MpegTS

def main():

    # Build up the buffer for the
    vidxidml = VidOverPCM.VidOverPCM()
    vidxidml.parseXidml("Configuration/vid_enc.xml")
    testbuffer = list()
    for t in range (1249):
        #testbuffer.append(random.randint(0,65536))
        testbuffer.append(t)
    vid_bufs = vidxidml.frameToBuffers(testbuffer)
    # Setup some mpeg ts
    mpegts = MpegTS.MpegTS()
    mpegts.dstudp += 1
    mpegts.addPayload(vid_bufs['KAD/VID/106'])
    mpegts.addPayload(vid_bufs['KAD/VID/106'])
    mpegts.addPayload(vid_bufs['KAD/VID/106'])
    print "here"


    print "here"

if __name__ == '__main__':
    main()

