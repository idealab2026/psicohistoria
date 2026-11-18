#!/usr/bin/env python3
"""Fail-closed arithmetic and calendar checks for 11-origin zero-low study."""
import math
import unittest

from experiment_geo_h2_11origin_zero_low_source_stress import (
    ORIGINS, COHORT_N, TRAIN_N, zero_low, shapley, edit_list, analyze,
)


class TestElevenOriginZeroLow(unittest.TestCase):
    def test_all_11_origins_and_unique_targets(self):
        self.assertEqual(ORIGINS,tuple(range(2012,2023)))
        self.assertEqual(len(set(y+2 for y in ORIGINS)),11)
        self.assertEqual((COHORT_N,TRAIN_N),(196,199))

    def test_zero_low_crosses_both_ways(self):
        for a,b in ((0,1),(0,24),(1,0),(24,0)):
            self.assertTrue(zero_low(a,b))

    def test_not_zero_low_if_other_state_crossing(self):
        for a,b in ((0,25),(0,100),(1,25),(24,99),(90,113),(0,0),(1,2)):
            self.assertFalse(zero_low(a,b))

    def test_unsupported_fatalities_rejected(self):
        for a,b in ((-1,0),(0,-1),(0,1.),("0",1)):
            with self.assertRaises(ValueError):
                zero_low(a,b)

    def test_source_edit_cutoff(self):
        old={cid:{2010:0,2011:0,2012:0,2013:0} for cid in range(1,200)}
        new={cid:dict(h) for cid,h in old.items()}
        new[2][2012]=1
        new[3][2013]=5
        before=edit_list(old,new,2012)
        self.assertEqual(len(before),1)
        self.assertEqual(before[0]["GWNO"],2)
        self.assertEqual(before[0]["year"],2012)

    def test_no_imputation_if_source_years_disagree(self):
        old={cid:{2011:0,2012:0} for cid in range(1,200)}
        new={cid:dict(h) for cid,h in old.items()}
        del new[1][2011]
        with self.assertRaises(ValueError):
            edit_list(old,new,2012)

    def test_shapley_interactions_and_sum(self):
        z,o=shapley(.1,.3,.2,.5)
        self.assertAlmostEqual(z+o,.4,places=14)
        self.assertAlmostEqual(z,.25,places=14)
        self.assertAlmostEqual(o,.15,places=14)

    def test_prior_provenance_fail_closed(self):
        with self.assertRaises(ValueError):
            analyze({}, {}, {}, [])


if __name__=="__main__":
    unittest.main()
