#   This module provides a number of utility functions for
#   X-ray fluorescence (XRF)
#
#   Author:  Mark Rivers
#   Created: Sept. 16, 2002
#   Modifications:

import os
import exceptions
class XrfError(exceptions.Exception):
   def __init__(self, args=None):
      self.args=args

atomic_symbols = (
   'H',  'He', 'Li', 'Be', 'B',  'C',  'N',  'O',  'F',  'Ne', 'Na', 'Mg', 'Al',
   'Si', 'P',  'S',  'Cl', 'Ar', 'K',  'Ca', 'Sc', 'Ti', 'V',  'Cr', 'Mn', 'Fe',
   'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 
   'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te',
   'I',  'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb',
   'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W',  'Re', 'Os', 'Ir', 'Pt',
   'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th', 'Pa',
   'U',  'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm')

xrf_dict = None
gamma_dict = None

def atomic_number(symbol):
      """
      Returns the atomic number of an element, given its atomic symbol 
  
      Inputs:
         symbol:
            The atomic symbol of the element whose atomic number is being
            requested.  This is a 1 or 2 character string, e.g. 'H', 'Si',
            etc.  It is case insensitive and leading or trailing blanks
            are ignorred.
            
      Outputs:
         This function returns the atomic number of the input element.  If an
         invalid atomic symbol is input then the function returns 0.
      """
      s = symbol.split()[0].upper()
      for i in range(len(atomic_symbols)):
         if (s == atomic_symbols[i].upper()): return i+1
      return None


def atomic_symbol(z):
      """
      This function returns the atomic symbol of an element, given its atomic
      number.
      
      Inputs:
         z:
            The atomic number of the element whose atomic symbol is being
            requested.  

       Outputs:
          This function returns the atomic symbol of the input element as a
          string.  If Z is an invalid atomic number then the function returns 
          None.
      """
      if (z > 0) and (z <= len(atomic_symbols)): return(atomic_symbols[z-1])
      return None


def lookup_xrf_line(xrf_line):
   """
   This function returns the energy in keV for a particular x-ray
   fluorescence line.

   Inputs:
      xrf_line:
         A string of the form 'Element Line', where Element is an
         atomic symbol, and Line is an acronym for a fluorescence line.
         Both Element and Line are case insensitive.  There must be a space
         between Element and Line.
         The valid lines are
             ka  - K-alpha (weighted average of ka1 and ka2)
             ka1 - K-alpha 1
             ka2 - K-alpha 2
             kb  - K-beta (weighted average of kb1 and kb2)
             kb1 - K-beta 1
             kb2 - K-beta 2
             la1 - L-alpha 1
             lb1 - L-beta 1
             lb2 - L-beta 2
             lg1 - L-gamma 1
             lg2 - L-gamma 2
             lg3 - L-gamma 3
             lg4 - L-gamma 4
             ll  - L-eta

      Examples of XRF_Line:
          'Fe Ka'  - Fe k-alpha
          'sr kb2' - Sr K-beta 2
          'pb lg2' - Pb L-gamma 2

   Outputs:
      This function returns the fluoresence energy of the specified line.
      If the input is invalid, e.g. non-existent element or line, then the
      function returns None

   Restrictions:
      This function uses the environment variable XRF_PEAK_LIBRARY to locate
      the file containing the database of XRF lines.  This environment
      variable must be defined to use this function.  On Unix systems
      this is typically done with a command like
      setenv XRF_PEAK_LIBRARY
                  /usr/local/idl_user/epics/mca/xrf_peak_library.txt
      On Windows NT systems this is typically done with the
              Settings/Control Panel/System/Environment control.

      If lookup_xrf_line() encounters an error in resolving the environment
      variable or in reading the file it raises an XrfError exception.

   Procedure:
      The first time this function is called it reads in the table from the
      file pointed to by the environment variable.  On all calls it looks
      up the element using function atomic_number() and searches for the
      specified line in the table.  It returns 0. if the element or line
      are invalid.

   Examples:
      energy = lookup_xrf_line('Fe Ka')  ; Look up iron k-alpha line
      energy = lookup_xrf_line('Pb lb1') ; Look up lead l-beta 1 line
   """
   nels = 100   # Number of elements in table
   nlines = 14  # Number of x-ray lines in table

   global xrf_dict
   # The database is a dictionary in the form xrf_dict{'FE': {'KA':6.400}}
   # Read in the data table if it has not already been done
   if (xrf_dict == None):
      xrf_dict = {}
      file = os.getenv('XRF_PEAK_LIBRARY')
      if (file == None):
         raise XrfError, 'XRF_PEAK_LIBRARY environment variable not defined'
      try:
         fp = open(file,'r')
         line = fp.readline()
         words = line.split()
         line_list = []
         for i in range(nlines):
            line_list.append(words[2+i].upper())
         for el in range(nels):
            s = atomic_symbols[el].upper()
            line = fp.readline()
            energy = line.split()
            e = {}
            for i in range(nlines):
               e[line_list[i]] = float(energy[2+i])
            xrf_dict[s] = e
         fp.close()
      except:
         raise XrfError, 'Error reading XRF_PEAK_LIBRARY file'

   try:
      words = xrf_line.split()
      return xrf_dict[words[0].upper()][words[1].upper()]
   except:
      return None


def lookup_gamma_line(gamma_line):
   """
   Returns the energy in keV for a particular gamma emmission line.

   Inputs:
      gamma_Line:
         A string of the form 'Isotope Line', where Isotope is a
         the symbol for a radioactive isotope, and Line is an index of the form
         g1, g2, ... gn.
         Both Isotope and Line are case insensitive.  There must be a space
         between Isotope and Line.

         Examples of Gamma_Line:
            'Cd109 g1'  - 88 keV line of Cd-109
            'co57 g2'   - 122 keV line of Co-57

   Outputs:
      This function returns the gamma energy of the specified line.
      If the input is invalid, e.g. non-existent isotope or line, then the
      function returns 0.

   Restrictions:
       This function only knows about a few isotopes at present.  It is
       intended for use with common radioactive check sources.  It is easy to
       add additional isotopes and gamma lines to this function as needed.
       The current library is:
           'CO57 G1' = 14.413
           'CO57 G2' = 122.0614
           'CO57 G3' = 136.4743
           'CD109 G1'= 88.04

   Example:
       energy = lookup_gamma_line('Co57 g1')  ; Look up 14 keV line of Co-57
   """
   global gamma_dict
   if (gamma_dict == None):
      gamma_dict = {}
      gamma_dict['CO57'] = {}
      gamma_dict['CO57']['G1'] = 14.413
      gamma_dict['CO57']['G2'] = 122.0614
      gamma_dict['CO57']['G3'] = 136.4743
      gamma_dict['CD109'] = {}
      gamma_dict['CD109']['G1'] = 88.04

   try:
      words = gamma_line.split()
      return gamma_dict[words[0].upper()][words[1].upper()]
   except:
      return None


def increment_filename(old_file):
   """
   Increments the file extension if it is numeric.  It preserves the number of
   characters in the extension.
   
   Examples:
      print increment_filename('test.001')
         test.002
      print increment_filename('test')
         test
      print increment_filename('file.1')
         file.2
   """
   dot = old_file.rfind('.')
   if (dot == -1): return old_file
   if (dot+1 == len(old_file)): return old_file

   ext = old_file[dot+1:]
   file = old_file[0:dot+1]
   nc = str(len(ext))
   try:
      ext = int(ext)+1      # Convert to number, add one, catch error
      format = '%' + nc + '.' + nc + 'd'
      ext = (format % ext)
      new_file = file + ext
      return new_file
   except:
      return old_file
