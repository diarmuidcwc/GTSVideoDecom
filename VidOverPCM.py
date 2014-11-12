#-------------------------------------------------------------------------------
# Name:        VidOverPCM
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

from lxml import etree
import re
import array
import struct

def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)


class VidOverPCM():
    def __init__(self):
        self.xidml = None
        self.tree = None
        self.root = None
        self.vid106s = dict()
        self.vidInstruments = "KAD/VID/106"
        # Hard code these for the moment but they can be pulled from the xidml
        self.minorFrameOffsetBits = 32
        self.minorFramesPerMajorFrames =1
        self.bitsPerFrame = 20000
        self.dataBitsPerWord = 16
        self.vidsPerXidml = list()
        # Internal only
        self._parameterOfInterestRE = "_VIDEO_"
        self._allVidParams = dict()

    def parseXidml(self,xidml):
        '''Parse a xidml2.4 file and setup the VidOverPCM class'''
        try:
            self.tree = etree.parse(xidml)
            self.root = self.tree.getroot()
        except:
            raise IOError("Failed to parse {}".format(xidml))
        self.xidml = xidml
        self._findAllModules()
        self._findAllParameters()
        self._findAllPCMPackages()
        self._numberOfVids()



    def _numberOfVids(self):
        '''Calculate how many separate VID instruments have parameters'''
        for vid,params in self.vid106s.iteritems():
            numberOfParams = len(params)
            if numberOfParams > 0:
                self.vidsPerXidml.append(vid)



    def frameToBuffers(self,listofwords):
        '''Takes a buffer containing a major frame and returns a list of buffers of MPEG_TS'''
        vid_bufs = {}
        for vid in self.vid106s:
            vid_bufs[vid] = ""
        for vid,params in self.vid106s.items():
            numberOfParams = len(params)
            # create a temp dict so that I can build the string out of order
            _buffertmp = {}
            for p_index,param in enumerate(natural_sort(params)):
                for wd_index,word_offset in enumerate(params[param]):
                    _buffertmp[(wd_index*numberOfParams)+p_index] = struct.pack('>H',listofwords[word_offset])

            # Now convert the dict back into string buffers
            for idx in sorted(_buffertmp):
                vid_bufs[vid] += _buffertmp[idx]

        return vid_bufs



    def _findAllModules(self):
        '''Find all the video instruments in the xidml'''
        allModules = self.root.findall(".//PartReference")
        for module in allModules:
            if module.text == self.vidInstruments:
                vidname = module.getparent().getparent().attrib["Name"]
                self.vid106s[vidname] = dict() # dict will contain the parameters + locations


    def _findAllParameters(self):
        '''Find all the parameters of interest connected to the video instruments'''
        allParameters = self.root.findall(".//Parameter")
        for parameter in allParameters:
            source_instrument = parameter.find("Source/Signal/InstrumentReference")
            if source_instrument != None:
                if source_instrument.text in self.vid106s:
                    if re.search(self._parameterOfInterestRE,parameter.attrib["Name"]):
                        # Build up a dict containing each instrument, each parameter and a list of the word offsets
                        self.vid106s[source_instrument.text][parameter.attrib["Name"]] = list()
                        self._allVidParams[parameter.attrib["Name"]] = source_instrument.text


    def _findAllPCMPackages(self):
        '''Find all the parameters of interest connected to the video instruments'''
        allPCMPackages= self.root.findall("Packages/PackageSet/X-IRIG-106-Ch-4-1.2")
        for package in allPCMPackages:
            for param in package.findall("Content/Parameter"):
                pname = param.attrib["Name"]
                if pname in self._allVidParams:
                    # Some testing of supported structures
                    if int(param.findtext("NumberOfDataBits")) != 16:
                        raise Exception("Video parameters of 1 word supported only")
                    if int(param.findtext("Location/MinorFrameNumber")) != 1:
                        raise Exception("Currently only support 1 minor frame")

                    # We have to handle the offset and then get a word index
                    if param.findtext("Location/Occurrences"):
                        poccurrances = int(param.findtext("Location/Occurrences"))
                    else:
                        poccurrances = 1

                    # Databits in words
                    if param.findtext("NumberOfDataBits"):
                        dbits = int(param.findtext("NumberOfDataBits"))
                    else:
                        dbits = self.dataBitsPerWord

                    firstWordOffset = int(param.findtext("Location/Offset_Bits"))/dbits
                    offsetWordInterval = self.bitsPerFrame / (poccurrances * dbits)
                    # If there are multiple instances of the word in a frame then they are equally spaced in the fram
                    # record the word offset per parameter in an array
                    for offset in range(poccurrances):
                        self.vid106s[self._allVidParams[pname]][pname].append(firstWordOffset+(offsetWordInterval*offset))




