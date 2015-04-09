"""
Creates a GUI window to control the presets for an Mca.

Author:         Mark Rivers
Created:        Sept. 18, 2002
Modifications:
"""
from Tkinter import *
import Pmw
 
class mcaControlPresets:
   def __init__(self, mca):
      """
      Creates a new GUI window for calibrating energy for an Mca object.
      The preset live time, real time, start channel, end channel and total
      counts can be controlled.

      Inputs:
         mca:
            An Mca instance for which the presets are to be controlled.
      """

      class widgets:
         pass
      self.mca = mca
      self.widgets = widgets()
      self.widgets.top = t = Pmw.Dialog(command=self.menu_ok_cancel,
                     buttons=('OK', 'Apply', 'Cancel'),
                     title='mcaControlPresets')
      top = t.component('dialogchildsite')

      self.presets = self.mca.get_presets()
      row = Frame(top); row.pack()
      self.widgets.real_time = t = Pmw.EntryField(row,
                               value=str(self.presets.real_time), labelpos=N,
                               label_text='Real time:',
                               entry_width=8, entry_justify=CENTER,
                               validate={'validator':'real'})
      t.pack(side=LEFT)
      self.widgets.live_time = t = Pmw.EntryField(row,
                               value=str(self.presets.live_time), labelpos=N,
                               label_text='Live time:',
                               entry_width=8, entry_justify=CENTER,
                               validate={'validator':'real'})
      t.pack(side=LEFT)
      self.widgets.total_counts = t = Pmw.EntryField(row,
                               value=str(self.presets.total_counts), labelpos=N,
                               label_text='Total counts:',
                               entry_width=8, entry_justify=CENTER,
                               validate={'validator':'real'})
      t.pack(side=LEFT)
      self.widgets.start_channel = t = Pmw.EntryField(row,
                               value=str(self.presets.start_channel), labelpos=N,
                               label_text='Start channel:',
                               entry_width=8, entry_justify=CENTER,
                               validate={'validator':'numeric'})
      t.pack(side=LEFT)
      self.widgets.end_channel = t = Pmw.EntryField(row,
                               value=str(self.presets.end_channel), labelpos=N,
                               label_text='End channel:',
                               entry_width=8, entry_justify=CENTER,
                               validate={'validator':'numeric'})
      t.pack(side=LEFT)

   def menu_ok_cancel(self, value):
      """ Private method """
      if (value == 'OK') or (value == 'Apply'):
         # Copy presets to Mca object
         self.presets.real_time = self.widgets.real_time.get()
         self.presets.live_time = self.widgets.live_time.get()
         self.presets.total_counts = self.widgets.total_counts.get()
         self.presets.start_chan = self.widgets.start_channel.get()
         self.presets.end_chan = self.widgets.end_channel.get()
         self.mca.set_presets(self.presets)
      if (value != 'Apply'): self.widgets.top.destroy()
      
