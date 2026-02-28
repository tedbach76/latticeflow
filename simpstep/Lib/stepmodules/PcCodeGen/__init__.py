# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.5 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/stepmodules/PcCodeGen/__init__.py,v $

""" PcCodeGen

Code generating, threaded STEP implementation. 

"""



import numarray as _na
import numarray.linear_algebra as _la
#from simp.stepmodules.Pc import *
from simp.stepmodules.Pc import Step as PcStep
from simp.stepmodules.PcThreaded import *

import scan
import PyInline
import simp.cache
from simp.step import *

import simp.stepmodules.PcThreaded.threadpool as threadpool

def test_build(distutils_args):
      m = PyInline.build(code="""
      int i = 5;
        double my_add(double a, double b) {
          return a + b + i;
        }
      """,cacheroot=simp.cache.CACHEDIR,
      distutils_args=distutils_args,rebuild=1)

distutils_args=[]
try:
  # test for pyinline. import fails if it does not work
  try: 
      test_build(distutils_args)
  except: 
      try: # try for mingw32 (just in case windows compler not installed)
	import os
        #todo: querry this from "Cygnus Solutions\Cygwinmounts v2\"/usr/bin""
	os.environ["PATH"]=os.environ["PATH"]+";C:\\cygwin\\bin"
        distutils_args = ["--compiler=mingw32"]
        test_build(distutils_args=distutils_args)
      except Exception,e: 
        print e
        print "import error"
	raise ImportError
except:
  raise ImportError, "Unable to build test"


Step = PcStep

class Step(PcStep):

  def __init__(self,size,verbose=1,**kwargs):
    # nthread
    if kwargs.has_key("nthread"): self.nthread = kwargs["nthread"]
    else: self.nthread = 1
    # maxlutsize
    self.maxlutsize = 16
    if kwargs.has_key("maxlutsize"): self.maxlutsize = kwargs["maxlutsize"]
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

  def __alloc_signal__(self,sig):
    # signals contains[cur_arr,out_arr]
    # (arrays for the current and output state
    if isinstance(sig.type,SmallUInt):
      datatype = UInt8
    elif sig.type in numarraytypes:
      datatype = sig.type
    else:
      raise StepError, "Unsupported signal data type ", sig.type

    if isinstance(sig,OutSignal):
      # Only allocate the output array since an output signal is output only
      self.signals[sig] = [None, 
                           _na.zeros(sig.shape,datatype)]
    else:
      # Allocate two arrays---one to hold outputs and one to hold inputs
      self.signals[sig] = [_na.zeros(sig.shape,datatype), # array
                           _na.zeros(sig.shape,datatype)]
    self.positions[sig] = [0]*sig.nd

  def __call_rule_doer__(self,rule,data):
      input_info,output_info,lut,lutshift,flags = data
      progs = rule.__doer__.get_scan_program(input_info,output_info)
      # schedule some of the threads
      for i in range(1,len(progs)): # self.nthread
         prog = progs[i]
         self.pool.put([rule.__doer__.do_scan,[prog]+data])

      # main thread should do one part
      prog = progs[0]
      rule.__doer__.do_scan([prog]+data)
      if self.pool!=None:
         # wait for the pool to finish the other partitions.
         self.pool.wait_for_idle()

#  def __call_rule_doer__(self,rule,data):
#      apply(rule.__doer__.do_lut,data)

  def __alloc_rule__(self,rule):
    """Create the position storage for a rule."""

    # initialize the input and output info
    rule.__input_offsets__ = [sig.neighbor_offset() for sig in rule.inputs]
    rule.__output_offsets__ = [sig.neighbor_offset() for sig in rule.outputs]
    rule.__base_inputs__ = [sig.base_signal() for sig in rule.inputs]
    rule.__base_outputs__ = [sig.base_signal() for sig in rule.outputs]

    # determine whether the LUT is wide or not
    lut_width = reduce(lambda x,y:x+lut.binary_info(y)[0],
                       rule.__base_outputs__,0)

    lut_size = reduce(lambda x,y:x+lut.binary_info(y)[0],
                       rule.__base_inputs__,0)

    if lut_size>self.maxlutsize:
      if self.verbose:
         str=("COMPILING C TRANSITION FUNCTION FOR %s INSTEAD OF LUT.\n"%rule)+\
               """The function has %i bits of input which is larger than the maxlutsize=%i. Because rules for C transition functions are more restrictive,the process may fail. Use a different engine, or adjust the maxlutsize STEP parameter (as in initialize(... , stepargs={"maxlutsize":%i}) ) to use a LUT instead.""" % (lut_size,self.maxlutsize,lut_size)
      self.__init_rule_nolut__(rule)
      rule.__doer__ = scan.ScanDoer(rule,self.verbose,
                                    ctransitionfun=1,nthread=self.nthread,
			            distutils_args=distutils_args)
      rule.__wide_lut__ = 0
      rule.__lut_shift__ = 0    
    else: 
       if lut_width>32:
           rule.__wide_lut__=1
           self.__init_rule_widelut__(rule)
           part_lut_width = len(lut.word_partition_outputs(rule.outputs))
           next_pow = int(math.ceil(math.log(part_lut_width)/math.log(2)))
           rule.__lut_shift__ = next_pow+2
       else:
           self.__init_rule_narrowlut__(rule)      
           rule.__wide_lut__=0
           rule.__lut_shift__ = 2

       # create the rule doer that uses a LUT
       rule.__doer__ = scan.ScanDoer(rule,self.verbose,
                                     ctransitionfun=0,nthread=self.nthread,
  			             distutils_args=distutils_args)    
         
      
    # initialize the position of the rule. 
    self.positions[rule] = [0]*rule.nd

    # determine the input signals that don't appear as outputs
    input_only = []
    for sig in rule.__base_inputs__:
      if not rule.__output_cosets__.has_key(sig):
        input_only.append(sig)
    rule.__input_only__=input_only


  def __init_rule_nolut__(self,rule):
    rule.__lut__ = None
    rule.__input_info__ = []
    shift = 0
    for i in xrange(len(rule.inputs)):
        nbits,mask,mask_ = lut.binary_info(rule.inputs[i])
        info = [-1,mask,-1,shift,0,-1,[-1]*self.nd]
        rule.__input_info__.append(info)        
        shift+=nbits
    rule.__output_info__ = []
    shift = 0
    for i in xrange(len(rule.outputs)):
        nbits,mask,mask_ = lut.binary_info(rule.outputs[i])
        info = [-1,mask<<shift,mask_,0,shift,-1,[-1]*self.nd]
        rule.__output_info__.append(info)        
        shift+=nbits
    

