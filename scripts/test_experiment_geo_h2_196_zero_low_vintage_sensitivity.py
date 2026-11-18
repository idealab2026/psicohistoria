#!/usr/bin/env python3
"""Control zero/low threshold, two-block Shapley and fail-closed input."""
import unittest

from experiment_geo_h2_196_zero_low_vintage_sensitivity import (
    ORIGIN, TARGET, N, two_block_shapley, zero_low, evaluate,
)


class ZeroLowSensitivityTest(unittest.TestCase):
    def test_true_zero_low_crossings_both_directions(self):
        for a,b in ((0,1),(0,24),(1,0),(24,0)):
            self.assertTrue(zero_low(a,b))

    def test_other_important_state_changes_not_zero_low(self):
        for a,b in ((0,25),(24,25),(99,100),(90,113),(0,0),
                    (1,3),(24,12),(0,100),(100,0)):
            self.assertFalse(zero_low(a,b))

    def test_negative_and_noninteger_rejected(self):
        for a,b in ((-1,1),(0,-1),(.0,1),(0,1.1)):
            with self.assertRaises(ValueError):
                zero_low(a,b)

    def test_symmetric_shapley_with_interaction(self):
        a,b,c,d=.1,.2,.15,.3
        z,o=two_block_shapley(a,b,c,d)
        self.assertAlmostEqual(z+o,d-a,places=14)
        self.assertAlmostEqual(z,.125,places=14)
        self.assertAlmostEqual(o,.075,places=14)

    def test_source_groups_with_only_other_changes(self):
        z,o=two_block_shapley(.14,.14,.18,.18)
        self.assertAlmostEqual(z,0,places=14)
        self.assertAlmostEqual(o,.04,places=14)

    def test_missing_official_provenance_refused(self):
        with self.assertRaises(ValueError):
            evaluate({}, {}, {}, {}, [])

    def test_horizon_and_original_gwno_count(self):
        self.assertEqual(ORIGIN,2021)
        self.assertEqual(TARGET-ORIGIN,2)
        self.assertEqual(N,196)


if __name__=="__main__":
    unittest.main()
