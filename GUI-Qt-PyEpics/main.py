#!/usr/bin/python
'''
Created on Apr 20, 2015

@author: slepicka
'''
import sys
from PyQt5 import QtGui, QtWidgets
from QtEpicsMotorLabel import QtEpicsMotorLabel
from QtEpicsMotorEntry import QtEpicsMotorEntry
from QtEpicsPVLabel import QtEpicsPVLabel
from QtEpicsPVEntry import QtEpicsPVEntry


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()
        
    def initUI(self):
        # Add components here
        self.labelM1RBV = QtEpicsMotorLabel("XF:AMXFMX{MC-Goni}Omega", self, 70, 5)
        self.editM1RBV = QtEpicsMotorEntry("XF:AMXFMX{MC-Goni}Omega", self, 70, 5)
        self.moveM1Btn = QtWidgets.QPushButton("Move", self)
        self.moveM1Btn.clicked.connect(self.moveM1BtnClicked)              
        
        self.labelM1Pos = QtEpicsPVLabel("XF:AMXFMX{MC-Goni}Omega.CNEN", self, 70, 5)
        self.labelM1RBVBase = QtEpicsPVLabel("XF:AMXFMX{MC-Goni}Omega.RBV", self, 70, 5)
        
        self.editM1Velo = QtEpicsPVEntry("XF:AMXFMX{MC-Goni}Omega.VELO", self, 70, 5)
                
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(self.labelM1RBV.getEntry(), 1, 0)
        grid.addWidget(self.editM1RBV.getEntry(), 1, 1)
        grid.addWidget(self.moveM1Btn, 1, 2)
        grid.addWidget(self.labelM1Pos.getEntry(), 2, 0)
        grid.addWidget(self.labelM1RBVBase.getEntry(), 3, 0)
        grid.addWidget(self.editM1Velo.getEntry(), 4, 0)

        self.setLayout(grid)
        
        self.setMinimumSize(400, 185)
        self.center()
        self.setWindowTitle("PyEpics QT Object Test")
        self.show()
        
    def center(self):        
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def moveM1BtnClicked(self):
        self.editM1RBV.getBasePV().put(self.editM1RBV.getEntry().text())

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()    
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()
