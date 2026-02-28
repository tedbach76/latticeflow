# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.6 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/stepmodules/Pc/__init__.py,v $

"""
The Pc STEP module implementation.

Pure Python implementation that aims to be clean, simple
and correct, but not efficient.

Does all operations immediately.

Rather than building LUTs to implement a rule, it implements rules
directly using the function.  Code analysis still must be performed to
determine the inputs and outputs of the function. 
"""

# INPUT/OUTPUT Info
#  : inputs (pointer,mask,shift_l,shift_r,inc) // 5*Nin
#  : outputs (pointer,in_mask,~out_mask,shift_l,shift_r,inc) // 6*Nout




import time, weakref

import numarray as _na
import numarray.linear_algebra as _la
import simp.step as step
from simp.step import *
#from simp.stephelpers import *
import simp.geom as geom
import simp.import_locally as import_locally

import copy,math
import simp.cache as cache

# Helper modules
#import simp.stepmodules.pc.lut as lut
#import simp.stepmodules.pc.lut as 
import lut,scan,_scan
  

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#            HELPERS
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=      

#def array_element(generator_,coord):
#  """Returns the array element of a lattice point under the rectangular
#  mapping"""

#def make_array(signal):
#   Make an array for holding 'signal'

def row_slice(indx):
  """Convert a row vector to a slice object"""
  return tuple(indx)[:-1]+(slice(None),)

def move_origin_subscripts(new_origin,shape):
    """Returns a set of subscripts that can be used to copy
    an array with shape 'shape' to a new origin given by 'new_origin'
    Specifically, the result is [[output_subscr,input_subscr]....]"""
    nd = len(new_origin)
    subscripts = []
    subscripts = [[[slice(None)]*nd,[slice(None)]*nd]]    
    for i in xrange(nd):
        indx = (new_origin[i])%shape[i]
        shape_ = shape[i]
        if indx==0: continue  # no shift needed
        # otherwise, break up the slices...
        out_slice0 = slice(0,shape_-indx);in_slice0 = slice(indx,shape_); 
        out_slice1 = slice(shape_-indx,shape_); in_slice1 = slice(0,indx)
        
        for j in xrange(len(subscripts)):
            out_sub0,in_sub0 = subscripts[j]
            out_sub1,in_sub1 = copy.copy(out_sub0),copy.copy(in_sub0)
            out_sub0[i]=out_slice0; in_sub0[i]=in_slice0;
            out_sub1[i]=out_slice1; in_sub1[i]=in_slice1;            
            subscripts.append([out_sub1,in_sub1])
    return subscripts

def na_move_origin(array,new_origin,output=None):
    """Returns a numarray with its origin moved to 'new_origin'"""
    if output==None:
        output = _na.zeros(array.shape,type=array.type())
    subscripts = move_origin_subscripts(new_origin,array.shape)
    for out_subscr,in_subscr in subscripts:
        output[out_subscr] = array[in_subscr]
    return output

def make_slice(start,stop,step=1):
  if stop==start+1: return start
  return slice(start,stop)

def region_to_wrapped_slices(region,position):
    """Used for generating the slices needed to read and write slices
    from and to an array region that wraps around to and from a full array.
    Returns a set of up to 2^n slices."""
    spacing = region.lat_arr.spacing
    start = (region.start + position)/spacing;
    shape = region.lat_arr.shape
    nd = region.lat_arr.nd
    if region.stop==None: return [[_na.zeros(nd),tuple(start)]]

    # the more difficult case where regions may wrap around
    # The algorithm:
    #   split up the subscripts along each dimension, duplicating the subscript
    #   if it wraps around. 
    stop = (region.stop+position)/spacing
    subscripts = [[[slice(None)]*nd,[None]*nd]]
    for i in xrange(nd):
        start_ = start[i]; stop_ = stop[i]; shape_ = shape[i]
        if stop_==0: stop_ = region.lattice.shape[i]/diag[i]
        # Compute the slices.
        if stop_<=shape_: # doesn't wrap around
            for arr_slc,wrap_slc in subscripts:
                wrap_slc[i] = make_slice(start_,stop_)
        else: # wraps around a boundary
            arr_slc0_ = make_slice(0,shape_-start_)
            arr_slc1_ = make_slice(shape_-start_,stop_-start_)
            wrap_slc0_ = make_slice(start_,shape_)
            wrap_slc1_ = make_slice(0,stop_-shape_)
            # Duplicate each slice region in this dimension...
            for j in xrange(len(subscripts)):
                arr_slc0,wrap_slc0 = subscripts[j]
                arr_slc1=copy.copy(arr_slc0);wrap_slc1=copy.copy(wrap_slc0)
                arr_slc0[i] = arr_slc0_; arr_slc1[i] = arr_slc1_
                wrap_slc0[i] = wrap_slc0_; wrap_slc1[i] = wrap_slc1_
                
                subscripts.append([arr_slc1,wrap_slc1])
    return subscripts
  
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#            STEP INTERFACE
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=      

class Step(step.Step):
  # signals : allocated signals
  #    - keyed on signal
  #    - value list [array,position,array_offset]
  #        array : UInt8 numarray containing current signal values
  #        position : current position modulo the lattice
  # rules : currently known rules
  #    - keyed on the rule
  #    - value list [position]
  
  # -------------------------------- STEP INTERFACE
  def __init__(self,size,verbose=1,**kwargs):
    self.verbose = verbose
    self.size = size
    self.nd = len(size)
#    self.signals = weakref.WeakKeyDictionary()
#    self.rules = weakref.WeakKeyDictionary()
    self.signals = {}
    self.output_signals = {}
    self.positions = {}
    # private copy of the random module
    self.random = import_locally.import_copy("random")
    self.SeedRandom(time.time())
    
  def Do(self,op,*vargs,**kwargs):
    """Do (or enqueue) a step operation"""
    if isinstance(op,Rule):
      self.__do_rule__(op)
    elif isinstance(op,Read):
#      if op.rule==None:
        return self.__do_read_values__(op,vargs)
#      else:
#        return self.__do_rendered_read__(op,vargs)
    elif isinstance(op,Write): self.__do_write__(op,vargs)
    elif isinstance(op,Sequence):
        # XXX add handlers for parallel ops       
        for op in op.ops: self.Do(op)
    elif isinstance(op,Shift):
      self.__do_shift__(op)
    elif isinstance(op,Shuffle):
      self.__do_Shuffle__(op)
    elif isinstance(op,GetCoset):
      position = self.positions[op.object]
      spacing = op.object.spacing
      return [position[i]%spacing[i] for i in xrange(len(position))]
    elif isinstance(op,SetCoset):
      for latarr in op.positions.keys():
        pos = copy.copy(op.positions[latarr])
#        if isinstance(pos,LatticeArray):
#            pos = copy.copy(self.positions[latarr])
#        else:
#            pos = copy.copy(op.position)          
        # set the coset position (only)
#        curpos = self.positions[latarr]
#        for i in xrange(len(pos)):
#          spacing_ = latarr.spacing[i] 
#          pos[i]=(pos[i]%spacing_)+(curpos[i]/spacing_)*spacing_
#        self.positions[latarr]=pos

        for i in xrange(len(pos)):
          spacing_ = latarr.spacing[i] 
          pos[i]=(pos[i]%spacing_)+(pos[i]/spacing_)*spacing_
        self.positions[latarr]=pos

#      if isinstance(op.position,LatticeArray):
#          pos = copy.copy(self.positions[op.position])
#      else:
#          pos = copy.copy(op.position)          
#      # set the coset position (only)
#      curpos = self.positions[op.object]
#      for i in xrange(len(pos)):
#        spacing_ = op.object.spacing[i]                
#        pos[i]=(pos[i]%spacing_)+(curpos[i]/spacing_)*spacing_
#      self.positions[op.object]=pos
##      position = [((position/spacing[i])*spacing[i]) + op.position[i]
##                  for i in xrange(len(position))]
    elif isinstance(op,step.Op):
      raise StepError,"Don't know how to handle",ob
    else:
      raise StepError,"%s is not a step operation" % ob


  def Register(self,ob):
    """Register an operation or signal or operation with the step"""
    # Handle registrations for the different types

    if isinstance(ob,step.OutSignal): self.__alloc_signal__(ob)
    elif isinstance(ob,step.Signal): self.__alloc_signal__(ob)
    elif isinstance(ob,step.Rule): self.__alloc_rule__(ob)
    elif isinstance(ob,Read): pass
#      if ob.rule!=None:
#        self.__register_rend_read__(ob)
    elif isinstance(ob,Write): pass
    elif isinstance(ob,Sequence): pass
    elif isinstance(ob,GetCoset): pass
    elif isinstance(ob,SetCoset): pass    
    elif isinstance(ob,Shift):  self.__register_shift__(ob)
    elif isinstance(ob,Shuffle): pass
    elif isinstance(ob,step.Op):
      raise StepError,"Don't know how to handle",ob
    else:
      raise StepError, `ob`+" is not a step object"
  
  def Flush(self):
    """Flush all pending operations"""
    pass

  def SeedRandom(self,seed):
    """Seed the random number generator"""
    self.random.seed(int(seed)%256)

  def ClearCache(self):
    """If the STEP caches values, clear the cache."""
    cache.clear_cache()

  # -------------------------------- PRIVATE METHODS
  def __alloc_signal__(self,sig):
    # signals contains[cur_arr,out_arr]
    # (arrays for the current and output state
    type = sig.type
    if not isinstance(sig,OutSignal) and not isinstance(type,step.SmallUInt):
      raise StepError, \
         "The Pc STEP currently only handles SmallUInt signals"
    if isinstance(sig,OutSignal):
      # Only allocate the output array since an output signal is output only
      self.signals[sig] = [None, 
                           _na.zeros(sig.shape,_na.UInt8)]
    else:
      # Allocate two arrays---one to hold outputs and one to hold inputs
      self.signals[sig] = [_na.zeros(sig.shape,_na.UInt8), # array
                           _na.zeros(sig.shape,_na.UInt8)]
    self.positions[sig] = [0]*sig.nd


  def __do_rule__(self,rule):
    input_info = rule.__input_info__
    output_info = rule.__output_info__
    rule_position = self.positions[rule]

    # Do shifts for any inputs that need adjustment and will not automatically
    # be adjusted by virture of appearing in the outputs. (This minimizes
    # the number of new scans that need to be compiled.)
    for sig in rule.__input_only__:
      position = self.positions[sig]
      new_origin = []; allzero = 1
      for i in xrange(len(position)):
        new_origin_ = -(position[i]/sig.spacing[i])
        if new_origin_!=0:allzero = 0
        new_origin.append(new_origin_)
      if not allzero:
        # Do the shift to adjust the position
        input,output = self.signals[sig]
        na_move_origin(input,new_origin,output) # could speed this up!
        # Flip the input and output arrays
        self.signals[sig] = [output,input]
        # Adjust the remainder of the position
        self.positions[sig] = sig.__coset_coordinate__(position)        
#        for j in xrange(sig.nd):
#          position[j] = position[j]%sig.spacing[j]
          
    # Update the input and output info
    # assume that the shifts and masks have already been computed
    for i in xrange(len(rule.inputs)):
        sig = rule.__base_inputs__[i]
        info = input_info[i]        
        # XXX don't really need to recompute positions when the signal is
        # orthogonal...
        position = self.positions[sig]
        neighbor_offset = rule.__input_offsets__[i]
       
        current,output = self.signals[sig]
        # set the numarray pointers and the stride
        info[0] = _scan.na_ptr(current)
        info[5] = current._strides
        # compute neighbor offsets
        ofst = info[6]
        for j in xrange(sig.nd):
          ofst[j] = rule_position[j]-position[j]+neighbor_offset[j]
          ofst[j]=(ofst[j]%sig.size[j])

    # XXX need to handle the case where the outputs don't cover...
    for i in xrange(len(rule.outputs)):
        sig = rule.__base_outputs__[i]
        info = output_info[i]        
        position = self.positions[sig]
        neighbor_offset = rule.__output_offsets__[i]
        current,output = self.signals[sig]
        # set the numarray pointers and the stride
        info[0] = _scan.na_ptr(output)
        info[5] = output._strides
        info = output_info[i]        
        # compute neighbor offsets
        ofst = info[6]
        for j in xrange(sig.nd):
            position_ = position[j]%sig.spacing[j]
            ofst[j] = rule_position[j]-position_+neighbor_offset[j]   
            ofst[j]=(ofst[j]%sig.size[j])            
          
    for sig in rule.__output_cosets__.keys():
        if not isinstance(sig,OutSignal):
          current,output = self.signals[sig]          
          if len(rule.__output_cosets__[sig][1])!=0:
              # Outputs don't cover, so set default values
              # XXX temporary hack---need to adjust for shifts too!
              # adjust for shift (with a new origin) if necessary.
              position = self.positions[sig]
              new_origin = []; allzero = 1
              for i in xrange(len(position)):
                new_origin_ = -(position[i]/sig.spacing[i])
                if new_origin_!=0:allzero = 0
                new_origin.append(new_origin_)
              if allzero:
                # just do a simple copy
                output.flat[:] = current.flat[:]
              else:
                # do any pending shift.
                na_move_origin(current,new_origin,output)
               
          # Flip the input and output arrays
          self.signals[sig] = [output,current]

        else: # Output Signals 
          if len(rule.__output_cosets__[sig][1])!=0:
            # Outputs don't cover, so set default values
             output.flat[:]=0
              
        # adjust the position---eliminate the portion that is a multiple
        # of the spacing---leave only the coset position.
        position = self.positions[sig]
        self.positions[sig] = sig.__coset_coordinate__(position)        
#        for j in xrange(sig.nd):
#            position[j] = position[j]%sig.spacing[j]
      
    # Finally, do the operation
    if rule.__wide_lut__:
         self.__call_rule_doer__(rule,[input_info,output_info,rule.__lut__,
                                rule.__lut_shift__,scan.SCAN_WIDELUT])
    else:
         self.__call_rule_doer__(rule,[input_info,output_info,rule.__lut__,
                                  rule.__lut_shift__,0])
    
  def __call_rule_doer__(self,rule,data):
      apply(rule.__doer__.do_lut,data)
#    for sig in rule.inputs:
#      current,output = self.signals[sig.base_signal()]
#
#    for sig in rule.outputs:
#      current,output = self.signals[sig.base_signal()]

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
      
   
    # initialize the position of the rule. 
    self.positions[rule] = [0]*rule.nd

    # determine the input signals that don't appear as outputs
    input_only = []
    for sig in rule.__base_inputs__:
      if not rule.__output_cosets__.has_key(sig):
        input_only.append(sig)
    rule.__input_only__=input_only

    # create the rule doer
    rule.__doer__ = scan.ScanDoer(rule,self.verbose)    

  def __init_rule_widelut__(self,rule):
    # initialization for a rule with a wide LUT
    rule.__lut__ = lut.get_rule_lut(rule,wide=1,verbose=self.verbose)
    rule.__input_info__ = []    
    shift = 0
    for i in xrange(len(rule.inputs)):
        nbits,mask,mask_ = lut.binary_info(rule.inputs[i])
        info = [-1,mask,-1,shift,0,-1,[-1]*self.nd]
        rule.__input_info__.append(info)        
        shift+=nbits
    rule.__output_info__ = []
    shift = 0;offset=0;
    for i in xrange(len(rule.outputs)):
        nbits,mask,mask_ = lut.binary_info(rule.outputs[i])
        if shift+nbits>32:
          shift=0
          offset+=1
        info = [-1,mask<<shift,mask_,offset*4,shift,-1,[-1]*self.nd]
        rule.__output_info__.append(info)        
        shift+=nbits
    

  def __init_rule_narrowlut__(self,rule):
    # initialization for a rule with a narrow LUT
    
    # Pre-allocate the info structure. Fields with values of -1
    # will be filled in later when the rule is called.

    # allocate the LUT
    rule.__lut__ = lut.get_rule_lut(rule,verbose=self.verbose)          
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


  def __do_write__(self,wr,values):
    if wr.values!=None: values = wr.values
    else: values = values[0] # decode the kwargs

    for i in xrange(len(wr.signals)):
      arr,out_arr = self.signals[wr.signals[i]]
      pos = self.positions[wr.signals[i]]
      slices = region_to_wrapped_slices(wr.region,pos)      
      for in_slc,wrap_slc in slices:
        val = values[i]
        if isinstance(val,_na.NumArray):
          arr[tuple(wrap_slc)] = val[tuple(in_slc)]  
        else:
          arr[tuple(wrap_slc)] = val

  def __register_shift__(self,shift):
    # signals with data to be shifted 
    shift.__signals__ = \
        filter(lambda x: isinstance(x,Signal) and not isinstance(x,OutSignal)
               ,shift.shifts.keys())
    shift.__signal_shifts__ = [geom.asintarray(shift.shifts[sig])
                              for sig in shift.__signals__]
                               
    # lattice arrays with only positions to be shifted
    shift.__latarrs__ = \
        filter(lambda x: isinstance(x,Rule) or isinstance(x,OutSignal),
               shift.shifts.keys())
    shift.__latarr_shifts__ = [geom.asintarray(shift.shifts[latarr])
                               for latarr in shift.__latarrs__]

#  def __register_Shuffle__(self,Shuffle):
    
  def __do_Shuffle__(self,Shuffle):
    for ob in Shuffle.Shuffle:
      position = self.positions[ob]      
      if (isinstance(ob,OutSignal) or not isinstance(ob,Signal)):
          # output signals or lattice array objects
          for i in xrange(len(ob.spacing)):
            position[i] = self.random.randrange(ob.spacing[i])
      elif (isinstance(ob,Signal)):
          # randomize coset position then do a random shift

          # XXX we eliminate this to eliminate unnecessary recompilations
          #     of the scan program, however, this may be a bad thing.
          
#          for i in xrange(len(ob.spacing)):          
#             position[i] = self.random.randrange(ob.spacing[i])
          # Shuffle the array with a random circular shift on the flat
          # version of the array
          input,output = self.signals[ob]
          input_,output_ = input.flat,output.flat
          length = len(input_)
          cut = self.random.randint(0,length)
          output_[0:cut]=input_[length-cut:length]
          output_[cut:length]=input_[0:length-cut]          
          self.signals[ob] = [output,input]
          #           +self.size[i]/4-ob.spacing[i]*3)%self.size[i]
#             position[i] = (self.size[i]/4-ob.spacing[i]*3)%self.size[i]
            
#          new_origin = []
#          for i in xrange(len(ob.shape)):
#            new_origin.append(self.random.randrange(ob.spacing[i]))
#          self.signals[ob][0] = \
#                na_move_origin(self.signals[ob][0],new_origin)          

  def __do_shift__(self,shift):

    # First do the lattice array objects
    for i in xrange(len(shift.__latarrs__)):
        latarr = shift.__latarrs__[i]
        position = self.positions[latarr]
        geom.add(position,shift.__latarr_shifts__[i],position)
        print latarr.__coset_coordinate__(position)
        self.positions[latarr] = latarr.__coset_coordinate__(position)
        
    # Then do the ordinary kicks
    for i in xrange(len(shift.__signals__)):
        sig = shift.__signals__[i]
        position = self.positions[sig]        
        geom.add(position,shift.__signal_shifts__[i],position)


#      # take the modulus of the position...
#      for i in xrange(len(position)):
#        position[i] = position[i]%latarr.spacing[i]
#    # next, do the signals and their corresponding arrays
#    # requires wrapping around...
#    for i in xrange(len(shift.__signals__)):
#      sig = shift.__signals__[i]
#      position = self.positions[sig]
#      geom.add(position,
#              shift.__signal_shifts__[i],position)
#      # take the divmod of the position
#      new_origin = []
#      for i in xrange(len(position)):
#        new_origin.append(-(position[i]/sig.spacing[i]))
#        position[i] = position[i]%sig.spacing[i]
#      # do the shifts
#      self.signals[sig][0] = na_move_origin(self.signals[sig][0],new_origin)

  def __do_rendered_read__(self,rd,args):
    """Do a rendered read to output signals"""

    # 1) Get the output arrays
#   arrays = args
#    if len(arrays)==0:
#      # allocate output arrays...
#      if rd.samearray and len(rd.signals)>0:
#        # must determine size...
#        # XXX should do type checking here.
#        rep = rd.signals[0]
#        array = _na.zeros(list(rep.shape)+[len(rd.signals)],_na.UInt8)
#        arrays = []
#        sl = [slice(None)]*rep.nd
#        for i in xrange(len(rd.signals)):
#          arrays.append(array[sl+[i]])
#      else:
#        
#    else:
#      # parse the array arguments
#      if rd.samearray:
#        array = arrays[0]
#        arrays = []
#        sl = [slice(None)]*rep.nd
#        for i in xrange(len(self.signals)):
#          arrays.append(array[sl+[i]])
#      else:
#        arrays = arrays[0]

    # 1) Allocate arrays for output from the rule
    out_arrays = map(lambda x: _na.zeros(x.shape,_na.UInt8),rd.signals)
    # convert 'arrays' to a dict
    out_dict = {}
    for i in xrange(len(rd.signals)): out_dict[rd.signals[i]]=out_arrays[i]
    
    # 2) Do the op (render the entire space)
    rd.rule.__doer__.do(out_dict)    

    # 3) Allocate output arrays if necessary
    if args==():
      if rd.samearray:
        out = _na.zeros(list(rd.region.shape)+[len(rd.signals)])
      else:
        shape = rd.region.shape
        out = map(lambda x: _na.zeros(shape),range(len(rd.signals)))
    else: out = args[0]
    out_slc = map(lambda x:slice(None),range(rd.region.lat_arr.nd))    

    # 4) fill the output arrays
    for i in xrange(len(rd.signals)):
      arr,out_arr = self.signals[rd.signals[i]]
      pos = self.positions[rd.signals[i]]
      slices = region_to_wrapped_slices(rd.region,pos)
      arr = out_arrays[i]
      if rd.samearray:
        for out_slc,wrap_slc in slices:
          # Note: wrap_slc[-len(arr.shape):] ensures that the slice
          # is not too large for the array
          out[out_slc+[i]]= arr[wrap_slc] 
      else:
        for out_slc,wrap_slc in slices:
          out[i][out_slc] = arr[wrap_slc]
    return out

    # 3) return the proper value
    # XXX should do slicing here...
    if rd.samearray:
      if len(rd.signals)==1: return arrays[0]
      else: return array      
    else: return arrays
    
    
    
  def __do_read_values__(self,rd,args):
    """Do an ordinary read to output signals"""
    # render output values if necessary
    if rd.rule!=None:
      self.__do_rule__(rd.rule)
    
    if args==():
      if rd.samearray:
        out = _na.zeros(list(rd.region.shape)+[len(rd.signals)])
      else:
        shape = rd.region.shape
        out = map(lambda x: _na.zeros(shape),range(len(rd.signals)))
    else: out = args[0]
    out_slc = map(lambda x:slice(None),range(rd.region.lat_arr.nd))    
    
    for i in xrange(len(rd.signals)):
      sig = rd.signals[i]      
      current,output = self.signals[sig]
      if isinstance(sig,OutSignal):
        read_array = output
      else:
        read_array = current
      pos = self.positions[sig]
      slices = region_to_wrapped_slices(rd.region,pos)
      if rd.samearray:
        for out_slc,wrap_slc in slices:
          out_slc = out_slc[-(len(out.shape)-1):] # trim the slice if necessary
          out[out_slc+[i]] = read_array[wrap_slc]
      else:
        for out_slc,wrap_slc in slices:
          _out = out[i]
          out_slc = out_slc[-len(_out.shape):] # trim the slice if necessary
          # sometimes its necessary to convert the slice to a tuple so that
          # numarray will handle it properly. 
          _out[tuple(out_slc)] = read_array[tuple(wrap_slc)]
    return out
