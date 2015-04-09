"""
Class library for "scans"

Author:
   Mark Rivers
   
Created:
   Oct. 1, 2002

Revision history:
"""

########################################################################
class Positioner:
   """
   Defines a scan positioner
   """
   LINEAR   = 0
   TABLE    = 1
   def __init__(self):
      self.start       = 0.
      self.end         = 0.
      self.step        = 0.
      self.name        = ""
      self.description = ""
      self.mode        = Positioner.LINEAR
      self.position    = []
      self.readback    = []

#######################################################################
class Detector:
   """
   Defines a scan detector
   """
   def __init__(self):
      self.name        = ""
      self.description = ""
      self.dimensions  = 0
      self.data        = None

#######################################################################
class Scan:
   def __init__(self):
      """
      """
      self.positioners = []
      self.detectors = []
      
