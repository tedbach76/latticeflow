// static_scancode.c
//
// Ted Bach, tbach@bu.edu
// Code for doing various scans with interrupts. 

//#include"scan.h"


#include "Python.h"
#include "libnumarray.h"
//typedef unsigned int UInt32;

#include<stdlib.h>		// malloc, free,
#include<stdio.h>		//  printf ...
#include<string.h>		//  strcmp ...

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





// If defined, the interrupt op_doer routine will print what it is doing.
//#define DEBUG_OPS 

void print_regs(UInt32 *regs,int n)
{
  int i;
  for (i=0;i<n;i++)
    {
      if (!(i%8))
	{
	  printf("\n%i-%i: ",i,i+8);
	}
      printf("%i ",regs[i]);
    }
};

int op_doer(int *pc,UInt32 *prog,UInt32 *reg)
{
    while (reg[IC_]==0){
	int opcode = prog[*pc];*pc+=1;
#ifdef DEBUG_OPS 
	printf("%i: ",*pc);
#endif
	switch (opcode) {
	case OP_ASSIGN: 
#ifdef DEBUG_OPS 
	  printf("ASSIGN %i,%i\n",prog[*pc],prog[*pc+1]);

#endif 
	  reg[prog[*pc]]=prog[*pc+1];
	  *pc+=2;
	  break;
	case OP_CONTINUE: 
#ifdef DEBUG_OPS 
	  printf("CONTINUE for %i\n",reg[IC_]);
#endif 
	  break;
	case OP_RETURN: 
#ifdef DEBUG_OPS 
	printf("RETURN\n",*pc);
#endif
	  return 1;
	case OP_ADD: 
#ifdef DEBUG_OPS 
	  printf("ADD %i(%x),%i(%x),%i(%x)\n",prog[*pc],reg[prog[*pc]],
              prog[*pc+1],reg[prog[*pc+1]],prog[*pc+2],reg[prog[*pc+2]]);
#endif 
	  reg[prog[*pc]]=reg[prog[*pc+1]]+reg[prog[*pc+2]]; 
	  *pc+=3;
	  break;
	case OP_ADDI: 
#ifdef DEBUG_OPS 
	  printf("ADDI %i(%x),%i(%x),%i\n",prog[*pc],reg[prog[*pc]],
              prog[*pc+1],reg[prog[*pc+1]],prog[*pc+2]);
#endif 
	  reg[prog[*pc]]=reg[prog[*pc+1]]+prog[*pc+2]; 
	  *pc+=3;
	  break;
	case OP_SUB: 
#ifdef DEBUG_OPS 
	  printf("SUB %i(%x),%i(%x),%i(%x)\n",prog[*pc],reg[prog[*pc]],
              prog[*pc+1],reg[prog[*pc+1]],prog[*pc+2],reg[prog[*pc+2]]);
#endif 
	  reg[prog[*pc]]=reg[prog[*pc+1]]-reg[prog[*pc+2]]; 
	  *pc+=3;
	  break;
	case OP_SUBI: 
#ifdef DEBUG_OPS 
	  printf("SUBI %i(%x),%i(%x),%i\n",prog[*pc],reg[prog[*pc+1]]-prog[*pc+2],
              prog[*pc+1],reg[prog[*pc+1]],prog[*pc+2]);
#endif 
	  reg[prog[*pc]]=reg[prog[*pc+1]]-prog[*pc+2]; 
	  *pc+=3;
	  break;
	case OP_INC: 
	  reg[prog[*pc]]+=1;
	  *pc+=1;
	  break;
	case OP_DEC: 
	  reg[prog[*pc]]-=1;
	  *pc+=1;
	  break;
	case OP_MOVE: 
	  reg[prog[*pc]]=reg[prog[*pc+1]];
	  *pc+=2;
	  break;
	case OP_SLT:
	  reg[prog[*pc]]=reg[prog[*pc+1]]<reg[prog[*pc+2]]; 	  
	  *pc+=3;
	case OP_JUMP:
	  *pc = prog[*pc];
	  break;
	case OP_BZ:
	  if (!reg[prog[*pc]]) *pc=prog[*pc+1];
	  else *pc+=2;
	  break;
	case OP_BNZ:
#ifdef DEBUG_OPS 
	  printf("BNZ %i(%i),%i\n",prog[*pc],reg[prog[*pc]],prog[*pc+1]);
#endif 

	  if (reg[prog[*pc]]) *pc=prog[*pc+1];
	  else *pc+=2;
	  break;
        case OP_PRINTALL:
	  print_regs(reg,NREGS);
	  break;
	default: 
	  printf("ERROR: Unknown instruction %i at %i exception interpreter",
		 opcode,*pc);
	  exit(1);
      }
    }
    return 0;
}

// Generic routine for the LUT scan (M inputs, n outputs)
void lut_scan(int Ninput,int Noutput,UInt32 *prog,char *lut,int lut_shift)
{
  UInt32 reg[NREGS]; // REGISTERS
  int pc = 0;
  //  int j;
  UInt32 input,output,tmp;
  int start = 1;
  int input_start = start;
  int Ninput_ = start+Ninput*5;
  int output_start = Ninput_;
  int Noutput_ = output_start+Noutput*6;
  int *reg_;
  int i;
  reg[IC_] = 0;
  
  while (1){
    /* 0) Execute the interrupt code if necessary */
    if (reg[IC_]==0)
      if (op_doer(&pc,prog,reg)) return;
    /* 1) Gather the inputs */
    input = 0;
    for (i=input_start;i<Ninput_;i+=5){
      // REPEAT for each input
      reg_ = reg+i;
      input|=((((*((UInt32*) reg_[0]))&(reg_[1]))  <<reg_[2])>>reg_[3]);
      //      printf("--%x,%i\n",reg_[0],input);
      reg_[0]+=reg_[4];
    }

    /* 2) Apply the LUT */ 
    output = *((UInt32*) (lut+(input<<lut_shift)) );

    /* 3) Write the output values */
    //    j = 0;
    for (i=output_start;i<Noutput_;i+=6)
      {
	reg_ = reg+i;
//	printf("----%x,%i,%i--%x,%x\n",reg_[0],j,output,reg_[1],reg_[2]);
//		j++;

        tmp = (*((UInt32*) reg_[0]))&reg_[2]; // clear the output
        tmp|=(((output&reg_[1]) <<reg_[3])>>(reg_[4]));
       	*((UInt32*) reg_[0])=tmp;
	reg_[0]+=reg_[5];
      }
				
    /* 5) Decrement the interrupt pointer */
    reg[IC_]-=1;               
  }
}

// Lut scan for the case where bits are not packed into arrays
void lut_scan_nopack(int Ninput,int Noutput,UInt32 *prog,char *lut,int lut_shift){
  UInt32 reg[NREGS]; // REGISTERS
  int pc = 0;
  //  int j;
  UInt32 input,output,tmp;
  int start = 1;
  int input_start = start;
  int Ninput_ = start+Ninput*5;
  int output_start = Ninput_;
  int Noutput_ = output_start+Noutput*6;
  int *reg_;
  int i;
  reg[IC_] = 0;
  
  while (1){
    /* 0) Execute the interrupt code if necessary */
    if (reg[IC_]==0)
      if (op_doer(&pc,prog,reg)) return;
    /* 1) Gather the inputs */
    input = 0;
    for (i=input_start;i<Ninput_;i+=5){
      // REPEAT for each input
      reg_ = reg+i;
      input|=(((*((UInt32*) reg_[0]))&(reg_[1]))  <<reg_[2]);
      //      printf("--%x,%i\n",reg_[0],input);
      reg_[0]+=reg_[4];
    }

    /* 2) Apply the LUT */ 
    output = *((UInt32*) (lut+(input<<lut_shift)) );

    /* 3) Write the output values */
    //    j = 0;
    for (i=output_start;i<Noutput_;i+=6)
      {
	reg_ = reg+i;
//	printf("----%x,%i,%i--%x,%x\n",reg_[0],j,output,reg_[1],reg_[2]);
//		j++;

       	*((UInt32*) reg_[0])=(output&reg_[1])>>reg_[4];
	reg_[0]+=reg_[5];
      }
				
    /* 5) Decrement the interrupt pointer */
    reg[IC_]-=1;               
  }
}


// Lut scan for the case where bits are not packed into arrays
// Use UINT8 data types...
void lut_scan_nopack_uint8(int Ninput,int Noutput,UInt32 *prog,char *lut,int lut_shift){
  UInt32 reg[NREGS]; // REGISTERS
  int pc = 0;
  //  int j;
  UInt32 input,output;
  int start = 1;
  int input_start = start;
  int Ninput_ = start+Ninput*5;
  int output_start = Ninput_;
  int Noutput_ = output_start+Noutput*6;
  int *reg_;
  int i;
  reg[IC_] = 0;
  
  while (1){
    /* 0) Execute the interrupt code if necessary */
    if (reg[IC_]==0){
      if (op_doer(&pc,prog,reg))
	{ 
	  return;
	}
    }
    /* 1) Gather the inputs */
    input = 0;
    for (i=input_start;i<Ninput_;i+=5){
      // REPEAT for each input
      reg_ = reg+i;
      input|=(((UInt8*) reg_[0]))[0] <<reg_[2];
      //printf("--%x,%x\n",reg_[0],input);
      reg_[0]+=reg_[4];
    }

    /* 2) Apply the LUT */ 
    output = *((UInt32*) (lut+(input<<lut_shift)) );
    //    printf("lut[%x]=%x\n",input<<lut_shift,output);
    /* 3) Write the output values */
    //    j = 0;
    for (i=output_start;i<Noutput_;i+=6)
      {
	reg_ = reg+i;
	// printf("----%x,%i,%i--%x,%x\n",reg_[0],output,i,reg_[1],reg_[2]);
	//         	     *((UInt8*) reg_[0])=(output&reg_[1])>>reg_[4];
       	((Int8*) reg_[0])[0] = (Int8) ((output&reg_[1])>>reg_[4]);

	reg_[0]+=reg_[5];
      }

    /* 5) Decrement the interrupt pointer */
    reg[IC_]-=1;               
  }
}

// Lut scan for wide LUTS when bits are not packed into arrays
// Use UINT8 data types...
// Output memory structure
// [out_ptr,mask,lut_offset,shift_right,inc]
void widelut_scan_nopack_uint8(int Ninput,int Noutput,UInt32 *prog,char *lut,int lut_shift){
  UInt32 reg[NREGS]; // REGISTERS
  int pc = 0;
  //  int j;
  UInt32 input,output;
  int start = 1;
  int input_start = start;
  int Ninput_ = start+Ninput*5;
  int output_start = Ninput_;
  char *lut_ptr;
  int Noutput_ = output_start+Noutput*6;
  int *reg_;
  int i;
  reg[IC_] = 0;
  
  while (1){
    /* 0) Execute the interrupt code if necessary */
    if (reg[IC_]==0){
      if (op_doer(&pc,prog,reg))
	{ 
	  return;
	}
    }
    /* 1) Gather the inputs */
    input = 0;
    for (i=input_start;i<Ninput_;i+=5){
      // REPEAT for each input
      reg_ = reg+i;
      input|=(*(((UInt8*) reg_[0]))) <<reg_[2];
      //      printf("--%x,%x\n",reg_[0],input);
      reg_[0]+=reg_[4];
    }

    /* 2) Apply the LUT */ 
    lut_ptr = lut+(input<<lut_shift);
    //    printf("lut[%x]=%x,  %i\n",input<<lut_shift,*lut_ptr,lut_shift);
    /* 3) Write the output values */
    //    j = 0;
    for (i=output_start;i<Noutput_;i+=6)
      {
	reg_ = reg+i;
       	*((UInt8*) reg_[0])=((*((UInt32*) (lut_ptr+reg_[3])))&reg_[1])>>reg_[4];
	//	printf("----%x,%x,%i--%x,%x\n",reg_[0],*((UInt8*) reg_[0]),i,reg_[1],reg_[3]);
	reg_[0]+=reg_[5];
      }

    /* 5) Decrement the interrupt pointer */
    reg[IC_]-=1;               
  }
}

/****************************************************************
            TRANSFER SCANS
****************************************************************/

void shift_scan_uint8_nopack(int N,UInt32 *prog)
{
  int reg[NREGS]; // REGISTERS
  int pc = 0;
  int start = 1;
  int input_start = start;
  int *reg_;
  int i;
  reg[IC_] = 0;
  
  while (1){
    /* 0) Execute the interrupt code if necessary */
    if (reg[IC_]==0)
      if (op_doer(&pc,prog,reg)) return;

    for (i=input_start;i<N;i+=5)
      {
	// REPEAT for each input
	reg_ = reg+i;
	*((UInt8*) reg_[1])=*((UInt8*) reg_[0]);
	  reg_[0]+=reg_[2];
	reg_[1]+=reg_[3];
    }
    /* 5) Decrement the interrupt pointer */
    reg[IC_]-=1;               
  }
}

// Address space
// 0 : interrupt
// 1 : 8*n : 0<n<N
//      0      1       2            3          
//     [input*,output*,~output_mask,input_mask,
//      4      5        6         7
//      shift_l,shift_r,input_inc,output_inc]
// 

void shift_scan_uint8(int N,UInt32 *prog)
{
  int reg[NREGS]; // REGISTERS
  int pc = 0;
  int start = 1;
  int input_start = start;
  int *reg_;
  int i;
  UInt32 tmp;
  reg[IC_] = 0;
  
  while (1){
    /* 0) Execute the interrupt code if necessary */
    if (reg[IC_]==0)
      if (op_doer(&pc,prog,reg)) return;

    for (i=input_start;i<N;i+=5)
      {
	// REPEAT for each input
	reg_ = reg+i;
	tmp = (*((UInt32*) reg_[1]))&reg_[2];  //output value
	tmp|= (((*((UInt32*) reg_[0]))&reg_[3])<<reg_[4])>>reg_[5];
	*((UInt32*) reg_[1])=tmp;
	reg_[0]+=reg_[6];
	reg_[1]+=reg_[7];
    }
    /* 5) Decrement the interrupt pointer */
    reg[IC_]-=1;               
  }
}




// Generic routine for the LUT scan (M inputs, n outputs
void transfer_scan(int Ninput,int Noutput,UInt32 *prog)
{
  int reg[NREGS]; // REGISTERS
  int pc = 0;
  int start = 1;
  int input_start = start;
  int Ninput_ = start+Ninput*5;
  int output_start = Ninput_;
  int Noutput_ = output_start+Noutput*6;
  int *reg_;
  int i;
  reg[IC_] = 0;
  
  while (1){
    /* 0) Execute the interrupt code if necessary */
    if (reg[IC_]==0)
      if (op_doer(&pc,prog,reg)) return;

    for (i=input_start;i<Ninput_;i+=5){
      // REPEAT for each input
      reg_ = reg+i;
      reg_[0]+=reg_[4];
    }

    /* 3) Write the output values */
    for (i=output_start;i<Noutput_;i+=7)
      {
	reg_ = reg+i;
	*((UInt32*) reg_[0])&=reg_[2]; // clear the output
	*((UInt32*) reg_[0]) |= 
            (((*((UInt32*) reg_[reg_[6]]))&reg_[1]) << reg_[3])>>(reg_[4]);
	reg_[0]+=reg_[5];
      }
				
    /* 5) Decrement the interrupt pointer */
    reg[IC_]-=1;               
  }
}

/****************************************************************
                 PYTHON WRAPPER CODE
****************************************************************/

    /*DOC*/ static char pc_transfer_scan_doc[] =
    /*DOC*/    "Do a transfer operation, passing values through a LUT"
    /*DOC*/    "\n"
    /*DOC*/    "(Ninput,Noutput,programArray)"
    /*DOC*/ ;


static PyObject *pc_transfer_scan(PyObject *obj, PyObject *args)
{
  int Ninput,Noutput;
  UInt32* prog;
  PyArrayObject* prog_na;

  if (!PyArg_ParseTuple(args,"iiO",
             &Ninput,&Noutput,&prog_na)){
    PyErr_SetString(PyExc_RuntimeError, "Invalid arguments");
    return NULL;
  }

  if (!NA_NumArrayCheck((PyObject*) prog_na))
    {
      PyErr_SetString(PyExc_RuntimeError, "Expected numarrays");
      return NULL;
    }
  prog = (UInt32*) NA_PTR(prog_na);
  transfer_scan(Ninput,Noutput,prog);
  Py_INCREF(Py_None);
  return Py_None;
}


    /*DOC*/ static char pc_lut_scan_doc[] =
    /*DOC*/    "Do a transfer operation, passing values through a LUT"
    /*DOC*/    "\n"
    /*DOC*/    "(Ninput,Noutput,programArray,lutArray,lut_shift,flags)"
    /*DOC*/ ;

# define SCAN_PACK 1
# define SCAN_WIDELUT 2
static PyObject *pc_lut_scan(PyObject *obj, PyObject *args)
{
  int Ninput,Noutput;
  UInt32* prog;
  PyArrayObject* prog_na;
  PyArrayObject* lut_na;
  char* lut;
  int lut_shift;
  int flags;

  if (!PyArg_ParseTuple(args,"iiOOii",
             &Ninput,&Noutput,&prog_na,&lut_na,&lut_shift,&flags)){
    PyErr_SetString(PyExc_RuntimeError, "Invalid arguments");
    return NULL;
  }

  if ((!NA_NumArrayCheck((PyObject*) prog_na)) || 
      (!NA_NumArrayCheck((PyObject*) lut_na)))
    {
      PyErr_SetString(PyExc_RuntimeError, "Expected numarrays");
      return NULL;
    }
  lut = NA_PTR(lut_na);
  prog = (UInt32*) NA_PTR(prog_na);
  if ((flags&SCAN_PACK)&&(!(flags&SCAN_WIDELUT) ))
    Py_BEGIN_ALLOW_THREADS // Release the global interpreter lock
    lut_scan(Ninput,Noutput,prog,lut,lut_shift);
    Py_END_ALLOW_THREADS // Get the interpreter lock back
  else if ((!(flags&SCAN_PACK))&&(!(flags&SCAN_WIDELUT) ))
    Py_BEGIN_ALLOW_THREADS // Release the global interpreter lock
    lut_scan_nopack_uint8(Ninput,Noutput,prog,lut,lut_shift);
    Py_END_ALLOW_THREADS // Get the interpreter lock back
  else if ((!(flags&SCAN_PACK))&&(flags&SCAN_WIDELUT))
    Py_BEGIN_ALLOW_THREADS // Release the global interpreter lock
    widelut_scan_nopack_uint8(Ninput,Noutput,prog,lut,lut_shift);
    Py_END_ALLOW_THREADS // Get the interpreter lock back
  else
    {
      PyErr_SetString(PyExc_RuntimeError, "Invalid scan flag");
      return NULL;
    }
    
  Py_INCREF(Py_None);
  return Py_None;
}


/****************************************************************
                    NA_HELPERS
****************************************************************/
static PyObject *na_ptr(PyObject *obj, PyObject *args)
{
  PyArrayObject *arr;
  if (!PyArg_ParseTuple(args,"O",&arr))
    {
      PyErr_SetString(PyExc_RuntimeError, "Only expected a single arg");
      return NULL;
    }
  // Eliminate this for speed. 
  if (!NA_NumArrayCheck((PyObject*) arr))
    {
      PyErr_SetString(PyExc_RuntimeError, "Require a numarray");
      return NULL;
    }
  
  return  PyInt_FromLong((int)NA_PTR(arr));
}

/****************************************************************
                    MODULE DECLARATION
****************************************************************/

static PyMethodDef methods[] = {
  {"na_ptr",  (PyCFunction)na_ptr,  METH_VARARGS,  NULL},
  {"lut_scan",  (PyCFunction)pc_lut_scan,  METH_VARARGS,  NULL},
  {"transfer_scan",  (PyCFunction)pc_transfer_scan,  METH_VARARGS,  NULL},
  {NULL, NULL, 0, NULL}
};


DL_EXPORT(void);
/* PyMODINIT_FUNC */
void
init_scan(void)
{
  Py_InitModule("_scan", methods);
  import_libnumarray(); // Will need to initialize if use numarray methods
}
