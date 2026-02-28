import os, shelve, math, pyx

# ================================================================ Plot size
import pyx
def parity_size(hostname):
    data = db["Parity size"][hostname]
    for i in xrange(len(data)):
        data[i] = [math.log(data[i][0])/math.log(2),(data[i][1])/10**6]
#        print data[i]

    d = pyx.graph.data.list(data,x=0,y=1,title="Parity",addlinenumbers=0)
#    g = pyx.graph.graphxy(width=rng[1]-1,x=pyx.graph.axis.logarithmic())
    g = pyx.graph.graphxy(width=6) # rng[1]-1
    g.plot(d) # use x marks
    g.plot(d,[pyx.graph.style.line()]) # make lines
    #g.plot(graph.data.list([range(1,rng[1]),data],title="Parity"))
    fname = "%s.paritysize"%hostname
    g.writeEPSfile(os.path.join(curdir,fname))

#     #    from matplotlib import pylab  # Plotting library
#         import pylab
#     #    pylab.clf()
#         pylab.plot(data)
#         pylab.title('Number of neighbors vs performance')
#         pylab.ylabel('Number of sites per second')
#         pylab.xlabel('Number of neighbors')
#     #    pylab.xlim(0, X)
#     
#     #   pylab.show() # use this to show the plot
#         pylab.savefig(fname+".eps") # use this to generate a figure
#         pylab.close()  # close the window        
    

# ================================================================ Plot neighbor
  #plotneigh(db["n neighbors, lug,nolut"]["pm5.bu.edu"],"parityneighborsnolut")
  #plotneigh(db["n neighbors, vert"]["pm5.bu.edu"],"parityneighborsvert")
  #plotneigh(db["n neighbors, lug,Pc"]["eugenus"],"parityneighPc")
  #plotneigh(db["n neighbors, lug,PcCodeGen"]["eugenus"],"parityneighPcCodeGen")
  #plotneigh(db["n neighbors, vert"]["pm5.bu.edu"],"parityneighborsvert")

def plotneigh(hostname):
    data = db["n neighbors, lug,Pc"][hostname]
    for i in xrange(len(data)):
        data[i] = [data[i][0],(1./data[i][1])/10**6]
#        print data[i]

    fname = "%s.parityneighbors" % hostname
    d = pyx.graph.data.list(data,x=0,y=1,title="Parity",addlinenumbers=0)
    g = pyx.graph.graphxy(width=6)
    g.plot(d) # use x marks
    g.plot(d,[pyx.graph.style.line()]) # make lines
    g.writeEPSfile(os.path.join(curdir,fname))

# ================================================================ PC vs CodeGen
def codegen_pc_compare(hostname):
# -------------------------------- sec/site
    g = pyx.graph.graphxy(width=6)

    data = db["n neighbors, lug,Pc"][hostname]

    d = pyx.graph.data.list(data,x=0,y=1,title="Parity",addlinenumbers=0)
    g.plot(d) # use x marks
    g.plot(d,[pyx.graph.style.line()]) # make lines

    data = db["n neighbors, lug,PcCodeGen"][hostname]
    
    d = pyx.graph.data.list(data,x=0,y=1,title="Parity",addlinenumbers=0)
    g.plot(d) # use x marks
    g.plot(d,[pyx.graph.style.line()]) # make lines

    g.writeEPSfile(os.path.join(curdir,"%s.PcVsCodeGen"%hostname))
    
# # -------------------------------- MSite/sec
#     g = pyx.graph.graphxy(width=6)
# 
#     data = db["n neighbors, lug,Pc"][hostname]
#     for i in xrange(len(data)):
#         data[i] = [data[i][0],(1./data[i][1])/10**6]        
#         print data[i]
# 
#     d = pyx.graph.data.list(data,x=0,y=1,title="Parity",addlinenumbers=0)
#     g.plot(d) # use x marks
#     g.plot(d,[pyx.graph.style.line(),
#               pyx.graph.symbol.circle(scale=pyx.unit.v_cm*.1)]) # make lines
# 
#     data = db["n neighbors, lug,PcCodeGen"][hostname]
#     for i in xrange(len(data)):
#         data[i] = [data[i][0],(1./data[i][1])/10**6]
#         print data[i]
#     
#     d = pyx.graph.data.list(data,x=0,y=1,title="Parity",addlinenumbers=0)
#     g.plot(d) # use x marks
#     g.plot(d,[pyx.graph.style.line()]) # make lines
# 
#     g.writeEPSfile(os.path.join(curdir,"%s.PcVsCodeGen2"%hostname))








# ================================================================ LUT vs CG
smallcircle =  pyx.graph.style.symbol(\
    pyx.graph.style.symbol.circle,size=pyx.unit.v_cm*.05,
    symbolattrs=[pyx.deco.filled])
solidline = pyx.graph.style.line()
dashedline = pyx.graph.style.line(lineattrs=[pyx.style.linestyle.dashed])

def codegen_lut_compare(hostname,HZ):
    g = pyx.graph.graphxy(width=6,
                          key=pyx.graph.key.key(pos="tl"),
                          y=pyx.graph.axis.linear(title="Cycles per site"),
                          x=pyx.graph.axis.linear(title="Number of neighbors",
                                            min=0,max=20,
                                            parter=pyx.graph.axis.parter.linear(
                                             tickdist=[4,1],
                                             labeldist=[4]) )
                          )


    # LUT
    
    data = db["n neighbors, lug,PcCodeGen_lut"][hostname]
    for i in xrange(len(data)): data[i]=(data[i][0],data[i][1]/(1./HZ))
    d = pyx.graph.data.list(data,x=0,y=1,title="LUT",addlinenumbers=0)
    g.plot(d,[solidline,smallcircle])
    
    # CODE

    data = db["n neighbors, lug,PcCodeGen_nolut"][hostname]
    for i in xrange(len(data)): data[i]=(data[i][0],data[i][1]/(1./HZ))
    d = pyx.graph.data.list(data,x=0,y=1,title="Code",addlinenumbers=0)
    g.plot(d,[smallcircle,dashedline])    
    
    
#    g.plot(d,[pyx.graph.style.symbol(pyx.graph.style.symbol.square)])

    g.writeEPSfile(os.path.join(curdir,"%sCodeGenLutVsCode"%hostname))



# ================================================================ 
# ================================================================ Open the DB
# ================================================================
if __name__=="__main__":

  dbfname = "benchmark.db"
  # Get the path to the current directory of this file.
  # perhaps there's a better way to do it...
  def dummy(): pass 
  curdir = os.path.split(os.path.realpath(dummy.func_code.co_filename))[0]
  dbfile = os.path.join(curdir,dbfname)
  db = shelve.open(dbfile)
  

  codegen_lut_compare("eugenus",600e6)
  plotneigh("pm5.bu.edu")
  parity_size("pm5.bu.edu")
  codegen_pc_compare("eugenus")
