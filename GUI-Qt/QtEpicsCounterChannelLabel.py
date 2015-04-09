"""
   This module provides a class library for a GUI label field widget bound to an Epics PV. The PV is monitored
   and the field is updated when the PV changes

Author:         John Skinner
Created:        Feb. 30, 2014
Modifications:
"""

import epicsPV
from beamline_support import *
from PyQt4 import QtGui, QtCore
import time

class QtEpicsCounterChannelLabel(QtGui.QWidget):
   """
   This module provides a class library for a GUI label field widget bound to an Epics PV. The PV is monitored
   and the field is updated when the PV changes

   """
   is_drawn = 1
   changeColor = QtCore.pyqtSignal() 
   writeValue = QtCore.pyqtSignal() 


   def __init__(self, pvname,parent,channel_number,input_width):
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
      super(QtEpicsCounterChannelLabel, self).__init__() 
      self.entry_var = ""
#      self.entry_pv = pvCreate(pvname+".S"+str(channel_number),self._conCB)
      self.entry_pv = pvCreate(pvname+".S"+str(channel_number))
      self.entry_dmov_pv = pvCreate(pvname+".CNT")
#      time.sleep(0.05)
      self.entry_var = str(pvGet(self.entry_pv))
      self.entry = QtGui.QLabel(parent)
      self.connect(self, QtCore.SIGNAL("changeColor"),self.setColor)
      self.connect(self, QtCore.SIGNAL("writeValue"),self.setTextValue)
      add_callback(self.entry_pv,self._entry_pv_movingCb,"")

      add_callback(self.entry_dmov_pv,self._entry_pv_dmovCb,[])




   def _entry_pv_movingCb(self,epics_args, user_args):
#      print "in callback " + str(epics_args['pv_value']) + " " + ca.dbf_text(epics_args['type'])
      if not (QtEpicsCounterChannelLabel.is_drawn):
        return
      self.entry_var=str(epics_args['pv_value'])
#      self.entry.setText(self.entry_var)
#      self.emit(QtCore.SIGNAL("changeColor"),"green")
      self.emit(QtCore.SIGNAL("writeValue"))

   def _entry_pv_dmovCb(self,epics_args, user_args):
#      print "in callback " + str(epics_args['pv_value'])
      if not (QtEpicsCounterChannelLabel.is_drawn):
        return
      if (epics_args['pv_value'] == 0):
        self.emit(QtCore.SIGNAL("changeColor"),"yellow")
      else:
        self.emit(QtCore.SIGNAL("changeColor"),"green")


        

#   def pack(self,side=LEFT,padx=0,pady=0): #pass the params in
#      self.entry.pack(side=side,padx=padx,pady=pady)

   def getEntry(self):
      return self.entry

   def getField(self):
      return self.entry_var
   
   def setTextValue(self):
      self.entry.setText(self.entry_var)
   
   def setColor(self,color_s="pink"):
     self.entry.setStyleSheet("background-color: %s;" % color_s)


   
