"""
Benchmarking utilities for gathering performance on the IBM P690 machines.

python parallelbenchmark.py <nsite> <np_low> <np_high>
    Runs a test range from np_low up to, but not including np_high
  
"""


from  simp.test.programs import *
import gc, sys

stepname = "PcThreaded"


nsite,np_low,np_high = map(int,sys.argv[2:]) # 2**22 

for nthread in xrange(np_low,np_high):
    instance = Parity("PcThreaded",stepargs={"nthread":nthread},nsite=nsite)
    site_sec = instance.benchmark(tmin=1)
    print "\t%s\t%s" % (nthread,1./site_sec) # seconds/site
    data.append((nthread,1./site_sec))
    del instance
    gc.collect()

print data

# example
# results = [(1, 4.5405408855003772e-08), (2, 2.3122154857446727e-08), (3, 1.5616191717526818e-08), (4, 1.1866784177527735e-08), (5, 9.672112355474383e-09), (6, 8.1970753740279182e-09), (7, 7.1566461201655323e-09), (8, 6.4575800706734297e-09)]

