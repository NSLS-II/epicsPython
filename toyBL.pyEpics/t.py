#!/usr/bin/ipython -i
import sys
import os
import time
import thread
import my_macros
from my_macros import *
import blCommUtils
from epics import PV

beamlineName = "john"
global command_list
command_list = []

#global message_string_pv
  


def comm_cb(pvname=None, value=None, char_value=None, **kw):
  command = char_value
  print command
  print kw["fish"]





def setupBlComm():

  comm_pv = PV(beamlineName + "_comm:command_s")
  comm_pv.put("\n",wait=True)
#  comm_pv.add_callback(comm_cb,{"fish":"bass"})
  comm_pv.add_callback(comm_cb,fish="bass")


def main():
  setupBlComm()
  while (1):
    time.sleep(1)

if __name__ == '__main__':
    main()

