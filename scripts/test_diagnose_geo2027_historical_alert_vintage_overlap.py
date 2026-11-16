"""Synthetic, tie-aware tests for historical GEO H2 vintage top-k comparison."""
from __future__ import annotations

import copy
import unittest

from test_diagnose_geo2028_historical_forecast_vintage_drift import synthetic
from diagnose_geo2027_historical_alert_vintage_overlap import (
    admissible_topk, group_comparison, study,
)


class HistoricalAlertVintageOverlapTests(unittest.TestCase):
    def test_boundary_ties_never_masquerade_as_unique_topk(self):
        ambiguous = admissible_topk({1: .8, 2: .5, 3: .5, 4: .1}, 2)
        self.assertEqual(ambiguous["ordered"], [1, 2])
        self.assertEqual(ambiguous["mandatory"], {1})
        self.assertEqual(ambiguous["possible"], {1, 2, 3})
        self.assertFalse(ambiguous["boundary_selection_unique"])
        unique = admissible_topk({1: .8, 2: .6, 3: .5, 4: .1}, 2)
        self.assertEqual(unique["mandatory"], {1, 2})
        self.assertTrue(unique["boundary_selection_unique"])

    def test_definite_changes_distinct_from_tie_break_exchanges(self):
        old = {
            1: {"origin_state": 0, "p_model_h2": .8},
            2: {"origin_state": 0, "p_model_h2": .5},
            3: {"origin_state": 0, "p_model_h2": .5},
            4: {"origin_state": 0, "p_model_h2": .1},
        }
        revised = {
            1: {"origin_state": 0, "q_local": [0.1, 0.8]},
            2: {"origin_state": 0, "q_local": [0.1, 0.8]},
            3: {"origin_state": 0, "q_local": [0.1, 0.8]},
            4: {"origin_state": 0, "q_local": [0.9, 0.9]},
        }
        res = group_comparison(old, revised, 0, {i: str(i) for i in old}, k=2)
        self.assertEqual(res["deterministic_swaps_n"], 1)
        self.assertEqual(res["definite_exits_n"], 0)  # old #2 was not mandatory
        self.assertEqual(res["definite_entries_n"], 1)  # old #4 was never eligible by ties

    def test_synthetic_all_six_edition_pairs_retain_scientific_limits(self):
        vintages, meta, original27, original28 = synthetic()
        names = {r["country_id"]: r["country"] for r in original28["countries"]}
        report = study(vintages, meta, names)
        self.assertEqual(len(report["paired_comparisons"]), 6)
        self.assertEqual(report["horizon_years"], 2)
        self.assertTrue(report["six_overlapping_edition_pairs_not_independent"])
        self.assertFalse(report["current_2027_alert_change_directly_measured"])
        self.assertEqual(report["n_2027_outcomes_resolved"], 0)
        for fold in report["paired_comparisons"]:
            for group in fold["groups"].values():
                self.assertEqual(len(group["old_topk"]), group["budget"])
                self.assertEqual(len(group["revised_topk"]), group["budget"])
                self.assertEqual(
                    group["deterministic_swaps_n"], len(group["deterministic_exited"]))
                self.assertEqual(
                    group["deterministic_swaps_n"], len(group["deterministic_entered"]))
        # 25.1 -> 26.1 synthetic 2024 origin label revision should be
        # separately counted without changing old-defined risk membership.
        final = report["paired_comparisons"][-1]
        self.assertEqual(sum(g["changed_origin_state_n"] for g in final["groups"].values()), 1)

    def test_reject_wrong_source_provenance(self):
        vintages, meta, d27, d28 = synthetic()
        names = {r["country_id"]: r["country"] for r in d28["countries"]}
        broken = copy.deepcopy(meta)
        broken["23.1"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA"):
            study(vintages, broken, names)


if __name__ == "__main__":
    unittest.main()
