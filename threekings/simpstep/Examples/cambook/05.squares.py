"""
Toffoli and Margolus, p. 37
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

def squares():
    p._        = N|S|E|W|NW|NE|SW|SE|p

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
ui.bind("STEP",Rule(squares))
ui.start()
