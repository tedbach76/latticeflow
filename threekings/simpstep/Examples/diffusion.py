"""Diffusion using the dimension-splitting technique.

Uses the technique described in

  D'Souza, Margolus, and Smith, "Dimension-Splitting for Simplifying
  Diffusion in Lattice Gas Models", Journal of Statistical Physics, Vol. 107,
  Nos. 1/2, April 2002.

Fractional shifts are used to implement an alternating lattice. 
"""

from simp import *
Y,X = 200,200
# -------------------------------- INITIALIZATION
initialize(generator=[2,2], # scale of the lattice. 
           size=[Y,X])

# -------------------------------- STATE
a = Signal(SmallUInt(2))   # two signals, one for each of two possible particles
b = Signal(SmallUInt(2))
r = Signal(SmallUInt(2))   # random coin for swapping

# -------------------------------- DYNAMICS
def swap():
    if r: a._ = b; b._ = a

swap = Sequence([Shuffle([r]),Rule(swap)])

diffuse = Sequence([Shift({a:[0,1],b:[0,-1]}),
                    swap,
                    Shift({a:[1,0],b:[-1,0]}),                   
                    swap])
# -------------------------------- RENDERING
white = OutSignal(UInt8)

def bw():  
    white._ = 255*(a+b)/2

# -------------------------------- COMMANDS
def init():
    """Make a square block in the center."""
    a[:,:] = 0; b[:,:] = 0
    a[40:60,40:60] = b[40:60,40:60] = 1
    r[:,:] = makedist(r.shape,[1,1])
init()
# -------------------------------- UI
ui = Console(Renderer(Rule(bw),white))
ui.bind("STEP",diffuse)
ui.bind("I",init)
# -------------------------------- INITIALIZE
ui.start()

