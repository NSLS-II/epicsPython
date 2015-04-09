import Tkinter
def myTkTop():
   """
   This routine creates a Tk() top-level widget and iconifies it.
   It is designed to work around a bug in Pmw.Blt.Graph which results in an
   error if Tk() is called more than once in a Python session.  Using this
   routine all "top-level" Tk widgets are actually children of this hidden
   Tk() widget.

   If there is no Tk() top level widget (i.e. Tkinter._default_root is None)
   then this routine creates a hidden Tk().

   This routine always returns a Toplevel() widget that is a child of the
   hidden Tk()
   """
   root = Tkinter._default_root
   if (root == None):
      root = Tkinter.Tk()
      root.title('Tk root')
      root.iconify()
   top = Tkinter.Toplevel(root)
   top.title('Tk top')
   return top
