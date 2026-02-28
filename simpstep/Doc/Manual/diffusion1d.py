"""
Uses matplotlib to generate a histogram of particle positions and an image
showing diffusion. 

"""

INTERACTIVE = 0
from simp import *
#-------------------------------- GOMETRY AND STATE
X = 40
TIME = 40
initialize(size=[X])                         
l     = Signal(SmallUInt(2))   # right-moving signal
r     = Signal(SmallUInt(2))   # left-moving signal
coin  = Signal(SmallUInt(2))   # random variable
coin[:] = makedist(coin.shape,[1,1])

def swap_randomly(): # change inertia if 'coin' is 1
   if coin: l._ = r; r._ = l
   
dynamics = Sequence([Shift(kvdict(l=[-1],r=[1])),Shuffle([coin]),
                     Rule(swap_randomly)])
declarecolors()
def bw():
    white._ = (2-(l+r))*127

rend = XTRenderer(Rule(bw),outputs=grayscale,time=-TIME)



if INTERACTIVE:
  r[X/4:X*3/4] = 1
  l[X/4:X*3/4] = 1
  #-------------------------------- CONSOLE USER INTERFACE
  ui  = Console(rend)
  ui.bind("STEP",dynamics)
  ui.start()

else:
  # Generate an image showing diffusion strobed every tenth step.
  r[X*3/8:X*5/8] = 1
  l[X*3/8:X*5/8] = 1
  for i in xrange(TIME-1):
      rend.record()      
      for i in xrange(4):  dynamics()
  rend.record()
  arr = rend()
  rescaled_arr = magnify2d(arr,magnification=6,grid=1) # magnify with grid lines
  # output image file
  open("naivediffusionblock.ppm","wb").write(arraytopnm(rescaled_arr)) 
  
  # Generate an image showing diffusion on two particles
  r[:] = 0; l[:] = 0
  r[X/2] = 1; l[X/2] = 1
  for i in xrange(TIME-1):
      rend.record()
      dynamics()
  rend.record()
  arr = rend()
  rescaled_arr = magnify2d(arr,magnification=6,grid=1) # magnify with grid lines
  # output image file
  open("naivediffusionparticles.ppm","wb").write(arraytopnm(rescaled_arr)) 
  
  # Generate the statistics of this diffusion rule
  Ntrial = 1000; time = 20

  import numarray
  from matplotlib import pylab  # Plotting library
  histo = numarray.zeros(X) # histogram
  bins = numarray.arange(X) # integer bins for the histogram
  positions = []
  def plotit(): # plot the data
    pylab.clf()
    pylab.hist(positions, bins) # plot the histogram as we go...
    pylab.title('Particle distribution after %i steps (%i trials)'% (time,i+1))
    pylab.ylabel('Number of particles')
    pylab.xlabel('$X$')                    
    pylab.xlim(0, X)
  for i in xrange(Ntrial):
      coin[:] = makedist(coin.shape,[1,1])
      r[:]= 0; l[:]= 0
      r[X/2]= 1; l[X/2]= 1
      for j in xrange(time): dynamics()
      for indx in numarray.nonzero(r[:].value()):
          positions.extend(indx)
      for indx in numarray.nonzero(l[:].value()):
          positions.extend(indx)          
      if not i%100: plotit()

  plotit()
#   pylab.show() # use this to show the plot
  pylab.savefig("naivediffusionhistogram.ps") # use this to generate a figure
  pylab.close()  # close the window        
      
      
      
