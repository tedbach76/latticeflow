"""
Toffoli and Margolus, p. 38
"""

from simp import *
from random import randint

X,Y = [200]*2
initialize(size=[Y,X])

# -------------------------------- STATE
p = Signal(SmallUInt(2))

# -------------------------------- DYNAMICS
N,S,E,W = p[-1,0],p[1,0],p[0,1],p[0,-1]

def diamonds():
    p._        = N|S|E|W|p

# --------------------------------
white = OutSignal(UInt8)

def bw():
    white._ = p*255
rend = Renderer(Rule(bw),outputs=white)

# -------------------------------- INITIALIZE STATE
p[:,:]     = 0
#p[Y/2,X/2] = 1
p[randint(0,200), randint(0,200)] = 1
p[randint(0,200), randint(0,200)] = 1
p[randint(0,200), randint(0,200)] = 1
p[randint(0,200), randint(0,200)] = 1
p[randint(0,200), randint(0,200)] = 1
p[randint(0,200), randint(0,200)] = 1
p[randint(0,200), randint(0,200)] = 1
p[randint(0,200), randint(0,200)] = 1
p[randint(0,200), randint(0,200)] = 1
p[randint(0,200), randint(0,200)] = 1
p[randint(0,200), randint(0,200)] = 1
p[randint(0,200), randint(0,200)] = 1
p[randint(0,200), randint(0,200)] = 1

# -------------------------------- CONSOLE
ui = Console(rend)
ui.bind("STEP",Rule(diamonds))
ui.start()
