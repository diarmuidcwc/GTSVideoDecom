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
import math
import logging

def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)


class VidOverPCM():
    def __init__(self):
        self.xidml = None
        self.xidmlVersion = "2.41"
        self.tree = None
        self.root = None
        self.vids = dict()
        self.vidInstruments = {"KAD/VID/106","KAD/VID/103"}
        # Hard code these for the moment but they can be pulled from the xidml
        self.minorFrameOffsetBits = 32
        self.minorFramesPerMajorFrames =1
        self.dataBitsPerWord = 16
        self.vidsPerXidml = list()
        # Internal only
        self._parameterOfInterestRE = "_VIDEO_"
        self._parameterReferenceVendorOfInterestRE = "MPEG2TS|Video"
        self._allVidParams = dict()

    def parseXidml(self,xidml):
        '''Parse a xidml2.4 file and setup the VidOverPCM class
        :type xidml: str
        '''
        try:
            self.tree = etree.parse(xidml)
            self.root = self.tree.getroot()
        except:
            raise IOError("Failed to parse {}".format(xidml))
        self.xidml = xidml
        self.xidmlVersion = self.root.attrib["Version"]
        self._findAllModules()
        self._findAllParameters()
        self._findAllPCMPackages()
        self._numberOfVids()



    def _numberOfVids(self):
        '''Calculate how many separate VID instruments have parameters'''
        for vid,params in self.vids.iteritems():
            numberOfParams = len(params)
            if numberOfParams > 0:
                self.vidsPerXidml.append(vid)



    def frameToBuffers(self,listofwords):
        '''Takes a buffer containing a major frame and returns a list of buffers of MPEG_TS
        :type listofwords: list(str)
        '''
        vid_bufs = {}
        #print "DEBUG: list of words len = {}".format(len(listofwords))
        for vid in self.vids:
            vid_bufs[vid] = ""
        for vid,params in self.vids.items():
            numberOfParams = len(params)
            # create a temp dict so that I can build the string out of order
            _buffertmp = {}
            for p_index,param in enumerate(natural_sort(params)):
                for wd_index,word_offset in enumerate(params[param]):
                    # bounds check
                    if word_offset > len(listofwords):
                        raise ValueError ("List of words not long enough .Are you using the correct xidml source file?")
                    _buffertmp[(wd_index*numberOfParams)+p_index] = struct.pack('>H',listofwords[word_offset])

            # Now convert the dict back into string buffers
            for idx in sorted(_buffertmp):
                vid_bufs[vid] += _buffertmp[idx]

        return vid_bufs



    def _findAllModules(self):
        '''Find all the video instruments in the xidml both 2.4 and 3.0'''
        allModules = self.root.findall(".//PartReference")
        for module in allModules:
            if module.text in self.vidInstruments:
                vidname = module.getparent().getparent().attrib["Name"]
                self.vids[vidname] = dict() # dict will contain the parameters + locations


    def _findAllParameters(self):
        '''Find all the parameters of interest connected to the video instruments'''
        allParameters = self.root.findall(".//Parameter")
        if self.xidmlVersion == "2.41":
            for parameter in allParameters:
                source_instrument = parameter.find("Source/Signal/InstrumentReference")
                if source_instrument != None:
                    if source_instrument.text in self.vids:
                        if re.search(self._parameterOfInterestRE,parameter.attrib["Name"]):
                            # Build up a dict containing each instrument, each parameter and a list of the word offsets
                            self.vids[source_instrument.text][parameter.attrib["Name"]] = list()
                            self._allVidParams[parameter.attrib["Name"]] = source_instrument.text
        else:
            allParameterReferences = self.root.findall(".//Parameters/ParameterReference")
            for parameterreference in allParameterReferences:
                source_instrument = parameterreference.getparent().getparent().attrib["Name"]
                if source_instrument != None:
                    if source_instrument in self.vids:
                        if re.search(self._parameterReferenceVendorOfInterestRE, parameterreference.attrib["VendorName"]):
                            self.vids[source_instrument][parameterreference.text] = list()
                            self._allVidParams[parameterreference.text] = source_instrument


    def _findAllPCMPackages(self):
        '''Find all the parameters of interest connected to the video instruments'''
        if self.xidmlVersion == "2.41":
            allPCMPackages= self.root.findall("Packages/PackageSet/X-IRIG-106-Ch-4-1.2")
            for package in allPCMPackages:
                bitsPerFrame = int(package.findtext("Properties/MajorFrameProperties/BitsPerMinorFrame"))
                minorFramesPerMajorFrames = int(package.findtext("Properties/MajorFrameProperties/MinorFramesPerMajorFrame"))
                for param in package.findall("Content/Parameter"):
                    pname = param.attrib["Name"]
                    if pname in self._allVidParams:
                        # Some testing of supported structures
                        if int(param.findtext("NumberOfDataBits")) != 16:
                            raise Exception("Video parameters of 1 word supported only")
                        if int(param.findtext("Location/MinorFrameNumber")) != 1:
                            raise Exception("Currently only support 1 minor frame")

                        # We have to handle the offset and then get a word index
                        #Occurrances seem o be ber major frame so divide to get occurrances per minor frame
                        if param.findtext("Location/Occurrences"):
                            poccurrances = int(param.findtext("Location/Occurrences")) / minorFramesPerMajorFrames
                        else:
                            poccurrances = 1

                        # Databits in words
                        if param.findtext("NumberOfDataBits"):
                            dbits = int(param.findtext("NumberOfDataBits"))
                        else:
                            dbits = self.dataBitsPerWord

                        firstWordOffset = int(param.findtext("Location/Offset_Bits"))/dbits
                        offsetWordInterval = bitsPerFrame / (poccurrances * dbits)
                        # If there are multiple instances of the word in a frame then they are equally spaced in the fram
                        # record the word offset per parameter in an array
                        for offset in range(poccurrances):
                            self.vids[self._allVidParams[pname]][pname].append(firstWordOffset+(offsetWordInterval*offset))
        else:
            allPCMPackages= self.root.findall("Packages/PackageSet/IRIG-106-Ch-4")
            for package in allPCMPackages:
                bitsPerFrame = int(package.findtext("Properties/MajorFrameProperties/BitsPerMinorFrame"))
                dbits = int(package.findtext("Properties/MajorFrameProperties/DefaultDataBitsPerWord"))
                minorframeoffset = int(package.findtext("Properties/SynchronizationStrategy/SubframeSynchronizationStrategy/SFID/MinorFrameOffset_Words"))
                for mapping in package.findall("Content/Mapping"):
                    pref = mapping.findtext("ParameterReference")
                    if pref in self._allVidParams:
                        if int(mapping.findtext("Location/MinorFrameNumber")) != 1:
                            raise Exception("Currently only support 1 minor frame")

                        if mapping.findtext("Location/Occurrences"):
                            poccurrances = int(mapping.findtext("Location/Occurrences"))
                        else:
                            poccurrances = 1

                        # Databits in words
                        firstWordOffset = int(mapping.findtext("Location/Offset_Words"))
                        (remainder, offsetWordInterval) = math.modf(float(bitsPerFrame) / (poccurrances * dbits))
                        logging.warning("Illegal xidml frame. I can only guess the frame structure based on the xidml")
                        # DASStudio generates invalid frames at time and this is the workaround
                        roundUpEveryXOccurances = int(math.ceil(1/remainder))
                        offsetWordInterval = int(offsetWordInterval)
                        # If there are multiple instances of the word in a frame then they are equally spaced in the fram
                        # record the word offset per parameter in an array
                        addOffsetIllegalFrame = 0
                        for offset in range(poccurrances):
                            self.vids[self._allVidParams[pref]][pref].append(addOffsetIllegalFrame+minorframeoffset+firstWordOffset+(offsetWordInterval*offset))
                            if offset % offsetWordInterval == (offsetWordInterval-1):
                                addOffsetIllegalFrame += 1



