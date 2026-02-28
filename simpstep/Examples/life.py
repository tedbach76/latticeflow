"""life.py

Conway's game of life with echo.
"""
from simp import *
# -------------------------------- GEOMETRY
Y,X = [300]*2
initialize(size=[Y,X])
# -------------------------------- STATE
binary = SmallUInt(2)
p,echo = map(Signal,[binary]*2) 
# -------------------------------- RULE
def life():
    sum = p[-1,-1]+p[-1,0]+p[-1,1] + \
          p[ 0,-1]+        p[ 0,1] + \
          p[ 1,-1]+p[ 1,0]+p[ 1,1]
    if p and sum<2 or sum>3:
        p._ = 0
    elif not p and sum==3:
        p._ = 1
    echo._ = p
# -------------------------------- RENDERING
red,green,blue = map(OutSignal,[UInt8]*3)

def echo_cm():
    if (not echo) and p:        red._ = 255
    elif echo and p:            green._ = 255
    elif echo and (not p):      blue._ = 255
# -------------------------------- UI

ui = Console(Renderer(Rule(echo_cm),(red,green,blue)))
ui.bind("STEP",Rule(life))
# -------------------------------- COMMANDS
def init():
    p[:,:] = makedist(p.shape,[1,1])
ui.bind("I",init)
# -------------------------------- RUN
init()
ui.start()
