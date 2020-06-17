"""
   This module provides a class library for a GUI label field widget bound to an Epics PV. The PV is monitored
   and the field is updated when the PV changes

Author:         Hugo Slepicka
Created:        Apr. 20, 2014
Modifications:
"""

from epics import PV
from qtpy import QtCore, QtGui, QtWidgets
import time

class QtEpicsBaseWidget(QtWidgets.QWidget):
    """
    This module provides a class library for a GUI label field widget bound to an Epics PV. The PV is monitored
    and the field is updated when the PV changes
    
    """
    changeColor = QtCore.pyqtSignal(str)
    
    def __init__(self, pvname, parent, input_width, precision = 2, editable=False, highlight_on_change=True, highlight_interval=2000):
        """
        
        Inputs:
           pvname:
              The name of the epics process variable.
           parent:
              The container to place the entry widget.
           input_width:
           precision:
           highlight_on_change:
        
        Example:
          detstat_file = epicsPVLabel("x12c_comm:datafilename",filestat_frame,70)
          detstat_file.getEntry().pack(side=LEFT,fill=X,expand=YES)
        
        """      
        super(QtEpicsBaseWidget, self).__init__()
        
        self.pvname = pvname
        self.parent = parent
        self.precision = precision
        self.editable = editable
        self.highlight_on_change = highlight_on_change
        self.entry_var = ""
        self.highlight_interval = highlight_interval # 5 seconds

        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.highlight_interval)
        self.timer.timeout.connect(self.resetColor)
                
        # Creates the PV
        self.base_pv = self.entry_pv = PV(pvname, connection_callback=self._conCB, callback=self._valueChangeCB)
        self.base_pv.get_ctrlvars()
        
        self.enum_strs = None
        if("enum" in self.base_pv.type):
            self.enum_strs = self.base_pv.enum_strs
        
        self.__createWidget()
        
        self.changeColor.connect(self.setColor)
        
        if (input_width != 0):
            self.entry.setFixedWidth(input_width)
        time.sleep(0.05)
        
        try: #because the connection CB handles the timeout for PVs that don't exist
            self.__updateValue(self.base_pv.get(as_string=True), skipHighlight=True)
        except:
            self.entry_var = "-----"
            self.entry.setText(self.entry_var)
            self.changeColor.emit("white")
            return
    '''
    CALLBACKS SECTION
    '''
    def _conCB(self,conn,**kwargs):
        if (conn):
            self.changeColor.emit("blue")
            # self.entry.configure(background="#729fff")
        else:
            self.entry_var = "-----"
            self.entry.setText(self.entry_var)
            self.changeColor.emit("white")
    
    def _valueChangeCB(self,value,char_value,**kwargs):
        try:
            if(self.timer.isActive()):
                self.timer.stop()
            self.__updateValue(char_value)
        except:
            pass           

    '''
    HELPER FUNCTIONS SECTION
    '''
    def _set_entry_var_with_precision(self,inval):
        try:
            val = float(inval)
            if (self.precision in range(0,5)):
                fmtStr = "%."+str(self.precision)+"f"
                self.entry_var = fmtStr % val
            else:
                self.entry_var ="%.5f" % val
        except TypeError:
            self.entry_var = str(inval)
        except ValueError:
            self.entry_var = str(inval)

    def __createWidget(self):
        if(self.editable):
            self.entry = QtWidgets.QLineEdit(self.parent)
        else:
            self.entry = QtWidgets.QLabel(self.parent)

    def __updateValue(self, value, skipHighlight=False):
        if(self.enum_strs == None):
            self._set_entry_var_with_precision(value)
        else:
            self._set_entry_var_with_precision(self.enum_strs[value])
        self.entry.setText(self.entry_var)
        if(self.highlight_on_change and not skipHighlight):
            self.changeColor.emit("#99FF66")
            self.timer.start()      

    def resetColor(self):
        self.timer.stop()
        self.changeColor.emit("None")

    '''
    GETTERS/SETTERS SECTION
    '''
    def getEntry(self):
        return self.entry
    
    def getBasePV(self):
        return self.base_pv
    
    def getField(self):
        return self.entry_var
    
    def setField(self,value):
        self.entry_var = value
    
    def setColor(self,color_s="pink"):
        self.entry.setStyleSheet("background-color: %s;" % color_s)
    
    
    
