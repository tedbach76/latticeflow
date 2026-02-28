"""simp, a Python programming environment for cellular and lattice gas automata

For general documentation see
  http://simpstep.sourceforge.net

Copyright (C) 2004 Ted Bach, BU Programmable Matter Group

print simp.__LICENSE__    for the terms of use
"""

# CVS Information 
# $Revision: 1.3 $
# $Source: /u/tbach/simpstep_cvs/simp/Lib/__init__.py,v $


__LICENSE__ = """
SIMP: Cellular and lattice gas automata in Python
Copyright (C) 2004,2005  Ted Bach

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

(The full text of the license is in the source distribution /LICENSE.txt)
"""

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#                    IMPORTS
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

from simpinclude import version as __version__

# System modules
import sys as _sys
import inspect as _inspect
import time as _time
import os as _os
import types as _types
# Numarray
import numarray.random_array as _ra
import numarray as _na
import numarray.linear_algebra as _la

# SIMP modules
import step as _step
import geom as _geom

# Definitions included in the SIMP environment.
from step import *
from helpers import *
from renderers import *
from pygame_console import Console 

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#                    DECLARATIONS AND DEFAULTS
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

# The default step implementation
#__stepname__ = "Reference"
#__stepname__ = "PcSsamearray"
__stepname__ = ["PcCodeGen","Pc"]
#__stepname__ = ["Pc"]
__verbose__ = 1
__stepargs__ = {}

# local names
__names__ = ["__size__","__generator__","__stepname__","__step__"]

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#                    READ the SIMP config file 
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
__home__ = _os.path.expanduser("~")
if __home__ == "~":
   #  "no home directory"
   __home__ = "c:/"   # hack for older versions of windows.
   #  print "using",__home__
__simprc__ = _os.path.join(__home__,".simp")

try: exec(open(__simprc__).read())
except IOError: pass
except Exception, e:
    print "You have an error in your simp configuration file %s" % __simprc__
    raise e

# replace defaults if they are defined in the config file
try: __default_stepname__ = default_stepname
except NameError: pass

try: __verbose__ = verbose 
except NameError: pass

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#                    WRAPPER FUNCTIONS 
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# These wrapper functions wrap the step classes with the same name
# and automatically supply the simp module to the step classes that
# require the simp module for setting default values and determining
# the STEP.

def Signal(type,generator=None):
    """SIMP wrapper function that returns a new step Signal object.

    The actual Signal class definition is simp.step.Signal.  Use it
    for determining whether an object is of type Signal. 
    """
    simp = simpmodule()
    return _step.Signal(type,generator,simp)

def OutSignal(type,generator=None):
    """SIMP wrapper function that returns a new step OutSignal object.

    The actual Signal class definition is simp.step.OutSignal.  Use it
    for determining whether an object is of type OutSignal. 
    """
    simp = simpmodule()
    return _step.OutSignal(type,generator,simp)

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#                    STEP METHOD WRAPPERS
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def Do(op,n=1,parameters=()):
    """Do an operation or sequence of operations n times.

     This is a wrapper for the STEP step Do method. The optional parameters
     are used to used to pass the result arrays to a Read op.
    """
    __step__.Do(op,n,parameters)

def Flush(op,n=1,parameters=()):
    """Do an operation or sequence of operations n times.

     This is a wrapper for the STEP step Do method. The optional parameters
     are used to used to pass the result arrays to a Read op.
    """
    __step__.Flush(op,n,parameters)

def ClearCache(op,n=1,parameters=()):
    """Do an operation or sequence of operations n times.

     This is a wrapper for the STEP step Do method. The optional parameters
     are used to used to pass the result arrays to a Read op.
    """
    __step__.Flush(op,n,parameters)

def SeedRandom(n=None):
    """Seed the random number generator.

     Seeds the pseudo-random (deterministic) random number generator
     that STEP employs for \class{Shuffle} operations and SIMP employs for
     \method{makedist}. 
 
    The default seed is the current time (an integer cast of
    time.time()).  It is set automatically when SIMP initializes.
    """
    global _ra_seed
    if n==None:
        n = int(time.time())
    _ra_seed = (n,n)        
    __step__.SeedRandom(n)                        

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#                    SIMP FUNCTIONS
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
__initialized__ = 0
def initialize(size,generator=None,stepname=None,stepargs=None,verbose=None):
    """Sets up the simp module's global parameters.

    Calling initialize instantiates a STEP. Therefore, initialize must
    be called before any step objects are instantiated or step methods
    are called. initialize can only be called once per module, raises
    an Exception if called twice.

    The parameters are stored in the simp module as private
    variables (eg. size is stored as simp.__size__) and uses them
    first to load a STEP and later to construct default parameters for
    STEP ops and data types.

    keyword arguments
        size --- Vector giving the size of the integer grid. The length
            gives number of dimensions, n.
        generator --- The default generator (an $n$ dimensional matrix or
            vector) for LatticeArray objects (eg. Rule and Signal objects).
            Defaults to identity---the generator used for an ordinary CA.
        stepname --- String giving the name of the step implementation
            module. Defaults to the default module for the installation
            or set in the \module{simp} configuration file. Examples
            include "reference" and "pc". Raises an ImportError if not found.
        stepargs ---A keyword dictionary containing arguments for
            initializing the STEP. The nature of the arguments depends
            on the \module{step} module used. Defaults to no arguments.
        verbose --- Integer controling how much information
            \module{simp} and the step implementation module print.  0 ->
            nothing, 1 -> standard information, 2 -> detailed information,
            3+ -> debugging information. Defaults to 1.
    """
    global __size__,__generator__,__stepname__,__stepargs__,__verbose__
    global __step__,__nd__,__initialized__,__script_context__

    # set up context of the simp script
    __script_context__ = _inspect.stack()[1][0].f_globals
    
    # 1) Set up SIMP 'environmnent variables'
   
    if __initialized__:
        raise Exception,"SIMP has already been initialized"
        __initialized__ = 1

    if verbose!=None:
        __verbose__ = int(verbose)

    # Number of dimensions
    __nd__ = len(size)
    # Verify size
    __size__ =  _na.array(_geom.asintarray(size))

    if len(__size__.shape)!=1:
        raise ValueError, "Invalid shape for the size vector"
    if not (_na.alltrue(__size__>0)):
        raise ValueError, "Size vector must be positive"

    # 2) Get and verify the lattice.
    lat_err =  "Lattice generator must be an (n x n) matrix or (n) vector, \n"+\
               "where n is the number of dimensions."

    if generator==None:
        __generator__ = _na.identity(__nd__)
    else:
        generator = _geom.asintarray(generator)
        if len(generator.shape)==2:
            if not (generator.shape[0]==__nd__ or generator.shape[1]==__nd__):
                raise IndexError, lat_err
        elif len(generator.shape)==1:
            if not (generator.shape[0]==__nd__):  raise IndexError, lat_err
            generator = generator*_na.identity(__nd__)
        else:
            raise IndexError, lat_err
        __generator__ = _na.array(_geom.asgenerator(generator,size))
                  
    # 3) import STEP, and obtain the STEP class and initialize it

    if stepname!=None:
        __stepname__ = stepname
    if not type(__stepname__)==_types.ListType or \
        type(__stepname__)==_types.TupleType:
       __stepname__ = [__stepname__]
    if stepargs!=None:
       __stepargs__ = stepargs

#    if __stepname__=="NONE": return

    success = 0
    for stepname in __stepname__:
       if __verbose__:
          print "Trying to import",stepname
       try:
          modname = __name__+".stepmodules."+stepname
          __stepmodule__ = __import__(modname,globals(),
                                      locals(),
                                      modname.split(".")[0:-1])
          success = 1; break
       except ImportError, e:
         # Try to import the module by itself.
         print e         
         try:
            __stepmodule__ = __import__(stepname)
            success = 1; break
         except ImportError,e:
            if __verbose__:
              print "Unable to import simp.stepmodules.%s or %s" % \
                   (stepname,stepname)
              print e
    if not success: 
        raise ImportError, "Unable to import simp.stepmodules.%s or %s" % \
                   (__stepname__,__stepname__)
    if __verbose__:
       print "success!"
    __stepname__ = stepname
  
    __step__ = apply(__stepmodule__.Step,[size,__verbose__],__stepargs__)

    SeedRandom()

def __reset__():
    g = globals()
    
    for name in __names__:
        try: del g[name]
        except: pass

__self__ = _sys.modules[__name__]

def simpmodule():
    """Returns the simp module"""
    return __self__ #_sys.modules[__name__]


def declarecolors(generator=None):
    """Declares the common color OutSignal objects in the global namespace.

    This is a convenience function for rendering. 
    
    keyword parameters
      generator --- the generator for the OutSignal objects

    Declared Output Signals: red, green, blue, white, alpha
    Output tuples: grayscale=(white,white,white)
                   rgb=(red,green,blue)
                   rgba=(red,green,blue,alpha)

    One of the output tuples is usually passed as an argument to
    a Renderer object.

    Raises a NameError if any of these are already defined.
    """
    print """Warning: declarecolors is deprecated. Declare color OutSignal 
          objects directly instead."""
    if generator==None: generator = __generator__
    caller_globals = _inspect.stack()[1][0].f_globals
    names = ["red","green","blue","alpha","white"]+["rgb","rgba","grayscale"]
    sigs = []
    for i in xrange(5):
        new = OutSignal(UInt8,generator)
        sigs.append(new)
    vals = sigs+[(sigs[0],sigs[1],sigs[2]), # rgb
                 (sigs[0],sigs[1],sigs[2],sigs[3]),#rgba
                 (sigs[4],)] # grayscale
    for i in xrange(len(names)):
        name = names[i]
        if caller_globals.has_key(name):
            raise NameError,"%s is already defined" % name
        caller_globals[name] = vals[i]


def makedist(shape,dist):
    """Return a new numarray with a given shape and distribution of values.

    keyword parameters
      shape --- shape of the output array
      dist --- list giving the ratios of element values.

    makedist((4,4),[1,3,5])
    returns a 4 by 4 array in which approximately 1/8 elements are 0,
    3/9 are 1 and 5/9 are 2.

    The seed for the random number generator is set with SeedRandom.
    """

    # Keep local seeds for the random array functions. 
    global _ra_seed

    # save old seed, use private seed
    old_seed =_ra.get_seed()
    apply(_ra.seed,_ra_seed)
    
    dist = [0]+list(dist) # zero element
    dist = _na.array(dist,type=_na.Float)
    # normalize the distribution
    for i in xrange(1,len(dist)):
        dist[i]+=dist[i-1]
    dist = dist/dist[-1]
    ra = _ra.random(shape)
    # quantize the values to the distribution
    out = _na.zeros(shape)
    do_set = _na.zeros(shape,type=_na.Bool)    
    for i in xrange(2,len(dist)):
        _na.logical_and(ra>dist[i-1],ra<=dist[i],do_set)
        _na.add(out,do_set*(i-1),out)

    # save seed, return old seed
    _ra_seed = _ra.get_seed()
    apply(_ra.seed,old_seed)
    
    return out

import numarray.nd_image as _nd_image
def getdist(arr,min,max):
    """Return the distribution of values between min and max of an integer array.
    keyword parameters
      arr --- the array
      min --- the minimum value
      max --- the maximum value (non inclusive)

    >>> arr = numarray.array([1,2,2,2,1,1,2,3,3,0])
    >>> getdist(arr,0,3)
    [1,3,4]
    
    For efficiency, should only be called on small ranges of values. 
    """
    # min = 0; max = arr.max()+1 return
    return list(_nd_image.histogram(arr,min,max,max-min))
