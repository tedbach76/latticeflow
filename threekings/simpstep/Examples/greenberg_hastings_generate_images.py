""" Greenberg Hastings example that captures four rendering snapshots
"""

#------------------------------------------------- HEADER
from simp import *            # Import simp and helpers
# ------------------------------------------------ GEOMETRY AND STATE VARIABLES
Y,X = 200,200
initialize(size=[Y,X])        # Declare an YxX square grid
c = Signal(SmallUInt(3))      # State variable (signal) declaration
READY=0; FIRE=1; REST=2;      # Mnemonics for state interpretations
# ------------------------------------------------ DYNAMICS
def gh():                     # Function describing the transition rule
  if c==READY:
   if (c[-1,0]==FIRE or c[0, 1]==FIRE or # If north,east,south, or west firing.
       c[ 1,0]==FIRE or c[0,-1]==FIRE):  # (Subscripts indicate neigh coord)
      c._ = FIRE              # Transition to FIRE
  elif c==FIRE: c._ = REST    # If firing transition to REST
  elif c==REST: c._ = READY   # If resting transition to READY

# ------------------------------------------------ RENDERING
red,green,blue = map(OutSignal,[UInt8]*3)

def tricolor():               # Function describing an appropriate color map
  if    c==READY:
      red._=green._=blue._ = 255 #   READY => white
  if    c==FIRE:
      red._   = 255           #   FIRE  => red
  elif  c==REST:
      blue._  = 255 #   REST  => blue

gh_rule = Rule(gh)

# Package tricolor into a rendering object  
tricolor_rend = Renderer(Rule(tricolor),(red,green,blue)) 
## ------------------------------------------------ RUN
c[:,:] = READY                 # Initialize all sites to READY
c[Y/2,X/2] = FIRE              # Set site in the center to FIRE

for i in range(4):
    img_arr = tricolor_rend() # get an array containing the current state
    open("gh%i.ppm" % i,"wb").write(arraytopnm(img_arr)) # save to file
    gh_rule() # do a step of the dynamics
