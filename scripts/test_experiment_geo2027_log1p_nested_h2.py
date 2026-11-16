"""Nested chronological GEO H2 continuous-intensity experiment: synthetic tests."""
from __future__ import annotations

import copy
import math
import unittest

from test_experiment_geo2027_intensity_markov_cross_release import sample
from diagnose_geo2028_historical_forecast_vintage_drift import _fit_at_origin
from experiment_geo2027_intensity_markov_cross_release import counts_to_binary
from experiment_geo2027_log1p_nested_h2 import (
    LAMBDAS, binary_h2_until, compare, features, fit, inner_rows, logistic,
    logit, predict, replay, select_and_fit, solve,
)


class NestedLogIntensityTests(unittest.TestCase):
    def test_continuous_features_and_finite_offset(self):
        a=features(0)
        b=features(24)
        c=features(25)
        d=features(100)
        self.assertEqual(a,(1.0,0.0,0.0))
        self.assertTrue(0<b[1]<1 and b[2]==0)
        self.assertEqual(c,(1.0,0.0,0.0))
        self.assertTrue(d[2]>0)
        self.assertTrue(features(1000)[2]>features(100)[2])
        for x in (-1,0.2,None,True):
            with self.assertRaises(ValueError):
                features(x)
        for p in (0,1,-0.1,2):
            with self.assertRaises(ValueError):
                logit(p)
        for z in (-1000,0,1000):
            self.assertTrue(0<=logistic(z)<=1)

    def test_gauss_pivoting_and_logistic_offset_unchanged_at_beta_zero(self):
        self.assertEqual(solve([[2.0,0.0,0.0],[0.0,3.0,0.0],
                                [0.0,0.0,4.0]],[2.0,6.0,12.0]),
                         [1.0,2.0,3.0])
        row={"p_original_binary":0.73,"origin_deaths":150}
        self.assertAlmostEqual(predict(row,(0.0,0.0,0.0)),0.73,places=12)

    def test_replicates_original_markov_at_2022_and_2023(self):
        deathcounts=sample()
        binary=counts_to_binary(deathcounts)
        for cutoff in (2022,2023):
            old,_=_fit_at_origin(binary,cutoff)
            new=binary_h2_until(binary,cutoff)
            self.assertEqual(set(new),set(old))
            for cid in old:
                self.assertAlmostEqual(old[cid]["p_model_h2"],new[cid],places=11)

    def test_inner_training_never_uses_post_origin_labels(self):
        src=sample()
        original, years=inner_rows(src,2022)
        altered=copy.deepcopy(src)
        for cid,h in altered.items():
            h[2023]=123 if cid%2 else 0
            h[2024]=789 if cid%3 else 0
            h[2025]=51 if cid%5 else 0
        newer, years2=inner_rows(altered,2022)
        self.assertEqual(original,newer)
        self.assertEqual(years,years2)
        self.assertEqual(min(r["target_year"] for r in original),2012)
        self.assertEqual(max(r["target_year"] for r in original),2022)
        self.assertTrue(all(r["origin_year"]+2==r["target_year"] for r in original))
        self.assertTrue(all(y["max_training_cutoff"]+2==y["target_year"] for y in years))

    def test_nested_selection_only_pre2021_and_final_ends_at_origin(self):
        training,years=inner_rows(sample(),2022)
        beta,intercept,meta=select_and_fit(training,2022)
        self.assertEqual(meta["inner_fit_targets"],[2012,2017])
        self.assertEqual(meta["inner_select_targets"],[2018,2020])
        self.assertEqual(meta["final_train_targets"],[2012,2022])
        self.assertIn(meta["selected_ridge_lambda"],LAMBDAS)
        self.assertEqual(len(meta["candidate_lambda_validation_scores"]),3)
        self.assertEqual(intercept[1:],(0.0,0.0))
        self.assertTrue(all(math.isfinite(x) for x in beta))
        self.assertGreater(meta["inner_fit_n"],500)
        self.assertGreater(meta["inner_validation_n"],500)

    def test_three_models_are_distinct_comparators(self):
        rows=[
            {"outcome":1,"p_original_binary":.6,
             "p_calibrated_intercept":.75,"p_offset_log1p":.8},
            {"outcome":0,"p_original_binary":.4,
             "p_calibrated_intercept":.3,"p_offset_log1p":.2},
        ]
        m=compare(rows)
        self.assertEqual(m["n"],2)
        self.assertAlmostEqual(m["scores"]["p_original_binary"]["brier"],.16)
        self.assertAlmostEqual(m["scores"]["p_calibrated_intercept"]["brier"],.07625)
        self.assertAlmostEqual(m["scores"]["p_offset_log1p"]["brier"],.04)
        self.assertLess(m["log1p_minus_intercept_delta_brier"],0)

    def test_bad_prior_source_cannot_count_as_independent(self):
        with self.assertRaisesRegex(ValueError,"provenance"):
            replay({},{"schema":"tampered"},{"schema":"tampered"})


if __name__=="__main__":
    unittest.main()
