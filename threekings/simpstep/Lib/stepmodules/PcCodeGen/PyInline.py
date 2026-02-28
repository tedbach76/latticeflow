"""PyInline

The main package for the Inline for Python distribution.

The PyInline module allows you to put source code from other
programming languages directly "inline" in a Python script or
module. The code is automatically compiled as needed, and then loaded
for immediate access from Python. PyInline is the Python equivalent of
Brian Ingerson's Inline module for Perl (http://inline.perl.org);
indeed, this README file plagerizes Brian's documentation almost
verbatim.

# PyInline C Module
# Copyright (c)2001 Ken Simpson. All Rights Reserved.

----------
# Repackaged and distributed within SIMP by Ted Bach 2005. 
# Notes:
#  * original license: artistic
#  * see http://pyinline.sourceforge.net for the original distribution
#       and documentation
# Modifications:
#   merged everything into a single file
#   removed option to compile for any language other than C
#   added 'cacheroot' build option to C.py for specifying the 
#   base path for the cache file
"""
# PyInline C Module
# Copyright (c)2001 Ken Simpson. All Rights Reserved.


# ================================================================

"""http://aspn.activestate.com/ASPN/docs/ActivePython/2.2/PyWin32/Recursive_directory_deletes_and_special_files.html
"""
def del_dir(path):
  """Try to recursively delete a directory. Do nothing if it doesn't work..."""
#        import win32con
#        import win32api
  import os

  try:
    for file in os.listdir(path):
        file_or_dir = os.path.join(path,file)
        if os.path.isdir(file_or_dir) and not os.path.islink(file_or_dir):
           #it's a directory reucursive call to function again
           del_dir(file_or_dir) 
        else:
          try: os.remove(file_or_dir) #it's a file, delete it
          except:
             pass #probably failed because it is not a normal file
  #    win32api.SetFileAttributes(file_or_dir, win32con.FILE_ATTRIBUTE_NORMAL)
  #    os.remove(file_or_dir) #it's a file, delete it
        try: os.rmdir(path) #delete the directory here
        except: pass
  except: pass

# ================================================================
# originally from __init__.py

__revision__ = "$Id: PyInline.py,v 1.3 2006/03/28 03:30:48 tedbach Exp $"
__version__ = "0.03"

import os, string, re

class BuildError(Exception):
    pass

def build(**args):
    """
    Build a chunk of code, returning an object which contains
    the code's methods and/or classes.
    """
    # Create a Builder object to build the chunk of code.
    b = Builder(**args)
    
    if args.get("rebuild")==1:
	import sys
        from distutils.util import get_platform
        # remove the contents of the build dir--thus forcing a rebuild
        plat_specifier = ".%s-%s" % (get_platform(), sys.version[0:3])
        build_platlib = os.path.join(b._buildDir,
                                     'build',
                                     'lib' + plat_specifier)
        del_dir(b._buildDir)
	if os.path.isdir(build_platlib):
          for path in os.listdir(build_platlib):
            if os.path.isfile(path):
              os.path.remove(path)
	
    # Build the code and return an object which contains whatever
    # resulted from the build.
    return b.build()

# ================================================================
# originally from C.py

from distutils.core import setup, Extension


def log(message):
    print message

class Builder:
    def __init__(self, **options):
        self._verifyOptions(options)
        self._options = options
        self._initDigest()
        self._initBuildNames()
        self._methods = []
        self.verbose = self._options.get('verbose')
        if self.verbose==None: self.verbose = 1

    def _verifyOptions(self, options):
        pass

    def _initDigest(self):
        import md5, os, sys
        digester = md5.new()
        digester.update(self._options.get('code'))
        self._digest = digester.hexdigest()

    def _initBuildNames(self):
        self._moduleName = "_PyInline_%s" % self._digest
        # Ted Bach: added a new root for the cache
        if self._options.has_key("cacheroot"):
            cacheroot = self._options["cacheroot"]
            self._buildDir = os.path.join(cacheroot,self._moduleName)
        else:
           self._buildDir = self._moduleName
        # end modifications        
        self._srcFileName = "%s.c" % self._moduleName
        self._moduleVersion = "1.0"
        self._homeDir = os.getcwd()

    def build(self):
        "Build a chunk of C source code."
        self._parse()

        try:
            return self._import()
        except ImportError:
            self._writeModule()
            self._compile()

            try:
                return self._import()
            except ImportError:
                raise BuildError("Build failed")

    def _import(self):
        "Import the new extension module into our client's namespace"
        from distutils.util import get_platform
        import sys, os
        
        # Add the module's lib directory to the Python path.
        plat_specifier = ".%s-%s" % (get_platform(), sys.version[0:3])
        build_platlib = os.path.join(self._buildDir,
                                     'build',
                                     'lib' + plat_specifier)
        sys.path.append(build_platlib)

        # Load the module.
        import imp
        fp, pathname, description = imp.find_module(self._moduleName)

        try:
            module = imp.load_module(self._moduleName, fp,
                                     pathname, description)
        finally:
            # Since we may exit via an exception, close fp explicitly.
            if fp:
                fp.close()

        if self._options.has_key('targetmodule'):
            # Load each of the module's methods into the caller's
            # global namespace.
            setattr(self._options.get('targetmodule'), self._moduleName, module)
            for method in self._methods:
                setattr(self._options.get('targetmodule'), method['name'],
                        getattr(module, method['name']))
                
        return module

    def _parse(self):
        code = preProcess(self._options.get('code'))

        defs = findFunctionDefs(code)
        for d in defs:
            d['params'] = self._parseParams(d['rawparams'])
            self._methods.append(d)

    _commaSpace = re.compile(",\s*")
    _space = re.compile("\s+")
    _spaceStars = re.compile("(?:\s*\*\s*)+")
    _void = re.compile("\s*void\s*")
    _blank = re.compile("\s+")

    def _parseParams(self, params):
        "Return a tuple of tuples describing a list of function params"
        import re, string
        rawparams = self._commaSpace.split(params)
        if self._void.match(params) or\
           self._blank.match(params) or\
           params == '':
            return []

        return [self._parseParam(p) for p in rawparams]

    def _parseParam(self, p):
        param = {}
        
        # Grab the parameter name and its type.
        m = c_pandm.match(p)
        if not m:
            raise BuildError("Error parsing parameter %s" % p)

        type = self._parseType(m.group(1))
        param['type'] = type['text']
        param['const'] = type['const']
        param['pointers'] = type['pointers']
        param['name'] = m.group(2)

        return param

    def _parseType(self, typeString):
        type = {}
        # Remove const from the type.
        if const.search(typeString):
            typeString = const.sub(" ", typeString)
            type['const'] = 1
        else:
            type['const'] = 0

        # Reformat asterisks in the type.
        type['pointers'] = typeString.count('*')
        type['text'] = trimWhite(star.sub("", typeString) +\
                                        ("*" * type['pointers']))

        return type
        
    def _makeBuildDirectory(self):
        try:
            os.mkdir(self._buildDir)
        except OSError, e:
            # Maybe the build directory already exists?
            log("Couldn't create build directory %s" % self._buildDir)

    def _writeModule(self):
        self._makeBuildDirectory()
        try:
            srcFile = open(os.path.join(self._buildDir, self._srcFileName),
                           "w")
        except IOError, e:
            raise BuildError("Couldn't open source file for writing: %s" % e)

        import time
        srcFile.write("// Generated by PyInline\n")
        srcFile.write("// At %s\n\n" %\
	 time.asctime(time.localtime(time.time())))
        srcFile.write('#include "Python.h"\n\n')

        # First, write out the user's code.
        srcFile.write("/* User Code */\n")
        srcFile.write(self._options.get('code'))
        srcFile.write("\n\n")

        # Then add in marshalling methods.
        for method in self._methods:
            srcFile.write("static PyObject *\n")
            method['hashname'] = "_%s_%s" % (self._digest, method['name'])
            srcFile.write("%s(PyObject *self, PyObject *args)\n" %\
                          method['hashname'])
            self._writeMethodBody(srcFile, method)

        # Finally, write out the method table.
        moduleMethods = "%s_Methods" % self._moduleName
        srcFile.write("static PyMethodDef %s[] = {\n  " %\
                      moduleMethods)
        table = string.join(map(lambda(x): '{"%s", %s, METH_VARARGS}' %\
                         (x['name'], x['hashname']), self._methods), ",\n  ")
        srcFile.write(table + ",\n  ")
        srcFile.write("{NULL, NULL}\n};\n\n")

        # And finally an initialization method...
        srcFile.write("""
DL_EXPORT(void) init%s(void) {
  Py_InitModule("%s", %s);
}
""" % (self._moduleName, self._moduleName, moduleMethods))

        srcFile.close()

    def _writeMethodBody(self, srcFile, method):
        srcFile.write("{\n")

        # Don't write a return value for void functions.
        srcFile.write("  /* Return value */\n")
        if method['return_type'] != 'void':
            srcFile.write("  %s %s;\n\n" % (method['return_type'], "_retval"))
            
        srcFile.write("  /* Function parameters */\n")
        for param in method['params']:
            srcFile.write("  %s %s;\n" % (param['type'], param['name']));
        srcFile.write("\n")

        # Now marshal the input parameters, if there are any.
        if method['params']:
            ptString = _buildPTString(method['params'])
            ptArgs = string.join(
                map(lambda(x): "&%s" % x['name'],
                    method['params']), ", ")
            srcFile.write('  if(!PyArg_ParseTuple(args, "%s", %s))\n' %\
                          (ptString, ptArgs))
            srcFile.write('    return NULL;\n');

        # And fill in the return value by calling the user's code
        # and then filling in the Python return object.
        retvalString = ""
        if method['return_type'] != 'void':
            retvalString = "_retval = "
            
        srcFile.write("  %s%s(%s);\n" %\
                      (retvalString,
                       method['name'],
                       string.join(map(lambda(x): '%s' % (x['name']),
                                method['params']),
                            ', ')))

        if method['return_type'] == 'void':
            srcFile.write("  /* void function. Return None.*/\n")
            srcFile.write("  Py_INCREF(Py_None);\n")
            srcFile.write("  return Py_None;\n")
        elif method['return_type'] == 'PyObject*':
            srcFile.write("  return _retval;\n")
        else:
            try:
                rt = self._parseType(method['return_type'])
                srcFile.write('  return Py_BuildValue("%s", _retval);\n' %\
                              ptStringMap[rt['text']])
            except KeyError:
                raise BuildError("Can't handle return type '%s' in function '%s'"%\
                                 (method['return_type'], method['name']))
        
        srcFile.write("}\n\n")

    def _compile(self):
        from distutils.core import setup, Extension
        os.chdir(self._buildDir)
        if self.verbose:
            print "Compiling ",os.path.join(self._buildDir,self._srcFileName)
        ext = Extension(self._moduleName,
                        [self._srcFileName],
                        library_dirs=self._options.get('library_dirs'),
                        libraries=self._options.get('libraries'),
                        define_macros=self._options.get('define_macros'),
                        undef_macros=self._options.get('undef_macros'))
        try:
            if self.verbose<2:
              script_args = ["-q","build"]+\
                       (self._options.get('distutils_args') or [])
            else:
              script_args = ["-q","build"]+\
                       (self._options.get('distutils_args') or [])
            setup(name = self._moduleName,
                  version = self._moduleVersion,
                  ext_modules = [ext],
                  script_args=script_args,
                  script_name="C.py",
                  package_dir=self._buildDir,
                  verbose=self.verbose)
        except SystemExit, e:
            raise BuildError(e)
            
        os.chdir(self._homeDir)

ptStringMap = {
    'unsigned': 'i',
    'unsigned int': 'i',
    'int': 'i',
    'long': 'l',
    'float': 'f',
    'double': 'd',
    'char': 'c',
    'short': 'h',
    'char*': 's',
    'PyObject*': 'O'}

def _buildPTString(params):
    ptString = ""
    for param in params:
        if ptStringMap.has_key(param['type']):
            ptString += ptStringMap[param['type']]
        else:
            raise BuildError("Cannot map argument type '%s' for argument '%s'" %\
                             (param['type'], param['name']))

    return ptString


        
# ================================================================
# originally from c_util.py
# Utility Functions and Classes for the PyInline.C module.
import re
c_directive = '\s*#.*'
c_cppcomment = '//.*'
c_simplecomment = '/\*[^*]*\*+([^/*][^*]*\*+)*/'
c_doublequote = r'(?:"(?:\\.|[^"\\])*")'
c_singlequote = r'(?:\'(?:\\.|[^\'\\])*\')'
c_comment = re.compile("(%s|%s)|(?:%s|%s|%s)" % (c_doublequote,
                                                 c_singlequote,
                                                 c_cppcomment,
                                                 c_simplecomment,
                                                 c_directive))

const = re.compile('\s*const\s*')
star = re.compile('\s*\*\s*')
_c_pandn = "((?:(?:[\w*]+)\s+)+\**)(\w+)"
c_pandm = re.compile(_c_pandn)
_c_function = _c_pandn + "\s*\(([^\)]*)\)"
c_function_def = re.compile("(?:%s|%s)|(%s)" % (c_doublequote,
                                                c_singlequote,
                                                _c_function + "\s*(?:\{|;)"))
c_function_decl = re.compile(_c_function + "\s*;")

trimwhite = re.compile("\s*(.*)\s*")

def preProcess(code):
    return c_comment.sub(lambda(match): match.group(1) or "", code)

def findFunctionDefs(code):
    functionDefs = []
    for match in c_function_def.findall(code):
        if match[0]:
            functionDefs.append({'return_type': trimWhite(match[1]),
                                 'name': trimWhite(match[2]),
                                 'rawparams': trimWhite(match[3])})
    return functionDefs


_wsLeft = re.compile("^\s*")
_wsRight = re.compile("\s*$")
def trimWhite(str):
    str = _wsLeft.sub("", str)
    str = _wsRight.sub("", str)
    return str
    
if __name__ == '__main__':
    x = """#include <stdio.h>
const char* foo = "long int x(int a) {";
long int barf(int a, char *b) {
  int x, y;
  int x[24];
}

long int *** fkfkfk(char * sdfkj, int a, char *b) {
  int x, y;
}

"""
    print findFunctionDefs(x)
                                    

