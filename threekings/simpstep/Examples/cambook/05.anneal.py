"""
Toffoli and Margolus, p. 41
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

def nine_sum():
    sum=N+S+E+W+NW+NE+SW+SE+p

    if(sum == 0):
        p._ = 0
    elif(sum == 1):
        p._ = 0
    elif(sum == 2):
        p._ = 0
    elif(sum == 3):
        p._ = 0
    elif(sum == 4):
        p._ = 1
    elif(sum == 5):
        p._ = 0
    elif(sum == 6):
        p._ = 1
    elif(sum == 7):
        p._ = 1
    elif(sum == 8):
        p._ = 1
    elif(sum == 9):
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
ui.bind("STEP",Rule(nine_sum))
ui.start()
