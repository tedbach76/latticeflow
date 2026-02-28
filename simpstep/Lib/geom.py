# geom.py: Collection of geometric functions
# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.1.1.1 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/geom.py,v $

"""geom.py

Linear algebraic and computational geomeotry routines used by SIMP.

All matrices are assumed to be upper triangular.

This contains several functions for decoding vectors with respect
to lattices given by $n\times n$ matrices.
"""

#from ratmat import *
from math import *
import copy

import numarray as _na
import numarray.linear_algebra as _la


# ----------------------------------------------------------------
#                   Vector and matrix computations
# ----------------------------------------------------------------
# They are a simple re-implementation of those included with numarray.
# We do this because numarray is slow for small operations. (it has
# a large overhead)
def dot(x,V,out=None):
    """xV (saves constructing a new numarray)
    Dot product row vector and a matrix"""
    nd = len(x)
    if out==None: out = [0]*nd    
    for i in range(nd):
      for j in range(nd):
         out[i]+=x[j]*V[j,i]
    return out

def add(x,y,out=None):
    """adds two one dimensional vectors quickly (faster than numarray)"""
    nd = len(x)
    if out==None:out=[0]*nd    
    for i in range(nd): out[i]=x[i]+y[i]
    return out

def sub(x,y,out=None):
    """subtract two one dimensional vectors quickly (faster than numarray)"""
    nd = len(x)
    if out==None:out=[0]*nd    
    for i in range(nd): out[i]=x[i]-y[i]
    return out

def arr_as_int(arr,sz):
    """Convert an array in positional notation with digit sizes given
    by sz to an integer"""
    mul = 1
    i = len(arr)-1
    val = 0
    while i>=0:
        val+=mul*arr[i]
        mul*=sz[i]	
        i-=1
    return val

# ----------------------------------------------------------------
#                   HELPER ROUTINES
# ----------------------------------------------------------------

_lat_err =  "Lattice generator must be an (n x n) matrix or (n) vector, \n"+\
           "where n is the number of dimensions."

def gcd(a, b):
	"""Return GCD of two numbers. 
	"""
	while b:
		a, b = b, a % b
	return a

def lcm(a,b):
        """Return the least common multiple two numbers
        """
        return a*b/gcd(a,b)

def rectangular_cell_size(gen):
    """Given a generator matrix, returns the multiple of the rectangular,
    orthogonal unit cell size.
    """
    mult = []
    multiples = _na.zeros(gen.shape[0])
    for i in xrange(len(gen)):
        row_mults = []
        for j in xrange(len(gen)):
            if gen[i,j]!=0:
                row_mults.append(gen[j,j]/gcd(gen[j,j],gen[i,j]))
        mult.append(reduce(lcm,row_mults,1))
    return mult*gen.diagonal()

def multidimensional_inc(indx,bounds,inc=1,dimen=-1):
    """Increment a vector that wraps according to 'bounds'"""
    if dimen<0: dimen = dimen%len(indx)
    while dimen>=0: # increment in each dimension
      indx[dimen]+=inc
      if indx[dimen]>=bounds[dimen]:
        indx[dimen]=0
        dimen-=1
      else: return

def is_zero(vector):
    """Returns true if the vector contains all zeros"""
    for i in xrange(len(vector)):
       if vector[i]!=0: return 0
    return 1

def asgenerator(generator,size):
    """Return a verified HNF generator. Raise an error if the generator
    is not compatible with the given size. 
    """
    nd = len(size)
    generator = _na.asarray(generator)
    if len(generator.shape)==2:
        if not (generator.shape[0]==nd or generator.shape[1]==nd):
            raise IndexError, _lat_err
    elif len(generator.shape)==1:
        if not (generator.shape[0]==nd):  raise IndexError, _lat_err
        generator = generator*_na.identity(nd)
    else:
        raise IndexError, _lat_err
    ensure_hnf(generator)

    rect = rectangular_cell_size(generator)
    rect_multiple = size/_na.array(rect,type=_na.Float32)
    try: asintarray(rect_multiple,10**-10)
    except ValueError:
       try_size = _na.array(_na.around(rect_multiple),type=_na.Int32)*rect
       raise ValueError, \
           "The size is not a multiple of the generator's rectangular\n"+\
           "unit cell (%s) try %s instead." % (rect,try_size)
    return generator
                    
def isorthonormal(lat):
    return _na.alltrue((lat==_na.identity(lat.shape[0])).flat)

def vectintmod(a,b):
    """Vector integer modulus function"""
    return _na.array([a[i]%b[i] for i in xrange(len(b))])

def issublattice(a,b):
    """Returns true if the generator a is a sublattice of b"""
    b_ = _la.inverse(b)
    m = _na.dot(a,b_)
    try: m = asintarray(m,.0000000000001)
    except: return 0
    return 1

def scale_coord(v,pitch,snapto):
    """Scale a coordinate (or matrix).

    Make sure that it is within snapto of an integer, otherwise raise
    a ValueError"""
    w = v*pitch
    if w.type()==_na.Int32:  return w

    w_ = _na.around(w)
    if _na.sometrue((_na.abs(w_-w)>snapto).flat):
        raise ValueError, "%s does not snap to the grid" % v

    return _na.array(w_,_na.Int32)
    
def ensure_hnf(m):
    """Ensure that a matrix or diagonal vector is a HNF matrix.

    Raises a ValueError if it is not."""
    if not isinstance(m.type(),_na.IntegralType):
        raise ValueError, "Not in HNF: %s is not an integer matrix"% m
    if not isuppertriang(m):
        raise ValueError, "Not in HNF: %s is not upper-triangular"% m
    if _na.sometrue(m.flat<0):
        raise ValueError, "Not in HNF: %s contains negative elements"% m
    if _na.sometrue(_na.add.reduce((m>=m.diagonal()))>1):
      raise ValueError,"Not in HNF: A column element is greater than its diagonal"
        
def asintarray(a,epsilon=.5):
    """Coerce to an integer array if necessary.  array is not within epsilon
    of an array, raise a ValueError"""
    a = _na.asarray(a)
    if isinstance(a,_na.IntegralType): return a

    a_ = _na.around(a)
    if _na.sometrue((_na.abs(a_-a)>epsilon).flat):
        raise ValueError, "%s is not within %s of an integer" % (a,epsilon)
    return _na.array(a_,_na.Int32)
    
def issquare(m):
    """Return true if m is a square matrix."""
    if not len(m.shape)==2: return 0
    if not m.shape[0]==m.shape[1]: return 0
    return 1

def isuppertriang(m):
    """Is the matrix upper triangular?
    """
    for j in range(0,m.shape[0]):
       for i in range(0,j):
         if m[j,i] != 0:
           return 0
    return 1
    
def isdiagonal(m):
    """Returns true if a 2D square matrix is a diagonal with positive column
    elements."""
    non_zero_cols = _na.add.reduce(m!=0)
    return  _na.alltrue((m.diagonal()!=0)==non_zero_cols)

#def get_diagonal(m):
#    """Returns the diagonal of a square matrix."""
#    non_zero_cols = _na.add.reduce(m!=0)
#    return  _na.alltrue((m.diagonal!=0)==non_zero_cols)

def make_diagonal(a):
    a = _na.asarray(a)
    I = _na.identity(len(a))
    return a*i

def test():
    """Test the helper functions, raise a ValueError if one is invalid"""
    res = scale_coord(_na.array([2.5,1]),_na.array([2,2]),10e-99)
    if not _na.alltrue(res==_na.array([5,2])):
       raise Exception
    scale_coord(_na.array([2.5,1]),_na.array([1,1]),.5)
    try:
        scale_coord(_na.array([2.25,1]),_na.array([1,1]),10e-99)
        raise Exception
    except ValueError: pass

    A = _na.array([[3.5,1],[0,2]])
    b = _na.array([2,3])
    res = scale_coord(b,A,10e-99)

    if not _na.alltrue((res==_na.array([[7,3],[0,6]])).flat):
       raise Exception
    B = _na.array([[3.5,0],[0,2]])
    
    if (not isdiagonal(B)) or (isdiagonal(A)):
        raise Exception

    try: ensure_hnf(A); raise Exception
    except ValueError: pass

    B = _na.array([[3,4],[0,2]])    
    try: ensure_hnf(B); raise Exception
    except ValueError: pass

    B = _na.array([[3,1],[0,2]])
    ensure_hnf(B)

    b = _na.array([2.,3])
    asintarray(b,10e-99)
    b = _na.array([2.1,3])
    try:
        asintarray(b,10e-99)
        raise Exception
    except ValueError: pass
    
# # -------------------------------- VECTOR DECODERS
# def decode_parallelepiped(x,V_):
#     """ Input: $V_$, an $n\times n$ non-singular matrix $V_=V^{-1}$
#                $\vect{x}$, an $n$ dimensional vector 
#     Decodes the lattice vector in $V$ of $x$ with respect to the
#     parallelepiped unit cell.  Mathematically, this is the point
#     $\vect{a} \in \mathcal{Z}^n$ such that $\vect{x} = (\vect{a} +
#     \vect{\alpha})V$ where $0 \leq \alpha_i \leq 1$.
# 
#     In other words, $a = \lfloor \vect{x}V^{-1} \rfloor$. 
#     """
#     return matrix_floor(x*V_)
# 
# def decode_babai(x,V_):
#     """Decode to the nearest Babai point---the parallelepiped cell is
#     centered about the lattice point"""
#     return matrix_round(x*V_)
# 
# def decode_rectangular(x,V,V_):
#     """Decode according to the rectangular unit cell delimited by
#     the diagonals"""
#     a = matrix_floor(x*V_)
#     tmp = x-a*V
#     return a + matrix_floor( elt_div(tmp,V.diag()) )
# 
# 
# def decode_nearest(x,V,V_):
#     """Decode to the nearest lattice point"""
#     d   = decode_parallelepiped(x,V_)  # 'dividend'
# #    d   = decode_rectangular(V,U,x)  # 'dividend'
#     r   = x-d*V                       # 'remainder'
#     N = x.cols() # number of dimensions
#     min_dist = 1000000000000000
#     min_indx = -1
#     indx = 0; INDX = 1<<N;
# 
#     # search the N dimensional binary cube for the min distance vector
#     while indx < INDX:
#         candidate_point = row_vector([0]*N) # create an initial zero vector
#         # matrix multiply with the binary vector, indx
#         for i in xrange(N):
#           if indx&(1<<i):
#               candidate_point += V[N-i-1,:]
# 
#         # compute the distance
#         sep = r-candidate_point
#         dist = sqrt(sep*sep.transpose())
#         
#         # check whether it is minimal
#         if dist<=min_dist:
#           min_dist = dist
#           min_indx = indx
#         indx+=1
# 
#     if min_indx==-1: return -1
#     # compute a vector from the index
#     correction = binary_vector_unpack(min_indx,N)
#     return d + correction
# 
# 
# # --------------------------------
# # Tools for converting vectors to binary vectors and vice versa.
# def binary_vector_pack(v):
#     """Pack a vector into a binary number. Going from the least to
#     the most significant bit, any zero value is encoded as a zero, everything
#     else is a 1.
#     """
#     binary = 0; select = 1
#     if v.is_column_vector():
#         for i in xrange(v.rows()):
#           if v.m[i][0]!=0: binary&=select
#           select= select<<1
#     elif v.is_row_vector():
#         for i in xrange(v.columns()):
#           if v.m[0][i]!=0: binary&=select
#           select= select<<1
#     else:
#         raise Matrix_Size_Error()
#     return binary
# 
# def binary_vector_unpack(binary,N,col=0):
#     """  Unpack a binary vector into a matrix object vector containing
#     values {0,1} depending on the value of the corresponding bit. N specifies
#     the length of the vector.
#     If 'col' is true it unpacks a column vector otherwise a row.
#     """
#     select = 1    
#     if col:
#       unpack = Matrix(N,1)     # column vector
#       for i in xrange(N):
#           if (binary&select): unpack[N-i-1,0] = 1
#           select = select<<1
#     else:  # row vector
#       unpack = row_vector(1,N) # row vector
#       for i in xrange(N):
#           if (binary&select): unpack[0,N-i-1] = 1
#           select = select<<1
#     return unpack
# 
# # --------------------------------
# def vect_to_index(v):
#     indx = []
#     if  v.is_row_vector():
#         for i in  xrange(v.cols()):
#             indx.append(int(v.m[0][i]))
#     elif v.is_column_vector():
#         for i in  xrange(v.rows()):
#             indx.append(int(v.m[i][0]))
#     else:
#         raise Matrix_Size_Error("Expected a vector, but got a matrix")
#     return indx
# 
# # TODO : fix convention from here on down ...........
# # -------------------------------- APPROXIMATE_SUBLATTICES
# def ut_restricted_babai_approx_sublattice(U,V):
#     """Input
#                U: fundamental lattice
#                V: lattice for which an approximate sublattice should be found
#        Output
#                A: Babai approximate sublattice restricted such that
#                   the result is uper triangular. IE, a column will only 
#                   find its nearest point relative to previous conlumns.
#        Returns None if the result is not of full rank. 
#     """
#     A = Matrix(V.cols())  # start with an empty matrix
# 
#     A[0,0] = int(round(V[0,0]/U[0,0]))
#     for i in range(1,U.cols()):
#       Usub      = U[:i+1,:i+1]
#       Usub_     = ut_inv(Usub)
#       v         = V[:i+1,i]
#       A[:i+1,i] = decode_babai(Usub_,v)
# 
#     return A
#     det = A.determinant()
#     if det==0:
#         return None
#     return A
# 
# def ut_round_approx(U,V):
#     """Do a greedy search in each coordinate for the closest approximation"""
#     return U*matrix_round(ut_inv(U)*V)
# 
# def ut_floor_approx(U,V):
#     """Do a greedy search in each coordinate for the closest approximation"""
#     return U*matrix_round(ut_inv(U)*V)
# 
# def ut_ceil_approx(U,V):
#     """Do a greedy search in each coordinate for the closest approximation"""
#     return U*matrix_round(ut_inv(U)*V)
# 
# # -------------------------------- APPROXIMATE_SUBLATTICES.transpose()
# def next_multiple(a,vals):
#     """Returns the next number after 'a' that is a multiple of
#     one of the values in the list 'vals'
#     """
#     d_min = 1<<30
#     for v in vals:
#        n    = ceil(a/v)
#        next_ = v*n
#        d = next_ - a  
#        if d==0: d = v; next_+=v
#        if d < d_min:
#            next  = next_
#            d_min = d
#     return next
# 
# def prev_multiple(a,vals):
#     """Returns the next number after 'a' that is a multiple of
#     one of the values in the list 'vals'
#     """
#     d_min = 1<<30
#     for v in vals:
#        n    = floor(a/v)
#        next_ = v*n
#        d = a - next_  
#        if d==0: d = v; next_-=v
#        if d < d_min and next_!=0:
#            next  = next_
#            d_min = d
#     return next
#     
# 
# def relative_error(V,A):
#     """Computes the element size normalized approximation error between
#     a lattice V and an approximation, A.  Assumes V and A are both upper
#     triangular."""
#     N = V.cols()
#     error = 0
#     for i in xrange(N):
#         for j in range(i,N):
#             if V[i,j]!=0:
#               error += abs( (V[i,j]-A[i,j])/V[i,j] )
#     return error
# 
# def n_errors(V,A):
#     """Returns the number of elements containing scaling errors"""
#     N = V.cols()
#     n_error = 0
#     for i in xrange(N):
#         for j in range(i,N):
#             if V[i,j]!=A[i,j]:
#                 n_error+=1
#     return n_error
# 
# 
# def nonzero_elements(V):
#     """Return a list of the nonzero elements of a matrix"""
#     elements = []
#     for i in xrange(V.rows()):
#        v = V.m[i]
#        for j in xrange(V.cols()):
#            if v[j]!=0: elements.append(v[j])
#     return elements
# 
# # -------------------------------- SERIES OF APPROXIMATIONS (for rendering)
# def get_best_approximations(U,V,alpha_start,alpha_stop):
#     """Given a fundamental lattice U and a desired lattice
#     to approximate, this gives a list of best scalings ordered
#     selected to have non-increasign error.  A list containing
#     the following is returned:
#       [alpha,Approx,error,size]"""
#     alpha = alpha_start
#     increments = nonzero_elements(V)
#     increments = map(lambda x: 1./x,increments)
#     min_error = 100
#     best      = []
#     while alpha<alpha_stop:
#         V_    = V*alpha
#         A     = (U,V_)
#         error = relative_error(V_,A)
#         if error<=min_error:
#             min_error = error
#             best.append([alpha,A,error,A.determinant()])
#         alpha = next_multiple(alpha,increments)        
#     return best
# 
# # Get unique approximations of increasing size that have
# # a minimal number of errors component sizes.  For components
# # that do have errors, calculate all combinations the floor
# # and ceiling 
# def get_approximations(U,V,alpha_start,alpha_stop):
#     """Given a fundamental lattice U and a desired lattice
#     to approximate, this gives a list of best scalings ordered
#     selected to have non-increasign error.  A list containing
#     the following is returned:
#       [alpha,Approx,n_error,error,size]"""
#     alpha       = alpha_start
#     increments  = nonzero_elements(V)
#     N           = V.cols()
#     increments  = map(lambda x: 1./x,increments)
#     best        = []
#     min_error   = ((N+1)*N)/2
#     while alpha<alpha_stop:
#         V_      = V*alpha
#         A       = matrix_round(V_)
#         error   = relative_error(V_,A)
#         n_error = n_errors(V_,A)        
#         if n_error<min_error:
#             min_error = n_error
#             if n_error == 0: break
#             
#         if n_error==min_error:
#             # should do special things for the case where n_error>1
#             A       = matrix_floor(V_)
#             best.append([alpha,A,error,n_error,A.determinant()])
#             A       = matrix_ceil(V_)
#             best.append([alpha,A,error,n_error,A.determinant()])
#         alpha = next_multiple(alpha,increments)
#     return filter(lambda x: x[3]==min_error,best)
# 
# # ---------------------------------------------------------------- 
# #               LATTICE 
# # ----------------------------------------------------------------
# 
# # unit cell types...
# PARALLELEPIPED = 1
# BABAI          = 2
# RECTANGULAR    = 3
# NEAREST        = 4
# 
# # todo: make this work for situations where the geometric and
# #       index matrix don't coencide.
# class lattice:
#     # members 
#     # gen   : (geometric) generator matrix
#     # igen  : index generator matrix
#     # cell  : unit cell  (None -> nearest)
#     # mod   : modulus matrix
#     # imod  : index modulues matrix
#     # size  : size of the lattice (diag of imod)    
#     # pos   : the position of lattice
#     # ipos  : index space position of lattice    
#     # Conventions
#     #  * invers matrices are denoted by appending an underscore "_"
# 
#     def __init__(s,gen,size=None,pos=None,mod=None,cell=PARALLELEPIPED):
#         """lattice(gen,pos,cell,size,mod)"""
#         # ---------------- GENERATOR
#         gen = ensure_mat(gen)
#         if not gen.is_ut():
#             raise ValueError, "Expected an upper trigangular generator matrix"
#         s.gen  = gen; s.gen_ = ut_inv(gen)
#         s.nd = gen.cols() # may need to fix this ....
#         s.gen_ident = (s.gen==unit_matrix(s.nd))
# 
#         # ---------------- MODULUS, SIZE
#         if mod==None:
#             size = ensure_mat(size)
#             mod  = diag(elt_mul(size,s.gen.diag()))
#             mod.make_float()
#         else:
#             mod  = ensure_mat(mod)
#             size = mod.diag()
#         s.size = size
#         s.M  = mod
#         if not cell==PARALLELEPIPED:
#             raise NotImplementedError(
#                 "Can only use the parallelepiped unit cell")
#         s.M  = mod; s.M_ = ut_inv(mod)
# 
#         s.iM = s.M*s.gen_  # need to ensure that we result in ints here...
#         s.iM.make_rat()
#         s.iM_= ut_inv(s.iM)
#         if not s.iM.is_int():
#             raise ValueError("The modulus matrix must be a sublattice!")
#         # ---------------- POSITION
#         if pos==None:
#             pos = Matrix(1,s.nd)
#         else:
#             pos = ensure_mat(pos)
#         s.ipos = pos*s.gen_
#         s.ipos.make_rat()
# 
#         # ---------------- CELL
#         s.cell = cell
#         
# 
#     def gmod(s,x):
#         """Compute the geometric quotient and remainder of a geometric
#         vector with respect to this lattice"""
#         x = ensure_mat(x)
#         # wrap
#         x = s.gwrap(x-s.ipos*s.gen)
#         q = decode_parallelepiped(x,s.gen_)
#         r = x-q*s.gen
#         return q,r
# 
#     def imod(s,x):
#         """Compute the index quotient and remainder of an index vector wrt
#         this lattice"""
#         x = ensure_mat(x)
#         x = s.iwrap(x-s.ipos)
#         # parallelepiped...
#         q = matrix_floor(x)        # index quotient
#         r = x-q
#         return q,r
# 
#     def gwrap(s,x):
#         """Convert a geometric vector to a geometric point on the torus"""
#         x = ensure_mat(x)        
#         q = decode_parallelepiped(x,s.M_)
#         r = x-q*s.M
#         return r
# 
#     def iwrap(s,x):
#         """Convert an index vector to an index vector on the torus"""
#         x = ensure_mat(x)        
#         q = decode_parallelepiped(x,s.iM_)
#         r = x-q*s.iM
#         return r
# 
#     def i_g(s,x):
#         """Convert index vector to geometric vector"""
#         if s.gen_ident: return x
#         x = ensure_mat(x)
#         return x*s.gen
#         
# 
#     def g_i(s,x):
#         """Convert geometric vector to index vector"""
#         if s.gen_ident: return x        
#         x = ensure_mat(x)        
#         return x*s.gen_
# 
#     def set_ipos(s,pos):
#         """Set the position of the lattice (modulo the unit cell)"""
# #        s.ipos   = Matrix(1,s.ipos.cols()) # set to zero ...
# #        q,s.ipos = s.imod(pos)
#         #pos   = ensure_mat(pos)
#         if s.gen_ident:
#             q        = matrix_floor(pos)
#         else:
#             q        = decode_parallelepiped(pos,s.gen_)
#         s.ipos   = pos - q
# 
#     def ikick(s,kick):
#         """Translate the lattice by a fixed amount.  Sets the new
#         position to the remainder (pos+kick)%cell.  Returns the integer
#         quotient of (pos+kick)/cell."""
#         new_pos      = kick+s.ipos
#         if s.gen_ident:
#             q        = matrix_floor(new_pos)
#         else:
#             q        = decode_parallelepiped(pos,s.gen_)
#         s.ipos = new_pos-q
#         return q
# 
#     def sublattice(s,gen=None,cell=None):
#         """sublattice(gen,cell)
#         Get a sublattice from this lattice.
#         gen : an integer matrix giving the generators of the sublattice
#              with respect to this one
#         cell: specifies the unit cell of this 
#         """
#         return copy.deepcopy(s)
#       
# 
#       
# # ---------------------------------------------------------------- 
# #               REGIONS
# # ----------------------------------------------------------------
# #import math
# 
# class region_base:
#   """Base class for specifying regions of data"""
#   def iranges(s,lattice=None):
#       """Returns a set of index ranges---specified as (start,stride,span)
#       tuples----representing the lattice points of the region"""
#       raise NotImplementedError('Derived must override')
# 
# class ellipse(region_base):
#     def __init__(s,ul,lr):
#         """Specifies an ellipse circumscribed by a rectangle going from
#         ul to lr"""
#         s.ul = ul
#         s.lr = lr
#     def iranges(s,lattice=None):
#       # Need to update for lattices other than the rectangular one
#       if lattice!=None:
#           raise NotImplementedError('Derived must override')
#       y1,x1 = s.ul
#       y2,x2 = s.lr
# 
# 
#       iranges = [];
#       stride  = None;
#       
#       dy = float(y2-y1); dx = float(x2-x1); cx = x1+dx/2.0
#       y = y1
#       while y<y2:
#         half_x_len = (dx/dy)*sqrt(fabs(y*(y1+y2)-(y2*y1)-y*y))
#         x_start    = int(floor(cx-half_x_len))
#         x_len      = int(ceil(2*half_x_len))
#         if x_len:
#           iranges.append(([x_start,y],stride,[x_len,1]))
#         y+=1
#       return iranges
# 
#     def __str__(s):
#       return "ellipse("+`s.ul`+`s.lr`+")"
# 
#     def __repr__(s): return s.__str__()
#       
#       
# 
# # ---------------------------------------------------------------- 
# #               TEST PROCEDURES
# # ----------------------------------------------------------------
# if __name__=="__main__":
#   # do some tests
#   gen = Matrix([[1,0],
#                 [0,1]])
# 
#   l = lattice(gen,[100,100])
# 
#   print l.iwrap([-2,-2])
#   q,r = l.imod([10.5,10.5])
#   print q,r
# 
#   for i in range(5):
#     print "iter",i
#     print "indx",l.ikick([.5,.5]).as_index()
#     print "pos",l.ipos
#   l2 = l.sublattice()
#   print l2.ipos
# 
# #if __name__=="__main__":
# #     V = Matrix([[ 1., 1./2      ],
# #                 [ 0., sqrt(3)/2 ]])
# #     x = column_vector([0,2.5])
# #     U = ut_inv(V)
# #     print decode_parallelepiped(U,x)
# #     print decode_babai(U,x)
# #     print decode_rectangular(V,U,x)
# # 
# #     print "Decode nearest"
# #     x = column_vector([1.4,.8])    
# #     print decode_nearest(V,U,x)    
# #    
# #     G = Matrix([[ 1, 0 ],
# #                 [ 0, 1 ]])
# #     alpha = 1
# #     V_ = V*alpha
# #     print V_
# #     print ut_restricted_babai_approx_sublattice(G,V_)
# # 
# #     # Find near approximations and the associated error
# #     vals = nonzero_elements(V)
# #     vals = map(lambda x: 1./x,vals)
# #     print vals
# #     a = min(vals)
# # 
# #     for i in xrange(20):
# #         V_ = V*a
# #         A  = ut_restricted_babai_approx_sublattice(G,V_)
# #         print "scale ",a, "error",relative_error(V_,A),"det",A.determinant(),
# #         print "rat",float(A[1,1])/A[0,1]   
# # #        print "scaled matrix", V_
# #         print A,
# #         a = next_multiple(a,vals)
# # 
# # #    for i in get_best_approximations(G,V,1,20):
# # #        A = i[1]
# # #        print i[0],i[2],i[3], float(A[1,1])/A[0,1]
# # #        print i[1],
# # 
# #     print "--------------------------------"
# #     for i in get_approximations(G,V,1,20):
# #         A = i[1]
# #         print i[0],i[2],i[3], float(A[1,1])/A[0,1]
# #         print i[1],
# #     print "--------------------------------"
# #     



