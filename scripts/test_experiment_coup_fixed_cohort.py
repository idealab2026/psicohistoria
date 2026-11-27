import unittest
from experiment_coup_fixed_cohort import gains,bound

class BoundTests(unittest.TestCase):
    def test_known(self):
        for label in (0,1):
            self.assertEqual(bound(.2,.1,label),tuple((x,x) for x in gains(.2,.1,label)))
    def test_unknown(self):
        b,ll=bound(.2,.1,None)
        self.assertAlmostEqual(b[0],-.03)
        self.assertAlmostEqual(b[1],.17)
        self.assertLess(ll[0],0)
        self.assertGreater(ll[1],0)
    def test_equal(self):
        self.assertEqual(bound(.1,.1,None),((0.,0.),(0.,0.)))
    def test_reversed(self):
        for a,b in zip(bound(.2,.1,None),bound(.1,.2,None)):
            self.assertAlmostEqual(a[0],-b[1])
            self.assertAlmostEqual(a[1],-b[0])

if __name__=="__main__":
    unittest.main()
