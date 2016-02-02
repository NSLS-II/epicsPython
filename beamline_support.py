#John Skinner
#beamline support library
#Common motor, counter, and scanning utilities
#code based on GSECARS Python Library from Mark Rivers

from string import *
import sys

from epicsScanParms import *
from epicsMotor import *
from epicsScaler import *
from epicsScan import *
from epicsPV import *
import time

from CaChannel import *


global beamline_designation,motor_dict,soft_motor_list,scan_list,counter_dict,motor_channel_dict,counter_channel_dict,number_of_counter_readouts,scanparms_channel_dict,beamline_scan_record,scan_active_pv,scan_reference_counter,scan_detector_count,datafile_name,pvChannelDict

motor_dict = {}
counter_dict = {}
pvLookupDict = {}
motor_channel_dict = {}
counter_channel_dict = {}
scanparms_channel_dict = {}
pvChannelDict = {}

scan_list = []
soft_motor_list = []

number_of_counter_readouts = 6
scan_detector_count = 4
datafile_name = ""



#####
# Start of commands
#####


#convenience to set a pv value given the name
def set_any_epics_pv(pv_prefix,field_name,value): #this does not use beamline designation
  pvname = "%s.%s" % (pv_prefix,field_name)
  try:
    if (not pvChannelDict.has_key(pvname)):
      pvChannelDict[pvname] = PVchannel = epicsPV(pvname)
    if (pvChannelDict[pvname] != None):
      pvChannelDict[pvname].putw(value)
  except CaChannelException, status:
    print ca.message(status)
    print "\n\nHandled Epics Error in set pv " + pvname + "\n\n"


#convenience to set a pv value given the name
def get_any_epics_pv(pv_prefix,field_name): #this does not use beamline designation
  pvname = "%s.%s" % (pv_prefix,field_name)
  try:
    if (not pvChannelDict.has_key(pvname)):
      pvChannelDict[pvname] = PVchannel = epicsPV(pvname)
    if (pvChannelDict[pvname] != None):
      pv_val = pvChannelDict[pvname].getw()
    else:
      pv_val = None
    return pv_val
  except CaChannelException, status:
    print ca.message(status)
    print "\n\nHandled Epics Error in get pv " + pvname + "\n\n"

#initializes epics motors and counter based on the file pointed to by $EPICS_BEAMLINE_INFO
#Below this line is an example beamline info file, (remove one '#' off the front of each line)
##beamline_designation
#x12c
##real motors
#tv1 table_vert1
#tv2 table_vert2
#mon monochromator
##virtual motors
#tbv table_vert
##scanned motors
#mon
#tbv
##counters
#scaler1 main_counter
def init_beamline():
  read_db()
  init_motors()
#  initControlPVs()
#  init_counters()
#  init_scanparms()
  

#relative simultaneous move of multiple motors
#usage example: mvr mon 1.0 tv2 0.5
def mvr(*args):
  multimot_list = {}
  movedist_list = {}
  try:
    for i in range(0,len(args),2):
      multimot_list[i/2] = beamline_designation+args[i]
      movedist_list[i/2] = float(args[i+1])
    for i in range(0,(len(args)/2)):
      motor_channel_dict[multimot_list[i]].move(movedist_list[i],relative=1)
    for i in range(0,(len(args)/2)):
      motor_channel_dict[multimot_list[i]].wait()
  except epicsMotorException,status:
    print "CAUGHT MOTOR EXCEPTION"
    try:
      ii = 0
      status_string = ""
      while(1):
        status_string = status_string + str(status[ii])
        ii = ii + 1
    except IndexError:
      print status_string
      raise epicsMotorException, status_string


#absolute simultaneous move of multiple motors
#usage example: mva mon 1.0 tv2 0.5
def mva(*args):
  multimot_list = {}
  movedist_list = {}
  try:
    for i in range(0,len(args),2):
      multimot_list[i/2] = beamline_designation+args[i]
      movedist_list[i/2] = float(args[i+1])
    for i in range(0,(len(args)/2)):
      motor_channel_dict[multimot_list[i]].move(movedist_list[i])
    for i in range(0,(len(args)/2)):
      motor_channel_dict[multimot_list[i]].wait()
  except epicsMotorException,status:
    print "CAUGHT MOTOR EXCEPTION"
    try:
      ii = 0
      status_string = ""
      while(1):
        status_string = status_string + str(status[ii])
        ii = ii + 1
    except IndexError:
      print status_string
      raise epicsMotorException, status_string


def get_motor_pos(motcode):
  return motor_channel_dict[beamline_designation+motcode].get_position(readback=1)

def stop_motors():
  for key in motor_channel_dict.keys():
    motor_channel_dict[key].stop()

#count for time_to_count seconds
def do_count(time_to_count=0):
  if (time_to_count == 0):  
    counter_channel_dict[counter_dict["main_counter"]].start()
  else:
    counter_channel_dict[counter_dict["main_counter"]].start(time_to_count)
  counter_channel_dict[counter_dict["main_counter"]].wait()
#  print_counts()

def ri(): #read intensity legacy call
  do_count()
  print_counts()

def set_count_time(time_to_count):
  counter_channel_dict[counter_dict["main_counter"]].setTime(time_to_count)

def get_count_time():
  return counter_channel_dict[counter_dict["main_counter"]].getTime()

def get_counts(time_to_count=0):
  do_count(time_to_count)
#  print counter_channel_dict[counter_dict["main_counter"]].read()[1:] #chop first channel
  return counter_channel_dict[counter_dict["main_counter"]].read()

def get_latest_counts():
  return counter_channel_dict[counter_dict["main_counter"]].read()

def set_scan_fly(motcode):
  index_string = "%s:%s:scanParms" % (beamline_designation,motcode)
  scanparms_channel_dict[index_string].set_fly()


def set_scan_linear(motcode):
  index_string = "%s:%s:scanParms" % (beamline_designation,motcode)
  scanparms_channel_dict[index_string].set_linear()


def set_scan_relative(motcode):
  index_string = "%s:%s:scanParms" % (beamline_designation,motcode)
  scanparms_channel_dict[index_string].set_relative()
  
def set_scan_absolute(motcode):
  index_string = "%s:%s:scanParms" % (beamline_designation,motcode)
  scanparms_channel_dict[index_string].set_absolute()
  

def set_scanpoints(motcode,numpoints):
  index_string = "%s:%s:scanParms" % (beamline_designation,motcode)
  scanparms_channel_dict[index_string].set_scanpoints(numpoints)

def get_scan_points(motcode):
  index_string = "%s:%s:scanParms" % (beamline_designation,motcode)
  return scanparms_channel_dict[index_string].get_scanpoints()


def set_scanstart(motcode,posn):
  index_string = "%s:%s:scanParms" % (beamline_designation,motcode)
  scanparms_channel_dict[index_string].set_start(posn)


def set_scanend(motcode,posn):
  index_string = "%s:%s:scanParms" % (beamline_designation,motcode)
  scanparms_channel_dict[index_string].set_end(posn)


def set_scanstepsize(motcode,stepsize): 
  index_string = "%s:%s:scanParms" % (beamline_designation,motcode)
  scanparms_channel_dict[index_string].set_scanstepsize(stepsize)


def get_scanstepsize(motcode):
  index_string = "%s:%s:scanParms" % (beamline_designation,motcode)
  return scanparms_channel_dict[index_string].get_scanstepsize()


def set_scan_reference_counter(counter_number):
  scan_reference_counter.putw(counter_number)


def set_scan_after_start(motcode):
  index_string = "%s:%s:scanParms" % (beamline_designation,motcode)
  scanparms_channel_dict[index_string].set_after_start()

def set_scan_after_end(motcode):
  index_string = "%s:%s:scanParms" % (beamline_designation,motcode)
  scanparms_channel_dict[index_string].set_after_end()

def set_scan_after_before_scan(motcode):
  index_string = "%s:%s:scanParms" % (beamline_designation,motcode)
  scanparms_channel_dict[index_string].set_after_before_scan()

def set_scan_after_peak(motcode):
  index_string = "%s:%s:scanParms" % (beamline_designation,motcode)
  scanparms_channel_dict[index_string].set_after_peak()

def load_scan_parms(motcode):
  index_string = "%s:%s:scanParms" % (beamline_designation,motcode)
  scanparms_channel_dict[index_string].load()  

def load_and_go_scan_parms(motcode):
  index_string = "%s:%s:scanParms" % (beamline_designation,motcode)
  scanparms_channel_dict[index_string].loadAndGo()  


#do a peak scan of one motor optimizing on counter_num
def peakScan(motcode,counter_num):
  set_scan_relative(motcode)        
  set_scan_reference_counter(counter_num)
  set_scan_after_peak(motcode)
  load_scan_parms(motcode)
  GScan(motcode)

def mvf(motcode,counter_num): #legacy
  peakScan(motcode,counter_num)

    
#scan a motor relative to current position and leave the motor at that position when done
def dscan(motcode):
  set_scan_relative(motcode)        
  set_scan_after_before_scan(motcode)
  load_scan_parms(motcode)
  GScan(motcode)
    

#scan a motor from start to end and leave the motor where it was before command was issued
def ascan(motcode):
  set_scan_absolute(motcode)        
  set_scan_after_before_scan(motcode)
  load_scan_parms(motcode)
  GScan(motcode)
    


def add_callback(pv,callback_name,user_args):
  pv.add_masked_array_event(ca.dbf_type_to_DBR_STS(pv.field_type()),None, ca.DBE_VALUE | ca.DBE_ALARM, callback_name,user_args)
  pv.pend_io(1.0)


def pvCreate(pvname,connCB=None):
  pv = None
  try:
    pv = epicsPV(pvname,connCB)
  except CaChannelException, status:
    print ca.message(status)
    print "\n\nCould not create PV " + pvname + "\n\n"
  return pv


def pvGet(pv):
  if (ca.dbf_text(pv.field_type()) == "DBF_CHAR"):
    return waveform_to_string(pv.getw())
  elif (ca.dbf_text(pv.field_type()) == "DBF_ENUM"):
    return pv.getw(ca.DBR_STRING)
  else:
    return pv.getw()


def pvPut(pv,val):
  pv.putw(val)


def pvClose(pv):
  del pv


def print_counts():
  count_result_list = []
  count_result_list = counter_channel_dict[counter_dict["main_counter"]].read()
  for i in range (0,number_of_counter_readouts):
    print "channel %d: %d" % (i,count_result_list[i])

def wait_for_scan():
  time.sleep(1)
  while (1):
    try:
#      scan_done_stat = scan_active_pv.getw()
      scan_done_stat = beamline_scan_record.getPhase()
      if (scan_done_stat == 0):
        break
      else:
        time.sleep(.5)
        pass
    except CaChannelException, status:
      print ca.message(status)
      print "\n\nHandled Epics Error waiting for scan\n\n"
      continue

#sets the name of the file that a scan writes to
def datafile(filename):
  global datafile_name

  datafile_name = filename

# creates a new datafile name based on a prefix. For example, if "scandata.1" exists,
# "newfile scandata" will set the datafile_name to "scandata.2"
def newfile(filename_prefix):
  global datafile_name

  for i in range(0,10000):
    datafile_name = "%s.%d" % (filename_prefix,i)
    if (os.path.exists(datafile_name) == 0):
      break
  return datafile_name

#returns the current datafile name
def nowfile():
  return datafile_name


#dumps motor parameters to a file. Used for creating scan file headers
def dump_mots(dump_filename):
  print("dumping to " + dump_filename)
  dump_file = open(dump_filename,'a+')
  dump_file.write("#%s\n" % time.ctime(time.time()))
  dump_file.write("#motor_code motor_name    pos speed bspd bcklsh acc bk_acc\n")
  for key in motor_channel_dict.keys():
    if (1):
#    if (not(is_soft_motor(key))):
      dump_file.write("# " + key)
      dump_file.write(" " + motor_channel_dict[key].description)
      dump_file.write(" %.3f" % motor_channel_dict[key].get_position())
      dump_file.write(" %.3f" % motor_channel_dict[key].slew_speed)
      dump_file.write(" %.3f" % motor_channel_dict[key].base_speed)
      dump_file.write(" %.3f" % motor_channel_dict[key].backlash)
      dump_file.write(" %.3f" % motor_channel_dict[key].acceleration)
      dump_file.write("\n")
  dump_file.close()



def sp(motcode,posn): #sets the position w/o moving
  if (not(is_soft_motor(motcode))):
    motor_channel_dict[beamline_designation+motcode].set_position(posn)
  else:
    print "Cannot set Soft Motor " + motcode


def fly_scan(half_scan_width,stepsize,counter_number,count_time,motcode,real_motcodes): 
#real_motcodes has the list of real motors for a composite motcode, it is an empty list otherwise

    speed_saves = {}
    print "scanning peak for " + motcode + "\n"
    scan_range = float(half_scan_width) * 2.0
    npoints = int(scan_range/abs(float(stepsize)))
    print "npoints = " + str(npoints) + "\n"    
    total_count_time = npoints*float(count_time)
    if (len(real_motcodes) > 0): #real motors that make up a composite
      for i in range (0,len(real_motcodes)):  
        current_motcode = beamline_designation+real_motcodes[i]
        urev = motor_channel_dict[current_motcode].urev
        print "urev = " + str(urev) + "\n"
        new_speed = (scan_range/total_count_time)/float(urev)
        print "speed =  " + str(new_speed) + "\n"
        speed_saves[current_motcode] = motor_channel_dict[current_motcode].speed
        motor_channel_dict[current_motcode].speed = new_speed
    else: #just one real motor
        current_motcode = beamline_designation+motcode
        urev = motor_channel_dict[current_motcode].urev
        print "urev = " + str(urev) + "\n"
        new_speed = (scan_range/total_count_time)/float(urev)
        print "speed =  " + str(new_speed) + "\n"
        speed_save = motor_channel_dict[current_motcode].speed
        motor_channel_dict[current_motcode].speed = new_speed
    set_scan_fly(motcode)
    if (float(stepsize)>0.0):
      direction = 1.0
    else:
      direction = -1.0
    align_left = (-1)*float(half_scan_width)*direction
    align_right = float(half_scan_width)*direction
    set_count_time(count_time)
    set_scan_relative(motcode)
    set_scanstart(motcode,align_left)
    set_scanend(motcode,align_right)
    set_scanstepsize(motcode,float(stepsize))
    scanfile_name = motcode + "_scan"
    newfile(scanfile_name)
    ri()
    mvf(motcode,counter_number)
    if (len(real_motcodes) > 0): #real motors that make up a composite
      for key in speed_saves.keys():
        motor_channel_dict[key].speed = speed_saves[key]    
    else: # one real motor
        motor_channel_dict[current_motcode].speed = speed_save 
    set_scan_linear(motcode)
    set_count_time(1.0)
    

def waveform_to_string(wave):
  s = ""
  for i in range (0,len(wave)):
    if (wave[i] == 0):
      break
    else:
      s = s + "%c" % wave[i]
  return s


#####
# most functions between here and the end of the file are mostly for internal use
####

def is_soft_motor(mcode):
  for i in range(0,len(soft_motor_list)):
    if (soft_motor_list[i] == mcode):
      return 1
    else:
      continue
  return 0
    

def read_db():
  global beamline_designation,motor_dict,soft_motor_list,scan_list,counter_dict
  
  envname = "EPICS_BEAMLINE_INFO"
  try:
    dbfilename = os.environ[envname]
  except KeyError:
    print envname + " not defined. Defaulting to epx.db."
    dbfilename = "epx.db"
  if (os.path.exists(dbfilename) == 0):
    error_msg = "EPICS BEAMLINE INFO %s does not exist.\n Program exiting." % dbfilename
    print error_msg
    sys.exit()
  else:
    dbfile = open(dbfilename,'r')
    line = dbfile.readline()
    line = dbfile.readline()
    beamline_designation = line[:-1]
    line = dbfile.readline()
    i = 0
    while(1):
      line = dbfile.readline()
      if (line == ""):
        break
      else:
        line = line[:-1]
        if (line == "#virtual motors"):
          break
        else:
          motor_inf = split(line)
          motor_dict[motor_inf[1]] = beamline_designation +  motor_inf[0]
    while(1):
      line = dbfile.readline()
      if (line == ""):
        break
      else:
        line = line[:-1]
        if (line == "#control PVs"):
          break
        else:
          motor_inf = split(line)
          soft_motor_list.append(beamline_designation + motor_inf[0])
          motor_dict[motor_inf[1]] = beamline_designation + motor_inf[0]          
    while(1):
      line = dbfile.readline()
      if (line == ""):
        break
      else:
        line = line[:-1]
        if (line == "#scanned motors"):
          break
        else:
          inf = split(line)
          pvLookupDict[inf[1]] = beamline_designation + inf[0]          
    while(1):
      line = dbfile.readline()
      if (line == ""):
        break
      else:
        line = line[:-1]
        if (line == "#counters"):
          break
        else:
          scan_list.append(beamline_designation + line + "scanParms")
    line = dbfile.readline()
    counter_inf = split(line)    
    counter_dict[counter_inf[1]] = beamline_designation + counter_inf[0]    



def init_motors():
  global motor_channel_dict

  for key in motor_dict.keys():
    try:
      motor_channel_dict[motor_dict[key]] = epicsMotor(motor_dict[key])
    except CaChannelException, status:
      print ca.message(status)
      print "\n\nCould not create motor channel " + motor_dict[key] + "\n\n"

def initControlPVs():
  global pvChannelDict

  for key in pvLookupDict.keys():
    try:
      pvChannelDict[pvLookupDict[key]] = pvCreate(pvLookupDict[key])
    except CaChannelException, status:
      print ca.message(status)
      print "\n\nCould not create control PV " + pvLookupDict[key] + "\n\n"
      

def init_counters():
  global counter_channel_dict

  for key in counter_dict.keys():
    try:
      counter_channel_dict[counter_dict[key]] = epicsScaler(counter_dict[key])
    except CaChannelException, status:
      print ca.message(status)
      print "\n\nCould not create counter channel " + counter_dict[key] + "\n\n"

def stop_scan():
  beamline_scan_record.stop()
  
def init_scanparms():
  global beamline_scan_record,scan_active_pv,scan_reference_counter

  beamline_scan_record = epicsScan(beamline_designation + "scan1")
#  scan_active_pv = epicsPV(beamline_designation+":scan1.FAZE")
  scan_reference_counter = epicsPV(beamline_designation+"scan1.REFD")
  for i in range(0,len(scan_list)):
    scanparms_channel_dict[scan_list[i]] = epicsScanParms(scan_list[i])

  

def GScan(motcode):

#kludge for wierd scan on soft mots, maybe not needed
##   mcode = "%s:%s" % (beamline_designation,motcode)
##   currpos = rbv_channel_list[mcode].getw()  
##   valpos = channel_list[mcode].getw()
##   if (currpos != valpos): 
##     channel_list[mcode].putw(currpos)

#  load_and_go_scan_parms(motcode)    
  beamline_scan_record.start()
  wait_for_scan()
  beamline_scan_record.read()
  if (datafile_name != ""):
    dump_mots(datafile_name)          
    datafile = open(datafile_name,'a+')
    datafile.write("#pt  %s  ct c2 c3 c4\n" % motcode)
    sys.stdout.write("#pt  %s  ct c2 c3 c4\n" % motcode)                      
    number_of_datapoints = len(beamline_scan_record.positioners[0].readback)
    scanpos_array = beamline_scan_record.positioners[0].readback
    for i in range(0,number_of_datapoints):
      scanpos = beamline_scan_record.positioners[0].readback[i]
      tmp_data_string = "%d %f" % (i,scanpos)
      for j in range(0,scan_detector_count):  
        data_string = "%s %d" % (tmp_data_string,beamline_scan_record.detectors[j].data[i])
        tmp_data_string = data_string
      datafile.write(data_string+"\n")
      sys.stdout.write(data_string+"\n")                            
    datafile.close()
  else:
    sys.stdout.write("No datafile name defined. Data not recorded.\n")


def get_short_motor_code(beamline_desginated_code): # return motor code minus beamline designation
  i = find(beamline_desginated_code,beamline_designation)
  if (i>-1):
    return beamline_desginated_code[len(beamline_designation):len(beamline_desginated_code)]
#    return beamline_desginated_code[len(beamline_designation)+1:len(beamline_desginated_code)]
  else:
    return beamline_desginated_code


def pvNameSuffix_from_descriptor(descriptor): # for example - {Gon:1-Ax:O}Mtr = pvNameSuffix_from_descriptor("omega")
  return get_short_motor_code(motor_code_from_descriptor(descriptor))

def motor_code_from_descriptor(descriptor):
  return motor_dict[descriptor]

def pvNameFromDescriptor(descriptor): 
  return pvLookupDict[descriptor]

def getPvValFromDescriptor(descriptor):
  return get_any_epics_pv(pvNameFromDescriptor(descriptor),"VAL")

def setPvValFromDescriptor(descriptor,setval):
  set_any_epics_pv(pvNameFromDescriptor(descriptor),"VAL",setval)
  
