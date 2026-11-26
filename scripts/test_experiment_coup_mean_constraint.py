import unittest
from experiment_coup_mean_constraint import constrain
class Tests(unittest.TestCase):
    def test_mean_and_order(self):
        p=[.05,.05,.1,.4]
        q,d=constrain(p,.025)
        self.assertAlmostEqual(sum(q)/len(q),.025,places=12)
        self.assertEqual(q[0],q[1]);self.assertLess(q[1],q[2]);self.assertLess(q[2],q[3])
        self.assertLess(d,0)
    def test_constant(self):
        q,d=constrain([.2]*10,.04)
        self.assertAlmostEqual(q[0],.04,places=12)
        self.assertEqual(len(set(q)),1)
    def test_invalid(self):
        with self.assertRaises(ValueError):constrain([0,.1],.05)
if __name__=="__main__":unittest.main()
