# -------------------------------- PARAMETERS
outfile = "Diffusion1DGrid.ppm"
X = 4
TIME = 5

from simp import *
#-------------------------------- GOMETRY, STATE, DYNAMICS
initialize(size=[X],generator=[[2]],stepname="Reference")
l     = Signal(SmallUInt(2))   # right-moving signal
r     = Signal(SmallUInt(2))   # left-moving signal
coin  = Signal(SmallUInt(2))   # random variable

def swap_randomly(): # change inertia if 'coin' is 1
   if coin: l._ = r; r._ = l

dynamics = Sequence([Shift(kvdict(l=[-1],r=[1])),
                     Shuffle([coin]),
                     Rule(swap_randomly)])
                     
# -------------------------------- INITIALIZATION
SeedRandom(1)  # for repeatability
coin[:] = [1,0]

l[:] = 0; r[:] = 0; 
l[X/2] = 1;
# -------------------------------- RENDERING
white = OutSignal(UInt8,generator=[[1]])  # declare colors on the sublattice

def bw():
    white[0]._ = (2-(l+r))*127 
    white[1]._ = 0 # light black
bw_rule = Rule(bw,generator=[[2]])
bw_rend = XTRenderer(bw_rule,white,time=-TIME)
dynamics = Sequence([dynamics,Shift({bw_rule:[1]})])
# -------------------------------- RECORD 
bw_rend.record()
for i in xrange(TIME-1):
    dynamics()
    bw_rend.record()

arr = bw_rend()
rescaled_arr = magnify2d(arr,mag=21,grid=1)
rescaled_arr[:,0] = 0; rescaled_arr[0,:] = 0
open(outfile,"wb").write(arraytopnm(rescaled_arr))

    


