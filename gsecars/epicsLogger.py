"""
A GUI window application for logging EPICS process variables to the screen and
to a disk file.

Author:
   Mark Rivers

Created:
   Sept. 18, 2002

Revision history:
   Original version was written in IDL, called EPICS_LOGGER.PRO,
   on July 10, 1999.

   15-Oct-2002 MLR Fixed bug with missing "import time" statement
   15-Oct-2002 MLR Close output file when exiting.
                  

"""
from Tkinter import *
import time
import Pmw
import epicsPV
import tkFileDialog

class epicsLogger:
   """ 
   Logs EPICS process variables to a GUI window and to a disk file.

   epicsLogger was primarily written to be an interactive application. 
   However, it creates a Python class with the following public methods, so it
   can be controlled from other applications or from the Python command line.

   Restrictions:
      Does not gracefully handle the case when PVs cannot be
      accessed, such as when a crate is rebooted.

   Example:
      from epicsLogger import *
      t = epicsLogger(input='xrf_pvs.inp', output='xrf_pvs.log', time=2., start=1)
      t.menu_time(10.)
      t.menu_output('another_file.out')

   """
   def __init__(self, input=None, output=None, time=10., xsize=700,
                ysize=300, max_lines=1000, start=0,
                label_font=('courier', 9, 'bold'), 
                output_font=('courier', 9), 
                help_font=('courier', 10) ):
      """
      Keywords:
      input:
          The name of an input file containing the list of EPICS process
          variables (PV) to be logged.  The format of this file is one line per
          PV.  Each line has the following format.  The spaces between the fields
          are optional, but the vertical bars (|) are required. 

              PVName | PVFormat | Description | DescriptionFormat

          "PVName" is the name of the EPICS PV.

          "PVFormat" is the format with which the PV should be displayed on the
          screen and written to the disk file, e.g. "%15.3f" or %15d".

          "Description" is a string which describes this PV. It is displayed at
          the top of the screen.  Any character except "|" can be used in this 
          field, including white space.

          "DescriptionFormat" is the format with which the description string
          should be displayed on the screen and in the disk file, e.g. %15.15s.
          This format should specify the same field width (e.g. 15 characters) as
          the PVformat for this PV to make things line up properly on the screen.

          Example input file:
           13BMD:DMM1Ch1_calc.VAL | %15.5f | Load, Tons | %15.15s
           13BMD:DMM1Ch3_calc.VAL | %15.5f | Ram Ht, mm | %15.15s
           13BMD:DMM1Ch5_calc.VAL | %15.3f | Sample Tc, mV | %15.15s
           13BMD:DMM2Ch6_calc.VAL | %15.5f | Amps | %15.15s
           13BMD:DMM2Ch1_calc.VAL | %15.5f | Volts | %15.15s
           13BMD:DMM1Ch8_calc.VAL | %15.5f | Anvil Tc | %15.15s
           13BMD:DMM1Ch10_calc.VAL | %15.5f | T (C) | %15.15s
           13BMD:DMM2Ch4_calc.VAL | %15.5f | Watts | %15.15s

          If "input" is not specified then the input file can be selected 
          later from the "File" menu in the procedure.
          The default is None.

      output:
          The name of the output file to which the logging data will be written.
          If "output" is not specified then the output file can be selected
          later from the "File" menu in the procedure.

          The output is an ASCII file with 3 types of lines in it.  Lines
          beginning with "PVS:" list the process variables which follow in the
          file. Lines beginning with "DESCRIPTION:" list the descriptions of the
          PVs.  Finally, lines beginning with "DATA:" list the date and time, and
          then the values of all of the PVs.  Each value on a line is separated
          from the next by a vertical bar ("|").
          The following is an example of the first few lines from an output file:
             PVS:|Date and time|13BMD:DMM1Ch1_calc.VAL|13BMD:DMM1Ch3_calc.VAL
             DESCRIPTION:|Date and time|Load, Tons|Ram Ht, mm
             DATA:|10-Jul-1999 09:35:44|91.42843|8.244
             DATA:|10-Jul-1999 09:35:45|91.42777|8.244
             DATA:|10-Jul-1999 09:35:46|91.42398|8.244
             DATA:|10-Jul-1999 09:35:47|91.38756|8.244
          These data files can be read into IDL with the function READ_EPICS_LOG.
          They can easily be read into spreadsheets such as Excel, by specifying
          that the input is "Delimited" with a delimiter character of "|".
          The date format in the file is recognized by Excel as a valid date/time
          field.
          The default is None.

      time:
          The time interval for logging, in floating point seconds.  
          The default is 10.0.

      lable_font:
          A tuple defining the font for the PV and description labels.  This 
          should be a fixed spacing font, i.e. not proportionally spaced, or the 
          columns won't line up correctly under the labels. 
          The default is ('courier', '9', 'bold')

      output_font:
          A tuple defining the font for the output window.  This should be a fixed
          spacing font, i.e. not proportionally spaced, or the columns won't line
          up correctly under the labels. 
          The default is ('courier', '9')
      
      help_font:
          A tuple defining the font for the help window.  The help looks better
          in a fixed spacing font, i.e. not proportionally spaced.
          The default is ('courier', '10')
      
      xsize:
          The width of the text output window in pixels. The window can be 
          resized with the mouse when the program is running.
          The default is 700.

      ysize:
          The height of the text output window in pixels. The window can be 
          resized with the mouse when the program is running.
          The default is 300.

      max_lines:
          The maximum number of lines which the text window will retain for
          vertical scrolling.  
          The default is 1000.

      start:
          Set this flag to 1 start logging immediately when the procedure begins.
          By default the user must press the "Start" button to begin logging.
          The default is start=0.
   """

      self.update_time = time
      self.after_id = None
      self.input_valid = 0
      self.logging_enabled = 0
      self.xsize = xsize
      self.ysize = ysize
      self.max_lines = max_lines
      self.pvs = None
      self.output = None
      self.widgets = {}
      self.fonts = {}
      self.fonts['labels'] = label_font
      self.fonts['output'] = output_font
      self.fonts['help'] = help_font
      self.buildDisplay()
      if (input != None): 
         self.menu_input(input)
      if (output != None): 
         self.menu_output(output)
      if (start): 
         self.menu_start()

   def buildDisplay(self):
      """ Private method """
      self.top = top = Tk()
      # Call menu_exit if the user closes the window with the window manager
      Wm.protocol(top, 'WM_DELETE_WINDOW', self.menu_exit)
      top.title('epicsLogger')
      top.geometry(str(self.xsize)+'x'+str(self.ysize))
      frame = Frame(top, borderwidth=1, relief='raised')
      frame.pack(fill=X)
      mb = Pmw.MenuBar(frame)
      mb.pack(fill=X)
      mb.addmenu('File', '', side='left')
      mb.addmenuitem('File', 'command', 
                      label='Input file ...', command=self.menu_input)
      mb.addmenuitem('File', 'command',
                      label='Output file ...', command=self.menu_output)
      mb.addmenuitem('File', 'command', 'Exit', label='Exit',
                      command=self.menu_exit)
      mb.addmenu('Help', '', side='right')
      mb.addmenuitem('Help', 'command', label='Usage', 
                      command=self.help)
      mb.addmenuitem('Help', 'command', label='About', 
                      command=self.about)

      frame = Frame(top); frame.pack(anchor=W)
      self.widgets['start'] = t = Button(frame, text="Start", 
                                 command=self.menu_start, state=DISABLED)
      t.pack(side=LEFT)
      self.widgets['stop'] = t =  Button(frame, text="Stop", 
                                 command=self.menu_stop, state=DISABLED)
      t.pack(side=LEFT)
      self.widgets['update_time'] = t = Pmw.EntryField(frame, labelpos=W,
                          value=self.update_time, entry_width=5, 
                          label_text='Update time (seconds)',
                          validate={'validator':'real', 'min':0.,'max':100},
                          command=self.menu_time); t.pack(side=LEFT)
      t = Label(frame, text='Output file:'); t.pack(side=LEFT)
      self.widgets['output_file'] = t = Label(frame, text='None')
      t.pack(side=LEFT) 

      self.widgets['sf'] = sf = Pmw.ScrolledFrame(top, vscrollmode=NONE, 
                             vertflex='expand', horizflex='fixed')
      sf.pack(expand=YES, fill=BOTH)
      frame = sf.interior()
      self.widgets['labels'] = t = Text(frame, wrap=NONE, relief='groove',
                                       height=2, font=self.fonts['labels'])
      t.insert(END, 'PVS\nDescription\n')
      t.pack(fill=X)
      self.widgets['output'] = t = Pmw.ScrolledText(frame, 
                                      text_font=self.fonts['output'],
                                      text_wrap=NONE, text_height=5,
                                      vscrollmode='static', hscrollmode=NONE,
                                      )
      t.pack(expand=YES, fill=BOTH)

   def menu_input(self, file=None):
      """
      Reads a new input file.  
      
      Keywords:
         file:
            The name of the new input file. If the file is not specified then
            this function opens a file chooser window to select one.
      """
      if (file == None): 
         file = tkFileDialog.askopenfilename(parent=self.top, 
                                title='Input file',
                                filetypes=[('All files','*')])
      if (file == ''): return
      input = open(file, 'r')
      lines = input.readlines()
      input.close()
      self.pvs = []
      for line in lines:
         pv = {}
         words = line.split('|')
         pv['name']=words[0].strip()
         pv['epicsPV'] = epicsPV.epicsPV(pv['name'])
         pv['data_format']=words[1].strip()
         pv['description']=words[2].strip()
         pv['description_format']=words[3].strip()
         self.pvs.append(pv)
      line = ('%20s' % ' ')
      for pv in self.pvs:
         line = line + ' ' + (pv['description_format'] % pv['name'])
      # Enable writing to label widgets
      self.widgets['labels'].configure(state=NORMAL)
      self.widgets['labels'].delete('1.0', END)
      self.widgets['labels'].insert('1.0', line+'\n')
      line = ('%20s' % 'Date and time')
      for pv in self.pvs:
         line = line + ' ' + (pv['description_format'] % pv['description'])
      self.widgets['labels'].insert('2.0', line+'\n')
      self.widgets['labels'].configure(state=DISABLED)
      # Set the widget width to the length of the line plus a bit to allow for
      # width of vertical scroll bar
      self.widgets['labels'].configure(width=len(line)+6)
      if (self.output != None): self.write_output_headers()
      self.input_valid=1
      self.widgets['start'].configure(state=NORMAL)

   def menu_start(self):
      """
      Starts logging.
      """
      self.logging_enabled = 1
      if (self.after_id != None): self.top.after_cancel(self.after_id)
      self.widgets['start'].configure(state=DISABLED)
      self.widgets['stop'].configure(state=NORMAL)
      self.timer()

   def menu_stop(self):
      """
      Stops logging.
      """
      self.logging_enabled = 0
      self.widgets['start'].configure(state=NORMAL)
      self.widgets['stop'].configure(state=DISABLED)

   def menu_exit(self):
      """
      Kills the application.
      """
      if (self.output != None): self.output.close()
      self.top.destroy()

   def menu_time(self, time=None):
      """
      Changes the time interval for logging.
      """
      if (time == None):
         time = float(self.widgets['update_time'].get())
      else:
         self.widgets['update_time'].setentry(str(time))
      self.update_time = time
      if (self.after_id != None): self.top.after_cancel(self.after_id)
      self.timer()

   def menu_output(self, file=None):
      """
      Opens a new output file.
      
      Keywords:
         file:
            The name of the new output file. If the file is not specified then
            this function opens a file chooser window to select one.
      """
      if (file == None):
         file = tkFileDialog.asksaveasfilename(parent=self.top, 
                                  title='Output file',
                                  filetypes=[('All files','*')])
      if (file == ''): return
      if (self.output != None): self.output.close()
      self.output = open(file, 'a')
      self.widgets['output_file'].configure(text=file)
      if (self.input_valid): self.write_output_headers()

   def write_output_headers(self):
      """ Private method """
      line1 = 'PVS|Date and time'
      line2 = 'DESCRIPTION|Date and time'
      for pv in self.pvs:
         line1 = line1 + '|' + pv['name'].strip()
         line2 = line2 + '|' + pv['description'].strip()
      self.output.write(line1+'\n')
      self.output.write(line2+'\n')
   
   def help(self):
      """ Opens a display window with help on the application. """
      top = Tk()
      top.title('Help on epicsLogger')
      text = Pmw.ScrolledText(top, text_font=self.fonts['help'], 
                              text_width=80, text_height=40)
      text.pack(fill=BOTH, expand=YES)
      text.insert(END, self.__doc__)
      text.insert(END, self.__init__.__doc__)

   def about(self):
      """ Opens a display window with information about the application. """
      Pmw.aboutversion('Version 1.0\nMay 10, 2002')
      Pmw.aboutcontact('Mark Rivers\n' +
                       'The University of Chicago\n' +
                       'rivers@cars.uchicago.edu\n')
      t = Pmw.AboutDialog(self.top, applicationname='epicsLogger')

   def timer(self):
      """ Private method """
      if (self.input_valid and self.logging_enabled):
         stime=time.strftime("%d-%b-%Y %H:%M:%S",time.localtime())
         line=stime
         for pv in self.pvs:
            pv['data'] = pv['epicsPV'].getw()
            line = line + ' ' + (pv['data_format'] % pv['data'])
         line = line + "\n"
         self.widgets['output'].insert(END, line)
         self.widgets['output'].yview_scroll(1, UNITS)
         if (self.output != None):
            line=stime
            for pv in self.pvs:
               line = line + "|" + (pv['data_format'] % pv['data']).strip()
            line = line + "\n"
            self.output.write(line)
         self.after_id=self.top.after(int(self.update_time*1000), self.timer)

if __name__ == '__main__':
   epicsLogger().mainloop()
