""" ising.py

tbach@bu.edu

Basic microcanonical Ising model
"""

from simp import *
Y,X = [200]*2
initialize(size=[Y,X])
# -------------------------------- State
p = Signal(SmallUInt(2))
# -------------------------------- Dynamics
def ising():
   sum = p[-1,0]+p[1,0]+p[0,-1]+p[0,1]
   if sum==2: # the energy balance is zero, so we are free to flip.
       p._ = not p
       
ising = Rule(ising,generator=[[1,1],
                              [0,2]])
step = Sequence([Shift({ising:[0,1]}),ising])
# -------------------------------- Dynamics
white = OutSignal(UInt8)

def bw():
  """Render the spin directly"""
  white._=p*255

bw = Renderer(Rule(bw),white)

def energy():
  """Energy difference between the left and right neighbors."""
  if p==0:
       white._ = 255-(p[0,1]+p[0,-1]+p[1,0]+p[-1,0])*(255/2)      
  if p==1:
       white._ = (p[0,1]+p[0,-1]+p[1,0]+p[-1,0])*(255/2)
energy = Renderer(Rule(energy),white)

ui = Console([bw,energy])
# -------------------------------- Commands
def SetMu(mu=.12):
  "Set mu, the proportion of states that are spin up"
  p[:,:] = makedist(p.shape,[1.-mu,mu])
ui.bind("M",SetMu)  

# -------------------------------- Commands
def Reverse():
  """Reverse the dynamics"""
  ising()
ui.bind("R",Reverse)
ui.bind("STEP",step)
SetMu()
ui.start()


  



