#!/usr/bin/python
from Tkinter import *
from epicsMotorLabel import *
root = Tk()
m = epicsMotorLabel("x25a:mon",root,10)
m.pack()
epicsMotorLabel.is_drawn = 1
root.mainloop()
