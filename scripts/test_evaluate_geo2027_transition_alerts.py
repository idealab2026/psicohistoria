"""Adversarial fictional data only. Real country scores/labels never enter tests."""
import copy
import unittest

from backtest_archived_country_vintages import SOURCES
from diagnose_geo2027_transition_skill import describe
from evaluate_geo2027_transition_alerts import (
    auc_with_midrank_ties, tie_group_average_precision, tie_safe_top_k,
    score_for_transition, metrics_by_group, run,
)


def toy_rows():
    rows = []
    for target, active_n, persist_n, first_entry, last_entry in (
        (2024, 37, 31, 38, 41),
        (2025, 34, 30, 35, 38),
    ):
        for country in range(1, 197):
            active = int(country <= active_n)
            target_state = int(country <= persist_n or
                               first_entry <= country <= last_entry)
            p_model = (0.08 + country / 5000) if not active else (0.65 + country / 10000)
            p_global = 0.05 if not active else 0.75
            rows.append({
                "country_id": country,
                "origin_state": active,
                "outcome": target_state,
                "target_year": target,
                "p_model": p_model,
                "p_global_markov": p_global,
                "p_baseline_global_5y": 0.15,
            })
    return rows


def toy_report(rows):
    return {
        "schema": "idealab.psico.geo2027_transition_attribution_cross_release.v1",
        "ex_ante_origin_state": {
            str(s): describe([r for r in rows if r["origin_state"] == s])
            for s in (0, 1)
        },
    }


def source_meta():
    return {k: {"sha256": v["sha256"]} for k, v in SOURCES.items()}


class TransitionAlertRankingTests(unittest.TestCase):
    def test_identical_scores_do_not_imply_unique_top_k_hits(self):
        scores = [(0.2, 1), (0.2, 1), (0.2, 0), (0.2, 0)]
        self.assertEqual(auc_with_midrank_ties(scores), 0.5)
        self.assertEqual(tie_group_average_precision(scores), 0.5)
        alerts = tie_safe_top_k(scores, 2)
        self.assertTrue(alerts["boundary_tie"])
        self.assertEqual((alerts["hits_min"], alerts["hits_max"]), (0, 2))
        self.assertEqual(alerts["random_expected_hits"], 1)

    def test_perfect_separation_and_ranking_are_one(self):
        scores = [(0.9, 1), (0.8, 1), (0.3, 0), (0.1, 0)]
        self.assertEqual(auc_with_midrank_ties(scores), 1.0)
        self.assertEqual(tie_group_average_precision(scores), 1.0)
        alerts = tie_safe_top_k(scores, 2)
        self.assertEqual((alerts["hits_min"], alerts["hits_max"]), (2, 2))
        self.assertFalse(alerts["boundary_tie"])

    def test_empty_or_single_class_discrimination_is_undefined(self):
        self.assertIsNone(auc_with_midrank_ties([(0.1, 0), (0.2, 0)]))
        self.assertIsNone(tie_group_average_precision([(0.1, 0), (0.2, 0)]))
        self.assertIsNone(auc_with_midrank_ties([(0.2, 1), (0.5, 1)]))
        with self.assertRaisesRegex(ValueError, "capacity"):
            tie_safe_top_k([(0.2, 1)], 2)

    def test_resolution_flips_model_and_outcome_but_preserves_brier(self):
        row = {"origin_state": 1, "outcome": 0, "p_model": .83,
               "p_global_markov": .71}
        p, y = score_for_transition(row, "country_markov")
        self.assertAlmostEqual(p, .17)
        self.assertEqual(y, 1)
        self.assertAlmostEqual((p-y)**2, (.83-0)**2)
        with self.assertRaisesRegex(ValueError, "Unregistered"):
            score_for_transition(row, "unknown")

    def test_two_year_two_risk_set_aggregates_and_fixed_budgets(self):
        rows = toy_rows()
        result = run(rows, source_meta(), toy_report(rows))
        self.assertEqual(result["per_origin_risk_group"]["0"]["transitions"], 8)
        self.assertEqual(result["per_origin_risk_group"]["1"]["transitions"], 10)
        self.assertEqual(result["per_origin_risk_group"]["0"]["n"], 321)
        self.assertEqual(result["per_origin_risk_group"]["1"]["n"], 71)
        self.assertEqual(result["per_target_year"]["2024"]["0"]["transitions"], 4)
        self.assertEqual(result["per_target_year"]["2025"]["1"]["transitions"], 4)
        self.assertEqual(result["per_origin_risk_group"]["0"]["fixed_alert_capacity"], 10)
        self.assertEqual(result["per_origin_risk_group"]["1"]["fixed_alert_capacity"], 5)
        self.assertFalse(result["prospective_2027_prediction_documents_modified"])
        self.assertEqual(result["prospective_2027_results_observed"], 0)
        self.assertAlmostEqual(
            result["per_target_year"]["2024"]["0"]["models"]["global_markov"]["roc_auc_midrank"], .5
        )

    def test_refuse_modified_sources_outcomes_and_reference(self):
        rows = toy_rows()
        report = toy_report(rows)
        altered = copy.deepcopy(rows)
        altered[0]["outcome"] = 1 - altered[0]["outcome"]
        with self.assertRaisesRegex(ValueError, "holdout altered"):
            run(altered, source_meta(), report)
        metadata = source_meta()
        metadata["23.1"]["sha256"] = "fake"
        with self.assertRaisesRegex(ValueError, "provenance mismatch"):
            run(rows, metadata, report)
        broken_report = copy.deepcopy(report)
        broken_report["ex_ante_origin_state"]["0"]["brier"]["p_model"] = 0.25
        with self.assertRaisesRegex(ValueError, "original Brier"):
            run(rows, source_meta(), broken_report)


if __name__ == "__main__":
    unittest.main()
