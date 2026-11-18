#!/usr/bin/env python3
"""Synthetic controls for fixed-estimator Rwanda local-vs-global edit Shapley."""
import math
import unittest

from experiment_geo_h2_rwanda_origin_vintage_shapley import (
    RWANDA, ORIGIN, TARGET, N, evaluate,
)


class RwandaSourceShapleyTest(unittest.TestCase):
    def test_shapley_two_factor_exhaustive_synthetic(self):
        # p00 baseline, p10 Rwanda-only, p01 other-195-only, p11 full revised
        for a,b,c,d in ((.1,.2,.15,.3),(.2,.2,.31,.31),(.1,.17,.1,.17)):
            own=((b-a)+(d-c))/2
            others=((c-a)+(d-b))/2
            self.assertAlmostEqual(own+others,d-a,places=14)

    def test_interaction_formula(self):
        a,b,c,d=.12,.20,.15,.32
        self.assertAlmostEqual(d-b-c+a,0.09,places=14)

    def test_both_groups_need_not_be_additive(self):
        a,b,c,d=.12,.20,.15,.32
        self.assertNotAlmostEqual(d-a,(b-a)+(c-a),places=10)

    def test_missing_official_rows_blocked(self):
        with self.assertRaises(ValueError):
            evaluate({}, {}, {})

    def test_wrong_source_schema_blocked(self):
        with self.assertRaises(ValueError):
            evaluate({}, {}, {"schema":"wrong"})

    def test_fixed_gwno_contract(self):
        self.assertEqual(RWANDA,517)
        self.assertEqual(N,196)
        self.assertEqual(TARGET-ORIGIN,2)

    def test_no_tiny_drift_as_boolean(self):
        self.assertFalse(math.isclose(0.113296,0,rel_tol=0,abs_tol=1e-12))


if __name__=="__main__":
    unittest.main()
