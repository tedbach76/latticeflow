SIMP/STEP---a Python Programming environment for cellular and lattice gas 
automata

See the following web pages and the Doc directory for SIMP user documentation.
  * http://pm.bu.edu
  * http://simpstep.sourceforge.net

Contents of the project

  Lib/  
    python code directory
    stepmodules/  Directory containing STEP implementations distributed wth SIMP
      reference.py -- simple reference implementation
      pc/ -- basic PC implementation. Optimized for speed
      pc_samearray.py -- version of pc that allocates signals on the same 
                         interleaved memory array
      pc_threaded.py -- version of pc that uses multiple threads.
      pc_dynamic/ dynamically generated code

    __init__.py -- file imported when one imports SIMP
    region.py -- defines lattice array objects and regions selected upon them
    step.py -- defines the STEP interface
    cache.py -- a shelve based persistent cache 
    helpers.py -- generic SIMP helper methods

    key_command.py -- retrieves keypresses from the command line
    pygame_console.py -- Define the console object---uses the PyGame interface
                      to SDL.

    renderers.py -- Defines the basic renderer objects
    rule_analysis.py -- Does AST analysis of rule transition functions
    
    import_locally.py -- Tools for doing special imports of modules and functions
               (useful for importing copies of the simp module.)

    simpinclude.py -- Generated file that contains the SIMP version.

  Src/ 
    C source code for the STEP modules.

  Misc/ 
    ast/ AST experiments
    Dist/  experimental distribution utilities automatically install deps
    gtk/ experimental version of the console using GTK

  DosUtils/
    Installation utilities for dos

  Doc/
    Documentation

   

  


The remainder of this file contains brief instructions for testing,installing 
and building SIMP.
================================================================
INSTALLING 

On windows, use the windows installer packages, on linux, either 
use the binary installers or RPMS.  Be sure to satisfy the dependencies.

1) Dependencies

   - python2.2 or above
     - numarray
     - numeric
     - pygame

   You should probably make the installations in the order listed. 
   Make sure that the Python packages match the python version that
   you have installed. 

2) Install SIMP

================================================================
TESTING
   After any installation, you should test simp by running 

      import simp.test
      simp.test.testall()

   at the Python command prompt or use the following command-line 
   one-liner

     python -c "import simp.test; simp.test.test()"

================================================================
BUILDING THE DOCUMENTATION

We have only built the documentation on a Linux system.

cd Doc/manual
make  (makes ps)
make html (make the web pages)

================================================================
BUILDING AND INSTALLING FROM SOURCE

SIMP uses the python distutils to manage compilation.  We give the
basic commands here, but you should consult the distutils
documentation for more options. In order to build SIMP, you must first
install all the dependencies listed above.

BUILD

    python setup.py build

BUILD AND INSTALL

    python setup.py install 

LOCAL INSTALLATIONS FOR TESTING (LINUX)

    python setup.py install --home=.
    export PYTHONPATH=${PYTHONPATH}:${PWD}/lib/python

CREATING INSTALLERS

    RPM

      python setup.py bdist_rpm

      (NOTE:

         You will get an error beginning with
  
           "AssertionError: unexpected number of RPM files found:"

         Don't worry, the RPM is fine. This error is due to the fact
         that newer versions of RPM now create a 'debuginfo' package,
         which the python distutils package (upon which setup.py
         depends) does not currently know how to handle.  Distutils
         expects only a single package.  Therefore, you must retrieve
         the rpm from "build/bdist.linux-i686/rpm/RPMS/i386/" or
         whatever directory is appropriate for your system.  )

    WINDOWS INSTALLER

      python setup.py bdist_wininst

    If there were no errors, the installers are left in a directory
    called dist/.

-------------------------------------------------------------------
SPECIAL INSTRUCTIONS FOR COMPILING ON WINDOWS WITH MINGW

MINGW requires one to go through some special setup steps---mainly
to obtain a verison of python23.dll which mingw can parse. One must
also use some special commands to do the compilation.

DEPENDENCIES
  - Mingw 
      I recommend the downloading full MinGw package from mingw.org, but
      you could just install the gcc compiler and dlltool
  - All the normal SIMP install dependencies

SETUP STEPS  
  These scripts are based on instructions from 
  http://sebsauvage.net/python/mingw.html  on how to build mingw
  based extensions. 
 
  1) Edit DosUtils/simpdefs.bat so that it contains the 
     correct python version and points to the location of the 
     python dll (ie. python23.dll)

  2) Create the DLL
     a) Open a dos window
     b) Change directory to simp/DosUtils
     c) Run the following batch scripts (just type their names)
          simpdefs               # sets paths etc to python variables, dlls
          mingw_py_setup         # creates a python23.dll that mingw can use

INSTALL FROM SOURCES

   python setup.py build --compiler=mingw32 install

CREATE A WINDOWS INSTALLER

   python setup.py build --compiler=mingw32 bdist_wininst 

================================================================
DEBUGGING 

  Below are some basic developer notes on testing and debugging 
  SIMP extensions.

  COMPILING A LOCAL INSTALLATION

    From the top-level simp directory run the following
  
      python setup.py install --home=${PWD}
      export PYTHONPATH=${PYTHONPATH}:${PWD}/lib/python

  TESTING

    To quickly test an example program run

      python Examples/life.py

    or to run the test suite use

     python -c "import simp.test; simp.test.test()"     

  DEBUGGING PYTHON EXTENSIONS
  
  
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66510
    
    The best way of finding core dumps with a Python extension is to
    compile the extension source with '-g', and then follow these 
    steps.  You may want to re-compile any other extensions 
    you use (like Numeric) with -g.
    
    % gdb /usr/bin/python2.1
    (gdb) br _PyImport_LoadDynamicModule 
    (gdb) cont   # repeat until your extension is loaded
    
    
    (gdb) finish # to load your extension
    (gdb) br wrap_myfunction  # the entry point in your code
    (gdb) disable 1   # don't want to break for more modules being loaded
    (gdb) continue
    
    
  PROFILING

    python /usr/lib/python2.2/profile.py na_step.py
    
    Profile the code
      cd lib/python
      python simp/na_step.py
    
    
  DEBUG with DDD
    # build with proper gcc flags ...
    python setup.py build --debug install --home=./
    
    # Put a print a statement in the code after the appropriate module has 
    # been loaded
    
      import simp._na_step as _na_step
      print "imported _na_step"
    
    # do the following 
    (gdb) exec-file /usr/bin/python
    (gdb) set args na_step.py
    (gdb) file _PyImport_LoadDynamicModule 
    (gdb) br _PyImport_LoadDynamicModule 
    
    # press cont until the print statement lets you know that your module
    # has been imported
    
    # disable the 'load' breakpoint
    
    (gdb) disable 1   # don't want to break for more modules being loaded
    
    # set a breakpoint at the place in the code where you would like to stop.
    
    (gdb) br ....

================================================================
Questions and answers
================================================================

How do I run PcCodeGen on a Windows system?

   PcCodeGen generates and compiles C code on-the-fly. As such it requires 
   that the system have a C compiler and that distutils---a Python facility
   for building Python extensions in C---know about it.  

   By default, most Linux/Unix systems already have gcc (the GNU C compiler) 
   installed and distutils will use it automatically.

   On most Windows systems, there is not a compiler installed by default, 
   so you'll have to install one yourself.  

   MSVC (The easy route)

     If you install the Microsoft Visual C compiler (freely available
     from Microsoft as part of their .net sdk) distutils will use it
     automatically. 

     You may have to make sure that the compiler executable appears in the 
     user's path. 

   GCC (The route for Unix Geeks in living in Windows)
    
     I like to install GCC (with Mingw) as part of the Cygwin package using 
     the handy installers from cygwin.org. 

     To use cygwin, you will need include the path to gcc in your user's path
     and tell distutils that it should use the mingw32 native windows libraries
     options by creating a file called pydistutils.cfg in your user 
     home directory containg the following lines (left justified):

        [build]
        compiler=mingw32

     If you did not use the cygwin installer (eg. you just installed mingw32), 
     you may also need to make sure that gcc appears in your path. You can 
     do this in Windows XP as follows

       Right-click My Computer, and then click Properties.
       Click the Advanced tab.
       Click Environment variables.
       Click one the following options, for either a user or a system variable:
       Click New to add a new variable name and value.
       Click an existing variable, and then click Edit to change its name 
          or value.
       Click an existing variable, and then click Delete to remove it.

   Other compilers (Who does this?)

      You may be able to use other compilers such as Borland.  To use them, 
      you will just need to make sure that distutils knows about them---you
      can find a list of supported compilers by running the following Python
      code 

         import distutils.ccompiler
         print distutils.ccompiler.show_compilers()

How do I run PcCodeGen on a Mac OS X system?

   Well, you've got me there!

In Windows, the SIMP console seems not to work---when it comes up, the
viewable area just has a copy of the screen that used to be under it.
What should I do?

   I have only seen this problem once.  I was able to fix it by
   changing the color mode from 32 to 16 bits.

   When it occured, it affected all pygame/SDL applications I tried to
   run on the system. (FYI: SIMP uses pygame---a python interface to
   the SDL, simple directmedia layer,---in order to provide the
   console's viewable screen.) After Googling, I have found similar
   reports on the web, but was not able to find a conclusive
   solution---a few mentioned that the system video driver was likely
   to blame.  Failing to find a better/newer driver for my Acer Aspire
   3610's Moble Intel 915/GMS,910GML Express Chipset Family video
   hardware, I tried changing the color mode and was happily rewarded
   with a working SIMP console.


Why is there a lag between pressing a command and getting a response?
  
   This is an artifact of threading. The console and STEP live in separate
   threads. 


   

   
