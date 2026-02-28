"""time_tunnel.py

Similar to the 'Time Tunnel' rule in the CAM book. 

Demonstrates how one can use SIMP to implement two copies of the same
dynamics and find the difference between two systems as they evolve
apart due to a difference in their initial conditions.  In it,
rule parameterization is used to make two different Rule objects---one
for each copy.

Essentially, this shows that the parity rule is linear.
"""

from simp import *
# -------------------------------- INITIALIZATION
initialize(size=[200,200])

# -------------------------------- STATE
a = Signal(SmallUInt(2))   # two signals, one for each copy
b = Signal(SmallUInt(2))

# -------------------------------- DYNAMICS
def parity():
    s._ = s^s[1,1]^s[1,-1]^s[-1,-1]^s[-1,1]

step = Sequence([Rule(parity,namespace=kwdict(s=a)), # Rule with s bound to a
                 Rule(parity,namespace=kwdict(s=b))]) # Rule with s bound to b

# -------------------------------- RENDERING
white = OutSignal(UInt8)

def bw():  # used to view a system
    if s: white._ = 255

def difference(): # used to view the difference between the systems
    if a!=b: white._ = 255
    
# -------------------------------- COMMANDS
def init():
    """Initialize A and B to a random configuration that differs in one bit."""
    a[:,:] = makedist(a.shape,[1,1]) # randomize a
    b[:,:] = a[:,:].value()  # copy a into b
    a[100,100] = 0   # make a and b different in one point
    b[100,100] = 1

init()    
# -------------------------------- UI
# Give the user three rendering options---view system a, system b,
# or the difference between the two.
ui = Console([Renderer(Rule(difference),white),       
                  Renderer(Rule(bw,namespace=kwdict(s=a)),white),
                  Renderer(Rule(bw,namespace=kwdict(s=b)),white)])
ui.bind("STEP",step)
ui.bind("I",init)

# -------------------------------- INITIALIZE
ui.start()

