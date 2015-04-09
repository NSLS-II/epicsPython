def localMedLayout():
   # This method must return a list of [X,Y] positions of each detector
   # element.  The origin is in the lower left as looking at the front of the
   # the detector, and the units are "detector widths".
   layout = [
         [1, 2], [1, 0], [2, 1], [0, 1]]  # Detectors 1-4
   return(layout)
