#!/usr/bin/python
import string
import sys
from beamline_support import *
import my_macros
from my_macros import *



global command_list,is_first
command_list = []

is_first = 1



def comm_cb(epics_args, user_args):
  global command_list,is_first
  
#  print waveform_to_string(epics_args['pv_value'])
  if (is_first == 0):
    command_list.append(waveform_to_string(epics_args['pv_value']))
  else:
    is_first = 0
  

def  process_input(s):
  input_tokens = string.split(s)
  if (len(input_tokens)>0):
    first_token = input_tokens[0]
    if (first_token == "q"): 
      sys.exit()
    else:
      if (len(input_tokens)>0):
        command_string = "%s(" % input_tokens[0]
        for i in range(1,len(input_tokens)):
          command_string = command_string + "\"" + input_tokens[i] + "\""
          if (i != (len(input_tokens)-1)):
            command_string = command_string + ","
        command_string = command_string + ")"
      try:
        print command_string
        from my_macros import *
        exec command_string
      except NameError:
        error_string = "Unknown command: " + command_string
        print error_string
      except SyntaxError:
        print "Syntax error"
      except KeyError:
        print "Key error"
      except TypeError:
        print "Type error"

def reload_macros():
  reload(my_macros)
  print "Macros reloaded\n"



def main():
  init_beamline()
  beamline = "john"
#  beamline = "x9"
  comm_pv = pvCreate(beamline + "_comm:command_s")
  add_callback(comm_pv,comm_cb,0)
  while 1:
    if (len(command_list) > 0):
      print "command list len " + str(len(command_list))
      process_input(command_list.pop(0))
      print "Command> "
    time.sleep(.05)

main()
