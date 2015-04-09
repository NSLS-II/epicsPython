#!/usr/bin/python
"""
This module provides enhancements to the Pmw.Blt.Graph widget.  It has the
following main features:

- A standalone plotting widget, BltPlot.BltPlot.  This widget has menus to:
   - Configure all of the plot characteristics
   - Save and restore the plot settings and data
   - Print the plot to a file or printer
  It has methods (BltPlot.plot and BltPlot.oplot) to create a new plot,
  to overplot more data, etc.  It is designed to provide a rough emulation of
  the command line plotting capabilities of IDL.
   
- GUI routines to configure all of the plot characteristics, such as axes,
  markers, legends, etc..  These routines work with any Pmw.Blt.Graph instance so
  they can be used from the standalone plotting widget in this package
  (BltPlot.BltPlot) or from any application that uses the Pmw.Blt.Graph widget.

- Routines to save and restore plot settings and data.

Author:          Mark Rivers
Created:         Sept. 18, 2002
Modifications:
  1.3   Nov 20 2002   M Newville  added BltExport function, and public method
                      BltPlot.export() to export image of graph to named
                      external file (available formats: gif, ppm, and also
                      png and jpg if Python Image library is available).
"""
from Tkinter import *
import tkColorChooser
import tkFileDialog
import Pmw
import os
import cPickle
import myTkTop

########################################################################
class BltPlot:
   """
   This class is used to build a standdalone plotting widget. It is designed
   to provide a rough emulation of the command line plotting capabilities of
   IDL.
   This widget has menus to:
      - Configure all of the plot characteristics
      - Save and restore the plot settings and data
      - Print the plot to a file or printer
   The configuration menus can also be accessed by double-clicking on the
   appropriate location of the plot, for example on the X axis.
   
   The only "public" functions are the constuctor (__init__) and the plot and
   oplot functions.

   The following example creates a plot of sin(x) and cos(x) with a legend:
   >>> from BltPlot import *
   >>> import Numeric
   >>> x = Numeric.arange(1000)/100.
   >>> y1 = Numeric.sin(x)
   >>> y2 = Numeric.cos(x)
   >>> p = BltPlot(x, y1, label='sin(x)', legend=1)
   >>> p.oplot(x, y2, label='cos(x)')
   """

   ########################################################################
   def __init__(self, xdata=None, ydata=None, exit_callback=None, **kw):
      """
      Creates a new plot widget.  After the plot widget is created it invokes
      the plot() function.  It accepts all of the parameters and keywords
      of the plot() function.
      It takes the following addtional keyword:
         exit_callback:
            This is an optional function that will be called when the BltPlot
            instance is destroyed.  The callback function will be called as:
               exit_callback(graph)
            where graph is the Pmw.Blt.Graph instance.
      """
      class widgets:
         pass
      self.exit_callback=exit_callback
      self.widgets = widgets()
      self.widgets.top = top = myTkTop.myTkTop()
      Wm.protocol(top, 'WM_DELETE_WINDOW', self.exit)
      self.settings_file = 'BltSettings.sav'
      frame = Frame(top, borderwidth=1, relief='raised')
      frame.pack(fill=X)
      self.widgets.mbar = mbar = Pmw.MenuBar(frame)
      mbar.pack(fill=X)

      self.graph = t = Pmw.Blt.Graph(self.widgets.top)
      t.pack(expand=YES, fill=BOTH)

      mbar.addmenu('File', '', side='left')
      mbar.addmenuitem('File', 'command', label='Save as...',
                      command=self.menu_save_as)
      mbar.addmenuitem('File', 'command', label='Save...',
                      command=self.menu_save)
      mbar.addmenuitem('File', 'command', label='Restore...',
                      command=self.menu_restore)
      mbar.addmenuitem('File', 'command', label='Print setup...',
                      command=lambda g=self.graph: BltPrintSetup(g))
      mbar.addmenuitem('File', 'command', label='Print...',
                      command=lambda g=self.graph: BltPrint(g))
      mbar.addmenuitem('File', 'command', label='Export...',
                      command=lambda g=self.graph, t=top: BltExport(g,t))
      mbar.addmenuitem('File', 'command', 'Exit', label='Exit',
                      command=self.exit)
      mbar.addmenu('Configure', '', side='left')
      mbar.addmenuitem('Configure', 'command', label='Graph...',
                      command=lambda g=self.graph: BltConfigureGraph(g))
      mbar.addmenuitem('Configure', 'command', label='Grid...',
                      command=lambda g=self.graph: BltConfigureGrid(g))
      mbar.addmenuitem('Configure', 'command', label='Legend...',
                      command=lambda g=self.graph: BltConfigureLegend(g))
      mbar.addcascademenu('Configure', 'Axis')
      mbar.addcascademenu('Configure', 'Element')
      mbar.addcascademenu('Configure', 'Marker')
      self.rebuild_menus()

      apply(self.plot, (xdata, ydata), kw)

   ########################################################################
   def exit(self):
      """ Private method """
      if (self.exit_callback != None):
         self.exit_callback(self.graph)
      self.widgets.top.destroy()


   ########################################################################
   def rebuild_menus(self):
      """ Private method """
      mbar = self.widgets.mbar
      mbar.deletemenu('Axis')
      mbar.addcascademenu('Configure', 'Axis')
      axes = self.graph.axis_names()
      for axis in axes:
         mbar.addmenuitem('Axis', 'command', label=axis.upper(),
            command=lambda g=self.graph, a=axis: BltConfigureAxis(g, a))
      mbar.deletemenu('Element')
      mbar.addcascademenu('Configure', 'Element')
      elements = self.graph.element_names()
      for element in elements:
         mbar.addmenuitem('Element', 'command', label=element,
            command=lambda g=self.graph, e=element: BltConfigureElement(g, e))
      mbar.deletemenu('Marker')
      mbar.addcascademenu('Configure', 'Marker')
      markers = self.graph.marker_names()
      for marker in markers:
         mbar.addmenuitem('Marker', 'command', label=marker,
            command=lambda g=self.graph, m=marker: BltConfigureMarker(g, m))

   ########################################################################
   def menu_save_as(self):
      """ Private method """
      file = tkFileDialog.asksaveasfilename(parent=self.widgets.top,
                                title='Settings file',
                                filetypes=[('Save files','*.sav'),
                                           ('All files','*')])
      if (file == ''): return
      self.settings_file = file
      BltSaveSettings(self.graph, self.settings_file)

   ########################################################################
   def menu_save(self):
      """ Private method """
      BltSaveSettings(self.graph, self.settings_file)

   ########################################################################
   def menu_restore(self):
      """ Private method """
      file = tkFileDialog.askopenfilename(parent=self.widgets.top,
                                title='Settings file',
                                filetypes=[('Save files','*.sav'),
                                           ('All files','*')])
      if (file == ''): return
      self.settings_file = file
      BltRestoreSettings(self.graph, self.settings_file)

   ########################################################################
   def plot(self, xdata, ydata=None, window_title='BltPlot', title=None,
            background='light grey', plotbackground='white',
            xmin="", xmax="", xtitle=None, xlog=0,
            xtickfont=('Helvetica','10'), xtitlefont=('Helvetica','11','bold'),
            ymin="", ymax="", ytitle=None, ylog=0,
            ytickfont=('Helvetica','10'), ytitlefont=('Helvetica','11','bold'),
            symbol="", linewidth=1, pixels=7, smooth="linear", color='black',
            label="line1", legend=0):
      """
      Creates a new plot, i.e. deletes any existing elements in the graph and
      adds the new data element.

      Inputs:
         xdata:
            A sequence (e.g. array, list, tuple) of the X axis coordinates of
            the data to be plotted.
            If xdata is input but ydata is not, then xdata are copied to ydata,
            i.e. xdata are the Y values.  In this case the X values are created
            as a simple sequence with xdata = tuple(range(len(ydata))).
            Pmw.Blt.Graph requires the xdata and ydata sequences to be tuples, so
            it is most efficient to pass them this way.  They will be
            converted to tuples if they are another type.

         ydata:
            A sequence (e.g. array, list, tuple) of the Y axis coordinates of
            the data to be plotted.

      Keywords:
         Most of the following keywords are simply the names of Pmw.Blt.Graph
         configuration parameters.  The user should consult the Pmw.Blt.Graph
         documentation for details.
         
         window_title:   The title in the title bar of the window.
         title:          The title of the graph, placed just above the graph
         background:     The color of the window background
         plotbackground: The color of the plot background
         xmin:           The minimum X value. Default is auto-scale.
         xmax:           The maximum X value. Default is auto-scale.
         xtitle:         The title of the X axis.
         xlog:           1 for log scale, 0 for linear scale.
         xtickfont:      The font for the X axis tick labels
         xtitlefont:     The font for the X axis title
         ymin:           The minimum Y value.  Default is auto-scale.
         ymax:           The maximum Y value. Default is auto-scale.
         ytitle:         The title of the Y axis.
         ylog:           1 for log scale, 0 for linear scale.
         ytickfont:      The font for the Y axis tick labels
         ytitlefont:     The font for the Y axis title
         symbol:         The plot symbol, e.g. 'circle', 'square'.
                         Default is no symbol.
         linewidth:      The width of the lines connecting the data points
         pixels:         The size of the plot symbols in pixels.
         smooth:         The smoothing algorithm for the line seqments
                         connecting data points.
         color:          The color of the plot symbols and line seqments.
         label:          A label for this graph element.  This is the string
                         that will appear in the legend and which is used
                         to configure this graph element.  Default='line1'.
         legend:         1=show legend, 0=hide legend.
         
      """

      self.widgets.top.title(window_title)
      g = self.graph
      elements = g.element_names()
      for element in elements:
         g.element_delete(element)
      # Double click event anywhere on widget
      self.widgets.top.bind('<Double-Button-1>', self.double_click)
      g.configure(title=title)
      g.configure(plotbackground=plotbackground)
      if (xdata == None): return
      xdata = tuple(xdata)
      if (ydata == None):
         ydata = xdata
         xdata = tuple(range(len(ydata)))
      else:
         ydata = tuple(ydata)
      g.line_create(label)
      g.element_configure(label, xdata=xdata, ydata=ydata,
                          color=color, symbol=symbol, linewidth=linewidth,
                          pixels=pixels, smooth=smooth)
      for event in ('<Enter>', '<Leave>', '<Double-Button-1>'):
         g.element_bind(label, event,
                       lambda e, s=self, t=label: s.element_mouse(e, t))
      g.legend_configure(hide=(not legend))
      for event in ('<Enter>', '<Leave>',
                     '<ButtonPress>', '<ButtonRelease>'):
         g.legend_bind(label, event, self.legend_mouse)
      g.xaxis_configure(min=xmin, max=xmax, title=xtitle, logscale=xlog,
                        tickfont=xtickfont, titlefont=xtitlefont)
      g.yaxis_configure(min=ymin, max=ymax, title=ytitle, logscale=ylog,
                        tickfont=ytickfont, titlefont=ytitlefont)
      self.rebuild_menus()

   ########################################################################
   def oplot(self, xdata=None, ydata=None, symbol="", linewidth=1, pixels=7,
             smooth="linear", color='black', label="line2"):
      """
      Plots an additional element on the existing plot, i.e. does not delete
      any existing elements in the graph.

      Inputs:
         Same as plot, described above.

      Keywords:
         Accepts a subset of the keywords used by plot(), described above.

         symbol:         The plot symbol, e.g. 'circle', 'square'.
                         Default is no symbol.
         linewidth:      The width of the lines connecting the data points
         pixels:         The size of the plot symbols in pixels.
         smooth:         The smoothing algorithm for the line seqments
                         connecting data points.
         color:          The color of the plot symbols and line seqments.
         label:          A label for this graph element.  This is the string
                         that will appear in the legend and which is used
                         to configure this graph element.
      """
      if (xdata == None): return
      xdata = tuple(xdata)
      if (ydata == None):
         ydata = xdata
         xdata = tuple(range(len(ydata)))
      else:
         ydata = tuple(ydata)
      g = self.graph
      g.line_create(label, color=color)
      g.element_configure(label, xdata=xdata, ydata=ydata,
                          color=color, symbol=symbol, linewidth=linewidth,
                          pixels=pixels, smooth=smooth)
      for event in ('<Enter>', '<Leave>', '<Double-Button-1>'):
         g.element_bind(label, event,
                       lambda e, s=self, t=label: s.element_mouse(e, t))
      for event in ('<Enter>', '<Leave>',
                     '<ButtonPress>', '<ButtonRelease>'):
         g.legend_bind(label, event, self.legend_mouse)
      self.rebuild_menus()

   ########################################################################
   def double_click(self, event):
      """ Private method """
      x = event.x; y=event.y
      g = self.graph
      if g.inside(x, y):
         BltConfigureGraph(self.graph)

      else:
         # Figure out what margin we are in
         s = self.graph.winfo_geometry()
         s=s.replace('x',' '); s=s.replace('+', ' '); w = s.split()
         wx = int(w[0]); wy = int(w[1])
         if (x <= g.extents('leftmargin')):
            BltConfigureAxis(self.graph, 'y')
         elif (x > (wx - g.extents('rightmargin'))):
            BltConfigureAxis(self.graph, 'y2')
         elif (y > (wy - g.extents('bottommargin'))):
            BltConfigureAxis(self.graph, 'x')
         else:
            BltConfigureAxis(self.graph, 'x2')

   ########################################################################
   def legend_mouse(self, event):
      """ Private method """
      g = self.graph
      tags = g.element_names()
      if (event.type == '2'):    # KeyPress event
         pos = g.legend_cget('position')
         if (pos[0] != '@'): return
         w = pos[1:].split(','); x = int(w[0]); y=int(w[1])
         if (event.keysym == 'Left'): x=x-1
         elif (event.keysym == 'Down'): y=y+1
         elif (event.keysym == 'Right'): x=x+1
         elif (event.keysym == 'Up'): y=y-1
         g.legend_configure(position='@'+str(x)+','+str(y))

      elif (event.type == '4'):
         # Button press event - start dragging if button 1
          if (event.num == 1):
             for tag in tags:  g.legend_bind(tag, '<Motion>', self.legend_mouse)

      elif (event.type == '5'):
         # Mouse button release event - stop dragging if button 1, menu if 3
         if (event.num == 1):
            for tag in tags:  g.legend_unbind(tag, '<Motion>')
         elif (event.num == 3): BltConfigureLegend(g)

      elif (event.type == '6'):  # Mouse drag event
         g.legend_configure(position='@'+str(event.x)+','+str(event.y))

      elif (event.type == '7'):  # Enter event - highlight and enable arrow keys
         for tag in tags: g.legend_activate(tag)
         self.widgets.top.bind('<KeyPress>', self.legend_mouse)

      elif (event.type == '8'):  # Leave event - unhighlight and disable arrow keys
         for tag in tags: g.legend_deactivate(tag)
         # There seems to be a bug that deactivate does not work after
         # drags.  Re-setting the background color fixes it
         g.legend_configure(background=g.legend_cget('background'))
         self.widgets.top.unbind('<KeyPress>')

   ########################################################################
   def element_mouse(self, event, element):
      """ Private method """
      g = self.graph
      if (event.type == '4'): # Double click event
         # NEED TO FIGURE OUT HOW TO "EAT" THIS EVENT SO IT DOES NOT GET
         # PASSED ON TO 'DOUBLE_CLICK" EVENT HANDLER
         BltConfigureElement(g, element)

      elif (event.type == '7'):  # Enter event - highlight
         #s = g.element_closest(event.x, event.y, element)
         #if (s == None): index=None
         #else: index=s['index']
         #g.element_activate(element, index)
         g.element_activate(element)

      elif (event.type == '8'):  # Leave event - unhighlight
         g.element_deactivate(element)

   ########################################################################
   def export(self, file='blt.gif',format=None):
      "Save graph image to GIF, PPM, (and possibly PNG, or JPG) output file"
      BltExport(self.graph, self.widgets.top, file=file,format=format)

########################################################################
class BltPrintSetup:
   """
   Creates a GUI window to configure the printing parameters of a Pmw.Blt.Graph
   object.
   """

   ########################################################################
   def __init__(self, graph, command=None):
      """
      Inputs:
         graph:
            A Pmw.Blt.Graph instance

        command:
            An optional callback function that will be called each time the
            printing parameters are modified.  The callback will be called as:
               command()
      """
      self.graph=graph
      BltPrintDefaults(graph)
      self.return_command = command
      self.widgets = {}
      cget = graph.postscript_cget
      self.widgets['top'] = t = Pmw.Dialog(parent=graph, command=self.commands,
                     buttons=('OK', 'Apply','Print', 'Print to file', 'Quit'),
                     title='BltPrintSetup')
      top = t.component('dialogchildsite')
      t = Label(top, text='Print setup',
                font=('Arial','12','bold')); t.pack()
      menu_option(self, top, 'decorations', 'Decorations:', ['No', 'Yes'],
                  int(cget('decorations')))
      menu_option(self, top, 'landscape', 'Orientation:',
                  ['Portrait', 'Landscape'],
                  int(cget('landscape')))
      menu_entry(self, top, 'width', 'Plot width:', cget('width'))
      menu_entry(self, top, 'height', 'Plot height:', cget('height'))
      menu_entry(self, top, 'paperwidth', 'Paper width:', cget('paperwidth'))
      menu_entry(self, top, 'paperheight', 'Paper height:', cget('paperheight'))
      menu_option(self, top, 'center', 'Center:', ['No', 'Yes'],
                  int(cget('center')))
      menu_option(self, top, 'preview', 'Preview:', ['No', 'Yes'],
                  int(cget('preview')))
      # There is a "previewformat" option, which appears to allow 'epsi' or
      # 'wmf' on Win32.  However, it gives an error if 'epsi' is used, and
      # the "previewformat" option does not exist at all on Linux, so skip it.
      #      menu_option(self, top, 'previewformat', 'Preview format:',
      #                  ['wmf', 'epsi'],
      #                  cget('previewformat'))
      menu_option(self, top, 'colormode', 'Color:', ['color', 'gray', 'mono'],
                  cget('colormode'))
      menu_entry(self, top, 'print_file', 'Print file:', graph.print_file)
      menu_entry(self, top, 'print_command', 'Print command:',
                 graph.print_command)

   ########################################################################
   def commands(self, button):
      """ Private method """
      widgets = self.widgets
      graph = self.graph
      configure = graph.postscript_configure
      if (button == 'OK') or (button == 'Apply'):
         configure(decorations=widgets['decorations'].index(Pmw.SELECT))
         configure(landscape=widgets['landscape'].index(Pmw.SELECT))
         configure(width=widgets['width'].get())
         configure(height=widgets['height'].get())
         configure(paperwidth=widgets['paperwidth'].get())
         configure(paperheight=widgets['paperheight'].get())
         configure(center=widgets['center'].index(Pmw.SELECT))
         configure(preview=widgets['preview'].index(Pmw.SELECT))
         # See comment above re: "previewformat"        
         # configure(previewformat=widgets['previewformat'].getcurselection())
         configure(colormode=widgets['colormode'].getcurselection())
         graph.print_file = widgets['print_file'].get()
         graph.print_command = widgets['print_command'].get()
         if (self.return_command != None): self.return_command()
      if (button == 'Print') or (button == 'Print to file'):
         graph.postscript_output(graph.file_name)
      if (button == 'Print'):
         BltPrint(graph)
      if (button != 'Apply'):
         self.widgets['top'].destroy()

########################################################################
def BltPrintDefaults(graph):
   """
   Creates the "print_command" or "print_file" attributes of the Pmw.Blt.Graph
   object if they do not already exist.  These are used by BltPrint().
   
   The first default for "print_command" is a command defined by the
   environment variable "PRINT_COMMAND".  If this environment variable does
   not exist, then the default is "lpr " on Unix, and "print " in Windows.

   The default for "print_file" is "Blt.ps".
   """
   if (hasattr(graph, 'print_command') == 0):
      graph.print_command = os.getenv('PRINT_COMMAND')
      if (graph.print_command == None):
         if (os.name == 'posix'):
            graph.print_command = 'lpr '
         else:
            graph.print_command = 'print '
   if (hasattr(graph, 'print_file') == 0):
      graph.print_file = 'Blt.ps'

########################################################################
def BltPrint(graph):
   """
   Prints the graph on a printer.  Uses the attributes graph.print_command and
   graph.print_file, which are added to Pmw.Blt.Graph by this BltPlot package.
   Default values for these attributes are created with BltPrintDefaults(). The
   attributes can be changed by the user.
   """
   BltPrintDefaults(graph)
   os.system(graph.print_command + ' ' + graph.print_file)

########################################################################
class BltConfigureAxis:
   """
   Creates a GUI window to configure an axis of a Pmw.Blt.Graph object.
   """

   ########################################################################
   def __init__(self, graph, axis, command=None):
      """
      Inputs:
         graph:
            A Pmw.Blt.Graph instance

         axis:
            The name of the axis, e.g. 'x', 'y', 'x2', 'y2'

         command:
            An optional callback function that will be called each time the
            legend is modified.  The callback will be called as:
               command(axis)
      """
      self.graph=graph
      self.axis=axis
      self.return_command=command
      self.widgets = {}
      cget = graph.axis_cget
      self.widgets['top'] = t = Pmw.Dialog(parent=graph, command=self.commands,
                                           buttons=('OK', 'Apply','Quit'),
                                           title='BltConfigureAxis')
      top = t.component('dialogchildsite')
      t = Label(top, text=axis.upper() + ' axis',
                font=('Arial','12','bold')); t.pack()
      menu_option(self, top, 'hide', 'Hide or show:', ['Show', 'Hide'],
                  int(cget(axis, 'hide')))
      menu_entry(self, top, 'title', 'Title:',
                 cget(axis, 'title'))
      menu_entry(self, top, 'titlefont', 'Title font:',
                 cget(axis, 'titlefont'))
      menu_color(self, top, 'titlecolor', 'Title color:',
                 cget(axis, 'titlecolor'))
      menu_entry(self, top, 'stepsize', 'Tick interval:',
                 cget(axis, 'stepsize'))
      menu_entry(self, top, 'subdivisions', 'Minor ticks:',
                 cget(axis, 'subdivisions'))
      menu_entry(self, top, 'ticklength', 'Tick length:',
                 cget(axis, 'ticklength'))
      menu_entry(self, top, 'tickfont', 'Tick font:',
                 cget(axis, 'tickfont'))
      menu_color(self, top, 'color', 'Axis color:',
                 cget(axis, 'color'))
      min = cget(axis, 'min')
      max = cget(axis, 'max')
      auto = ((min == "") and (max == ""))
      menu_option(self, top, 'auto', 'Limits:', ['Manual', 'Auto'], auto)
      menu_entry(self, top, 'min', 'Minimum:',
                 cget(axis, 'min'))
      menu_entry(self, top, 'max', 'Maximum:',
                 cget(axis, 'max'))
      menu_option(self, top, 'logscale', 'Scale:', ['Linear', 'Logarithmic'],
                  int(cget(axis, 'logscale')))

   ########################################################################
   def commands(self, button):
      """ Private method """
      widgets = self.widgets
      graph = self.graph
      axis = self.axis
      configure = graph.axis_configure
      if (button == 'OK') or (button == 'Apply'):
         configure(axis, title=widgets['title'].get())
         configure(axis, titlefont=widgets['titlefont'].get())
         configure(axis, titlecolor=widgets['titlecolor'].get())
         configure(axis, stepsize=widgets['stepsize'].get())
         configure(axis, subdivisions=widgets['subdivisions'].get())
         configure(axis, ticklength=widgets['ticklength'].get())
         configure(axis, color=widgets['color'].get())
         configure(axis, tickfont=widgets['tickfont'].get())
         configure(axis, hide=widgets['hide'].index(Pmw.SELECT))
         auto = widgets['auto'].index(Pmw.SELECT)
         if (auto):
            configure(axis, min="", max="")
         else:
            configure(axis, min=widgets['min'].get(), max=widgets['max'].get())
         configure(axis, logscale=widgets['logscale'].index(Pmw.SELECT))
         if (self.return_command != None): self.return_command(axis)
      if (button != 'Apply'):
         self.widgets['top'].destroy()

########################################################################
class BltConfigureLegend:
   """
   Creates a GUI window to configure the legend of a Pmw.Blt.Graph object.
   """

   ########################################################################
   def __init__(self, graph, command=None):
      """
      Inputs:
         graph:
            A Pmw.Blt.Graph instance

         command:
            An optional callback function that will be called each time the
            legend is modified.  The callback will be called as:
               command()
      """
      self.graph=graph
      self.return_command=command
      self.widgets = {}
      cget = graph.legend_cget
      self.widgets['top'] = t = Pmw.Dialog(parent=graph, command=self.commands,
                                           buttons=('OK', 'Apply','Quit'),
                                           title='BltConfigureLegend')
      top = t.component('dialogchildsite')
      t = Label(top, text='Legend configuration',
                font=('Arial','12','bold')); t.pack()
      initial=int(cget('hide'))
      menu_option(self, top, 'hide', 'Hide or show:', ['Show', 'Hide'],
                  int(cget('hide')))
      menu_entry(self, top, 'font', 'Legend font:', cget('font'))
      menu_color(self, top, 'foreground', 'Text color:', cget('foreground'))
      menu_color(self, top, 'background', 'Background color:', cget('background'))
      initial=cget('position')
      # Windows uses 'rightmargin' rather than 'right', etc.  Trim it.
      p = initial.find('margin')
      if (p != -1): initial=initial[:p]
      if (initial[0] == '@'): initial='manual'
      menu_option(self, top, 'position', 'Legend position:',
                       ['left', 'right', 'top', 'bottom', 'plotarea', 'manual'],
                       initial)
      menu_option(self, top, 'anchor', 'Legend anchor:',
                  ['center', 'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw'],
                  cget('anchor'))
      menu_entry(self, top, 'borderwidth', 'Border width:', cget('borderwidth'))
      menu_option(self, top, 'relief', 'Relief:',
                  ['raised', 'sunken', 'groove', 'ridge', 'flat'],
                  cget('relief'))

   ########################################################################
   def commands(self, button):
      """ Private method """
      widgets = self.widgets
      graph = self.graph
      configure = graph.legend_configure
      if (button == 'OK') or (button == 'Apply'):
         configure(hide=widgets['hide'].index(Pmw.SELECT))
         configure(font=widgets['font'].get())
         configure(foreground=widgets['foreground'].get())
         configure(background=widgets['background'].get())
         position=widgets['position'].getcurselection()
         if (position != 'manual'):
            configure(position=widgets['position'].getcurselection())
         configure(anchor=widgets['anchor'].getcurselection())
         configure(borderwidth=widgets['borderwidth'].get())
         configure(relief=widgets['relief'].getcurselection())
         if (self.return_command != None): self.return_command()
      if (button != 'Apply'):
         self.widgets['top'].destroy()

########################################################################
class BltConfigureGrid:
   """
   Creates a GUI window to configure the grid attributes in a Pmw.Blt.Graph
   object.
   """

   ########################################################################
   def __init__(self, graph, command=None):
      """
      Inputs:
         graph:
            A Pmw.Blt.Graph instance

         command:
            An optional callback function that will be called each time the
            grid is modified.  The callback will be called as:
               command()
      """
      self.graph=graph
      self.return_command=command
      self.widgets = {}
      cget = graph.grid_cget
      self.widgets['top'] = t = Pmw.Dialog(parent=graph, command=self.commands,
                     buttons=('OK', 'Apply','Quit'),
                     title='BltConfigureGrid')
      top = t.component('dialogchildsite')
      t = Label(top, text='Grid configuration',
                font=('Arial','12','bold')); t.pack()
      initial=int(cget('hide'))
      menu_option(self, top, 'hide', 'Hide or show:', ['Show', 'Hide'],
                  int(cget('hide')))
      menu_color(self, top, 'color', 'Grid color:', cget('color'))
      menu_entry(self, top, 'linewidth', 'Line width:', cget('linewidth'))
      menu_entry(self, top, 'dashes', 'Dash pattern:', cget('dashes'))
      menu_option(self, top, 'minor', 'Minor grid lines:',
                  ['No', 'Yes'],
                  int(cget('minor')))

   ########################################################################
   def commands(self, button):
      """ Private method """
      widgets = self.widgets
      graph = self.graph
      configure = graph.grid_configure
      if (button == 'OK') or (button == 'Apply'):
         configure(hide=widgets['hide'].index(Pmw.SELECT))
         configure(color=widgets['color'].get())
         configure(linewidth=widgets['linewidth'].get())
         configure(dashes=widgets['dashes'].get())
         configure(minor=widgets['minor'].index(Pmw.SELECT))
         if (self.return_command != None): self.return_command()
      if (button != 'Apply'):
         self.widgets['top'].destroy()

########################################################################
class BltConfigureElement:
   """
   Creates a GUI window to configure an "element" in a Pmw.Blt.Graph object.
   """

   ########################################################################
   def __init__(self, graph, element, command=None):
      """
      Inputs:
         graph:
            A Pmw.Blt.Graph instance

         element:
            The name of the element to configure.

         command:
            An optional callback function that will be called each time the
            element is modified.  The callback will be called as:
               command(element)
      """
         
      self.graph=graph
      self.return_command = command
      self.selected_elements = list(graph.element_names(element))
      self.selected_elements.sort()
      self.element = element = self.selected_elements[0]
      self.widgets = {}
      cget = graph.element_cget
      self.widgets['top'] = t = Pmw.Dialog(parent=graph, command=self.commands,
                     buttons=('OK', 'Apply','Quit'),
                     title='BltConfigureElement')
      top = t.component('dialogchildsite')
      t = Label(top, text=element + ' configuration',
                font=('Arial','12','bold')); t.pack()
      menu_option(self, top, 'hide', 'Hide or show:', ['Show', 'Hide'],
                  int(cget(element, 'hide')))
      menu_entry(self, top, 'label', 'Label:', cget(element, 'label'))
      menu_entry(self, top, 'linewidth', 'Line width:', cget(element, 'linewidth'))
      menu_entry(self, top, 'dashes', 'Line pattern:', cget(element, 'dashes'))
      line_color = cget(element, 'color')
      menu_color(self, top, 'color', 'Line color:', line_color)
      initial = cget(element, 'symbol')
      menu_option(self, top, 'symbol', 'Symbol:',
                       ["none", "square", "circle", "diamond", "plus",
                        "cross", "splus", "scross", "triangle"],
                       initial)
      menu_entry(self, top, 'pixels', 'Symbol size:', cget(element, 'pixels'))
      menu_color(self, top, 'fill', 'Symbol fill color:', 
                     cget(element, 'fill'), defcolor=line_color)
      menu_color(self, top, 'outline', 'Outline color:',
                 cget(element, 'outline'), defcolor=line_color)
      menu_entry(self, top, 'outlinewidth', 'Outline width:',
                 cget(element, 'outlinewidth'))
      initial=cget(element, 'smooth')
      menu_option(self, top, 'smooth', 'Line smoothing:',
                  ['linear', 'quadratic', 'step', 'natural'],
                  initial)

   ########################################################################
   def commands(self, button):
      """ Private method """
      widgets = self.widgets
      graph = self.graph
      configure = graph.element_configure
      if (button == 'OK') or (button == 'Apply'):
         for element in self.selected_elements:
            configure(element, hide=widgets['hide'].index(Pmw.SELECT))
            configure(element, label=widgets['label'].get())
            configure(element, linewidth=widgets['linewidth'].get())
            configure(element, dashes=widgets['dashes'].get())
            configure(element, color=widgets['color'].get())
            configure(element, symbol=widgets['symbol'].getcurselection())
            configure(element, pixels=widgets['pixels'].get())
            configure(element, fill=widgets['fill'].get())
            configure(element, outline=widgets['outline'].get())
            configure(element, outlinewidth=widgets['outlinewidth'].get())
            configure(element, smooth=widgets['smooth'].getcurselection())
            if (self.return_command != None): self.return_command(element)
      if (button != 'Apply'):
         self.widgets['top'].destroy()

########################################################################
class BltConfigureMarker:
   """
   Creates a GUI window to configure one or more markers in a Pmw.Blt.Graph object.
   """


   ########################################################################
   def __init__(self, graph, marker, command=None):
      """
      Inputs:
         graph:
            A Pmw.Blt.Graph instance

         marker:
            The name of the marker to configure.  The marker name can contain
            wildcards, in which case all markers matching the pattern will be
            modified.  Only the name of the first marker will be displayed in
            the window.

         command:
            An optional callback function that will be called each time the
            marker is modified.  The callback will be called as:
               command(marker)
      """
      class widgets:
         pass
      self.graph=graph
      self.return_command = command
      self.selected_markers = list(graph.marker_names(marker))
      self.selected_markers.sort()
      self.marker = marker = self.selected_markers[0]
      self.widgets = {}
      self.type = graph.marker_type(self.marker)
      cget = graph.marker_cget
      self.widgets['top'] = t = Pmw.Dialog(parent=graph, command=self.commands,
                                           buttons=('OK', 'Apply','Quit'),
                                           title='BltConfigureMarker')
      top = t.component('dialogchildsite')
      t = Label(top, text=marker + ' configuration',
                font=('Arial','12','bold')); t.pack()
      menu_option(self, top, 'hide', 'Hide or show:', ['Show', 'Hide'],
           int(cget(marker, 'hide')))
      menu_entry(self, top, 'coords', 'Coordinates:',
              cget(marker, 'coords'))
      # Windows returns 'LineMarker', Linux returns 'line'
      if (self.type == 'LineMarker') or (self.type == 'line'):
         menu_color(self, top, 'outline', 'Foreground color:',
                 cget(marker, 'outline'))
         menu_color(self, top, 'fill', 'Background color:',
                 cget(marker, 'fill'))
         menu_entry(self, top, 'linewidth', 'Line width:',
                 cget(marker, 'linewidth'))
         menu_entry(self, top, 'dashes', 'Line pattern:',
                 cget(marker, 'dashes'))
      # Windows returns 'TextMarker', Linux returns 'text'
      if (self.type == 'TextMarker') or (self.type == 'text'):
         menu_text(self, top, 'text', 'Text:',
                 cget(marker, 'text'))
         menu_entry(self, top, 'font', 'Font:',
                 cget(marker, 'font'))
         menu_color(self, top, 'outline', 'Text color:',
                 cget(marker, 'outline'))
         menu_color(self, top, 'fill', 'Background color:',
                 cget(marker, 'fill'))
         menu_color(self, top, 'shadow', 'Shadow color:',
                 cget(marker, 'shadow'))
         menu_option(self, top, 'anchor', 'Text anchor:',
                 ['center', 'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw'],
                 cget(marker, 'anchor'))
         menu_option(self, top, 'justify', 'Text justfication:',
                 ['left', 'right', 'center'],
                 cget(marker, 'justify'))
         menu_entry(self, top, 'rotate', 'Rotate:',
                 cget(marker, 'rotate'))

   ########################################################################
   def commands(self, button):
      """ Private method """
      widgets = self.widgets
      graph = self.graph
      configure = graph.marker_configure
      if (button == 'OK') or (button == 'Apply'):
         for marker in self.selected_markers:
            configure(marker, hide=widgets['hide'].index(Pmw.SELECT))
            # Only change coordinates of first marker
            configure(self.selected_markers[0], coords=widgets['coords'].get())
            if (self.type == 'LineMarker') or (self.type == 'line'):
               configure(marker, outline=widgets['outline'].get())
               configure(marker, fill=widgets['fill'].get())
               configure(marker, linewidth=widgets['linewidth'].get())
               configure(marker, dashes=widgets['dashes'].get())
            elif (self.type == 'TextMarker') or (self.type == 'text'):
               configure(marker, text=widgets['text'].get(1.0, END))
               configure(marker, font=widgets['font'].get())
               configure(marker, outline=widgets['outline'].get())
               configure(marker, fill=widgets['fill'].get())
               configure(marker, shadow=widgets['shadow'].get())
               configure(marker, anchor=widgets['anchor'].getcurselection())
               configure(marker, justify=widgets['justify'].getcurselection())
               configure(marker, rotate=widgets['rotate'].get())
         if (self.return_command != None): self.return_command(marker)
      if (button != 'Apply'):
         self.widgets['top'].destroy()

########################################################################
class BltConfigureGraph:
   """
   Creates a GUI window to configure the primary graph attributes in a
   Pmw.Blt.Graph object.  The attributes include the background colors, title
   font, relief, etc.
   """

   ########################################################################
   def __init__(self, graph, command=None):
      """
      Inputs:
         graph:
            A Pmw.Blt.Graph instance

         command:
            An optional callback function that will be called each time the
            graph attributes are modified.  The callback will be called as:
               command()
      """
      self.graph=graph
      self.return_command = command
      self.widgets = {}
      cget = graph.cget
      self.widgets['top'] = t = Pmw.Dialog(parent=graph, command=self.commands,
                                           buttons=('OK', 'Apply','Quit'),
                                           title='BltConfigureGraph')
      top = t.component('dialogchildsite')
      t = Label(top, text='Graph configuration',
                font=('Arial','12','bold')); t.pack()
      lwidth=25
      menu_color(self, top, 'background', 'Widget background color:',
                 cget('background'), label_width=lwidth)
      menu_color(self, top, 'plotbackground', 'Plot background color:',
                 cget('plotbackground'), label_width=lwidth)
      menu_entry(self, top, 'title', 'Title:', cget('title'),
                 label_width=lwidth)
      menu_entry(self, top, 'font', 'Title font:', cget('font'),
                 label_width=lwidth)
      menu_entry(self, top, 'borderwidth', 'Border width:', cget('borderwidth'),
                 label_width=lwidth)
      menu_option(self, top, 'relief', 'Relief:',
                  ['raised', 'sunken', 'groove', 'ridge', 'flat'],
                  cget('relief'), label_width=lwidth)
      menu_entry(self, top, 'plotborderwidth', 'Plot border width:',
                 cget('plotborderwidth'), label_width=lwidth)
      menu_option(self, top, 'plotrelief', 'Plot relief:',
                  ['raised', 'sunken', 'groove', 'ridge', 'flat'],
                  cget('plotrelief'), label_width=lwidth)

   ########################################################################
   def commands(self, button):
      """ Private method """
      widgets = self.widgets
      graph = self.graph
      configure = graph.configure
      if (button == 'OK') or (button == 'Apply'):
         configure(background=widgets['background'].get())
         configure(plotbackground=widgets['plotbackground'].get())
         configure(title=widgets['title'].get())
         configure(font=widgets['font'].get())
         configure(borderwidth=widgets['borderwidth'].get())
         configure(relief=widgets['relief'].getcurselection())
         configure(plotborderwidth=widgets['plotborderwidth'].get())
         configure(plotrelief=widgets['plotrelief'].getcurselection())
         if (self.return_command != None): self.return_command()
      if (button != 'Apply'):
         self.widgets['top'].destroy()

########################################################################
def menu_entry(self, parent, attribute, label, value, validate=None,
               label_width=20, entry_width=20):
   """ Private method """
   t = Pmw.EntryField(parent, value=value,
                      labelpos=W, label_text=label, label_width=label_width,
                      label_anchor=E,
                      entry_width=entry_width, entry_justify=LEFT,
                      validate=validate,
                      command=lambda s=self: s.commands('Apply'))
   t.pack(anchor=W)
   self.widgets[attribute] = t

########################################################################
def menu_text(self, parent, attribute, label, value, validate=None,
               label_width=20, text_width=20, text_height=3):
   """ Private method """
   row = Frame(parent); row.pack(anchor=W)
   label = Label(row, anchor=E, text=label, width=label_width);
   label.pack(side=LEFT)
   text = Text(row, width=text_width, height=text_height)
   text.insert(INSERT, value)
   text.pack(side=LEFT)
   self.widgets[attribute] = text

########################################################################
def menu_option(self, parent, attribute, label, items, initial,
                label_width=20):
   """ Private method """
   t = Pmw.OptionMenu(parent, items=items, initialitem=initial,
                      labelpos=W, label_text=label, label_width=label_width,
                      label_anchor=E,
                      command=lambda v,s=self: s.commands('Apply'))
   t.pack(anchor=W)
   self.widgets[attribute] = t

########################################################################
def menu_color(self, parent, attribute, label, value, label_width=20,
               entry_width=20, defcolor=None):
   """ Private method """
   row = Frame(parent); row.pack(anchor=W, pady=2)
   t = Pmw.EntryField(row, value=value,
                      labelpos=W, label_text=label, label_width=label_width,
                      label_anchor=E,
                      entry_width=entry_width, entry_justify=LEFT,
                      command=lambda s=self, a=attribute: new_color(s, a))
   t.pack(side=LEFT)
   self.widgets[attribute] = t
   bcolor = value
   if (value == 'defcolor') and (defcolor != None): bcolor=defcolor
   if (value == ""): bcolor=None
   t = Button(row, background=bcolor, width=5, height=1,
              command=lambda s=self,v=value,a=attribute,d=defcolor:
              ask_color(s, v, a, defcolor=d))
   t.pack(side=LEFT, padx=5)
   self.widgets[attribute+'_color'] = t

########################################################################
def new_color(self, attribute):
   """ Private method """
   c = self.widgets[attribute].get()
   if (c == ""): c = None
   self.widgets[attribute+'_color'].configure(background=c)
   self.commands('Apply')

########################################################################
def ask_color(self, value, attribute, defcolor=None):
   """ Private method """
   if (value == 'defcolor') and (defcolor != None): value=defcolor
   c = tkColorChooser.askcolor(value, parent=self.graph)
   c = c[1]
   if (c != None):
      self.widgets[attribute].setentry(c)
      self.widgets[attribute+'_color'].configure(background=c)
      self.commands('Apply')

########################################################################
class BltSettings:
   """
   Class used for saving and restoring settings.
   """

   ########################################################################
   def __init__(self):
      pass

########################################################################
def BltGetSettings(graph, main=1, legend=1, grid=1, axes=1,
                   elements=1, data=1, markers=1, postscript=1):
   """
   Returns a BltSettings class containing the current settings of the
   Pmw.Blt.Graph instance.

   This function is used by BltSaveSettings(), but it could be called by other
   applications that use different methods to save and restore settings.

   Inputs:
      graph:
         A Pmw.Blt.Graph instance

   Keywords:
      The following keywords control which settings are returned in the
      BltSettings instance.
      The default for each keyword is 1, meaning that those settings are saved.
      Set the keyword to 0 to avoid returning those settings.

      main:
         The main graph settings, i.e. those that are configured with
         BltConfigureGraph.
         
      legend:
         The legend settings.

      grid:
         The grid settings.

      axes:
         The axis settings.

      elements:
         The element settings, but not including the element data.

      data:
         The graph data.

      markers:
         The marker data.

      postscript:
         The printing settings.
   """
   s = BltSettings()
   if (main == 1):
      s.graph_config = _get_settings(graph.configure())
   if (legend == 1):
      s.legend_config = _get_settings(graph.legend_configure())
   if (grid == 1):
      s.grid_config = _get_settings(graph.grid_configure())
   if (axes == 1):
      s.axis_names = graph.axis_names()
      s.axis_config = {}
      for axis in s.axis_names:
         s.axis_config[axis] = _get_settings(
                                    graph.axis_configure(axis))
   if (elements == 1):
      s.element_names = graph.element_names()
      s.element_config = {}
      for element in s.element_names:
         s.element_config[element] = _get_settings(
                                       graph.element_configure(element))
         if (data != 1):
            # The 'x' and 'y' keys seem to exist on Windows but not Linux
            if (s.element_config[element].has_key('x')):
               del s.element_config[element]['x']
            if (s.element_config[element].has_key('y')):
               del s.element_config[element]['y']
            del s.element_config[element]['xdata']
            del s.element_config[element]['ydata']
            del s.element_config[element]['data']
   if (markers == 1):
      s.marker_names = graph.marker_names()
      s.marker_config = {}
      for marker in s.marker_names:
         s.marker_config[marker] = _get_settings(
                                       graph.marker_configure(marker))
         # We don't want to save or restore the "name" parameter, it is
         # redundant since it is the name of the marker, and it is an error to
         # restore it
         del s.marker_config[marker]['name']
   if (postscript == 1):
      s.postscript_config = _get_settings(graph.postscript_configure())
      BltPrintDefaults(graph)
      s.print_config = {'print_file': graph.print_file,
                        'print_command': graph.print_command}

   return s

########################################################################
def _get_settings(dict):
   """ Private method """
   t = {}
   for key in dict.keys():
      t[key] = dict[key][-1]
   return t

########################################################################
def BltSaveSettings(graph, file, **kw):
   """
   Save settings for a Pmw.Blt.Graph object to a file .  Settings are
   restored with BltRestoreSettings().
   
   These settings may or may not include the data itself.

   Inputs:
      graph:
         A Pmw.Blt.Graph instance

      file:
         The name of a file containing the settings saved previously with
         BltSaveSettings().

   Keywords:
      Keywords are used to control which settings are saved.  These keywords
      are simply passed to BltGetSettings().  See the documentation for that
      function for details.
   """
   s = apply(BltGetSettings, (graph,), kw)
   fp = open(file, 'w')
   cPickle.dump(s, fp)
   fp.close

########################################################################
def BltLoadSettings(graph, s):
   """
   Loads settings to a Pmw.Blt.Graph object from a BltSettings instance.
   This function is used by BltRestoreSettings(), but it could be called by other
   applications that use different methods to save and restore settings.

   Inputs:
      graph:
         A Pmw.Blt.Graph instance

      s:
         A BltSettings instance.
   """
   if (hasattr(s, 'graph_config')):
       _restore_settings(s.graph_config, graph.configure)
   if (hasattr(s, 'legend_config')):
      _restore_settings(s.legend_config, graph.legend_configure)
   if (hasattr(s, 'grid_config')):
      _restore_settings(s.grid_config, graph.grid_configure)
   if (hasattr(s, 'axis_names')):
      for axis in s.axis_names:
         _restore_settings(
            s.axis_config[axis], graph.axis_configure, axis)
   if (hasattr(s, 'element_names')):
      for element in s.element_names:
         _restore_settings(
            s.element_config[element], graph.element_configure, element)
   if (hasattr(s, 'marker_names')):
      for marker in s.marker_names:
         _restore_settings(
            s.marker_config[marker], graph.marker_configure, marker)
   if (hasattr(s, 'postscript_config')):
      _restore_settings(s.postscript_config, graph.postscript_configure)
   if (hasattr(s, 'print_config')):
      graph.print_file = s.print_config['print_file']
      graph.print_command = s.print_config['print_command']

########################################################################
def _restore_settings(dict, function, *args):
   """ Private method """
   for key in dict.keys():
      kw = {key: dict[key]}
      try:
         apply(function, args, kw)
      except:
         pass

########################################################################
def BltRestoreSettings(graph, file):
   """
   Restores settings saved in a file to a Pmw.Blt.Graph object.  Settings are
   saved with BltSaveSettings().
   
   These settings may or may not include the data itself.

   Inputs:
      graph:
         A Pmw.Blt.Graph instance

      file:
         The name of a file containing the settings saved previously with
         BltSaveSettings().
   
   """
   fp = open(file, 'r')
   s = cPickle.load(fp)
   BltLoadSettings(graph, s)
   ########################################################################

def BltExport(graph, master, file=None, format=None):
   """
   save graph image to GIF, PPM, (and possibly PNG, or JPG) output file.
   
     BltExport(graph, master, file='my.png', format='png')

   where
     graph    Blt.graph
     master   toplevel widget containing graph
     file     name of output file
     format   output format ('gif','ppm') and possibly ('png', 'jpg')
    
   if format is not recognized, no output is written.
   if file=None (or is not supplied), a Tk file dialog is presented.
   
   notes: saving PNG or JPG requires the Python Imaging Library,
          and uses a temporary PPM file named '_blt_image.ppm'
          (since Tk PhotoImage has a write() method that takes a
          filename, not a file instance!!)
   """

   # ImgForms keeps formats and corresponding way of saving
   import string
   ImgForms = {'gif':None, 'ppm': None}

   try:   # if we can import Image, add png and jpg image types
      import Image
      Image_open = Image.open
      ImgForms.update({ 'png':'PNG', 'jpg':'JPEG', 'jpeg':'JPEG'})
      # these image require Image extension and a temporary file
      _temp_   = '_blt_image.tmp'
   except:
      Image_open = None
   #
   types   = ImgForms.keys() ; types.sort()
   img_list= string.join(map(lambda x:"*.%s" % (x), types))

   if (not file):
      file = tkFileDialog.asksaveasfilename(parent=master,
                                            title='Export to image file',
                                            filetypes=[('Image Files',img_list),
                                                       ('All files','*')])
      
   if (file == ''): return

   # if the format was not explicit, get it from file extension
   if (not format):    format = file.split('.')[-1].lower()
   if (format not in ImgForms.keys()): format = 'gif'

   out = (file,format)       # save output file / format

   if (format in ImgForms.keys()):
      if (ImgForms[format]):  out = (_temp_,  'ppm')

      # save image (possibly to temporary file)
      if (graph):
         img = PhotoImage(master=master, name='blt_snap')
         graph.snap(img)
         img.write(out[0],out[1])

         # if png or jpg is needed, use Image library
         # to convert temporary PPM to PNG/JPEG
         if (ImgForms[format] and Image_open):
            im = Image_open(_temp_)
            im.save(file, ImgForms[format])
            os.unlink(_temp_)

   ########################################################################


