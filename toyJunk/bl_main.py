#!/usr/bin/env python
import string
import sys
from beamline_support import *
import my_macros
from my_macros import *
###from SpecClient import SpecCommand
###from SpecClient import SpecClientError


#some examples
###global any_spec_command
###any_spec_command = SpecCommand.SpecCommand('','lobster:6789')


###def send_to_spec(command_s):
###  try:
###    any_spec_command.executeCommand(command_s)
###  except SpecClientError.SpecClientError:
###    print "Error executing spec command" + command_s



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
#  monitor_counter2()
  while 1:
    command = raw_input("Command> ")
    process_input(command)  

main()
