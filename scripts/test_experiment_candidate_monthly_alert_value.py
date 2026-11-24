import unittest
from experiment_candidate_monthly_alert_value import alert,pooled,hit_probability
class Tests(unittest.TestCase):
    def test_constant_matches_random(self):
        a=alert([.1]*10,[1,1]+[0]*8,3)
        self.assertAlmostEqual(a["lift"],1)
        self.assertAlmostEqual(a["probability_at_least_one_hit"],a["random_probability_at_least_one_hit"])
        self.assertEqual((a["minimum_hits"],a["maximum_hits"]),(0,2))
    def test_cutoff_tie_invariant(self):
        p=[.9,.4,.4,.4,.1]; y=[1,1,0,0,0]
        a=alert(p,y,2)
        self.assertEqual(a,alert(list(reversed(p)),list(reversed(y)),2))
        self.assertAlmostEqual(a["expected_hits"],4/3)
        self.assertEqual((a["minimum_hits"],a["maximum_hits"]),(1,2))
    def test_zero_positive(self):
        a=alert([.2,.1],[0,0],1)
        self.assertIsNone(a["recall"]);self.assertIsNone(a["lift"])
        self.assertEqual(a["probability_at_least_one_hit"],0)
    def test_exact_hit_probability(self):
        self.assertAlmostEqual(hit_probability(4,2,2),5/6)
        self.assertEqual(hit_probability(4,2,3),1)
    def test_pool_weighted_by_counts(self):
        a=alert([.2]*10,[1]+[0]*9,2)
        b=alert([.2]*20,[1,1]+[0]*18,2)
        self.assertAlmostEqual(pooled([a,b])["lift"],1)
if __name__=="__main__": unittest.main()
