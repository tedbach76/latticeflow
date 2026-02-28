"""
SIMP Automatic testing module.

usage:

import simp.test

simp.test.testall()

"""

#import test_simp
#test = test_simp.test
import numarray as _na
import unittest

import sysinfo
import simp.import_locally

import sys
# The following search path is useful when building test versions of python
sys.path.append("../../lib/python")


class TestSimpInitialize(unittest.TestCase):
   
   def setUp(self):
       self.simp = simp.import_locally.import_copy("simp")

   def testBasic(self):
      self.simp.initialize(size=[100],stepname="Reference")

   def testNegative(self):
      try:
          self.simp.initialize(size=[-100],stepname="Reference")
          self.assert_(0,"Didn't find problem with negative size")
      except: pass

     
   def testNotHNF(self):
      def call():
          self.simp.initialize(size=[100,100],generator=[[1,2],[1,3]],
                               stepname="Reference")
      self.assertRaises(ValueError,call)

   def testWrongSize(self):
      def call():
        self.simp.initialize(size=[100,100],generator=[[1,2],[0,3]],
                             stepname="Reference")
      self.assertRaises(ValueError,call)

   def testSignalDeclaration(self):
      self.simp.initialize(size=[100,100],stepname="Reference")
      a = self.simp.Signal(self.simp.SmallUInt(2))
      sl = a[1,1]

   def testStepInterface(self):
      import numarray
      simp = self.simp
      self.simp.initialize(size=[100,100],stepname="Reference")
      
      a = simp.Signal(simp.SmallUInt(2))
      b = simp.Signal(simp.SmallUInt(2))
      c = simp.Signal(simp.SmallUInt(2))
      
      def foo():
          a = b^c[-1,1]
          
      # construct each type of STEP object...
#      lutrule = simp.LutRule(numarray.zeros([2,2,1]),[a,b],[c])
      rd = simp.Read(simp.subscr[1:3,2:10],a)
      wr = simp.Write(simp.subscr[1:3,2:10],b)
      shift = simp.Shift(simp.kvdict(a=[1,1],b=[2,3],c=[2,2]))
      put = simp.SetCoset(simp.kvdict(a=[1,1],b=[2,3],c=[2,2]))
      readpos = simp.GetCoset(a)
      Shuffle = simp.Shuffle([a,b,c])
      sequence = simp.Sequence([rd,wr,shift,put,readpos,Shuffle])
       
      
         


# ---------------------------------------------------------------- TESTING
import sysinfo

__bench_test__ = ["hpp.py","life.py"]
   
import simp.geom
import programs
import simp.rule_analysis
import doctest, simp.latticearray
def test():
   print "Testing SIMP"
   print """Please email results to tbach@bu.edu.
             Especially if there are problems !!!! """
   
   print "INFO: "
   print sysinfo.info
   print "GEOMETRY: "
   simp.geom.test()
   print "SIMP BASICS:"
   suite = unittest.makeSuite(TestSimpInitialize,'test')
   unittest.TextTestRunner(verbosity=0).run(suite)
   doctest.testmod(simp.latticearray)
   print "RULE ANALYSIS:"
   simp.rule_analysis.test()
   print "VALIDATE REFERENCE IMPLEMENTATION"
   programs.validate_parity2d(stepname="Reference")      
   programs.validate_parity3d(stepname="Reference")
   print "CROSS VALIDATE STEP IMPLEMENTATIONS:"
   programs.cross_validate()
   

# Could use doctest to do testing too.
#    import doctest, ieeespecial
#    return doctest.testmod(ieeespecial)
