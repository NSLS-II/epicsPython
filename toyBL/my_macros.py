from beamline_support import *
from threading import Timer
import time

global timer_interval
beamline = "john"

#some examples

def hi_macro():
  print "hey from macros\n"



def motor_scan(motname,inc,numsteps,ctime,counter_num,end_code):  #end code - 0=startpos,1=peak
  scan_step = float(inc)
  count_time = float(ctime)
  numpoints = int(numsteps)
  scan_width = (numpoints-1) * scan_step
  half_scan_width = -scan_width /2.0
  current_filename = newfile("scan_results")
  if (1):  #maybe check something later
    results_file = open(current_filename,"w")    
    startpos = get_motor_pos(motname)
    print "startpos in scan = ",startpos
    mvr(motname,half_scan_width)    
#    plot_lib2.plot_init()
    for i in range (0,numpoints):
      count_list = get_counts(count_time)
#      for j in range(2,plot_lib2.number_of_counter_readouts):      
#        plot_lib2.plot_results(j-1,query_mot_pos(motname),count_list[j])
      results = "%f %d\n" % (get_motor_pos(motname),count_list[int(counter_num)-1])
      results_file.write(results)
      mvr(motname,scan_step)
    results_file.close()
    if (int(end_code) == 1):
      results_file = open(current_filename,"r")
      max_count = 0
      max_mot_pos = startpos
      for result_line in results_file.readlines():
        tokens = split(result_line)
        if (int(tokens[1]) > max_count):
          max_count = int(tokens[1])
          max_mot_pos = float(tokens[0])
      results_file.close()
      print "max count = ",max_count,"max pos = ",max_mot_pos
      mva(motname,max_mot_pos)        
    else:
      mva(motname,startpos)          




    
