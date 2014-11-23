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
#import VideoGTSDecom
from Tkinter import *
import tkFileDialog
import logging

class LoggingToGui(logging.Handler):
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

class VideoFrame(Frame,):
    def __init__(self, parent):
        Frame.__init__(self, parent, background="white")


class MainFrame(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent, background="white")

        # The core of the application
        self.vidxidml = VidOverPCM.VidOverPCM()
        #self.mygtsdec = VideoGTSDecom.VideoGTSDecom()
        self.acquiring = False  # current acqusition state

        # Settings
        self.dllpath    = os.path.join("C:\\","ACRA","GroundStationSetup","3.3.0","Software","Bin","gtsdecw.dll")
        self.gtsDecName = "MyCard"
        self.gtsdecSerialNum = "XS9766"

        # The windowing aspects
        self.parent = parent
        self.xidmlLabel = StringVar()
        self.xidmlFName = None
        self.gtsLabel = StringVar()
        self.gtsFName = None
        self.runButton = None
        self.configButton = None

        # The init calls
        self.initUI()
        self._addMenuBar()
        self._addLabels()
        self._addButtons()
        self._addConsole()

        self._setupLogging()

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
        self.runButton = Button(self.parent,text="Run Acqusition",command=self.toggleAcqusition,state=DISABLED)

        # place them
        self.configButton.grid(row=1,column=3)
        self.runButton.grid(row=2,column=3)

    def _addConsole(self):
        self.console = Text(self.parent,height=10,width=50)
        self.console.grid(row=10,column=1,columnspan=3)


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
        fname = tkFileDialog.askopenfilename(filetypes=(("DASStudio Files", "*.xidml"),
                                           ("KSM Files", "*.xml"),
                                           ("All files", "*.*") ))

        if os.path.exists(fname):
            self.xidmlFName = fname
            self.xidmlLabel.set(os.path.basename(fname))

            self.vidxidml.parseXidml(fname)
            #self.mygtsdec.addVidOverPCM(self.vidxidml)
            for vidname in self.vidxidml.vids:
                logging.info("Found vid = {}".format(vidname))

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
        self.mygtsdec.setDLLPath(self.dllpath)                       # Pass the dll path
        self.mygtsdec.configureGtsDec(self.gtsFName,self.gtsDecName)  # Configure the GTS DEC card with the frame configuration
        self.mygtsdec.openGtsDec(self.gtsdecSerialNum)              # Open the card by serial number
        #logging.info("GTS/DEC card successfully opened")
        self.mygtsdec.setupCallback()                            # Setup the default callback, this is the method declared in
                                                                # my CustomGTSDecom class
        self.runButton['state'] = 'normal'

    def toggleAcqusition(self):
        if self.acquiring == False:
            self.mygtsdec.run()
            self.acquiring = True
            self.configButton['state'] = 'disabled'
            self.runButton['text'] = "Stop Acqusition"
        else:
            self.mygtsdec.stop()
            self.acquiring = False
            self.configButton['state'] = 'normal'
            self.runButton['text'] = "Run Acqusition"

def main():

    root = Tk()
    root.geometry("400x400+300+300")
    app = MainFrame(root)
    root.mainloop()


if __name__ == '__main__':
    main()