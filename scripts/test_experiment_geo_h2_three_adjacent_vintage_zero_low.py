#!/usr/bin/env python3
"""Synthetic source edit threshold, cutoff and exact factorial checks."""
import unittest
from experiment_geo_h2_three_adjacent_vintage_zero_low import (
    ORIGINS,PAIRS,COHORT,TRAIN,zero_low,source_edits,shapley,analyze,
)


class AdjacentEditTests(unittest.TestCase):
    def test_predeclared_33_folds(self):
        self.assertEqual(len(ORIGINS)*len(PAIRS),33)
        self.assertEqual((COHORT,TRAIN),(196,199))
        self.assertEqual(PAIRS,(("23.1","24.1"),("24.1","25.1"),("25.1","26.1")))

    def test_zero_low_uses_exact_bins(self):
        for x,y in ((0,1),(0,24),(24,0)):
            self.assertTrue(zero_low(x,y))
        for x,y in ((0,25),(0,99),(0,100),(24,25),(1,2),(100,101)):
            self.assertFalse(zero_low(x,y))

    def test_invalid_death_values_not_accepted(self):
        for x,y in ((-1,0),(0,-2),(0,1.0),("0",1)):
            with self.assertRaises(ValueError):
                zero_low(x,y)

    def test_shapley_nonadditivity(self):
        z,o=shapley(.2,.25,.22,.40)
        self.assertAlmostEqual(z+o,.2)
        self.assertAlmostEqual(z,.115)
        self.assertAlmostEqual(o,.085)

    def test_no_future_data_in_edits(self):
        old={cid:{2010:0,2011:0,2012:0,2013:0} for cid in range(1,200)}
        new={cid:dict(h) for cid,h in old.items()}
        new[2][2011]=2
        new[3][2013]=4
        edits=source_edits(old,new,2012)
        self.assertEqual(len(edits),1)
        self.assertEqual(edits[0][:2],(2,2011))

    def test_coverage_not_silently_imputed(self):
        old={cid:{2011:0,2012:0} for cid in range(1,200)}
        new={cid:dict(h) for cid,h in old.items()}
        del new[1][2011]
        with self.assertRaises(ValueError):
            source_edits(old,new,2012)

    def test_missing_reference_blocked(self):
        with self.assertRaises(ValueError):
            analyze({},[],{})


if __name__=="__main__":
    unittest.main()
