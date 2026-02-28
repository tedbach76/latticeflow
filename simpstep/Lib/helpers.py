# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.3 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/helpers.py,v $

"""
Author: Ted Bach (tbach@bu.edu)

A general repository of helper methods useful for writing SIMP programs.
See the SIMP tutorial for examples of how to use them.

functions:
rotations() --- circular rotations of lists
kwdict() --- create dictionary with kwdict(key=value)
kvdict() --- create value dictionary with kvdict(name=value)
arraytopnm()
ellipsemask()
magnify2d()

"""
__version__ = "$Revision: 1.3 $"
# $Source: /u/tbach/simpstep_cvs/simp/Lib/helpers.py,v $

import inspect as _inspect
import numarray as _na


def magnify2d(arr,mag,grid=0,out=None):
    """Return a magnified 2D image array with optional grid lines.

   This function is used to magnify image arrays. If the magnification
   is negative, the output array is shown at strides of '-mag'
   (decimation). 

   keyword parameters
     arr --- the array to be scaled--must have at least two dimensions
     mag --- the magnification to be applied in the two most
        significant dimensions. Must be a nonzero integer.
     grid --- the size of the grid lines defaults to zero (no grid lines)
     out --- output array. A new array is created by default.

    If the shape of the input array is (200,100) and the mag is 3,
    the output array will be of size (600,300) and each pixel in the
    original array will be expanded to 3x3 blocks 9 new pixels. If the
    spacing is 1, the blocks will be 2x2 and there will be a spacing
    of 1 between each block.

    """
    if mag<0:
        out_size = _na.array(arr.shape)/-mag
        out_size[2:]=arr.shape[2:]
    if mag>0:
        out_size = _na.array(arr.shape)*mag
        out_size[2:]=arr.shape[2:]
    else:
        raise ValueError, "Magnification can not be zero"

    # Allocate the output array if necessary
    if out!=None:
        if tuple(out_size)!=tuple(out.shape):
            raise ValueError, "Out shape does not match the rescaling"
        if grid!=0: out.flat[:]=0
    else:
        out = _na.zeros(out_size,type=arr.type())

    # negative magnification
    if mag<0:
        out[:,:,Ellipsis] = arr[::-mag,::-mag]
        return out
    # positive mag
    for i in range(mag-grid):
        out[i::mag,::mag,Ellipsis]=arr
    for i in range(1,mag-grid):    
        out[:,i::mag,Ellipsis] = out[:,::mag,Ellipsis]
    return out

def grayscaletorgb(arr,out=None):
    """Convert a grayscale array to a RGB array

    """
    if out==None:
      out = _na.zeros(list(arr.shape)+[3],type=arr.type())
    out[:,:,0] = out[:,:,1] = out[:,:,2] = arr
    return out

def rotations(lst):
  """Return a list of all circular rotations of a list.

  Rotates left, starting with the original list. 

  arguments:
  lst - list to rotate

  The result is [[lst[0], ... lst[n-2], lst[n-1]],
                 [lst[1], ... lst[n-1], lst[0]],
                  ...
                 [lst[n-1], ... lst[n-3], lst[n-2]] ]
  """
  out_lst = []
  length = len(lst)
  for i in range(0,length):
     new_lst = []
     for j in range(0,length):
       k = (i+j)%length                 # wrap around
       new_lst.append(lst[k])
     out_lst.append(new_lst)
  return out_lst

def kwdict(**kwargs):
  """Returns a dictionary keyed on the keywords as strings.

  >>> kwdict(a=1,b=3)
  {"a":1,"b":2}

  """
  return kwargs

def kvdict(**kwargs):
  """Returns a dictionary keyed on objects and values.

      >>> a = 5
      >>> b = "test"
      >>> kvdict(a=1,b=3)
      {5:1,"test":3}
      >>> {a:1,b:2} 

  kvdict(a=1,b=3) is basically equivalent to {a:1,b:2}.
  
  The key values must be in the namespace, otherwise a NameError is
  raised. A TypeError is raised if an object is not a hashable
  dictionary key.
  """
      
  # Do something to get the key values from the global namespace where
  # this function was called.
  
  # 1) unload the old context (remove values from the global namespace)
  caller_globals = _inspect.stack()[1][0].f_globals  # globals from caller

  kvdict = {}
  for key in kwargs.keys():
      try: new_key = caller_globals[key]
      except KeyError:
        try:
          caller_locals = _inspect.stack()[1][0].f_locals  # globals from caller
          new_key = caller_locals[key]
        except KeyError:
          raise NameError, "name '%s' is not defined" % key
      kvdict[new_key] = kwargs[key]
  return kvdict

import numarray as _na
def arraytopnm(array,maxval=255):
  """Return portable anymap (pnm) image string from an array and maxval.

  The array must be a 2D RGB array (3D numarray giving with
  a[Y,X,color] with color indexing RGB values), in which case a
  portable pixmap (.ppm) file string is returned, or a 2D grayscale
  array (a[Y,X] giving the grayscale value), in which case a portable
  graymap (.pgm) file string is returned.

  0 is the lowest intensity and maxval is the highest.
  If values in the array are not in range 0-maxval, the image will
  not be output correctly. The default maxval is 255. Maxval must be
  in the range 1 to 65536.
  """

  if maxval<256 and maxval>0:
     if not array.type()==_na.UInt8:
         # convert to UInt8
         array = _na.array(array,type=_na.UInt8)
#    raise TypeError, "The array type must be UInt8"
  elif maxval<65536:
      if not array.type()==_na.UInt16:
         array = _na.array(array,type=_na.UInt16)
  else:
      raise ValueError, "maxval must be in range 1 to 65536"

  if len(array.shape)==3 and array.shape[2]==3:
    header = "P6\n%s %s\n%i\n" % (array.shape[1],array.shape[0],maxval)
    return header+array.tostring()
  elif len(array.shape)==2: # grayscale
    header = "P5\n%s %s\n%i\n" % (array.shape[1],array.shape[0],maxval)
    return header+array.tostring()
  else:
    raise ValueError,\
      "Invalid shape %s  for the array---must be (Y,X,3) or (X,Y)" % array.shape

# magic width height [#comment\n] maxval pixels
# "(\S)*\s*(\S*)"

# see the ppm man page for an explanation of the format. 
import re as _re
_pnmsep = r"(\s+|\#[^\n]*\n)+"
_pnmre = _re.compile(\
  r"(?P<ext>\w+)"+_pnmsep+r"(?P<width>\d+)"+_pnmsep+\
  r"(?P<height>\d+)"+_pnmsep+r"(?P<maxval>\d+)\s(?P<data>.*)" \
  ,_re.DOTALL)
def pnmtoarray(pnmstr):
    """Return an (array,maxval) tuple constructed from a portable anymap (pnm) string.

    Note: can't handle ASCII or portable bitmap (pbm) file pnm formats.

    The string may only contain a single image. Raises a value error if the
    string is not a binary ppm or pgm file. 

    The maxval is the saturation value for the image.

    The resulting array is a 2D RGB array (3D numarray giving with
    a[Y,X,color] with color indexing RGB values) if the string is a portable
    pixmap (.ppm) file string or a 2D grayscale array (a[Y,X] giving the
    grayscale value) if the string was a portable graymap (.pgm) file string.

    The type of the array depends upon maxval of the ppm file.
      *    0<maxval<256  yields a UInt8 array
      *    255<maxval<65536  yields a UInt16 array
    """
    # first remove any comment lines...no can't do this first...
    ext = pnmstr[:2]
    # now match the format
    m = _pnmre.search(pnmstr)
    if m==None:
       raise ValueError, "Invalid pnm file"
    ext = m.group("ext")
    if not (ext=="P5" or ext=="P6"):
       raise ValueError, "Unrecognized pnm format"
    width = int(m.group("width"))
    height = int(m.group("height"))
    maxval = int(m.group("maxval"))
    data = m.group("data")    

    if 1<maxval and maxval<256: arrtype = _na.UInt8; targetsize=1
    elif maxval<65536: arrtype = _na.UInt16;targetsize=2
    else: raise ValueError, "Invalid maxval, %s" % maxval
    
    if ext=="P5":
        try:
          targetsize*=width*height;data = data[:targetsize]
          arr = _na.array(data,shape=(height,width),copy=1,type=arrtype)
        except ValueError:
          raise ValueError, "Invalid format"
    
    if ext=="P6":
        try:
          targetsize*=width*height*3;data = data[:targetsize]
          arr = _na.array(data,shape=(height,width,3),copy=1,type=arrtype)
        except ValueError, e:
          raise e
          raise ValueError, "Invalid format"
    return arr,maxval
                                  
    
import step as _step
import time
def benchmarkrule(rule,Niter=100):
  """Benchmark a rule, returning the number of sites updated per second
  
  """
  sz = 1
  for i in xrange(rule.nd):
     sz*=rule.size[i]/rule.spacing[i]
  t0 = time.time()
  for i in xrange(Niter):  rule()
  return (sz/(time.time()-t0))

def benchmark(func,Niter=100):
  """Returns the amount of time to call a function Niter times"""
  t0 = time.time()
  for i in xrange(Niter):  func()  
  return time.time()-t0

# ================================================================
#                        Helper Functions
# ================================================================
import math
def ellipsemask(shape): # ,axes=None
  """Return a 2D mask of values indicating the interior of an ellipse.

  parameters
    shape --- the shape of the array

  The major axes are Y-1,X-1 where shape=Y,X.  The goodness of the
  discrete ellipse approximation is dependent on the shape.  For
  example, odd number sizes are typically more accurate than accurate
  than even.
  """
  # XXX Need to improve the handling for signal lattices. 
  if isinstance(shape,_step.SignalRegion):
      shape = shape.shape
  
  if len(shape)!=2:
      raise ValueError, \
        """ellipsemask currently only handles 2D"""
  mask = _na.zeros(shape)
  Y,X = map(float,shape)
  Y,X = Y-1,X-1
  X_Y = (X/Y)
  epsilon = 10**-9
  for y in xrange(shape[0]):
      y_ = y
      half_x = X_Y*math.sqrt(math.fabs(y_*Y-y_*y_))
#      x_start = int(round(X/2.-half_x))
#      x_stop = int(round(X/2.+half_x))
      x_start = int(math.ceil(X/2.-half_x))
      x_stop = int(math.ceil(X/2.+half_x+epsilon))      
      mask[y,x_start:x_stop] = 1
  return mask

#def ellipsemask(shape):
#  """Return a 2D mask with the given shape an an ellipse drawin inside.
#
#  The ellipse is centered in the array and has axes given by Y and X,
#  shape=(Y,X).  
#  """
#  if len(shape)!=2:
#      raise ValueError, \
#        """ellipsemask currently only handles 2D"""
#  mask = _na.zeros(shape)
#  Y,X = map(float,shape)
#  X_Y = (X/Y)
#  for y in xrange(shape[0]):
#      y_ = y+.5
#      half_x = X_Y*sqrt(fabs(y_*Y-y_*y_))
#      x_start = int(ceil(X/2.-.5-half_x)) # the ceiling function takes care
#      x_stop = int(ceil(X/2.-.5+half_x))  # of adding .5
#      mask[y,x_start:x_stop] = 1
#  return mask

# -----------------------------------------------------

#class __class_wrapper__: pass
#
#def dict_wrapper(dict):
#    """Return a class whose attributes are given by a dictionary. Setting
#    attributes sets the dictionary value. Deleting them deletes the dictionary
#    value"""
#    d = __class_wrapper__()
#    d.__dict__ = dict
#    return d

if __name__=="__main__":
   expected_rot = ([1,2,3],[2,3,1],[3,1,2])
   rot = rotations([1,2,3])
   print rot

