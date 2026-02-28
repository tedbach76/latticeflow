""" simp.test.programs.py
Contains a number of SIMP programs that are wrapped into classes and used
for testing and cross validation.
"""
import math
def benchmark(stepname="Pc",stepargs={},rng=(20,26)):
    progs = [Hpp,HppPca,Parity]
#    progs = [Parity]    
    for prog in progs:
      print prog.__name__+"/"+stepname+"\tNsite\tsite/sec"
  #    for nsite in xrange(10**5,10**6,10**5):
#      for i in xrange(12,30):
      for i in apply(xrange,rng):
          nsite = int(math.e**(i/2.))
          instance = prog(stepname,nsite=nsite)
          site_sec = instance.benchmark()
          print "\t%s\t%s" % (nsite,site_sec)

def benchmark_neigh(stepname="Pc",stepargs={},nsite=2*(10**5),rng=(1,16)):
    """Benchmark using a CA whose size varies"""
#    progs = [ParameterizedParityLug,
#             ParameterizedParityHorizontal,
#             ParameterizedParityVertical]
    progs= [ParameterizedParityVertical]

    for prog in progs:
      print "size",nsite
      print prog.__name__+"/"+stepname+"\tNneigh\tsite/sec"
      for nneigh in apply(xrange,rng):
          instance = prog(stepname,nsite=nsite,nneigh=nneigh)
          site_sec = instance.benchmark()
          print "\t%s\t%s" % (nneigh,site_sec)


def cross_validate():
    steps = ["Reference","Pc","PcSamearray","PcThreaded","PcCodeGen"]
#    steps = ["pc","pc_multiprocessor"]
    nsite = 1000
    progs = [Hpp,HppPca,Parity,Parity3D]
    for prog in progs:
      for i in xrange(1,len(steps)):
          step0,step1 = steps[i-1:i+1]
          print "Cross validating %s and %s on %s:" % \
                   (step0,step1,prog.__name__),
          exp0 = prog(step0,nsite=nsite)
          exp1 = prog(step1,nsite=nsite)
          result=exp0.cross_validate(exp1)
          if not result:
              print "failed"
          else:
              print "success"

def validate_parity3d(stepname="Pc"):
    print "Validating %s on Parity3D" % stepname
    import results
    prog = Parity3D(stepname,nsite=27)
    prog.signals[0][:,:,:] = results.parity3dresults[0]
    for i in xrange(len(results.parity3dresults)):
        if not numarray.allclose(prog.signals[0].value(),
                                 results.parity3dresults[i]):
            print "failed iteration",i
            print prog.signals[0].value()!=results.parity3dresults[i]
            print "------"
            print prog.signals[0].value()
            return
        prog.update()
    print "Success!"

def validate_parity2d(stepname="Pc"):
    print "Validating %s on Parity2D" % stepname
    import results
    prog = Parity(stepname,nsite=9)
    prog.signals[0][:,:] = results.parity2dresults[0]
    for i in xrange(len(results.parity2dresults)):
        if not numarray.allclose(prog.signals[0].value(),
                                 results.parity2dresults[i]):
            print "failed iteration",i
            print prog.signals[0].value()!=results.parity2dresults[i]
            print "------"
            print prog.signals[0].value()
            return
        prog.update()
    print "Success!"
    
    

import time
class ProgramWrapper:
    """Base class for wrapping a SIMP program
       The following attributes should be defined:

       nsite : the actual number of sites affected by an update
       renderer : the renderer for the program
       update : the update step for the rule
    """
    def __init__(self,stepname,stepargs={},nsite=1024):
        """
        stepname : the step implementation to use
        nsite : the approximate size number of sites
        """
        self.stepname = stepname
        self.nsite = nsite

    def benchmark(self,warmup=10):
        """Do a benchmark that takes at least 2 seconds (for stability)
        return the number of sites/second
        """
        niter = 10
        done = 0
        for i in xrange(warmup): self.update()
        while not done:
            t0 = time.time()
            for i in xrange(niter):
              self.update()
            deltat = time.time() - t0
            if deltat>1:    done = 1
            else: niter*=2
#            print niter
        sites_sec = self.nsite*niter/deltat
        return sites_sec

    def cross_validate(self,other):
        """Returns 1 if the cross validation succeeded, 0 otherwise.
        other is another instance of the same experiment. Each program
        determines what cross validation means to it."""

    def signals_eq(self,other):
        for i in xrange(len(self.signals)):
            self_sig = self.signals[i]
            other_sig = other.signals[i]
            if not numarray.allclose(
                self_sig.GetCoset(),other_sig.GetCoset()):
                print "Positions are different"
                return 0
            elif not numarray.allclose(self_sig.value(),other_sig.value()):
                print "Values don't match"
                return 0
            return 1


from simp import import_locally

import math,numarray

def hpp():  # scatter at right angles on collision
    if ( (p0==p2) and (p1==p3) ):
        p0._ = p3;    p1._ = p2       # swap horizontally
        p3._ = p0;    p2._ = p1

class Hpp(ProgramWrapper):
    """Test/Benchmarking program based upon the HPP lattice gas"""
    def __init__(self,stepname,stepargs={},nsite=1000):
        simp = import_locally.import_copy("simp")
        self.simp = simp
        self.stepname = stepname
        self.nsite = int(math.sqrt(nsite))**2
        Y,X = [int(math.sqrt(nsite))*2]*2
        self.Y,self.X = Y,X
        simp.initialize(size=[Y,X],generator=[2,2],verbose=0,
                        stepname=stepname,stepargs=stepargs)
        binary = simp.SmallUInt(2)
        self.signals = map(simp.Signal,[binary]*4)
        p0,p1,p2,p3 =self.signals
        signal_dict = {"p0":p0,"p1":p1,"p2":p2,"p3":p3}
        self.update = simp.Sequence([
                            simp.Shift(simp.kvdict(p0=[ 1, 1],p1=[ 1,-1],  
                                              p3=[-1, 1],p2=[-1,-1])),
                            simp.Rule(hpp,namespace=signal_dict)])
                                    
        self.simp.SeedRandom(1)
        for sig in self.signals:
            sig[:,:] = simp.makedist(sig.shape,[1,1])

    def cross_validate(self,other):
        if not (self.X==other.X and self.Y==other.Y):
            raise ValueError, "Can't cross validate---not the same size"
        niter=10
        for i in xrange(niter):
            self.update()
            other.update()
            if not self.signals_eq(other):
                print "failed on iteration",i
                return 0
        return 1

def hpp_pca():                
   if ( (p[0,0]==p[1,1]) and (p[0,1]==p[1,0]) ):   # collision
       p[0,0]._ = p[0,1]; p[0,1]._ = p[0,0]  # particles swap horiz
       p[1,0]._ = p[1,1]; p[1,1]._ = p[1,0]   
   else:                                           # keep moving
       p[0,0]._ = p[1,1]; p[0,1]._ = p[1,0]  # particles swap diag
       p[1,0]._ = p[0,1]; p[1,1]._ = p[0,0]        
   
class HppPca(Hpp):
    """Test/Benchmarking program based upon the HPP lattice gas"""
    def __init__(self,stepname,stepargs={},nsite=1000):
        simp = import_locally.import_copy("simp")
        self.simp = simp
        self.stepname = stepname
        self.nsite = int(math.sqrt(nsite))**2
        Y,X = [int(math.sqrt(nsite))*2]*2
        self.Y,self.X = Y,X
        simp.initialize(size=[Y,X],verbose=0,
                        stepname=stepname,stepargs=stepargs)
        binary = simp.SmallUInt(2)
        self.signals = map(simp.Signal,[binary]*1)
        p = self.signals[0]
        signal_dict = {"p":p}
        hpp_rule = simp.Rule(hpp_pca,generator=[2,2],namespace=signal_dict) 
        self.update = simp.Sequence([
                    hpp_rule,
                    simp.Shift({hpp_rule:[1,1]})])
                                    
        self.simp.SeedRandom(1)
        for sig in self.signals:
            sig[:,:] = simp.makedist(sig.shape,[1,1])

def parity():                
  C._ = C^C[0,1]^C[1,0]^C[0,-1]^C[-1,0]

class Parity(Hpp):
    """Test/Benchmarking program 2D parity"""
    def __init__(self,stepname,stepargs={},nsite=1000):
        simp = import_locally.import_copy("simp")
        self.simp = simp
        self.stepname = stepname
        self.nsite = int(math.sqrt(nsite))**2
        Y,X = [int(math.sqrt(nsite))]*2
        self.Y,self.X = Y,X
        simp.initialize(size=[Y,X],verbose=0,
                        stepname=stepname,stepargs=stepargs)
        binary = simp.SmallUInt(2)
        self.signals = [simp.Signal(binary)]
        C = self.signals[0]
        signal_dict = {"C":C}
        self.update = simp.Rule(parity,namespace=signal_dict) 

        # Randomize the signals
        self.simp.SeedRandom(1)                                    
        for sig in self.signals: sig[:,:] = simp.makedist(sig.shape,[1,1])

def parity3d():                
  C._ = C^C[0,0,1]^C[0,1,0]^C[0,0,-1]^C[0,-1,0]^C[1,0,0]^C[-1,0,0]

class Parity3D(ProgramWrapper):
    """Test/Benchmarking program 3D parity"""
    def __init__(self,stepname,stepargs={},nsite=1000):
        simp = import_locally.import_copy("simp")
        self.simp = simp
        self.stepname = stepname
        
        Y,X,Z = [int(nsite**(1/3.))]*3
        self.Z,self.Y,self.X = Z,Y,X
        simp.initialize(size=[Z,Y,X],verbose=0,
                        stepname=stepname,stepargs=stepargs)
        self.nsite = X**3        
        binary = simp.SmallUInt(2)
        self.signals = [simp.Signal(binary)]
        C = self.signals[0]
        signal_dict = {"C":C}
        self.update = simp.Rule(parity3d,namespace=signal_dict) 

        # Randomize the signals
        self.simp.SeedRandom(1)                                    
        for sig in self.signals: sig[:,:,:] = simp.makedist(sig.shape,[1,1])

    def cross_validate(self,other):
        if not (self.X==other.X and self.Y==other.Y and self.Z==other.Z):
            raise ValueError, "Can't cross validate---not the same size"
        niter=10
        for i in xrange(niter):
            self.update()
            other.update()
            if not self.signals_eq(other):
                print "failed on iteration",i
                return 0
        return 1
                

def ParameterizedParityLug_parity():                
    C._ = N0^N1^N2^N3^N4^N5^N6^N7^N8^\
          N9^N10^N11^N12^N13^N14^N15^N16^\
          N17^N18^N19^N20

class ParameterizedParityLug(Hpp):
    """Test/Benchmarking program based upon parity with an arbitrary
    number of neighbors.

    Pattern:
        N9       N14     N10     N9  N18  N14 N19 N10    
            N5   N2  N6          N17 N5   N2  N6  N20    
        N13 N1   N0  N3  N15     N13 N1   N0  N3  N15                 
            N8   N4  N7          N24 N8   N4  N7  N21    
        N12      N16     N11     N12 N23  N16 N22 N11    
    """
    neighbors = [[0,0],[0,-1],[-1,0],[0,1],[1,0],
                       [-1,-1],[-1,1],[1,1],[1,-1],
                       [-2,-2],[-2,2],[2,2],[2,-2],
                       [0,-2],[-2,0],[0,2],[2,0],
                       [-1,-2],[-2,-1],[-2,1],[-1,2]]
                
    def __init__(self,stepname,stepargs={},nsite=1000,nneigh=10,randomize=1):
        simp = import_locally.import_copy("simp")
        self.simp = simp
        self.stepname = stepname
        self.nsite = int(math.sqrt(nsite))**2
        Y,X = [int(math.sqrt(nsite))]*2
        self.Y,self.X = Y,X
        simp.initialize(size=[Y,X],verbose=0,
                        stepname=stepname,stepargs=stepargs)
        binary = simp.SmallUInt(2)
        C = simp.Signal(binary)
        self.signals = [C]

        # construct the namespace for the rule N0...N16
        namespace = {"C":C}
        for i in xrange(0,nneigh):
            namespace["N%i"%i] = C[self.neighbors[i]]
        for i in xrange(nneigh,len(self.neighbors)):
            namespace["N%i"%i] = 0 # use zeros for everything else

        self.update = simp.Rule(ParameterizedParityLug_parity,
                                namespace=namespace) 

        # Randomize the signals
        self.simp.SeedRandom(1)
        if randomize:
            for sig in self.signals: sig[:,:] = simp.makedist(sig.shape,[1,1])
        else:
            for sig in self.signals: sig[:,:] = 0

class ParameterizedParityHorizontal(ParameterizedParityLug):
    """
    Pattern: 
            ... N3 N1 N0 N2 N4 ....
     
    """
    neighbors = [[0,0],[0,-1],[0,1],[0,-2],[0,2],[0,-3],[0,3],[0,-4],[0,4],
                 [0,-5],[0,5],[0,-6],[0,6],[0,-7],[0,7],[0,-8],[0,8],
                 [0,-9],[0,9],[0,-10],[0,10]]

class ParameterizedParityVertical(ParameterizedParityLug):
    """
    Pattern:          ..
                      N1
                      N0 
                      N2
                      ..
    """
    neighbors = [[0,0],[-1,0],[1,0],[-2,0],[2,0],[-3,0],[3,0],[-4,0],[4,0],
                 [-5,0],[5,0],[-6,0],[6,0],[-7,0],[7,0],[-8,0],[8,0],
                 [-9,0],[9,0],[-10,0],[10,0]]                 
    
