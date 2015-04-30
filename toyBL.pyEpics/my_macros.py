import blCommUtils
#some examples

def hi_macro():
  print "hey from macros\n"
  blCommUtils.broadcast_output("broadcast hi")


def multiArgsTest(*args):
  print "args mac "
  for i in range (0,len(args)):
    print args[i]





    
