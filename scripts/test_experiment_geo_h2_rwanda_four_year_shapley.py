#!/usr/bin/env python3
"""Synthetic 5-factor Shapley, interaction, and missing-mask controls."""
import itertools
import math
import unittest

from experiment_geo_h2_rwanda_four_year_shapley import (
    ALL_MASK, FACTOR_NAMES, NFACTORS, YEARS, exact_shapley,
)


class RwandaFiveFactorTest(unittest.TestCase):
    def test_additive_independent_factors_exact(self):
        weights=(.07,0.,0.,.11,-.003)
        values={mask:.13+sum(weights[i] for i in range(NFACTORS)
                             if mask&(1<<i))
                for mask in range(1<<NFACTORS)}
        got=exact_shapley(values)
        for i,name in enumerate(FACTOR_NAMES):
            self.assertAlmostEqual(got[name],weights[i],places=13)

    def test_pairwise_interaction_split_equally(self):
        values={mask:.12+(.10 if mask&1 and mask&8 else 0)
                for mask in range(1<<NFACTORS)}
        got=exact_shapley(values)
        self.assertAlmostEqual(got[FACTOR_NAMES[0]],.05,places=14)
        self.assertAlmostEqual(got[FACTOR_NAMES[3]],.05,places=14)
        for i in (1,2,4):
            self.assertAlmostEqual(got[FACTOR_NAMES[i]],0,places=14)

    def test_three_way_interaction_allocated_equally(self):
        values={mask:.08+(.09 if mask&1 and mask&8 and mask&16 else 0)
                for mask in range(1<<NFACTORS)}
        got=exact_shapley(values)
        for i in (0,3,4):
            self.assertAlmostEqual(got[FACTOR_NAMES[i]],.03,places=13)

    def test_missing_counterfactual_rejected(self):
        with self.assertRaises(ValueError):
            exact_shapley({0:.1, ALL_MASK:.2})

    def test_exact_sum_with_nonlinear_function(self):
        values={mask:math.sin((mask+1)/13.0)/5+0.3
                for mask in range(1<<NFACTORS)}
        got=exact_shapley(values)
        self.assertAlmostEqual(sum(got.values()),
                               values[ALL_MASK]-values[0],places=13)

    def test_horizon_and_expected_revisions(self):
        self.assertEqual(YEARS,(1996,1997,2018,2021))
        self.assertEqual(NFACTORS,5)
        self.assertEqual(ALL_MASK,31)

    def test_constant_function_has_zero_shapley(self):
        got=exact_shapley({mask:.4 for mask in range(1<<NFACTORS)})
        self.assertTrue(all(x==0 for x in got.values()))


if __name__=="__main__":
    unittest.main()
