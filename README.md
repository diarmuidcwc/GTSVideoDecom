GTSVideoDecom
=============

GTS/DEC Video Solution

#Introduction#
GTSVideoDecom is a PCM to Video solution based around the [GTS/DEC](http://www.cwc-ae.com/product/gtsdec005) card. It allows a user to decom a
PCM stream from a PCM transmitter such as a [BCU/101](http://www.cwc-ae.com/product/kadbcu101) or [ENC/106](http://www.cwc-ae.com/product/kadenc106), take out all the video words in the
frame and reconstruct and transmit the MPEG Transport Stream back out over UDP. Multiple video instruments
in the one frame are supported

Off the shelf video players such as VLC or mplayer can play back this video stream on standard computers

##Requirements##
* Windows XP or Windows 7
* [GTS/DEC decom card](http://www.cwc-ae.com/product/gtsdec005) with the SDK installed
* Python 2.7
* lxml (http://lxml.de/)

##Install##
Clone this repo to a local directory
```
git clone https://github.com/diarmuidcwc/GTSVideoDecom.git
```

##Inputs to Application##
* xidml source file from KSM or DASStudio. This file defines the instruments and the PCM frames
* xml configuration for the GTS/DEC. This file configures the GTS/DEC instrument
Sample files are in the Configuration directory

##Playback##
This application generates a single UDP stream per video instruments. The application will
report the destination IP Address and UDP Port for each stream. To playback these streams, run
VLC or mplayer as follows.
```
vlc udp://@235.0.0.1:7777
mplayer udp://@235.0.0.1:7777 -benchmark
```

