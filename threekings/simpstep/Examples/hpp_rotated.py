"""The HPP Lattice Gas on a lattice that has been rotated by 45 degrees
"""
#-------------------------------- HEADER
from simp import *
#-------------------------------- GOMETRY
X,Y = [500]*2
initialize(size=[X,Y],
           generator=[2,2])       # grid size
#-------------------------------- STATE
binary = SmallUInt(2)                 # make 4 binary signals for particles

p0,p1,p2,p3 = map(Signal,[binary]*4)

#-------------------------------- COLLISION 
def hpp():  # scatter at right angles on collision

    if ( (p0==p2) and (p1==p3) ):
        p0._ = p3;    p1._ = p2       # swap horizontally
        p3._ = p0;    p2._ = p1
hpp = Rule(hpp)

#-------------------------------- Declare the update
hpp_step = Sequence([
        Shift(kvdict(p0=[ 1, 1],p1=[ 1,-1],  
                     p3=[-1, 1],p2=[-1,-1])),
        hpp])

reverse_hpp_step = Sequence([
        Shift(kvdict(p0=[-1,-1],p1=[-1, 1],  
                     p3=[ 1,-1],p2=[ 1, 1])),
        hpp])

#-------------------------------- RENDERING
white = OutSignal(UInt8)

def intensity():   
    white._ = (p0+p1+p2+p3)*255/4

rend = Renderer(Rule(intensity),outputs=white)
#-------------------------------- COMMANDS
# Randomize and set a `vacuum' in the center
import numarray
def init():
  for sig in (p0,p1,p2,p3):
      sig[:,:] = makedist(sig.shape,[1,1])
      ellipse_region = sig[Y*3/8:Y*5/8,X*3/8:X*5/8]
      arr = ellipse_region.value()
      numarray.putmask(arr,ellipsemask(ellipse_region),0)
      ellipse_region._ = arr

direction = 0
def reverse():
    global direction
    hpp()
    if direction==0:
        ui.bind("STEP",reverse_hpp_step)
    elif direction==1:
        ui.bind("STEP",hpp_step)
    direction=(direction+1)%2
init()      
#-------------------------------- USER INTERFACE
ui  = Console(rend)
ui.bind("STEP",hpp_step)
ui.bind("R",reverse)
ui.bind("I",init)
#-------------------------------- INIT and RUN
ui.start()
