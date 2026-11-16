"""Tests for post-issued inactive log1p slope attenuation Pareto ablation."""
from __future__ import annotations

import json
import unittest

from audit_geo2027_log1p_shadow_issue import (
    ISSUE, MANIFEST, ORIGINAL, audit as audit_issue,
)
from audit_geo2027_log1p_issued_death_stress import ALERTS
from experiment_geo2027_log1p_inactive_attenuation_frontier import (
    ALPHAS, PRIOR_STRESS, fold_scores, issued_counterfactual,
    nondominated, p_scaled, scaled_beta,
)


class InactiveAttenuationAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.issue=json.loads(ISSUE.read_text(encoding="utf8"))
        cls.previous=json.loads(PRIOR_STRESS.read_text(encoding="utf8"))
        cls.alerts=json.loads(ALERTS.read_text(encoding="utf8"))
        cls.beta=cls.issue["training"]["final_beta_log1p"]

    def test_first_issue_still_sha_frozen(self):
        result=audit_issue(ISSUE.read_bytes(),MANIFEST.read_bytes(),
                           ORIGINAL.read_bytes())
        self.assertEqual(result["country_n"],196)
        self.assertEqual(result["future_2027_outcomes_resolved"],0)

    def test_predeclared_exact_grid_and_only_inactive_slope_scaled(self):
        self.assertEqual(ALPHAS,(0.0,.25,.5,.75,1.0))
        for a in ALPHAS:
            b=scaled_beta(self.beta,a)
            self.assertEqual(b[0],self.beta[0])
            self.assertAlmostEqual(b[1],a*self.beta[1])
            self.assertEqual(b[2],self.beta[2])
        for candidate in (0.1,2,1,True,-.25):
            with self.assertRaises(ValueError):
                scaled_beta(self.beta,candidate)

    def test_zero_deaths_centre_same_at_all_alphas(self):
        row=next(r for r in self.issue["countries"]
                 if r["country"]=="Burundi")
        self.assertEqual(row["origin_deaths_best_2025"],0)
        p0=row["original_2027_p_active"]
        outputs=[p_scaled(p0,0,self.beta,a) for a in ALPHAS]
        self.assertTrue(all(abs(x-outputs[0])<1e-14 for x in outputs))
        self.assertAlmostEqual(outputs[-1],
                               row["log1p_shadow_p_active_2027"],places=11)

    def test_active_p_current_and_source_stress_unchanged(self):
        row=next(r for r in self.issue["countries"] if
                 r["country"]=="Ukraine")
        p0=row["original_2027_p_active"]
        deaths=row["origin_deaths_best_2025"]
        self.assertGreaterEqual(deaths,25)
        values=[p_scaled(p0,deaths,self.beta,a) for a in ALPHAS]
        self.assertTrue(all(abs(p-values[0])<1e-14 for p in values))
        self.assertAlmostEqual(values[-1],
                               row["log1p_shadow_p_active_2027"],places=11)

    def test_folds_compare_same_outcomes_and_source_probabilities(self):
        rows=[{"outcome":0,"p_original_binary":.2,"origin_deaths":0},
              {"outcome":1,"p_original_binary":.7,"origin_deaths":23},
              {"outcome":1,"p_original_binary":.8,"origin_deaths":200}]
        result=fold_scores(rows,self.beta)
        self.assertEqual(set(result),set(str(a) for a in ALPHAS))
        for m in result.values():
            self.assertGreater(m["brier"],0)
            self.assertGreater(m["logloss"],0)

    def test_complete_2027_frozen_scenario_replays_and_zero_alpha_stabilizes_top10(self):
        r=issued_counterfactual(self.issue,self.previous,self.alerts)
        self.assertEqual(set(r),set(str(a) for a in ALPHAS))
        self.assertEqual(r["0.0"]["topk_mandatory_possible"]["0"]["mandatory_n"],10)
        self.assertEqual(r["0.0"]["topk_mandatory_possible"]["0"]["possible_n"],10)
        self.assertEqual(r["1.0"]["topk_mandatory_possible"]["0"]["mandatory_n"],2)
        self.assertEqual(r["1.0"]["topk_mandatory_possible"]["1"]["mandatory_n"],3)
        self.assertEqual(r["1.0"]["n_countries"],196)
        self.assertAlmostEqual(
            r["1.0"]["mean_10death_full_width_pp"],
            self.previous["scenario_summaries"][2]["mean_full_envelope_width_pp"],
            places=8)
        self.assertAlmostEqual(r["1.0"]["Burundi_2025_0_to_10_case"]["alpha_10death_shift_pp"],
                               18.535392449,places=7)
        for alpha in ALPHAS:
            self.assertAlmostEqual(
                r[str(alpha)]["Burundi_2025_0_to_10_case"]["issued_p"],.22621207819)
            self.assertEqual(len(r[str(alpha)]["all_country_counterfactual_bands"]),196)
        self.assertLess(r["0.0"]["mean_10death_full_width_pp"],
                        r["1.0"]["mean_10death_full_width_pp"])

    def test_pareto_dominance_not_a_winner_selection(self):
        hist={"0.0":{"brier":.042},"0.25":{"brier":.040},
              "0.5":{"brier":.038},"0.75":{"brier":.037},
              "1.0":{"brier":.036}}
        stress={str(a):{"mean_10death_full_width_pp":a}
                for a in ALPHAS}
        front=nondominated(hist,stress)
        self.assertEqual(len(front),5)
        self.assertTrue(all(r["non_dominated_on_these_two_exploratory_axes"]
                            for r in front))
        hist["0.25"]["brier"]=.045
        front=nondominated(hist,stress)
        self.assertFalse(front[1]["non_dominated_on_these_two_exploratory_axes"])
        self.assertEqual(front[1]["dominated_by_alpha"],[0.0])

    def test_changed_prior_provenance_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"provenance"):
            issued_counterfactual(self.issue,{"schema":"tampered"},self.alerts)


if __name__=="__main__":
    unittest.main()
