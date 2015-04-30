"""
   This module provides a class library for a GUI label field widget bound to an Epics PV. The PV is monitored
   and the field is updated when the PV changes

Author:         John Skinner
Created:        Feb. 30, 2014
Modifications:
Apr. 20, 2015 - Hugo Slepicka - Changing from caChannel to PyEpics
"""

from PyQt4 import QtGui, QtCore
from QtEpicsMotorWidget import QtEpicsMotorWidget
import time

class QtEpicsMotorEntry(QtEpicsMotorWidget):
   """
   This module provides a class library for a GUI label field widget bound to an Epics PV. The PV is monitored
   and the field is updated when the PV changes

   """
   def __init__(self, pvname,parent,input_width,precision = 2):
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
      super(QtEpicsMotorEntry, self).__init__(pvname, parent, input_width, precision, editable=True) 
      