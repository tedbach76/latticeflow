# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.1.1.1 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/stepmodules/Pc/lut.py,v $

"""
LUT compilation routines.

May be of general use. 
"""

from simp import cache
from simp.step import *
from simp import geom as _geom
import numarray as _na


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#            LUT COMPILATION
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def binary_info(signal):
    """Returns a list giving [nbits,mask,~mask] for a signal"""
    type = signal.base_signal().type
    if isinstance(type,SmallUInt):
        return [type.nbits,type.mask,~type.mask]
    elif type==_na.UInt8:  return [8,0xff,~0xff]
    elif type==_na.Int8:   return [8,0xff,~0xff]
    elif type==_na.UInt16:  return [16,0xffff,~0xffff]
    elif type==_na.Int16:  return [16,0xffff,~0xffff]    
    elif type==_na.UInt32:  return [32,-1,0]
    elif type==_na.Int32:  return [32,-1,0]    
    elif type==_na.Float32:  return [32,-1,0]    
    else: raise ValueError, "Unknown signal type"
           
def unpack_bits(value,vect_info):
    """Unpack a scalar binary representation into a vector."""    
    vect = []
    for nbits,mask,mask_ in vect_info:
        vect.append(value&mask)
        value  = value>>nbits
    return vect

def pack_bits(vect,vect_info):
    """Pack a vector into a scalar binary representation."""
    value = 0; shift = 0; i = 0
    for nbits,mask,mask_ in vect_info:
        value|=(vect[i]&mask)<<shift
        shift+=nbits
        i+=1
    return value

#def natural_bit_positions(signals):
#    """Computes the natural ordering of bit positions for an ordered list
#    of signals---bit positions count up from 0"""
#    position = 0; bit_pos = {}
#    for sig in signals:
#      bit_pos[sig] = position
#      nbits,mask,mask_ = binary_info(sig)
#      position+=nbits
#    return bit_pos

def word_partition_outputs(signals):
    """Partitions the outputs into groups of 32 bit words."""
    partitions = []
    partition = []
    shift = 0; bit_pos = {}
    for sig in signals:
      nbits,mask,mask_ = binary_info(sig)
      if shift+nbits>32: # start a new position
          shift=0
          partitions.append(partition)
          partition = [sig]
      else:
          partition.append(sig)
      shift+=nbits
    if partition!=[]:
        partitions.append(partition)
    return partitions


# Base function for compiling a LUT
def compile_rule_lut(rule):
    """Get a lookup table representing a rule's transition function"""

    outputs = rule.outputs; inputs = rule.inputs

    # get the binary information for the loop
    output_bin_info = map(binary_info,outputs)
    input_bin_info = map(binary_info,inputs)

    # Get and check the size of the LUT inputs and outputs
    nbits  = reduce(lambda x,y: x+y[0],input_bin_info,0)
    length = 1<<nbits
    width  = reduce(lambda x,y: x+y[0],output_bin_info,0)

    if nbits>32:
      raise StepError, \
           """Can not support luts with more than 32 bits of input"""
    if width>32:
      raise StepError, \
           """Can not support luts with more than 32 bits of output"""
  
    # Do the LUT compilation loop
    lut = _na.zeros([length],_na.Int32)
    input_scalar = 0
    strobed_rule = rule.__strobed__
    while input_scalar<length:
        # XXX should add methods to display progress
        # Construct inputs to the LUT
        input_vals = unpack_bits(input_scalar,input_bin_info)

        output_vals = strobed_rule(input_vals)
        output_scalar = pack_bits(output_vals,output_bin_info)
        # Store the output into the LUT
        lut[input_scalar] = output_scalar
        input_scalar+=1
    return lut

import math
# Compile a rule with a wide LUT
def compile_rule_widelut(rule):
    """Get a lookup table representing a rule's transition function. Make
    it as many words wide as is necessary."""

    outputs = rule.outputs; inputs = rule.inputs
    input_bin_info = map(binary_info,inputs)
    
    partitioned_outputs = word_partition_outputs(outputs)
    partitioned_bin_info = []
    for partition in partitioned_outputs:
        partitioned_bin_info.append(map(binary_info,partition))

    # Get and check the size of the LUT inputs and outputs
    nbits  = reduce(lambda x,y: x+y[0],input_bin_info,0)
    length = 1<<nbits

    if nbits>32:
      raise StepError, \
           """Can not support luts with more than 32 bits of input"""
  
    # Do the LUT compilation loop
    width = len(partitioned_outputs)
    # get to the next power of 2
    next_pow = int(math.ceil(math.log(width)/math.log(2)))
    pow2_width = 1<<next_pow
    lut = _na.zeros((length,pow2_width),_na.UInt32)
    input_scalar = 0
    strobed_rule = rule.__strobed__
    while input_scalar<length:
        # XXX should add methods to display progress
        # Construct inputs to the LUT
        input_vals = unpack_bits(input_scalar,input_bin_info)

        output_vals = strobed_rule(input_vals)
        j = 0
        for i in xrange(width):
           partition_info = partitioned_bin_info[i]
           partition_sz = len(partition_info)
           output_vals_ = output_vals[j:j+partition_sz]
           output_scalar = pack_bits(output_vals_,partition_info)
           j+=partition_sz
           # Store the output into the LUT
           lut[input_scalar,i] = output_scalar
        input_scalar+=1
    return lut.flat


def get_rule_lut(rule,wide=0,verbose=1):
    """Either recompile the LUT or get it from the cache. If wide is
    specified, it compiles a wide LUT"""
    hash = rule.__strobed__.hash_string()
    try:
        lut = cache.cache[hash]
    except KeyError:
        if verbose:
            print "compiling LUT for", rule.rule_function.__name__
        if wide:
            lut = compile_rule_widelut(rule)
        else:
            lut = compile_rule_lut(rule)
        cache.cache[hash] = lut
    return lut
    

def compile_lut_rule_lut(rule):
    """Compile a LUT for a LUT rule"""
    pass
    
