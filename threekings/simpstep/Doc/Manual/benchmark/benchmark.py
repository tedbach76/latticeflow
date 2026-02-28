""" Gather all several benchmark results for the current machine and
store it in a custom shelve database.

DB format:
  {testname : {hostname: results}}

    results are typically arranged as a list of tuples in which element 0 
    is the free variable and 1 the dependent.
"""

import socket, os, shelve
from  simp.test.programs import *

hostname = socket.gethostname()
# ================================================================ Open the DB
dbfname = "benchmark.db"
# Get the path to the current directory of this file.
# perhaps there's a better way to do it...
def dummy(): pass 
curdir = os.path.split(os.path.realpath(dummy.func_code.co_filename))[0]
dbfile = os.path.join(curdir,dbfname)

db = shelve.open(dbfile)
# ================================================================ FUNCTIONS
# store the results.
def store_results(testname,hostname,data):
   try:
       results = db[testname]
   except KeyError:
       results = {}
   results[hostname] = data
   db[testname] = results

# ================================================================ TESTS
if 0:
  # --------------------------------
  testname = "Parity size"
  # --------------------------------
  stepname="Pc"
  nsite = 2*(10**5)
  #rng=(10,21)
  rng=(10*2,22*2+1)
  prog = Parity
  
  print prog.__name__+"/"+stepname+"\tNsite\tsite/sec"
  data = []
  for i in apply(xrange,rng):
  #    nsite = int(math.e**(i/2.))
      nsite = int(2**(i/2.))
      instance = prog(stepname,nsite=nsite)
      site_sec = instance.benchmark()
  #    data.append((nsite,site_sec))
      data.append((nsite,site_sec))    
      print "\t%s\t%s" % (nsite,site_sec)
      
  store_results(testname,hostname,data)

# --------------------------------
# --------------------------------
def parity(testname,prog,randomize=1,stepname="Pc",nsite=2**20,rng=(0,21),\
           stepargs={}):
    data = []
    print "size",nsite
    print "Test:",testname
    print prog.__name__+"/"+stepname+"\tNneigh\ttime/sec"
    for nneigh in apply(xrange,rng):
        instance = prog(stepname,nsite=nsite,nneigh=nneigh,randomize=randomize,\
                        stepargs=stepargs)
        site_sec = instance.benchmark()
        print "\t%s\t%s" % (nneigh,1./site_sec) # seconds/site
    #    data.append((nneigh,site_sec))
        data.append((nneigh,1./site_sec))
    
    store_results(testname,hostname,data)

#parity("n neighbors, lug,Pc",ParameterizedParityLug,
#       stepname="Pc",nsite=200000,rng=(0,10))
#parity("n neighbors, lug,PcCodeGen",ParameterizedParityLug,
#       stepname="PcCodeGen",nsite=200000,rng=(0,10))

# parity("n neighbors, lug,Pc",ParameterizedParityLug,stepname="Pc")
# parity("n neighbors, lug,PcCodeGen",ParameterizedParityLug,stepname="PcCodeGen")
 
parity("n neighbors, lug,PcCodeGen_nolut",ParameterizedParityLug,\
       stepname="PcCodeGen",stepargs={"maxlutsize":0},rng=(0,21))

parity("n neighbors, lug,PcCodeGen_lut",ParameterizedParityLug,\
       stepname="PcCodeGen",stepargs={"maxlutsize":100},rng=(0,21))

# ,rng=(17,21)

#parity("n neighbors, lug",ParameterizedParityLug,stepname="Pc")
#parity("n neighbors, lug,nolut",ParameterizedParityLug,randomize=0)
#parity("n neighbors, vert",ParameterizedParityVertical)
# --------------------------------
db.close()
