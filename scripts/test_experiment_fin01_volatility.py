import unittest
from experiment_fin01_volatility import predict,loss,month_index

class VolTests(unittest.TestCase):
    def setUp(self):
        self.t=month_index("199001")
        self.v={j:.001+(j%5)*.0002 for j in range(month_index("195001"),self.t+3)}
    def test_no_future_dependence(self):
        p=predict(self.v,self.t)
        for j in range(self.t-1,self.t+3): self.v[j]=.5
        self.assertEqual(p,predict(self.v,self.t))
    def test_constant(self):
        p=predict({j:.002 for j in self.v},self.t)
        for x in p.values(): self.assertAlmostEqual(x,.002)
    def test_loss(self):
        self.assertEqual(loss(.04,.04),(0.,0.))
        self.assertAlmostEqual(loss(.04,.01)[1],.1)
    def test_invalid(self):
        with self.assertRaises(ValueError): loss(0,.01)
    def test_har(self):
        p=predict(self.v,self.t)
        a=[self.v[j] for j in range(self.t-13,self.t-1)]
        self.assertAlmostEqual(p["har_proxy"],(a[-1]+sum(a[-3:])/3+sum(a)/12)/3)

if __name__=="__main__": unittest.main()
