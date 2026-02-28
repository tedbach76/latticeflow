# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.2 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/stepmodules/Reference.py,v $

"""
The reference STEP module implementation.

Pure Python implementation that aims to be clean, simple
and correct, but not efficient.

Does all operations immediately.

Rather than building LUTs to implement a rule, it implements rules
directly using the function.  Code analysis still must be performed to
determine the inputs and outputs of the function. 
"""



import time, weakref

import numarray as _na
import numarray.linear_algebra as _la
import simp.step as step
from simp.step import *
#from simp.stephelpers import *
import simp.geom as geom
import simp.import_locally as import_locally

import copy

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
                wrap_slc[i] = slice(start_,stop_)
        else: # wraps around a boundary
            arr_slc0_ = slice(0,shape_-start_)
            arr_slc1_ = slice(shape_-start_,stop_-start_)
            wrap_slc0_ = slice(start_,shape_)
            wrap_slc1_ = slice(0,stop_-shape_)
            # Duplicate each slice region in this dimension...
            for j in xrange(len(subscripts)):
                arr_slc0,wrap_slc0 = subscripts[j]
                arr_slc1=copy.copy(arr_slc0);wrap_slc1=copy.copy(wrap_slc0)
                arr_slc0[i] = arr_slc0_; arr_slc1[i] = arr_slc1_
                wrap_slc0[i] = wrap_slc0_; wrap_slc1[i] = wrap_slc1_
                
                subscripts.append([arr_slc1,wrap_slc1])
    return subscripts
  
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#            OP WRAPPERS
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=      

# How a scan is implemented
#  * determine input and output signals, get neighbor offsets and add them
#    to the signal positions to get the scan offset. 
#  * ensure that outputs do not overlap
#  * determine whether the outputs cover that signal
#  * get new arrays for outputs signals (copy of the current array value)
# 
#  for each row:
#    * compute the start index for each element
#    * obtain 1D slices for each row
#    for each element in the row
#       * increment the index1d pointers, wrapping modulo the size of each
#         array
#       * construct the input vector from the current array values
#       * apply the function
#       * copy the output vector into the outputs.


class RuleDoer:
  # The rule doer defines three special cases
  #   orthonormal : the rule lattice and the signal lattices are orthogonal
  #                 (ordinary CA)
  #   orthogonal : the rule lattice and the signal lattices are orthogonal
  #   skew : the rule lattice and the signal lattices are skewed
  def __init__(self,rule,step):
    self.step = step
    self.rule = rule
    self.mode = "UNKNOWN"

    if geom.isorthonormal(self.rule.generator): self.mode = "ORTHONORMAL"

    self.strobed = rule.__strobed__
    # construct other helper data structures
    self.inputs = rule.inputs
    self.outputs = rule.outputs

    if self.mode=="ORTHONORMAL":
        # prevent output collisions
        out_dict = {}
        for sig in self.outputs:
          if not out_dict.has_key(sig):
            out_dict[sig] = 0
          else:
            raise StepError, "Duplicate output on signal", `sig`
    else:
      # check that the rule's lattice is a sublattice of the lattice of all
      # of the inputs and outputs.
      rule_gen = rule.generator
      for sig in [sig.base_signal() for sig in self.inputs+self.outputs]:
        if not geom.issublattice(rule_gen,sig.generator):
          raise StepError, "The rule is not on a sublattice of "+`sig`

    self.input_offsets = map(_na.zeros,[rule.nd]*len(self.inputs))
    self.output_offsets = map(_na.zeros,[rule.nd]*len(self.outputs))

  def compute_offsets(self):
    """Get the (coordinate) offset vectors for the inputs as a function of the
    current offset of the rule, the position of the signals, and the neighbor
    access of each signal.
    """
    # For efficiency, we do all operations on the offsets inplace.
    rule_position = self.step.positions[self.rule]
    # first do the input offsets    
    for i in xrange(len(self.inputs)):
      sig = self.inputs[i]
      ofst = self.input_offsets[i]
      realsig = sig.base_signal()      
      _na.subtract(rule_position,self.step.positions[realsig],ofst)
      # add neighbor offsets if necessary
      if isinstance(sig,SignalRegion):
        _na.add(ofst,sig.neighbor_offset(),ofst)
      for j in xrange(len(ofst)): ofst[j] = ofst[j]%realsig.size[j]

    # then the output offsets
    for i in xrange(len(self.outputs)):
      sig = self.outputs[i]
      ofst = self.output_offsets[i]
      # Only subtract out the position modulo the spacing.  This
      # effectively shifts the position to itself modulo the spacing.
      realsig = sig.base_signal()
      position = self.step.positions[realsig]
      for j in xrange(len(ofst)):
#        ofst[j] =  rule_position[j] - (position[j]%realsig.spacing[j])
          ofst[j] =  rule_position[j] - position[j]
      # add neighbor offset if necessary
      if isinstance(sig,SignalRegion):
        _na.add(ofst,sig.neighbor_offset(),ofst)
      for j in xrange(len(ofst)): ofst[j] = ofst[j]%realsig.size[j]
      
#  def adjust_output_positions(self):
#    """Adjust the positions of the output signals to account for the
#    rearrangement."""
#    for sig in self.outputs:
#      realsig = sig.base_signal()
#      position = self.step.positions[realsig]
#      for i in xrange(len(position)):
#        position[i] = (position[i]%realsig.spacing[i])
        
    

  def get_output_arrays(self,output_sigs):
    """Get a set of new arrays for the output values"""
    # Use a dictionary to ensure the uniqueness of output array allocations
    # since a signal may be represented more than once (but at different
    #  offsets). Only allocate a single array for all copies of the output
    # signal

    # Also, handle the OutSignal objects in a special way---take the
    # output array from the 'output_arrays' dictionary.
    output_dict = {}

    for out in output_sigs:
      if not output_dict.has_key(out):
        try:
          output_dict[out] = self.output_arrays[out]
        except KeyError:
          if isinstance(out,OutSignal):
            raise StepError,"Outputs must be specified for all OutSignals"
          # copy the current signal
          output_dict[out] = _na.array(self.step.signals[out][0])
    # return a list of output signals in the same order.
    return [output_dict[sig] for sig in output_sigs]
            
  def do(self,arrays = {}):
    self.output_arrays = arrays
#    if self.mode=="ORTHONORMAL":
#      self.__do_orthonormal__() # not working
#    else:
    self.__do__()
    

  def __do__(self):

    loop_bounds = self.rule.shape
    row_sz = loop_bounds[-1]
    nd = self.rule.nd
    loop_index = _na.zeros(nd)
    coord = _na.zeros(nd)    
    # We add sz before taking the modulus so that all offsets are positive.
    self.compute_offsets()
    in_ofsts = self.input_offsets; out_ofsts = self.output_offsets

    # Output lattice parameters 
    output_sigs = [sig.base_signal() for sig in self.outputs]
    out_arrs = self.get_output_arrays(output_sigs)
    out_rows = [None]*len(out_arrs)
    out_row_indx = [None]*len(out_arrs)
    out_row_shapes = [sig.shape[-1] for sig in output_sigs]
    out_row_strides = [self.rule.spacing[-1]/sig.spacing[-1]
                       for sig in output_sigs]

    # Input lattice parameters     
    input_sigs = [sig.base_signal() for sig in self.inputs]
    in_arrs = map(lambda sig:self.step.signals[sig][0],input_sigs)
    in_rows = [None]*len(in_arrs)
    in_row_indx = [None]*len(in_arrs)
    in_row_shapes = [sig.shape[-1] for sig in input_sigs]    
    in_row_strides = [self.rule.spacing[-1]/sig.spacing[-1]
                       for sig in input_sigs]

    input_dict = {}
    for sig in input_sigs: input_dict[sig] = 1

    call_rule = self.rule.__strobed__
    output_vect = [None]*len(self.outputs)
    input_vect = [None]*len(self.inputs)    

    while 1:
        # Compute the coordinate for the start of the row
        scan_coord = self.rule.__coordinate__(loop_index)
        # Get the rows and row offsets
        for i in xrange(len(self.inputs)):
            _na.add(in_ofsts[i],scan_coord,coord)
            indx = input_sigs[i].__array_index__(coord)
            for j in xrange(len(indx)): indx[j]=indx[j]%input_sigs[i].shape[j]
            in_rows[i] = in_arrs[i][row_slice(indx)]
            in_row_indx[i]=indx[-1]

        for i in xrange(len(self.outputs)):
            _na.add(out_ofsts[i],scan_coord,coord)
            indx = output_sigs[i].__array_index__(coord)
            for j in xrange(len(indx)): indx[j]=indx[j]%output_sigs[i].shape[j]
            out_rows[i] = out_arrs[i][row_slice(indx)]
            out_row_indx[i]=indx[-1]
#        print "======================="
#        print scan_coord
#        print in_row_indx
#        print out_row_indx        

        # Update the elements within a row
        for i in xrange(row_sz): # 

          # gather inputs
          for j in xrange(len(self.inputs)):
            input_vect[j]= in_rows[j][
               (in_row_indx[j]+i*in_row_strides[j])%in_row_shapes[j]]

#          out = call_rule(input_vect,output_vect)
          out = call_rule(input_vect)

          # write the outputs
          for j in xrange(len(self.outputs)):
            out_val =  out[j]
            elt = (out_row_indx[j]+i*out_row_strides[j])%out_row_shapes[j]
            out_rows[j][elt] = out_val
          
#          # write the outputs
#          for j in xrange(len(self.outputs)):
#            out_val =  out[j]
#            elt = (out_row_indx[j]+i*out_row_strides[j])%out_row_shapes[j]
#
#            if out_val==None: # lookup default value for the outputs
#              if not input_dict.has_key(output_sigs[j]):
#                 out_rows[j][elt] = 0 # default val
#              # otherwise, use current value as the default.
#            else:
#              out_rows[j][elt] = out_val

        # increment the index values, return if necessary        
        geom.multidimensional_inc(loop_index,loop_bounds,1,-2)
        if _na.alltrue(loop_index==0):
          break
        
    # replace current array values with the values of the outputs
    for i in xrange(len(output_sigs)):
        sig = output_sigs[i]
        self.step.signals[sig][0]=out_arrs[i]
    
  def __do_orthonormal__(self):
    # Do a scan on the arrays.
    # 
    # Variables  
    #   offsets : neighbor offset index values
    #   sigs : signals
    #   arrs : arrays allocated to the signals
    #   rows : current row being scaned
    #   row_indxs : the row index values
    #   row_sz : size of a row

    # Get static values for neighbor offsets
    sz = self.rule.size

    # Compute the current offsets (accounts for shifting...)
    self.compute_offsets()
    input_ofsts = self.input_offsets; output_ofsts = self.output_offsets

    loop_bounds = self.rule.size
    nd = self.rule.nd
    indx = _na.zeros(nd)

    output_sigs = [sig.base_signal() for sig in self.outputs]
    out_arrs = self.get_output_arrays(output_sigs)
    out_rows = [None]*len(out_arrs)
    input_sigs = [sig.base_signal() for sig in self.inputs]
    in_arrs = map(lambda sig:self.step.signals[sig][0],input_sigs)
    row_sz = loop_bounds[-1]
    input_dict = {}
    for sig in input_sigs: input_dict[sig] = 1

    in_row_ofsts = [x[-1] for x in input_ofsts]
    out_row_ofsts = [x[-1] for x in output_ofsts]
    call_rule = self.rule.__strobed__
    output_vect = [None]*len(self.outputs)

    while 1:
#        print "======",len(in_arrs),input_ofsts
#        print in_arrs[0][:]
#        print in_arrs
#        print in_arrs[1][:]        
#        print input_ofsts[0]
#        print input_ofsts[1]        
        # get the rows and the 1d index values
        in_rows = [in_arrs[i][row_slice(input_ofsts[i])] \
                              for i in xrange(len(in_arrs))]
  
        out_rows = [out_arrs[i][row_slice(output_ofsts[i])] \
                              for i in xrange(len(out_arrs))]
  
        for i in xrange(row_sz): # update elements
          # gather inputs
          input_vect= [in_rows[x][(i+in_row_ofsts[x])%row_sz]
                          for x in xrange(len(in_row_ofsts))]
  
          out = call_rule(input_vect)
#          for x in xrange(len(out)):
#            out_val =  out[x]
#            if out_val==None:
#              # get default value for the outputs
#              if not input_dict.has_key(output_sigs[x]):
#                 out_rows[x][(i+out_row_ofsts[x])%row_sz] = 0 # default val
#              # otherwise, use current value as the default.
#            else:
#              out_rows[x][(i+out_row_ofsts[x])%row_sz] = out_val
        # write the outputs
        for x in xrange(len(out)):
          out_val =  out[x]
          out_rows[x][(i+out_row_ofsts[x])%row_sz] = out_val
          
        for x in xrange(len(self.inputs)):
          geom.multidimensional_inc(input_ofsts[x],loop_bounds,1,-2)
  
        for x in xrange(len(output_ofsts)):
          geom.multidimensional_inc(output_ofsts[x],loop_bounds,1,-2)
  
        # increment the index values, return if necessary
        geom.multidimensional_inc(indx,loop_bounds,1,-2)
        if _na.alltrue(indx==0):
          break
        
    # replace current array values with the values of the outputs
    # XXX should check for uniqueness of output signals

    for i in xrange(len(output_sigs)):
        sig = output_sigs[i]
        self.step.signals[sig][0]=out_arrs[i]
#    self.adjust_output_positions()

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
    self.signals = {}
    self.output_signals = {}
    self.positions = {}
    # private copy of the random module
    self.random = import_locally.import_copy("random")
    self.SeedRandom(time.time())
    
  def Do(self,op,*vargs,**kwargs):
    """Do (or enqueue) a step operation"""
    if isinstance(op,Rule):
      op.__doer__.do()
    elif isinstance(op,Sequence):
        # XXX add handlers for parallel ops       
        for op in op.ops: self.Do(op)
    elif isinstance(op,Read):
      if op.rule==None:
        return self.__do_read_values__(op,vargs)
      else:
        return self.__do_rendered_read__(op,vargs)
    elif isinstance(op,Write): self.__do_write__(op,vargs)
    elif isinstance(op,Shift): self.__do_shift__(op)
    elif isinstance(op,Shuffle): self.__do_Shuffle__(op)
    elif isinstance(op,GetCoset):
      return _na.array(self.positions[op.object])
    elif isinstance(op,SetCoset):
      for latarr in op.positions.keys():
        pos = op.positions[latarr]
        if isinstance(pos,LatticeArray):
            pos = copy.copy(self.positions[op.position])
        else:
            pos = copy.copy(op.position)          
        # set the coset position (only)
        curpos = self.positions[latarr]
        for i in xrange(len(pos)):
          spacing_ = latarr.spacing[i] 
          pos[i]=(pos[i]%spacing_)+(curpos[i]/spacing_)*spacing_
        self.positions[latarr]=pos
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
    elif isinstance(ob,Read):
      if ob.rule!=None:
        self.__register_rend_read__(ob)
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
    pass
  
  # -------------------------------- PRIVATE IMPLEMENTATION METHODS
  def __register_rend_read__(self,rd):
    rule_outs = rd.rule.__doer__.outputs
    rule_outs = [sig.base_signal() for sig in rule_outs]    
    rule_outs = filter(lambda x: isinstance(x,OutSignal),rule_outs)

#   not really needed
#    for out in rd.signals:
#      if not (out in rule_outs):
#        raise StepError, \
#           "Read Signal %s is not given as an OutSignal of the Rule." % out


  def __alloc_signal__(self,sig):
    type = sig.type
    if not isinstance(sig,OutSignal) and not isinstance(type,step.SmallUInt):
      raise StepError, \
         "The reference STEP currently only handles SmallUInt signals"
#    lat_ = _la.inverse(sig.generator)
#    sig_sz = geom.asintarray(_na.matrixmultiply(s.size,lat_))
    if isinstance(sig,OutSignal):
      self.signals[sig] = [None, # array
                           geom.isorthonormal(sig.generator)]
    else:
      self.signals[sig] = [_na.zeros(sig.shape,_na.UInt8), # array
                           geom.isorthonormal(sig.generator)]
    self.positions[sig] = _na.zeros(self.nd)    
      

  
  def __alloc_rule__(self,rule):
    """Create the position storage for a rule."""
    rule.__doer__ = RuleDoer(rule,self)
    self.positions[rule] = _na.zeros(self.nd)
    
  def __do_write__(self,wr,values):
    if wr.values!=None: values = wr.values
    else: values = values[0] # decode the kwargs

    # XXX Need to add handlers for writes that go over the boundary
    for i in xrange(len(wr.signals)):
      arr,mode = self.signals[wr.signals[i]]
      pos = self.positions[wr.signals[i]]
      slices = region_to_wrapped_slices(wr.region,pos)      
      for in_slc,wrap_slc in slices:
        val = values[i]
        if isinstance(val,_na.NumArray):
          arr[wrap_slc] = val[in_slc]  
        else:
          arr[wrap_slc] = val

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

  def __do_Shuffle__(self,Shuffle):
    for ob in Shuffle.Shuffle:
      position = self.positions[ob]      
      if (isinstance(ob,OutSignal) or isinstance(ob,Rule)):
          # just randomize the coset position
          for i in xrange(len(ob.spacing)):
            position[i] = self.random.randrange(ob.spacing[i])
      elif (isinstance(ob,Signal)):
          # randomize coset position then do a random shift 
          for i in xrange(len(ob.spacing)):          
            position[i] = self.random.randrange(ob.spacing[i])
          new_origin = []
          for i in xrange(len(ob.shape)):
            new_origin.append(self.random.randrange(ob.spacing[i]))
          self.signals[ob][0] = \
               na_move_origin(self.signals[ob][0],new_origin)          

  def __do_shift__(self,shift):
    # first do the latarr objects
    for i in xrange(len(shift.__latarrs__)):
      latarr = shift.__latarrs__[i]
      position = self.positions[latarr]
      _na.add(position,
              shift.__latarr_shifts__[i],position)
      # take the modulus of the position...
      self.positions[latarr] = _na.array(latarr.__coset_coordinate__(position))
      
#      for i in xrange(len(position)):
#        position[i] = position[i]%latarr.spacing[i]
    # next, do the signals and their corresponding arrays
    # requires wrapping around...
    for i in xrange(len(shift.__signals__)):
      sig = shift.__signals__[i]
      position = self.positions[sig]
      _na.add(position,
              shift.__signal_shifts__[i],position)
      # take the divmod of the position
      new_origin = []
      for i in xrange(len(position)):
        new_origin.append(-(position[i]/sig.spacing[i]))
        position[i] = position[i]%sig.spacing[i]
      # do the shifts
      self.signals[sig][0] = na_move_origin(self.signals[sig][0],new_origin)

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
      arr,mode = self.signals[rd.signals[i]]
      pos = self.positions[rd.signals[i]]
      slices = region_to_wrapped_slices(rd.region,pos)
      arr = out_arrays[i]
      if rd.samearray:
        for out_slc,wrap_slc in slices:
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
    if args==():
      if rd.samearray:
        out = _na.zeros(list(rd.region.shape+[len(rd.signals)]))
      else:
        shape = rd.region.shape
        out = map(lambda x: _na.zeros(shape),range(len(rd.signals)))
    else: out = args[0]
    out_slc = map(lambda x:slice(None),range(rd.region.lat_arr.nd))    
    
    for i in xrange(len(rd.signals)):
      arr,mode = self.signals[rd.signals[i]]
      pos = self.positions[rd.signals[i]]
      slices = region_to_wrapped_slices(rd.region,pos)
      if rd.samearray:
        for out_slc,wrap_slc in slices:
          out[out_slc+[i]] = arr[wrap_slc]
      else:
        for out_slc,wrap_slc in slices:
          out[i][out_slc] = arr[wrap_slc]
    return out
