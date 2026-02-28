from simp import *
#-------------------------------- GOMETRY AND STATE
X = 10
TIME = 10
initialize(size=[X],generator=[[2]])
l     = Signal(SmallUInt(2))   # right-moving signal
r     = Signal(SmallUInt(2))   # left-moving signal
coin  = Signal(SmallUInt(2))   # random variable


SeedRandom(2)
coin[:] = makedist(coin.shape,[1,1])

def swap_randomly(): # change inertia if 'coin' is 1
   if coin: l._ = r; r._ = l


white = OutSignal(UInt8,generator=[[1]])
def bw1():
    white._ = (2-(l+r))*127
    white[1]._ = 230

def bw2():
    white._ = (2-(l+r))*127
    white[1]._ = (2-(l+r))*127    

bw_sub1 = Rule(bw1)
bw_sub1no = Rule(bw1)
bw_sub2 = Rule(bw2)

dynamics = Sequence([Shift(kvdict(l=[-1],r=[1],bw_sub1=[1],bw_sub2=[1])),
                     Shuffle([coin]),
                     Rule(swap_randomly)
                     ])

white_samelat = OutSignal(UInt8)
def bw():
  white_samelat._ = (2-(l+r))*127



rend_sub1 = XTRenderer(bw_sub1,outputs=white,time=-TIME)
rend_sub1no = XTRenderer(bw_sub1no,outputs=white,time=-TIME)
rend_sub2 = XTRenderer(bw_sub2,outputs=white,time=-TIME)
rend3 = XTRenderer(Rule(bw),outputs=white_samelat,time=-TIME)

renderers = rend_sub1,rend_sub1no,rend_sub2,rend3

l[:] = 0; r[:] = 0; 
l[X/2] = 1;


map(lambda x: x.record(),renderers)
for i in xrange(X-1):
    dynamics()
    map(lambda x: x.record(),renderers)
    

import numarray


#arr = numarray.zeros([X,X],type=numarray.UInt8)
#arr[:,:]=255
arr = rend_sub1()
rescaled_arr = magnify2d(arr,mag=12,grid=1)
open("diffusionrend1.ppm","wb").write(arraytopnm(rescaled_arr))
# Write this one as a dummy file.
open("diffusion1d2.ppm","wb").write(arraytopnm(rescaled_arr)) 

arr = rend_sub1no()
rescaled_arr = magnify2d(arr,mag=12,grid=1)
open("diffusionrend1no.ppm","wb").write(arraytopnm(rescaled_arr)) 

#arr[:,:]=255
arr = rend_sub2()
rescaled_arr = magnify2d(arr,mag=12,grid=1)
open("diffusionrend2.ppm","wb").write(arraytopnm(rescaled_arr)) 


arr = rend3()
rescaled_arr = magnify2d(arr,mag=12,grid=1)
open("diffusionrend3.ppm","wb").write(arraytopnm(rescaled_arr)) 

    

