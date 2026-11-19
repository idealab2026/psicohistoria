#!/usr/bin/env python3
"""Adversarial guards for retrospective low/best/high fatality envelopes."""
import unittest
from datetime import date
import audit_geo_ged251_marginal_fatality_interval as m


class IntervalAudit(unittest.TestCase):
    def test_three_disjoint_threshold_classes(self):
        self.assertEqual(m.label_class(18,20,24),"negative_for_all_three_estimates")
        self.assertEqual(m.label_class(25,25,25),"positive_for_all_three_estimates")
        self.assertEqual(m.label_class(8,23,23),"negative_for_all_three_estimates")
        self.assertEqual(m.label_class(19,34,34),"low_high_straddle_binary_threshold")
        self.assertEqual(m.label_class(24,24,25),"low_high_straddle_binary_threshold")
        self.assertEqual(m.label_class(24,25,25),"low_high_straddle_binary_threshold")

    def test_no_bounds_are_probability_confidence_intervals(self):
        sums=m.sum_envelope([
            {"low":8,"best":23,"high":23},
            {"low":10,"best":11,"high":11}])
        self.assertEqual([sums[x] for x in ("low","best","high")],[18,34,34])
        self.assertTrue(sums["best_vs_low_label_disagrees"])
        self.assertFalse(sums["best_vs_high_label_disagrees"])
        self.assertEqual(sums["class"],"low_high_straddle_binary_threshold")

    def test_ucdp_clarity2_high_below_best_is_valid_official_semantics(self):
        # GED25.1 codebook section 5.5, page 23: when a clarity-2
        # aggregate has clear subevents subtracted, high may be below best.
        rows=[
            {"low":9,"best":15,"high":4,"event_clarity":2},
            {"low":10,"best":11,"high":11,"event_clarity":1}
        ]
        v=m.sum_envelope(rows)
        self.assertEqual([v[k] for k in ("low","best","high")],[19,26,15])
        self.assertEqual((v["per_row_min_total"],v["per_row_max_total"]),(14,26))
        self.assertEqual(v["class"],"low_high_straddle_binary_threshold")
        self.assertFalse(v["raw_scenario_totals_monotone"])
        self.assertTrue(v["best_vs_high_label_disagrees"])

    def test_monotone_input_has_same_raw_and_normalized_bounds(self):
        rows=[{"low":8,"best":23,"high":23}]
        v=m.sum_envelope(rows)
        self.assertEqual(v["per_row_min_total"],v["low"])
        self.assertEqual(v["per_row_max_total"],v["high"])
        self.assertTrue(v["raw_scenario_totals_monotone"])

    def test_high_bound_can_flip_inactive_to_active(self):
        sums=m.sum_envelope([
            {"low":18,"best":18,"high":26}])
        self.assertFalse(sums["best_label_ge25"])
        self.assertTrue(sums["high_label_ge25"])
        self.assertTrue(sums["best_vs_high_label_disagrees"])

    def test_low_equals_high_does_not_fake_uncertainty(self):
        sums=m.sum_envelope([{"low":25,"best":25,"high":25}])
        self.assertEqual(sums["uncertainty_range_total"],0)
        self.assertEqual(sums["class"],"positive_for_all_three_estimates")

    def test_impossible_ged_low_best_high_blocked(self):
        for triple in ((25,24,26),(25,25,24),(-1,1,1),
                       (0,-1,4),(0,1,-1),(1.1,2,3)):
            with self.assertRaises(ValueError):
                m.label_class(*triple)

    def test_threshold_boundary_25(self):
        self.assertEqual(m.label_class(24,24,24),
                         "negative_for_all_three_estimates")
        self.assertEqual(m.label_class(24,25,25),
                         "low_high_straddle_binary_threshold")
        self.assertEqual(m.label_class(25,25,26),
                         "positive_for_all_three_estimates")

    def test_original_selection_fixed(self):
        prior,selected=m.read_source_cohort()
        self.assertEqual(len(selected),14)
        self.assertEqual(prior["prespecified_band_inclusive"],[15,35])
        self.assertIn((373,2021),selected)
        self.assertIn((461,2022),selected)

    def test_fake_zip_cannot_masquerade_as_ucdp_official(self):
        _,sel=m.read_source_cohort()
        with self.assertRaises(ValueError):
            m.source_extract(b"not official UCDP archive",sel)

    def test_original_issued_ged_zip_locked(self):
        self.assertEqual(m.GED_SHA,
          "e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d")

    def test_empty_case_group_would_not_fake_conflict(self):
        x=m.sum_envelope([])
        self.assertEqual((x["low"],x["best"],x["high"]),(0,0,0))
        self.assertEqual(x["class"],"negative_for_all_three_estimates")


if __name__=="__main__":
    unittest.main()
