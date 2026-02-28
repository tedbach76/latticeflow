// scan.h
// Generic header for the scan routines

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

