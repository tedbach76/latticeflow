"""  stochastic_greenberg_hastings.py

A stochastic version of the greenberg hastings automaton.
"""
#------------------------------------------------- HEADER
from simp import *            # Import simp and helpers

# ------------------------------------------------ GEOMETRY AND STATE VARIABLES
Y,X = 200,200
initialize(size=[Y,X])        # Declare an YxX square grid
c = Signal(SmallUInt(3))      # State variable (signal) declaration
READY=0; FIRE=1; REST=2;      # Mnemonics for state interpretations
binary = SmallUInt(2)
P,Q,R = map(Signal,[binary]*3)

# ------------------------------------------------ DYNAMICS
def stochastic_gh():                 # Function describing the transition rule
  if c==READY and P==1:
   if (c[-1,0]==FIRE or c[0, 1]==FIRE or # If north,east,south, or west firing.
       c[ 1,0]==FIRE or c[0,-1]==FIRE):  # (Subscripts indicate neigh coord)
      c._ = FIRE              # Transition to FIRE
  elif c==FIRE and Q==1: c._ = REST    # If firing transition to REST
  elif c==REST and R==1: c._ = READY   # If resting transition to READY

stochastic_gh_step = Sequence([Shuffle([P,Q,R]),
                               Rule(stochastic_gh)])
# ------------------------------------------------ RENDERING
red,green,blue = map(OutSignal,[UInt8]*3)

def tricolor():               # Function describing an appropriate color map
  if    c==READY:
      red._=green._=blue._ = 255 #   READY => white
  if    c==FIRE:
      red._   = 255           #   FIRE  => red
  elif  c==REST:
      blue._  = 255 #   REST  => blue

# Package tricolor into a rendering object  
tricolor_rend = Renderer(Rule(tricolor),(red,green,blue)) 

# ------------------------------------------------ RUN
c[:,:] = READY                 # Initialize all sites to READY
c[Y/2,X/2] = FIRE              # Set site in the center to FIRE

ui = Console(tricolor_rend)         # Initialize the console
ui.bind("STEP",stochastic_gh_step)  # Bind gh_step to the console's STEP event

# ------------------------------------------------ UI CONSOLE COMMANDS
def set_parameters(p_=.34,q_=.4,r_=.01):
  """Set the 'flamability', 'burn rate' and 'regrowth rate'  parameters.
  p,q,r (must be in range [0,1]"""
  global p,q,r
  p,q,r = p_,q_,r_
  P[:,:]  = makedist(P.shape,[1-p, p])
  Q[:,:]  = makedist(Q.shape,[1-q, q])
  R[:,:]  = makedist(R.shape,[1-r, r])
ui.bind("P",set_parameters)

def forrest_fire_burnout():
  """Run until the fire burns out. (regrowth rate = 0)"""
  R[:,:]      = 0
  c[:,:]      = READY
  c[Y/2,X/2]  = FIRE
  t = 0
  ui.render()
  while getdist(c[:,:].value(),0,3)[1]:
    for i in xrange(10):
      stochastic_gh_step()
      t+=1
    ui.issue("RENDER")      
  print 
  dist   = getdist(c[:,:].value(),0,3)
  p_burn = dist[2]/float(dist[0]+dist[1]+dist[2])*100
  print "Params: p=%f,q=%f,r=%f" % (p,q,r)
  print "burned out in ",t,"steps"  
  print "percentage burned=",p_burn
  R[:,:] = makedist(R.shape,[1-r, r])
ui.bind("B",forrest_fire_burnout)

def spark():
  """Make a single spark in the center"""
  c[Y/2,X/2] = FIRE
ui.bind("S",spark)

def initialize():
  set_parameters()
  c[:,:] = READY
  spark()
initialize()  
ui.bind("I",initialize)

# ------------------------------------------------ INITIALIZATION
ui.bind("STEP",stochastic_gh_step) # Bind gh_step to the console's STEP event
ui.start()                         # Start the interactive interface
