#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
ZetCode PyQt4 tutorial 

This program creates a skeleton of
a classic GUI application with a menubar,
toolbar, statusbar and a central widget. 

author: Jan Bodnar
website: zetcode.com 
last edited: September 2011
"""

import sys
from beamline_support import *
from PyQt4 import QtGui
from PyQt4 import QtCore

class Example(QtGui.QMainWindow):
    
    def __init__(self):
        super(Example, self).__init__()
        
        self.initUI()
        
    def initUI(self):               
        beamline = "john"        
        textEdit = QtGui.QTextEdit()
        tabs= QtGui.QTabWidget()

#        self.setCentralWidget(textEdit)
 
        pushButton1 = QtGui.QPushButton("QPushButton 1")
        pushButton2 = QtGui.QPushButton("QPushButton 2")
        self.command_entry = QtGui.QLineEdit(self)
        self.text_output = QtGui.QTextEdit(self)
#        self.command_entry.textChanged[str].connect(self.command)
        self.command_entry.returnPressed.connect(self.commandEntered)
        self.comm_pv = pvCreate(beamline + "_comm:command_s")
        command_frame = QtGui.QFrame(self)
    
        tab1= QtGui.QWidget()
        tab2= QtGui.QWidget()
        tab3= QtGui.QWidget()
    
        vBoxlayout= QtGui.QVBoxLayout()
        vBoxlayout.addWidget(pushButton1)
        vBoxlayout.addWidget(pushButton2)

        vBoxlayout1= QtGui.QVBoxLayout()
        vBoxlayout1.addWidget(self.command_entry)

        tabs.resize(250, 150)
    
    #Move QTabWidget to x:300,y:300
#    tabs.move(300, 300)
    
    #Set Layout for Third Tab Page
#        tab1.setLayout(vBoxlayout1)   
        tab3.setLayout(vBoxlayout)   
        command_frame.setLayout(vBoxlayout1)
    
        tabs.addTab(tab1,"Collect")
        tabs.addTab(tab2,"Beamline")
        tabs.addTab(tab3,"Whatever")
        splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical,self)
        splitter1.addWidget(tabs)
        self.setCentralWidget(splitter1)
        splitter1.addWidget(command_frame)
        splitter1.addWidget(self.text_output)

    
#    tabs.setWindowTitle('PyQt QTabWidget Add Tabs and Widgets Inside Tab')
#    tabs.show()

        exitAction = QtGui.QAction(QtGui.QIcon('exit24.png'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)

#        toolbar = self.addToolBar('Exit')
#        toolbar.addAction(exitAction)
        
        self.setGeometry(300, 300, 350, 250)
        self.setWindowTitle('Main window')    
        self.show()
        
    def commandEntered(self):
        
      comm_s = str(self.command_entry.text())
      print comm_s
      pvPut(self.comm_pv,comm_s)
        


def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()    
