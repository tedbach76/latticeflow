"""
2D parity celluar automaton
"""
from simp import *
X,Y = [200]*2
initialize(size=[Y,X])
# -------------------------------- STATE
p = Signal(SmallUInt(2))
# -------------------------------- DYNAMICS

N,S,E,W = p[-1,0],p[1,0],p[0,1],p[0,-1]

def parity():
    p._        = N^S^E^W^p
# --------------------------------
white = OutSignal(UInt8)

def bw():
    white._ = p*255
rend = Renderer(Rule(bw),outputs=white)
# -------------------------------- INITIALIZE STATE
p[:,:]     = 1
p[Y/2,X/2]     = 0
# -------------------------------- CONSOLE
ui = Console(rend)
ui.bind("STEP",Rule(parity))
ui.start()
