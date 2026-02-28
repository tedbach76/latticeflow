"""
Toffoli and Margolus, p. 43
"""

from simp import *
from random import randint

X,Y = [200]*2
initialize(size=[Y,X])

# -------------------------------- STATE
p = Signal(SmallUInt(2))

# -------------------------------- DYNAMICS
N,S,E,W = p[-1,0],p[1,0],p[0,1],p[0,-1]

def banks():
    sum=N+S+E+W

    if(sum == 2):    # corner?
        if(N!=S):    # if N and S are not equal it's a corner
            p._ = 0  # p is either already zero or should be set to zero
    elif(sum == 3):
        p._ = 1
    elif(sum == 4):
        p._ = 1

# --------------------------------
white = OutSignal(UInt8)

def bw():
    white._ = p*255
rend = Renderer(Rule(bw),outputs=white)

# -------------------------------- INITIALIZE STATE
import numarray
p[:,:] = makedist(p.shape,[.5,.5])

# -------------------------------- CONSOLE
ui = Console(rend)
ui.bind("STEP",Rule(banks))
ui.start()
