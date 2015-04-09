"""
Support for the EPICS "scaler" record.

Author:         Mark Rivers 
Created:        Sept. 16, 2002. 
Modifications:
"""
import epicsPV
import time

class epicsScaler:
   def __init__(self, name):
      """
      Creates a new epicsScaler instance.
      
      Inputs:
         name:
            The name of the EPICS scaler record, without the trailing period
            or field name.
            
      Example:
         s = epicsScaler('13IDC:scaler1')
      """
      self.nchans = epicsPV.epicsPV(name+'.NCH').getw()
      self.pvs = {'count': epicsPV.epicsPV(name+'.CNT'), 
                  'preset_time': epicsPV.epicsPV(name+'.TP'),
                  'preset':[], 'counts':[], 'label':[]}
      for i in range(1, self.nchans+1): 
         self.pvs['preset'].append(epicsPV.epicsPV(name+'.PR'+str(i)))
         self.pvs['counts'].append(epicsPV.epicsPV(name+'.S'+str(i)))
         self.pvs['label'].append(epicsPV.epicsPV(name+'.NM'+str(i)))
# Wait for all PVs to connect
      self.pvs['count'].pend_io()

   def setTime(self,time):
      """
      Skinner added
      """
      self.pvs['preset_time'].putw(time)


   def getTime(self):
      """
      Skinner added
      """
      return self.pvs['preset_time'].getw()


   def start(self, time=None):
      """
      Starts the scaler.
      
      Keywords:
         time:
            The desired count time.  If time is not specified then the current
            counting time is preserved.
      """
      if (time != None):
         self.pvs['count'].putw(0)
         self.pvs['preset_time'].putw(time)
         self.pvs['count'].putw(1)
      else:
         self.pvs['count'].putw(0)
         self.pvs['count'].putw(1)

   def stop(self):
      """
      Immediately stops the scaler from counting.
      """
      self.pvs['count'].putw(0)

   def read(self, scaler=None):
      """
      Returns the current counts on the scaler.  The default is to return a list
      of counts, one for each of the .Sn fields in the record, i.e.
      [.S1, .S2 ...].  If the scaler keyword is specified then only the counts
      on that scaler are returned.
      
      Keywords:
         scaler:
            The number of the specific scaler channel to read and return.

      Example:
         s = epicsScaler('13IDC:scaler1')
         counts = s.read()
         count1 = s.read(1)
      """
      if (scaler == None):
         counts = []
         for i in range(self.nchans):
            self.pvs['counts'][i].array_get()
         self.pvs['count'].pend_io()
         for i in range(self.nchans):
            counts.append(self.pvs['counts'][i].getValue())
      else:
         counts = self.pvs['counts'][scaler].getw()
      return counts
   
   def get_label(self, scaler=None):
      """
      Returns the descriptive strings for the scaler inputs.
      The default is to return a list of strings, one for each of the .NMn
      fields in the record, i.e. [.NM1, .NM2 ...].  If the scaler keyword is
      specified then only the string for that scaler are returned.
      
      Keywords:
         scaler:
            The number of the specific scaler channel to return the label for.

      Example:
         s = epicsScaler('13IDC:scaler1')
         labels = s.get_label()
         label1 = s.get_label(1)
      """
      if (scaler == None):
         labels = []
         for i in range(self.nchans):
            self.pvs['label'][i].array_get()
         self.pvs['count'].pend_io()
         for i in range(self.nchans):
            labels.append(self.pvs['label'][i].getValue())
      else:
         labels = self.pvs['label'][scaler].getw()
      return labels

   def set_label(self, label, scaler):
      """
      Writes a new descriptive label strings to the specified scaler channel.

      Inputs:
         label:
            The label string.

         scaler
            The number of the specific scaler channel to write the label to.

      Example:
         s = epicsScaler('13IDC:scaler1')
         s.set_label('Ion chamber counts', 2)
      """
      self.pvs['label'][scaler].putw(label)

   def wait(self, start=None, stop=None, poll=0.1):
      """
      Waits for the scaler to start or stop counting.
      
      Keywords:
         start:
            Set start=1 to wait for the scaler to start.
            
         stop:
            Set stop=1 to wait for the scaler to stop.
            
         poll:
            Set this keyword to the time to wait between reading the
            .CNT field of the record to see if the scaler is counting.
            The default is 0.1 seconds.
            
      Notes:
         If neither the "start" nor "stop" keywords are set then "stop"
         is set to 1, so the routine waits for the scaler to stop counting.
         If only "start" is set to 1 then the routine only waits for the
         scaler to start counting.
         If both "start" and "stop" are set to 1 then the routine first
         waits for the scaler to start counting, and then to stop counting.
         
      Example:
         s=epicsScaler('13BMD:scaler1')
         s.start(10.)              # Start counting for 10 seconds
         s.wait(start=1, stop=1)   # Wait for the scaler to start counting
                                   # and then to stop counting
      """
      if (start == None) and (stop == None): stop=1
      if (start != None):
         while(1):
            counting = self.pvs['count'].getw()
            if (counting != 0): break
            time.sleep(poll)
      if (stop != None):
         while(1):
            counting = self.pvs['count'].getw()
            if (counting == 0): break
            time.sleep(poll)
