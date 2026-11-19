#!/usr/bin/env python3
"""Adversarial GED source-overlap / 25-death single-record hypothesis tests."""
from datetime import date
import unittest

import audit_geo_ged251_candidate_source_threshold as m


class CandidateSourceThreshold(unittest.TestCase):
    def test_same_source_citation_normalization(self):
        a=m.normalize_source_articles("  Reuters, 2022-02-01, event report x   /// BBC, 2022-02-01, report other ")
        b=m.normalize_source_articles("reuters, 2022-02-01, event report x")
        c=m.normalize_source_articles("Independent Press, 2022-02-01, unrelated claim")
        self.assertEqual(len(a & b),1)
        self.assertEqual(len(a & c),0)
        self.assertEqual(m.normalize_source_articles(""),frozenset())
        self.assertEqual(m.normalize_source_articles("NA"),frozenset())

    def test_unknown_dyad_not_equivalent_to_zero(self):
        self.assertIsNone(m.valid_dyad("NA"))
        self.assertIsNone(m.valid_dyad(""))
        self.assertEqual(m.valid_dyad(123),"123")

    def test_single_row_deletion_pivotal(self):
        x=m.counterfactual_single_row_removal(26,1,2)
        self.assertTrue(x["either_single_removal_flips_label"])
        self.assertFalse(x["both_possible_single_removals_flip_label"])
        self.assertFalse(x["remove_left_flips_label"])
        self.assertTrue(x["remove_right_flips_label"])

    def test_single_row_deletion_both_pivotal(self):
        x=m.counterfactual_single_row_removal(25,1,4)
        self.assertTrue(x["either_single_removal_flips_label"])
        self.assertTrue(x["both_possible_single_removals_flip_label"])

    def test_high_totals_robust_to_one_deletion(self):
        x=m.counterfactual_single_row_removal(3000,43,50)
        self.assertFalse(x["either_single_removal_flips_label"])
        self.assertTrue(x["baseline_ge25"])

    def test_inactive_deletion_cannot_create_active(self):
        x=m.counterfactual_single_row_removal(20,1,10)
        self.assertFalse(x["either_single_removal_flips_label"])
        self.assertFalse(x["baseline_ge25"])

    def test_total_smaller_than_event_rejected(self):
        with self.assertRaises(ValueError):
            m.counterfactual_single_row_removal(5,6,1)

    def test_candidate_hyperparameters_unchanged(self):
        self.assertEqual(m.CANDIDATE_DISTANCE_KM,25)
        self.assertEqual(m.CANDIDATE_GAP_DAYS,3)
        self.assertEqual(m.TARGET_THRESHOLD,25)

    def test_date_gap_is_not_distance_to_midpoints(self):
        from audit_geo_ged251_stratified_linkage import gap_days
        a={"start":date(2022,3,1),"end":date(2022,3,7)}
        b={"start":date(2022,3,10),"end":date(2022,3,11)}
        self.assertEqual(gap_days(a,b),3)

    def test_source_fragment_reuse_is_not_a_witness(self):
        a=m.normalize_source_articles("Agency, 2021-09-03, violent incident")
        b=m.normalize_source_articles("Agency, 2021-09-03, violent incident")
        self.assertEqual(len(a & b),1)
        self.assertFalse(m.counterfactual_single_row_removal(30,1,1)[
            "either_single_removal_flips_label"])


if __name__=="__main__":
    unittest.main()
