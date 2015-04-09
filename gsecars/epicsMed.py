import time
import Med
import Mca
import epicsMca
import Xrf
import epicsPV

############################################################################
class epicsMed(Med.Med):
   def __init__(self, prefix, n_detectors=16, bad=None):
      """
      This is the initialization code which is invoked when a new object of
      type epicsMed is created.
      med = epicsMed(prefix, n_detectors=16, bad=None)
      INPUTS:
         Prefix:  The prefix of the EPICS process variables for this
                  multi-element detector database.  The records for the 
                  process variables must be named according to the
                  following rules:
         prefix + 'Start'  ; PV which starts acquisition when 1 is written to it
         prefix + 'Stop'   ; PV which stops acquisition when 1 is written to it
         prefix + 'EraseAll' ; PV which erases all MCAs when 1 is written to it
         prefix + 'ReadSeq' ; PV which reads all MCAs when 1 is written to it
         prefix + 'ElapsedLive' ; PV from which elapsed live time can be read
         prefix + 'ElapsedReal' ; PV from which elapsed real time can be read
         prefix + 'PresetLive'  ; PV to which preset live time can be written
         prefix + 'PresetReal'  ; PV to which preset real time can be written
         prefix + 'Acquiring'   ; PV which is 1 when any detector is acquiring,
                                ;   0 when they are all done acquiring
         prefix + 'mcaN'        ; Name of MCA record for each detector, e.g. 
                                ; prefix + 'mca1', prefix + 'mca2', etc.
      KEYORD INPUTS:
         n_detectors: The number of detectors in the Med.  Default is 16.
         bad:  A scalar or list the bad detectors, e.g. bad=[3,7].
               The detectors are numbered from 1 to n_detectors.
               These detectors will not be accessed by any of the MED methods.
               In the following example:
               med = epicsMed('13IDC:med:', 16, bad=[3,7])
               detectors 3 and 7, out of a total of 16, are bad.  All of the
               Med functions, such as get_calibration(), get_data(), etc.
               will return only 14 values, not 16.
      SIDE EFFECTS:
         The routine establishes channel access monitors on all of the fields
         in the records which the methods in this class will read.  This
         greatly improves the speed and efficiency.
      """
      class pvs:
         pass
      self.pvs = pvs()
      t = Med.Med.__init__(self, n_detectors)  # Invoke base class initialization
      self.pvs.start = epicsPV.epicsPV(prefix + 'StartAll', wait=0)
      self.pvs.erasestart = epicsPV.epicsPV(prefix + 'EraseStart', wait=0)
      self.pvs.stop  = epicsPV.epicsPV(prefix + 'StopAll', wait=0)
      self.pvs.erase = epicsPV.epicsPV(prefix + 'EraseAll', wait=0)
      self.pvs.read  = epicsPV.epicsPV(prefix + 'ReadAll', wait=0)
      self.pvs.elive  = epicsPV.epicsPV(prefix + 'ElapsedLive', wait=0)
      self.pvs.ereal  = epicsPV.epicsPV(prefix + 'ElapsedReal', wait=0)
      self.pvs.plive  = epicsPV.epicsPV(prefix + 'PresetLive', wait=0)
      self.pvs.preal  = epicsPV.epicsPV(prefix + 'PresetReal', wait=0)
      self.pvs.dwell  = epicsPV.epicsPV(prefix + 'Dwell', wait=0)
      self.pvs.channel_advance  = epicsPV.epicsPV(prefix + 'ChannelAdvance', wait=0)
      self.pvs.prescale  = epicsPV.epicsPV(prefix + 'Prescale', wait=0)
      self.pvs.acquiring  = epicsPV.epicsPV(prefix + 'Acquiring', wait=0)
      self.pvs.client_wait  = epicsPV.epicsPV(prefix + 'ClientWait', wait=0)
      self.pvs.enable_client_wait  = epicsPV.epicsPV(prefix + 'EnableClientWait', wait=0)
      good_detectors = range(1, self.n_detectors+1)
      if (bad != None):
         for b in bad:
            del good_detectors[b-1]
      self.n_detectors = len(good_detectors)
      self.good_detectors = good_detectors
      for i in range(self.n_detectors):
         pv = prefix + 'mca' + str(self.good_detectors[i])
         self.mcas[i] = epicsMca.epicsMca(pv)
      self.pvs.elive.setMonitor()
      self.pvs.ereal.setMonitor()
      self.pvs.acquiring.setMonitor()
      self.pvs.client_wait.setMonitor()
      # Wait for all PVs to connect
      self.pvs.client_wait.pend_io(30.)
      # Read the first MCA to get the number of channels
      t = self.mcas[0].get_data()
      # Read the environment from the first MCA
      self.environment = self.mcas[0].get_environment()

   ############################################################################
   def set_presets(self, presets):
      """
      Sets the preset parameters for the Med. The preset information is
      contained in an object of type McaPresets.
      epics_med.set_presets(presets)
      PROCEDURE:
         This function knows about the EPICS database which fans out a single 
         preset to each multiplexed group of detectors.
      """
      self.presets = presets
      self.pvs.preal.putw(presets.real_time)
      self.pvs.plive.putw(presets.live_time)
      self.pvs.dwell.putw(presets.dwell)
      self.pvs.channel_advance.putw(presets.channel_advance)
      self.pvs.prescale.putw(presets.prescale)

   ############################################################################
   def copy_rois(self, detector=1, energy=0):
      """
      Copies the ROIs defined for one detector to all of the other detectors
      med.copy_rois(detector=1, energy=0)
      This function simply converts from detector numbers as seen by the user
      (1-N, including bad elements) to the index in the Mca object array in
      the Med.  It then calls Med.copy_rois.
      """
      detector = self.good_detectors.index(detector-1) + 1
      Med.Med.copy_rois(self, detector, energy=energy)


   ############################################################################
   def get_acquire_status(self, update=0):
      """
      Returns the acquisition status for the Med, 1 if the Med is acquiring
      and 0 if it is not acquiring.
      UPDATE:  Set this keyword to update the acquisition status.
               By default this routine does not do this.
      """
      if (update != 0): self.pvs.read.putw(1)
      acquiring = self.pvs.acquiring.getw()
      return acquiring

   ############################################################################
   def get_environment(self):
      """
      Returns the environment parameters for the Med, as a list of objects
      of type McaEnvironment.
      e = epics_med.get_environment()
      """
      return self.mcas[0].get_environment()
    
   ############################################################################
   def wait(self, delay=.1, start=0, stop=1):
      """
      PURPOSE:
         This procedures waits for acquisition of the Med to complete.
      KEYWORD INPUTS:
         delay:  The time between polling.  Default=0.1 seconds
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


   ############################################################################
   def erase(self):
      """
      PURPOSE:
         Erases the array data, i.e. sets all channels of each detector to zero.
      PROCEDURE:
         This procedure erases the Med by sending the appropriate command to
         the EPICS database.  For efficiency it does not call epicsMca.Erase()
         for each epicsMca in the epicsMed.
      """
      self.pvs.erase.putw(1)

   ############################################################################
   def start(self, erase=0):
      """
      PURPOSE:
         Starts acquisition.
      KEYWORD INPUTS:
         erase:  Set this flag to erase the Med before acquisition starts.
      PROCEDURE:
         Starts the Med by sending the appropriate command to
         the EPICS database.  For efficiency it does not call 
         epicsMca.start() for each epicsMca in the epicsMed.
      """
      if (erase == 0):
         self.pvs.start.putw(1)
      else:
         self.pvs.erasestart.putw(1)

   ############################################################################
   def stop(self):
      """
      PURPOSE:
         Stops acquisition.
      PROCEDURE:
         Stops the Med by sending the appropriate command to
         the EPICS database.  For efficiency it does not call 
         epicsMca.stop() for each epicsMca in the epicsMed.
      """
      self.pvs.stop.putw(1)

   #######################################################################
   def write_file(self, file):
      Mca.Mca.write_file(self, file)
      # Reset the client wait flag in case it is set.
      self.pvs.client_wait.putw(0)

   ############################################################################
   def spectra_scan(self, first_file, scan_record):
      """
      PURPOSE:
         This procedures collects Med spectra and saves them to disk in
         conjunction with an EPICS scan record.
         epics_med.spectra_scan(first_file, scan_record)
      INPUTS:
         first_file:  
            The name of the first spectrum file to save.  Subsequent files 
            will be named using the INCREMENT_FILENAME()function.  The 
            filename must end in a numeric extension for this to work.
         scan_record:
            The name of the EPICS scan record which is controlling the scan.
            This scan record must be configure to start epicsMed data collection
            by writing "1" into the EraseStart record of the EPICS MED database.
      PROCEDURE:
         1) Wait for scan.EXSC = 1, meaning scan has started
         2) Wait for ClientWait=1, meaning acquisition has started
         3) Wait for Acquiring=0, meaning acquisition has completed
         4) Write data to disk with MED::WRITE_FILE, increment file name
         5) Reset ClientWait to 0 so scan will continue
         6) If scan.EXSC is still 1 go to 2.
      """
      file = first_file

      # Enable waiting for client
      self.pvs.enable_client_wait.putw(1)

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

         # Write file.  This resets the client wait flag
         self.write_file(file)
         print 'Saved file: ', file
         file = Xrf.increment_filename(file)
