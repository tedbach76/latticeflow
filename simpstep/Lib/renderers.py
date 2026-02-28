# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.4 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/renderers.py,v $

"""
Defines the renderer objects.
"""

import simp.step as _step
import simp.geom as _geom
import types
import numarray as _na

class Renderer:
    """Standard 2D renderer---renders signals to colors.

    Given a rule, mapping signals to a set of output signals, the
    Renderer constructs the approproate STEP Read operations for
    reading out specified views.  In particular, the renderer provides
    an interface that the Console and scripts can easily use to
    control rendering.

    The renderer is a callable object that, when called, returns the
    rendered output signal values in a single array.  If there is
    more than one output signal, the values are packed into a single
    array with n+1 dimensions---the least significant is indexed by
    the ordering of the output signals. 

    The view is the portion of the state rendered.  The renderer has
    the following read only state attributes pertaining to the view
       center --- the center coordinate for the view
       shape --- the array shape of the view
       size --- the grid size of the view
       region --- the coordinate region of the view
       maxshape --- the largest shape that can be viewed

    One can set the center with setcenter(). The Console uses this for
    panning. One can set the array shape of the view with setshape().
    The actual center or shape may differ from the values
    specified. For example, if one sets a shape larger than maxshape,
    the shape is clamped to maxshape.  Therefore, one should always use
    the shape and center attributes to query the information after calling
    a set function.

    Together, the center and the shape specify the region.  The region
    is a rectangular grid region to be rendered.  One can set the
    region with setregion.  It accepts the standard region
    objets---Python subscript lists and simp.latticearray.Region
    objects. Changing the region automatically changes the center and
    shape.
    """
    # maxshape : maximum size that can be rendered
    # shape : current shape of the array
    def __init__(self,render_rule,outputs): # ,background=None
        """Declare a new renderer.

        keyword parameters
          render_rule --- a Rule object mapping signals to outputs
          outputs --- tuple or list of OutSignals rendered to.

        When the Renderer is declared, by center is initialized to
        the center of the space and the shape fills the space.
        
        """
        if not isinstance(render_rule,_step.Rule):
            raise ValueError, "Expected the render_rule to be a Rule object"
        if not (type(outputs)==types.ListType or \
                type(outputs)==types.TupleType):
            outputs = [outputs]
        self.outputs = outputs
        
        self.__simp__ = render_rule.__simp__
        self.__step__ = self.__simp__.__step__
        self.maxsize = self.__simp__.__size__
        self.__out_lat_arr__ = outputs[0]
        self.maxshape = self.__out_lat_arr__.shape
        self.render_rule = render_rule
        self.name = render_rule.name
        self.setregion(None)

#        self.background = background
#        if self.background!=None:
#            if not len(self.background)==len(outputs):
#                raise ValueError,\
#                    "Background must be the same size as the number of outputs"
        

    def setregion(self,region=None):
        """Sets the region to be rendered.

         The default is from 0 to maxsize.        

        The region is a rectangular grid region to be rendered.  One
        can set the region with setregion.  It accepts the standard
        region descriptor types---Python subscript lists and
        simp.latticearray.Region objects. Changing the region
        automatically changes the center and shape.
        """
        
        # XXX Must add checks for the size of the region and handling
        # for regions in dimensions higher than 2.  # (higher
        #                    dimensions should be 1)
        
        if region!=None:
            self.region = _step.LatticeArrayRegion(region,self.__out_lat_arr__)
        else:
            subscr = [slice(None)]*self.__out_lat_arr__.nd
            for i in xrange(0,self.__out_lat_arr__.nd-2):
                subscr[i]=0
            self.region = _step.LatticeArrayRegion(subscr,self.__out_lat_arr__)

        self.size = self.region.size
        self.shape = self.region.shape
        self.center = (self.region.stop+self.region.start)/2
        if len(self.outputs)==1:
          self.read = _step.Read(self.region,self.outputs,
                               self.render_rule,samearray=0)
        else:
          self.read = _step.Read(self.region,self.outputs,
                               self.render_rule,samearray=1)
      
    def setcenter(self,center=None):
        """Set the center grid coordinate vector for rendering.

        Returns the actual center position used. If center is not
        given, it automatically selects the center of the space.
        """
        
        # take center modulo size
        center = [center[i]%self.maxsize[i] for i in xrange(len(self.maxsize))]
        start = center-(self.size)/2
        stop = center+(self.size+1)/2
        self.setregion([start,stop])

    def setshape(self,shape=None):
        """Set the shape of the 2D array to be rendered.

        If None, the shape is set to the maximum shape. Initially, the
        shape is the maximum shape. Returns the actual shape used.
        """
        # XXX should be made to handle shapes that are
        # smaller than the number of dimensions
        if shape==None:
            shape = self.__out_lat_arr__.shape
        else:
            # extend the shape with ones in any missing dimensions. 
            shape = tuple([1]*(len(self.region.start)-len(shape)))+tuple(shape)

        newsize = shape*self.__out_lat_arr__.spacing
        start = self.center-(newsize)/2
        stop = self.center+(newsize+1)/2
        self.setregion([start,stop])

    def __call__(self,out=None):
        """Call the renderer and return the output array.

        parameters
          out --- array to be rendered to. If not specified, a new array
          is returned.

        Rendering is performed on the current view (as specified by
        the shape parameters). 

        The renderer is a callable object that, when called, returns
        the rendered output signal values in a single array.  If there
        is more than one output signal, the values are packed into a
        single array with n+1 dimensions---the least significant is
        indexed by the ordering of the output signals.
        """
        if out==None:
            # XXX should allow one to change the type
#            if self.background!=None:
#                out = _na.array(shape=self.shape,type=_na.UInt8)
#                out[:,:,...] = self.background
#                return self.read(out)
#            else:
            out_arr = self.read()
            if len(self.outputs)==1:
                out_arr = out_arr[0]
            return out_arr
        else:
#            if self.background!=None:
#                out[:,:,...] = self.background
            return self.read(out)

    def __str__(self):
        return "<Renderer name=%s>" % self.name


class XTRenderer:
    """The space-time renderer XTRenderer records and renders past history.

    
    It provides an n+1 dimensional space-time view. The record() method
    records the renderes and records the current state. Calling the
    renderer returns the history array.

    Beyond this, it implements the basic Renderer interface.

    Space-time renderer.
    """
     
    def __init__(self,render_rule,outputs,time=None): # background=None,
        """
        Except for the addition of the time, the initialization
        parameters are the same as those of an ordinary renderer.  Time
        gives the amount of history to be maintained.  (By
        default, it's the same as the size of the lowest dimension.)
        """
        # set up the basics
        if not (type(outputs)==types.ListType or \
                type(outputs)==types.TupleType):
            outputs = [outputs]
        self.outputs = outputs
        self.__simp__ = render_rule.__simp__
        self.__step__ = self.__simp__.__step__
        self.name = render_rule.name
        self.maxsize = self.__simp__.__size__
        self.__out_lat_arr__ = outputs[0]
        self.render_rule = render_rule
#        self.background = background
#        if self.background!=None:
#            if not len(self.background)==len(outputs):
#                raise ValueError, \
#                    "Background must be the same size as the number of outputs"
        
        self.direction = 0
        if time == None:
            time = self.__out_lat_arr__.shape[-1]
        if time<0:
            self.direction = 1
        self.time = abs(time)
        self.current_time = 0   # will be incremented mod self.time
        
        # allocate the output array
        self.maxshape = [self.time] + list(self.__out_lat_arr__.shape)
        if len(outputs)==1:
            self.__array_shape__=self.maxshape
        else:
            self.__array_shape__=self.maxshape+[len(outputs)]
        self.__array__ = _na.zeros(self.__array_shape__,type=_na.UInt8)
        # Set up the background if necessary
#        if self.background!=None:
#            self.__array__[:,:,...] = self.background
            
        # Set up the default rendering region
        subscr = [slice(None)]*self.__out_lat_arr__.nd
        self.region = _step.LatticeArrayRegion(subscr,self.__out_lat_arr__)
        self.size = self.region.size
        self.shape = [self.time]+list(self.region.shape)
        self.center = (self.region.stop+self.region.start)/2

        # read the entire space...
        if len(self.outputs)==1:
          self.read = _step.Read(self.region,self.outputs,
                               self.render_rule,samearray=0)
        else:
          self.read = _step.Read(self.region,self.outputs,
                               self.render_rule,samearray=1)

    def setregion(self,region=None):
        """Sets the region to be rendered. If none given, uses the default
        region. """
#        raise NotImplementedError, "Not implemented"                
            
      
    def setcenter(self,center=None):
        """Set the center position for rendering. Returns the actual
        center position used. If center is not given, it automatically selects
        the center of the space."""
        print "Warning: Panning is not currently implemented for the space-time renderer"
#        raise NotImplementedError, "Not implemented"        

    def setshape(self,shape):
        """Set the shape of the 2D array to be rendered. If None, the
        shape is set to the maximum shape. Initially, the shape is the
        maximum shape. Returns the actual shape used."""
        # should handle shapes that are smaller than the number of dimensions
        print "Warning: Can't currently change the shape of the XTRenderer"
#        raise NotImplementedError, "Not implemented"

    def __call__(self,array=None):
        if array==None:
              array = _na.zeros(self.__array_shape__,type=_na.UInt8)            
        array[0:self.time-self.current_time,...] = \
           self.__array__[self.current_time:self.time,...]
        array[self.time-self.current_time:self.time,...] = \
           self.__array__[0:self.current_time,...]
        return array

    def record(self):
        """Record the current state."""
#            if len(self.outputs)==1:
#                out_arr = out_arr[0]
            
        
        if self.direction==0:
            out_arr = self.__array__[self.current_time,...]
#            if self.background!=None:
#                out_arr[:,...] = self.background
            self.read(out_arr)            
            self.current_time = (self.current_time+1)%self.time
        else:
            self.current_time = (self.current_time-1)%self.time
            out_arr = self.__array__[self.current_time,...]
#            if self.background!=None:
#                out_arr[:,...] = self.background
            self.read(out_arr)

    def __str__(self):
        return "<XTRenderer name=%s>" % self.name

# Volume rendering ideas
# A simple volume rendering technique that doesn't use shading...
# http://www.starlink.rl.ac.uk/star/docs/sg8.htx/node14.html

#emulate 3D rendering similar to that of the CAM-8
#def 3drender(array):
#    out = numarray.out(list(array.shape[-3:-1])+[3])
#    light = numarray.zeros(array.shape[-3:-1])
#    light[:,:]=255
#    for z in xrange(array.shape[0]):
#        alpha = array[z,:,:,3]/255.
#        numarray.multiply
#        light[:,:] = light*alpha/255
#
#        light = light*array[z,:,:,3]
#        for i in xrange(3):
#             out[:,:,i]+=out[:,:,i]+
#    out = numarray.array(out.clip(array,0,255),type=numarray.UInt8)
#    return out

