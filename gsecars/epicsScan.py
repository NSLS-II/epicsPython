"""
Class library for the EPICS scan and sscan records

Author:
   Mark Rivers

Created:
   Oct. 1, 2002

Revision history: Original version was written in IDL
"""
import Scan
import os
import epicsPV

########################################################################
class epicsPositioner(Scan.Positioner):
   """
   Defines a scan positioner
   """
   def __init__(self, recordName, num):
      Scan.Positioner.__init__(self)
      n = '%d' % (num+1)
      self.pvs = {}
      self.pvs['cpt']           = epv(recordName, 'CPT')
      self.pvs['data']          = epv(recordName, 'DATA')
      self.pvs['link']          = epv(recordName, 'P'+n+'PV')
      self.pvs['valid']         = epv(recordName, 'P'+n+'NV')
      self.pvs['readbackLink']  = epv(recordName, 'R'+n+'PV')
      self.pvs['readbackValid'] = epv(recordName, 'R'+n+'NV')
      self.pvs['start']         = epv(recordName, 'P'+n+'SP')
      self.pvs['end']           = epv(recordName, 'P'+n+'EP')
      self.pvs['step']          = epv(recordName, 'P'+n+'SI')
      self.pvs['tableMode']     = epv(recordName, 'P'+n+'SM')
      self.pvs['relativeMode']  = epv(recordName, 'P'+n+'AR')
      self.pvs['cv']            = epv(recordName, 'P'+n+'CV')
      self.pvs['rcv']           = epv(recordName, 'R'+n+'CV')
      self.pvs['position']      = epv(recordName, 'P'+n+'PA')
      self.pvs['readback']      = epv(recordName, 'P'+n+'RA')
      self.link            = ""
      self.readbackLink    = ""
      self.valid           = 0
      self.readbackValid   = 0
      self.start           = 0
      self.end             = 0
      self.step            = 0
      self.tableMode       = "LINEAR"
      self.relativeMode    = "RELATIVE"
      self.readback        = []
      self.position        = []

   ########################################################################
   def setMonitors(self):
      for pv in self.pvs.keys():
         self.pvs[pv].setMonitor()

   ########################################################################
   def read(self):
      self.valid           = not(self.pvs['valid'].getw())
      if (self.valid): 
         self.dataReady       = self.pvs['data'].getw()
         self.currentPoint    = self.pvs['cpt'].getw()
         self.link         = self.pvs['link'].getw()
         self.start        = self.pvs['start'].getw()
         self.end          = self.pvs['end'].getw()
         self.step         = self.pvs['step'].getw()
         self.tableMode    = self.pvs['tableMode'].getw()
         self.relativeMode = self.pvs['relativeMode'].getw()
         if (self.dataReady):  # Read the array data
            self.position     = self.pvs['position'].getw(
                                                    count=self.currentPoint)
         else:                 # Read current value and append
            if (self.currentPoint == 0):
               self.position = []
            if (self.pvs['cv'].checkMonitor()):
               values = self.pvs['cv'].getw()
               for value in values:
                  self.position.append(value)
                   
      self.readbackValid   = not(self.pvs['readbackValid'].getw())
      if (self.readbackValid):
         self.dataReady       = self.pvs['data'].getw()
         self.currentPoint    = self.pvs['cpt'].getw()
         self.readbackLink = self.pvs['readbackLink'].getw()
         if (self.dataReady):  # Read the array data
            self.readback = self.pvs['readback'].getw(
                                                    count=self.currentPoint)
         else:                 # Read current value and append
            if (self.currentPoint == 0):
               self.readback = []
            if (self.pvs['rcv'].checkMonitor()):
               values = self.pvs['rcv'].getw()
               for value in values:
                  self.readback.append(value)

   ########################################################################
   def write(self):
      self.pvs = {}
      self.pvs['link'].putw(self.link)
      self.pvs['start'].putw(self.start)
      self.pvs['end'].putw(self.end)
      self.pvs['step'].putw(self.step)
      self.pvs['tableMode'].putw(self.tableMode)
      self.pvs['relativeMode'].putw(self.relativeMode)
      if (self.tableMode == "TABLE"):
         self.pvs['position'].putw(self.position)
      self.pvs['readbackLink'].putw(self.readbackLink)


########################################################################
class epicsDetector(Scan.Detector):
   """
   Defines a scan detector
   """
   def __init__(self, recordName, num):
      Scan.Detector.__init__(self)
      n = '%2.2d' % (num+1)
      self.pvs = {}
      self.pvs['cpt']   = epv(recordName, 'CPT')
      self.pvs['data']  = epv(recordName, 'DATA')
      self.pvs['link']  = epv(recordName, 'D'+n+'PV')
      self.pvs['valid'] = epv(recordName, 'D'+n+'NV')
      self.pvs['cv']    = epv(recordName, 'D'+n+'CV')
      self.pvs['data']  = epv(recordName, 'D'+n+'DA')
      self.link = ""
      self.valid = 0
      self.data = []
                        
   ########################################################################
   def setMonitors(self):
      for pv in self.pvs.keys():
         self.pvs[pv].setMonitor()

   ########################################################################
   def read(self):
      self.valid        = not(self.pvs['valid'].getw())
      if (self.valid): 
         self.dataReady    = self.pvs['data'].getw()
         self.currentPoint = self.pvs['cpt'].getw()
         self.link = self.pvs['link'].getw()
         if (self.dataReady):  # Read the array data
            self.data = self.pvs['data'].getw(count=self.currentPoint)
         else:                      # Read current value and append
            if (self.currentPoint == 0):
               self.data = []
            if (self.pvs['cv'].checkMonitor()):
               values = self.pvs['cv'].getw()
               for value in values:
                  self.data.append(value)
      
   ########################################################################
   def write(self):
      self.pvs['link'].putw(self.link)

########################################################################
class epicsTrigger:
   """
   Defines a scan trigger
   """
   def __init__(self, recordName, num):
      n = '%d' % (num+1)
      self.pvs = {}
      self.pvs['link']    = epv(recordName, 'T'+n+'PV')
      self.pvs['valid']   = epv(recordName, 'T'+n+'NV')
      self.pvs['value']   = epv(recordName, 'T'+n+'CD')
      self.link = ""
      self.valid = 0
      self.value = 1

   ########################################################################
   def setMonitors(self):
      for pv in self.pvs.keys():
         self.pvs[pv].setMonitor()

   ########################################################################
   def read(self):
      self.valid      = not(self.pvs['valid'].getw())
      if (self.valid): 
         self.link  = self.pvs['link'].getw()
         self.value = self.pvs['value'].getw()
      
   ########################################################################
   def write(self):
      self.pvs['link'].putw(self.link)
      self.pvs['value'].putw(self.value)
      
#######################################################################
class epicsScan(Scan.Scan):
   def __init__(self, recordName, environmentFile=None):
      """
      Creates a new epicsScan.
      
      Inputs:
         record_Name:
            The name of the EPICS SSCAN record for the epicsScan object being
            created, without a trailing period or field name.
            
      Keywords:
         environment_file:
            This keyword can be used to specify the name of a file which
            contains the names of EPICS process variables which should be saved
            in the header of files written with .write_file().
            If this keyword is not specified then this function will attempt the            following:
               - If the system environment variable MCA_ENVIRONMENT is set then
                 it will attempt to open that file
               - If this fails, it will attempt to open a file called
                 'catch1d.env' in the current directory.
                 This is done to be compatible with the data catcher program.
            This is an ASCII file with each line containing a process variable
            name, followed by a space and a description field.

      Example:
        >>> from epicsScan import *
        >>> scan = epicsScan('13IDC:scan1')
        >>> print scan.detectors[0].data
      """
      Scan.Scan.__init__(self)
#skinner - I reduced the following from 70->6 and from 4->1 to match what we use
      self.maxDetectors = 6
      self.maxPositioners = 1
      self.maxTriggers = 4
      self.recordName = recordName
      self.triggers = []
      # Construct the positioners
      for i in range(self.maxPositioners):
         self.positioners.append(epicsPositioner(recordName, i))

      # Construct the detectors
      for i in range(self.maxDetectors):
         self.detectors.append(epicsDetector(recordName, i))

      # Construct the triggers
      for i in range(self.maxTriggers):
         self.triggers.append(epicsTrigger(recordName, i))

      # PVs for fields other than positioners, detectors and triggers
      self.pvs = {'exsc': None,
                  'paus': None,
                  'busy': None,
                  'data': None,
                  'npts': None,
                  'mpts': None,
                  'cpt':  None,
                  'pdly': None,
                  'ddly': None,
                  'vers': None,
                  'smsg': None,
                  'cmnd': None,
                  'alrt': None,
                  'faze': None,
                  }
      for pv in self.pvs.keys():
         self.pvs[pv] = epv(self.recordName, pv.upper())
      # Construct the names of the PVs for the environment
      environment_file = os.getenv('MCA_ENVIRONMENT')
      if (environment_file == None):
         environment_file = 'catch1d.env'
      self.read_environment_file(environment_file)
      self.env_pvs = []
      for env in self.environment:
         self.env_pvs.append(epicsPV.epicsPV(env.name, wait=0))

      # Wait for all PVs to connect.  30 second timeout is for WAN, but
      # even this does not seem to be long enough on DSL connection
      self.pvs['exsc'].pend_io(30.)

      # Set monitors on all of the fields
      for p in self.positioners:
         p.setMonitors()
      for d in self.detectors:
         d.setMonitors()
      for t in self.triggers:
         t.setMonitors()
      for pv in self.pvs.keys():
         self.pvs[pv].setMonitor()


      # Read all of the information from the record
      self.read()

   #######################################################################
   def read_environment_file(self, file):
      """
      Reads a file containing the "environment" PVs.  The values and desriptions of these
      PVs are stored in the data files written by Mca.write_file().

      Inputs:
         file:
            The name of the file containing the environment PVs. This is an ASCII file
            with each line containing a process variable name, followed by a
            space and a description field.
      """
      self.environment = []
      try:
         fp = open(file, 'r')
         lines = fp.readlines()
         fp.close()
      except:
         return
      for line in lines:
          env = Mca.McaEnvironment()
          pos = line.find(' ')
          if (pos != -1):
             env.name = line[0:pos]
             env.description = line[pos+1:].strip()
          else:
             env.name = line.strip()
             env.description = ' '
          self.environment.append(env)

   #######################################################################
   def read(self):
      self.readPositioners()
      self.readDetectors()
      self.readTriggers()
      self.readOther()
 
   #######################################################################
   def readPositioners(self):
      """ Reads current values of all positioner fields from record) """
      for p in self.positioners:
         p.read()

   #######################################################################
   def readDetectors(self):
      """ Reads current values of all detector fields from record """
      for d in self.detectors:
         d.read()

   #######################################################################
   def readTriggers(self):
      """ Reads current values of all trigger fields from record """
      for t in self.triggers:
         t.read()

   #######################################################################
   def readOther(self):
      """ Reads current values of all fields other
      than positioner, trigger or detector from the record """
      self.executing       = self.pvs['exsc'].getw()
      self.paused          = self.pvs['paus'].getw()
      self.busy            = self.pvs['busy'].getw()
      self.dataReady       = self.pvs['data'].getw()
      self.numPoints       = self.pvs['npts'].getw()
      self.maxPoints       = self.pvs['mpts'].getw()
      self.currentPoint    = self.pvs['cpt'].getw()
      self.positionerDelay = self.pvs['pdly'].getw()
      self.detectorDelay   = self.pvs['ddly'].getw()
      self.version         = self.pvs['vers'].getw()
      self.message         = self.pvs['smsg'].getw()
      self.command         = self.pvs['cmnd'].getw()
      self.alert           = self.pvs['alrt'].getw()
      self.phase           = self.pvs['faze'].getw()

   #######################################################################
   def write(self):
      self.writePositioners()
      self.writeDetectors()
      self.writeTriggers()
      self.writeOther()
 
   #######################################################################
#skinner added
   def getPhase(self):
     return self.pvs['faze'].getw()

   #######################################################################
   def writePositioners(self):
      """ Writes current values of all positioner fields to the record) """
      for p in self.positioners:
         p.write()

   #######################################################################
   def writeDetectors(self):
      """ Writes current values of all detector fields to the record """
      for d in self.detectors:
         d.write()

   #######################################################################
   def writeTriggers(self):
      """ Writes current values of all trigger fields to the record """
      for t in self.triggers:
         t.write()

   #######################################################################
   def writeOther(self):
      """ Writes current values of all fields other
      than positioner, trigger or detector to the record """
      self.message         = self.pvs['smsg'].getw()
      self.command         = self.pvs['cmnd'].getw()

   #######################################################################
   def start(self):
      """ Starts a scan """
      self.pvs['exsc'].putw(1)

   #######################################################################
   def stop(self):
      """ Stops a scan """
      self.pvs['exsc'].putw(0)

   #######################################################################
   def pause(self):
      """ Pauses a scan """
      self.pvs['paus'].putw(1)

   #######################################################################
   def resume(self):
      """ Resumes a scan """
      self.pvs['paus'].putw(0)

   #######################################################################
   def setNumPoints(self, numPoints):
      """ Sets the number of points in a scan """
      self.numPoints = numPoints
      self.pvs['npts'].putw(self.numPoints)
      
   #######################################################################
   def setPositionerDelay(self, positionerDelay):
      """ Sets the positioner delay """
      self.positionerDelay = positionerDelay
      self.pvs['pdly'].putw(self.positionerDelay)

   #######################################################################
   def setDetectorDelay(self, detectorDelay):
      """ Sets the detector delay """
      self.detectorDelay = detectorDelay
      self.pvs['ddly'].putw(self.detectorDelay)

   #######################################################################
   def clearMessage(self):
      """ Clears message field """
      self.pvs['cmnd'].putw(0)

def epv(recordName, fieldName):
   pv = epicsPV.epicsPV(recordName + '.' + fieldName.upper(), wait=0)
   return(pv)
