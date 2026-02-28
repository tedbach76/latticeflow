# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.2 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/consolebase.py,v $

"""
This base class definitions for the console, including the terminal
key command console.

Issues:

  * pressing control c (Key interrupt) causes the code interpreter to freeze
    (stops accepting keys from the terminal)

"""


import threading, Queue, thread, types, time, traceback, inspect



# ================================================================
#                      HELPER FUNCTIONS
# ================================================================
import string
# ================================ Helper Functions
def MakeBlockString(lhsChars,lhs,str):
  """Print a block"""
  width = 80
  str = string.replace(str,"\n"," ")
  seg = string.ljust(lhs,lhsChars)
  result = ""
  while len(str):
    while str[0]==" ": 
      str = str[1:]
      if len(str)==0: break      
    if len(str)==0: break      
    i=width-len(seg)
    if i>=len(str): i=len(str)
    else:
      while i>0:
        if str[i-1]==" ": break
        i=i-1;
    if i==0: break
    result = result+seg+str[:i]+"\n"
    str = str[i:]
    seg = string.ljust("",lhsChars)
  return result

def printcommands(cmds):
  text = ""
  keys = cmds.keys()
  # partition into upper (user defined) and lower case and chars
  lowercase=[]; uppercase=[]; other = []
  for k in keys:
    if "a" <= k and "z" >= k: lowercase.append(k)
    elif "A" <= k and "Z" >= k: uppercase.append(k)
    else: other.append(k)
  text+="--- SYSTEM DEFINED COMMANDS ---\n"    
  text+=printcommands_keys(lowercase,cmds)
  text+=printcommands_keys(other,cmds)
  text+="--- USER DEFINED COMMANDS ---\n"
  text+=printcommands_keys(uppercase,cmds)
  return text
  
def printcommands_keys(keys,cmds):
  """Print out a command dictionary"""
  text = ""
  for k in keys:
    if type(k)!=types.StringType: continue  # skip other events
    if k=="RENDER" or k=="STEP": continue # skip these two
    label = ""
    keyname = k
    if cmds[k].keyname!=None: keyname = cmds[k].keyname
    label =  string.ljust(keyname,10) + string.ljust(cmds[k].name,20)
    if cmds[k].doc != None:
      str = cmds[k].doc
      loc = string.rfind(str,"\n*")			# Get doc after \n* 
      if loc>0:
        if loc+2<len(str): str=str[loc+2:]
        else: 	       str=""
      text+=MakeBlockString(30,label,str)
    else: 
      text+=label+"\n"
  return text

# ================================
import inspect
def top_level_globals():
  """Gets the globals from the top level module"""
  frames = inspect.getouterframes(inspect.currentframe())
  return frames[-1][0].f_globals


# ================================================================
#                      COMMAND WRAPPER CLASS
# ================================================================
class CommandWrapper:
   """Wrapper for command functions. Manages the setting and modification
   of arguments to the functions, their calling, and their invocation."""

   def __init__(s,cmd_func,name=None,doc=None,keyname=None):
     """cmd_func can be a single list or a list of functions"""

     # Handle the function type
     s.cmd_func       = cmd_func; 
     if type(cmd_func)==types.ListType:
        s.cmd_func = cmd_func[0]         
     if type(cmd_func)==types.FunctionType:
       # Obtain default arguments and argument names
       argc         = cmd_func.func_code.co_argcount
       s.arg_names  = cmd_func.func_code.co_varnames[0:argc]
     elif type(cmd_func)==types.MethodType:
       # Obtain default arguments and argument names for a method
       argc         = cmd_func.func_code.co_argcount
       # account for self arg              
       s.arg_names  = cmd_func.func_code.co_varnames[1:argc]
       argc -= 1 
       cmd_func = cmd_func.im_func
     else:
       raise AttributeError, "Expected a function or method"

     if cmd_func.func_defaults!=None:         
       s.argv = [None]*(argc-len(cmd_func.func_defaults)) + \
                                   list(cmd_func.func_defaults)
     else:
       s.argv     = [None]*argc

     # Obtain command name, doc, 
     if name==None:   s.name   = cmd_func.__name__
     else:            s.name   = name
     if doc==None:    s.doc        = cmd_func.__doc__
     else:            s.doc        = doc

     s.keyname = keyname

   def __call__(s,*args):

     if args!=(): s.update_args(args)

     if type(s.cmd_func)==types.ListType:
        for fun in s.cmd_func:            apply(s.cmd_func,s.argv)
     else:                            apply(s.cmd_func,s.argv)

   def update_args(s,args):
     # Update arguments to the function
     for i in range(0,min(len(args),len(s.argv))):
       s.argv[i] = args[i]


   def get_call_str(s):
     """Return the function call string for this command"""

     arg_str= "("
     for i in range(0,len(s.arg_names)):
       arg_str+=s.arg_names[i]+"="+`s.argv[i]`+","
     if len(s.arg_names)>0:                          # clip trailing comma
       arg_str=arg_str[0:-1]
     return s.name+arg_str+")"

   def __doc__(s):
     """Get the documentation string for this command"""
     if s.doc:
       return s.doc
     else:
       return "<no documentation>"



# ================================================================
#         CONSOLE BASE CLASS
# ================================================================


# base console event manager
class console_base:
   sleep_time = .01 # amount of time to sleep when waiting for commands.


   def __init__(s):
     s.__commands__ = {}
     s.event_queue  = Queue.Queue(3)  # accept a maximum of 3 pending events
     s.running      = 0              # flag specifying if CP is running
     s.running_cont = 0          # flag specifying if CP running cmd cont
     s.update       = None            # no update function
     s.updating     = 0               # flag to say whether we are currently
                                      # updating
     s.executing_command = 0            # true whenever a command is being run

     s.__eat_next__ = None            # a function that eats the next command...
     s.n_steps     = 1                # number of steps per update
     
     s.arg_sem      = threading.Semaphore()
     s.ARGUMENT     = ()             # current value of the command arg
     # Register basic builtin commands
     s.bind(" ",s.__step_command__,"STEP", keyname="<space>") 
     s.bind("q",s.Quit)
     s.bind("\n",s.__run__,"Run",keyname="<enter>")
     s.bind("h",s.DisplayHelp,"Help")
     s.done = 0
     s.step_counter = 0              # keeps track of the current step

   def set_arg(s,arg):
     s.arg_sem.acquire()
     s.ARGUMENT = arg
     s.arg_sem.release()

   def get_arg(s):
     return s.ARGUMENT

   def enqueue(s,event):
     """Public method for input data sources run as separate threads"""
# USE ^c to do this ...     
#     if event == 'i':                      # INTERRUPT COMMAND
#         if s.executing_command==1:
#           # interrupt the currently running command ...
#           # should add option to quit the current iteration...
#           s.Print("Interrupt()")
#           thread.interrupt_main()
#         else:
#           s.Print("Interrupt()")
#         return
     if event==' 'and (s.updating or s.running_cont): # STOP RUNNING COMMAND
         s.updating     = 0
         s.running_cont = 0         
         print " Stop() t=%i\n" % s.step_counter
         # interrupt the main thread---the one running the current command
         return

     try:
       s.event_queue.put(event,block=0)
     except Queue.Full:
       print "Queue is full, can't enqueue event", event

   def issue(s,event):
     s.enqueue(event)
     # run the event.
     s.pump()

   def start(s):
     """Start running the console"""
     s.running = 1     # the CP is currently running ...

     # -------------------------------- Begin running
     try:
       s.run()
     except Exception, e:
       if not traceback==None: # XXX: for unknown reasons traceback is often
         # none when there is an unhandled exception.
         traceback.print_exc()
       if s.running:
          s.running = 0
          s.destroy()
          raise e
     s.destroy()


   def run(s):
     """The main event dispatcher"""
     i = 0
     while s.running:
       s.__pump__(s.sleep_time)
     s.done = 1

   def pump(s,sleep_time=0):
     if not s.running:
       s.__pump__(sleep_time)
       
   def __pump__(s,sleep_time=0):
        # Handle all events in the queue.
        try:
          while 1:
            event = s.event_queue.get(block=0)
            s.__handle_event__(event)  # pass event to the event handler...
        except Queue.Empty: pass

        # If running, run commands....
        if s.running_cont:
            s.executing_command = 1
            try:
              s.__do_step__()
            except KeyboardInterrupt:
              s.executing_command = 0
              s.clear_queue()
            s.executing_command = 0
        else:
          if sleep_time: 
            time.sleep(sleep_time)
     
   def destroy(s):  s.running = 0

   def clear_queue(s):
     # empty the queue
     try:
         while 1: s.event_queue.get(block=0)
     except Queue.Empty:  pass
     s.running_cont = 0 # stop running

   def __handle_event__(s,event):
     if s.__eat_next__:
         s.__eat_next__(event); s.__eat_next__ = None
     else:
#         if s.getting_string:
#           if type(event)==types.StringType:
#             if next=="\n": s.getting_string=0                  # \n: DONE
#             elif next=="\b" or next=="\177":                   # \b: DELETE
#               s.result_str = s.result_str[:max(len(buffer)-1,0)]
#               print
#               print ">",s.result_str,;sys.stdout.flush()
#             else: 
#               if event in string.printable:
#                 sys.stdout.write(event)
#                 sys.stdout.flush()
#                 s.result_str+=event
#            return
#         elif s.getting_key:
#           if type(event)==types.StringType:
#             s.result_str = event
#             s.getting_key = 0
         if type(event)==types.StringType:
           # Handle numeric arguments (append to arg)
           if len(event)==1 and (event in "0123456789"):
             s.__number_argument__(event)
             return
           # Handle deletion
           if event=='\b' or event=='\177':  # markers for delete
             s.__argument_delete__()
             return
         # dispatch other types of events.
         try:
           cmd = s.__commands__[event]
           if isinstance(cmd,CommandWrapper):
             if cmd.argv==[]:
                print " "+cmd.name+"()",
             else:
               arg = s.ARGUMENT; s.ARGUMENT = ()
               if type(arg)!=types.ListType and type(arg)!=types.TupleType:
                 arg = (arg,)
               cmd.update_args(arg)
               if len(cmd.argv)==1:
                 print " "+cmd.name+"("+`cmd.argv[0]`+")",
               else:
                 print " "+cmd.name+`tuple(cmd.argv)`,
#             if cmd==s.__step_command__:
             print "t=%i" % s.step_counter
#             else:
#               print
           s.executing_command = 1               
           cmd()
           
           # render any effects if there is currently a renderer
           if s.__commands__.has_key("RENDER"): # render if renderer exists.
               render_cmd = s.__commands__["RENDER"]
               render_cmd()
           s.executing_command = 0
         except KeyError:
           s.executing_command = 0
           if event in string.printable: 
             print "Invalid command: '"+str(event)+"'\n"
           else:
             print "Invalid command"
         except KeyboardInterrupt:
           s.executing_command = 0
           s.clear_queue()
           print "Interrupted command"
         except Exception, e:
           print "Error encountered:"+str(e)
           traceback.print_exc()     
           print e
           s.executing_command = 0

   def bind(s,event,handler,name=None,keyname=None):
     """Register a new command with the KeyCommand"""

     # check to make sure that the handler is callable
     if not callable(handler):
       raise ValueError, "The event handler must be a callable object"
     
     if type(handler)==types.FunctionType or type(handler)==types.MethodType:
       command = CommandWrapper(handler,name,keyname=keyname)
     else:
       command = handler
     
     if type(event)==types.ListType or type(event)==types.TupleType:
       for k in key: s.bind(handler,k,event,name,keyname)
#     elif event==STEP:
#       s.step         = update_func
#       s.after_update = after_update_func
     else:
       s.__commands__[event] = command
     
     return command

   def binding(s,event):
       """Returns the current object bound to an event"""
       return s.__commands__[event]
     
   # ----------------------------------------------------------------
   def __number_argument__(s,num):
     """Use the number keys to enter an integer argument"""
     if not type(s.ARGUMENT)==types.IntType:
       s.ARGUMENT = int(num)
     else:
       s.ARGUMENT = s.ARGUMENT*10 + int(num)
     print "arg: "+`s.ARGUMENT`


   def __argument_delete__(s):
     """Delete a number from the current if it is a number, or the whole arg
     if not."""
     if type(s.ARGUMENT)==types.IntType:
       s.ARGUMENT = s.ARGUMENT/10
     else:
       s.ARGUMENT = ()
     print "arg: "+`s.ARGUMENT`              
     

   def __do_step__(s):
#     print "do update"
     if s.__commands__.has_key("STEP"):
       step_cmd = s.__commands__["STEP"]
       s.updating = 1
       for i in range(0,s.n_steps):
         if not s.updating: break
         s.step_counter+=1
         step_cmd()
         # Record if necessary
         if hasattr(s,"renderers"):
           for rend in s.renderers:
             if hasattr(rend,"record"):
               rend.record()
       s.updating = 0
       if s.__commands__.has_key("RENDER"): # render if renderer exists.
         render_cmd = s.__commands__["RENDER"]
         render_cmd()

   def __step_command__(s,n_steps=1):
     """Do an update consisting of n_"""
     s.n_steps = n_steps
     if (s.running_cont):
       s.running_cont = 0        # if was running, stop.
       print "stopping" 
       return
     else:
       s.__do_step__()    # do an update sequence

   def __run__(s):
     """When doing nothing else, update according to the update function"""
     s.running_cont = not s.running_cont
     if s.running_cont: print "running"
     else:              print "stopping"

#   def step(s):
#     step_cmd = s.__commands__["STEP"]
#     step_cmd()

   def render(s):
     print """Warning: the render() function is deprecated.
     Use issue("RENDER") instead"""
     render_cmd = s.__commands__["RENDER"]
     render_cmd()
     
   def Quit(s):
     """Quit the console"""
     s.running = 0
   # ----------------------------------------------------------------
   def DisplayHelp(s):
    "Display help on commands"
#    print "\nBuiltin commands:" 
    print "---------------- Command help Help ----------------\n",\
      string.ljust("key",10)+string.ljust("command",20)+"description","\n",\
      printcommands(s.__commands__)
    print


import sys,signal

class unix_terminal(threading.Thread):
  """Class for reading characters from the terminal"""
  input_poll_interval = .01 # sometimes this causes problems ...


  def __init__(s,keypress_handler):
    """The TerminalKeyReader calls keypress handler function on every keypress
    """
    s.keypress_sem = threading.Semaphore()
    s.running = 0
    s.keypress_handler = keypress_handler
    s.other_process_reading = 0
    threading.Thread.__init__(s)
    s.get_keys    = 0                       # flag to turn behavior on and off

  def start(s):
    s.running = 1
    s.__init_terminal__()
    
    # fix term properties when the process continues...
    def reinit_term(signal,frame): s.__init_terminal__()
    try: 
      signal.signal(signal.SIGCONT,reinit_term)
    except:  # signals must be set on the same thread
      pass # there is no SIGCONT on windows
      

    # start running
    threading.Thread.start(s)

  def stop(s):
#    s.keypress_sem.acquire()        
    s.running = 0
#    s.keypress_sem.release()            
#    signal.signal(signal.SIGCONT,signal.SIG_DFL)

  def run(s):
    """Get keys one after another"""
    try:    
      while s.running!=0:
        if s.get_keys:
          try:
            s.keypress_sem.acquire()
            key = sys.stdin.read(1)   # should convert this to a non-blocking rd
            key = s.__arrow_key_filter__(key)
            s.keypress_sem.release()          
          except IOError:
            s.keypress_sem.release()         
            time.sleep( s.input_poll_interval )
            continue
          s.keypress_handler( key )
        else:
          time.sleep( s.input_poll_interval )
    except Exception, e:
        print e
        s.__reset_terminal__()        

#    finally: pass
      # reset terminal and remove signal handler
#      s.__reset_terminal__()

  def GetKey(s):
    s.keypress_sem.acquire()
    key = s.__getkey__()
    s.keypress_sem.release()
    return key

  def __getkey__(s):
    key=None
    while key==None and s.running:
        try:
          key = sys.stdin.read(1)
        except IOError:
          time.sleep( s.input_poll_interval )
    return s.__arrow_key_filter__(key)

  def poll_key(s):
    key=None
    try:
       key = sys.stdin.read(1)
    except IOError:
       time.sleep( s.input_poll_interval )
    return key

  def __arrow_key_filter__(s,key):
    """Filter out the arrow keys"""
    if key=='\033':
      key = None 
      try:
        key = sys.stdin.read(1)
        if key=="[":
 	  key = sys.stdin.read(1)
# 	  if key[len(key)-1]   == 'A': key="\020"	# Up
# 	  elif key[len(key)-1] == 'B': key="\016"	# Down
# 	  elif key[len(key)-1] == 'D': key="\002"	# Left
# 	  elif key[len(key)-1] == 'C': key="\006"	# Right
 	  if key[len(key)-1]   == 'A': key="arrow up"	
 	  elif key[len(key)-1] == 'B': key="arrow down"	
 	  elif key[len(key)-1] == 'D': key="arrow left"	
 	  elif key[len(key)-1] == 'C': key="arrow right"
      except IOError:  key='\033'
    return key
 

  def GetLine(s,default=None, start="",completer=None):
     """Read a line from the user (terminated by enter).
     default  : the default value to use if nothing is entered
     start    : a starting string that the user may edit
     completer: a string completer"""
     buffer = start
     if default:       print "[%s]>" % default,
     else:             print ">",
     print buffer, ; sys.stdout.flush()
     next = None
     
     s.keypress_sem.acquire()
     try:
      while 1:
        next = s.__getkey__()
        if next=="\n": break                               # \n: DONE
        if next =="\t":  # tab completion
          if not completer: continue                       # \t: COMPLETE
          # use completer info here ...
          matches, common_extension = completer(buffer)
          if common:  buffer = buffer+common
          else:
            print
            matches.sort()
            for x in matches: print x
            # TODO: pretty print into columns
          print 
          print ">",buffer,;sys.stdout.flush()
        elif next=="\b" or next=="\177":                   # \b: DELETE
          buffer = buffer[:max(len(buffer)-1,0)]
          print
          print ">",buffer,;sys.stdout.flush()
        else: buffer=buffer+next
     except Exception, e:
      s.keypress_sem.release()
      if not traceback==None: # XXX: for unknown reasons traceback is often
        # none when there is an unhandled exception.
        traceback.print_exc()
      if s.running:
        raise e
     s.keypress_sem.release()              
     
     if default!=None and buffer=="": return default
     else:                            return buffer


  def __init_terminal__(s):
    """Set up the terminal IO properties for the terminal window"""
    try:
      import termios, fcntl  # newer versions
    except ImportError, e:
      import TERMIOS,FCNTL   # fall back on old names
      termios,fcntl = TERMIOS,FCNTL

    # flags from deprecated TERMIOS
    ICANON     = 2
    TCSANOW    = 0    
    # flags from deprecated FCNTL 
    F_GETFL    = 3
    F_SETFL    = 4
    O_NONBLOCK = 2048

    # if not QUIET_MODE:
    if 1:
      stdinfd = sys.stdin.fileno()        
      s._oldterm = termios.tcgetattr(stdinfd)
      s._oldflags = fcntl.fcntl(stdinfd,F_GETFL)
      newattr = termios.tcgetattr(stdinfd)
      newattr[3] = newattr[3] & ~ICANON 
      # & ~TERMIOS.ECHO
      # & TERMIOS.FLUSHO 
      termios.tcsetattr(stdinfd, TCSANOW, newattr)
      fcntl.fcntl(stdinfd,F_SETFL,s._oldflags|O_NONBLOCK)
    s.get_keys = 1

  def __reset_terminal__(s):
    """Set the terminal's IO properties back to normal"""
    s.get_keys    = 0  
    try:
      import termios, fcntl  # newer versions
    except ImportError, e:
      import TERMIOS,FCNTL   # fall back on old names
      termios,fcntl = TERMIOS,FCNTL

    # if not QUIET_MODE:
    if 1:
      stdinfd = sys.stdin.fileno()                
      # flags from deprecated TERMIOS    
      TCSAFLUSH = 2
      # flags from deprecated FCNTL
      F_SETFL    = 4    
      termios.tcsetattr(stdinfd, TCSAFLUSH, s._oldterm)
      fcntl.fcntl(stdinfd,F_SETFL,s._oldflags)

  def pause(s):
    s.__reset_terminal__()

  def restart(s):
    s.__init_terminal__()

class windows_terminal(threading.Thread):
  """Class for reading characters from the windows terminal"""
  input_poll_interval = .02
  def __init__(s,keypress_handler):
    global msvcrt
    import msvcrt

    s.keypress_sem = threading.Semaphore()
    s.running = 0
    s.keypress_handler = keypress_handler
    s.other_process_reading = 0
    threading.Thread.__init__(s)
    s.get_keys    = 0                       # flag to turn behavior on and off

  def start(s):
    s.running  = 1
    s.get_keys = 1    

    # start running
    threading.Thread.start(s)

  def stop(s):
    if s.running:
      s.running  = 0
      s.get_keys = 0
#      msvcrt.ungetch("x")   # push a dummy character back to unblock

  def run(s):
    """Get keys one after another"""
    while s.running:
      if s.get_keys:        
          if msvcrt.kbhit():
            key = msvcrt.getch()
            if s.get_keys:
              # filter key
              key = s.__key_filter__(key)
              if key==None: continue
              # forward it
              s.keypress_handler( key )
          else: time.sleep( s.input_poll_interval )
      else:
        time.sleep( s.input_poll_interval )

  def __key_filter__(s,key):
     """Filter to standard key names..."""
     if key=='\xe0':  # special keys
        next = msvcrt.getch()
 	if   next=="H":   key="\020"	# Up arrow (control P)
        elif next=="P":   key="\016"    # Down     (control N)
        elif next=="M":   key="\006"	# Right    (control F)
        elif next=="K":   key="\002"	# Left     (control B)
        else: return None
     elif key=='\r':
        key = '\n'
     return key

  def pause(s):
    s.get_keys = 0
#    msvcrt.ungetch("x")   # push a dummy character back to unblock
    
    
  def restart(s):
    s.get_keys = 1

#  def get_key_thread
#      s.keypress_sem.acquire()
#      s.pause()
#      key = msvcrt.getch()
#      s.restart()
#      s.keypress_sem.release()
#      return key

  def GetLine(s,default=None, start="",completer=None):
     s.keypress_sem.acquire()
     s.pause()
     str = ""
     while 1:
       newkey = msvcrt.getche()
       if newkey=='\r': break    # end of line
       elif newkey=="\x08": # backspace
          msvcrt.putch(" "); # erase the old char
          msvcrt.putch("\x08") # go back
          str = str[:-1]
       else:
          str+=newkey
     s.restart()
     s.keypress_sem.release()
     return str

  def poll_key():
    if msvcrt.kbhit():
      return msvcrt.getch()
    return None

# ================================================================
class terminal_console(console_base):
  """Terminal window version of the console"""
  def __init__(s):
    console_base.__init__(s)

    # Special commands
    s.bind("a",s.EnterArgument)
    s.bind("e",s.EditCommandArgs)
    s.bind("z",s.RunPythonInterpreter)

  def destroy(s):
    s.term_key_reader.stop()


  def EnterArgument(s):
    """Enter the command argument. The argument can be either a single
    python value, list of values or a tuple"""
    arg = s.term_key_reader.GetLine(start=`s.ARGUMENT`)

    try:
      arg = eval(arg)
    except SyntaxError, e:
      traceback.print_exc()  # TODO: find a way to convert this to a string...
      print "Invalid Argument...not entered"
      return
    s.ARGUMENT = arg
    print "arg:", s.ARGUMENT

  def EditCommandArgs(s):
     """Edit the arguments for a command."""
     print "\t enter command to edit"
     key = s.term_key_reader.GetKey()
     cmd = s.__commands__[key]

     # Get arguments
     if len(cmd.argv)==0:
       print cmd.name+" has no arguments"
       return
     elif len(cmd.argv)==1:
       print "Edit argument for "+cmd.name
       arg = s.term_key_reader.GetLine(start=`cmd.argv[0]`)
     else:
       print "Edit argument for "+cmd.name         
       arg = s.term_key_reader.GetLine(start=`tuple(cmd.argv)`)
     try:
       arg = eval(arg)
     except SyntaxError, e:
       traceback.print_exc()  # TODO: find a way to convert this to a string...
       print "Invalid Argument...not entered"
       return

     if not type(arg)==types.TupleType:  arg = (arg,)     
     cmd.update_args(arg)

     if len(cmd.argv)==1:
       print "Updated args: "+cmd.name+"("+`cmd.argv[0]`+")"
     else:
       print "Updated args: "+cmd.name+`tuple(cmd.argv)`

  def RunPythonInterpreter(s):
    "Enter the Python interactive interpreter"

    s.term_key_reader.pause()       
      
    import code
    _banner="""Entering Python interactive interpreter
    Use ^D (Control-D) to exit the interactive interpreter"""
    code.interact(banner=_banner,local=frames[-1][0].f_globals)

    s.clear_queue()  # Clear any events that may have entered the queue...
    s.term_key_reader.restart()

  def Quit(s):
    s.running = 0
    print "quitting..."
    s.term_key_reader.stop()
    # TODO, wait for the thread to exit
    while not s.done:
      time.sleep(s.sleep_time)    

  def start(s):
    try:
       import termios, fcntl  # newer versions
       s.term_key_reader = unix_terminal(s.enqueue)
       s.term_key_reader.start()
    except ImportError:
       s.term_key_reader = windows_terminal(s.enqueue)
       s.term_key_reader.start()
    s.running = 1               
    console_base.start(s)

  



# ----------------------------------------------------------------
# Test handle
if __name__=="__main__":

#    stop = 0
#    def print_key(key):
#        global stop
#        print `key`
#        print "key",key
#        if key=="q": stop = 1
# 
#    wt = windows_terminal(print_key)
# 
#    wt.start()
# 
#    while not stop:
#        time.sleep(.1)
#    wt.stop()

   console = terminal_console()
   i = 0
   def dummy_update():
     global i
     print i
     time.sleep(1)
     i += 1
   def after_update(): print "---"

   console.bind("STEP",dummy_update)
   console.bind("RENDER",after_update)   
   def tcr_getline():
      print `console.term_key_reader.GetLine()`
   console.bind('G',tcr_getline)

   console.start()


