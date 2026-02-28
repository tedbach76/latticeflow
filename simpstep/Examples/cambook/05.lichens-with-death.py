"""
Toffoli and Margolus, p. 40
"""

from simp import *
from random import randint

X,Y = [200]*2
initialize(size=[Y,X])

# -------------------------------- STATE
p = Signal(SmallUInt(2))

# -------------------------------- DYNAMICS
N,S,E,W = p[-1,0],p[1,0],p[0,1],p[0,-1]
NW, NE, SW, SE = p[-1,-1], p[-1,1], p[1,-1], p[1,1]

def eight_sum():
    sum=N+S+E+W+NW+NE+SW+SE

    if(sum == 3):
        p._ = 1
    elif(sum == 4):
        p._ = 0
    elif(sum == 7):
        p._ = 1
    elif(sum == 8):
        p._ = 1

# --------------------------------
white = OutSignal(UInt8)

def bw():
    white._ = p*255
rend = Renderer(Rule(bw),outputs=white)

# -------------------------------- INITIALIZE STATE
import numarray
p[:,:] = makedist(p.shape,[0,0])
ellipse_region = p[Y*3/8:Y*5/8,X*3/8:X*5/8]
arr = ellipse_region.value()
numarray.putmask(arr,ellipsemask(ellipse_region),makedist(p.shape,[1-.25, .25]))
ellipse_region._ = arr

# -------------------------------- CONSOLE
ui = Console(rend)
ui.bind("STEP",Rule(eight_sum))
ui.start()
