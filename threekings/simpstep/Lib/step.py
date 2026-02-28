# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.4 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/step.py,v $

""" Defines the STEP runtime interface
"""

import numarray as _na
import numarray.linear_algebra as _la
import math as _math
import inspect as _inspect
import weakref as _weakref
import types as _types
import copy as _copy

from latticearray import *  # for region definitions 

from simp import geom as _geom


class StepError(Exception):
  """Class representing a step error. """
  pass

# def __get_simp__(simp):
#   # If simp=None, go up through the namespaces in the call stack to 
#   # find the first global import of the simp module
#   if simp!=None: return simp
#   
#   for nest in xrange(1,len(_inspect.stack())):
#     caller_globals = _inspect.stack()[nest][0].f_globals
#     try:
#       simp = caller_globals["simp_module"]()
#       return simp
#     except KeyError:
#       try:
#         caller_locals = _inspect.stack()[nest][0].f_locals
#         simp = caller_locals["simp_module"]()
#         return simp
#       except KeyError: pass
#   raise NameError, """No simp module imported.
#         must either specify simp explicitly , or use 'from simp import *"""
#   return simp


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#                           SIGNAL TYPES
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
Int8 = _na.Int8
Int16 = _na.Int16
Int32 = _na.Int32

UInt8 = _na.UInt8
UInt16 = _na.UInt16
UInt32 = _na.UInt32

Float32 = _na.Float32

numarraytypes = [Int8,Int16,Int32,UInt8,UInt16,UInt32,Float32]

class SmallUInt:
  """SmallUInt(n) Small unsigned integer in the range 0 to n-1.
  """
  #    Public Attributes (Read-Only)
  #      n : number of states
  #      nbits : number of bits in this type
  #      mask  : binary mask for this type
  #      size : maximum binary size  
  
  def __init__(self,n):
      self.n = n
      if n>256:
        raise ValueError, """Size of a SmallUInt must be less than or equal to
        256, use UInt16 or UInt32 instead"""
      self.nbits = int(_math.ceil(_math.log(n)/_math.log(2)))
      self.nstates = 1<<self.nbits # real number of states 
      self.mask = self.nstates - 1

  # Biased integer functions
  def __repr__(self):
    return "SmallUInt%i" % (self.n)

  def __eq__(self,o):
    if not self.__class__==o.__class__: return 0
    return (self.n==o.n) and (self.n == o.n)

def numarraytypetostr(type):
  if isinstance(type,SmallUInt): return UInt8
  return {UInt8:"UInt8",UInt16:"UInt16",UInt32:"UInt32",
           Int8:"Int8", Int16:"Int16",  Int32:"Int32",
          Float32:"Float32"}[type]


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#                           SIGNALS
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
class Signal(LatticeArray):
  """A parallel data allocation in a STEP

   initialization parameters
      type --- the type of the signal (SmallUInt or UInt8)
      generator --- the generator matrix for the lattice
         defaults to the generator specified by SIMP.
      simp --- the simp module 
  """    
  # ps            : present state
  # _             : next state
  # lattice       : the lattice on which this signal has been allocated

  def __init__(self,type,generator=None,simp=None):
      self.__simp__ = simp
      self.__step__ = self.__simp__.__step__
      self.__id__ = id(self)
      # get the default generator from SIMP if it is not specified here.
      if generator==None: generator = self.__simp__.__generator__
      # check type
      self.type = type
      LatticeArray.__init__(self,generator,self.__simp__.__size__)
      self.__region__ = LatticeArrayRegion([slice(None)]*self.nd,self)
      self.__step__.Register(self)

  def value(self):
    """Return the entire array for the Signal as a numarray.

    When called from a Signal object, returns the entire
    array for the signal as a numarray. When called from a
    SignalRegion, returns the array for the signal at the
    slice.  The type of the array depends on the signal type.
    """
    return Read(self.__region__,self)()[0]

#  def __pos__(self): return self.array()
#  def __neg__(self): return -self.array()

  def __getitem__(self,index):
    # check for 1D index values
    if not isinstance(index,Region) and\
           not (isinstance(index,_types.TupleType) or \
                isinstance(index,_types.ListType)):
        index = (index,)
    return SignalRegion(self,index)

  def __setattr__(self,name,value): 
    """Used for actively setting ._ (does value checking)"""
    if (name=='_'):
      raise StepError, """Can only set the output attribute '_' within a Rule"""
    self.__dict__.update({name:value})
    return value

  def __repr__(self):
    return "<Signal id=%s type%s>" % (`self.__id__`,repr(self.type))
  
  def __str__(self):       return self.__repr__()

  def __setitem__(self,index,value):
    """Do slice assignment on the array"""
    if not isinstance(index,Region) and \
           not (isinstance(index,_types.TupleType) or \
                isinstance(index,_types.ListType)):
        index = (index,)    
    Write(index,[self],[value])()
    return value

  def neighbor_offset(self):
    """Returns the neighbor offset with respect to the signal"""    
#    return _na.zeros(self.nd)
    return [0]*self.nd

  def GetCoset(self):
    """Return the rectangular grid coset position (vector) of the lattice"""
    return GetCoset(self)()

  def SetCoset(self,position):
    """Set the rectangular grid coset position (vector) of the lattice"""
    return SetCoset(self,position)()

  def base_signal(self):
    """Return a reference to self.

    Only defined so that one can handle Signal and SignalRegion objects
    in a homogenous way.
    """
    return self
  
class SignalRegion:
  """ Represents a sliced signal.

  members (Read only)
    signal --- the base signal that the slice references
    region --- the LatticeArrayRegion that this slice refers to
  """
  def __init__(self,signal,subscr):
    self.signal = signal
    # decode the slice
    self.region = LatticeArrayRegion(subscr,signal)
    self.shape = _na.array(self.region.shape)

  def __repr__(self):
    return "<SignalRegion %s  %s" % (self.signal,self.region)
  
  def __str__(self): return self.__repr__()

  def value(self):
    """Return the data array associated with this signal slice.

     If the subscript references a single coordinate, it returns a scalar.
     (Wrapper for the STEP \class{Read} operation)
    """
    out = Read(self.region,[self.signal])()[0]
#    return out
    # might make sense to do this, but then the function shouldn't
    # be called 'array'
    # if out.size()==1: return out # return a scalar if possible
    if self.region.stop==None: return out.flat[0]
    return out

#  def int(self):
#    """Return the integer associated with the subscript.
#
#       The subscript must be a single coordinate, otherwise 
#       an array is needed to hold the values and a ValueError
#       is raised.
#    """
#    if self.region.stop!=None:
#      if not reduce(lambda x,y:x*y,list(self.shape),1) == 1:
#        raise ValueError, "Can only get an int from a region with a single site"
#    return Read(self.region,[self.signal])()[0]
    
  def __setattr__(self,name,value): 
    """Used for actively setting ._ (does value checking)"""
    if (name=='_'):
      return self.signal.__setitem__(self.region,value)
    else:
      self.__dict__.update({name:value})
    return value

  def neighbor_offset(self):
    """Returns the neighbor offset with respect to the signal"""
    if self.region.stop!=None:
      raise StepError, "Slice, %s is not a single neighbor" +`self`
    return list(self.region.start)

  def base_signal(self):
    """Returns the actual signal referenced"""
    return self.signal




class OutSignal(Signal):
  """
     A signal that is used as an output only.

     It is the same as an ordinary signal in all ways except that it is 
     output only.

     \class{OutSignal} objects are used in rendered \class{Read} operations.
  """
  
  def __setitem__(self,position,value):
    """Do slice assignment on the array"""
    raise StepError, "Can only set the output value of an Output Signal"

  def __getitem__(self,index):
    # check for 1D index values
    if not (isinstance(index,_types.TupleType) or \
                    isinstance(index,_types.ListType)):
        index = (index,)
    return SignalRegion(self,index)
#  def __getitem__(self,name):
#    raise StepError,"Must use a Read object read values from an OutSignal"
  def array(self):
    raise StepError,"Must use a Read object read values from an OutSignal" 
  def __setattr__(self,name,value): 
    """Used for actively setting ._ (does value checking)"""
    if (name=='_'):
      raise StepError, "Can only set the output value of an Output Signal"
    else:
      self.__dict__.update({name:value})
    return value

  def __repr__(self):
    return "<OutSignal id=%s type%s>" % (`self.__id__`,repr(self.type))

# ----------------------------------------------------------------
class Op:
    """Base class for the STEP primitive OPs"""
    # simp       : simp instance with respect to which the primitive is defined
    def __init__(self,simp):
      self.__simp__ = simp
      self.__step__ = self.__simp__.__step__
                                  
    def __call__(self,*vargs,**kwargs):
      return apply(self.__step__.Do,(self,)+vargs,kwargs)

      
# ----------------------------------------------------------------
class Sequence(Op):
    """Class for representing a sequence of STEP operations to be performed.
    
     The constructor expects a list STEP operation objects. Calling the
     Sequence will do them in order. 
   
     Creating \class{Sequence} objects notifies the STEP that the
     operations will be done one-after-another. The STEP, in turn, can
     sequence optimize the sequence.
   
     Because a sequence is itself an operation, sequences can be nested.
     """
    def __init__(self,list):
      self.ops = list
      # should validate the operations here somehow...
      
      if isinstance(self.ops[0],Op): simp = self.ops[0].__simp__
      else: simp = self.ops[0][0].__simp__
      Op.__init__(self,simp)      
      self.__validate_same_step__()
      self.__step__.Register(self)
      
    def __validate_same_step__(self):
      for op in self.ops:
         if isinstance(op,Op):
           if not id(op.__step__)==id(self.__step__):
             raise StepError, \
               "Operation %s does not belong to the same Step instance" % i
         else:
           for parallel_op in op:
             if not isinstance(parallel_op,Op):
               raise StepError, "A sequence can only contain operations"
             if not id(parallel_op.step)==id(self.__step__):
               raise StepError, \
                 "Operation %s does not belong to the same Step instance" % i

#import simp.rule_compiler_tools as _rct
import simp.rule_analysis as _ra

def __get_output_cosets__(rule,outputs):
   """Ensure that the outputs are unique cosets"""
   # Construct a dictionary keyed on output signals that contains
   # a dictionaries of the rectangular unit cell coset representatives
   # of each signal. Raise an error if it is not unique.

   # For each signal, the output signal cosets dictionary contains 
   #   0 : a dictionary mapping coset representatives to the neighbor
   #       signal representing it.
   #   1 : The cosets that aren't contained as outputs
   #   2 : The unit cell bounds
   output_signal_cosets = {}
   for i in xrange(len(outputs)):
     out = outputs[i]
     sig = out.base_signal()     
     offset = out.neighbor_offset()
    
     # The following does ot work....does not take skew into account
     #coset = tuple([(offset[j]%(rule.spacing[j]/sig.spacing[j]))
     #               for j in xrange(len(offset))])

     coset = tuple(rule.__coset_coordinate__(offset))

     # TODO :  Make sure that we are actually doing an intelligent thing here.
     # In particular, that we would like to represent the "coset" of a 
     # sublattice using its n-dimensional floor rather than taking the array 
     # index or the like...
     #     coset = tuple(sig.__array_index__(coset))

     coset = tuple([(coset[j]/sig.spacing[j])*sig.spacing[j]
                for j in xrange(len(coset))])

     if output_signal_cosets.has_key(sig):
       coset_dict = output_signal_cosets[sig]
       if coset_dict.has_key(coset):
         raise StepError, "Write conflict, same coset assigned twice:"+ \
             "\n\tsignal offset %s and %s both refer to coset %s" % \
               (coset_dict[coset].neighbor_offset(),
                 out.neighbor_offset(),coset)
       coset_dict[coset]=out
     else:
       output_signal_cosets[sig] = {coset:out}

   # for each output signal, construct a dictionary of the cosets that
   # aren't present.
   for sig,coset_dict in output_signal_cosets.items():
     no_rep_dict = {} # dictionary of cosets that aren't represented
     indx = [0]*rule.nd
     # construct the coset size
     bounds = [rule.spacing[i]/sig.spacing[i] for i in xrange(rule.nd)]
     while 1:
         if not coset_dict.has_key(tuple(indx)):
           no_rep_dict[tuple(indx)]=None
         _geom.multidimensional_inc(indx,bounds)
         if _geom.is_zero(indx): break
     output_signal_cosets[sig] = [coset_dict,no_rep_dict,bounds]
   return output_signal_cosets


class Rule(Op,LatticeArray):
    """A STEP operation that performs parallel, local updates.

    constructor parameters
       rule_function --- the local transition function of the rule
       namespace --- a dictionary of names that overrides the global namespace
       generator --- generator for the Rule's lattice

    """
    def __init__(self,rule_function,generator=None,namespace={}):
      # Analyze the input rule function
      self.namespace = namespace
      self.rule_function = rule_function
      self.name = rule_function.__name__
      
      if not isinstance(rule_function,_types.FunctionType):
        raise ValueError, \
         "rule transition function %s must be a Python function" % rule_function
      self.__strobed__ = _ra.RuleStrober(self.rule_function,
                            [self.namespace,self.rule_function.func_globals])
      # inputs in a canonical ordering
      self.inputs = self.__strobed__.inputs()
      # outputs in a canonical ordering
      self.outputs = self.__strobed__.outputs()
      
      if len(self.outputs)==0:
        raise ValueError,"Function %s has no signal outputs." %\
                  (rule_function.__name__)

      # initialize the SIMP instance
      simp=self.outputs[0].base_signal().__simp__
      Op.__init__(self,simp)
      if generator==None: generator=self.__simp__.__generator__
      LatticeArray.__init__(self,generator,self.__simp__.__size__)      

      # ensure rule is a sublattice of the inputs and outputs
      for sig in self.outputs+self.inputs:
        if not _geom.issublattice(self.generator,sig.base_signal().generator):
          raise StepError,\
            "The rule must be a sublattice of its input and output signals."
        

      self.__output_cosets__ = __get_output_cosets__(self,self.outputs)
#      print "***********Output signal cosets",self.__output_cosets__
      self.__strobed__.hash_string()
      self.__step__.Register(self)

    def GetCoset(self):
      return GetCoset(self)()
    def SetCoset(self,position):
      return SetCoset(self,position)()

    def __repr__(self):
        return "<Rule name=%s>" % self.name


class LutRule(Op,LatticeArray):
    """A STEP Rule with a transition function specified by a lookup-table.
    
    keyword parameters 
      lut --- numarray holding the lookup table
      inputs --- signal inputs (in order)
      outputs --- signals outputs (in orders)
    """
    def __init__(self,lut,inputs,outputs,
                 generator=None,simp=None,name="unnamed"):
      self.lut = lut
      self.inputs = inputs
      self.outputs = outputs
      self.name = name
      simp = self.outputs[0].base_signal().__simp__
      Op.__init__(self,simp)       
      LatticeArray.__init__(self,generator,self.__simp__.__size__)
      self.__check_lut__()
      self.__output_cosets__ = __get_output_cosets__(self,self.outputs)
      self.__step__.Register(self)
      
    def __check_lut__(self):
      if not (isinstance(self.lut,_na.NumArray) and
             isinstance(self.lut.type(),_na.IntegralType)):
        raise ValueError, "LUT must be an Integral type numarray"
      
      for out in self.outputs:
        if not (isinstance(out.type,SmallUInt) or (out.type in numarraytypes)):
           raise ValueError, "Unsupported LUT output type", out.type
      # verify the number of LUT outputs
      if not len(self.lut.shape)==len(self.inputs)+1:
        raise ValueError, \
           "Invalid number of dimensions in lut array, expected " +\
                  `len(self.inputs)+1`
      if not self.lut.shape[-1]==len(self.outputs):
        raise ValueError, "The LUT array does not match the number of outputs"
      
      for i in xrange(len(self.inputs)):
        in_ = self.inputs[i]
        if (isinstance(out.type,SmallUInt)):
            if self.lut.shape[i]<out.type.n:
               raise ValueError, "LUT is too small in the %ith dimension" % i
        elif out.type==_na.UInt8:
            if self.lut.shape[i]<256:
               raise ValueError, "LUT is too small in the %ith dimension" % i
        else:
           raise ValueError, "Unsupported LUT input type", out.type

    def GetCoset(self):  return GetCoset(self)()
    def SetCoset(self,position): return SetCoset(self,position)()
        


class Shift(Op):
  """STEP operation that shifts the position of \class{LatticeArray} objects.
  
  constructor parameters
    shifts --- dictionary keyed on LatticeArray objects giving the
               shift vectors to be applied to each
  """
  def __init__(self,shifts):
    keys = shifts.keys()
    simp = keys[0].__simp__
    Op.__init__(self,simp)
    self.shifts = {}
    for ob in keys:
      if not isinstance(ob,LatticeArray):
         raise ValueError, "can't shift",`ob`
      if not id(self.__step__)==id(ob.__step__):
         raise ValueError, "%s does not come from the same STEP" % `ob`
      self.shifts[ob] = _geom.asintarray(shifts[ob])
      # _geom.scale_coord(shifts[ob],ob.coord_pitch,ob.snapto)
    self.__step__.Register(self)

class Shuffle(Op):
  """STEP operation that randomly shuffles LatticeArray object positions.
  
  constructor parameters
    objects - list LatticeArray objects to be Shufflered.
  """
  def __init__(self,objects):
    if len(objects)==1 and \
       (isinstance(objects[0],_types.ListType) or \
        isinstance(objects[0],_types.TupleType)):
         objects = objects[0]

    self.Shuffle = tuple(objects)  # in case it was a list...
    
    simp = objects[0].__simp__
    Op.__init__(self,simp)    
    for ob in objects:
      if not isinstance(ob,LatticeArray):      
        raise ValueError, "can't Shuffle",`ob`
      if not id(self.__step__)==id(ob.__step__):
        raise StepError, "%s does not come from the same STEP instance" % ob
    self.__step__.Register(self)

class RWOp(Op):
  """
  Public Attributes (read only)
    signals : signals to be read or written
    region: LatticeArrayRegion to be operated upon
  """
  def __init__(self,region,signals):
    # convert signals to a list if necessary
    
    if not (isinstance(signals,_types.ListType) or \
           isinstance(signals,_types.TupleType)):
      signals = [signals]
    self.signals = tuple(signals)

    # representative signal
    rep = self.signals[0]    

    Op.__init__(self,rep.__simp__)
    self.region = LatticeArrayRegion(region,rep)
    if len(self.signals)==1:
      if not (isinstance(rep,Signal) or \
              isinstance(rep,OutSignal)):
        raise ValueError, "%s is not a Signal" % rep
      return
    generator = rep.generator;
    
    for sig in self.signals:
      if not (isinstance(sig,Signal) or isinstance(sig,OutSignal)):
        raise ValueError, "%s is not a Signal" % self.signals[0]
      if not id(self.__step__)==id(sig.__step__):
        raise ValueError, "%s does not come from the same STEP" % `sig`
      if not _na.alltrue((rep.generator==generator).flat):
        raise ValueError, \
            "%s is not on the same lattice as the other signals" % sig

def __shapes_eq_1__(x,y):
    """Works when y is longer than x"""
    if x==y[-len(x):]:
      return reduce(lambda x,y: x and y, map(lambda x: x==1,y[0:len(y)-len(x)]))
    else: return 0


def __shapes_eq__(x,y):
  """Return true if shapes are equal modulo higher dimensions of either shape
  that has a value of 1"""
  x = tuple(x); y=tuple(y)
  len_x = len(x); len_y = len(y)
  
  if len_x==len_y: return x==y
  elif len_x<len_y: return __shapes_eq_1__(x,y)
  else: return __shapes_eq_1__(y,x)
   
      
class Read(RWOp):
  """STEP operation foor reading Signal and OutSignal data.

  constructor parameters
    region --- data region to read out
    signals --- list of signals to read
    rule --- rendering rule for reading OutSignal objects (unspecified
             by default)
    samearray --- indicates whether read results are returned ass a list of
             arrayys, or as a single array with the least significant index
             indexing the output signal it came from.

  Public Attributes (read only)
    rule --- rule for a rendered read (None for a regular read op)
    samearray --- flag indicating whether the outputs should all be
          read to the same array
  """
  def __init__(self,region,signals,rule=None,samearray=0):
    RWOp.__init__(self,region,signals)
    self.rule = rule
    if self.rule!=None:
      for sig in self.signals:
        if not isinstance(sig,OutSignal):
          raise StepError, "%s is not a signal." % sig
#    rule_outsigs=filter(lambda x: isinstance(x,OutSignal),self.rule.outputs)
#    for out in self.signals:
#      if not (out in self.rule.outputs):
#        raise StepError, \
#           "Read Signal %s is not given as an OutSignal of the Rule." % out
    self.samearray = samearray
    if rule!=None and (id(rule.__step__)!=id(self.__step__)):
      raise StepError, "Rule does not match the current step"

    self.__step__.Register(self)

  def __call__(self,arrays=None):
    # check the values and then call the function
    if arrays!=None:
      if self.samearray:
        # should do more advanced shape checking here...
        if not isinstance(arrays,_na.NumArray):
          raise ValueError,\
           "When read is declared with 'samearray', a single array is expected"
        expected_shape = tuple(list(self.region.shape)+[len(self.signals)])
        #tuple(rep.shape
        if not arrays.shape==expected_shape:
          raise ValueError, "Invalid output array shape %s, expected %s" \
                % (arrays.shape,expected_shape)
      else:
        if isinstance(arrays,_na.NumArray): arrays = [arrays]
        if not len(arrays)==len(self.signals):
          raise ValueError, "There are %s outputs, expected same number of output arrays" % len(self.signals)

        region_shape = self.region.shape

        for  i in xrange(len(arrays)):
          arr = arrays[i]
          arr_shape = arr.shape
          nd = len(self.region.shape)
          # check that the lower dimensions are consistent with the region's
          # shape and that all upper dimensions are 1.
          if not __shapes_eq__(arr_shape,region_shape):
              raise ValueError, \
                "Invalid shape %s for input array %i, expected it to be %s"\
                   % (`arr.shape`,i,`tuple(self.region.shape)`)
      return self.__step__.Do(self,arrays)
    
    return self.__step__.Do(self)


class GetCoset(Op):
  """STEP operation for getting the coset position of a LatticeArray.

  When called, returns the coset pposition.
  
  constructor parameters
     ob --- LatticeArray object (Rule, Signal, or OutSignal)
  """
  def __init__(self,ob):
    self.object = ob
    if not isinstance(ob,LatticeArray): 
        raise ValueError, `ob`+" is not a LatticeArray object"
    simp = ob.__simp__
    Op.__init__(self,simp)
    self.__step__.Register(self)

class SetCoset(Op):
  """STEP operation for setting the coset positions of a LatticeArray objects.
  constructor parameters
     positions --- dictionary keyed on LatticeArray objects mapping them
                   to their new coset position.  The position should be a
                   vector or another LatticeArray object. 
  """
  def __init__(self,positions):
    self.positions = positions
    # check all of the new positions...
    for latarr in self.positions.keys():
        position = self.positions[latarr]
        if not isinstance(latarr,LatticeArray):
          raise ValueError, `latarr`+" has no lattice position"
        if isinstance(position,LatticeArray):
          self.position = position
        elif not len(position)==latarr.nd:
          raise ValueError, "Wrong number of dimensions in the position"
          position = [position[i]%latarr.spacing[i]
                           for i in xrange (len(position))]
        self.positions[latarr] = position
    Op.__init__(self,latarr.__simp__)
    self.__step__.Register(self)

class Write(RWOp):
  """STEP operation for writing signal values.

    constructor parameters
      region --- the region to write to
      signals --- list signals to write
      values --- list of values (one for each signal) to write
                 If specified, the write is static, otherwise it is
                 dynamic and the values must be specified when called.

  """
  def __init__(self,region,signals,values=None):
    RWOp.__init__(self,region,signals)     
    self.values = values
    if values!=None:
      self.__check_values__(values)
    # should check the values
    self.__step__.Register(self)      

  def __call__(self,values=None):
    if values==None:
      if self.values==None:
        raise StepError, "A dynamic Write expects array arguments"
      self.__step__.Do(self)  
    else:
      if self.values!=None:
        raise StepError, "A static Write does not expect arguments"
      self.__step__.Do(self,values)
      
  def __check_values__(self,values):
    """Check the read or write values to ensure that they are appropriate"""
    # XXX Should check that the array shape is correct 
    if len(values)!=len(self.signals):
        raise ValueError, "Length of signals and values don't match"

#----------------------------------------------------------------
#        The STEP runtime
#---------------------------------------------------------------- 
# Base class for STEP runtime implementations

class Step:

    def __init__(self,size,verbose=1,*kwargs):
      self.size = size
      raise NotImplementedError("Subclass must override")      

    def Do(self,operation):
      """Do (or enqueue) a step operation"""
      raise NotImplementedError("Subclass must override")

    def Register(self,ob):
      """Register an operation or signal or operation with the step"""
      raise NotImplementedError("Subclass must override")
    
    def Flush(self):
      """Flush all pending operations"""
      raise NotImplementedError("Subclass must override")

    def SeedRandom(self,seed):
      """Seed the random number generator"""
      raise NotImplementedError("Subclass must override")

    def ClearCache(self):
      """If the STEP caches values, clear the cache."""
      raise NotImplementedError("Subclass must override")    

