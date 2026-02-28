""" SIMP code for the FHP lattice gas.
Simple version where particles move with unit velocity unless exactly
two collide head-on in which case they are rotated randomly.

Uses the 'brick wall' approximation for rendering.
"""
from simp import *

#-------------------------------- GOMETRY
Y,X = 200,200
initialize(generator=[[1,1],
                      [0,2]],
           size=[Y,X])
#-------------------------------- SIGNALS
#      p0 p1 
#     p5 x p2    signals move towards x
#      p4 p3     

binary = SmallUInt(2)
state_signals = map(Signal,[binary]*6)  # allocate 6 binary signals 
p0,p1,p2,p3,p4,p5 = state_signals       # name the signals separately
r = Signal(binary)                      # will hold randomness

#-------------------------------- INTERACTION
def fhp():
  if (p0==p3) and (p1==p4) and (p5==p2): # rotate randomly
      if r==1: 		        # rotate cw
        p0._=p5; p1._=p0; p2._=p1; p3._=p2; p4._=p3; p5._=p4
      else: 			# rrotate ccw
        p0._=p1; p1._=p2; p2._=p3; p3._=p4; p4._=p5; p5._=p0        

#-------------------------------- STEP
# shift the state variables in each of the six directions, shuffle
# the randomness and apply the fhp rule
fhp_step = Sequence([
               Shift(kvdict(p0=[1,1], p1=[-1,1], 
                       p5=[0,2],        p2=[0,-2],
                         p4=[1,-1], p3=[-1,-1])),
               Shuffle([r]),
               Rule(fhp)])

#-------------------------------- RENDERING
# Render on the grid  (generator=[1,1]) 
white = OutSignal(UInt8,generator=[1,1])

def intensity(): # use a 'brick wall' approximation of a hex lattice
  white[0,1]._ = white[0,0]._ = (p0+p1+p2+p3+p4+p5)*255/6
#-------------------------------- INITIALIZATION
r[:,:]   = makedist(r.shape,[1,1]) # Randomizes the coin

# initialize with an ellipse in the center
import numarray
for sig in state_signals:
    sig[:,:] = makedist(sig.shape,[1,1])
    # make an ellipsoidal vacuum in the center
    ellipse_region = sig[Y*3/8:Y*5/8,X*3/8:X*5/8]
    arr = ellipse_region.value()
    numarray.putmask(arr,ellipsemask(ellipse_region),0)
    ellipse_region._ = arr

#-------------------------------- CONSOLE USER INTERFACE
ui  = Console(Renderer(Rule(intensity),white))
ui.bind("STEP",fhp_step)
ui.start()
