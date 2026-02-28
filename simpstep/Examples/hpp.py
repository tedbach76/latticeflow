"""
The HPP Lattice Gas defined in the most straight-forward way without
a rotated lattice and only simulating half of the lattice.
"""
#-------------------------------- HEADER
from simp import *
#-------------------------------- GOMETRY
X,Y = [200]*2
initialize(size=[X,Y],
           generator=[[1,1],
                      [0,2]])       # grid size
#-------------------------------- STATE
binary = SmallUInt(2)                 # make 4 binary signals for particles

signals = map(Signal,[binary]*4)
p0,p1,p2,p3 = signals

#-------------------------------- COLLISION 
def hpp():  # scatter at right angles on collision
    if ( (p0==p2) and (p1==p3) ):
        p0._ = p3;    p1._ = p2       # swap horizontally
        p3._ = p0;    p2._ = p1
hpp = Rule(hpp)

#-------------------------------- RENDERING
white = OutSignal(UInt8,generator=[1,1])   

def intensity():   
    white[0,0]._ = (p0+p1+p2+p3)*255/4
    white[0,1]._ = (p0+p1+p2+p3)*255/4    

render_rule = Rule(intensity)
rend = Renderer(render_rule,outputs=white)

#-------------------------------- Declare the update
hpp_step = Sequence([
        Shift(kvdict( p0=[ 1, 0],
             p1=[ 0, 1],      p3=[ 0,-1],
                      p2=[-1, 0],
             render_rule=[0,-1])),
        hpp])

# transport particles in the reverse directions
reverse_hpp_step = Sequence([
        Shift(kvdict( p0=[-1, 0],
             p1=[ 0,-1],      p3=[ 0, 1],
                      p2=[ 1, 0],
             render_rule=[0,-1])),
        hpp])
#-------------------------------- COMMANDS
# Randomize and set a `vacuum' in the center
import numarray
def init():
  for sig in signals:
      sig[:,:] = makedist(sig.shape,[1,1])
      ellipse_region = sig[Y*3/8:Y*5/8,X*3/8:X*5/8]
      arr = ellipse_region.value()
      numarray.putmask(arr,ellipsemask(ellipse_region),0)
      ellipse_region._ = arr

direction = 0
def reverse():
    global direction
    hpp() # undo the rule application
    # rebind step to its inverse.
    if direction==0: ui.bind("STEP",reverse_hpp_step)
    elif direction==1: ui.bind("STEP",hpp_step)
    direction=(direction+1)%2
init()      
#-------------------------------- USER INTERFACE
ui  = Console(rend)
ui.bind("STEP",hpp_step)
ui.bind("R",reverse)
ui.bind("I",init)
#-------------------------------- INIT and RUN
ui.start()
