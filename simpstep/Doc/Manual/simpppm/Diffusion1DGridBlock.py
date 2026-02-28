# -------------------------------- PARAMETERS
outfile = "Diffusion1DGridBlock.ppm"
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
red,green,blue = map(lambda x: apply(OutSignal,x),[(UInt8, [[1]] )]*3)

def block():
    if l: red[0]._=255;
    else: red[0]._ = green[0]._ = blue[0]._ = 255
    if r: blue[1]._ = 255;
    else: red[1]._ = green[1]._ = blue[1]._ = 255 # white
    
#    blue[0]._ = 255
#    red[0]._ = green[0]._ = 255*(1-l)
#
#    green[1]._ = 230
#    red[1]._ = blue[1]._ = 230*(1-r)
    
#    red[0]._ = green[0]._ = blue[0]._ = 255*(1-l)
#    red[1]._ = green[1]._ = blue[1]._ = 230*(1-r)

#    red[0]._ = green[0]._ = blue[0]._ = (2-(l+r))*127
#    red[1]._ = green[1]._ = blue[1]._ = 230

#    white[0]._ = (2-(l+r))*127

#    if r: blue[1]._=255
#    else: red[1]._ = green[1]._ = blue[1]._ = 255

block_rule = Rule(block,generator=[[2]])
block_rend = XTRenderer(block_rule,(red,green,blue),time=-TIME)
dynamics = Sequence([dynamics,Shift({block_rule:[1]})])

# -------------------------------- RECORD 
block_rend.record()
for i in xrange(TIME-1):
    dynamics()
    block_rend.record()

arr = block_rend()
rescaled_arr = magnify2d(arr,mag=21,grid=1)
rescaled_arr[:,0,:] = 0; rescaled_arr[0,:,:] = 0
open(outfile,"wb").write(arraytopnm(rescaled_arr))

    


