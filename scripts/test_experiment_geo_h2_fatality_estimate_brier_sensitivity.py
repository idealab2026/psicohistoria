"""Synthetic, model-independent counterchecks for two-vintage UCDP label perturbation.

No assumed future 2027 outcomes. Brute-force sharp finite-cohort Brier extrema.
"""
from __future__ import annotations

import copy
import itertools
import json
import math
import unittest

from audit_geo2027_ucdp_fatality_vintages import classify
from audit_geo2027_global_only_matched_issue import ISSUE
from backtest_archived_country_vintages import SOURCES
from experiment_geo_h2_fatality_estimate_brier_sensitivity import (
    N, _assert_scores_frozen, _delta, _sign, replay, summarize,
)
from experiment_geo2027_intensity_markov_cross_release import (
    four_state_forecast, counts_to_binary,
)
from diagnose_geo2028_historical_forecast_vintage_drift import _fit_at_origin
from test_experiment_geo2027_intensity_markov_cross_release import sample


def case(cid, triple, p, q, year=2024):
    return {
        "country_id": cid,
        "target_year": year,
        "official_fatalities_estimates": triple,
        "p_original_binary": p,
        "p_intensity_markov": q,
    }


class GEOH2FatalityMeasurementSensitivityTests(unittest.TestCase):
    def test_exact_proper_score_for_each_estimate_and_sign(self):
        rows = [
            case(1, (0, 0, 0), .4, .2),
            case(2, (24, 25, 26), .6, .8),
            case(3, (24, 24, 25), .8, .2),
            case(4, (0, 26, 24), .7, .9), # real UCDP-style best > high
        ]
        out = summarize(rows)
        self.assertEqual(out["ambiguous_country_year_n"], 3)
        self.assertEqual(out["ambiguous_country_years"],
                         [[2024, 2], [2024, 3], [2024, 4]])
        self.assertEqual(out["nonmonotonic_named_death_estimate_country_years"],
                         [[2024, 4]])
        self.assertEqual([out["scenarios"][s]["positives"]
                          for s in ("low", "best", "high")], [0,2,2])
        for name, index in (("low", 0), ("best", 1), ("high", 2)):
            brier_a = sum((r["p_original_binary"] -
                           classify(r["official_fatalities_estimates"])[index]) ** 2
                          for r in rows) / len(rows)
            brier_b = sum((r["p_intensity_markov"] -
                           classify(r["official_fatalities_estimates"])[index]) ** 2
                          for r in rows) / len(rows)
            observed=out["scenarios"][name]
            self.assertAlmostEqual(observed["original_binary"]["brier"],brier_a)
            self.assertAlmostEqual(observed["four_state_intensity"]["brier"],brier_b)
            self.assertAlmostEqual(observed["four_state_minus_original_delta_brier"],
                                   brier_b-brier_a)

    def test_sharp_envelope_exhaustive_three_ambiguous_cases(self):
        rows=[case(1, (0,0,0),.2,.4),
              case(2, (24,25,26),.6,.8),
              case(3, (24,24,25),.6,.5),
              case(4, (0,26,24),.1,.2)]
        out=summarize(rows)
        brute=[]
        for choices in itertools.product((0,1),repeat=3):
            outcomes=[0,*choices]
            brute.append(sum(_delta(r["p_intensity_markov"],
                                    r["p_original_binary"],y)
                             for r,y in zip(rows,outcomes))/len(rows))
        bounds=out["sharp_label_ambiguity_envelope"]
        self.assertAlmostEqual(min(brute),bounds["sharp_finite_cohort_lower_delta_brier"])
        self.assertAlmostEqual(max(brute),bounds["sharp_finite_cohort_upper_delta_brier"])
        for name in ("low","best","high"):
            v=out["scenarios"][name]["four_state_minus_original_delta_brier"]
            self.assertLessEqual(min(brute)-1e-12,v)
            self.assertGreaterEqual(max(brute)+1e-12,v)

    def test_exhaustive_robust_sign_and_inconclusive_sign(self):
        rows=[case(1, (0,25,27), .2,.8)]
        v=summarize(rows)
        self.assertFalse(v["sharp_label_ambiguity_envelope"][
            "zero_excluded_by_algebraic_envelope"])
        self.assertEqual(v["sharp_label_ambiguity_envelope"][
            "same_model_lower_brier_for_every_consistent_binary_label_assignment"],
            "not_identified")
        always_original=summarize([case(1,(0,25,27),.2,.4),
                                   case(2,(0,0,0),.1,.9)])
        b=always_original["sharp_label_ambiguity_envelope"]
        self.assertTrue(b["zero_excluded_by_algebraic_envelope"])
        self.assertEqual(b["same_model_lower_brier_for_every_consistent_binary_label_assignment"],
                         "original_binary_lower_brier")

    def test_duplicate_cases_bad_probability_and_bad_deaths_fail_closed(self):
        r=case(1,(24,25,26),.3,.4)
        for rows in ([r,r],[case(1,(-1,1,2),.3,.4)],
                     [case(1,(24,25,26),0.,.4)],
                     [case(1,(24,25,26),.3,float("nan"))],
                     [case(1,(24.5,25,26),.3,.4)]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                summarize(rows)

    def test_histories_have_no_target_data_leakage(self):
        data=sample()
        binary,_=_fit_at_origin(counts_to_binary(data),2022)
        alt,_=four_state_forecast(data,2022)
        infected=copy.deepcopy(data)
        for _,h in infected.items():
            h[2023]=10_000
            h[2024]=0
        later_binary,_=_fit_at_origin(counts_to_binary(infected),2022)
        later_alt,_=four_state_forecast(infected,2022)
        self.assertEqual(binary,later_binary)
        self.assertEqual(alt,later_alt)
        self.assertEqual(len(binary),N)

    def test_replay_requires_source_separated_archives_and_frozen_refs(self):
        with self.assertRaisesRegex(ValueError, "Exactly four"):
            replay({}, {}, {"official_2027_outcomes_resolved":0}, {}, {}, {})
        self.assertEqual(_sign(-.2),"four_state_lower_brier")
        self.assertEqual(_sign(.2),"original_binary_lower_brier")
        self.assertEqual(_sign(0),"numerically_tied")

    def test_official_frozen_country_universe_and_source_cutoffs(self):
        issue=json.loads(ISSUE.read_text(encoding="utf-8"))
        self.assertEqual(len(issue["countries"]), N)
        self.assertEqual([SOURCES[f]["last_year"] for f in
                          ("23.1","24.1","25.1","26.1")],
                         [2022,2023,2024,2025])
        self.assertEqual(issue["official_2027_outcomes_resolved"],0)


if __name__ == "__main__":
    unittest.main()
