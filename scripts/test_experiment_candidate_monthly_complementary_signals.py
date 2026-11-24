import unittest
from experiment_candidate_monthly_complementary_signals import extended_predict,run
from audit_candidate_monthly_bridge import counts
from datetime import date
class Tests(unittest.TestCase):
    def test_fixed_weights_and_no_outcome_leakage(self):
        tr=[(2021,1,0,5,5),(2021,2,1,0,0)]
        other={(2021,1):1,(2021,2):0,(2023,1):1}
        a=extended_predict(tr,[(2023,1,0,0,0)],other,2023,5,30)
        b=extended_predict(tr,[(2023,1,0,999,999)],other,2023,5,30)
        self.assertEqual(a,b)
        g,q,c,p,o,p3=a[0]
        self.assertAlmostEqual(p,(q+c)/2)
        self.assertAlmostEqual(p3,(q+c+o)/3)
    def test_other_is_distinct(self):
        start=date(2023,1,1)
        events={"a":(1,1,1,5,start,start),"b":(1,2,1,3,start,start),"c":(1,3,1,4,start,start)}
        self.assertEqual(counts(events,2023,[1]),{1:5})
        self.assertEqual(counts(events,2023,[1],(2,3)),{1:7})
    def test_future_training_rejected(self):
        with self.assertRaises(ValueError):
            extended_predict([(2022,1,0,0,0)],[(2023,1,0,0,0)],{},2023,5,30)
if __name__=="__main__": unittest.main()
