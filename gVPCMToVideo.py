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


import os
import time
import VidOverPCM
import VideoGTSDecom
import MpegTS
from Tkinter import *
import tkFileDialog
import logging
import pprint
import datetime



class LoggingToGui(logging.Handler):
    '''
    Class to send the logging output to a console
    '''
    def __init__(self, widget):
        logging.Handler.__init__(self)
        self.setLevel(logging.DEBUG)
        self.widget = widget
        self.widget.config(state='disabled')

    def emit(self, record):
        self.widget.config(state='normal')
        # Append message (record) to the widget
        self.widget.insert(END, self.format(record) + '\n')
        self.widget.see(END)  # Scroll to the bottom
        self.widget.config(state='disabled')




class VidFrame(LabelFrame):
    def __init__(self, parent, mpegts):
        '''
        :type parent:
        :type mpegts: MpegTS.MpegTS
        '''
        LabelFrame.__init__(self, parent, text=mpegts.name)

        self.mpegts = mpegts

        self.parent = parent
        self.udpLabel = StringVar()
        self.udpLabel.set(self.mpegts.dstudp)
        self.ipLabel = StringVar()
        self.ipLabel.set(self.mpegts.dstip)
        self.pids = dict() # dict of pids with StringVars
        self.dumpToFileStatus = IntVar()


        self.pack()
        self._addLabels()
        self._addAlignmentLabel()
        self._addDiagnostics()
        self.mpegts._alignmentObservers.append(self._setAlignment)
        self.mpegts._diagnosticObservers.append(self._displayDiagnostics)


    def _addLabels(self):
        '''
        Add all the labels to the Video Frame
        '''
        udpLabel  = Label(self, text="UDP Port")
        udpText =  Entry(self, textvariable=self.udpLabel)
        ipLabel  = Label(self, text="IP Address")
        ipText =  Entry(self, textvariable=self.ipLabel)
        udpLabel.grid(row=1,column=1)
        udpText.grid(row=1,column=2,sticky=E+W)
        ipLabel.grid(row=2,column=1)
        ipText.grid(row=2,column=2,sticky=E+W)

    def _addAlignmentLabel(self):
        '''
        Add the alignment label
        :return:
        '''
        self.alignmentLabel = Label(self,text="Not Aligned",background="red")
        self.alignmentLabel.grid(row=3,column=1,columnspan=2,sticky=E+W,pady=10,padx=10)


    def _setAlignment(self,status):
        '''
        Set the alignment in the GUI
        :type status: bool
        '''
        if status:
            self.alignmentLabel['text'] = "Aligned"
            self.alignmentLabel['background'] = "green"
        else:
            self.alignmentLabel['text'] = "Not Aligned"
            self.alignmentLabel['background'] = "red"

    def _addDiagnostics(self):
        self.logToFile = Checkbutton(self,text="Dump to file",command=self.dumpToFile,variable=self.dumpToFileStatus).grid(row=4,column=1,columnspan=2,sticky=E+W,pady=2,padx=2)
        Label(self,text="PID").grid(row=1,column=3)
        Label(self,text="Blocks Received").grid(row=1,column=4)
        Label(self,text="Dropped Blocks").grid(row=1,column=5)

    def dumpToFile(self):
        if self.dumpToFileStatus.get() == 1:
            sanitisedFname = self.mpegts.name.replace("/","_")
            self.mpegts._dumpfname = "{}_{}.ts".format(sanitisedFname,datetime.datetime.now().strftime("%Y%m%d%H%S"))
            logging.info("Writing video from {} to {}".format(self.mpegts.name,self.mpegts._dumpfname))
        else:
            self.mpegts._dumpfname = None

    def resetDiagnostics(self):
        pass

    def _displayDiagnostics(self,pids):
        '''
        Update the diagnostics of the PID display
        :type pids: dict
        '''
        for pid in sorted(pids):
            if pid in self.pids:
                self.pids[pid]['countEntryVar'].set(pids[pid]['count'])
                self.pids[pid]['dropEntryVar'].set(pids[pid]['cdrops'])
            else:
                add_row = len(self.pids)+2
                try:
                    textPID = MpegTS.MpegTS.PID_TEXT[pid]
                except:
                    textPID = pid
                self.pids[pid] = dict()
                Label(self,text=textPID).grid(row=add_row,column=3,sticky=E+W,pady=2,padx=2)
                self.pids[pid]['countEntryVar'] = StringVar()
                self.pids[pid]['countEntry'] = Entry(self, textvariable=self.pids[pid]['countEntryVar'])
                self.pids[pid]['countEntry'].grid(row=add_row,column=4,sticky=E+W,pady=2,padx=2)
                self.pids[pid]['dropEntryVar'] = StringVar()
                self.pids[pid]['dropEntry'] = Entry(self, textvariable=self.pids[pid]['dropEntryVar'])
                self.pids[pid]['dropEntry'].grid(row=add_row,column=5,sticky=E+W,pady=2,padx=2)


class MainFrame(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent)

        self._initStructures()

        # Settings
        self.dllpath    = os.path.join("C:\\","ACRA","GroundStationSetup","3.3.0","Software","Bin","gtsdecw.dll")
        self.gtsDecName = "MyCard"
        self.gtsdecSerialNum = "XS9766"

        # The windowing aspects
        self.parent = parent
        self.xidmlLabel = StringVar()
        self.gtsLabel = StringVar()

        self.runButton = None
        self.configButton = None
        self.vidFrames = []

        # The init calls
        self.initUI()
        self._addMenuBar()
        self._addLabels()
        self._addButtons()
        self._addConsole()

        self._setupLogging()

    # Create some init structures that are called on creation and on loading a new xidml
    def _initStructures(self):
        # The core of the application
        self.vidxidml = VidOverPCM.VidOverPCM()
        self.mygtsdec = VideoGTSDecom.VideoGTSDecom()
        self.mygtsdec.logtofile = False
        self.acquiring = False  # current acqusition state
        self.xidmlFName = None
        self.gtsFName = None

    ###################################
    # Methods to configure the window
    ###################################
    def initUI(self):

        self.parent.title("PCM To Video Server")

    def _addMenuBar(self):
        menubar = Menu(self.parent)
        self.parent.config(menu=menubar)
        fileMenu = Menu(menubar)
        fileMenu.add_command(label="Load DasStudio/KSM Config", command=self.loadXidml)
        fileMenu.add_command(label="Load GTSDEC Config", command=self.loadGTSConfig)
        fileMenu.add_separator()
        fileMenu.add_command(label="Exit", command=self.onExit)
        menubar.add_cascade(label="File", menu=fileMenu)

    def _addLabels(self):
        xidmllabel = Label(self.parent, text="Xidml")
        xidmltext =  Entry(self.parent, textvariable=self.xidmlLabel)
        gtslabel   = Label(self.parent, text="GTS/DEC")
        gtstext   = Entry(self.parent, textvariable=self.gtsLabel)
        xidmllabel.grid(row=1,column=1)
        gtslabel.grid(row=2,column=1)
        xidmltext.grid(row=1,column=2)
        gtstext.grid(row=2,column=2)

    def _addButtons(self):
        self.configButton = Button(self.parent,text="Configure GTS/DEC",command=self.setupGTSDec,state=DISABLED)
        self.runButton = Button(self.parent,text="Run Acqusition",command=self.toggleAcqusition,state=DISABLED,background="red")


        # place them
        self.configButton.grid(row=1,column=3,sticky=E+W,pady=5,ipady=5,ipadx=5)
        self.runButton.grid(row=2,column=3,sticky=E+W,pady=5,ipady=5,ipadx=5)

    def _addConsole(self):
        self.consoleScrollbar = Scrollbar(self.parent)
        self.console = Text(self.parent,height=10,width=50)
        self.console.config(yscrollcommand=self.consoleScrollbar.set)
        self.consoleScrollbar.config(command=self.console.yview)
        self.console.grid(row=100,column=1,columnspan=5,sticky=E+W)
        self.consoleScrollbar.grid(row=100,column=6,sticky=N+S)


    def _setupLogging(self):
        self.log = logging.getLogger()
        self.log.setLevel('DEBUG')
        ch = LoggingToGui(self.console)
        ch.setLevel(logging.DEBUG)
        self.log.addHandler(ch)
    ###################################
    # Methods to control the app
    ###################################
    def onExit(self):
        exit()

    def loadXidml(self):
        self._initStructures()

        fname = tkFileDialog.askopenfilename(filetypes=(("DASStudio Files", "*.xidml"),
                                           ("KSM Files", "*.xml"),
                                           ("All files", "*.*") ))

        if os.path.exists(fname):
            self.xidmlFName = fname
            self.xidmlLabel.set(os.path.basename(fname))

            self.vidxidml.parseXidml(fname)
            self.mygtsdec.addVidOverPCM(self.vidxidml)
            for vidname in self.vidxidml.vids:
                logging.info("Found vid = {}".format(vidname))
            myrow = 3
            for mpegts in self.mygtsdec.mpegTS.itervalues():
                vframe = VidFrame(self.parent,mpegts)
                vframe.grid(row=myrow,column=1,columnspan=5,sticky=E+W,pady=10,padx=10)
                vframe.grid(row=myrow,column=1,columnspan=5,sticky=E+W,pady=10,padx=10)
                self.vidFrames.append(vframe)
                myrow += 20


        else:
            return 0


    def loadGTSConfig(self):
        fname = tkFileDialog.askopenfilename(filetypes=(("GTS/DEC Configuration", "*.xml"),
                                           ("All files", "*.*") ))
        if os.path.exists(fname):
            self.gtsLabel.set(os.path.basename(fname))
            self.gtsFName = fname
            self.configButton['state'] = 'normal'



    def setupGTSDec(self):
        try:
            logging.info("Configuring the GTS/DEC card. Please wait...")
            self.mygtsdec.setDLLPath(self.dllpath)                       # Pass the dll path
            self.mygtsdec.configureGtsDec(self.gtsFName,self.gtsDecName)  # Configure the GTS DEC card with the frame configuration
            self.mygtsdec.openGtsDec(self.gtsdecSerialNum)              # Open the card by serial number
            #logging.info("GTS/DEC card successfully opened")
            self.mygtsdec.setupCallback()                            # Setup the default callback, this is the method declared in
                                                                    # my CustomGTSDecom class
            self.runButton['state'] = 'normal'
        except:
            logging.error("Failed to program GTS/DEC {} with configuration {}".format(self.gtsDecName,self.gtsFName))

    def toggleAcqusition(self):
        if self.acquiring == False:
            self.mygtsdec.run()
            self.acquiring = True
            self.configButton['state'] = 'disabled'
            self.runButton['text'] = "Stop Acqusition"
            self.runButton['background'] = "green"
        else:
            self.mygtsdec.stop()
            self.acquiring = False
            self.configButton['state'] = 'normal'
            self.runButton['text'] = "Run Acqusition"
            self.runButton['background'] = "red"
            for vidframe in self.vidFrames:
                vidframe._setAlignment(False)
                vidframe.mpegts.resetData()

def main():

    root = Tk()
    root.geometry("600x800+100+100")
    app = MainFrame(root)
    root.mainloop()


if __name__ == '__main__':
    main()