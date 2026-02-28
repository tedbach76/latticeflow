from simp import *

#---------------------------------------------------------GEOMETRY AND STATE
X								   = 0x100
initialize(size=[X])

bit = SmallUInt(2)
q   = Signal(bit)				# this site
p   = Signal(bit)					# 2nd order

#-------------------------------------------------------------------DYNAMICS
'''
def erg():
  sum = q[-2]+q[-1]+q[1]+q[2]
  if p: return 4-sum
  else: return sum
'''

def scarf():
  sum = p[-2]+p[-1]+p[+1]+p[+2]
  if p: erg = 4-sum
  else: erg = sum
  if (erg==2):  q._ = 1^p
  p._ = q

scarf = Rule(scarf)
#------------------------------------------------------------------RENDERING
declarecolors()
def krgb():
  if q and p: red._ = 255
  else:
    if q: green._ = 255
    if p: blue._ = 255

krgb = XTRenderer(Rule(krgb),rgb,time=-X)
ui = Console(krgb)

#--------------------------------------------------------------USER COMMANDS
def Braid():
  """Initialize with a braid-generating initial state"""
  q[:]	= 0
  p[:]	= 0
  q[X/2-3:X/2+3] = 1

def Randomize():
  """Generate random initial configuration."""
  q[:]	= makedist(q.shape,[1,1])
  q[:]	= makedist(p.shape,[1,1])

ui.bind('STEP',scarf)
ui.bind('B',Braid)
ui.bind('R',Randomize)

#----------------------------------------------------------------------START
Randomize()
ui.start()
