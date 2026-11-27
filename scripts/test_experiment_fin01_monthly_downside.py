import unittest
from experiment_fin01_monthly_downside import month_index,month_name,label,predict,features,losses

class FinTests(unittest.TestCase):
    def test_calendar(self):
        self.assertEqual(month_index("202501")-month_index("202412"),1)
        self.assertEqual(month_name(month_index("202412")),"2024-12")
    def test_threshold(self):
        self.assertEqual((label(-.05),label(-.049)),(1,0))
    def test_no_future_dependence(self):
        t=month_index("200001")
        v={i:(.08 if i%7 else -.09) for i in range(t-240,t+3)}
        original=predict(v,t)
        for j in range(t-1,t+3): v[j]=-.8
        self.assertEqual(original,predict(v,t))
    def test_probabilities(self):
        t=month_index("200001")
        v={i:0. for i in range(t-240,t)}
        p=predict(v,t)
        self.assertEqual(p["normal_vol"],.001)
        self.assertTrue(all(0<x<1 for x in p.values()))
    def test_loss(self):
        self.assertAlmostEqual(losses(.2,1)[0],.64)

if __name__=="__main__":
    unittest.main()
