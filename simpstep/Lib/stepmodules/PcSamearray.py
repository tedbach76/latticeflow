# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.1.1.1 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/stepmodules/PcSamearray.py,v $

"""
Static PC STEP implementation that allocates signals on the same data array
to increase data locality.
"""

import numarray as _na
import numarray.linear_algebra as _la
from simp.stepmodules.Pc import *
import simp.stepmodules.Pc._scan as _scan

class Step(Step):
  def __alloc_signal__(self,sig):
    # signals contains[cur_arr,out_arr]
    # (arrays for the current and output state
    type = sig.type
    if not isinstance(sig,OutSignal) and not isinstance(type,step.SmallUInt):
      raise StepError, \
         "PcSamearray STEP currently only handles SmallUInt signals"
    if isinstance(sig,OutSignal):
      # Only allocate the output array since an output signal is output only
      self.signals[sig] = [None, 
                           _na.zeros(sig.shape,_na.UInt8)]
    else:
      # Allocate two arrays---one to hold outputs and one to hold inputs
      arr = _na.zeros(list(sig.shape)+[2],_na.UInt8)
      
      self.signals[sig] = [arr[...,0], # array
                           arr[...,1]]
    self.positions[sig] = [0]*sig.nd
