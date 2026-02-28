# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.5 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/stepmodules/PcCodeGen/code.py,v $

import simp.rule_analysis as rule_analysis
import copy
import simp.stepmodules.Pc.lut as lut
import simp.step as step

def promotetype(type):
    return {"UInt8":"UInt32","Int8":"Int32",
            "UInt16":"UInt32","Int16":"Int32",
            "UInt32":"UInt32","Int32":"Int32",
            "Float32":"Float32"}[type]
    

def get_ctrans_scan_code(rule):
    tree = copy.deepcopy(rule.__strobed__.tree)
    
    nf = rule_analysis.compiler.walk(tree.code,rule_analysis.NameFinder())
    names = copy.deepcopy(nf.getLocals().elts)
    names.update(nf.getGlobals().elts)

    tree.code.nodes = tree.code.nodes[:-1] # remove the return statement    

    # Should do dynamic type analysis here, but for now, just assume all types
    # are unsigned int.
    iotypedict = rule.__strobed__.iotypedict()
    vartypedict = rule_analysis.getvartypes(tree.code,iotypedict)
    # promote variable types
    for key in vartypedict.keys():
        vartypedict[key] = promotetype(vartypedict[key])
    var_types = names
    for name in var_types.keys():
        type = iotypedict.get(name)
        if type==None:
            type = vartypedict.get(name)
            if type==None:
                raise Exception, """Unable to determine type for '%s'
                  Please submit a bug report on this."""  % name
        # prompte types to 32 bit types
        var_types[name] = type

    # Make the variable declarations for the names.
    declaration_code = ""
    for var,ctype in var_types.items():
        declaration_code+="\n  %s %s;" % (ctype,var)


    code = header+funcheader2+declaration_code+"""
  #ifdef WITH_THREAD // Release the global interpreter lock  
  PyThreadState *_save; \
  _save = PyEval_SaveThread(); 
#endif
  while (1){""" + interrupt_handler

    Ninput = len(rule.inputs)
    Noutput = len(rule.outputs)
    input_start = 1
    output_start = input_start+Ninput*5

    # get the inputs
    input_names = rule.__strobed__.input_proxy_names
    for i in xrange(Ninput):
        x,mask,x,shift,x,x,x = rule.__input_info__[i]
        j = input_start+i*5
        code+="\n\t%s=(*((%s*) reg[%i]));" % \
               (input_names[i],var_types[input_names[i]],j)
        # XXX should eliminate the register access here and make constant
        code+="\n\treg[%i]+=reg[%i];" % (j,j+4)

    # insert the rule's code
    rule_code = rule_analysis.CCodeGenen().getc(tree)
    code+=rule_code

    # write the outputs
    output_names = rule.__strobed__.output_proxy_names
    for i in xrange(Noutput):
        j = output_start+i*6
        if isinstance(rule.outputs[i].base_signal().type,step.SmallUInt):
            # mask output for small uint type
            nbits,mask,mask_ = lut.binary_info(rule.outputs[i])
            code+="\n\t((%s*) reg[%i])[0] = (%s&0x%x);"%\
             (var_types[output_names[i]],j,output_names[i],mask)
        else:
            code+="\n\t((%s*) reg[%i])[0] = %s;"%\
                   (var_types[output_names[i]],j,output_names[i])
        # XXX should eliminate the register access here and make increment
        code+="\n\treg[%i]+=reg[%i];" % (j,j+5)

    # decrement interrupt pointer
    code+="\n\treg[IC_]-=1;\n\t}\n}"
    return code

def get_scan_code(rule):
    # make header and interrupt handler
    code = header+funcheader+interrupt_handler
    Ninput = len(rule.inputs)
    Noutput = len(rule.outputs)
    input_start = 1
    output_start = input_start+Ninput*5
    
    # gather inputs
    code+="\n\tinput = 0;"
    for i in xrange(Ninput):
        x,mask,x,shift,x,x,x = rule.__input_info__[i]
        j = input_start+i*5
#        code+="\n\tinput|=(*(((UInt8*) reg[%i]))) <<reg[%i];" % (j,j+2)
        code+="\n\tinput|=(*(((UInt8*) reg[%i]))) <<%i;" % (j,shift)
        # XXX should eliminate the register access here and make constant
        code+="\n\treg[%i]+=reg[%i];" % (j,j+4)

    code+="\n"
    # get lut position
    if rule.__wide_lut__:
        code+="\n\tlut_ptr = lut+(input<<%i);" % rule.__lut_shift__
#        code+="\n"
#        code+="""\nprintf("first output %i\n",*lut_ptr);"""
    else:
        code += \
          "\n\toutput = *((UInt32*) (lut+(input<<%i)) );" % rule.__lut_shift__
#        code+="\n"
#        code+="""\nprintf("output %i\n",output);"""

    # write outputs
    for i in xrange(Noutput):
        x,mask,mask_,lut_ofst,shift,x,x = rule.__output_info__[i]
        j = output_start+i*6
        if rule.__wide_lut__:
       	    code+= \
             "\n\t((UInt8*) reg[%i])[0]=((*((UInt32*) (lut_ptr+%i)))&0x%x)>>%i; "\
             % (j,lut_ofst,mask,shift)
        else:
            code+="\n\t((Int8*) reg[%i])[0]=(Int8) ((output&0x%x)>>%i);"%\
                 (j,mask,shift)
        # XXX should eliminate the register access here and make increment
        code+="\n\treg[%i]+=reg[%i];" % (j,j+5)

    # decrement interrupt pointer
    code+="\n\treg[IC_]-=1;\n\t}\n}"
    return code

header = """
// NUMARRAY TYPES (some of them)
typedef signed char              Int8;
typedef unsigned char            UInt8;
typedef short int                Int16;
typedef unsigned short int       UInt16;
typedef int                      Int32;
typedef unsigned int             UInt32;
typedef float                    Float32;


//#include<stdlib.h>		// malloc, free,
#include<stdio.h>		//  printf ...
//#include<string.h>		//  strcmp ...

// REGISTER MEMORY MAP
#define IC_  0  // interrupt counter
#define NREGS 1<<10

/*
REGISTER STRUCTURE
0 : Interupt counter
1 : 
  : inputs (pointer,mask,shift_l,shift_r,inc) // 5*Nin
  : outputs (pointer,in_mask,~out_mask,shift_l,shift_r,inc) // 6*Nout
400: base_pointers
*/

// INTERRUPT INSTRUCTIONS
#define OP_ASSIGN 0       // ASSIGN a,b         reg[a] <- b               
#define OP_CONTINUE 1     // CONTINUE           Continue in the loop
#define OP_RETURN 2       // RETURN             Exit the function
#define OP_ADD 3          // ADD a,b,c          reg[a] <- reg[b]+reg[c]
#define OP_SUB 4          // SUB a,b,c          reg[a] <- reg[b]-reg[c]
#define OP_INC 5          // INC a              reg[a] <- reg[a]+1
#define OP_DEC 6          // DEC a              reg[a] <- reg[a]-1
#define OP_MOVE 7         // MOVE a,b           reg[a] <- reg[b]
#define OP_SLT 8          // SLT a,b,c          reg[a] <- reg[b]<reg[c]
#define OP_BNZ 9          // BNZ a,b            if reg[b]!=0: pc <- b          
#define OP_JUMP 10        // JUMP a             pc <- a 
#define OP_BZ 11          // BZ  a,b            if reg[b]==0: pc <- b          
#define OP_PRINTALL 12    // PRINTALL           print all of the registers
#define OP_ADDI 13        // ADD a,b,c          reg[a] <- reg[b]+c
#define OP_SUBI 14        // SUB a,b,c          reg[a] <- reg[b]-c

"""


funcheader2 = """
void scan(int progptr){
  UInt32 *prog = (UInt32*) progptr;
  UInt32 reg[NREGS]; // REGISTERS
  int pc = 0;
  reg[IC_] = 0;
"""


funcheader = """
void scan(int progptr,int lutptr){
  UInt32 *prog = (UInt32*) progptr;
  char *lut = (char*)lutptr;
  UInt32 reg[NREGS]; // REGISTERS
  int pc = 0;
  char *lut_ptr;  
  UInt32 input,output;
  reg[IC_] = 0;

#ifdef WITH_THREAD // Release the global interpreter lock  
  PyThreadState *_save; \
  _save = PyEval_SaveThread(); 
#endif
  while (1){
"""
#   int start = 1;
#   int input_start = start;
#   int Ninput_ = start+Ninput*5;
#   int output_start = Ninput_;
#   char *lut_ptr;
#   int Noutput_ = output_start+Noutput*6;
#   int *reg_;
#   int i;
interrupt_handler = """
    /* 0) Execute the interrupt code if necessary */
    while (reg[IC_]==0){
  	int opcode = prog[pc];pc+=1;
  	switch (opcode) {
  	case OP_ASSIGN: 
  	  reg[prog[pc]]=prog[pc+1];
  	  pc+=2;
  	  break;
  	case OP_CONTINUE: 
  	  break;
  	case OP_RETURN:
          #ifdef WITH_THREAD 
            PyEval_RestoreThread(_save); // Get the interpreter lock back
          #endif
  	  return;
  	case OP_ADD: 
  	  reg[prog[pc]]=reg[prog[pc+1]]+reg[prog[pc+2]]; 
  	  pc+=3;
  	  break;
  	case OP_ADDI: 
  	  reg[prog[pc]]=reg[prog[pc+1]]+prog[pc+2]; 
  	  pc+=3;
  	  break;
  	case OP_SUB: 
  	  reg[prog[pc]]=reg[prog[pc+1]]-reg[prog[pc+2]]; 
  	  pc+=3;
  	  break;
  	case OP_SUBI: 
  	  reg[prog[pc]]=reg[prog[pc+1]]-prog[pc+2]; 
  	  pc+=3;
  	  break;
  	case OP_INC: 
  	  reg[prog[pc]]+=1;
  	  pc+=1;
  	  break;
  	case OP_DEC: 
  	  reg[prog[pc]]-=1;
  	  pc+=1;
  	  break;
  	case OP_MOVE: 
  	  reg[prog[pc]]=reg[prog[pc+1]];
  	  pc+=2;
  	  break;
  	case OP_SLT:
  	  reg[prog[pc]]=reg[prog[pc+1]]<reg[prog[pc+2]]; 	  
  	  pc+=3;
  	case OP_JUMP:
  	  pc = prog[pc];
  	  break;
  	case OP_BZ:
  	  if (!reg[prog[pc]]) pc=prog[pc+1];
  	  else pc+=2;
  	  break;
  	case OP_BNZ:
  	  if (reg[prog[pc]]) pc=prog[pc+1];
  	  else pc+=2;
  	  break;
  //        case OP_PRINTALL:
  //	  print_regs(reg,NREGS);
  //	  break;
  	default: 
  	  printf("ERROR: Unknown instruction %i at %i exception interpreter",
  		 opcode,pc);
  	  exit(1);
        }
    }
"""



interrupt_handler_debug = """
    while (reg[IC_]==0){
	int opcode = prog[pc];pc+=1;
	printf("%i: ",pc);
	switch (opcode) {
	case OP_ASSIGN: 
	  printf("ASSIGN %i,%i\n",prog[pc],prog[pc+1]);
	  reg[prog[pc]]=prog[pc+1];
	  pc+=2;
	  break;
	case OP_CONTINUE: 
	  printf("CONTINUE for %i\n",reg[IC_]);
	  break;
	case OP_RETURN: 
	  printf("RETURN\n",pc);
          #ifdef WITH_THREAD 
            PyEval_RestoreThread(_save); // Get the interpreter lock back
          #endif
	  return;
	case OP_ADD: 
	  printf("ADD %i(%x),%i(%x),%i(%x)\n",prog[pc],reg[prog[pc]],
              prog[pc+1],reg[prog[pc+1]],prog[pc+2],reg[prog[pc+2]]);
	  reg[prog[pc]]=reg[prog[pc+1]]+reg[prog[pc+2]]; 
	  pc+=3;
	  break;
	case OP_ADDI: 
	  printf("ADDI %i(%x),%i(%x),%i\n",prog[pc],reg[prog[pc]],
              prog[pc+1],reg[prog[pc+1]],prog[pc+2]);
	  reg[prog[pc]]=reg[prog[pc+1]]+prog[pc+2]; 
	  pc+=3;
	  break;
	case OP_SUB: 
	  printf("SUB %i(%x),%i(%x),%i(%x)\n",prog[pc],reg[prog[pc]],
              prog[pc+1],reg[prog[pc+1]],prog[pc+2],reg[prog[pc+2]]);
	  reg[prog[pc]]=reg[prog[pc+1]]-reg[prog[pc+2]]; 
	  pc+=3;
	  break;
	case OP_SUBI: 
	  printf("SUBI %i(%x),%i(%x),%i\n",prog[pc],reg[prog[pc+1]]-prog[pc+2],
              prog[pc+1],reg[prog[pc+1]],prog[pc+2]);
	  reg[prog[pc]]=reg[prog[pc+1]]-prog[pc+2]; 
	  pc+=3;
	  break;
	case OP_INC: 
	  reg[prog[pc]]+=1;
	  pc+=1;
	  break;
	case OP_DEC: 
	  reg[prog[pc]]-=1;
	  pc+=1;
	  break;
	case OP_MOVE: 
	  reg[prog[pc]]=reg[prog[pc+1]];
	  pc+=2;
	  break;
	case OP_SLT:
	  reg[prog[pc]]=reg[prog[pc+1]]<reg[prog[pc+2]]; 	  
	  pc+=3;
	case OP_JUMP:
	  pc = prog[pc];
	  break;
	case OP_BZ:
	  if (!reg[prog[pc]]) pc=prog[pc+1];
	  else pc+=2;
	  break;
	case OP_BNZ:
	  printf("BNZ %i(%i),%i\n",prog[pc],reg[prog[pc]],prog[pc+1]);
	  if (reg[prog[pc]]) pc=prog[pc+1];
	  else pc+=2;
	  break;
//        case OP_PRINTALL:
//	  print_regs(reg,NREGS);
//	  break;
	default: 
	  printf("ERROR: Unknown instruction %i at %i exception interpreter",
		 opcode,pc);
	  exit(1);
      }
    }
"""


