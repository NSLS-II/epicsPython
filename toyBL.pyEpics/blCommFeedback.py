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
  
def execute_command(command_s):
  exec command_s


def process_commands(frequency):
  while (1):
    if (len(command_list) > 0):
      process_input(command_list.pop(0))
    time.sleep(frequency)      


def comm_cb(pvname=None, value=None, char_value=None, **kw):
  command = char_value
  command_list.append(command)




def process_input(command_string):
  if (command_string == ""):
    return
  blCommUtils.broadcast_output(time.ctime(time.time())+ "\n" + command_string+ "\n")
  if (command_string == "q"):
    sys.exit()
  print time.ctime(time.time()) + "\n" + command_string
  try:
#    daq_lib.set_field("program_state","Program Busy")
    execute_command(command_string)
  except NameError:
    error_string = "Unknown command: " + command_string
    print error_string
  except SyntaxError:
    print "Syntax error"
  except KeyError:
    print "Key error"
  except TypeError:
    print "Type error"
  except KeyboardInterrupt:
#    abort_data_collection()
    print "Interrupt caught by daq server\n"
#    daq_lib.set_field("program_state","Program Ready")

def setupBlComm():

  thread.start_new_thread(process_commands,(.05,))  
  blCommUtils.message_string_pv = PV(beamlineName + "_comm:message_string")
  comm_pv = PV(beamlineName + "_comm:command_s")
  comm_pv.put("\n",wait=True)
  comm_pv.add_callback(comm_cb)


def main():
  setupBlComm()

if __name__ == '__main__':
    main()

