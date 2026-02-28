"""
Record 25 time steps of the one-dimensional version of the parity automaton
and store the result in 'parity1d_record.ppm'
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
# -------------------------------- Record 25 time steps
bw_xt.record()  # record the initial state
for i in xrange(24): # Do 24 updates
   parity() # call the rule (does a step of the dynamics)
   bw_xt.record() # record the state
arr = bw_xt()  # get the rendering output array 
rescaled_arr = magnify2d(arr,scale=8,grid=1) # magnify with grid lines
open("out.ppm","wb").write(arraytopnm(rescaled_arr)) # output image file
