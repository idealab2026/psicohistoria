import unittest
from experiment_coup2025_temporal_extension import predictions

class ExtensionTests(unittest.TestCase):
    def test_cutoff(self):
        with self.assertRaises(ValueError):
            predictions([(2024,1,1)],{1})
    def test_roster_and_dummy_invariance(self):
        rows=[(y,c,int(y==2020 and c==1)) for y in range(1950,2024) for c in (1,2)]
        p=predictions(rows,{1,2,3})
        self.assertEqual(len(p),3)
        for v in p.values():
            self.assertEqual(len(v),3)
            self.assertAlmostEqual(sum(v)/3,p["global_recent"][0])
    def test_empty(self):
        with self.assertRaises(ValueError):
            predictions([],set())

if __name__=="__main__":
    unittest.main()
