#!/usr/bin/env python3
"""Exact synthetic controls for ranking, ties, year masks and old-source safeguards."""
import copy
import unittest

from audit_geo_h2_2526_fixed_brier_ranking import (
    MODELS, _compare, _rank, analyze,
)


def sample():
    labels=list(MODELS)
    old={labels[0]:0.1, labels[1]:0.2, labels[2]:0.3, labels[3]:0.4}
    return old


class TestRanking(unittest.TestCase):
    def test_unchanged_rank_with_smaller_margin(self):
        old=sample()
        newer={**old, "p_original_binary":0.15}
        comparison=_compare(old,newer)
        self.assertFalse(comparison["ranking_changed"])
        self.assertEqual(comparison["pairwise_order_or_tie_reversed"], [])

    def test_real_reversal_detected(self):
        old=sample()
        newer={**old, "p_original_binary":0.22}
        r=_compare(old,newer)
        self.assertTrue(r["ranking_changed"])
        self.assertEqual(len(r["pairwise_order_or_tie_reversed"]),1)

    def test_ties_disclosed_as_rank_change(self):
        old=sample()
        newer={**old, "p_original_binary":0.2}
        r=_compare(old,newer)
        self.assertEqual(len(r["pairwise_order_or_tie_reversed"]),1)

    def test_missing_historical_inputs_rejected(self):
        with self.assertRaises(ValueError):
            analyze({},{})

    def test_bad_future_claim_rejected(self):
        with self.assertRaises(ValueError):
            analyze({"schema":"idealab.psico.geo_h2_fixed_origin_outcome_revision_brier.v1",
                     "historical_model_issued_at_real_origin":True}, {})

    def test_lexical_tie_break_is_deterministic(self):
        old=sample()
        old["p_original_binary"]=old["p_intensity_markov"]
        self.assertEqual(_rank(old), sorted(old,key=lambda k:(old[k],k)))

    def test_delta_sign_precision(self):
        old=sample()
        newer={k:v+0.000001 for k,v in old.items()}
        c=_compare(old,newer)
        self.assertFalse(c["ranking_changed"])
        self.assertFalse(c["pairwise_order_or_tie_reversed"])


if __name__=="__main__":
    unittest.main()
