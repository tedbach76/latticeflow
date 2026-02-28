# import_locally.py: for importing local copies of python modules
# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.1.1.1 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/import_locally.py,v $

"""
Author: Ted Bach (tbach@bu.edu)

A set functions for instantiating and using multiple instances of a module.


The Python facilities for importing modules operate globally.  In its
default behavior, a module can only be instantiated once.  Of course,
that module also only has one namespace.

This is a good common case---it is more efficient than loading a module
afresh multiple times and often it makes sense to have only a single module.

With these facilities, we offer tools for the special case where one would
like to have multiple instances of the same module.  In a sense, we are
treating the module like a special type of class definition.

We also introduce a variant of the 'from module import *' semantics in
which it is possible to import everything from a specific module object.
We also allow one to unload a module, capturing the semantics of the
non-existent exression 'from module unimport *'.  Together, these
functions allow the user to change the working context, bringing in
names from different modules and allowing them to be called without
bearing the burden of full qualification.   It allows the user
to work in a simpler shorthand.  It is very nice for scripts.

Warning:

  Similar to the case in a normal Python import statement, attributes,
  functions and methods are copied into the namespace. Although they
  have the same names, changing the value of a name in the namespace
  will not change it in the object (or module).

The import_all and unimport_all methods can also be called on objects.


We arrived at these conventions after working a similar construct
that allows one to import the methods and definitions of a class into
the global namespace.


The following doesn't work:
   new_mod  = import_copy("string")
   from new_mod import *
this is because 'from import' statement trys to find the string literal
'new_mod' in the dictionary sys.modules.  An alternative is to use
the import_all function.


"""

import sys,inspect
def import_copy(module_name):
    """Import a new copy of a module---don't add it to the global list of
    modules.
    """
    current_loaded = None
    if sys.modules.has_key(module_name):
       current_loaded = sys.modules[module_name]
       del sys.modules[module_name]
    try:
      glbls = inspect.stack()[1][0].f_globals
      locals = inspect.stack()[1][0].f_globals      
      new_module = __import__(module_name,glbls,locals,
                              module_name.split(".")[0:-1])
#      sys.modules[module_name]
    except Exception,e:
      if current_loaded!=None:
          sys.modules[module_name] = current_loaded
      raise e

    if current_loaded!=None:
      sys.modules[module_name] = current_loaded
    else:
      del sys.modules[module_name] 
  
    return new_module


def import_all(object,namespace=None,no_clobber=1):
    """Emulates the hypothetical statement 'from object import *

    arguments:
    object  --- the object to be loaded into the namespace
    no_clobber --- if True, raises a NameError if the name already exists
                     (True by default)
    namespace --- the dictionary to load names into
                           (locals() of the caller by default)
    """
    
    if namespace==None:
      namespace = inspect.stack()[1][0].f_locals # top dict from where called
    
    for name in dir(object):
        if name[0]!="_":
            namespace[name] = getattr(object,name)


def unimport_all(object,namespace=None):
    """ Emulates the hypothetical statement,'from object unimport *'

    Removes all of the public names of an object from the namespace.

    arguments:
    object --- Python object with names to be removed
    namespace --- the dictionary to load names into
                           (locals() of the caller by default)
    """
    
    if namespace==None:
      namespace = inspect.stack()[1][0].f_locals # top dict from where called

    for name in dir(object):
        if name[0]!="_":
          if namespace.has_key(name):
            if id(namespace[name])==id(getattr(object,name)):
                del namespace[name]
              
            
    
