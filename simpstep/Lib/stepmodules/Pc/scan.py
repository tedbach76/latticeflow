# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.2 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/stepmodules/Pc/scan.py,v $

"""
Basic routines for generating scan programs.

TODO:
  Make generic versions of these scan generators.
  
"""

from simp.step import *

from simp import geom as _geom
import numarray as _na
import _scan

from simp import cache

import math
SCAN_PACK=1
SCAN_WIDELUT=2
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#            PC SCAN OPERATIONS
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
OP_ASSIGN = 0       # ASSIGN a,b         reg[a] <- b               
OP_CONTINUE = 1     # CONTINUE           Continue in the loop
OP_RETURN = 2       # RETURN             Exit the function
OP_ADD = 3          # ADD a,b,c          reg[a] <- reg[b]+reg[c]
OP_SUB = 4          # SUB a,b,c          reg[a] <- reg[b]-reg[c]
OP_INC = 5          # INC a              reg[a] <- reg[a]+1
OP_DEC = 6          # DEC a              reg[a] <- reg[a]-1
OP_MOVE = 7         # MOVE a,b           reg[a] <- reg[b]
OP_SLT = 8          # SLT a,b,c          reg[a] <- reg[b]<reg[c]
OP_BNZ = 9          # BNZ a,b            if reg[b]!=0: pc <- b          
OP_JUMP = 10        # JUMP a             pc <- a 
OP_BZ = 11          # BZ  a,b            if reg[b]==0: pc <- b          
OP_PRINTALL = 12    # PRINTALL           print all of the registers
OP_ADDI = 13         # ADD a,b,c          reg[a] <- reg[b]+c
OP_SUBI = 14         # SUB a,b,c          reg[a] <- reg[b]-c

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#            PC SCAN PROGRAM
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def compute_coset_scan(signals,positions,strides,registers,rule):
    """Return a matrix giving the index offsets of a signal at a given
    position from the start of each row."""
    def sorter(a,b): # for sorting into ascending order
        if a[0]<b[0]: return -1
        return 1
    rect = _geom.rectangular_cell_size(rule.generator)/rule.spacing
    coset_scans = []
    indx = _na.zeros(len(rect))
    size = rule.size    
    while 1:
        coord = rule.__coordinate__(indx)        
        wraps = []
        prog = []
        for i in xrange(len(signals)):

            signal = signals[i]

#            print "=========",positions[i],coord,
            ofst = signal.__array_index__(_geom.add(positions[i],coord))
            ofst_ = ofst[-1]
            wrap = int(math.ceil((signal.shape[-1]-ofst_)/ \
                                 float(rule.spacing[-1]/signal.spacing[-1])))
            wrap = wrap%rule.shape[-1]
#            print ofst,
            ofst = (ofst[-1])*strides[i][-1]
#            print ofst,wrap
            if ofst!=0:
                prog.extend([OP_ADDI,registers[i],registers[i],ofst])
            if wrap!=0: # don't append if it wraps around at zero. 
                wraps.append([wrap,i,signals[i].shape[-1]*strides[i][-1]])
        if len(wraps)>0:
            # put on a sentinel for the end of the row scan
            wraps.append([rule.size[-1]/rule.spacing[-1],-1,0])
            # sort into ascending order                             
            wraps.sort(sorter) 
            # compute interrupt distances
            i = len(wraps)-1
            while i>=1:
                wraps[i][0] = wraps[i][0]-wraps[i-1][0]    
                i-=1
            # construct the interrupt program
            # add interrupts for wrap-around
            for i in xrange(len(wraps)):
                intr,elt,sub = wraps[i]
                if intr!=0:
                    prog.extend([OP_ASSIGN,0,intr])
                if (elt!=-1):
                    prog.extend([OP_SUBI,registers[elt],registers[elt],sub])
        else:
            # set the interrupt for a row scan.
            prog.extend([OP_ASSIGN,0,rule.size[-1]/rule.spacing[-1]]) 
        coset_scans.append(prog)
#        print prog
        _geom.multidimensional_inc(indx,rect,1,-1)
        if _na.alltrue(indx==0):  break
    return coset_scans

def compute_interrupts(signals,positions,strides,base_registers,
                       ptr_registers,rule):
    """Returns an interrupt program for a rule..."""
    rect = _geom.rectangular_cell_size(rule.generator)/rule.spacing
#    print "HERE=-------------------------"
    row_scan = compute_coset_scan(signals,positions,strides,ptr_registers,rule)
#    print row_scan
    scan_prog = []
    nd = rule.nd
    indx = _na.zeros(len(rect))
#    for sig in signals:
#        sig_strides[i] = strides[i]*(rule.spacing/sig.spacing)

    adjusted_coord = _na.zeros(nd)
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

    return scan_prog

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#            ScanDoer
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

#REGISTER STRUCTURE
#0 : Interupt counter
#1 : 
#  : inputs (pointer,mask,shift_l,shift_r,inc) // 5*Nin
#  : outputs (pointer,in_mask,~out_mask,shift_l,shift_r,inc) // 6*Nout
#400: base_pointers

class ScanDoer:
    def __init__(self,rule,verbose=1):
        self.verbose = verbose
        self.rule = rule
        self.signals = rule.inputs+rule.outputs
        self.base_signals = [sig.base_signal() for sig in self.signals]
#        self.signal_offsets = [sig.neighbor_offset() for sig in self.signals]

        # compute the row step size for all of the signals
        rule_spacing = self.rule.spacing[-1]                
        self.stepsizes = [rule_spacing/sig.spacing[-1] 
                          for sig in self.base_signals]
        
        self.Ninputs = len(rule.inputs)
        self.Noutputs = len(rule.outputs)
#        self.input_strides = input_strides
#        self.output_strides = output_strides
        # XXX need to compute masks, shifts and the like
        self.__compute_register_mappings__()
        # cached scans...
        self.prog = None
        self.cache = cache.cache
        # compute the base hash (not needed since each doer keeps its own cache)
        base_hash = "LUT SCAN\nsize"+`rule.size`
        base_hash+= "\ninputs:"+\
                    `[sig.base_signal().generator for sig in self.rule.inputs]` 
        base_hash+= "\noutputs:"+\
                    `[sig.base_signal().generator for sig in self.rule.outputs]` 
        if self.rule!=None:
            base_hash+= "\nrule:"+`self.rule.generator`
        self.base_hash = base_hash

    def scan_program_initialization(self):
        """Compile the part of the scan program that does the initialization."""
        # What the initialization does:
        prog = []
        #   1) assign base pointer values masks,shifts, increments
        for i in xrange(self.Ninputs):
            prog.extend([OP_ASSIGN,self.in_base_reg[i],-1])
            prog.extend([OP_ASSIGN,self.in_mask_reg[i],-1])
            prog.extend([OP_ASSIGN,self.in_shiftl_reg[i],-1])
            prog.extend([OP_ASSIGN,self.in_shiftr_reg[i],-1])
            prog.extend([OP_ASSIGN,self.in_inc_reg[i],-1])
            
        for i in xrange(self.Noutputs):
            prog.extend([OP_ASSIGN,self.out_base_reg[i],-1])
            prog.extend([OP_ASSIGN,self.out_inmask_reg[i],-1])
            prog.extend([OP_ASSIGN,self.out_outmask_reg[i],-1])
            prog.extend([OP_ASSIGN,self.out_shiftl_reg[i],-1])
            prog.extend([OP_ASSIGN,self.out_shiftr_reg[i],-1])
            prog.extend([OP_ASSIGN,self.out_inc_reg[i],-1])
        return prog

    def set_info(self,input_info,output_info,prog):
        """ info: [base_ptr,mask,shiftl,shiftr,bytesize]
        """
        for i in xrange(self.Ninputs):
            ofst = i*5*3+2
            info = input_info[i]
            prog[ofst+0] = info[0] # base pointer
            prog[ofst+3] = info[1] # in mask
            prog[ofst+6] = info[3] # shift_l
            prog[ofst+9] = info[4] # shift_r
            # element stride
            prog[ofst+12] = info[5][-1]*self.stepsizes[i]

        ofst_base = self.Ninputs*5*3
        if self.Ninputs==0: i=0
        else: i+=1
        for j in xrange(self.Noutputs):
            ofst = ofst_base + j*3*6+2
            info = output_info[j]
            prog[ofst+0] = info[0] # base pointer
            # Note: the masking is a hack reduce mask sizes to fit into 
            # a 32 bit integer---this only really is needed to work around
            # a problem when there are more than 32 bits of input (PcCodeGen)
            prog[ofst+3] = int(0xffffffff&info[1]) # input mask
            prog[ofst+6] = int(0xffffffff&info[2]) # output mask
            prog[ofst+9] = info[3] # shift left
            prog[ofst+12] = info[4] # shift right
            # element stride
            prog[ofst+15] = info[5][-1]*self.stepsizes[i]
            i+=1
        
    def __compute_register_mappings__(self):
      # Compute the register mappings for the various fields that we
      # will be using.

      # We choose the start of the base pointer regs so that it is
      # greater than the number of registers that could be used
      # assuming a maxumum of 32 input and output pointers
      # (ie. 1+(6+5)*32=353).
      self.BASE_START = 400
      self.INPUT_START = 1
      self.INPUT_RECORD_SZ = 5
      self.OUTPUT_START = self.INPUT_START+self.Ninputs*self.INPUT_RECORD_SZ
      self.OUTPUT_RECORD_SZ = 6

      self.in_base_reg = [] # base pointers
      # Input records
      self.in_ptr_reg = []
      self.in_mask_reg = []
      self.in_shiftl_reg = []
      self.in_shiftr_reg = []
      self.in_inc_reg = []

      self.out_base_reg = [] # base pointers
      # Output Records
      self.out_ptr_reg = []
      self.out_inmask_reg = []
      self.out_outmask_reg = [] # inverted mask
      self.out_shiftl_reg = []
      self.out_shiftr_reg = []
      self.out_inc_reg = []

      for i in xrange(self.Ninputs):
        self.in_base_reg.append(self.BASE_START+i)
        self.in_ptr_reg.append(self.INPUT_START+i*self.INPUT_RECORD_SZ+0)
        self.in_mask_reg.append(self.INPUT_START+i*self.INPUT_RECORD_SZ+1)
        self.in_shiftl_reg.append(self.INPUT_START+i*self.INPUT_RECORD_SZ+2)
        self.in_shiftr_reg.append(self.INPUT_START+i*self.INPUT_RECORD_SZ+3)
        self.in_inc_reg.append(self.INPUT_START+i*self.INPUT_RECORD_SZ+4)

      for i in xrange(self.Noutputs):
        self.out_base_reg.append(self.BASE_START+self.Ninputs+i)
        self.out_ptr_reg.append(self.OUTPUT_START+i*self.OUTPUT_RECORD_SZ+0)
        self.out_inmask_reg.append(self.OUTPUT_START+i*self.OUTPUT_RECORD_SZ+1)
        self.out_outmask_reg.append(self.OUTPUT_START+i*self.OUTPUT_RECORD_SZ+2)
        self.out_shiftl_reg.append(self.OUTPUT_START+i*self.OUTPUT_RECORD_SZ+3)
        self.out_shiftr_reg.append(self.OUTPUT_START+i*self.OUTPUT_RECORD_SZ+4)
        self.out_inc_reg.append(self.OUTPUT_START+i*self.OUTPUT_RECORD_SZ+5)

    def get_scan_program(self):
        # Get the strides and positions
        strides = [0]*(self.Ninputs+self.Noutputs)
        positions = [0]*(self.Ninputs+self.Noutputs)
        for i in xrange(self.Ninputs):
            info = self.input_info[i]
            strides[i] = info[5]; positions[i] = info[6]
        if self.Ninputs==0: i=0
        else:         i+=1            
        for j in xrange(self.Noutputs):
            info = self.output_info[j]
            strides[i] = info[5]; positions[i] = info[6]
            i+=1
        hash = self.base_hash+ "positions"+`positions`+"strides" +`strides`

        # Try to get the program from cache
        try: return self.cache[hash]
        except KeyError,e: pass

        if self.verbose:
            print """COMPILING THE SCAN ..........................."""
        # Compile the scan from scratch
        self.strides, self.positions = strides,positions
        prog = compute_interrupts(self.base_signals,
                           positions,strides,
                           self.in_base_reg+self.out_base_reg,
                           self.in_ptr_reg+self.out_ptr_reg,self.rule)
        prog = self.scan_program_initialization()+prog+[OP_RETURN]
        prog = _na.array(prog)
        # Cache it
        self.cache[hash]=prog
        # Return it
        return prog

    def do_lut(self,input_info,output_info,lut,lutshift=2,flags=0):
        """Do the scan on a set of input and output arrays
        info : [base_ptr,inmask,outmask,shift_l,shift_r,strides,position]
          position : the current position of the sign
        """

        self.input_info = input_info
        self.output_info = output_info
        self.lut = lut

        prog = self.get_scan_program()
        self.set_info(input_info,output_info,prog)
        _scan.lut_scan(self.Ninputs,self.Noutputs,
                       prog,self.lut,lutshift,flags)

        
