"""Predeclared four-state GEO H2 ablation: no source leakage, deterministic math."""
from __future__ import annotations

import copy
import math
import unittest

from test_forecast_2027_statebased import toy
from diagnose_geo2028_historical_forecast_vintage_drift import _fit_at_origin
from experiment_geo2027_intensity_markov_cross_release import (
    intensity_state, four_state_forecast, counts_to_binary,
    scores, compare_scores, parse_counts, replay,
)


def sample():
    base, _ = toy()
    return {
        cid: {
            year: (0 if binary == 0 and (cid+year)%7 else
                   7 if binary == 0 else
                   140 if (cid+year)%3==0 else 35)
            for year,binary in history.items()
        } for cid, history in base.items()
    }


class FourStateIntensityMarkovTests(unittest.TestCase):
    def test_exact_predeclared_intensity_bins(self):
        for d,k in ((0,0),(1,1),(24,1),(25,2),(99,2),(100,3),(1000,3)):
            self.assertEqual(intensity_state(d),k)
        for invalid in (-1,0.3,True,None):
            with self.assertRaises(ValueError):
                intensity_state(invalid)

    def test_no_origin_plus_one_or_target_source_leakage(self):
        counts=sample()
        p,meta=four_state_forecast(counts,2022)
        changed=copy.deepcopy(counts)
        for cid,history in changed.items():
            history[2023]=100000 if cid%3 else 0
            history[2024]=0 if cid%4 else 100000
        later,m2=four_state_forecast(changed,2022)
        self.assertEqual((p,meta),(later,m2))
        self.assertEqual(meta["cutoff_max"],2022)
        self.assertEqual(meta["eligible_countries"],196)
        self.assertEqual(len(meta["global_4x4_transitions"]),4)
        self.assertTrue(all(len(row)==4 for row in
                            meta["global_4x4_transitions"]))
        for probs in p.values():
            self.assertTrue(0<probs["p_intensity_markov"]<1)

    def test_binary_original_model_stays_two_state_target(self):
        counts=sample()
        binary=counts_to_binary(counts)
        reference,meta=_fit_at_origin(binary,2022)
        alternative,_=four_state_forecast(counts,2022)
        self.assertEqual(set(reference),set(alternative))
        self.assertEqual(len(reference),196)
        for cid in reference:
            self.assertEqual(alternative[cid]["origin_state"],
                             binary[cid][2022])
            self.assertTrue(0<reference[cid]["p_model_h2"]<1)

    def test_four_state_low_and_high_same_binary_but_different_h2(self):
        counts=sample()
        model,_=four_state_forecast(counts,2023)
        altered=copy.deepcopy(counts)
        # Change an exposure from high state to active-low state but preserve
        # every binary >=25 label. The 4-state alternative must respond.
        for year in range(1989,2023):
            if altered[1][year]>=100:
                altered[1][year]=30
        changed,_=four_state_forecast(altered,2023)
        self.assertEqual(counts_to_binary(counts),
                         counts_to_binary(altered))
        self.assertTrue(any(model[c]["p_intensity_markov"]!=
                            changed[c]["p_intensity_markov"] for c in model))

    def test_proper_scores_and_paired_sign(self):
        rows=[
            {"outcome":1,"p_original_binary":.6,
             "p_intensity_markov":.8},
            {"outcome":0,"p_original_binary":.4,
             "p_intensity_markov":.2},
        ]
        s=compare_scores(rows)
        self.assertEqual(s["n"],2)
        self.assertAlmostEqual(s["original_binary"]["brier"],.16)
        self.assertAlmostEqual(s["intensity_four_state"]["brier"],.04)
        self.assertLess(s["intensity_minus_binary_delta_brier"],0)
        self.assertLess(s["intensity_minus_binary_delta_logloss"],0)

    def test_source_sha_fail_closed_without_network(self):
        with self.assertRaisesRegex(ValueError,"SHA"):
            parse_counts(b"tampered official zip","25.1")

    def test_do_not_accept_modified_retro_protocol_as_issued_skill(self):
        with self.assertRaisesRegex(ValueError,"reference"):
            replay({},{"schema":"tampered","prospective_skill_demonstrated":True})


if __name__=="__main__":
    unittest.main()
