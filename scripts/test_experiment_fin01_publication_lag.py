import unittest
from experiment_fin01_monthly_downside import predict
from experiment_fin01_publication_lag import lag_predict

class LagTests(unittest.TestCase):
    def setUp(self):
        self.t=24000
        self.v={i:(.08 if i%7 else -.09) for i in range(self.t-240,self.t+3)}
    def test_exact_original(self):
        self.assertEqual(predict(self.v,self.t),lag_predict(self.v,self.t,2))
    def test_lag3_no_future_dependence(self):
        p=lag_predict(self.v,self.t,3)
        for j in range(self.t-2,self.t+3): self.v[j]=-.8
        self.assertEqual(p,lag_predict(self.v,self.t,3))
    def test_lag3_exact_cutoff(self):
        p=lag_predict(self.v,self.t,3)
        truncated={k:v for k,v in self.v.items() if k<=self.t-3}
        self.assertEqual(p,lag_predict(truncated,self.t,3))
    def test_bad_lag(self):
        with self.assertRaises(ValueError): lag_predict(self.v,self.t,1)

if __name__=="__main__": unittest.main()
