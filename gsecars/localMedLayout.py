def localMedLayout():
   # This method must return a list of [X,Y] positions of each detector
   # element.  The origin is in the lower left as looking at the front of the
   # the detector, and the units are "detector widths".
   layout = [
         [1, 3.5], [1, 2.5], [1, 1.5], [1, .5],  # Detectors 1-4
         [2, 4], [2, 3], [2, 2], [2, 1], [2, 0], # Detectors 5-9
         [3, 3.5], [3, 2.5], [3, 1.5], [3, .5],  # Detectors 10-13
         [0, 2.5], [0, 1.5],                     # Detectors 14-15
         [4, 2]]                                 # Detector 16
   return(layout)
