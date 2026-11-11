"""Synthetic-only tests for exact year-stratified null; no private or individual data."""
import copy
import math
import unittest

from diagnose_geo2027_exact_alert_null import (
    analyze, convolve, fixed_budget_null, hypergeom_pmf, quantile,
    within_year_auc,
)
from evaluate_geo2027_transition_alerts import run as prior_study
from test_evaluate_geo2027_transition_alerts import (
    source_meta, toy_report, toy_rows,
)


def fixed_toy():
    rows = toy_rows()
    report = prior_study(rows, source_meta(), toy_report(rows))
    return rows, report


class GeoExactConditionalAlertNullTests(unittest.TestCase):
    def test_hypergeometric_matches_hand_counted_combinations(self):
        pmf = hypergeom_pmf(4, 2, 2)
        self.assertEqual(set(pmf), {0, 1, 2})
        self.assertAlmostEqual(pmf[0], 1 / 6)
        self.assertAlmostEqual(pmf[1], 4 / 6)
        self.assertAlmostEqual(pmf[2], 1 / 6)
        combined = convolve(pmf, pmf)
        self.assertAlmostEqual(sum(combined.values()), 1)
        self.assertAlmostEqual(combined[0], 1 / 36)
        self.assertAlmostEqual(combined[4], 1 / 36)
        self.assertEqual(quantile(pmf, 0.5), 1)

    def test_invalid_hypergeometric_rejected(self):
        for args in ((0, 0, 0), (10, 11, 1), (10, 1, 11), (10, -1, 3),
                     (10, 1, -2), (10, True, 3), (10, 1.3, 2)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    hypergeom_pmf(*args)

    def test_year_stratified_exact_null_with_no_boundary_tie(self):
        rows, report = fixed_toy()
        for state in (0, 1):
            pooled = fixed_budget_null(rows, state)
            self.assertEqual(pooled["null_status"],
                             "EXACT_YEAR_CONDITIONAL_EXCHANGEABILITY")
            self.assertFalse(pooled["cutoff_tie"])
            cells = pooled["year_conditional_null"]["cells"]
            self.assertEqual([c["year"] for c in cells], [2024, 2025])
            self.assertEqual(sum(c["selected_slots"] for c in cells),
                             pooled["alert_capacity"])
            self.assertAlmostEqual(sum(
                pooled["year_conditional_null"]["hit_count_probability_mass"].values()
            ), 1)
            self.assertGreaterEqual(pooled["year_conditional_null"][
                "one_sided_probability_random_hits_at_least_observed"], 0)
            self.assertLessEqual(pooled["year_conditional_null"][
                "one_sided_probability_random_hits_at_least_observed"], 1)
            for year in (2024, 2025):
                by_year = fixed_budget_null(rows, state, year)
                self.assertEqual(len(by_year["year_conditional_null"]["cells"]), 1)

    def test_tied_baseline_never_promises_unique_alerts_or_pvalue(self):
        rows, _ = fixed_toy()
        for state in (0, 1):
            b = fixed_budget_null(rows, state, model="global_markov")
            self.assertTrue(b["cutoff_tie"])
            self.assertEqual(b["null_status"], "UNDEFINED_BOUNDARY_TIE")
            self.assertIsNone(b["year_conditional_null"])

    def test_within_year_auc_excludes_global_year_prevalence_confounding(self):
        rows, _ = fixed_toy()
        for row in rows:
            row["p_global_markov"] = (
                0.10 if row["target_year"] == 2024 else 0.06
            ) if row["origin_state"] == 0 else (
                0.75 if row["target_year"] == 2024 else 0.65
            )
        for state in (0, 1):
            value = within_year_auc(rows, state, "global_markov")
            self.assertEqual(len(value["by_year"]), 2)
            self.assertAlmostEqual(value["auc_pair_weighted"], 0.5)

    def test_prior_report_immutability_and_no_prospective_claims(self):
        rows, prior = fixed_toy()
        result = analyze(rows, prior)
        self.assertEqual(set(result["risk_sets"]), {"0", "1"})
        self.assertTrue(result["probabilities_are_not_confirmatory_p_values"])
        self.assertEqual(result["prospective_2027_outcomes_observed"], 0)
        self.assertTrue(result["prospective_2027_forecasts_unchanged"])
        for state in ("0", "1"):
            self.assertEqual(result["risk_sets"][state]["transitions"],
                             8 if state == "0" else 10)
            for model in ("country_markov", "global_markov"):
                self.assertIn("within_year_auc",
                              result["risk_sets"][state]["models"][model])
        broken = copy.deepcopy(prior)
        broken["per_origin_risk_group"]["0"]["models"]["country_markov"][
            "top_k"]["hits_min"] += 1
        with self.assertRaisesRegex(ValueError, "tie-safe"):
            analyze(rows, broken)
        altered = copy.deepcopy(rows)
        altered[0]["outcome"] = 1 - altered[0]["outcome"]
        with self.assertRaisesRegex(ValueError, "holdout"):
            analyze(altered, prior)


if __name__ == "__main__":
    unittest.main()
