# latticearray.py: Class for representing a lattice object in SIMP
# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.3 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/latticearray.py,v $

"""
Python conventions for subscript indexing support selecting single
points and slices of them.  Numarray extends these conventions to
multidimensional arrays.  SIMP employs similar conventions, but
modifies them to account for lattice arrays and arrays with
wraparound.

In numarray, a[1,2] specifies the point at [1,2]. a[1:5,2:5] specifies
the rectangle starting at [1,2] and stopping at, but not including
[5,5] (the size of the slice is [4,3], rather than [5,4] since the
stopping boundary is not included).  Python slicing can also use
implicit indices as in a[1:,2:], which specifies all the points from
[1,2] up through the upper bound of the array or a[:1,2:] which
specifies all the points from [0,2] up through 1 in the most
significant dimension and the bounds of the array in the least.  The
entire array can also be selected as in a[:,:].

To represent these index subscripts, Python uses lists.  a[1,2] is
converted straightforwardly to [1,2]. Slice subscripts are converted
to slice objects.  For example, a[1:] is converted to
[slice(1,None,None)] where the elements of the slice---start,stop, and
step---indicate the starting position for the slice, the stopping
position and the step (stride) size.  (Currently, SIMP does not use
the stride).  A value of None for stop indicates that the slice
extends to the bound of the array, for start it indicates a start of
0, and for step, a step of one.


Represented as such, slices are relative to the implicit size of the
array and its boundaries.  In SIMP, we provide similar subscripting
facilities for signal objects.  Signals are allocated on a rectangular
grid, which gives the bounds of the coordinates for indexing.
However, a numarray, a signal has a boundary that wraps around and a
stop index that is smaller than the start index wraps around the
boundary (in an ordinary array, such a start/stop pair selects no
elements). Therefore, unlike the same subscript on a numarray which
selects no elements, a subscript s[1:1,2:2] on a signal actually
selects the entire space starting from position [1,2].  (s[:1,2:] has
the same interpretation for an array.  Also, indexes that are greater
than the boundary are automatically wrapped.

Examples with wraparound. Assume boundary is [200,100]
  a[:,:] specifies the entire space,  from [0,0] to [200,100](==[0,0])
  a[2:2,1:1] the entire space starting from [2,1], and ending at [2,1]
     (equivalent to a[2:202,1:101])
  a[:2,:1] from [0,0] to [2,1]
  a[2,1] the point, 2,1
  a[...,1] everything in the highest dimension, 1 in the lowest

Python subscripts are a convenient way for the system to represent
represent subscripts, however it is not always the most suitable one.
One may wish to obtain an absolute (rather than relative) slice.  One
may need separate the start, stop, and step vectors rather than have
them packed into a single list. The user might like to specify a slice
by means of a start and stop vector---rather than as a slice.  Because
of this and the fact that regions are used often, STEP chooses to
represent them with an object---called a Region object.  A region
object may be initialized with a slice.  Like a Python subscript, a
Region may be given in relative form. It may also be converted to an
absolute form once the geometric parameters are known.

We call a region that has only a start, but no stop an index.
The size of a region is a multidimensional vector giving the
number of grid points from start to stop (wrap-around included if
the boundary wraps). 

Lattice Regions

  In addition to their boundary conditions, Signal indexes and regions
  have another wrinkle.  Unlike an array which has an element at every
  positive integer point in their bounds, a Signal is allocated on a
  sublattice of the integer grid and may start at position that is
  offset from the origin. The grid sublattice is represented by an
  upper triangular HNF generator matrix---a set of vectors giving the
  offsets in each dimension of lattice points from each-other.  The
  diagonal of the generator matrix gives the orthogonal spacing of
  lattice points.  It is a rectangle.
  
  Giving a single index specifies the lattice element in the
  rectangular region from the index to the index plus the spacing.
  Because the rectangle given by the spacing is a unit cell of the
  lattice, it is guaranteed to contain exactly one lattice element.
  By extension, the number of lattice elements in a region can be
  computed by element-wise dividing the size of the region by the
  lattice spacing.  If an integer results, the region contains a fixed
  number of elements. If not, the number of elements in the region
  depends on the position of the lattice and the the position of the
  region.  In general, this is bad since it may result in a
  non-rectangular region. Therefore, when this is occurs, either the
  region should be normalized by adjusting the stop vector (rounding
  it up or down to the nearest multiple---up probably makes the most
  sense) or an error should be raised. 

  When a Signal region is selected, it is read out to an array.  Unlike
  the lattices of a signal, arrays must be compact.  A rectangular region
  can be packed into an array.  We describe how below.

  One can view a region as a collection of index points.  In the
  standard array view, this collection includes every integer vector
  between start and stop.  However, when the lattice spacing is larger
  than unity, the array view has more points than the lattice.  An
  alternate collection of index points is in order.  We choose the
  points between start and stop at integer multiples of the lattice
  spacing.  This not only gives the right number of points in each
  dimension, but also, when combined with the rectangular unit cell of
  the spacing, gives a means for associating lattice points with elements
  of a compact array.

  If the size of the region is a multiple of the spacing, the size the compact
  array will always be fixed.

Lattice Regions with steps or a step lattice

  Although we don't currently support it, it would be possible to 
  specify regions with steps.  When this is done, the region may be seen
  as a collection of points.  Giving a step yields a mechanism for selecting
  the points where the rectangle unit cells begin.  The steps could
  be restricted to multiples of the spacing so that overlap and irregular
  regions may be avoided.  Furthermore, rather than using only a vector
  to give the steps, a generator matrix could be used. 


Converting Python Subscripts to Regions

   When the user specifies a region it is typically done in a relative
   way using a Python subscript.  However, a region may also be specified
   by start and stop vector. Similar to a Python slice, a step might also
   be given.  In the region object, we convert a subscript (with slices)
   into start and stop vectors.  The region can be converted into an
   absolute region given the lattice, size and boundary conditions.
   
   The start vector is always an integer vector, however, it may have an
   Ellipsis object at the beginning or end to denote elided indices.  If
   the region is given only by a start point (single index), the stop
   vector is not given, and its value is set to 'NoIndex'.  In such a case,
   the region is an index.
   
   If the region contains more than a point, the stop vector is defined.
   In each dimension, the elements of the stop vectors indicate the extent
   of the region. An integer value indicates a stopping coordinate, a None
   value indicates the entire space, and a NoIndex value indicates that only
   the start coordinate is given and that the stop should be adjusted to include
   exactly one point.
   
   The None and NoIndex values in a region can not really be interpreted
   and used until it is converted to an absolute region.  When this
   happens, NoIndex and None values are converted to actual values.
   Currently, SIMP only supports regions that wrap around on the torus.
   
   In the case of SIMP, this conversion requires that we specify the
   generator of the lattice for the region, the boundary type and the
   size of the boundary.  Currently, the only boundary type that SIMP
   addresses is the wrapped boundary. To accomodate this class of wrapped
   region, we provide a class called WrappedLatticeRegion.  It is
   constructed with a relative region, a size bound and the generator
   matrix of a lattice.

Region Computations

   One of the most important region computations is converting a
   relative region into an absolute one.  Once this is done, a host of
   other computations may be performed such as ones to determine the
   size of a region.  Absolute regions are used in conjunction with
   lattices to index and scan the arrays that store the the signals
   and compute the size of arrays.


Rectangular mapping

   Talk about it...

Canonical form
   When a region is made into an absolute region (with wraparound), the
   start and stop methods return the starting position and stopping position
   as absolute coordinates.  The stop coordinate may be obtained in
   one of two forms---wrapped and unwrapped.

   In wrapped form, the stop index elements may be wrapped around and
   smaller than the corresponding start element.  In unwrapped form,
   the stop coordinate elements are strictly larger than the start
   elements.  Internally, the coordinates are stored in unwrapped
   form.
   

-------------------------------- doc testing
>>> from latticearray import *
>>> Region(subscr[:,1,1,2:1])
Region([0, 1, 1, 2],[None, NoIndex, NoIndex, 1])
>>> Region(subscr[:,1,1,2:1]).subscript()   
[slice(0, None, None), 1, 1, slice(2, 1, None)]
>>> Region(subscr[1,1,1])
Region([1, 1, 1],None)
>>> r = Region(subscr[:,1,1,2:1])
>>> Region(r)
Region([0, 1, 1, 2],[None, NoIndex, NoIndex, 1])
>>> r.size()
[None, NoIndex, NoIndex, -1]
"""

import copy as _copy
import types as _types
import math as _math
import numarray as _na
import numarray.linear_algebra as _la

import geom as _geom

import inspect as _inspect

class __subscript__:
    """A class whose 'getitem' function returns a slice"""
    def __getitem__(self,slice):
      return slice

subscr = __subscript__()
Subscr = __subscript__()


class __NoIndex__:
    def __repr__(self):
        return "NoIndex"

NoIndex = __NoIndex__()


# ================================================================
# ================================================================
class LatticeArray:
  """Base class for STEP lattice array objects
  
  Public attributes (read only)
    generator : generator matrix for the lattice
    igenerator : inverse of thhe generator matrix
    spacing : orthogonal spacing of the lattice's generators     
    size : the size of the lattice's underlying grid
    shape : shape of multidimensional array holding the lattice points
    nd : number of dimensions
  """
  def __init__(self,generator=None,size=None):
      """Generic method for setting up the lattice parameters for the signal"""
      self.generator = _na.array(_geom.asgenerator(generator,size))
      self.igenerator = _la.inverse(self.generator)
      self.spacing = self.generator.diagonal()
      self.nd = len(size)
      self.size = _na.array(size)
      self.shape = _geom.asintarray(self.size*self.igenerator.diagonal())


      # Helper members for lattice geometric calculations
      self.__iG__ = self.igenerator
      self.__G__ = self.generator
      # flags 
      self.__orthonormal__ = _geom.isorthonormal(self.__G__) # 
      self.__orthogonal__ = _geom.isdiagonal(self.__G__)
      # rectangular generator and helpers
      self.__h__ = self.__G__.diagonal()
      self.__H__ = _na.identity(self.nd)*self.__G__
      self.__iH__ = _la.inverse(self.__H__)
      self.__GiH__ = _na.dot(self.__G__,self.__iH__)
      self.__HiG__ = _na.dot(self.__H__,self.__iG__)
      
#  def array_index(self,coord,out=None):
#      """Return the array index associated with a given coordinate."""
##      if self.__orthonormal__: return coord
#      if out==None:  out = [0]*len(coord)
#      c = _geom.dot(coord,self.__iH__)
#      for i in xrange(self.nd):  out[i] = _math.ceil(c[i])
#      d = _geom.dot(out,self.__GiH__)
#
#      for i in xrange(self.nd):
#          out[i] = int(_math.ceil(c[i]-(d[i]%1.)))%self.shape[i]
##      b = _na.array(
##          [b[i]%self.shape[i] for i in xrange(self.nd)],type=_na.Int32)
#      return out      
#
#  def coset_coord(self,coord,out=None):
#      """Return the rectangular coset coordinate of a coordinate."""
#      if out==None: out = [0]*len(coord)
#      else: out[:] = [0]*len(coord)
#      
#      for i in xrange(self.nd):
#          spacing_ = self.spacing[i]
#          div,mod = divmod(coord[i],spacing_)
#          out[i] = (out[i]+mod)%spacing_
#          for j in xrange(i+1,self.nd):
#              out[j]+=self.generator[i,j]*div # add the generator.
#      return out      
#  
#
#  def coord(self,index,out=None):
#      """Return the coordinate associated with a given index."""
##      if self.__orthonormal__: return index
##      elif self.__orthogonal__: return index*self.__h__
#      if out==None: out = [0]*len(index)
#      coord = _geom.dot(index,self.__G__) 
#      for i in xrange(len(coord)):
#          out[i] = index[i]*self.spacing[i]+(coord[i]%self.spacing[i])
#      return out

  def __array_index__(self,coord,out=None):
      """Return the array index associated with a given coordinate."""
#      if self.__orthonormal__: return coord
      if out==None:  out = [0]*len(coord)
      c = _geom.dot(coord,self.__iH__)
      for i in xrange(self.nd):  out[i] = _math.ceil(c[i])
      d = _geom.dot(out,self.__GiH__)

      for i in xrange(self.nd):
          out[i] = int(_math.ceil(c[i]-(d[i]%1.)))%self.shape[i]
#      b = _na.array(
#          [b[i]%self.shape[i] for i in xrange(self.nd)],type=_na.Int32)
      return out      

  def __coset_coordinate__(self,coord,out=None):
      """Return the rectangular coset coordinate of a coordinate."""
      if out==None: out = [0]*len(coord)
      else: out[:] = [0]*len(coord)
      
      for i in xrange(self.nd):
          spacing_ = self.spacing[i]
          div,mod = divmod(coord[i],spacing_)
          out[i] = (out[i]+mod)%spacing_
          for j in xrange(i+1,self.nd):
              out[j]-=self.generator[i,j]*div # add the generator.
      return out      

  def __rect_divmod__(self,coord):
      """Return the rectangular division and modulus of a coordinate"""
      divcoord = [0]*len(coord)
      modcoord = [0]*len(coord)
      for i in xrange(self.nd):
          spacing_ = self.spacing[i]
          div,mod = divmod(coord[i],spacing_)
          divcoord[i]=div*spacing_
          modcoord[i] = (mod+modcoord[i])%spacing_
          for j in xrange(i+1,self.nd):
              modcoord[j]+=self.generator[i,j]*div # add the generator.
      return divcoord,modcoord

  def __coordinate__(self,index,out=None):
      """Return the coordinate associated with a given index."""
#      if self.__orthonormal__: return index
#      elif self.__orthogonal__: return index*self.__h__
      if out==None: out = [0]*len(index)
      coord = _geom.dot(index,self.__G__) 
      for i in xrange(len(coord)):
          out[i] = index[i]*self.spacing[i]+(coord[i]%self.spacing[i])
      return out


  
# ================================================================
# ================================================================

class Region:
    def __init__(self,subscr=None):
        """Initialize with a region or list of slices
        Public attributes (read only)
          start : start position for the region
          stop : stop position for the region
        """
        if isinstance(subscr,Region):
            self.start = _copy.copy(subscr.start)
            self.stop = _copy.copy(subscr.stop)
            return 
        elif isinstance(subscr,_types.SliceType):
            subscr = [subscr]
        elif len(subscr)==2 and (isinstance(subscr[0],_types.ListType)
                               or isinstance(subscr[0],_types.TupleType) 
                               or isinstance(subscr[0],_na.NumArray)):
            # XXX do some value checking here
            self.start = subscr[0]
            self.stop = subscr[1]
            return
            

        start = []; stop = []
        has_stops = 0
        for i in xrange(len(subscr)):
          stop_ = NoIndex
          try:
            start_ = int(round(subscr[i])) # round to the nearest integer
          except TypeError:
            has_stops = 1
            sl = subscr[i]
            if not isinstance(sl,_types.SliceType):
              raise IndexError, "Invalid subscript %s" % sl
            try:
              if sl.start==None: start_ = 0
              else: start_ = int(round(sl.start))
            except:
              raise IndexError, "Invalid subscript %s" % sl
            stop_ = sl.stop
            # hack for 1d slices obj[:] -> slice(0,2147483647,None)
            if stop_==2147483647: stop_=None
            try:
                if stop_!=None: stop_ = int(round(stop_))
            except: raise IndexError, "Invalid stop %s" % stop_
            # XXX should do something with the steps
            if sl.step!=None:
                raise IndexError,"A region may not have a step %s" % sl
          start.append(start_); stop.append(stop_)
        if not has_stops: self.stop = None
        else: self.stop = stop
        self.start = start

    def subscript(self):
        """Return a Python list representing the region's subscript"""
        if self.stop==None:
            return _copy.copy(self.start)
        subscr = []
        for i in xrange(len(self.start)):
            start_ = self.start[i]
            stop_ = self.stop[i]
            if stop_==NoIndex:
                subscr.append(start_)
            else:
                subscr.append(slice(start_,stop_))
        return subscr

    def size(self):
        """Gives the size of the region. Returns None if its the size
        of the space, or a vector of sizes"""
        extent = []
        if self.stop==None: return None
        for i in range(len(self.start)):
            try:
                extent.append(self.stop[i]-self.start[i])
            except: extent.append(self.stop[i])
        return extent
    
    def __repr__(self):
        return "Region(%s,%s)" % (self.start,self.stop)

    def __add__(self,other):
        start = self.start(); stop = self.stop()
        try:
            for i in xrange(len(start)):
                start[i]+=other[i]
            if stop!=None:
                for i in xrange(len(start)):                
                    if stop[i]!=NoIndex and stop[i]!=None:
                        stop[i]+=other[i]
        except TypeError: # len failed
            for i in xrange(len(start)):
                start[i]+=other
            if stop!=None:
                for i in xrange(len(start)):                
                    if stop[i]!=NoIndex and stop[i]!=None:
                        stop[i]+=other
        return Region([start,stop])
    
    def shape(self):
        raise NotImplementedError

    def center(self):
      if self.stop==None: return self.start
      return (self.stop+self.start)/2

#    def __eq__(self,other):
#      try:
#          if self.start==other.start:
#              return 1

# ================================================================
# ================================================================

class LatticeArrayRegion(Region):
    """Region for lattices on spaces that wrap around"""
    def __init__(self,region,lat_arr,fit=1):
        """ 
        If fit is set, then fit the region to the lattice generator
        so that the size of the region is a multiple of the lattice spacing.
        Also, if the region is larger than the bounds, snap to the bound
        size. Otherwise, raise errors if the bounds are not correct. 
        """
        self.lat_arr = lat_arr  # Array lattice that the region refers to
        size = self.lat_arr.size
        Region.__init__(self,region)        
        if len(self.start)!=len(size):
            raise IndexError, "Mismatch in number of dimensions"
        
        # Normalize to the size of the region and size
        # Raise an error if the size is too large, or the stop dimension
        # does not fit.
        for i in xrange(len(self.start)): # wrap the start position
            self.start[i] = self.start[i]%size[i]
            
        if self.stop==None:
          self.start = _na.array(self.start)
          self.size = self.lat_arr.spacing
          self.shape = _na.ones(self.lat_arr.nd)
          return

    
        for i in xrange(len(self.start)): # wrap the start position
            stop_ = self.stop[i]
            if stop_==None: # end of the space
                stop_ = size[i]
            elif stop_==NoIndex: # region offset
                stop_ = self.start[i]+self.lat_arr.spacing[i]
            else:
                stop_ = stop_%size[i]
                if stop_<=self.start[i]: # make stop > start...
                    stop_ = stop_+size[i]
            self.stop[i] = stop_
        # compute the size of this region.
        reg_size = []
        reg_shape = []
        spacing = self.lat_arr.spacing
        for i in xrange(len(self.start)):
            reg_size_ = self.stop[i]-self.start[i]
            div,mod = divmod(reg_size_,spacing[i])            
            if mod: # the region
                if not fit:
                    raise ValueError, \
                "Region is not a multiple of the lattice spacing in index "+`i`
                self.stop[i]+=(spacing[i]-mod)
                reg_size_+=(spacing[i]-mod)
                div+=1
            reg_size.append(reg_size_)
            reg_shape.append(div)
        self.start = _na.array(self.start)
        if self.stop!=None:
          self.stop = _na.array(self.stop)        
        self.size = _na.array(reg_size)
        self.shape = _na.array(reg_shape)
                            
    def __repr__(self):
        return "LatticeArrayRegion(%s,%s)" % (self.start,self.stop)

# ================================================================
#                        TESTING
# ===============================================================

def _decode(lat_arr,targets):
  Y,X = list(lat_arr.size)
  out = _na.zeros((Y,X))
  for y in range(Y):
      for x in range(X):          
          indx = [y,x]
          b = lat_arr.__array_index__(indx)
          for target,tag in targets:
              if _na.allclose(b,target,.00000001):
                  out[y,x] = tag
  return out

def _test():
    Region(subscr[:,1,1,2:1])
    Region(subscr[:,1,1,2:1]).subscript()        
    Region(subscr[1,1,1])
    r = Region(subscr[:,1,1,2:1])
    print Region(r)
    print Region(r).subscript()
    print Region(r).start
#    r = Region(subscr[2:4,4:])
#    r = Region(subscr[2:4,-2:4])
    r = Region([[1,3],[7,7]])
    la = LatticeArray([[1,1],[0,2]],[100,100])
    lr = LatticeArrayRegion(r,la)
    print lr.stop,lr.start
    print lr.size
    print lr.shape
    wr = LatticeArrayRegion(subscr[4:4,:],la)
#    for x in region_to_wrapped_slices(wr,[0,0]): print x
#    la = LatticeArray([[3,1],[0,4]],[12,12])
    la = LatticeArray([[4,2],[0,4]],[16,12])
    print "array shape",la.shape
#    print la.shape
#    print _decode(la,[[(0,0),1],[(0,1),2],[(0,2),3],
#                      [(1,0),4],[(1,1),5],[(1,2),6]])

    
    
    
if __name__=="__main__":
    _test()
