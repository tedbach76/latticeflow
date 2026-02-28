""" The basic Greenberg Hastings automaton running at the SIMP console
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

ui = Console(tricolor_rend)    # Instantiate a console called "ui"
                               # and initialize its renderer
ui.bind("STEP",gh_rule)        # Bind gh_rule to the console's STEP event
ui.start()                     # Start the interactive interface
