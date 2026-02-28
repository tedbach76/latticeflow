"""
One dimensional diffusion.
"""

INTERACTIVE = 0
from simp import *
#-------------------------------- GOMETRY AND STATE
X = 50; TIME = 50
initialize(size=[X])                         
l     = Signal(SmallUInt(2),[2])   # right-moving signal
r     = Signal(SmallUInt(2),[2])   # left-moving signal
coin  = Signal(SmallUInt(2),[2])   # random variable
coin[:] = makedist(coin.shape,[1,1])

#-------------------------------- Dynamics
def swap_randomly(): # change inertia if 'coin' is 1
   if coin: l._ = r; r._ = l
   
white = OutSignal(UInt8)

def bw():
    white._ = (2-(l+r))*127
bw = Rule(bw,[2])
rend = XTRenderer(bw,outputs=(white,white,white),time=TIME)

dynamics = Sequence([Shift({l:[-1],r:[1]}),
                     Shift({bw:[1]}),
                     Shuffle([coin]),
                     Rule(swap_randomly,[2])])

r[X/4:X*3/4] = 1
l[X/4:X*3/4] = 1
#-------------------------------- CONSOLE USER INTERFACE
ui  = Console(rend)
ui.bind("STEP",dynamics)
ui.start()
