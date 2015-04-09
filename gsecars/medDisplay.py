"""
Simple Graphical User Interface to Multi-Element-Detector

Author:
   M Newville  Nov. 8, 2001

Modifications:
   Aug. 20, 2002, Mark Rivers
      - Converted from IDL to Python, Mark Rivers, 
   Sept. 24, 2002.  MLR
      - Fixed bug in opening a new mcaDisplay.
      - Change directory when saving a file so location becomes default
   Sept. 25, 2002  MLR
      - Added "Save Next" file menu and button
      - Changed default file extension for saving files from ".xrf" to nothing.
"""

from Tkinter import *
import tkFileDialog
import Pmw
import os
import mcaDisplay
import epicsPV
import myTkTop
import epicsMed
import localMedLayout
import Xrf

class medDisplay:
   def __init__(self, detector='13GE1:med:', element=1):
      class widgets:
         pass
      self.widgets = widgets()
      self.detector = detector
      self.element = element
      self.status = 'Ready'
      self.path = '.'
      self.file = 'test.xrf'
      self.next_file = self.file
      self.pvs = {}
      self.pvs['ElapsedReal'] = epicsPV.epicsPV(detector + 'ElapsedReal', wait=0)
      self.pvs['PresetReal']  = epicsPV.epicsPV(detector + 'PresetReal', wait=0)
      self.pvs['StartAll']    = epicsPV.epicsPV(detector + 'StartAll', wait=0)
      self.pvs['StopAll']     = epicsPV.epicsPV(detector + 'StopAll', wait=0)
      self.pvs['EraseAll']    = epicsPV.epicsPV(detector + 'EraseAll', wait=0)
      self.pvs['EraseStart']  = epicsPV.epicsPV(detector + 'EraseStart', wait=0)
      self.pvs['Acquiring']  = epicsPV.epicsPV(detector + 'Acquiring', wait=0)
      self.pvs['mca1.ERTM']   = epicsPV.epicsPV(detector + 'mca1.ERTM', wait=0)
      self.pvs['mca1.ERTM'].pend_io()
      
      self.preset_real = self.pvs['PresetReal'].getw()
      self.elapsed_real = self.pvs['ElapsedReal'].getw()
      self.update_time = .5
      
      # menus
      top = myTkTop.myTkTop()
      top.title('medDisplay')
      self.widgets.top = top
      frame = Frame(top, borderwidth=1, relief='raised')
      frame.pack(fill=X)
      mb = Pmw.MenuBar(frame)
      mb.pack(fill=X)
      mb.addmenu('File', '', side='left')
      self.widgets.file = mb.component('File-menu')
      mb.addmenuitem('File', 'command',
                      label='Save As ...',
                      command=self.menu_save)
      mb.addmenuitem('File', 'command',
                      label='Save Next = ' + self.next_file,
                      command=self.menu_save_next)
      mb.addmenuitem('File', 'command',
                      label='New MCA Display',
                      command=self.menu_new_display)
      mb.addmenuitem('File', 'command', 'Exit', label='Exit',
                      command=self.menu_exit)
      mb.addmenu('Help', '', side='right')
      self.widgets.help = mb.component('Help-menu')
      mb.addmenuitem('Help', 'command', label='Usage',
                      command=self.menu_help)
      mb.addmenuitem('Help', 'command', label='About',
                      command=self.menu_about)

      mb.addmenu('Options', '', side='left')
      self.widgets.options = mb.component('Options-menu')
      self.erase_on_start = IntVar()
      self.erase_on_start.set(1)
      mb.addmenuitem('Options', 'checkbutton', label='Erase on Start',
                     variable=self.erase_on_start)
 
      # main page
      main_frame = Frame(self.widgets.top); main_frame.pack()
      left_frame = Frame(main_frame, borderwidth=1, relief='solid')
      left_frame.pack(side=LEFT, anchor=N)
      self.widgets.left_frame = left_frame
      right_frame = Frame(main_frame, borderwidth=1, relief='solid')
      right_frame.pack(side=LEFT, anchor=N)
      self.widgets.right_frame = right_frame

      # Right Hand Side for control buttons
      row = Frame(right_frame)
      row.pack(side=TOP, anchor=W)
      t = Label(row, text = 'Preset Real Time (s):', width=22, 
                anchor=E); 
      t.pack(side=LEFT)
      self.widgets.preset_real = t = Pmw.EntryField(row, value=0,
                            entry_width=9, entry_justify=CENTER,
                            validate={'validator':'real'},
                            entry_background='light blue',
                            command=self.menu_preset_real)
      t.pack(side=LEFT)

      row = Frame(right_frame); 
      row.pack(side=TOP, anchor=W)
      t = Label(row, text = 'Elapsed Real Time (s):', width=22, 
                anchor=E); 
      t.pack(side=LEFT)
      self.widgets.elapsed_real = t = Label(row, text=str(self.elapsed_real),
                                            foreground='blue')
      t.pack(side=LEFT)
      self.widgets.preset_real.setentry(self.preset_real)

      row = Frame(right_frame); row.pack(side=TOP)
      t = Button(row, text='Start', command=self.menu_start); t.pack(side=LEFT)
      t = Button(row, text='Stop', command=self.menu_stop); t.pack(side=LEFT)
      t = Button(row, text='Erase', command=self.menu_erase); t.pack(side=LEFT)
      row = Frame(right_frame); row.pack(side=TOP)
      t = Button(row, text='Copy ROIS', command=self.menu_copy_rois)
      t.pack(side=LEFT)
      row = Frame(right_frame); row.pack(side=TOP, anchor=W)
      t = Button(row, text='Save As ...', command=self.menu_save); t.pack(side=LEFT)
      self.widgets.save_next = t = Button(row, text='Save Next = ' + self.next_file,
                                          command=self.menu_save_next)
      t.pack(side=LEFT)

      #
      row = Frame(right_frame); row.pack(side=TOP, anchor=W)
      t = Label(row, text = 'Viewing Element: '); t.pack(side=LEFT)
      self.widgets.element = t = Label(row, text=str(self.element), width=2,
                                       foreground='blue')
      t.pack(side=LEFT)

      row = Frame(right_frame); row.pack(side=TOP, anchor=W)
      t = Label(row, text = 'Status: '); t.pack(side=LEFT)
      self.widgets.status = t = Label(row, text='Initializing...', 
                                      foreground='blue'); t.pack(side=LEFT)
      t.pack(side=RIGHT)

      #
      # Left Hand Side shows Detector Element Layout
      #
      t = Label(left_frame, text='Detector Elements'); t.pack(side=TOP)
      width = 230
      height = 230
      area = Frame(left_frame, width=width, height=height); area.pack(side=TOP)
      self.widgets.area = area
      self.detector_positions = localMedLayout.localMedLayout()
      self.n_detectors = len(self.detector_positions)
      button_width=1
      button_height=1
      self.geom_state= 0
      self.widgets.det_buttons = []
      for d in range(self.n_detectors):
         t = Button(area, text=str(d+1), width=button_width,
                    height=button_height,
                    command = lambda s=self, d=d: s.menu_element(d+1))
         self.widgets.det_buttons.append(t)
      self.layout_detector()

      # Finally, load real versions of the mca_display and EPICS_MED objects
      # This will take some time, so we start with 'Initializing ...' in the
      # status message

      self.widgets.elapsed_real.configure(text=' ')
      self.mcaDisplay = mcaDisplay.mcaDisplay()
      self.mca = self.detector + 'mca' + str(self.element)
      self.mcaDisplay.open_detector(self.mca)
      self.med = epicsMed.epicsMed(self.detector, n_detectors=self.n_detectors)

      # when objects are really created, report 'Ready'.
      self.widgets.status.configure(text='Ready')

      # Start the timer routine
      self.widgets.top.after(int(self.update_time*1000), self.menu_timer)

   
   ############################################################
   def layout_detector(self):
      # Nicely positions the detector elements on the display
      wx = self.widgets.det_buttons[0].winfo_width()
      wy = self.widgets.det_buttons[0].winfo_height()
      # Note: wx will be 1 if the screen has not yet been fully drawn
      if (self.geom_state == 0) or ((self.geom_state == 1) and (wx > 1)):
         xoffset = 15; yoffset = 10;
         if (wx > 1): scale = max(wx+3, wy+3)
         else:        scale = 35  # Assume 35 pixels for button size
         # Find maximum value of x and y (in "button widths") from user layout
         xmax = 0; ymax = 0
         for p in self.detector_positions:
            xmax = max(p[0], xmax)
            ymax = max(p[1], ymax)
         # Compute desired window size
         width =  (xmax+1)*scale + 2*xoffset 
         height = (ymax+1)*scale + 2*yoffset 
         self.widgets.area.configure(width=width, height=height)
         for d in range(len(self.detector_positions)):
            x = (xoffset + self.detector_positions[d][0]*scale)
            y = (yoffset + self.detector_positions[d][1]*scale)
            self.widgets.det_buttons[d].place(x=x, y=height-y-scale)
         self.geom_state = self.geom_state + 1

   ############################################################
   def menu_exit(self):
      self.widgets.top.destroy()

   ############################################################
   def menu_help(self):
      pass

   ############################################################
   def menu_about(self):
      pass

   ############################################################
   def menu_element(self, element):
      self.element = element
      selement = str(element)
      dx = self.detector + 'mca' + selement
      self.widgets.status.configure(text='Loading Element ' + selement)
      self.widgets.elapsed_real.configure(text=' ')
      self.mcaDisplay.open_detector(dx)
      self.widgets.element.configure(text=selement)
      self.widgets.status.configure(text='Ready')
         
   ############################################################
   def menu_start(self):
       erase_on_start = self.erase_on_start.get()
       if (erase_on_start):
          self.pvs['EraseStart'].putw(1)
       else:
          self.pvs['StartAll'].putw(1)

   ############################################################
   def menu_stop(self):
        self.pvs['StopAll'].putw(1)

   ############################################################
   def menu_erase(self):
        self.pvs['EraseAll'].putw(1)

   ############################################################
   def menu_preset_real(self):
      time = float(self.widgets.preset_real.get())
      self.pvs['PresetReal'].putw(time)

   ############################################################
   def menu_copy_rois(self):
       s = 'Copying ROIs from ' + str(self.element).strip()
       self.widgets.status.configure(text=s)
       self.widgets.elapsed_real.configure(text=' ')
       self.med.copy_rois(self.element, energy=1)
       self.widgets.status.configure(text='Ready')

   ############################################################
   def menu_new_display(self):
       self.mcaDisplay = mcaDisplay.mcaDisplay()
       mca  = self.detector + 'mca' + str(self.element).strip()
       self.mcaDisplay.open_detector(mca)

   ############################################################
   def menu_save_next(self):
      self.save_file(self.next_file)

   ############################################################
   def menu_save(self):
      tfile = self.file
      file = tkFileDialog.asksaveasfilename(parent=self.widgets.top,
                                title='Output file',
                                initialdir=self.path,
                                filetypes=[('All files','*')])
      if (file == ''): return
      self.path = os.path.dirname(file)
      os.chdir(self.path)
      self.file = os.path.basename(file)
      self.save_file(self.file)

   ############################################################
   def save_file(self, file):
      self.widgets.status.configure(text='Saving Spectra...')
      self.widgets.elapsed_real.configure(text=' ')
      self.med.write_file(file)
      self.widgets.status.configure(text='Ready')
      self.next_file = Xrf.increment_filename(file)
      self.widgets.file.entryconfigure('Save Next*', label='Save Next = ' +
                                                    self.next_file)
      self.widgets.save_next.configure(text='Save Next = ' + self.next_file)

   ############################################################
   def menu_timer(self):
      if (self.geom_state != 2):
         self.layout_detector()
      self.pvs['PresetReal'].array_get()
      self.pvs['ElapsedReal'].array_get()
      self.pvs['mca1.ERTM'].array_get()
      self.pvs['Acquiring'].array_get()
      self.pvs['Acquiring'].pend_io()
      pr = self.pvs['PresetReal'].getValue()
      xt1 = self.pvs['ElapsedReal'].getValue()
      xt2 = self.pvs['mca1.ERTM'].getValue()
      status = self.pvs['Acquiring'].getValue()
      # presetreal changed somewhere else:
      if (abs(pr-self.preset_real) > 1.e-2):
         self.preset_real = pr
         self.widgets.preset_real.setentry(pr)
      stime  = ('%7.2f' % xt2)
      stat = 'Ready'
      if (status > 0):
         stat = 'Acquiring'
      self.widgets.status.configure(text=stat)
      self.widgets.elapsed_real.configure(text=stime)
      self.widgets.top.after(int(self.update_time*1000), self.menu_timer)
