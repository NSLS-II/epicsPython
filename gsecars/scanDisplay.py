"""
This program provides a scan display in Python using Tkinter widgets and Blt.

Author:        Mark Rivers
Created:       Oct 5, 2002
Modifications:
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
import Xrf
import BltPlot
import myTkTop
import Scan
import epicsScan


############################################################
class scanDisplay_options:
   def __init__(self):
      self.autosave       = 0 # Automatically save file when scan completes
      self.autorestart    = 0 # Automatically restart scan when scan completes
      self.warn_overwrite = 1 # Warn user of attempt to overwrite existing file
      self.warn_erase     = 0 # Warn user of attempt to erase without prior save
      self.save_done      = 0 # Flag to keep track of save done before erase
      self.inform_save    = 0 # Inform user via popup of successful file save
      self.debug          = 0 # Debug flag - not presently used

############################################################
class scanDisplay_file:
   def __init__(self):
      self.filepath      = './'
      self.filename      = ''          # name of saved or read
      self.next_filename = 'test.dat'  # name of next file to save
      self.settings_file = 'scan.settings'

############################################################
class scanDisplay_display:
   def __init__(self):
      self.update_time = .5
      self.current_time = 0.
      self.current_acqg = 0
      self.prev_time   = 0.
      self.prev_acqg   = 0
      self.new_stats   = 0
      self.horiz_mode  = 0
      self.hmin        = 0
      self.hmax        = 2048
      self.vlog        = 1


############################################################
class scanDisplay_colors:
   def __init__(self):
      self.background           = 'lightgrey'
      self.markers              = 'red'
      self.highlight_markers    = 'green'
      self.plot                 = 'black'
      self.labels               = 'blue'
      self.entry_foreground     = 'black'
      self.entry_background     = 'lightblue'
      self.label_foreground     = 'blue'
      self.label_background     = 'white'

############################################################
class scanDisplaySettings:
   def __init__(self):
      pass

############################################################
class scanDisplay_fonts:
   def __init__(self):
      self.label  = ('helvetica', -12)
      self.text   = ('helvetica', -12)
      self.button = ('helvetica', -12, 'bold')
      self.help   = ('courier', 10)

############################################################
class scanDisplay_scan:
   def __init__(self):
      self.name         = ''
      self.valid        = 0
      self.is_detector  = 0
      self.nchans       = 0
      self.data         = []


############################################################
class scanDisplay:
   """
   This program provides a scan display and control in Python using
   Tk widgets. It emulates the look and feel of the Canberra scan package.

   This program requires that the following environment variables be set:
       SCAN_SETTINGS     - File name to save/restore for scan program
                           settings, such as size, colors, line style,
                           etc.  If environment variable not set then the
                           file scan.settings in the current default
                           directory is used
       SCAN_HELP_COMMAND - System command to display scan help text
   """

   def __init__(self, file=None, detector=None):

      self.options    = scanDisplay_options()
      self.file       = scanDisplay_file()
      self.display    = scanDisplay_display()
      self.colors     = scanDisplay_colors()
      self.fonts      = scanDisplay_fonts()
      self.print_settings   = None
      class widgets:
         pass
      self.widgets    = widgets()
      self.create_display()
      self.update_plot(rescale=1)
      settings_file = os.getenv('SCAN_SETTINGS')
      if (settings_file != None): self.file.settings_file = settings_file
      self.restore_settings(self.file.settings_file)

#     self.about()
      self.new_inputs()
      if (file != None): self.open_file(file)
      if (scan != None): self.open_scan(scan)
      self.after_id=self.widgets.top.after(
                            int(self.display.update_time*1000), self.timer)

   #############################################################
   def __del__(self):
      pass

   #############################################################
   def create_display(self):
      top = myTkTop.myTkTop()
      top.title('scanDisplay')
      self.widgets.top = top
      frame = Frame(top, borderwidth=1, relief='raised')
      frame.pack(fill=X)
      mb = Pmw.MenuBar(frame)
      mb.pack(fill=X)
      mb.addmenu('File', '', side='left')
      self.widgets.file = mb.component('File-menu')
      mb.addmenuitem('File', 'command', label='Scan record...',
                                    command=self.open_scan)
      mb.addmenuitem('File', 'command', label='Read file...',
                                    command=self.menu_open_file)
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

      mb.addmenu('View', '', side='left')
      self.widgets.display = mb.component('View-menu')
      mb.addmenuitem('View', 'command', label='Plot...',
                      command=self.menu_plot)
      mb.addcascademenu('View', 'Preferences')
      mb.addmenuitem('Preferences', 'command', label='Update time...',
         command=self.update_time)
      mb.addmenuitem('Preferences', 'command', label='Plot...',
         command=lambda s=self: BltPlot.BltConfigureGraph(s.widgets.plot))
      mb.addmenuitem('Preferences', 'command', label='Foreground plot...',
         command=lambda s=self: BltPlot.BltConfigureElement(s.widgets.plot, 'foreground'))
      mb.addmenuitem('Preferences', 'command', label='Background plot...',
         command=lambda s=self: BltPlot.BltConfigureElement(s.widgets.plot, 'background'))
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
      row = Frame(acquire); row.pack()
      self.widgets.erase = t = Button(row, text="Pause",
                                 command=self.menu_pause)
      t.pack(side=LEFT)
      self.widgets.erase = t = Button(row, text="Resume",
                                 command=self.menu_resume)
      t.pack(side=LEFT)

      status = Frame(control_column, borderwidth=1, relief='solid')
      status.pack(fill=X, pady=fypad)
      t = Label(status, text='Current point:', width=15); t.pack(side=TOP)
      self.widgets.current_point = t = Label(status, width=8, relief='groove',
                                    text='0',
                                    foreground=self.colors.label_foreground,
                                    background=self.colors.label_background)
      t.pack(side=TOP)
      t = Label(status, text='Status', width=5); t.pack(side=TOP)
      self.widgets.status = t = Label(status, width=8, relief='groove',
                                text=' ',
                                foreground=self.colors.label_foreground,
                                background=self.colors.label_background)
      t.pack(side=TOP)


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

      self.widgets.plot = t = Pmw.Blt.Graph(data_column)
      t.configure(plotbackground=self.colors.background)
      t.line_create('foreground', symbol="", pixels=2,
                    color=self.colors.plot)

      t.pack(side=TOP, anchor=N, expand=YES, fill=BOTH)
      self.set_marker_colors()

   ############################################################
   def marker_callback(self, marker):
      # This is called from BltConfigureMarker() whenever the marker/cursor
      # configuration has changed.
      self.colors.markers = self.widgets.plot.marker_cget(
                                           self.markers['left'], 'outline')
      self.colors.highlight_markers = self.widgets.plot.marker_cget(
                                           self.markers['left'], 'fill')


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
      self.update_plot(rescale=1)

   ############################################################
   def menu_open_file(self):
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
   def menu_print(self):
      BltPlot.BltPrint(self.widgets.plot)

   ############################################################
   def menu_plot(self):
      BltPlot.BltPrint(self.widgets.plot)
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
      t = scanDisplayFilePreferences(self)

   ############################################################
   def menu_start(self):
      self.scan.start()

   ############################################################
   def menu_stop(self):
      self.scan.stop()

   ############################################################
   def menu_pause(self):
      self.scan.pause()

   ############################################################
   def menu_resume(self):
      self.scan.resume()

   ############################################################
   def menu_zoom_up(self):
      range = self.display.hmax-self.display.hmin
      t = max((range/4), 5)       # Always display at least 10 channels
      self.display.hmin = min(max((self.display.cursor - t), 0),
                           (self.foreground.nchans-1))
      self.display.hmax = min(max((self.display.cursor + t), 0),
                           (self.foreground.nchans-1))
      self.update_plot(rescale=1)

   ############################################################
   def menu_zoom_down(self):
      range = self.display.hmax-self.display.hmin
      t = range
      self.display.hmin = min(max((self.display.cursor - t), 0),
                           (self.foreground.nchans-1))
      self.display.hmax = min(max((self.display.cursor + t), 0),
                           (self.foreground.nchans-1))
      self.update_plot(rescale=1)

   ############################################################
   def menu_shift_up(self):
      range = self.display.hmax-self.display.hmin
      t = (range/2)
      self.display.hmax = min(max((self.display.hmax + t), 0),
                                  (self.foreground.nchans-1))
      self.display.hmin = min(max((self.display.hmax - range), 0),
                                  (self.foreground.nchans-1))
      self.update_plot(rescale=1)

   ############################################################
   def menu_shift_down(self):
      range = self.display.hmax-self.display.hmin
      t = (range/2)
      self.display.hmin = min(max((self.display.hmin - t), 0),
                                  (self.foreground.nchans-1))
      self.display.hmax = min(max((self.display.hmin + range), 0),
                                  (self.foreground.nchans-1))
      self.update_plot(rescale=1)

   ############################################################
   def menu_lin_log(self, value):
      index=self.widgets.lin_log.index(value)
      self.display.vlog = index
      self.update_plot(rescale=1)

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
      Pmw.aboutversion('Version 1.0.0\nOctober 6, 2002')
      Pmw.aboutcontact('Mark Rivers\n' +
                       'The University of Chicago\n' +
                       'rivers@cars.uchicago.edu\n')
      t = Pmw.AboutDialog(self.widgets.top, applicationname='scanDisplay')

   ############################################################
   def help(self):
       command = os.getenv('SCAN_HELP_COMMAND')
       if (command == ''):
          tkMessageBox.showerror(title='scanDisplay Error',
                   message='Environment variable SCAN_HELP_COMMAND not defined')
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
         if ((self.scan != None) and
            (isinstance(self.scan, 'epicsScan'))):
            new_flag = self.display.new_acquire_status()
            if (new_flag):
               scanning = self.scan.busy
               stats_changed = 1
               self.display.scanning = scanning
               if (self.display.scanning):
                  self.options.save_done = 0
                  self.widgets.start.configure(state=DISABLED)
                  self.widgets.stop.configure(state=NORMAL)
               else:
                  if (self.display.prev_scanning):
                     # Scan just completed
                     if (self.options.autosave):
                        self.save_file(self.file.next_filename)
                     if (self.options.autorestart):
                        self.scan.start()
                  self.widgets.start.configure(state=NORMAL)
                  self.widgets.stop.configure(state=DISABLED)
            self.display.prev_scanning = self.display.scanning
            new_flag = self.scan.currentPoint != self.display.lastPoint
            if (new_flag):
               stats_changed = 1
               self.foreground.data = self.foreground.scan.get_data()
               # These values are used for computing counts/second in show_stats
               redraw_needed = 1
         else:    # Foreground is not detector
            self.display.scanning = 0

      else:
         stats_changed = 1  # User is moving cursor or markers
      if (redraw_needed): self.update_plot()
      if (stats_changed): self.show_stats()
      self.after_id=self.widgets.top.after(
                            int(self.display.update_time*1000), self.timer)


   ############################################################
   def update_plot(self, rescale=0):
      graph = self.widgets.plot
      hmax = min((self.display.hmax), (self.foreground.nchans-1))
      hmin = max(self.display.hmin, 0)
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
      graph.yaxis_configure(logscale=self.display.vlog)
      graph.element_show(display)

      self.lmarker(self.display.lmarker)
      self.rmarker(self.display.rmarker)
      self.cursor(self.display.cursor)

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
   def save_settings(self, file=None):
      if (file == None): file = self.file.settings_file
      settings = scanDisplaySettings()
      settings.filepath = self.file.filepath
      settings.scan_filename = self.file.filename
      settings.scan_name = self.file.scan_name
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
         tkMessageBox.showerror(title='scanDisplay Error',
               message = 'Error saving settings in file: ' + file)

   ############################################################
   def restore_settings(self, file):
      try:
         fp = open(file, 'r')
         settings = cPickle.load(fp)
         fp.close()
      except:
         tkMessageBox.showerror(title='scanDisplay Error',
               message = 'Error reading settings from file: ' + file)
         return()
      if (hasattr(settings, 'filepath')):
          self.file.filepath = settings.filepath
          os.chdir(self.file.filepath)
      if (hasattr(settings, 'scan_filename')):
         self.file.filename = settings.scan_filename
      if (hasattr(settings, 'scan_name')):
         self.file.scan_name = settings.scan_name
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
      self.update_plot(rescale=1)

   ############################################################
   def set_marker_colors(self):
      g = self.widgets.plot
      markers = g.marker_names('Markers*')
      for marker in markers:
         g.marker_configure(marker, outline=self.colors.markers)

   ############################################################
   def new_inputs(self):
      if (self.scan.valid): state=NORMAL
      else: state=DISABLED
      self.widgets.file.entryconfigure('Save Next*', state=state)
      self.widgets.file.entryconfigure('Save As*', state=state)
      self.widgets.file.entryconfigure('Print*', state=state)

      if (self.scan.is_live): state=NORMAL
      else: state=DISABLED
      self.widgets.start.configure(state=state)
      self.widgets.stop.configure(state=state)
      self.widgets.elive.configure(state=state)
      self.widgets.ereal.configure(state=state)
      self.widgets.control.entryconfigure('Preset*', state=state)

      title = 'scanDisplay '
      if (self.foreground.valid):
         title = title + '(Foreground=' + self.scan.name + ') '
         self.widgets.plot.element_configure('plot',
                                             label=self.scan.name)
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
   def open_scan(self):
      name = tkSimpleDialog.askstring("Open Scan", "Scan record name",
                                      initialvalue=self.file.scan_name,
                                      parent=self.widgets.top)
      if (name != None):
         self.open_scan(name)

   ############################################################
   def open_scan(self, name):
      try:
         scan = epicsScan.epicsScan(name)
         self.open(scan, name)
      except:
         tkMessageBox.showerror(title='scanDisplay Error',
               message = 'Unable to open scan ' + name)
         self.foreground.valid = 1
         self.foreground.is_detector = 0
         self.new_inputs()

   ############################################################
   def open_file(self, file, background=0):
      try:
         med = Med.Med()
         med.read_file(file)
         scans = med.get_scans()
         n_det = len(scans)
         if (n_det == 1):
            scan = scans[0]
         else:       # Multi-element detector
            detector = self.select_det(n_det)
            if (detector < n_det):
               scan = scans[detector]
            else:
               scan = scans[0]
               data = med.get_data(total=1, align=1)
               scan.set_data(data)
         self.open(scan, file, background=background)
      except IOError, e:
         if (background != 0):
            self.background.valid=0
            self.background.is_detector=0
         else:
             self.foreground.valid=1
             self.foreground.is_detector=0
         self.update_plot(rescale=1)
         self.show_stats()
         self.new_inputs()
         tkMessageBox.showerror(title='scanDisplay Error',
                    message='Error reading file: ' + file + '\n' +
                            e.strerror)


   ############################################################
   def open(self, scan, name=' '):
      # Called when a new file or detector is opened
      if (not isinstance(scan, Scan.Scan)): return
      if (isinstance(scan, epicsScan.epicsScan)):
         self.file.scan_name = name
         is_detector=1
      else:
         # self.file.filename = name
         is_detector=0

      self.foreground.name = name
      self.foreground.valid = 1
      self.foreground.is_detector = is_detector
      self.foreground.scan = scan
      self.foreground.roi = self.foreground.scan.get_rois()
      self.foreground.nrois = len(self.foreground.roi)
      self.foreground.elapsed = self.foreground.scan.get_elapsed()
      self.foreground.data = self.foreground.scan.get_data()
      self.foreground.nchans = len(self.foreground.data)
      self.display.hmax = self.foreground.nchans-1
      self.update_plot(rescale=1)
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
      #   reply = tkMessageBox.askyesno(title='scanDisplay warning',
      #      message='Warning - file: ' + file +
      #               ' already exists.  Overwrite file?')
      #   if (not reply): return

      try:
         self.foreground.scan.write_file(file)
      except Exception, e:
         reply = tkMessageBox.showerror(title='scanDisplay error',
               message = 'Unable to open file: ' + file + ' ' + e)
         return

      self.options.save_done = 1
      if (self.options.inform_save):
         top = self.widgets.save_file_top = Toplevel()
         Pmw.MessageDialog(top, buttons=('OK',), defaultbutton=0,
                           message_text='Successfully saved as file: ' + file,
                           command=self.save_file_acknowledge)
         top.after(2000,self.save_file_acknowledge)

      self.file.next_filename = Xrf.increment_filename(file)
      self.widgets.file.entryconfigure('Save Next*', label='Save Next = ' +
                                                    self.file.next_filename)

   def save_file_acknowledge(self, button=None):
         self.widdgets.save_file_top.after_cancel()
         self.widgets.save_file_top.destroy()

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
         chan = self.foreground.scan.energy_to_channel(value)
      elif (d_spacing):
         chan = self.foreground.scan.d_to_channel(value)
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
            chan = self.foreground.scan.energy_to_channel(e, clip=1)
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
class scanDisplayFilePreferences:
   def __init__(self, display):
      class widgets:
         pass
      self.display = display
      self.widgets = widgets()
      self.widgets.top = t = Pmw.Dialog(command=self.commands,
                     buttons=('OK', 'Cancel'),
                     title='scanDisplayFilePreferences')
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
                                 self.widgets.warn_overwrite.getcurselection()
         self.display.options.warn_erase = \
                                 self.widgets.warn_erase.getcurselection()
         self.display.options.inform_save = \
                                 self.widgets.inform_save.getcurselection()
         self.display.options.autosave = \
                                 self.widgets.autosave.getcurselection()
         self.display.options.autorestart = \
                                 self.widgets.autorestart.getcurselection()
      self.widgets.top.destroy()

