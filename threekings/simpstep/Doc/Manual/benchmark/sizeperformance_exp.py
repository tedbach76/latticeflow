""" Plot the dependence of the performance on the number of neighbors.
"""
from  simp.test.programs import *


fname = "sizeperformanceexp"
stepname="Pc"
nsite = 2*(10**5)

rng=(14,28)

data = []

prog = Parity
print prog.__name__+"/"+stepname+"\tNsite\tsite/sec"
for i in apply(xrange,rng):
    nsite = int(math.e**(i/2.))
    instance = prog(stepname,nsite=nsite)
    site_sec = instance.benchmark()
#    data.append((nsite,site_sec))
#    data.append((math.log(nsite)/math.log(2),site_sec))
    data.append((nsite,site_sec))    
    print "\t%s\t%s" % (nsite,site_sec)


#  print "size",nsite
#  prog = ParameterizedParityLug
#  prog = ParameterizedParityVertical
#  print prog.__name__+"/"+stepname+"\tSize\tsite/sec"
#  for nneigh in apply(xrange,rng):
#      instance = prog(stepname,nsite=nsite,nneigh=nneigh)
#      site_sec = instance.benchmark()
#      print "\t%s\t%s" % (nneigh,site_sec)
#      data.append((nneigh,site_sec))
#  #    data.append(site_sec)

#data = [[1,1],[2,2],[3,3]] # dummy data

PYX = 1
if PYX:
    import pyx
    d = pyx.graph.data.list(data,x=0,y=1,title="Parity",addlinenumbers=0)
    g = pyx.graph.graphxy(width=8,x=pyx.graph.axis.logarithmic())
#    g = pyx.graph.graphxy(width=7) # rng[1]-1
    g.plot(d) # use x marks
    g.plot(d,[pyx.graph.style.line()]) # make lines
    #g.plot(graph.data.list([range(1,rng[1]),data],title="Parity"))
    g.writeEPSfile(fname)
else:
#    from matplotlib import pylab  # Plotting library
    import pylab
#    pylab.clf()
    pylab.plot(data)
    pylab.title('Number of neighbors vs performance')
    pylab.ylabel('Number of sites per second')
    pylab.xlabel('Number of neighbors')
#    pylab.xlim(0, X)

#   pylab.show() # use this to show the plot
    pylab.savefig(fname+".eps") # use this to generate a figure
    pylab.close()  # close the window        
    





