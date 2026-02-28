""" polymer.py
SIMP code for the polymer rule.
Programmed with the 'pinwheel' partitioning CA neighborhood.

[note to tt: this description is just a reminder for us, it should
be improved for a self-contained version. ]

Summary

 Polymers particles are represented by bits on a grid.  A polymer chain
 is composed of adjacent particles.

 In the dynamics the particles move so long as doing so doesn't break
 or create polymer chains. 

 The rule must look at data in positions '*' to determine if position
 'X' can swap in each of the two orientations shown below.

        *             *          **
       *X             X*        *XX*
         X*         *X          *XX*
         *           *           **
                            
       SWAP 1      SWAP 2     TOGETHER

 Because the particles can't swap independently, the rule needs to
 update them together yielding the 'together' tile above.

Rule Lattice

  We call the rule's lattice the "mesh" 

  The rule applications need to be spaced properly to ensure that
  sites particles in the 'sensitive horns' of the dogbone don't change
  while a block is being updated.  Below we derive a lattice that is
  compatable with this constraint. 
  
                   
         XX  XX  XX             .   .   .       ---> [0,4]
         XX  XX  XX                             \
           XX  XX                 .   .          > [2,2] 
           XX  XX            
         XX  XX  XX             .   .   .   
         XX  XX  XX
         
      THE OUTPUT TILES         THEIR LATTICE    THEIR GENERATORS     
"""

from simp import *
# -------------------------------- GEOMETRY
Y,X = [102,100]
initialize(size=[Y,X])
# We use the size [102,100] because otherwise the mesh will not wrap 
# around to itself.
# 
# (SIMP raises a StepError whenever a an non-wraping lattice is declared)
# 


# -------------------------------- STATE
mesh    = [[3,2],       # generator for the rule 'mesh'
           [0,4]]       

p      = Signal(SmallUInt(2))         # polymer state
r      = Signal(SmallUInt(2),mesh)    # random bit for emulating
                                      # Poisson updating ---declared on the mesh

# -------------------------------- DYNAMICS
def thermalize():
    """Swap if doing so doesn't create or break a polymer chain."""
    if r: # emulate Poisson updating with the random bit.
        if ((p[-1,0]+p[0,-1]+p[2,1]+p[1,2])==0):
            p[0,0]._ = p[1,1]
            p[1,1]._ = p[0,0]
    else:
        if ((p[1,-1]+p[2,0]+p[-1,1]+p[0,2])==0):
            p[1,0]._ = p[0,1]
            p[0,1]._ = p[1,0]

thermalize_rule =  Rule(thermalize,generator=mesh)# declare the rule on the mesh
thermalize_step = Sequence([thermalize_rule,
                           Shuffle([r,thermalize_rule])])
# The step for updating the polymer does two things---it applies the rule,
# Shuffles the randomness and moves the rule to a random starting position.

# -------------------------------- RENDERING
white = OutSignal(UInt8)

def bw():
    """black if a polymer is present"""
    if p: white._ = 255
  
bw = Renderer(Rule(bw),outputs=white)

# -------------------------------- INITIALIZE
r[:,:] = makedist(r.shape,[1,1])   # Poisson updating

def make_rectangle(sig,x,y,width,height):
    sig[y,x:x+width] = 1  # top of the rectangle
    sig[y:y+height,x] = 1  # left side
    sig[y:y+height,x+width] = 1  # right side
    sig[y+height,x:x+width+1] = 1  # bottom
  
def init():
    # Initialize the polymer with a rectangle. 
    p[:,:] = 0  # set everything to zero
    minwidth = 10
    Nline = 10
    Xofst = 10
    Yofst = 10
    for i in xrange(Nline):
        y = Yofst+ i*Y/(Nline+1)
        Xextent = Xofst + i*X/(Nline+1)*8/10 + X/10
        p[y,Xofst:Xextent]._ = 1

    make_rectangle(p,(X*5)/8,Y/4,20,20)

    p[Y/8,X/2:X*15/16]._ = 1
    p[Y/8:Y/2,X*15/16]._ = 1    
    
#    make_rectangle(p,5,5,X*2/3,Y*2/3)
#    p[Y-1,0:X-1] = 1  # line
#    p[Y/2,X/2-20:X/2] = 1
  
# -------------------------------- CONSOLE USER INTERFACE
init()
ui  = Console(bw)
ui.bind('STEP',thermalize_step)
ui.bind("I",init)
ui.start()
