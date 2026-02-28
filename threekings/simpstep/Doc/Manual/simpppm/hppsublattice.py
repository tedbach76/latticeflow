"""
The HPP Lattice Gas.  We only simulate one of the two non-interacting
sublattices. 
"""
#-------------------------------- HEADER
from simp import *
#-------------------------------- GEOMETRY
X,Y = [100]*2
initialize(size=[X,Y],
           generator=[[1,1],
                      [0,2]])       # grid size
#-------------------------------- STATE
binary = SmallUInt(2)                 # make 4 binary signals for particles

signals = map(Signal,[binary]*4)
p0,p1,p2,p3 = signals

#-------------------------------- COLLISION 
def hpp():  # scatter at right angles on collision
    if ( (p0==p2) and (p1==p3) ):
        p0._ = p3;    p1._ = p2       # swap horizontally
        p3._ = p0;    p2._ = p1
hpp = Rule(hpp)

#-------------------------------- RENDERING
white = OutSignal(UInt8,generator=[1,1])

def intensity():   
    white[0,0]._ = (p0+p1+p2+p3)*255/4
    white[0,1]._ = 0

render_rule = Rule(intensity)
rend = Renderer(render_rule,outputs=white)

def intensity_brick():   
    white[0,0]._ = (p0+p1+p2+p3)*255/4
    white[0,1]._ = (p0+p1+p2+p3)*255/4

render_rule_brick = Rule(intensity_brick)
rend_brick = Renderer(render_rule_brick,outputs=white)

#-------------------------------- Declare the update
hpp_step = Sequence([
        Shift(kvdict( p0=[ 1, 0],
             p1=[ 0, 1],      p3=[ 0,-1],
                      p2=[-1, 0],
             render_rule=[0,-1],
             render_rule_brick=[0,-1])),
        hpp])

#-------------------------------- COMMANDS
# Randomize and set a `vacuum' in the center
import numarray
def init():
  for sig in signals:
      sig[:,:] = makedist(sig.shape,[1,1])
      ellipse_region = sig[Y*3/8:Y*5/8,X*3/8:X*5/8]
      arr = ellipse_region.value()
      numarray.putmask(arr,ellipsemask(ellipse_region),0)
      ellipse_region._ = arr

##-------------------------------- USER INTERFACE
#ui  = Console(rend)
#ui.bind("STEP",hpp_step)
#ui.bind("I",init)
##-------------------------------- INIT and RUN
#ui.start()

SeedRandom(1);init()
img = rend()
open("hpp%i.ppm"%0,"wb").write(arraytopnm(img))
for i in xrange(1,4):
    for j in xrange(X/8):
        hpp_step()
    img = rend()        
    open("hpp%i.ppm" % (i*X/8),"wb").write(arraytopnm(img))
open("hppzoom%i.ppm" % (i*X/8),"wb").write(arraytopnm(img[Y*7/16:Y*9/16,Y*7/16:Y*9/16]))

SeedRandom(1);init()
img = rend()
for i in xrange(1,4):
    for j in xrange(X/8):
        hpp_step()
img = rend_brick()        
open("hppbrick%i.ppm" % (i*X/8),"wb").write(arraytopnm(img))
open("hppbrickzoom%i.ppm" % (i*X/8),"wb").write(arraytopnm(img[Y*7/16:Y*9/16,Y*7/16:Y*9/16]))
# Write this one as a dummy for thhe makefile.
open("hppsublattice.ppm","wb").write(arraytopnm(img[Y*7/16:Y*9/16,Y*7/16:Y*9/16]))
