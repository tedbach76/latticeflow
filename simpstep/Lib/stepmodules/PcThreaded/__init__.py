# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.1.1.1 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/stepmodules/PcThreaded/__init__.py,v $

"""Multiprocessor version of STEP

Partitions LUT scans and hands them off to multiple processors.
The partitioning is simple---it cuts the space along the most
significant dimension into N partitions.

Threading is handled by the thread pool.  Threading is employed to
handle scans only. The main thread handles one portion of the space;
if more than one thread is requested, these threads handle the
remaining partitions.  When a scan is issued, the job is partitioned
among the pool members and the main thread waits for all of these
threads to finish before continuing.

The work load could perhaps be better balanced by giving the main
thread a smaller portion of the work (or even none of the work) and
postponing synchronization until the next STEP op is requested (or
even better yet, until the results that depend on the work are
needed).  This way, the main thread could take care of the SIMP
overhead while the others do STEP processing.

"""

import numarray as _na
import numarray.linear_algebra as _la
from simp.stepmodules.Pc import *
from simp.stepmodules.Pc import Step as PcStep
import scan
import threadpool

# Function for handling threads
# the first data element is the function that the thread should run.
def thread_do(data):
  func,data = data
  func(data)

class Step(PcStep):
  def __init__(self,size,verbose=1,**kwargs):
    if kwargs.has_key("nthread"): self.nthread = kwargs["nthread"]
    else: self.nthread = 4
    apply(PcStep.__init__,[self,size,verbose],kwargs)
    if self.nthread>1:
      self.pool = threadpool.easy_pool(thread_do)
      self.pool.start_threads(self.nthread-1)
    else:
      self.pool = None

  def __del__(self): 
    if self.pool!=None: # destroy threads if necessary
      # circular dependencies often stop this from being called, so
      # threadpool automatically calls stop_threads when sys.exitfunc
      # is called.
      self.pool.stop_threads()
      
  def __alloc_rule__(self,rule):
    """Create the position storage for a rule."""
    # call the original rule allocation code
    PcStep.__alloc_rule__(self,rule)
    # replace the doer with our multithreaded doer
    rule.__doer__ = scan.ScanDoer(rule,self.verbose,self.nthread)

  def __call_rule_doer__(self,rule,data):
      input_info,output_info,lut,lutshift,flags = data
      progs = rule.__doer__.get_scan_program(input_info,output_info)
      # schedule some of the threads
      for i in range(1,len(progs)): # self.nthread
         prog = progs[i]
         self.pool.put([rule.__doer__.do_lut_prog,[prog]+data])

      # main thread should do one part
      prog = progs[0]
      rule.__doer__.do_lut_prog([prog]+data)
      if self.pool!=None:
         # wait for the pool to finish the other partitions.
         self.pool.wait_for_idle()
