"""The HPP Lattice Gas
Programmed using in the partitioning cellular automata paradigm using
the Margolus neighborhood.

Allows simplified rendering of individual particles.
"""
#-------------------------------- HEADER
from simp import *
#-------------------------------- GOMETRY
Y,X = [100,100]
initialize(size=[Y,X])       # grid size
#-------------------------------- STATE
p  = Signal(SmallUInt(2))
#-------------------------------- COLLISION
hpp_mesh = [2,2]    # define processing is on a coarser mesh.
# This is the short-hand equivalent of
# hpp_mesh = [[2,0],
#             [0,2]]

def hpp():                
    if ( (p[0,0]==p[1,1]) and (p[0,1]==p[1,0]) ):   # collision
        p[0,0]._ = p[0,1]; p[0,1]._ = p[0,0]  # particles swap horizontally
        p[1,0]._ = p[1,1]; p[1,1]._ = p[1,0]   
    else:                                           # keep moving
        p[0,0]._ = p[1,1]; p[0,1]._ = p[1,0]  # particles swap diagonally 
        p[1,0]._ = p[0,1]; p[1,1]._ = p[0,0]        
        
#-------------------------------- Declare the update
hpp_rule = Rule(hpp,generator=hpp_mesh)          # Declare the hpp_rule on 
                                               # a sparser lattice (mesh)
hpp_step = Sequence([hpp_rule,                  # Apply the rule and 
                    Shift({hpp_rule:[1,1]})])  # shift the rule's lattice (mesh)
#-------------------------------- RENDERING
white = OutSignal(UInt8)

def intensity():   
    if p: white._ = 255

#-------------------------------- COMMANDS
# Randomize and set a `vacuum' in the center
import numarray
def init():
    p[:,:] = makedist(p.shape,[1,1])  # Randomize all the signals
    ellipse_region = p[Y*3/8:Y*5/8,X*3/8:X*5/8]
    arr = ellipse_region.value()
    numarray.putmask(arr,ellipsemask(ellipse_region),0)
    ellipse_region._ = arr
  

def reverse():
  hpp_rule()
      
#-------------------------------- USER INTERFACE
ui  = Console(Renderer(Rule(intensity),white))
ui.bind("STEP",hpp_step)
ui.bind("I",init)
ui.bind("R",reverse)
#-------------------------------- INIT and RUN
init()
ui.start()
