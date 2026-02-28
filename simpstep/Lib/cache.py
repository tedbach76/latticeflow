# cache.py: Persistent shelve based cache.
# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.3 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/cache.py,v $

"""
Module that keeps a persistent cache on disk for SIMP.
"""

import os,shelve

__home__ = os.path.expanduser("~")
if __home__ == "~":
  print "no home directory"
  __home__ = "c:/"   # hack for older versions of windows.
  print "using",__home__

#CACHE = os.path.join(__home__,".simpcache")
CACHEDIR = os.path.join(__home__,".simpcache")
SHELFCACHE = os.path.join(CACHEDIR,"shelfcache.db")


import cPickle
import simp.simpinclude as simpinclude


#def removerecursive(top):
#  # Delete everything reachable from the directory named in 'top',
#  # assuming there are no symbolic links.
#  # CAUTION:  This is dangerous!  For example, if top == '/', it
#  # could delete all your disk files.
#  try:
#     import distutils.dir_util
#     distutils.dir_util.remove_tree(top)
#  except AttributeError: 
#      for root, dirs, files in os.path.walk(top):
#          for name in files:
#              os.remove(os.path.join(root, name))
#          for name in dirs:
#              os.rmdir(os.path.join(root, name))
#    

import distutils.dir_util
removerecursive = distutils.dir_util.remove_tree
mkpath = distutils.dir_util.mkpath

try:mkpath(CACHEDIR)
except distutils.errors.DistutilsFileError:
  os.remove(CACHEDIR)
  mkpath(CACHEDIR)
  


class cached_shelf:
    """A wrapper for the python shelf object that caches attributes that
    have been accessed in memory.
    """
    def __init__(self, fname):
        self.fname = fname
        try:      
          self.shelf = shelve.open(fname)  # open a regular old shelf
        except: # if at first you can't open, delete the file and try again.
          try:
	     os.remove(fname)            
             self.shelf = shelve.open(fname)  # open a regular old shelf
          except:
             raise IOError, "Unable to open cache file "+ fname+\
                "\nPerhaps it doesn't exist, or another program has it locked"
        self.cache = {}

#    def keys(self):
#        return self.shelf.keys()

#    def __len__(self):
#        return len(self.shelf)
    def rebuild_shelf(self):
       """Reloads the shelf cache if we get DB errors"""
       try: s.shelf.close()
       except: pass
       try: os.remove(self.fname)
       except Exception, e:
         raise Exception, "SIMP Cache error, unable remove SIMP cache.\n"+\
                          "Try removing %s manually." % self.fname
       self.shelf = shelve.open(self.fname)  # open a regular old shelf
       self["VERSION"] = VERSION

    def has_key(self, key):
        if self.cache.has_key(key): return 1
        try:
          if self.shelf.has_key(key):
            # put into cache now for safe keeping
            try: self.cache[key] = self.shelf[key]
            except cPickle.UnpicklingError, e:# these are intermittently raised
              self.cache[key] = self.shelf[key]
            return 1
        except: self.rebuild_shelf()
        return 0

    def get(self, key, default=None):
        try:  return self[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        try:
            value = self.cache[key]
        except KeyError:
            try:
              value = self.shelf[key]
              self.cache[key] = value
            except cPickle.UnpicklingError, e: # these are intermittently raised
              value = self.shelf[key]  # try again
              self.cache[key] = value              
#              del self.shelf[key]
#              raise
            except KeyError, e: raise e
            except:
              self.rebuild_shelf()
              raise KeyError, key
        return value

    def __setitem__(self, key, value):
        self.cache[key] = value
        try: self.shelf[key] = value
        except cPickle.PicklingError,e: raise e
        except:
          self.rebuild_shelf()
          self.shelf[key] = value
        

    def __delitem__(self, key):
        try: del self.shelf[key]
        except KeyError,e: raise e
        except:  self.rebuild_shelf()
        try:
            del self.cache[key]
        except KeyError:
            pass
    def __del__(s):
        s.close()

    def close(s):
        s.shelf.close()

def clear_cache():
    global cache
    cache.close()
    try:
      removerecursive(CACHEDIR)
      mkpath(CACHEDIR)      
      os.remove(SHELFCACHE)
    except OSError:
      print "Unable to remove the old simpcache file"
      print "Deleting all entries"
       # manually delete all keys
      cache  = cached_shelf(SHELFCACHE)
      for key in cache.shelf.keys():
         del cache.shelf[key]
      cache["VERSION"] = VERSION
      return
    cache  = cached_shelf(SHELFCACHE)

VERSION = simpinclude.version
DEBUG = 0

if os.path.isfile(SHELFCACHE): # if the file exists
  cache  = cached_shelf(SHELFCACHE)
  # Clear the cache if the version does not match.
  try:
    if cache["VERSION"]!=VERSION:
#     print "CLEARING CACHE!!!!!!!!!!!!!!!"
      clear_cache()
  except KeyError:
    clear_cache()
else:
    cache  = cached_shelf(SHELFCACHE)
    
cache["VERSION"] = VERSION


# Ensure that the cache actually gets closed (for some reason, DEL is not always
# called for the object!!!!
import atexit
atexit.register(cache.close)

  