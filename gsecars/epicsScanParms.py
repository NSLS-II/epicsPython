"""
This module provides support for the EPICS scanParm record.

Author:         John Skinner
Created:        Sept, 23 2009
Modifications:
"""

import epicsPV

class epicsScanParms:
   """
   This module provides a class library for the EPICS scanParm record.
   It uses the epicsPV class, which is in turn a subclass of CaChannel.

   """

   def __init__(self, name):
      """
      Creates a new scanParms instance.

      Inputs:
         name:
            The name of the EPICS motor record without any trailing period or field
            name.

      Example:
         m=scanParm('x12c:mon:scanParms')
      """
      self.pvs = {'step' : epicsPV.epicsPV(name+'.STEP',  wait=0), 
                  'sp': epicsPV.epicsPV(name+'.SP', wait=0),
                  'ep': epicsPV.epicsPV(name+'.EP', wait=0),
                  'np' : epicsPV.epicsPV(name+'.NP',  wait=0),
                  'go' : epicsPV.epicsPV(name+'.GO',  wait=0),
                  'ar': epicsPV.epicsPV(name+'.AR', wait=0),
                  'aft': epicsPV.epicsPV(name+'.AFT', wait=0),
                  'sm': epicsPV.epicsPV(name+'.SM', wait=0),
                  'load': epicsPV.epicsPV(name+'.LOAD', wait=0),
                  }
      # Wait for all PVs to connect
      self.pvs['load'].pend_io() 


   def load(self):
      self.pvs['load'].putw(1)

   def loadAndGo(self):
      self.pvs['go'].putw(1)

   def set_linear(self):
      self.pvs['sm'].putw(0)

   def set_fly(self):
      self.pvs['sm'].putw(2)     
     
   def set_relative(self):
      self.pvs['ar'].putw(1)     

   def set_absolute(self):
      self.pvs['ar'].putw(0)     

   def set_scanpoints(self,numpoints):
      self.pvs['np'].putw(numpoints)     

   def get_scanpoints(self):
      return self.pvs['np'].getw()

   def set_start(self,posn):
      self.pvs['sp'].putw(posn)     

   def set_end(self,posn):
      self.pvs['ep'].putw(posn)     

   def set_scanstepsize(self,stepsize):
      startpos = self.pvs['sp'].getw()
      endpos = self.pvs['ep'].getw()
      numpoints = int((endpos-startpos)/float(stepsize))
      if ((numpoints%2) != 1):
        numpoints = numpoints+1
      self.set_scanpoints(numpoints)

   def get_scanstepsize(self):
      return self.pvs['step'].getw()     

   def set_after_start(self):
      self.pvs['aft'].putw(1)     

   
   def set_after_end(self):
      self.pvs['aft'].putw(0)     

   
   def set_after_before_scan(self):
      self.pvs['aft'].putw(2)     

   
   def set_after_peak(self):
      self.pvs['aft'].putw(3)     

   
   
