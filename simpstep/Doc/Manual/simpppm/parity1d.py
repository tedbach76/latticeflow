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
bw = XTRenderer(Rule(bw),white,time=X/2)
# -------------------------------- INITIALIZE
c[X/2]=1  # point seed in the center.
bw.record()  # record the initial state

for i in xrange(X/2-1):
    parity()
    bw.record()

#outfile = "parity1d24.ppm"
outfile = "parity1d.ppm"
arr = bw()
rescaled_arr = magnify2d(arr,mag=4,grid=1)
open(outfile,"wb").write(arraytopnm(rescaled_arr))

