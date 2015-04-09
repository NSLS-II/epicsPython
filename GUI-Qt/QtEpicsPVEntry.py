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

#class QtEpicsPVLabel(QtCore.QObject):
class QtEpicsPVEntry(QtGui.QWidget):
   """
   This module provides a class library for a GUI label field widget bound to an Epics PV. The PV is monitored
   and the field is updated when the PV changes

   """
   is_drawn = 1
   changeColor = QtCore.pyqtSignal() 

   def __init__(self, pvname,parent,input_width,type_string,precision = 2):
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
      super(QtEpicsPVEntry, self).__init__() 
      self.pv_statestrings = [] #for enums, b/c this CaChannel ignores type conversions on callback returns
      self.precision = precision
      self.entry_var = ""
      self.entry_pv = pvCreate(pvname,self._conCB)
      time.sleep(0.05)
      if (type_string == "none"):
        self.entry = QtGui.QLineEdit(parent)
      else:
        self.entry = QtGui.QLineEdit(parent) # how about validator
#        self.entry = Pmw.EntryField(parent,value=str(pvGet(self.entry_pv)),validate = {'validator':type_string})
      if (input_width != 0):
        self.entry.setFixedWidth(input_width)

      if (ca.dbf_text(self.entry_pv.field_type()) == "DBF_ENUM"):
        self.entry_pv.getControl()
        self.pv_statestrings = getattr(self.entry_pv.callBack,'pv_statestrings')
        self.entry_var = pvGet(self.entry_pv)
      else:
        try: #because the connection CB handles the timeout for PVs that don't exist
          self._set_entry_var_with_precision(pvGet(self.entry_pv))
        except CaChannelException:
          self.entry_var = "-----"
          self.entry.setText(self.entry_var)
          self.emit(QtCore.SIGNAL("changeColor"),"white")
          return

      self.connect(self, QtCore.SIGNAL("changeColor"),self.setColor)
      add_callback(self.entry_pv,self._entry_pv_movingCb,"")


   def _conCB(self,epics_args, user_args):
#     print "in Con callback %d" % epics_args[1]
     if (epics_args[1] == 6):
       if (QtEpicsPVEntry.is_drawn):
         self.emit(QtCore.SIGNAL("changeColor"),"white")
#          self.entry.configure(background="#729fff")
     elif (epics_args[1] == 7):
       self.entry_var = "-----"
       self.entry.setText(self.entry_var)
       self.emit(QtCore.SIGNAL("changeColor"),"white")


   def _entry_pv_movingCb(self,epics_args, user_args):
#      print "in callback " + str(epics_args['pv_value']) + " " + ca.dbf_text(epics_args['type'])
#HEY - NOTE THAT i'M SETTING THE TEXT IN THE CALLBACK INSTEAD OF EMITTING A SIGNAL TO DO IT. i DID THAT IN THE COUNTER CHANNEL CLASS.
      if not (QtEpicsPVEntry.is_drawn):
        return
      if (ca.dbf_text(epics_args['type']) == "DBF_CHAR"):         
        self.entry_var=waveform_to_string(epics_args['pv_value'])
      elif (ca.dbf_text(epics_args['type']) == "DBF_ENUM"):
        if (self.pv_statestrings):
          self.entry_var=self.pv_statestrings[epics_args['pv_value']]
        else:
          self.entry_var=epics_args['pv_value']
      else:
#        self.emit(QtCore.SIGNAL("changeColor"),"green")
        self._set_entry_var_with_precision(epics_args['pv_value'])                    
      self.entry.setText(self.entry_var)


        
   def _set_entry_var_with_precision(self,inval):
      try:
        val = float(inval)
        if (self.precision == 0):
           self.entry_var = "%.0f" % val
        elif (self.precision == 1):
           self.entry_var = "%.1f" % val
        elif (self.precision == 2):
           self.entry_var = "%.2f" % val
        elif (self.precision == 3):
           self.entry_var ="%.3f" % val
        elif (self.precision == 4):
           self.entry_var = "%.4f" % val
        else:
           self.entry_var ="%.5f" % val
      except TypeError:
         self.entry_var = waveform_to_string(inval)
      except ValueError:
         self.entry_var = waveform_to_string(inval)
 


#   def pack(self,side=LEFT,padx=0,pady=0): #pass the params in
#      self.entry.pack(side=side,padx=padx,pady=pady)

   def getEntry(self):
      return self.entry

   def getField(self):
      return self.entry_var

   def text(self):
      return self.entry_var
   
   def setField(self,value):
      self.entry_var = value

   def setColor(self,color_s="pink"):
     self.entry.setStyleSheet("background-color: %s;" % color_s)


   
