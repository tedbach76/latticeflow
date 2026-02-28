# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.1.1.1 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/stepmodules/PcThreaded/scan.py,v $

from simp.stepmodules.Pc.scan import *
import simp.stepmodules.Pc.scan as scan

from simp import geom as _geom
import numarray as _na
import simp.stepmodules.Pc._scan as _scan


def compute_interrupts(signals,positions,strides,base_registers,
                       ptr_registers,rule,npartition=1):
    """Returns an interrupt program for a rule..."""
    rect = _geom.rectangular_cell_size(rule.generator)/rule.spacing
#    print "HERE=-------------------------"
    row_scan = compute_coset_scan(signals,positions,strides,ptr_registers,rule)
#    print row_scan
    nd = rule.nd
    indx = _na.zeros(len(rect))
#    for sig in signals:
#        sig_strides[i] = strides[i]*(rule.spacing/sig.spacing)
    adjusted_coord = _na.zeros(nd)

    # partition the scan into several sets of interrupt programs using
    # the most significant dimension.
    partitions = []
    msd = rule.shape[0] # most significant dimension size
    if npartition > msd:
        print "Warning: Unable to partition among %i threads, "+\
              "using %i instead" % (nthread,msd)
        npartition = msd

    if nd==1 and npartition>1:
        # don't make partitions
        print "Warning: Must have two or more dimensions for a partitioning"
    elif npartition>1:
        for i in xrange(1,npartition):
          partitions.append(i*(msd/npartition))

    scan_progs = []
    scan_prog = []        
    while 1:
        # compute the current pointer offsets for the row
        coord = rule.__coordinate__(indx)
#        print coord,
        for i in xrange(len(signals)):
            sig = signals[i]
            for j in xrange(nd): adjusted_coord[j]=positions[i][j]+coord[j]
#            adjusted_coord = coord+positions[i] # very slow!!!
#            _na.add(positions[i],coord,adjusted_coord) # very slow!!!
#            offset=1
            arr_indx = sig.__array_index__(adjusted_coord)
#            print  arr_indx
            stride = strides[i]; offset = 0
            for j in xrange(nd-1):
                offset+=stride[j]*(arr_indx[j]%sig.shape[j])
            scan_prog.extend([OP_ADDI,ptr_registers[i],
                              base_registers[i],offset])
        # scan the row
        coset_indx = [indx[i]%rect[i] for i in xrange(len(rect))]
#        print "coset indx",coset_indx,
        coset = _geom.arr_as_int(coset_indx,rect)
#        print coset,rect
        scan_prog.extend(row_scan[coset])

        if nd==1: break # done with the scan...
        _geom.multidimensional_inc(indx,rule.shape,1,-2)
        allzero = 1
        for i in xrange(len(indx)):
            if not indx[i]==0:
                allzero=0
                break
        if allzero: break
        if partitions!=[]:
            if partitions[0]==indx[0]: # gather the partition
                partitions = partitions[1:]
                scan_progs.append(scan_prog)
                scan_prog = [] # start a new program
    scan_progs.append(scan_prog) # get the last program partition
    return scan_progs


class ScanDoer(scan.ScanDoer):
    def __init__(self,rule,verbose=1,nthread=2):
        self.nthread = nthread
        scan.ScanDoer.__init__(self,rule,verbose)

    def get_scan_program(self,input_info,output_info):
        # Get the strides and positions
        strides = [0]*(self.Ninputs+self.Noutputs)
        positions = [0]*(self.Ninputs+self.Noutputs)
        for i in xrange(self.Ninputs):
            info = input_info[i]
            strides[i] = info[5]; positions[i] = info[6]
        if self.Ninputs==0: i=0
        else:         i+=1            
        for j in xrange(self.Noutputs):
            info = output_info[j]
            strides[i] = info[5]; positions[i] = info[6]
            i+=1
        hash = self.base_hash+ "positions"+`positions`+"strides" +`strides`+ \
                "nthread" + `self.nthread`

        # Try to get the program from cache
        try: return self.cache[hash]
        except KeyError,e: pass

        if self.verbose:
            print """COMPILING THE SCAN ..........................."""

        # Compile the scan from scratch
        self.strides, self.positions = strides,positions
        progs = compute_interrupts(self.base_signals,
                           positions,strides,
                           self.in_base_reg+self.out_base_reg,
                           self.in_ptr_reg+self.out_ptr_reg,
                           self.rule,self.nthread)
        init = self.scan_program_initialization()
        for i in xrange(len(progs)): # set up all of the scan programs...
            prog = progs[i]
            prog = init+prog+[OP_RETURN]
            prog = _na.array(prog)
            progs[i] = prog
        # Cache it
        self.cache[hash]=progs
        # Return it
        return progs


    def do_lut(self,input_info,output_info,lut,lutshift=2,flags=0):
        """Do the scan on a set of input and output arrays
        info : [base_ptr,inmask,outmask,shift_l,shift_r,strides,position]
          position : the current position of the sign
        """
        progs = self.get_scan_program(input_info,output_info)
        # should really do this using the pool of processors. 
        for prog in progs:
           self.set_info(input_info,output_info,prog)
           _scan.lut_scan(self.Ninputs,self.Noutputs,
                          prog,lut,lutshift,flags)
    
    def do_lut_prog(self,data):
        """Do the scan on a set of input and output arrays
        """
        prog,input_info,output_info,lut,lutshift,flags = data
        self.set_info(input_info,output_info,prog)
        _scan.lut_scan(self.Ninputs,self.Noutputs,
                          prog,lut,lutshift,flags)
    
