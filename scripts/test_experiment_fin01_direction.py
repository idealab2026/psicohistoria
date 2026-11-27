import unittest
from experiment_fin01_direction import predict,summary

class DirectionTests(unittest.TestCase):
    def setUp(self):
        self.t=24000
        self.v={j:(.03 if j%3 else -.06) for j in range(self.t-240,self.t+3)}
    def test_future(self):
        for lag in (2,3):
            p=predict(self.v,self.t,lag)
            changed={k:(.8 if k>self.t-lag else v) for k,v in self.v.items()}
            self.assertEqual(p,predict(changed,self.t,lag))
    def test_constant(self):
        p=predict({j:.02 for j in self.v},self.t,3)
        for x in p.values():
            self.assertAlmostEqual(x["mean_return"],.02)
            self.assertTrue(0<x["p_positive"]<1)
    def test_zero_nonpositive(self):
        p=predict({j:0. for j in self.v},self.t,3)
        s=summary([(self.t,0.,p)])
        self.assertEqual(s["positive_months"],0)
        self.assertEqual(s["models"]["joint_regime"]["mse"],0)
    def test_unregistered_lag(self):
        with self.assertRaises(ValueError): predict(self.v,self.t,1)

if __name__=="__main__": unittest.main()
