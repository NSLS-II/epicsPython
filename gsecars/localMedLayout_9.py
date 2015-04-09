def localMedLayout():
   # This method must return a list of [X,Y] positions of each detector
   # element.  The origin is in the lower left as looking at the front of the
   # the detector, and the units are "detector widths".
   layout = [
         [0, 2], [1, 2], [2, 2],  # Detectors 1-3
         [0, 1], [1, 1], [2, 1],  # Detectors 4-6
         [0, 0], [1, 0], [2, 0]]  # Detectors 7-9
   return(layout)
