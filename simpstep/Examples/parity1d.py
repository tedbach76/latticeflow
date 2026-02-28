"""
One dimensional version of the parity automaton.
"""
from simp import *
X=50
initialize(size=[X])    # 1D grid
# -------------------------------- SIGNAL DECLARATION
c = Signal(SmallUInt(2))  # binary state
# -------------------------------- TRANSITION FUNCTION
l,r = c[-1],c[1]  # declare the neighbor directions
def parity(): 
    c._ = l^c^r  # ^ denotes 'xor', sets bit if 'l+c+r' is odd.
parity = Rule(parity)    
# -------------------------------- RENDERING
white = OutSignal(UInt8)

def bw():
    if not c: white._ = 255
bw_xt = XTRenderer(Rule(bw),white,time=X/2)
# -------------------------------- INITIALIZE
c[X/2]=1  # point seed in the center.
bw_xt.record()  # record the initial state
# -------------------------------- CONSOLE
ui = Console(bw_xt,mag=8)
#ui.setmag(8)  # set the magnification
ui.bind('STEP',parity)         # Specifies the 1D renderer.
ui.start()
