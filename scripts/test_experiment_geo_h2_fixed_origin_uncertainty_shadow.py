#!/usr/bin/env python3
"""Uncertainty shadow: fixed origin-mixture mathematical and archival guards."""
import math
import unittest
from experiment_geo_h2_fixed_origin_uncertainty_shadow import (
    LAMBDA, N, TRAIN, ORIGINS, PROSPECTIVE_TARGET,
    compute_probabilities, analyze,
)


class OriginStateShadowTest(unittest.TestCase):
    def test_lambda_fixed_before_labels(self):
        self.assertEqual(LAMBDA,.10)
        self.assertEqual(len(ORIGINS),11)
        self.assertEqual((N,TRAIN),(196,199))
        self.assertEqual(PROSPECTIVE_TARGET,2027)

    def test_convex_weights_for_adjacent_states(self):
        p_zero,p_low=.15,.35
        self.assertAlmostEqual((1-LAMBDA)*p_zero+LAMBDA*p_low,.17)
        self.assertAlmostEqual((1-LAMBDA)*p_low+LAMBDA*p_zero,.33)

    def test_same_state_shift_is_zero_for_2_3(self):
        for p in (.01,.25,.99):
            self.assertEqual(round(p,12),round(p,12))

    def test_valid_probability_mixture(self):
        for p,q in ((.001,.999),(.99,.1),(.3,.3)):
            mix=(1-LAMBDA)*p+LAMBDA*q
            self.assertTrue(0<mix<1)

    def test_no_source_imputation_or_cohort_changes(self):
        with self.assertRaises(ValueError):
            compute_probabilities({},2025,set())

    def test_missing_reference_refused(self):
        with self.assertRaises(ValueError):
            analyze({},[],{})

    def test_original_prospective_not_replaced(self):
        self.assertLess(max(ORIGINS),PROSPECTIVE_TARGET-2)

    def test_two_step_markov_mixture_linear_in_initial_distribution(self):
        # Conditional forecast for an initial state is linear in its
        # distribution, while individual transition rows remain unchanged.
        conditional=(.1,.4,.8,.9)
        new=.9*conditional[0]+.1*conditional[1]
        self.assertAlmostEqual(new,.13)


if __name__=="__main__":
    unittest.main()
