"""
This module provides a class library for a GUI label field widget bound to an Epics scaler counter channel. The counter channel is monitored
and the field is updated and lit up green when the count changes.


Author:         John Skinner
Created:        Nov, 2 2009
Modifications:
"""

import epicsPV
from mtTkinter import *
import Pmw
from beamline_support import *

class epicsCounterChannelLabel:
   """
   This module provides a class library for a GUI label field widget bound to an Epics scaler counter channel. The counter channel is monitored
   and the field is updated and lit up green when the count changes.

   """
   is_drawn = 0
   
   def __init__(self, pvname,parent,channel_number,input_width):
      """

      Inputs:
         pvname:
            The name of the epics scaler record
         parent:
            The container to place the entry widget.
         channel_number:
         input_width:

      Example to monitor counter channel 2 on x12c:scaler1
            counter_channel = epicsCounterChannelLabel("x12c:scaler1",counter_output_frame,2,9)
            counter_channel.pack(side=LEFT)


      """
      self.entry_var = StringVar()
      self.entry_pv = pvCreate(pvname+".S"+str(channel_number))
      self.entry_dmov_pv = pvCreate(pvname+".CNT")
      self.entry_var.set(str(pvGet(self.entry_pv)))      
      self.entry = Label(parent,textvariable=self.entry_var,width=input_width)
      add_callback(self.entry_pv,self._entry_pv_movingCb,self.entry_var)
      add_callback(self.entry_dmov_pv,self._entry_pv_dmovCb,[])
      
      
   def _entry_pv_movingCb(self,epics_args, user_args):
#      print "in callback " + str(epics_args['pv_value'])
      if not (epicsCounterChannelLabel.is_drawn):
        return
      user_args[0].set(str(epics_args['pv_value']))


   def _entry_pv_dmovCb(self,epics_args, user_args):
#      print "in callback " + str(epics_args['pv_value'])
      if not (epicsCounterChannelLabel.is_drawn):
        return
      if (epics_args['pv_value'] == 0):
        self.entry.configure(background="#729fff")
      else:
        self.entry.configure(background="green")         


   def pack(self,side=LEFT,padx=0,pady=0): #pass the params in
      self.entry.pack(side=side,padx=padx,pady=pady)

   def getField():
      return self.entry_var.get()
   
   def setColor(color_string):
      self.entry.configure(background=color_string)

   
