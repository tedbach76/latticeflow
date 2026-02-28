# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.5 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/pygame_console.py,v $

"""
Pygame based console

# issues:
  * string editing commands seem to need to be done through the interactive
    the terminal window rather than the viewer
  * the interpreter will only run in the interpreter.


The console has a number of parts. One is for capturing and executing
key commands.  Another is for managing the numarray.  Yet another is
for using a numarray interface to the blit routine of pygame.

"""


import Numeric
import numarray
import types

from consolebase import *
import thread,time

from simp import helpers

import inspect
#def top_level_globals():
#   """Gets the globals from the top level module"""
#   frames = inspect.getouterframes(inspect.currentframe())
#    # set up context of the simp script
##    __script_context__ = _inspect.stack()[1][0].f_globals
#   return frames[-1][0].f_globals



def numeric_as_numarray(arr): # ,type=numarray.UInt8
    """Returns a numeric array reference to the data in a numarray
    >>> a = Numeric.array([1,2,3])
    >>> b = numeric_as_numarray(a)
    >>> b[0]=5
    >>> a
    array([5, 2, 3])
    """
    return  numarray.NumArray(shape=arr.shape,
                               type=arr.typecode(),buffer=arr)


class Console(terminal_console):
    # canvas : the array that the renderer will render to
    #   canvas_shape : the shape of the output canvas
    #   
    # surfarr : the array that will be blitted to the screen
    #   surfarr_shape : the shape of the screen that will be drawn
    #   surfarrN : natural numarray surface
    #   surfarrBlit : the numarray that will be blitted to the screen
    # mag : the current magnification

    sleep_time = .1
    initialized = 0
    def __init__(self,renderers,shape=None,
                 center=None,mag=1,zoom=1,showgrid=1):
        global pgl,pygame
        from pygame import locals as pgl
        import pygame
        import pygame.display
        import pygame.image

        # get a reference to the context in which the console was created
        self.script_context = inspect.stack()[1][0].f_globals
        
        if Console.initialized:
            raise RuntimeError(
                """Due to the nature of pygame, there can be only one""" +\
                """instance of the pygame console""")
        pygame.init()
        Console.initialized = 1
        pygame.display.init()
        terminal_console.__init__(self)        
        self.pygame_get_events = 1     # should start out getting events.
        
        self.screensize = pygame.display.list_modes()[0]

        self.mag = mag
        self.zoom = zoom
        self.showgrid = showgrid

#       self.initialized = 0 # flag that shows whether SIMP has been initialized

        try: renderers = list(renderers)
        except: renderers = [renderers]
        self.renderers = renderers
        self.renderer = self.renderers[0]

        # XXX should perhaps make a way to clamp the maximum shape
        if shape==None: shape = numarray.array(self.renderer.shape)
        if center==None: center = numarray.array(self.renderer.center)
        self.canvas_shape, self.center = shape,center
        # this will initialize everything else

        # set up the SIMP icon
        img = pygame.display.set_icon(\
             pygame.image.fromstring(simp_icon_data,(16,16), "RGB"))
        
        # Needed to get around pygame/SDL thread deficiendies
        self.__needs_updating__ = 0
        self.__main_thread__ = threading.currentThread()
        
#        self.__setrenderer__(self.renderers[0])
        self.ToggleRenderer()
        
        # bind commands
        self.bind("i",self.ZoomIn)
        self.bind("o",self.ZoomOut)
        self.bind("=",self.Magnify)
        self.bind("-",self.Demagnify)
        self.bind("arrow up",self.PanUp)
        self.bind("arrow down",self.PanDown)        
        self.bind("arrow left",self.PanLeft)
        self.bind("arrow right",self.PanRight)        
        self.bind("f",self.PanForward)
        self.bind("b",self.PanBackward)
        self.bind("c",self.CaptureView)        
        self.bind("g",self.ToggleGridLines)
        self.bind("t",self.ToggleRenderer)


    def setcenter(self,center):
        self.renderer.setcenter(center)
        self.center = numarray.array(self.renderer.center)

    def __update_screen__(self):
        if not self.__main_thread__ == threading.currentThread():
            self.__needs_updating__=1 # to get around bad pygame/SDL threading
            while self.__needs_updating__==1:
               time.sleep(.01)
            return
        screen_shape = list(self.canvas_shape[-2:]*self.mag)
        screen_shape.reverse()
        self.screen = pygame.display.set_mode(screen_shape)
        self.__render__()
        
        
    def __setshape__(self,shape):
        self.renderer.setshape(shape)
        self.canvas_shape = numarray.array(self.renderer.shape)[-2:]
 #        time.sleep(.1)  # hack to give the viewer time
        # Allocate the output array
        self.surfarr_shape = self.canvas_shape*self.mag
        self.surfarrN = Numeric.zeros(list(self.surfarr_shape)+[3])
        self.surfarr = numeric_as_numarray(self.surfarrN)
        # Obtain a transposed copy for use by pygame (proper X/Y format)
        self.surfarrBlitN = Numeric.transpose(self.surfarrN,
                                                       axes=(1,0,2))
        if self.mag==1: # use the same array for canvas and surfarr
            self.canvas = self.surfarr
        else: # allocate a separate array for the canvas
            self.canvas = numarray.zeros(list(self.canvas_shape)+[3])
        self.__update_screen__()

    def setshape(self,shape):
        self.__setshape__(shape)

    def setmag(self,mag):
        """Set the magnification to be used for rendering."""
        mag = int(mag)
        if mag<=0:
            raise ValueError, "Magnification must be positive"
        # do nothing if the magnification has not changed...
        if mag==self.mag: return
        self.mag = mag
        # adjust the size of the surfarr_shape
        self.surfarr_shape = self.canvas_shape*self.mag

        # Allocate the surfarr, and adjust the canvas if necessary...
        self.surfarrN = Numeric.zeros(list(self.surfarr_shape)+[3])
        self.surfarr = numeric_as_numarray(self.surfarrN)
        # Obtain a transposed copy for use by pygame (proper X/Y format)
        self.surfarrBlitN = Numeric.transpose(self.surfarrN,axes=(1,0,2))
        
        if self.mag==1: # use the same array for canvas and surfarr
            canv = self.canvas
            self.surfarr[...] = self.canvas
            self.canvas = self.surfarr
        self.__update_screen__()
        
    def setrenderer(self,renderers):
        """Set the renderer or renderers to be used. If a list of renderers
        is given, then one may toggle the renderer."""
        # ensure that the renderers are a list
        try: renderers = list(renderers)
        except: renderers = [renderers]
        self.renderers = renderers
        self.__setrenderer__(self.renderers[0])

    def __setrenderer__(self,renderer):
        self.renderer = renderer
        self.setcenter(self.center)
        self.__commands__["RENDER"]=self.__render__
        self.__setshape__(self.canvas_shape)

    def __render__(self):
        """Do the rendering operation and update the output array"""
        if len(self.renderer.outputs)==3: # plain rgb
            self.renderer(self.canvas)
        elif len(self.renderer.outputs)==1: # propagate bw
            self.renderer(self.canvas[:,:,0])
            self.canvas[:,:,1] = self.canvas[:,:,0]
            self.canvas[:,:,2] = self.canvas[:,:,0]     
            
        if self.mag!=1:
            if self.showgrid and (self.mag>4): gridwidth=1
            else: gridwidth = 0
            helpers.magnify2d(self.canvas,self.mag,gridwidth,self.surfarr)
        self.__show__()

    def __show__(self):
        """Show the current array contents"""
        pygame.surfarray.blit_array(self.screen,self.surfarrBlitN)
        pygame.event.pump()                 
        pygame.display.update()
        pygame.event.pump()

    def array(self):
       return numarray.array(self.surfarr)

    # --------------------------------------------
    def unbind(self,event):
        try: del self.__commands__[event]
        except KeyError: pass
        
#    def bind(self,event,handler,name=None,keyname=None):
#       if event=="RENDER":
#         if isinstance(types.TupleType) or isinstance(types.ListType):
#             self.renderers = list(handler)
#             s.__set_renderer__(handler)
#             self.bind("t",self.ToggleRenderer)
#         else:
#             self.renderer = renderer
#             s.__set_renderer__(handler) 
#             self.unbind("t")
#       panel_base.bind(self,event,handler,name,keyname)

    def do(self,event):
        self.enqueue(event)
        
    # --------------------------------------------
#    def __set_renderer__(self,renderer):
#        if self.renderer==None:
#            # set the initial size
#            self.renderer = renderer
#            self.region =  self.renderer.get_region()
#        else:
#            self.renderer = renderer            
#            self.renderer.set_region(self.region)
#            self.region = self.renderer.get_region()
#        self.__commands__["RENDER"] = self.render        

    def start(self):
#     s.running = 1
#      thread.start_new_thread(self.pygame_event_handler,())
#      s.pygame_getkeys = 1              
#      terminal_control_panel.start(self)

      # start the control panel in a separate thread (rather than pygame)...
      # otherwise windows really complains...

#      if hasattr(self,"renderers"):
#        for rend in self.renderers:
#          if hasattr(rend,"record"):
#            rend.record()
      
      self.running = 1
      self.__render__()
      thread.start_new_thread(terminal_console.start,(self,))
      self.pygame_getkeys = 1              
      self.pygame_event_handler()

      # render to get things started ...
#      self.enqueue(RENDER)

    def pygame_pause(self):
      self.pygame_get_events = 0

    def pygame_restart(self):
      pygame.event.clear()   # clear all pending events
      self.pygame_get_events = 1

    def pygame_event_handler(self):
      while self.running:
         # GET THE EVENT 
         e = pgl.NOEVENT
#	 pygame.event.pump()  # may not be necessary...
         if self.pygame_get_events:
           e = pygame.event.poll()
#           e = pygame.event.wait()
           # HANDLE IT
           if e.type == pgl.KEYDOWN:
              key = self.__key_event_filter__(e)
              if key!=None:
                self.enqueue(key)
                time.sleep(self.sleep_time)
  #         elif e.type == pgl.MOUSEBUTTONDOWN:
  #           break
           elif e.type == pgl.QUIT:
             raise SystemExit
           else:
             time.sleep(self.sleep_time)
         else:
           time.sleep(self.sleep_time)
         if self.__needs_updating__==1: # to get around bad pygame/SDL threading
             self.__update_screen__()
             self.__needs_updating__ = 0

    def __key_event_filter__(self,event):
       """Turn a key event into a character"""
       char = str(event.unicode)
       if        char=='\r':           char="\n"
#       elif event.key==pygame.K_UP:    char="\020"	# Up arrow (control P)
#       elif event.key==pygame.K_DOWN:  char="\016"	# Down     (control N) 
#       elif event.key==pygame.K_RIGHT: char="\006"	# Right    (control F)
#       elif event.key==pygame.K_LEFT:  char="\002"	# Left     (control B)

       elif event.key==pygame.K_UP:    char="arrow up"	# Up arrow (control P)
       elif event.key==pygame.K_DOWN:  char="arrow down"# Down     (control N) 
       elif event.key==pygame.K_RIGHT: char="arrow left"# Right    (control F)
       elif event.key==pygame.K_LEFT:  char="arrow right"# Left     (control B)
       
       if char=="": return None
       return char

    def pygame_poll_key(self):
      """returns none if no key was found"""
      e = pygame.event.poll()
      key = None
      if e == pgl.KEYDOWN:
          print "key found"          
          key = self.__key_event_filter__(e)
      return key
      
    def poll_key(self):
      key = self.pygame_poll_key()
      if key!=None: return key
      key = self.term_key_reader.poll_key()
      return key
       
    def get_key(self):
      """Get a single keypress"""
      self.pygame_pause()
      self.term_key_reader.pause()
      key = None
      while key==None:
          key = self.poll_key()
          if key!=None: continue
          time.sleep(self.sleep_time)
          
      self.pygame_restart()
      self.term_key_reader.restart()       
      return key

    def get_line(self,default=None, start="",completer=None):
      """Get a single keypress"""
      buffer = start      
      if default:       print "[%s]>" % default,
      else:             print ">",
      print buffer, ; sys.stdout.flush()
      
      self.pygame_pause()
      self.term_key_reader.pause()
      
      line = ""
      buffer = ""
      while 1:
          key = self.poll_key()
          if key==None: 
              time.sleep(self.sleep_time)
              continue
          if   key=="\n": break
          elif key=="\b" or key=="\177":
              buffer = buffer[:max(len(buffer)-1,0)]
              print
              print ">",buffer,;sys.stdout.flush()
          else: buffer=buffer+key

      self.pygame_restart()
      self.term_key_reader.restart()       
      if default!=None and buffer=="": return default
      else:                            return buffer

    def close(self):
      pygame.display.quit()
      Console.initialized = 0      

    def __del__(self):
      self.close()

    # -------------------------------- COMMANDS

    def EnterArgument(self):
      """Enter the command argument. The argument can be either a single
      python value, list of values or a tuple"""
      arg = self.get_line(start=`self.ARGUMENT`)
      try:
        arg = eval(arg)
      except SyntaxError, e:
        traceback.print_exc()  # TODO: find a way to convert this to a string...
        print "Invalid Argument...not entered"
        return
      self.ARGUMENT = arg
      print "arg:", self.ARGUMENT
  
    def EditCommandArgs(self):
       """Edit the arguments for a command."""
       print "\t enter command to edit"
       key = self.get_key()
       cmd = self.__commands__[key]
  
       # Get arguments
       if len(cmd.argv)==0:
         print cmd.name+" has no arguments"
         return
       elif len(cmd.argv)==1:
         print "Edit argument for "+cmd.name
         arg = self.get_line(start=`cmd.argv[0]`)
       else:
         print "Edit argument for "+cmd.name         
         arg = self.get_line(start=`tuple(cmd.argv)`)
       try:
         arg = eval(arg)
       except SyntaxError, e:
         traceback.print_exc() # TODO: find a way to convert this to a string...
         print "Invalid Argument...not entered"
         return
  
       if not type(arg)==types.TupleType:  arg = (arg,)     
       cmd.update_args(arg)
  
       if len(cmd.argv)==1:
         print "Updated args: "+cmd.name+"("+`cmd.argv[0]`+")"
       else:
         print "Updated args: "+cmd.name+`tuple(cmd.argv)`
    def RunPythonInterpreter(self):
      "Enter the Python interactive interpreter"
  
      self.term_key_reader.pause()
      self.pygame_pause()
        
      import code
      _banner="""Entering Python interactive interpreter
      Use <Control-D> to exit on UNIX or <Control-Z><Enter> to exit on Windows.
      Use the terminal window to enter text (the viewer will not respond).
      """
#      frames = inspect.getouterframes(inspect.currentframe())
#      print "----", type(frames[-1][0].f_globals),frames[-1][0].f_globals
      
      code.interact(banner=_banner,local=self.script_context)

      self.clear_queue()  # Clear any events that may have entered the queue...
      self.term_key_reader.restart()
      self.pygame_restart()
    
    def ToggleRenderer(self):
        new_renderer = self.renderers[0]
        self.renderers = self.renderers[1:]+[new_renderer]
        self.__setrenderer__(new_renderer)
        print "Switching to renderer %s" % self.renderer

    def Magnify(self):
        """Increase the current magnification"""
        mag=self.mag*2
        newshape = self.canvas_shape*mag
        for i in xrange(len(newshape)):
            x = newshape[i]
            if x==0 or x>self.screensize[i]*2:
                print "Can't magnify farther."
                return
        self.setmag(mag)        

    def Demagnify(self):
        """Increase the current magnification"""
        if (self.mag/2)==0:
           print "Can't demagnify farther"
           return        
        mag=self.mag/2
        self.setmag(mag)

    def ZoomIn(self):
        """Zoom the view in"""
        self.mag = self.mag*2
        self.zoom=self.zoom*2
        newshape = self.renderer.maxshape/self.zoom
        newshape=newshape[-2:] # ignore higher dimensions

        for x in newshape:
            if x==0 or x>2*10**6:
                self.mag/=2 # undo what was done
                self.zoom/=2 # undo what was done
                print "Can't zoom in farther."
                return
        self.setshape(newshape)

    def array(self):
       """Return a copy the current RGB array being shown by the Console."""
       return numarray.array(self.surfarr,type=numarray.UInt8)

    def ZoomOut(self):
        """Zoom the view out"""
        if (self.mag/2==0) or (self.zoom/2==0): return
        self.mag=max(1,self.mag/2)
        self.zoom=max(1,self.zoom/2)
        newshape = self.renderer.maxshape/self.zoom
        newshape=newshape[-2:] # ignore higher dimensions
        print "newshape",newshape        
        self.setshape(newshape)        

    def PanRight(self):
        """Pan view to the right"""
        sz = self.renderer.size
        self.center[-1]-=max(1,sz[-1]/16)
        self.setcenter(self.center)        
        self.__render__()

    def PanLeft(self):        
        """Pan view to the left"""
        sz = self.renderer.size
        self.center[-1]+=max(1,sz[-1]/16)
        self.setcenter(self.center)
        self.__render__()
        
    def PanUp(self):
        """Pan view up"""
        sz = self.renderer.size
        self.center[-2]-=max(1,sz[-2]/16)
        self.setcenter(self.center)        
        self.__render__()
        
    def PanDown(self):
        """Pan view down"""
        sz = self.renderer.size
        self.center[-2]+=max(1,sz[-2]/16)
        self.setcenter(self.center)                
        self.__render__()
        
    def PanForward(self):
        """Pan the view forward (only valid in 3D)"""
        sz = self.renderer.size
        try:
            self.center[-3]-=max(1,sz[-3]/16)
        except IndexError:
            print "Can only pan forward in 3D"
            return
        self.setcenter(self.center)        
	print self.center
        self.__render__()
        
    def PanBackward(self):
        """Pan the view backward (only valid in 3D slices)"""
        sz = self.renderer.size
        try:
            self.center[-3]+=max(1,sz[-3]/16)
        except IndexError:
            print "Can only pan backward in 3D"
            return
        self.setcenter(self.center)                
        self.__render__()

    def ToggleGridLines(self):
       """Show gridlines if possible"""
       self.showgrid=not self.showgrid
       self.__render__()

    def ToggleGridLines(self):
       """Show gridlines if possible"""
       self.showgrid=not self.showgrid
       self.__render__()

    def CaptureView(self):
       """Capture the current view as '<step_num>'.ppm"""
       arr = self.array()
       outfile = "%i.ppm" % self.step_counter
       print "Writing to ",outfile
       open(outfile,"wb").write(helpers.arraytopnm(arr))

def _test():
    import simp.pygame_console
    ui = simp.pygame_console.console()
    arr = Numeric.zeros((200,200,3))
    arr[2:30,10:50,:] = 255
    ui.set_array(arr)
    ui.show()
    ui.start()
    


simp_icon_data ='\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\x00\x00\x00\x00\x00\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\x00\xf0\x00\x00\x00\x00\x00\x00\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\xee\xee\xee\x00\x00\x00\x00\x00\x00\x00\x00\x00\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\x00\xf0\x00\x00\x00\x00\x00\x00\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\xee\xee\xee\xee\xee\xee\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

