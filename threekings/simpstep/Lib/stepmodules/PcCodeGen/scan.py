# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.3 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/stepmodules/PcCodeGen/scan.py,v $

from simp.stepmodules.PcThreaded.scan import *
import simp.stepmodules.PcThreaded.scan as scan

from simp import geom as _geom
import numarray as _na
import simp.stepmodules.Pc._scan as _scan

import PyInline
import code
import simp.cache

def get_scan_func(rule,verbose=1,distutils_args=[]):
    # Now create the function that will do the scan.
    ccode = code.get_scan_code(rule)
#    distutils_args=[]
#    if verbose<2: distutils_args.append("-q")
    m = PyInline.build(code=ccode,language="C",cacheroot=simp.cache.CACHEDIR,
                       verbose=verbose,distutils_args=distutils_args) 
    return m.scan

def get_scan_func_ctransition(rule,verbose=1,distutils_args=[]):
    """Get a C scan function with an embedded transition function"""
    # Now create the function that will do the scan.
    ccode = code.get_ctrans_scan_code(rule)
#    distutils_args=[]
#    if verbose<2: distutils_args.append("-q")
    m = PyInline.build(code=ccode,language="C",cacheroot=simp.cache.CACHEDIR,
                       verbose=verbose,distutils_args=distutils_args) # 
    return m.scan

class ScanDoer(scan.ScanDoer):

    def __init__(self,rule,verbose=1,ctransitionfun=0,nthread=1,
                 distutils_args=[]):    
        scan.ScanDoer.__init__(self,rule,verbose,nthread=nthread)
        self.ctransitionfun = ctransitionfun
        if self.ctransitionfun:
          self.scanfunc = get_scan_func_ctransition(rule,verbose,distutils_args)
        else:
          self.scanfunc = get_scan_func(rule,verbose,distutils_args)         

    def do_lut(self,input_info,output_info,lut,lutshift=2,flags=0):
        """Do the scan on a set of input and output arrays
        info : [base_ptr,inmask,outmask,shift_l,shift_r,strides,position]
          position : the current position of the sign
        """

        self.input_info = input_info
        self.output_info = output_info
        self.lut = lut

        print "do ",self.lut,flags,lutshift
	
        prog = self.get_scan_program()
        self.set_info(input_info,output_info,prog)
        if self.ctransitionfun:
            self.scanfunc(_scan.na_ptr(prog))            
        else:
            self.scanfunc(_scan.na_ptr(prog),_scan.na_ptr(self.lut))
        
#        _scan.lut_scan(self.Ninputs,self.Noutputs,
#                       prog,self.lut,lutshift,flags)
    
    def do_scan(self,data):
        """Do the scan on a set of input and output arrays
        """
        prog,input_info,output_info,lut,lutshift,flags = data
        self.set_info(input_info,output_info,prog)

        if self.ctransitionfun:
            self.scanfunc(_scan.na_ptr(prog))            
        else:
            self.scanfunc(_scan.na_ptr(prog),_scan.na_ptr(lut))
#        _scan.lut_scan(self.Ninputs,self.Noutputs,
#                          prog,lut,lutshift,flags)
    

