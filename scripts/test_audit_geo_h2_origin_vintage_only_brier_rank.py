#!/usr/bin/env python3
"""Fail-closed synthetic checks for the factorized source-version comparison."""
import copy
import unittest
from audit_geo_h2_origin_vintage_only_brier_rank import contrast, rank, audit


class TestOriginVintageRanking(unittest.TestCase):
    def test_true_winner_flip(self):
        old={"original_binary":0.04,"four_state_intensity":0.039,
             "global_markov":0.08,"global_prevalence_5y":0.11}
        late={**old,"four_state_intensity":0.040,"original_binary":0.038}
        result=contrast(old,late)
        self.assertTrue(result["winner_changed"])
        self.assertTrue(result["rank_changed"])
        self.assertEqual(result["winner_origin23_1"],"four_state_intensity")
        self.assertEqual(result["winner_origin24_1"],"original_binary")
        self.assertEqual(len(result["pairwise_reversals_or_tie_changes"]),1)

    def test_nonstrict_tie_explicitly_reported(self):
        old={"original_binary":0.04,"four_state_intensity":0.03,
             "global_markov":0.08,"global_prevalence_5y":0.11}
        new={**old,"original_binary":0.03}
        self.assertEqual(len(contrast(old,new)["pairwise_reversals_or_tie_changes"]),1)

    def test_drift_without_rank_flip(self):
        old={"original_binary":0.04,"four_state_intensity":0.03,
             "global_markov":0.08,"global_prevalence_5y":0.11}
        new={**old,"original_binary":0.039}
        self.assertFalse(contrast(old,new)["rank_changed"])
        self.assertFalse(contrast(old,new)["winner_changed"])

    def test_missing_data_cannot_be_claimed_valid(self):
        with self.assertRaises(ValueError):
            audit({}, {})

    def test_spurious_source_vintage_blocked(self):
        with self.assertRaises(ValueError):
            audit({"schema":"idealab.psico.geo_h2_rolling_historical_2014_2025.v1"}, {})

    def test_all_four_models_ranked_once(self):
        x={"original_binary":0.04,"four_state_intensity":0.03,
           "global_markov":0.08,"global_prevalence_5y":0.11}
        self.assertEqual(rank(x),["four_state_intensity","original_binary",
                                  "global_markov","global_prevalence_5y"])

    def test_scores_are_not_asof_prospective_claims(self):
        with self.assertRaises(ValueError):
            audit({"not_prospective_or_independently_timestamped_skill":False},
                  {"historical_issued_asof_evidence":True})


if __name__=="__main__":
    unittest.main()
