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
#import VidOverPCM
#import VideoGTSDecom
from Tkinter import *

class ControlFrame(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent, background="white")

        self.parent = parent
        self.xidmlfname = StringVar()
        self.gtsfname = StringVar()

        self.initUI()
        self._addMenuBar()
        self._addLabels()
        self.xidmlfname.set("XidmlFname")
        self.gtsfname.set("GTSFname")

    def initUI(self):

        self.parent.title("Simple")

    def _addMenuBar(self):
        menubar = Menu(self.parent)
        self.parent.config(menu=menubar)
        fileMenu = Menu(menubar)
        fileMenu.add_command(label="Exit", command=self.onExit)
        menubar.add_cascade(label="File", menu=fileMenu)

    def _addLabels(self):
        xidmllabel = Label(self.parent, textvariable=self.xidmlfname)
        gtslabel   = Label(self.parent, textvariable=self.gtsfname)
        xidmllabel.grid(row=1,column=1)
        gtslabel.grid(row=2,column=1)

    def onExit(self):
        exit()


def main():

    root = Tk()
    root.geometry("200x400+300+300")
    app = ControlFrame(root)
    root.mainloop()


if __name__ == '__main__':
    main()