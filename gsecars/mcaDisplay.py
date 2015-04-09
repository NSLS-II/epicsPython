"""
This program provides a multichannel analyzer (MCA) display in Python using
Tkinter widgets and Blt.

Author:        Mark Rivers
Created:       Sept. 20, 2002.  Based on my earlier IDL program
Modifications:
   Sept. 24, 2002. MLR
      - Change default directory every time a file is read or written,
        and when settings file is restored.
      - Attempt to restore settings when display is created.
      - Save settings each time program is exited with "File/Exit"
      - Use MCA_SETTINGS environment variable, and mca.settings file
        in current directory, in that order as location of settings.
      - Remember MCA detector name and use it as default
   Sept. 26, 2002 MLR
      - Fixed bugs in the "Add Peaks" and "Add ROIs" functions of JCPDS.
   Oct. 15, 2002 MLR
      - Fixed bugs in update_display, force hmin and hmax to be integers
   Oct. 24, 2002 MLR
      - Fixed bugs related to the "preferences" menu, i.e. autosave,
        autorestart, etc.
"""
import os
import math
import cPickle
import Numeric
from Tkinter import *
import tkFileDialog
import tkMessageBox
import tkSimpleDialog
import Pmw
import Mca
import Med
import hardwareMca
import Xrf
import CARSMath
import mcaControlPresets
import mcaCalibrateEnergy
import mcaCalibrate2theta
import mcaPeakFit
import jcpds
import BltPlot
import myTkTop


############################################################
class mcaDisplay_options:
   def __init__(self):
      self.autosave       = 0 # Automatically save file when acq. completes
      self.autorestart    = 0 # Automatically restart acq. when acq. completes
      self.warn_overwrite = 1 # Warn user of attempt to overwrite existing file
      self.warn_erase     = 0 # Warn user of attempt to erase without prior save
      self.save_done      = 0 # Flag to keep track of save done before erase
      self.inform_save    = 0 # Inform user via popup of successful file save
      self.download_rois  = 0 # Download ROIs to record when reading file
      self.download_cal   = 0 # Download calibration to record when reading file
      self.download_data  = 0 # Download MCA data to record when reading file
      self.debug          = 0 # Debug flag - not presently used

############################################################
class mcaDisplay_file:
   def __init__(self):
      self.filepath      = './'
      self.filename      = ''          # name of saved or read
      self.next_filename = 'test.dat'  # name of next file to save
      self.settings_file = 'mca.settings'
      self.jcpds_path    = os.getenv('JCPDS_PATH')
      self.jcpds         = jcpds.jcpds()
      self.mca_name      = ''

############################################################
class mcaDisplay_display:
   def __init__(self):
      self.update_time = .5
      self.current_time = 0.
      self.current_counts = 0
      self.current_bgd = 0
      self.current_acqg = 0
      self.prev_time   = 0.
      self.prev_counts = 0
      self.prev_bgd    = 0
      self.prev_acqg   = 0
      self.new_stats   = 0
      self.horiz_mode  = 0
      self.hmin        = 0
      self.hmax        = 2048
      self.vlog        = 1
      self.lmarker     = 100
      self.rmarker     = 200
      self.cursor      = 300
      self.klm         = 26 # Start with Fe
      self.current_roi = 0
      self.pressure    = 0.
      self.temperature = 0.
      self.psym        = 0
      self.k_lines = ['Ka1', 'Ka2', 'Kb1', 'Kb2']
      self.l_lines = ['La1', 'Lb1', 'Lb2', 'Lg1', 'Lg2', 'Lg3', 'Lg4', 'Ll']


############################################################
class mcaDisplay_colors:
   def __init__(self):
      self.background           = 'black'
      self.markers              = 'red'
      self.highlight_markers    = 'green'
      self.klm                  = 'green'
      self.highlight_klm        = 'light blue'
      self.jcpds                = 'green'
      self.highlight_jcpds      = 'light blue'
      self.foreground_spectrum  = 'yellow'
      self.background_spectrum  = 'green'
      self.roi                  = 'blue'
      self.labels               = 'blue'
      self.entry_foreground     = 'black'
      self.entry_background     = 'lightblue'
      self.label_foreground     = 'blue'
      self.label_background     = 'white'

############################################################
class mcaDisplaySettings:
   def __init__(self):
      pass

############################################################
class mcaDisplay_fonts:
   def __init__(self):
      self.label  = ('helvetica', -12)
      self.text   = ('helvetica', -12)
      self.button = ('helvetica', -12, 'bold')
      self.help   = ('courier', 10)

############################################################
class mcaDisplay_mca:
   def __init__(self):
      self.mca          = Mca.Mca()
      self.name         = ''
      self.valid        = 0
      self.is_detector  = 0
      self.nchans       = 0
      self.data         = []
      self.elapsed      = Mca.McaElapsed()
      self.roi          = []


############################################################
class mcaDisplay:
   """
   This program provides a multichannel analyzer (MCA) display in Python using
   Tk widgets. It emulates the look and feel of the Canberra MCA package.

   This program requires that the following environment variables be set:
       MCA_SETTINGS      - File name to save/restore for MCA program
                           settings, such as size, colors, line style,
                           etc.  If environment variable not set then the
                           file mca.settings in the current default
                           directory is used
       MCA_HELP_COMMAND  - System command to display MCA help text
       XRF_PEAK_LIBRARY  - File containing XRF line data.
                           Used by lookup_xrf_line.pro

   This program requires at least version 3.0 of the MCA record, which
   supports fields for ROI labels and calibration parameters.
   """

   def __init__(self, file=None, detector=None):

      self.options    = mcaDisplay_options()
      self.file       = mcaDisplay_file()
      self.display    = mcaDisplay_display()
      self.colors     = mcaDisplay_colors()
      self.fonts      = mcaDisplay_fonts()
      self.print_settings   = None
      self.foreground = mcaDisplay_mca()
      self.foreground.name = ' '
      self.foreground.valid = 1
      self.MAX_ROIS = 32
      self.MAX_JCPDS = 32
      self.foreground.roi = self.foreground.mca.get_rois()
      self.foreground.nrois = len(self.foreground.roi)
      self.foreground.elapsed = self.foreground.mca.get_elapsed()
      self.foreground.data = self.foreground.mca.get_data()
      self.foreground.nchans = len(self.foreground.data)
      self.background = mcaDisplay_mca()
      self.peak_fit = Mca.McaFit()
      class widgets:
         pass
      self.widgets    = widgets()
      self.create_display()
      self.update_spectrum(rescale=1)
      settings_file = os.getenv('MCA_SETTINGS')
      if (settings_file != None): self.file.settings_file = settings_file
      self.restore_settings(self.file.settings_file)

#     self.about()
      self.new_inputs()
      if (file != None): self.open_file(file)
      if (detector != None): self.open_detector(detector)
      self.after_id=self.widgets.top.after(
                            int(self.display.update_time*1000), self.timer)

   #############################################################
   def __del__(self):
      pass

   #############################################################
   def create_display(self):
      top = myTkTop.myTkTop()
      top.title('mcaDisplay')
      self.widgets.top = top
      frame = Frame(top, borderwidth=1, relief='raised')
      frame.pack(fill=X)
      mb = Pmw.MenuBar(frame)
      mb.pack(fill=X)
      mb.addmenu('File', '', side='left')
      self.widgets.file = mb.component('File-menu')
      mb.addcascademenu('File', 'Foreground')
      mb.addmenuitem('Foreground', 'command', label='Open detector...',
                                    command=self.menu_foreground_open_det)
      mb.addmenuitem('Foreground', 'command', label='Read file...',
                                    command=self.menu_foreground_open_file)
      mb.addcascademenu('File', 'Background')
      mb.addmenuitem('Background', 'command', label='Open detector...',
                                    command=self.menu_background_open_det)
      mb.addmenuitem('Background', 'command', label='Read file...',
                                    command=self.menu_background_open_file)
      mb.addmenuitem('Background', 'command',
                      label='Close', command=self.menu_background_close)
      mb.addmenuitem('File', 'command',
                      label='Swap Foreground<.Background',
                      command=self.menu_swap)
      mb.addmenuitem('File', 'command',
                      label='Save Next = ' + self.file.next_filename,
                      command=self.menu_save_next)
      mb.addmenuitem('File', 'command',
                      label='Save As...', command=self.menu_save_as)
      mb.addmenuitem('File', 'command', label='Print setup...',
                      command=self.menu_print_setup)
      mb.addmenuitem('File', 'command', label='Print...',
                      command=self.menu_print)
      mb.addmenuitem('File', 'command', label='Preferences...',
                      command=self.menu_preferences)
      mb.addmenuitem('File', 'command', label='Save settings...',
                      command=self.menu_save_settings)
      mb.addmenuitem('File', 'command', label='Restore settings...',
                      command=self.menu_restore_settings)
      mb.addmenuitem('File', 'command', 'Exit', label='Exit',
                      command=self.menu_exit)
      mb.addmenu('Help', '', side='right')
      self.widgets.help = mb.component('Help-menu')
      mb.addmenuitem('Help', 'command', label='Usage',
                      command=self.help)
      mb.addmenuitem('Help', 'command', label='About',
                      command=self.about)

      mb.addmenu('Control', '', side='left')
      self.widgets.control = mb.component('Control-menu')
      mb.addmenuitem('Control', 'command', label='Presets...',
                      command=self.menu_presets)
      mb.addmenuitem('Control', 'command', label='Calibrate energy...',
                      command=self.menu_calibrate_energy)
      mb.addmenuitem('Control', 'command', label='Calibrate 2-theta...',
                      command=self.menu_calibrate_two_theta)

      mb.addmenu('Display', '', side='left')
      self.widgets.display = mb.component('Display-menu')
      mb.addcascademenu('Display', 'Preferences')
      mb.addmenuitem('Preferences', 'command', label='Update time...',
         command=self.update_time)
      mb.addmenuitem('Preferences', 'command', label='Plot...',
         command=lambda s=self: BltPlot.BltConfigureGraph(s.widgets.plot))
      mb.addmenuitem('Preferences', 'command', label='Foreground spectrum...',
         command=lambda s=self: BltPlot.BltConfigureElement(s.widgets.plot, 'foreground'))
      mb.addmenuitem('Preferences', 'command', label='Background spectrum...',
         command=lambda s=self: BltPlot.BltConfigureElement(s.widgets.plot, 'background'))
      mb.addmenuitem('Preferences', 'command', label='ROIs...',
         command=lambda s=self: BltPlot.BltConfigureElement(s.widgets.plot, 'ROI*'))
      mb.addmenuitem('Preferences', 'command', label='Markers and cursor...',
         command=lambda s=self: BltPlot.BltConfigureMarker(
                     s.widgets.plot, 'Markers*', command=s.marker_callback))
      mb.addmenuitem('Preferences', 'command', label='KLM lines...',
         command=lambda s=self: BltPlot.BltConfigureMarker(
                     s.widgets.plot, 'KLM*', command=s.klm_marker_callback))
      mb.addmenuitem('Preferences', 'command', label='JCPDS lines...',
         command=lambda s=self: BltPlot.BltConfigureMarker(
                                s.widgets.plot, 'JCPDS*', command=s.JCPDS_marker_callback))
      mb.addmenuitem('Preferences', 'command', label='X axis...',
         command=lambda s=self: BltPlot.BltConfigureAxis(
                     s.widgets.plot, 'x', command=s.xaxis_callback))
      mb.addmenuitem('Preferences', 'command', label='Y axis...',
         command=lambda s=self: BltPlot.BltConfigureAxis(
                     s.widgets.plot, 'y', command=s.yaxis_callback))
      mb.addmenuitem('Preferences', 'command', label='Grid...',
         command=lambda s=self: BltPlot.BltConfigureGrid(s.widgets.plot))
      mb.addmenuitem('Preferences', 'command', label='Legend',
         command=lambda s=self: BltPlot.BltConfigureLegend(s.widgets.plot))
      mb.addmenuitem('Display', 'command', label='JCPDS...',
                      command=self.menu_jcpds)
      mb.addmenuitem('Display', 'command', label='Fit peaks...',
                      command=self.menu_fit_peaks)

      control_column = Frame(top)
      control_column.pack(side=LEFT, anchor=N)

      data_column = Frame(top, borderwidth=1, relief='raised')
      data_column.pack(side=LEFT, expand=YES, fill=BOTH)

      # Define padding
      fypad = 2  # pady for frames

      acquire = Frame(control_column, borderwidth=1, relief='solid')
      acquire.pack(fill=X, pady=fypad)
      t = Label(acquire, text='Acquisition'); t.pack()
      row = Frame(acquire); row.pack()
      self.widgets.start = t = Button(row, text="Start",
                                 command=self.menu_start)
      t.pack(side=LEFT)
      self.widgets.stop = t = Button(row, text="Stop",
                                 command=self.menu_stop)
      t.pack(side=LEFT)
      self.widgets.erase = t = Button(acquire, text="Erase",
                                 command=self.menu_erase)
      t.pack()

      status = Frame(control_column, borderwidth=1, relief='solid')
      status.pack(fill=X, pady=fypad)
      t = Label(status, text='Elapsed Time'); t.pack()
      row = Frame(status); row.pack()
      t = Label(row, text='Live:', width=5); t.pack(side=LEFT)
      self.widgets.elive = t = Label(row, width=8, relief='groove',
                                    text='0.00',
                                    foreground=self.colors.label_foreground,
                                    background=self.colors.label_background)
      t.pack(side=LEFT)
      row = Frame(status); row.pack()
      t = Label(row, text='Real:', width=5); t.pack(side=LEFT)
      self.widgets.ereal = t = Label(row, width=8, relief='groove',
                                text='0.00',
                                foreground=self.colors.label_foreground,
                                background=self.colors.label_background)
      t.pack(side=LEFT)

      roi = Frame(control_column, borderwidth=1, relief='solid')
      roi.pack(anchor=N, fill=X, pady=fypad)
      t = Label(roi, text='ROIs'); t.pack()
      row = Frame(roi); row.pack()
      self.widgets.add_roi = t = Button(row, text='Add',
                                        command=self.menu_add_roi);
      t.pack(side=LEFT)
      self.widgets.delete_roi = t = Button(row, text='Delete',
                                        command=self.menu_delete_roi)
      t.pack(side=LEFT)
      row = Frame(roi); row.pack()
      self.widgets.clear_roi = t = Button(row, text='Clear All',
                                        command=self.menu_clear_roi)
      t.pack(side=LEFT)
      row = Frame(roi); row.pack()
      self.widgets.prev_roi = t = Button(row, text='<', padx='2m',
                                        command=self.menu_prev_roi)
      t.pack(side=LEFT)
      self.widgets.label_roi = t = Pmw.EntryField(row, value=' ',
                            entry_width=10, entry_justify=CENTER,
                            entry_background=self.colors.entry_background,
                            entry_foreground=self.colors.entry_foreground,
                            command=self.menu_label_roi)
      t.pack(side=LEFT)
      self.widgets.next_roi = t = Button(row, text='>', padx='2m',
                                        command=self.menu_next_roi)
      t.pack(side=LEFT)

      klm = Frame(control_column, borderwidth=1, relief='solid')
      klm.pack(anchor=N, fill=X, pady=fypad)
      t = Label(klm, text='KLM markers')
      t.pack()
      row = Frame(klm); row.pack()
      self.widgets.klm_down = t = Button(row, text= '<',  padx='2m',
                                        command=self.menu_klm_down)
      t.pack(side=LEFT)
      self.widgets.klm_element = t = Pmw.ComboBox(row, history=0,
                            scrolledlist_items=Xrf.atomic_symbols,
                            entry_width=5, listbox_width=5,
                            selectioncommand=self.menu_klm_element)
      t.selectitem(self.display.klm-1)
      t.pack(side=LEFT, fill=X, expand=1)
      t.pack(side=LEFT, fill=X, expand=1)
      self.widgets.klm_up = t = Button(row, text= '>', padx='2m',
                                        command=self.menu_klm_up)
      t.pack(side=LEFT)
      row = Frame(klm); row.pack()
      self.widgets.klm_line = t = Pmw.OptionMenu(row, labelpos=W,
                                        label_text='Series:',
                                        items=('None','K','L','K & L'),
                                        initialitem = 0,
                                        command=self.menu_klm_line)
      t.pack(side=LEFT)

      display = Frame(control_column, borderwidth=1, relief='solid')
      display.pack(anchor=N, fill=X, pady=fypad)
      t = Label(display, text='Display'); t.pack()
      row = Frame(display); row.pack()
      self.widgets.zoom_down = t = Button(row, text= '<', padx='2m',
                                    command=self.menu_zoom_down)
      t.pack(side=LEFT)
      t = Label(row, text='Zoom', borderwidth=1, relief='solid', width=8)
      t.pack(side=LEFT)
      self.widgets.zoom_up = t = Button(row, text= '>', padx='2m',
                                    command=self.menu_zoom_up)
      t.pack(side=LEFT)
      row = Frame(display); row.pack()
      self.widgets.shift_down = t = Button(row, text= '<', padx='2m',
                                    command=self.menu_shift_down)
      t.pack(side=LEFT)
      t = Label(row, text='Shift', borderwidth=1, relief='solid', width=8)
      t.pack(side=LEFT)
      self.widgets.shift_up = t = Button(row, text= '>', padx='2m',
                                    command=self.menu_shift_up)
      t.pack(side=LEFT)
      self.widgets.lin_log = t = Pmw.OptionMenu(display, labelpos=N,
                                        label_text='Vertical Scale',
                                        items=('Linear','Logarithmic'),
                                        initialitem = self.display.vlog,
                                        command=self.menu_lin_log)
      t.pack()

      # There is a bug (???) in Pmw.Blt, it won't create a new graph if
      # Tkinter.Tk() has been called since the last time a graph was created.
      # Work around the problem for now by reloading Pmw.Blt.
      #reload(Pmw.Blt)
      self.widgets.plot = t = Pmw.Blt.Graph(data_column)
      t.configure(plotbackground=self.colors.background)
      t.axis_configure(('x','y'), hide=1)
      t.line_create('foreground', symbol="", pixels=2,
                    color=self.colors.foreground_spectrum)
      t.line_create('background', symbol="", pixels=2,
                    color=self.colors.background_spectrum)
      for i in range(self.MAX_ROIS):
         roi = 'ROI'+str(i)
         t.line_create(roi, symbol="", label="", pixels=2, color=self.colors.roi)
      t.legend_configure(hide=1)
      self.markers = {'left': 'MarkersLeft',
                      'right': 'MarkersRight',
                      'cursor': 'MarkersCursor'}
      for marker in self.markers.keys():
         t.marker_create('line', name=self.markers[marker], linewidth=2)
         for event in ('<Enter>', '<Leave>',
                       '<ButtonPress>', '<ButtonRelease>'):
            t.marker_bind(self.markers[marker], event,
                         lambda e, s=self, m=marker: s.marker_mouse(e, m))
      for line in (self.display.k_lines + self.display.l_lines):
         name = 'KLM'+line
         t.marker_create('line', name=name, hide=1, linewidth=2)
         for event in ('<Enter>', '<Leave>'):
            t.marker_bind(name, event,
                         lambda e, s=self, m=name: s.klm_mouse(e, m))
      t.marker_create('text', name='klm_text', hide=1, coords=(0,0), text='')
      for i in range(self.MAX_JCPDS):
         name = 'JCPDS'+str(i)
         t.marker_create('line', name=name,
                         coords=(0, '-Inf', 100, 'Inf'), hide=1, linewidth=2)
         for event in ('<Enter>', '<Leave>'):
            t.marker_bind(name, event,
                         lambda e, s=self, m=name: s.jcpds_mouse(e, m))
      t.marker_create('text', name='jcpds_text', hide=1, coords=(0,0), text='')

      t.pack(side=TOP, anchor=N, expand=YES, fill=BOTH)
      self.set_marker_colors()

      bottom_row = Frame(data_column)
      bottom_row.pack(anchor=W, pady=3)
      row = Frame(bottom_row, relief='solid', borderwidth=1);
      row.pack(side=LEFT)

      # The widths for entry and label fields
      width=11
      t = Label(row, text=' ')
      t.grid(row=0, column=0)
      self.widgets.horiz_mode = t = Pmw.OptionMenu(row, menubutton_width=8,
                                       items=('Channel', 'Energy', 'd-spacing'),
                                       command=self.menu_horiz_mode)
      t.grid(row=1, column=0)
      t = Label(row, text='Counts')
      t.grid(row=2, column=0)

      t = Label(row, text='Cursor')
      t.grid(row=0, column=1)
      self.widgets.cur_pos = t = Pmw.EntryField(row, value=0,
                            entry_width=width, entry_justify=CENTER,
                            entry_background=self.colors.entry_background,
                            entry_foreground=self.colors.entry_foreground,
                            validate={'validator':'real'},
                            command=self.menu_cur_pos)
      t.grid(row=1, column=1)
      self.widgets.cur_counts = t = Label(row, text='0', width=width,
                                    background=self.colors.label_background,
                                    foreground=self.colors.label_foreground)
      t.grid(row=2, column=1, padx=3)

      t = Label(row, text='Left marker')
      t.grid(row=0, column=2)
      self.widgets.lm_pos = t = Pmw.EntryField(row, value=0,
                            entry_width=width, entry_justify=CENTER,
                            entry_background=self.colors.entry_background,
                            entry_foreground=self.colors.entry_foreground,
                            validate={'validator':'real'},
                            command=self.menu_lm_pos)
      t.grid(row=1, column=2)
      self.widgets.lm_counts = t = Label(row, text='0', width=width,
                                    background=self.colors.label_background,
                                    foreground=self.colors.label_foreground)
      t.grid(row=2, column=2, padx=3)

      t = Label(row, text='Right marker')
      t.grid(row=0, column=3)
      self.widgets.rm_pos = t = Pmw.EntryField(row, value=0,
                            entry_width=width, entry_justify=CENTER,
                            entry_background=self.colors.entry_background,
                            entry_foreground=self.colors.entry_foreground,
                            validate={'validator':'real'},
                            command=self.menu_rm_pos)
      t.grid(row=1, column=3)
      self.widgets.rm_counts = t = Label(row, text='0', width=width,
                                    background=self.colors.label_background,
                                    foreground=self.colors.label_foreground)
      t.grid(row=2, column=3, padx=3)

      t = Label(row, text='Centroid')
      t.grid(row=0, column=4)
      self.widgets.center_pos = t = Label(row, text='0', width=width,
                                    background=self.colors.label_background,
                                    foreground=self.colors.label_foreground)
      t.grid(row=1, column=4, padx=3)

      t = Label(row, text='FWHM')
      t.grid(row=0, column=5)
      self.widgets.fwhm_pos = t = Label(row, text='0', width=width,
                                    background=self.colors.label_background,
                                    foreground=self.colors.label_foreground)
      t.grid(row=1, column=5, padx=3)

      t = Frame(row, width=2, height=1, borderwidth=1, relief='solid');
      t.grid(row=0, column=6, rowspan=3, stick='NS')
      t = Label(row, text=' ')
      t.grid(row=0, column=7)
      t = Label(row, text='Total')
      t.grid(row=1, column=7)
      t = Label(row, text='Net')
      t.grid(row=2, column=7)
      t = Label(row, text='Counts')
      t.grid(row=0, column=8)
      self.widgets.total_counts = t = Label(row, text='0', width=width,
                                    background=self.colors.label_background,
                                    foreground=self.colors.label_foreground)
      t.grid(row=1, column=8)
      self.widgets.net_counts = t = Label(row, text='0', width=width,
                                    background=self.colors.label_background,
                                    foreground=self.colors.label_foreground)
      t.grid(row=2, column=8, padx=3)
      t = Label(row, text='Counts/sec')
      t.grid(row=0, column=9)
      self.widgets.total_cps = t = Label(row, text='0', width=width,
                                    background=self.colors.label_background,
                                    foreground=self.colors.label_foreground)
      t.grid(row=1, column=9)
      self.widgets.net_cps = t = Label(row, text='0', width=width,
                                    background=self.colors.label_background,
                                    foreground=self.colors.label_foreground)
      t.grid(row=2, column=9, padx=3)



   ############################################################
   def marker_callback(self, marker):
      # This is called from BltConfigureMarker() whenever the marker/cursor
      # configuration has changed.
      self.colors.markers = self.widgets.plot.marker_cget(
                                           self.markers['left'], 'outline')
      self.colors.highlight_markers = self.widgets.plot.marker_cget(
                                           self.markers['left'], 'fill')

   ############################################################
   def klm_marker_callback(self, marker):
      # This is called from BltConfigureMarker() whenever the KLM marker
      # configuration has changed.
      self.colors.klm = self.widgets.plot.marker_cget('KLMKa1', 'outline')
      self.colors.highlight_klm = self.widgets.plot.marker_cget('KLMKa1', 'fill')

   ############################################################
   def JCPDS_marker_callback(self, marker):
      # This is called from BltConfigureMarker() whenever the JCPDS marker
      # configuration has changed.
      self.colors.jcpds = self.widgets.plot.marker_cget('JCPDS0', 'outline')
      self.colors.highlight_jcpds = self.widgets.plot.marker_cget('JCPDS0', 'fill')

   ############################################################
   def yaxis_callback(self, axis):
      # This is called from BltConfigureAxis() whenever the Y axis
      # configuration has changed.
      self.display.vlog = int(self.widgets.plot.yaxis_cget('logscale'))
      self.widgets.lin_log.invoke(self.display.vlog)

   ############################################################
   def xaxis_callback(self, axis):
      # This is called from BltConfigureAxis() whenever the X axis
      # configuration has changed.
      self.display.hmin = int(float(self.widgets.plot.xaxis_cget('min')))
      self.display.hmax = int(float(self.widgets.plot.xaxis_cget('max')))
      self.update_spectrum(rescale=1)

   ############################################################
   def menu_foreground_open_det(self):
      self.open_det(background=0)

   ############################################################
   def menu_foreground_open_file(self):
      file = tkFileDialog.askopenfilename(parent=self.widgets.top,
                                title='Input file',
                                filetypes=[('All files','*')])
      if (file == ''): return
      path = os.path.dirname(file)
      file = os.path.basename(file)
      self.file.filepath = path
      os.chdir(path)
      self.file.filename = file
      self.open_file(path + os.path.os.sep + file)

   ############################################################
   def menu_background_open_det(self):
      self.open_det(background=1)

   ############################################################
   def menu_background_open_file(self):
      file = tkFileDialog.askopenfilename(parent=self.widgets.top,
                                title='Input file',
                                filetypes=[('All files','*')])
      if (file == ''): return
      path = os.path.dirname(file)
      file = os.path.basename(file)
      self.file.filepath = path
      os.chdir(path)
      self.file.filename = file
      self.background.name = file
      self.open_file(path + os.path.os.sep + file, background=1)

   ############################################################
   def menu_background_close(self):
      #obj_destroy, self.background.mca
      self.background.valid = 0
      self.background.is_detector = 0
      self.update_spectrum(rescale=1)
      self.new_inputs()

   ############################################################
   def menu_swap(self):
       temp = self.foreground
       self.foreground = self.background
       self.background = temp
       self.update_spectrum(rescale=1)
       self.show_stats()
       self.new_inputs()

   ############################################################
   def menu_save_next(self):
      self.save_file(self.file.next_filename)

   ############################################################
   def menu_save_as(self):
      file = tkFileDialog.asksaveasfilename(parent=self.widgets.top,
                                title='Output file',
                                filetypes=[('All files','*')])
      if (file == ''): return
      path = os.path.dirname(file)
      file = os.path.basename(file)
      self.file.filepath = path
      os.chdir(path)
      self.file.filename = file
      self.save_file(file)

   ############################################################
   def menu_print_setup(self):
      self.create_print_plot(exit_callback=self.print_setup_callback)

   ############################################################
   def print_setup_callback(self, graph):
      self.print_settings = BltPlot.BltGetSettings(graph, data=0, markers=0)

   ############################################################
   def create_print_plot(self, exit_callback=None):
      b = BltPlot.BltPlot(exit_callback=exit_callback)
      graph = b.graph
      xdata = range(self.foreground.nchans)
      mode = self.widgets.horiz_mode.getcurselection()
      if (mode == 'Energy'):
         xdata = self.foreground.mca.channel_to_energy(xdata)
      elif (mode == 'd-spacing'):
         xdata = self.foreground.mca.channel_to_d(xdata)
      display = ['foreground']
      b.plot(tuple(xdata),
             tuple(self.foreground.data), label='foreground')
      graph = b.graph
      if (self.background.valid):
         # There is a bug in Blt log plot if all channels are 0, sets
         # small minimum.  Work around by setting channel 0 to 1 for now
         self.background.data[0]=1
         b.oplot(tuple(xdata),
                 tuple(self.background.data), label='background')
         display.append('background')
      for i in range(self.foreground.nrois):
         roi = 'ROI'+str(i)
         left = self.foreground.roi[i].left
         right = self.foreground.roi[i].right+1
         label = self.foreground.roi[i].label.strip()
         if (label == ''): label=roi
         b.oplot(tuple(xdata[left:right]),
                 tuple(self.foreground.data[left:right]), label=label)
         display.append(label)
      # Create a text marker with calibration info, etc.
      cal = self.foreground.mca.get_calibration()
      text = (
         'File: ' + self.foreground.name + '\n' +
         'Date: ' + self.foreground.elapsed.start_time + '\n' +
         'Live time: ' + ('%.2f' % self.foreground.elapsed.live_time) + '\n' +
         'Real time: ' + ('%.2f' % self.foreground.elapsed.real_time) + '\n' +
         'Calibration offset: ' + ('%.5f' % cal.offset) + '\n' +
         'Calibration slope: '  + ('%.5f' % cal.slope) + '\n' +
         'Calibration quad: '   + ('%.5f' % cal.quad) + '\n' +
         '2-theta: '            + ('%.4f' % cal.two_theta))
      b.graph.marker_create('text', name='file_info', coords=('-Inf', 'Inf'),
                            text=text, anchor=NW, justify=LEFT)
      # Set the display list order
      b.graph.element_show(display)
      # Rebuild menus so marker can be configured
      b.rebuild_menus()
      if (self.print_settings != None):
         BltPlot.BltLoadSettings(graph, self.print_settings)
      return b

   ############################################################
   def menu_print(self):
      b = self.create_print_plot()
      BltPlot.BltPrint(b.graph)
      b.widgets.top.destroy()

   ############################################################
   def menu_save_settings(self):
      file = tkFileDialog.asksaveasfilename(parent=self.widgets.top,
                                title='Settings file',
                                filetypes=[('Save files','*.sav'),
                                           ('All files','*')])
      if (file == ''): return
      self.widgets.plot.configure(cursor='watch')
      self.widgets.plot.update()
      self.save_settings(file)
      self.widgets.plot.configure(cursor='')

   ############################################################
   def menu_restore_settings(self):
      file = tkFileDialog.askopenfilename(parent=self.widgets.top,
                                title='Settings file',
                                filetypes=[('Save files','*.sav'),
                                           ('All files','*')])
      if (file == ''): return
      self.widgets.plot.configure(cursor='watch')
      self.widgets.plot.update()
      self.restore_settings(file)
      self.widgets.plot.configure(cursor='')

   ############################################################
   def menu_preferences(self):
      t = mcaDisplayFilePreferences(self)

   ############################################################
   def menu_presets(self):
      mcaControlPresets.mcaControlPresets(self.foreground.mca)

   ############################################################
   def menu_calibrate_energy(self):
      mcaCalibrateEnergy.mcaCalibrateEnergy(self.foreground.mca,
                         command=self.calibrate_energy_done)

   ############################################################
   def calibrate_energy_done(self, status):
      # This is called when the energy calibration window is closed.  status=1 if
      # OK was pressed, status=0 otherwise
      if (status):
         self.update_spectrum(rescale=1)
         self.show_stats()

   ############################################################
   def menu_calibrate_two_theta(self):
      mcaCalibrate2theta.mcaCalibrate2theta(self.foreground.mca)

   ############################################################
   def menu_jcpds(self):
      t = mcaDisplayJcpds(self)

   ############################################################
   def menu_fit_peaks(self):
      mcaPeakFit.mcaPeakFit(self.foreground.mca,
                                    fit=self.peak_fit,
                                    command=self.fit_peaks_return)

   ############################################################
   def menu_start(self):
      self.foreground.mca.start()

   ############################################################
   def menu_stop(self):
      self.foreground.mca.stop()

   ############################################################
   def menu_erase(self):
      if ((not self.options.save_done) and (self.options.warn_erase)):
         reply = tkMessageBox.askyesno(title='mcaDisplay warning',
               message='Warning - data have not been saved.  Erase anyway? ')
         if (not reply): return
      self.foreground.mca.erase()
      self.options.save_done = 1
      self.update_spectrum()

   ############################################################
   def menu_add_roi(self):
      # widget_control, /hourglass
      label = self.widgets.label_roi.get()
      roi = Mca.McaROI()
      roi.left = self.display.lmarker
      roi.right = self.display.rmarker
      roi.label = label.strip()
      roi.use = 1
      if (self.foreground.nrois < self.MAX_ROIS):
         self.foreground.mca.add_roi(roi)
      else:
         tkMessageBox.showerror(title='mcaDisplay Error', message = 'Too many ROIs')
         return
      self.foreground.roi = self.foreground.mca.get_rois()
      self.foreground.nrois = len(self.foreground.roi)
      index = self.foreground.mca.find_roi(roi.left, roi.right)
      if (index >= 0): self.display.current_roi = index
      self.update_spectrum(rescale=1)

   ############################################################
   def menu_delete_roi(self):
      # widget_control, /hourglass
      roi = self.foreground.mca.find_roi(self.display.lmarker,
                                            self.display.rmarker)
      self.foreground.mca.delete_roi(roi)
      self.foreground.roi = self.foreground.mca.get_rois()
      self.foreground.nrois = len(self.foreground.roi)
      self.display.current_roi = max((self.display.current_roi-1),0)
      self.update_spectrum(rescale=1)

   ############################################################
   def menu_clear_roi(self):
      # widget_control, /hourglass
      self.foreground.mca.set_rois([])
      self.foreground.roi = self.foreground.mca.get_rois()
      self.foreground.nrois = len(self.foreground.roi)
      self.update_spectrum(rescale=1)

   ############################################################
   def menu_label_roi(self):
      if (self.foreground.nrois > 0):
         # If the markers are on the current ROI then
         # change the label of the current ROI
         roi = self.display.current_roi
         if ((self.display.lmarker ==
                        self.foreground.roi[roi].left) and
             (self.display.rmarker ==
                        self.foreground.roi[roi].right)):
            value = self.widgets.label_roi.get()
            self.foreground.roi[roi].label = value.strip()
            self.foreground.mca.set_rois(self.foreground.roi)

   ############################################################
   def menu_next_roi(self):
      if (self.foreground.nrois > 0):
         self.display.current_roi = self.display.current_roi + 1
         if (self.display.current_roi >= self.foreground.nrois):
            self.display.current_roi = 0
         self.show_roi(self.display.current_roi)

   ############################################################
   def menu_prev_roi(self):
      if (self.foreground.nrois > 0):
         self.display.current_roi = self.display.current_roi - 1
         if (self.display.current_roi < 0):
            self.display.current_roi = self.foreground.nrois - 1
         self.show_roi(self.display.current_roi)

   ############################################################
   def menu_klm_element(self, value):
      z = Xrf.atomic_number(value)
      if (z != None):
         self.klm_markers(z)

   ############################################################
   def menu_klm_line(self, value):
      self.klm_markers(self.display.klm)

   ############################################################
   def menu_klm_up(self):
      self.klm_markers(self.display.klm + 1)

   ############################################################
   def menu_klm_down(self):
      self.klm_markers(self.display.klm - 1)

   ############################################################
   def menu_zoom_up(self):
      range = self.display.hmax-self.display.hmin
      t = max((range/4), 5)       # Always display at least 10 channels
      self.display.hmin = min(max((self.display.cursor - t), 0),
                           (self.foreground.nchans-1))
      self.display.hmax = min(max((self.display.cursor + t), 0),
                           (self.foreground.nchans-1))
      self.update_spectrum(rescale=1)

   ############################################################
   def menu_zoom_down(self):
      range = self.display.hmax-self.display.hmin
      t = range
      self.display.hmin = min(max((self.display.cursor - t), 0),
                           (self.foreground.nchans-1))
      self.display.hmax = min(max((self.display.cursor + t), 0),
                           (self.foreground.nchans-1))
      self.update_spectrum(rescale=1)

   ############################################################
   def menu_shift_up(self):
      range = self.display.hmax-self.display.hmin
      t = (range/2)
      self.display.hmax = min(max((self.display.hmax + t), 0),
                                  (self.foreground.nchans-1))
      self.display.hmin = min(max((self.display.hmax - range), 0),
                                  (self.foreground.nchans-1))
      self.update_spectrum(rescale=1)

   ############################################################
   def menu_shift_down(self):
      range = self.display.hmax-self.display.hmin
      t = (range/2)
      self.display.hmin = min(max((self.display.hmin - t), 0),
                                  (self.foreground.nchans-1))
      self.display.hmax = min(max((self.display.hmin + range), 0),
                                  (self.foreground.nchans-1))
      self.update_spectrum(rescale=1)

   ############################################################
   def menu_lin_log(self, value):
      index=self.widgets.lin_log.index(value)
      self.display.vlog = index
      self.update_spectrum(rescale=1)

   ############################################################
   def menu_horiz_mode(self, value):
      index=self.widgets.horiz_mode.index(value)
      self.display.horiz_mode=index
      self.lmarker(self.display.lmarker)
      self.rmarker(self.display.rmarker)
      self.cursor(self.display.cursor)
      self.show_stats()

   ############################################################
   def menu_lm_pos(self):
      value = self.widgets.lm_pos.get()
      if (self.display.horiz_mode == 0):
         self.lmarker(int(value))
      elif (self.display.horiz_mode == 1):
         self.lmarker(float(value), energy=1)
      elif (self.display.horiz_mode == 2):
         self.lmarker(float(value), d_spacing=1)
      self.show_stats()

   ############################################################
   def menu_rm_pos(self):
      value = self.widgets.rm_pos.get()
      if (self.display.horiz_mode == 0):
         self.rmarker(int(value))
      elif (self.display.horiz_mode == 1):
         self.rmarker(float(value), energy=1)
      elif (self.display.horiz_mode == 2):
         self.rmarker(float(value), d_spacing=1)
      self.show_stats()

   ############################################################
   def menu_cur_pos(self):
      value = self.widgets.cur_pos.get()
      if (self.display.horiz_mode == 0):
         self.cursor(int(value))
      elif (self.display.horiz_mode == 1):
         self.cursor(float(value), energy=1)
      elif (self.display.horiz_mode == 2):
         self.cursor(float(value), d_spacing=1)

   ############################################################
   def about(self):
      Pmw.aboutversion('Version 1.0.0\nMay 20, 2002')
      Pmw.aboutcontact('Mark Rivers\n' +
                       'The University of Chicago\n' +
                       'rivers@cars.uchicago.edu\n')
      t = Pmw.AboutDialog(self.widgets.top, applicationname='mcaDisplay')

   ############################################################
   def help(self):
       command = os.getenv('MCA_HELP_COMMAND')
       if (command == ''):
          tkMessageBox.showerror(title='mcaDisplay Error',
                   message='Environment variable MCA_HELP_COMMAND not defined')
       else:
          os.system(command)

   ############################################################
   def menu_exit(self):
      self.save_settings()
      self.widgets.top.destroy()

   ############################################################
   def timer(self):
      redraw_needed = 0
      stats_changed = 0
      # if (self.windows.mouse_button == 0):
      if (1):
         if ((self.foreground.mca != None) and
            (self.foreground.is_detector)):
            new_flag = self.foreground.mca.new_acquire_status()
            if (new_flag):
               acqg = self.foreground.mca.get_acquire_status()
               stats_changed = 1
               self.display.current_acqg = acqg
               if (self.display.current_acqg):
                  self.options.save_done = 0
                  self.widgets.start.configure(state=DISABLED)
                  self.widgets.stop.configure(state=NORMAL)
               else:
                  if (self.display.prev_acqg):
                     # Acquisition just completed
                     if (self.options.autosave):
                        self.save_file(self.file.next_filename)
                     if (self.options.autorestart):
                        self.foreground.mca.erase()
                        self.foreground.mca.start()
                  self.widgets.start.configure(state=NORMAL)
                  self.widgets.stop.configure(state=DISABLED)
            self.display.prev_acqg = self.display.current_acqg
            new_flag = self.foreground.mca.new_elapsed()
            if (new_flag):
               self.foreground.elapsed = self.foreground.mca.get_elapsed()
               stats_changed = 1
            new_flag = self.foreground.mca.new_data()
            if (new_flag):
               self.foreground.data = self.foreground.mca.get_data()
               # These values are used for computing counts/second in show_stats
               self.display.prev_time = self.display.current_time
               self.display.current_time = self.foreground.elapsed.read_time
               self.display.prev_counts = self.display.current_counts
               self.display.prev_bgd = self.display.current_bgd
               redraw_needed = 1
         else:    # Foreground is not detector
            self.display.current_acqg = 0

         if (self.background.mca != None) and (self.background.is_detector):
            new_flag = self.background.mca.new_data()
            if (new_flag):
               self.background.data = self.background.mca.get_data()
               redraw_needed = 1
            new_flag = self.background.mca.new_elapsed()
            if (new_flag):
               self.background.elapsed = self.background.mca.get_elapsed()
               stats_changed = 1
      else:
         stats_changed = 1  # User is moving cursor or markers
      if (redraw_needed): self.update_spectrum()
      if (stats_changed): self.show_stats()
      self.after_id=self.widgets.top.after(
                            int(self.display.update_time*1000), self.timer)


   ############################################################
   def update_spectrum(self, rescale=0):
      graph = self.widgets.plot
      hmax = int(min((self.display.hmax), (self.foreground.nchans-1)))
      hmin = int(max(self.display.hmin, 0))
      xdata = tuple(range(hmin, hmax+1))
      if (rescale):
         graph.xaxis_configure(max=hmax, min=hmin)
      if (self.foreground.valid):
         ydata = self.foreground.data[hmin:hmax+1]
         graph.element_configure('foreground', xdata=xdata,
                                               ydata=tuple(ydata))
#            visible_data = self.foreground.data[self.display.hmin:
#                                                self.display.hmax+1]
#            ymin = min(visible_data)
#            ymax = max(visible_data)

      # Build the display list of elements to display
      display = ['foreground']
      if (self.background.valid):
         # There is a bug in Blt log plot if all channels are 0, sets
         # small minimum.  Work around by setting channel 0 to 1 for now
         self.background.data[0]=1
         ydata = self.background.data[hmin:hmax+1]
         graph.element_configure('background', xdata=xdata,
                                               ydata=tuple(ydata))
         display.append('background')
      for i in range(self.foreground.nrois):
         roi = 'ROI'+str(i)
         left = self.foreground.roi[i].left
         right = self.foreground.roi[i].right+1
         if (left > hmax) or (right < hmin): continue
         left = max(left, hmin)
         right = min(right, hmax)
         graph.element_configure(roi,
                                 xdata=tuple(range(left, right)),
                                 ydata=tuple(self.foreground.data[left:right]))
         display.append(roi)
      graph.yaxis_configure(logscale=self.display.vlog)
      graph.element_show(display)

      self.lmarker(self.display.lmarker)
      self.rmarker(self.display.rmarker)
      self.cursor(self.display.cursor)
      self.rescale_jcpds()

   ############################################################
   def show_stats(self):
      # Display statistics on region between left and right markers
      left = self.display.lmarker
      right = self.display.rmarker
      total_counts = self.foreground.data[left:right+1]
      tot  = int(Numeric.sum(total_counts))
      n_sel        = right - left + 1
      sel_chans    = left + Numeric.arange(n_sel)
      left_counts  = self.foreground.data[left]
      right_counts = self.foreground.data[right]
      bgd_counts   = left_counts + (Numeric.arange(n_sel)/(n_sel-1) *
                                   (right_counts - left_counts))
      bgd = int(Numeric.sum(bgd_counts))
      net_counts   = total_counts - bgd_counts
      net          = Numeric.sum(net_counts)

      self.display.current_counts = tot
      self.display.current_bgd = bgd

      # Total Counts
      self.display.current_counts = tot
      self.widgets.total_counts.configure(text=str(tot))

      # Net Counts
      self.widgets.net_counts.configure(text=str(tot-bgd))

      # Counts/second
      # If acquisition is in progress then use instantaneous counts/sec, else
      # use integrated counts/second
      total_cps = 0.
      net_cps = 0.
      if (self.display.current_acqg):
         delta_t = self.display.current_time - self.display.prev_time
         if (delta_t > 0):
             total_cps = ((self.display.current_counts -
                          self.display.prev_counts)
                         / delta_t)
             net_cps = ((self.display.current_counts -
                         self.display.prev_counts -
                         self.display.current_bgd + self.display.prev_bgd)
                         / delta_t)
      else:
         if (self.foreground.elapsed.real_time > 0.):
             total_cps = (self.display.current_counts /
                         (self.foreground.elapsed.real_time))
             net_cps = ((self.display.current_counts -
                        self.display.current_bgd) /
                        (self.foreground.elapsed.real_time))
      s = ('%.1f' % total_cps)
      self.widgets.total_cps.configure(text=s)
      s = ('%.1f' % net_cps)
      self.widgets.net_cps.configure(text=s)

      # Peak centroid and FWHM
      if ((net > 0.) and (n_sel >= 3)):
         amplitude, centroid, fwhm = CARSMath.fit_gaussian(sel_chans, net_counts)
      else:
         centroid = (left + right)/2.
         fwhm = right - left
      cal = self.channel_to_cal(centroid)
      s = ('%.3f' % cal)
      self.widgets.center_pos.configure(text=s)
      # To calculate FWHM in energy is a little tricky because of possible
      # quadratic calibration term.
      cal = (self.channel_to_cal(centroid+fwhm/2.) -
             self.channel_to_cal(centroid-fwhm/2.))
      s = ('%.3f' % abs(cal))
      self.widgets.fwhm_pos.configure(text=s)

      # Marker  and cursor counts
      s = ('%d' % self.foreground.data[left])
      self.widgets.lm_counts.configure(text=s)
      s = ('%d' % self.foreground.data[self.display.cursor])
      self.widgets.cur_counts.configure(text=s)
      s = ('%d' % self.foreground.data[right])
      self.widgets.rm_counts.configure(text=s)

      # Elapsed live time, real time and counts
      s = ('%.2f' % self.foreground.elapsed.live_time)
      self.widgets.elive.configure(text=s)
      s = ('%.2f' % self.foreground.elapsed.real_time)
      self.widgets.ereal.configure(text=s)

   ############################################################
   def fit_peaks_return(self, background_mca=None, cursor=None,
                        fit_mca=None, fit=None, get_cursor=None):
      if (background_mca != None):
         self.open(background_mca, name='Background fit', background=1)
      if (fit_mca != None):
         self.open(fit_mca, name='Peak fit', background=1)
      if (cursor != None):
         self.cursor(cursor);
         self.lmarker(cursor-1)
         self.rmarker(cursor+1)
      if (fit != None):
         self.peak_fit = fit
      if (get_cursor != None):
         return self.display.cursor

   ############################################################
   def save_settings(self, file=None):
      if (file == None): file = self.file.settings_file
      settings = mcaDisplaySettings()
      settings.filepath = self.file.filepath
      settings.mca_filename = self.file.filename
      settings.mca_name = self.file.mca_name
      settings.vlog = self.display.vlog
      settings.display_update_time =    self.display.update_time
      settings.autosave =       self.options.autosave
      settings.inform_save =    self.options.inform_save
      settings.warn_overwrite = self.options.warn_overwrite
      settings.warn_erase =     self.options.warn_erase
      settings.colors = self.colors
      settings.plot_settings = BltPlot.BltGetSettings(self.widgets.plot,
                                                         data=0, markers=0)
      settings.print_settings = self.print_settings

      try:
         fp = open(file, 'w')
         cPickle.dump(settings, fp)
         fp.close()
      except:
         tkMessageBox.showerror(title='mcaDisplay Error',
               message = 'Error saving settings in file: ' + file)

   ############################################################
   def restore_settings(self, file):
      try:
         fp = open(file, 'r')
         settings = cPickle.load(fp)
         fp.close()
      except:
         tkMessageBox.showerror(title='mcaDisplay Error',
               message = 'Error reading settings from file: ' + file)
         return()
      if (hasattr(settings, 'filepath')):
          self.file.filepath = settings.filepath
          os.chdir(self.file.filepath)
      if (hasattr(settings, 'mca_filename')):
         self.file.filename = settings.mca_filename
      if (hasattr(settings, 'mca_name')):
         self.file.mca_name = settings.mca_name
      if (hasattr(settings, 'vlog')):
         self.display.vlog = settings.vlog
      if (hasattr(settings, 'display_update_time')):
         self.display.update_time = settings.display_update_time
      if (hasattr(settings, 'autosave')):
         self.options.autosave = settings.autosave
      if (hasattr(settings, 'inform_save')):
         self.options.inform_save = settings.inform_save
      if (hasattr(settings, 'warn_overwrite')):
         self.options.warn_overwrite = settings.warn_overwrite
      if (hasattr(settings, 'warn_erase')):
         self.options.warn_erase = settings.warn_erase
      if (hasattr(settings, 'colors')):
         self.colors = settings.colors
      if (hasattr(settings, 'print_settings')):
         self.print_settings = settings.print_settings
      if (hasattr(settings, 'plot_settings')):
         BltPlot.BltLoadSettings(self.widgets.plot, settings.plot_settings)
      self.set_marker_colors()
      self.update_spectrum(rescale=1)

   ############################################################
   def set_marker_colors(self):
      g = self.widgets.plot
      markers = g.marker_names('Markers*')
      for marker in markers:
         g.marker_configure(marker, outline=self.colors.markers)
      markers = g.marker_names('KLM*')
      for marker in markers:
         g.marker_configure(marker, outline=self.colors.klm)
      g.marker_configure('klm_text', outline=self.colors.highlight_klm)
      markers = g.marker_names('JCPDS*')
      for marker in markers:
         g.marker_configure(marker, outline=self.colors.jcpds)
      g.marker_configure('jcpds_text', outline=self.colors.highlight_jcpds)

   ############################################################
   def channel_to_cal(self, chan):
      mode = self.display.horiz_mode
      if (mode == 0): return chan
      elif (mode == 1): return self.foreground.mca.channel_to_energy(chan)
      elif (mode == 2): return self.foreground.mca.channel_to_d(chan)

   ############################################################
   def cal_to_channel(self, cal):
      mode = self.display.horiz_mode
      if (mode == 0): return cal
      elif (mode == 1): return self.foreground.mca.energy_to_channel(cal)
      elif (mode == 2): return self.foreground.mca.d_to_channel(cal)

   ############################################################
   def new_inputs(self):
      if (self.foreground.valid): state=NORMAL
      else: state=DISABLED
      self.widgets.add_roi.configure(state=state)
      self.widgets.delete_roi.configure(state=state)
      self.widgets.clear_roi.configure(state=state)
      self.widgets.label_roi.configure(entry_state=state)
      self.widgets.next_roi.configure(state=state)
      self.widgets.prev_roi.configure(state=state)
      self.widgets.klm_element.configure(entry_state=state)
#      self.widgets.klm_line.configure(menu_state=state)
      self.widgets.klm_down.configure(state=state)
      self.widgets.klm_up.configure(state=state)
      self.widgets.file.entryconfigure('Save Next*', state=state)
      self.widgets.file.entryconfigure('Save As*', state=state)
      self.widgets.file.entryconfigure('Print*', state=state)
      self.widgets.control.entryconfigure('Calibrate e*', state=state)
      self.widgets.control.entryconfigure('Calibrate 2*', state=state)
      self.widgets.display.entryconfigure('JCPDS*', state=state)
      self.widgets.display.entryconfigure('Fit*', state=state)

      if (self.foreground.is_detector): state=NORMAL
      else: state=DISABLED
      self.widgets.start.configure(state=state)
      self.widgets.stop.configure(state=state)
      self.widgets.erase.configure(state=state)
      self.widgets.elive.configure(state=state)
      self.widgets.ereal.configure(state=state)
      self.widgets.control.entryconfigure('Preset*', state=state)

      if (self.foreground.valid) and (self.background.valid): state=NORMAL
      else: state=DISABLED
      self.widgets.file.entryconfigure('Swap*', state=state)

      title = 'mcaDisplay '
      if (self.foreground.valid):
         title = title + '(Foreground=' + self.foreground.name + ') '
         self.widgets.plot.element_configure('foreground',
                                             label=self.foreground.name)
      if (self.background.valid):
         title = title + '(Background=' + self.background.name + ') '
         self.widgets.plot.element_configure('background',
                                             label=self.background.name)
      self.widgets.top.title(title)

############################################################
   def update_time(self):
      self.widgets.update_time_base = t = Pmw.Dialog(
                     command=self.update_time_return,
                     buttons=('OK', 'Apply', 'Cancel'),
                     title='Update time')
      top = t.component('dialogchildsite')
      choices=['0.1', '0.2', '0.5', '1.0', '2.0', '5.0']
      current_time = choices.index('%.1f' % self.display.update_time)
      self.widgets.update_time = t = Pmw.OptionMenu(top, items=choices,
                        labelpos=W, label_text='Display update time (sec)',
                        initialitem = current_time)
      t.pack(anchor=W)

   def update_time_return(self, button):
      if (button == 'OK') or (button == 'Apply'):
         self.display.update_time = \
                float(self.widgets.update_time.getcurselection())
      if (button != 'Apply'): self.widgets.update_time_base.destroy()


   ############################################################
   def open_det(self, background=0):
      name = tkSimpleDialog.askstring("Open Detector", "Detector name",
                                      initialvalue=self.file.mca_name,
                                      parent=self.widgets.top)
      if (name != None):
         self.open_detector(name, background=background)

   ############################################################
   def open_detector(self, name, background=0):
      try:
         mca = hardwareMca.hardwareMca(name)
         self.open(mca, name, background=background)
      except:
         tkMessageBox.showerror(title='mcaDisplay Error',
               message = 'Unable to open detector ' + name)
         if (background):
            self.background.valid = 0
            self.background.is_detector = 0
         else:
            self.foreground.valid = 1
            self.foreground.is_detector = 0
         self.new_inputs()

   ############################################################
   def select_det(self, n_det):
      text = []
      for i in range(1, n_det+1):
         text.append(str(i))
      text.append('Total')
      self.widgets.select_det = t = Pmw.SelectionDialog(self.widgets.top,
                              buttons=['OK'],
                              title='Select Detector',
                              scrolledlist_labelpos = 'n',
                              label_text='Select detector to display:',
                              command=self.select_det_done,
                              scrolledlist_items=text)
      # The following command makes this window modal
      t.activate()
      self.widgets.select_det.destroy()
      return(self.selected_detector)
      
   ############################################################
   def select_det_done(self, result):
      all = list(self.widgets.select_det.get())
      sel = self.widgets.select_det.getcurselection()
      if (len(sel) == 0): self.selected_detector=0
      else:
         sel = sel[0]
         self.selected_detector=all.index(sel)
      self.widgets.select_det.deactivate(result)


   ############################################################
   def open_file(self, file, background=0):
      try:
         # if (background != 0):
         #    obj_destroy, self.background.mca
         # else:
         #   obj_destroy, self.foreground.mca
         med = Med.Med()
         med.read_file(file)
         mcas = med.get_mcas()
         n_det = len(mcas)
         if (n_det == 1):
            mca = mcas[0]
         else:       # Multi-element detector
            detector = self.select_det(n_det)
            if (detector < n_det):
               mca = mcas[detector]
            else:
               mca = mcas[0]
               data = med.get_data(total=1, align=1)
               mca.set_data(data)
         self.open(mca, file, background=background)
      except IOError, e:
         if (background != 0):
            self.background.valid=0
            self.background.is_detector=0
         else:
             self.foreground.valid=1
             self.foreground.is_detector=0
         self.update_spectrum(rescale=1)
         self.show_stats()
         self.new_inputs()
         tkMessageBox.showerror(title='mcaDisplay Error',
                    message='Error reading file: ' + file + '\n' +
                            e.strerror)


   ############################################################
   def open(self, mca, name=' ', background=0):
      # Called when a new file or detector is opened
      if (not isinstance(mca, Mca.Mca)): return
      if (isinstance(mca, hardwareMca.hardwareMca)):
         self.file.mca_name = name
         is_detector=1
      else:
         # self.file.filename = name
         is_detector=0

      if (background != 0):
         self.background.name = name
         self.background.valid = 1
         self.background.is_detector = is_detector
         self.background.mca = mca
         self.background.roi = self.background.mca.get_rois()
         self.background.nrois = len(self.background.roi)
         self.background.elapsed = self.background.mca.get_elapsed()
         self.background.data = self.background.mca.get_data()
         self.background.nchans = len(self.background.data)
      else:
         self.foreground.name = name
         self.foreground.valid = 1
         self.foreground.is_detector = is_detector
         self.foreground.mca = mca
         self.foreground.roi = self.foreground.mca.get_rois()
         self.foreground.nrois = len(self.foreground.roi)
         self.foreground.elapsed = self.foreground.mca.get_elapsed()
         self.foreground.data = self.foreground.mca.get_data()
         self.foreground.nchans = len(self.foreground.data)
         self.display.hmax = self.foreground.nchans-1
      self.update_spectrum(rescale=1)
      self.show_stats()
      self.new_inputs()

   ############################################################
   def save_file(self, file):
      # The following code warns the user if the file already exists, and
      # if warn_overwrite is set then puts up a dialog to confirm overwriting.
      # However, tk_asksavefile does this automatically and it can't be turned
      # off, so we comment it out here.
      
      # exists =  (os.path.isfile(file))
      # if (exists and self.options.warn_overwrite):
      #   reply = tkMessageBox.askyesno(title='mcaDisplay warning',
      #      message='Warning - file: ' + file +
      #               ' already exists.  Overwrite file?')
      #   if (not reply): return

      try:
         self.foreground.mca.write_file(file)
      except Exception, e:
         reply = tkMessageBox.showerror(title='mcaDisplay error',
               message = 'Unable to open file: ' + file + ' ' + e)
         return

      self.options.save_done = 1
      if (self.options.inform_save):
         self.widgets.save_file_top = Pmw.MessageDialog(self.widgets.top,
                           buttons=('OK',), defaultbutton=0,
                           message_text='Successfully saved as file: ' + file,
                           command=self.save_file_acknowledge)
         self.save_after_id = self.widgets.save_file_top.after(2000,
                                                   self.save_file_acknowledge)

      self.file.next_filename = Xrf.increment_filename(file)
      self.widgets.file.entryconfigure('Save Next*', label='Save Next = ' +
                                                    self.file.next_filename)

   def save_file_acknowledge(self, button=None):
         self.widgets.save_file_top.after_cancel(self.save_after_id)
         self.widgets.save_file_top.destroy()

   ############################################################
   def show_roi(self, in_index):
      if (self.foreground.nrois <= 0): return
      index = min(max(in_index, 0), (self.foreground.nrois-1))
      left = self.foreground.roi[index].left
      right = self.foreground.roi[index].right
      middle = (left + right)/2
      if (self.display.hmin > left) or (self.display.hmax < right):
         range = self.display.hmax - self.display.hmin
         hmin = min((middle - range/2.), left)
         hmax = max((middle + range/2.), right)
         self.display.hmin = min(max(hmin,0), (self.foreground.nchans-1))
         self.display.hmax = min(max(hmax,hmin), (self.foreground.nchans-1))
         self.update_spectrum(rescale=1)
      self.lmarker(left)
      self.rmarker(right)
      self.cursor(middle)
      self.show_stats()
      self.widgets.label_roi.setentry(self.foreground.roi[index].label)


   ############################################################
   def update_marker_text(self, marker):
      if (marker == 'cursor'):
         chan = self.display.cursor
         pos_widget = self.widgets.cur_pos
         count_widget = self.widgets.cur_counts
      elif (marker == 'left'):
         chan = self.display.lmarker
         pos_widget = self.widgets.lm_pos
         count_widget = self.widgets.lm_counts
      elif (marker == 'right'):
         chan = self.display.rmarker
         pos_widget = self.widgets.rm_pos
         count_widget = self.widgets.rm_counts

      # Get calibrated units
      if (self.foreground.valid): cal = self.channel_to_cal(chan)
      else: cal = chan

      if (self.display.horiz_mode == 0):
         # Channel
         pos_widget.setentry(('%d' % cal))
      elif (self.display.horiz_mode == 1):
         # Energy
         pos_widget.setentry(('%.3f' % cal))
      elif (self.display.horiz_mode == 2):
         # d-spacing
         pos_widget.setentry(('%.3f' % cal))

      # Update the counts on the screen
      count_widget.configure(text = ('%d' % self.foreground.data[chan]))


   ############################################################
   def new_marker(self, marker, value, energy=0, d_spacing=0):
      if (energy):
         chan = self.foreground.mca.energy_to_channel(value)
      elif (d_spacing):
         chan = self.foreground.mca.d_to_channel(value)
      else: chan = value
      chan = int(min(max(chan, self.display.hmin), self.display.hmax))

      if (marker == 'left'):
         self.display.lmarker = chan
         # Move the right marker if necessary
         if (self.display.rmarker <= self.display.lmarker):
            self.rmarker(self.display.lmarker + 1)
      elif (marker == 'right'):
         self.display.rmarker = chan
         # Move the left marker if necessary
         if (self.display.lmarker >= self.display.rmarker):
            self.lmarker(self.display.rmarker - 1)
      elif (marker == 'cursor'):
         self.display.cursor = chan

      # Update the marker text widgets
      self.update_marker_text(marker)
      # Draw the new marker
      self.draw_marker(marker)

   ############################################################
   def lmarker(self, value, energy=0, d_spacing=0):
      self.new_marker('left', value, energy=energy, d_spacing=d_spacing)

   ############################################################
   def rmarker(self, value, energy=0, d_spacing=0):
      self.new_marker('right', value, energy=energy, d_spacing=d_spacing)

   ############################################################
   def cursor(self, value, energy=0, d_spacing=0):
      self.new_marker('cursor', value, energy=energy, d_spacing=d_spacing)

   ############################################################
   def marker_mouse(self, event, marker):
      g = self.widgets.plot
      (x,y) = g.invtransform(event.x, event.y)

      if (event.type == '2'):    # KeyPress event
         if (marker == 'left'):     x=self.display.lmarker
         elif (marker == 'right'):  x=self.display.rmarker
         elif (marker == 'cursor'): x=self.display.cursor
         if (event.keysym == 'Left') or (event.keysym == 'Down'): x=x-1
         elif (event.keysym == 'Right') or (event.keysym == 'Up'): x=x+1
         self.new_marker(marker, x)
         self.show_stats()       # Update net/total counts, FWHM, etc.

      elif (event.type == '4'):  # Button press event - start dragging
         g.marker_bind(self.markers[marker], '<Motion>',
                       lambda e, s=self, m=marker: s.marker_mouse(e, m))
         self.new_marker(marker, x)

      elif (event.type == '5'):  # Mouse button release event - stop dragging
         g.marker_unbind(self.markers[marker], '<Motion>')
         self.new_marker(marker, x)
         self.show_stats()       # Update net/total counts, FWHM, etc.

      elif (event.type == '6'):  # Mouse drag event
         self.new_marker(marker, x)

      elif (event.type == '7'):  # Enter event - highlight and enable arrow keys
         self.widgets.top.bind('<KeyPress>',
                       lambda e, s=self, m=marker: s.marker_mouse(e, m))
         g.marker_configure(self.markers[marker], outline=self.colors.highlight_markers)

      elif (event.type == '8'):  # Leave event - unhighlight and disable arrow keys
         self.widgets.top.unbind('<KeyPress>')
         g.marker_configure(self.markers[marker], outline=self.colors.markers)

   ############################################################
   def draw_marker(self, marker):
      if (marker == 'left'):
         chan = self.display.lmarker
         length = .15
      elif (marker == 'right'):
         chan = self.display.rmarker
         length = .15
      if (marker == 'cursor'):
         chan = self.display.cursor
         length = .3
      graph = self.widgets.plot
      y0 = self.foreground.data[chan]
      # Convert marker sizes from fractions of display height to graph units
      (ymin,ymax) = graph.yaxis_limits()
      if (self.display.vlog):
         l = math.exp(length*(math.log(ymax) - math.log(ymin))+
                      math.log(max(y0,1)))
      else:
         l = length*(ymax-ymin)
      graph.marker_configure(self.markers[marker], coords=(chan, y0, chan, y0+l))


   ############################################################
   def klm_markers(self, in_z):
      # Displays X-ray lines of element with atomic number Z.
      # Check that Z is within bounds.
      z = min(max(in_z, 1), 100)
      self.display.klm = z
      self.widgets.klm_element.selectitem(z-1, setentry=1)

      lines = []
      all_lines = self.display.k_lines + self.display.l_lines
      graph = self.widgets.plot
      for line in all_lines:
         marker = 'KLM'+line
         graph.marker_configure(marker, hide=1)
      element = self.widgets.klm_element.getcurselection()[0]
      show_lines = self.widgets.klm_line.getcurselection()
      if (show_lines == 'K') or (show_lines == 'K & L'):
         lines = lines + self.display.k_lines
      if (show_lines == 'L') or (show_lines == 'K & L'):
         lines = lines + self.display.l_lines
      length = .25
      # Convert marker sizes from fractions of display height to graph units
      (ymin,ymax) = graph.yaxis_limits()
      if (self.display.vlog):
         l = math.exp(length*(math.log(ymax) - math.log(ymin)))
      else:
         l = length*(ymax-ymin)
      for line in lines:
         marker = 'KLM'+line
         e = Xrf.lookup_xrf_line(element + ' ' + line)
         if (e != 0.):
            chan = self.foreground.mca.energy_to_channel(e, clip=1)
            data = self.foreground.data[chan]
            y = max(data, ymin+l)
            graph.marker_configure(marker, coords=(chan, '-Inf', chan, y),
                                   hide=0)

   ############################################################
   def klm_mouse(self, event, marker):
      g = self.widgets.plot
      (x,y) = g.invtransform(event.x, event.y-25)
      if (event.type == '7'):  # Enter event - create a new text label
         line = self.widgets.klm_element.getcurselection()[0] + ' ' + marker[3:]
         energy = Xrf.lookup_xrf_line(line)
         text = line + '\n' + ('%.3f' % energy) + ' keV'
         g.marker_configure('klm_text', text=text, hide=0, coords=(x, y))
         g.marker_configure(marker, outline=self.colors.highlight_klm)
      elif (event.type == '8'):  # Leave event - delete text label
         g.marker_configure('klm_text', hide=1)
         g.marker_configure(marker, outline=self.colors.klm)

   ############################################################
   def draw_jcpds(self):
      jcpds = self.file.jcpds
      jcpds.compute_d(self.display.pressure,
                      self.display.temperature)
      refl = jcpds.get_reflections()
      if (len(refl) == 0): return

      graph = self.widgets.plot
      # Hide any existing JCPDS markers
      markers = graph.marker_names('JCPDS*')
      for m in markers: graph.marker_configure(m, hide=1)
      material = jcpds.name
      marker = 0
      for r in refl:
         chan = self.foreground.mca.d_to_channel(r.d, clip=1)
         # Change marker coordinates
         graph.marker_configure(markers[marker], hide=0,
                              coords=(chan, '-Inf', chan, 'Inf'))
         marker = marker+1
         if (marker >= self.MAX_JCPDS): break
      self.rescale_jcpds()

   ############################################################
   def rescale_jcpds(self):
      graph = self.widgets.plot
      markers = graph.marker_names('JCPDS*')
      if (len(markers) == 0): return
      length = .25
      # Convert marker sizes from fractions of display height to graph units
      (ymin,ymax) = graph.yaxis_limits()
      if (self.display.vlog):
         l = math.exp(length*(math.log(ymax) - math.log(ymin)))
      else:
         l = length*(ymax-ymin)
      for m in markers:
         str = graph.marker_cget(m, 'coords')
         words = str.split()
         chan = int(float(words[0]))
         data = self.foreground.data[chan]
         y = max(data, ymin+l)
         graph.marker_configure(m, coords=(chan, '-Inf', chan, y))

   ############################################################
   def jcpds_mouse(self, event, marker):
      g = self.widgets.plot
      (x,y) = g.invtransform(event.x, event.y-25)
      refl=self.file.jcpds.get_reflections()
      n = int(marker[5:])
      #      print 'marker, n=', marker, n
      r = refl[n]
      text = self.file.jcpds.name + ' ' + str(r.h)+str(r.k)+str(r.l)
      if (event.type == '7'):  # Enter event - display text marker
         g.marker_configure('jcpds_text', text=text, coords=(x, y), hide=0)
         g.marker_configure(marker, outline=self.colors.highlight_jcpds)
      elif (event.type == '8'):  # Leave event - delete text label
         g.marker_configure('jcpds_text', hide=1)
         g.marker_configure(marker, outline=self.colors.jcpds)


############################################################
class mcaDisplayJcpds:
   def __init__(self, display):
      class widgets:
         pass
      self.display = display
      self.widgets = widgets()
#     if xregistered( 'mca_display::display_jcpds') then return
      calibration = self.display.foreground.mca.get_calibration()
      self.widgets.top = t = Pmw.Dialog(command=self.commands,
                     buttons=('Add ROIs', 'Add peaks', 'Clear', 'Exit'),
                     title='mcaDisplayJCPDS')
      top = t.component('dialogchildsite')

      row = Frame(top); row.pack(anchor=W)
      self.widgets.new_path = t = Button(row, text='JCPDS directory...',
                                     command=self.new_path);
      t.pack(side=LEFT)
      entry_width = 10
      label_width = 20
      self.widgets.material = t = Pmw.ComboBox(row, history=0,
                            entry_width=20, listbox_width=20,
                            scrolledlist_items=[' ', ' '],
                            selectioncommand=self.read_file)
      self.build_list()
      t.selectitem(0, setentry=1)
      t.pack(side=LEFT)

      self.widgets.pressure = t = Pmw.EntryField(top,
                            value=str(self.display.display.pressure),
                            labelpos=W, label_text='Pressure (GPa):',
                            label_width=label_width, label_anchor=E,
                            entry_width=entry_width, entry_justify=CENTER,
                            validate={'validator':'real'},
                            command=self.pressure)
      t.pack(anchor=W)
      self.widgets.temperature = t = Pmw.EntryField(top,
                            value=str(self.display.display.temperature),
                            labelpos=W, label_text='Temperature (K):',
                            label_width=label_width, label_anchor=E,
                            entry_width=entry_width, entry_justify=CENTER,
                            validate={'validator':'real'},
                            command=self.temperature)
      t.pack(anchor=W)
      two_theta = self.display.foreground.mca.get_calibration().two_theta
      self.widgets.two_theta = t = Pmw.EntryField(top,
                            value=str(two_theta),
                            labelpos=W, label_text='2-theta (degrees):',
                            label_width=label_width, label_anchor=E,
                            entry_width=entry_width, entry_justify=CENTER,
                            validate={'validator':'real'},
                            command=self.two_theta)
      t.pack(anchor=W)

   ############################################################
   def new_path(self):
      file = tkFileDialog.askopenfilename(parent=self.display.widgets.top,
                                title='Select directory',
                                initialdir=self.display.file.jcpds_path,
                                filetypes=[('All files','*')])
      if (file == ''): return
      path = os.path.dirname(file)+os.path.os.sep
      self.display.file.jcpds_path = path
      self.build_list()

   ############################################################
   def build_list(self):
      path = self.display.file.jcpds_path
      if (path == None): path='.'
      files = os.listdir(path)
      goodfiles=[]
      for f in files:
         if (f.find('.jcpds') != -1):
            goodfiles.append(f.replace('.jcpds',''))
      self.widgets.material._list.setlist(goodfiles)

   ############################################################
   def read_file(self, file):
      if (file == ''): return
      file = self.display.file.jcpds_path + file + '.jcpds'
      self.display.file.jcpds.read_file(file)
      self.display.draw_jcpds()

   ############################################################
   def pressure(self):
      self.display.display.pressure = float(self.widgets.pressure.get())
      self.display.draw_jcpds()

   ############################################################
   def temperature(self):
      self.display.display.temperature = float(self.widgets.temperature.get())
      self.display.draw_jcpds()

   ############################################################
   def two_theta(self):
      two_theta = float(self.widgets.pressure.get())
      calibration = self.display.foreground.mca.get_calibration()
      calibration.two_theta = two_theta
      self.display.foreground.mca.set_calibration(calibration)
      self.display.draw_jcpds()

   ############################################################
   def add_rois(self):
      refl = self.display.file.jcpds.get_reflections()
      npeaks = min(len(refl), self.display.MAX_ROIS)
      for i in range(npeaks):
         r = refl[i]
         chan = self.display.foreground.mca.d_to_channel(r.d)
         if (chan > 20) and (chan < self.display.foreground.nchans-21):
            left = chan-20
            right = chan+20
            label = self.display.file.jcpds.name
            label = label + ' ' + str(r.h) + str(r.k) + str(r.l)
            roi = Mca.McaROI()
            roi.left = left
            roi.right = right
            roi.label = label
            roi.d_spacing = r.d
            roi.use = 1
            self.display.foreground.mca.add_roi(roi)
      self.display.foreground.roi = self.display.foreground.mca.get_rois()
      self.display.foreground.nrois = len(self.display.foreground.roi)
      self.display.show_roi(0)
      self.display.update_spectrum(rescale=1)

   ############################################################
   def add_peaks(self):
      refl = self.display.file.jcpds.get_reflections()
      if (len(refl) == 0): return
      peaks = self.display.peak_fit.peaks
      for r in refl:
         new_peak = Mca.McaPeak()
         chan = self.display.foreground.mca.d_to_channel(r.d)
         energy = self.display.foreground.mca.channel_to_energy(chan)
         new_peak.initial_energy = energy
         label=self.widgets.material.get()
         label = label + ' ' + str(r.h) + str(r.k) + str(r.l)
         new_peak.label = label
         # Make a reasonble estimate of initial FWHM
         new_peak.initial_fwhm = 0.2 + .03*math.sqrt(abs(energy))
         new_peak.energy_flag=1
         new_peak.fwhm_flag=1
         peaks.append(new_peak)
      tkMessageBox.showinfo(title='mcaDisplayJCPDS',
                            message = 'Added ' + str(len(refl)) +
                            ' peaks to the peak list')

   ############################################################
   def commands(self, button):
      if (button == 'Add ROIs'): self.add_rois()
      elif (button == 'Add peaks'): self.add_peaks()
      elif (button == 'Clear'):
         # Delete any existing JCPDS markers
         graph = self.display.widgets.plot
         markers = graph.marker_names('JCPDS*')
         for m in markers: graph.marker_configure(m, hide=1)
      else: self.widgets.top.destroy()

############################################################
class mcaDisplayFilePreferences:
   def __init__(self, display):
      class widgets:
         pass
      self.display = display
      self.widgets = widgets()
      self.widgets.top = t = Pmw.Dialog(command=self.commands,
                     buttons=('OK', 'Cancel'),
                     title='mcaDisplayFilePreferences')
      top = t.component('dialogchildsite')
      self.widgets.warn_overwrite = self.add_row(top,
                              self.display.options.warn_overwrite,
                              'Warning when overwriting file:')
      self.widgets.warn_erase = self.add_row(top,
                              self.display.options.warn_erase,
                              'Warning when erasing unsaved data:')
      self.widgets.inform_save = self.add_row(top,
                              self.display.options.inform_save,
                              'Informational popup after saving file:')
      self.widgets.autosave = self.add_row(top,
                              self.display.options.autosave,
                              'Autosave when acquisition stops:')
      self.widgets.autorestart = self.add_row(top,
                              self.display.options.autorestart,
                              'Auto-restart when acquisition stops:')

   ############################################################
   def add_row(self, parent, option, text):
      t = Pmw.RadioSelect(parent, buttontype='radiobutton',
                          labelpos=W, label_width=35, label_anchor=E,
                          label_text=text)
      t.pack()
      for text in ('No', 'Yes'):
         t.add(text)
      t.invoke(option)
      return t

   ############################################################
   def commands(self, button):
      if (button == 'OK'):
         self.display.options.warn_overwrite = \
                        self.widgets.warn_overwrite.getcurselection() == 'Yes'
         self.display.options.warn_erase = \
                        self.widgets.warn_erase.getcurselection() == 'Yes'
         self.display.options.inform_save = \
                        self.widgets.inform_save.getcurselection() == 'Yes'
         self.display.options.autosave = \
                        self.widgets.autosave.getcurselection() == 'Yes'
         self.display.options.autorestart = \
                        self.widgets.autorestart.getcurselection() == 'Yes'
      self.widgets.top.destroy()

