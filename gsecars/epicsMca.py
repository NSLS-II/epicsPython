"""
EPICS device-dependent support for the Mca class.  Uses the EPICS mca record.

Author:           Mark Rivers
Created:          Sept. 18, 2002
Revision history: Original version was written in IDL
   Sept. 24, 2002  MLR.
      - Changed __init__ to use MCA_ENVIRONMENT environment variable when
        opening environment file.
      - Fixed bug when opening environment file
      - Fixed bug reading description from environment file
      - Fixed bug reading environment PVs
   Sept. 25, 2002  MLR.
      - Fixed bug reading environment file
"""
import os
import string
import time
import Numeric
import epicsPV
import Mca
import Xrf

#######################################################################
class epicsMca(Mca.Mca):
   def __init__(self, record_name, environment_file=None):
      """
      Creates a new epicsMca.
      
      Inputs:
         record_Name:
            The name of the EPICS MCA record for the MCA object being created, without
            a trailing period or field name.
            
      Keywords:
         environment_file:
            This keyword can be used to specify the name of a file which
            contains the names of EPICS process variables which should be saved
            in the header of files written with Mca.write_file().
            If this keyword is not specified then this function will attempt the
            following:
               - If the system environment variable MCA_ENVIRONMENT is set then
                 it will attempt to open that file
               - If this fails, it will attempt to open a file called
                 'catch1d.env' in the current directory.
                 This is done to be compatible with the data catcher program.
            This is an ASCII file with each line containing a process variable
            name, followed by a space and a description field.

      Example:
        >>> from epicsMca import *
        >>> mca = epicsMca('13IDC:mca1')
        >>> print mca.data
      """
      Mca.Mca.__init__(self)
      self.max_rois = 32
      self.record_name = record_name
      self.name = record_name
      self.sequence = 0
      self.pvs = {'calibration': 
                    {'calo': None,
                     'cals': None,
                     'calq': None,
                     'tth' : None,
                     'egu' : None},
                  'presets':
                    {'prtm': None,
                     'pltm': None,
                     'pct':  None,
                     'pctl': None,
                     'pcth': None,
                     'chas': None,
                     'dwel': None,
                     'pscl': None},
                  'elapsed':
                    {'ertm': None,
                     'eltm': None,
                     'act' : None,
                     'rtim': None,
                     'stim': None},
                  'acquire':
                    {'strt': None,
                     'stop': None,
                     'eras': None,
                     'acqg': None,
                     'proc': None,
                     'erst': None},
                  'data':
                    {'nuse': None,
                     'nmax': None,
                     'val':  None}}
      for group in self.pvs.keys():
         for pv in self.pvs[group].keys():
            name = self.record_name + '.' + string.upper(pv)
            self.pvs[group][pv] = epicsPV.epicsPV(name, wait=0)
      # Construct the names of the PVs for the ROIs
      self.roi_def_pvs=[]
      self.roi_data_pvs=[]
      for i in range(self.max_rois):
         n = 'R'+str(i)
         r = {n+'lo'  : None,
              n+'hi'  : None,
              n+'bg'  : None,
              n+'nm'  : None}
         self.roi_def_pvs.append(r)
         r = {n       : None,
              n+'n'   : None}
         self.roi_data_pvs.append(r)
      for roi in range(self.max_rois):
         for pv in self.roi_def_pvs[roi].keys():
            name = self.record_name + '.' + string.upper(pv)
            self.roi_def_pvs[roi][pv] = epicsPV.epicsPV(name, wait=0)
         for pv in self.roi_data_pvs[roi].keys():
            name = self.record_name + '.' + string.upper(pv)
            self.roi_data_pvs[roi][pv] = epicsPV.epicsPV(name, wait=0)

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
      self.pvs['calibration']['calo'].pend_io(30.)

      # ClientWait does not exist in simple_mca.db, which is used
      # for multi-element detectors.  We see if it exists by trying to connect
      # with a short timeout.
      client_wait = epicsPV.epicsPV(self.record_name + 'ClientWait', wait=0)
      enable_wait = epicsPV.epicsPV(self.record_name + 'EnableWait', wait=0)
      try:
         client_wait.pend_io(.01)
         self.pvs['acquire']['client_wait'] = client_wait
         self.pvs['acquire']['enable_wait'] = enable_wait
      except:
         self.pvs['acquire']['client_wait'] = None
         self.pvs['acquire']['enable_wait'] = None

      # Put monitors on the ERTM, VAL, NUSE and ACQG fields
      self.pvs['data']['nuse'].setMonitor()
      self.pvs['data']['val'].setMonitor()
      self.pvs['acquire']['acqg'].setMonitor()
      self.pvs['elapsed']['ertm'].setMonitor()

      # Read all of the information from the record
      self.get_calibration()
      self.get_presets()
      self.get_elapsed()
      self.get_rois()
      self.get_data()
 

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
   def get_calibration(self):
      """
      Reads the calibration information from the EPICS mca record.  Stores this information
      in the epicsMca object, and returns an McaCalibration object with this information.
      """
      calibration = Mca.McaCalibration()
      pvs = self.pvs['calibration']
      for pv in pvs.keys():
         pvs[pv].array_get()
      pvs[pv].pend_io()
      calibration.offset    = pvs['calo'].getValue()
      calibration.slope     = pvs['cals'].getValue()
      calibration.quad      = pvs['calq'].getValue()
      calibration.two_theta = pvs['tth'].getValue()
      calibration.units     = pvs['egu'].getValue()
      Mca.Mca.set_calibration(self, calibration)
      return calibration

   #######################################################################
   def set_calibration(self, calibration):
      """
      Writes the calibration information from an McaCalibration object to the EPICS mca
      record.

      Inputs:
         calibration:
            An McaCalibration instance containing the calibration information.
      """
      Mca.Mca.set_calibration(self, calibration)
      pvs = self.pvs['calibration']
      pvs['calo'].array_put(calibration.offset)
      pvs['cals'].array_put(calibration.slope)
      pvs['calq'].array_put(calibration.quad)
      pvs['tth'].array_put(calibration.two_theta)
      pvs['egu'].array_put(calibration.units)
      pvs['egu'].pend_io()

   #######################################################################
   def get_presets(self):
      """
      Reads the preset information from the EPICS mca record.  Stores this information
      in the epicsMca object, and returns an McaPresets object with this information.
      """
      presets = Mca.McaPresets()
      pvs = self.pvs['presets']
      for pv in pvs.keys():
         pvs[pv].array_get()
      pvs[pv].pend_io()
      presets.real_time       = pvs['prtm'].getValue()
      presets.live_time       = pvs['pltm'].getValue()
      presets.total_counts    = pvs['pct'].getValue()
      presets.start_channel   = pvs['pctl'].getValue()
      presets.end_channel     = pvs['pcth'].getValue()
      presets.dwell           = pvs['dwel'].getValue()
      presets.channel_advance = pvs['chas'].getValue()
      presets.prescale        = pvs['pscl'].getValue()
      Mca.Mca.set_presets(self, presets)
      return presets

   #######################################################################
   def set_presets(self, presets):
      """
      Writes the presets information from an McaPresets object to the EPICS mca
      record.

      Inputs:
         presets:
            An McaPresets instance containing the presets information.
      """
      Mca.Mca.set_presets(self, presets)
      pvs = self.pvs['presets']
      pvs['prtm'].array_put(presets.real_time)
      pvs['pltm'].array_put(presets.live_time)
      pvs['pct'].array_put(presets.total_counts)
      pvs['pctl'].array_put(presets.start_channel)
      pvs['pcth'].array_put(presets.end_channel)
      pvs['dwel'].array_put(presets.dwell)
      pvs['chas'].array_put(presets.channel_advance)
      pvs['pscl'].array_put(presets.prescale)
      pvs['pscl'].pend_io()

   #######################################################################
   def new_elapsed(self):
      """
      Returns a flag to indicate if the elapsed parameters for the mca record have changed
      since they were last read.  Returns 1 if there are new values, 0 if there are not.
      """
      return self.pvs['elapsed']['ertm'].checkMonitor()

   #######################################################################
   def get_elapsed(self):
      """
      Reads the elapsed information from the EPICS mca record.  Stores this information
      in the epicsMca object, and returns an McaElapsed object with this information.
      """
      elapsed = Mca.McaElapsed()
      pvs = self.pvs['elapsed']
      for pv in pvs.keys():
         pvs[pv].array_get()
      pvs[pv].pend_io()
      elapsed.real_time    = pvs['ertm'].getValue()
      elapsed.live_time    = pvs['eltm'].getValue()
      elapsed.total_counts = pvs['act'].getValue()
      elapsed.read_time    = pvs['rtim'].getValue()
      elapsed.start_time   = string.strip(pvs['stim'].getValue())
      Mca.Mca.set_elapsed(self, elapsed)
      return elapsed

   #######################################################################
   def set_elapsed(self, elapsed):
      """
      Writes the elapsed information from an McaElapsed object to the EPICS mca
      record.

      Inputs:
         elapsed:
            An McaElapsed instance containing the elapsed information.
      """
      Mca.Mca.set_elapsed(self, elapsed)

   #######################################################################
   def get_sequence(self):
      """
      Reads the current "sequence" from the EPICS mca record.  The sequence is typically
      used for fast data collection where multiple spectra are stored in the hardware.
      """
      pvs = self.pvs['sequence']
      for pv in pvs.keys():
         pvs[pv].array_get()
      pvs[pv].pend_io()
      sequence=pvs['seq'].getValue()
      return sequence

   #######################################################################
   def set_sequence(self, sequence):
      """
      Sets the current "sequence" from the EPICS mca record.  The sequence is typically
      used for fast data collection where multiple spectra are stored in the hardware.

      Inputs:
         sequence:
            The sequence number for data collection.
      """
      pvs = self.pvs['sequence']
      pvs['seq'].array_put(sequence)
      pvs['seq'].pend_io()
         
   #######################################################################
   def get_rois(self, energy=0):
      """
      Reads the ROI information from the EPICS mca record.  Stores this information
      in the epicsMca object, and returns a list of McaROI objects with this information.
      """
      for i in range(self.max_rois):
         pvs = self.roi_def_pvs[i]
         for pv in pvs.keys():
            pvs[pv].array_get()
      pvs[pv].pend_io()
      rois = []
      for i in range(self.max_rois):
         roi = Mca.McaROI()
         pvs = self.roi_def_pvs[i]
         r = 'R'+str(i)
         roi.left      = pvs[r+'lo'].getValue()
         roi.right     = pvs[r+'hi'].getValue()
         roi.label     = pvs[r+'nm'].getValue()
         roi.bgd_width = pvs[r+'bg'].getValue()
         roi.use = 1
         if (roi.left > 0) and (roi.right > 0): rois.append(roi)
      Mca.Mca.set_rois(self, rois)
      return Mca.Mca.get_rois(self, energy=energy)

   #######################################################################
   def set_rois(self, rois, energy=0):
      """
      Writes the ROI information from a list of mcaROI objects to the EPICS mca
      record.

      Inputs:
         rois:
            A list of mcaROI objects.

      Keywords:
         energy:
            Set this flag if the .left and .right fields of the ROIs are in energy units.
            By default these fields are assumed to be in channels.
      """
      Mca.Mca.set_rois(self, rois, energy=energy)
      nrois = len(self.rois)
      for i in range(nrois):
         roi = rois[i]
         pvs = self.roi_def_pvs[i]
         n = 'R'+str(i)
         pvs[n+'lo'].array_put(roi.left)
         pvs[n+'hi'].array_put(roi.right)
         pvs[n+'nm'].array_put(roi.label)
         pvs[n+'bg'].array_put(roi.bgd_width)
      for i in range(nrois, self.max_rois):
         n = 'R'+str(i)
         pvs = self.roi_def_pvs[i]
         pvs[n+'lo'].array_put(-1)
         pvs[n+'hi'].array_put(-1)
         pvs[n+'nm'].array_put(" ")
         pvs[n+'bg'].array_put(0)
      pvs[n+'bg'].pend_io()

   #######################################################################
   def get_roi_counts(self):
      """
      Reads the ROI counts from the EPICS mca record. Returns a tuple containing two lists,
      (total, net), containing the total and net counts in each ROI.
      """
      nrois = len(self.rois)
      for roi in range(nrois):
         for pv in self.roi_data_pvs[roi].keys():
            pv.array_get()
      pvs[pv].pend_io()
      total = []
      net = []
      for i in range(nrois):
         pvs = self.roi_data_pvs[i]
         total.append(pvs['n'].getValue())
         net.append(pvs['nn'].getValue())
      return total, net

   #######################################################################
   def add_roi(self, roi, energy=0):
      """
      Adds a new ROI to the epicsMca.

      Inputs:
         roi:
            An McaROI object.

      Keywords:
         energy:
            Set this flag if the .left and .right fields in the mcaROI are in energy units.
            By default these fields are assumed to be in channels.
      """
      Mca.Mca.add_roi(self, roi, energy=energy)
      self.set_rois(self.rois)

   #######################################################################
   def delete_roi(self, index):
      """
      Deletes an ROI from the epicsMca.

      Inputs:
         index:
            The index number of the ROI to be deleted (0-31).
      """
      Mca.Mca.delete_roi(self, index)
      self.set_rois(self.rois)


   #######################################################################
   def get_environment(self):
      """
      Reads the current values of the environment PVs.  Returns a list of
      McaEnvironment objects with Mca.get_environment().
      """
      if (len(self.env_pvs) > 0):
         for pv in self.env_pvs:
            pv.array_get()
         pv.pend_io()
         for i in range(len(self.environment)):
            self.environment[i].name = self.env_pvs[i].name()
            self.environment[i].value = self.env_pvs[i].getValue()
      return Mca.Mca.get_environment(self)

   #######################################################################
   def new_data(self):
      """
      Returns a flag to indicate if the data (counts) for the mca record have changed
      since they were last read.  Returns 1 if there are new values, 0 if there are not.
      """
      return self.pvs['data']['val'].checkMonitor()

   #######################################################################
   def get_data(self):
      """
      Reads the data from the EPICS mca record.  Returns the data with Mca.get_data().
      """
      nuse = self.pvs['data']['nuse'].getw()
      nchans = max(nuse,1)
      data = self.pvs['data']['val'].getw(count=nchans)
      data = Numeric.asarray(data)
      Mca.Mca.set_data(self, data)
      return Mca.Mca.get_data(self)

   #######################################################################
   def set_data(self, data):
      """
      Writes data to the EPICS mca record.  The .VAL and .NUSE fields are written to.

      Inputs:
         data:
            The array of counts to be written to the mca record.
      """
      nmax = self.pvs['data']['nmax'].getw()
      n_chans = max(len(data), nmax)
      Mca.Mca.set_data(self, data[0:n_chans])
      self.pvs['data']['nuse'].array_put(n_chans)
      self.pvs['data']['val'].putw(data[0:nchans])

   #######################################################################
   def new_acquire_status(self):
      """
      Returns a flag to indicate if the acquisition status (acquiring or done) for the mca
      record has changed since it was last read.  Returns 1 if the status has changed,
      0 if it has not.
      """
      return self.pvs['acquire']['acqg'].checkMonitor()

   #######################################################################
   def get_acquire_status(self, update=0):
      """
      Returns the acquisition status.  1 if the mca is acquiring, 0 if it is not.

      Keywords:
         update:
            Set this keyword to force the routine to process the record, and thus read
            the hardware.
            By default update=0 and this routine does not process the record.
            The acquire status returned will be the status when the record
            was last processed.
      """
      if (update != 0): 
         self.pvs['acquire']['proc'].putw(1)
      busy = self.pvs['acquire']['acqg'].getw()
      return busy

   #######################################################################
   def wait(self, delay=.1, start=0, stop=1):
      """
      Waits for acquisition of the MCA to start and/or complete.

      Keywords:
         delay:  The time between polling.  Default=0.1 seconds.
         
         start:
            Set this flag to wait for acquisition to start.
            
         stop:
            Set this flag to wait for acquisition to stop.  This is the default.

         If both the "start" and "stop" keywords are given then the routine 
         will wait first for acquisition to start and then for acquistion to 
         stop.  If only start=1 is given then it will not wait for acquisition
         to stop.
      """
      if (start == 0) and (stop == 0): stop=1
      if (start != 0):
         while (1):
            busy = self.get_acquire_status(update=1)
            if (busy != 0): break
            time.sleep(delay)

      if (stop != 0):
         while (1):
            busy = self.get_acquire_status(update=1)
            if (busy == 0): break
            time.sleep(delay)

   #######################################################################
   def erase(self):
      """  Erases the EPICS mca """
      self.pvs['acquire']['eras'].putw(1)

   #######################################################################
   def start(self, erase=0):
      """
      Starts acquisition of the EPICS mca.

      Keywords:
         erase:
            Set this flag to erase the mca before starting acquisition.  The default
            is not to erase first.
      """
      if (erase == 0):
         self.pvs['acquire']['strt'].putw(1)
      else:
         self.pvs['acquire']['erst'].putw(1)

   #######################################################################
   def stop(self):
      """ Stops acquisition of the EPICS mca. """
      self.pvs['acquire']['stop'].putw(1)

   #######################################################################
   def write_file(self, file):
      """
      Invokes Mca.write_file to write the mca to a disk file.
      After the file is written resets the client wait flag PV, if it exists.
      This flag is typically used by the EPICS scan record to wait for a client application
      to save the file before it goes on to the next point in the scan.

      Inputs:
         file:
            The name of the file to write the mca to.
      """
      Mca.Mca.write_file(self, file)
      # Reset the client wait flag in case it is set.  It may not exist.
      if (self.pvs['acquire']['client_wait'] != None):
         self.pvs['acquire']['client_wait'].putw(0)

   ############################################################################
   def spectra_scan(self, first_file, scan_record):
      """
      Collects Mca spectra and saves them to disk in conjunction with an EPICS scan record.

      Inputs:
         first_file:  
            The name of the first spectrum file to save.  Subsequent files 
            will be named using the Xrf.increment_filename()function.  The 
            filename must end in a numeric extension for this to work.
            
         scan_record:
            The name of the EPICS scan record which is controlling the scan.
            This scan record must be configure to start epicsMca data collection
            by writing "1" into the ERST field if the EPICS MCA.
            
      Procedure:
         1) Waits for scan.EXSC = 1, meaning scan has started
         2) Waits for ClientWait=1, meaning acquisition has started
         3) Waits for Acquiring=0, meaning acquisition has completed
         4) Writes data to disk with epicsMca::write_file, increment file name
         5) Resets ClientWait to 0 so scan will continue
         6) If scan.EXSC is still 1 go to 2.
      """
      file = first_file

      # Enable waiting for client
      self.pvs['acquire']['enable_wait'].putw(1)

      # Create PV for scan record executing
      scanPV = epicsPV.epicsPV(scan_record + '.EXSC')
      # Wait for scan to start
      while (scanPV.getw() == 0):
         time.sleep(.1)

      while (1):
         # If scan is complete, exit
         if (scanPV.getw() == 0): return

         # Wait for acquisition to start
         self.wait(start=1, stop=0)

         # Wait for acquisition to complete
         self.wait(start=0, stop=1)
 
         # Write file.  This will reset the client wait flag.
         self.write_file(file)
         print 'Saved file: ', file
         file = Xrf.increment_filename(file)
