"""Fictional binary panels; no real country identities or private records."""
import copy
import unittest

from diagnose_geo2027_transition_skill import (
    describe, make_holdout_rows, summarize
)
from backtest_archived_country_vintages import SOURCES


def fake_archives():
    # Full 196-country, 1989-2025 toy binary sources, with origin-only features.
    editions = {}
    for edition, max_year in (("23.1", 2022), ("24.1", 2023),
                              ("25.1", 2024), ("26.1", 2025)):
        countries = {}
        for index in range(196):
            base = {year: int(index % 5 == 0 and
                               (year % 3 == 0 or year >= 2017))
                    for year in range(1989, max_year + 1)}
            if max_year >= 2024:
                base[2024] = int(index < 35)
            if max_year >= 2025:
                base[2025] = int(index < 34)
            countries[index + 1] = base
        editions[edition] = countries
    return editions


def fake_metadata():
    return {v: {"sha256": d["sha256"]} for v, d in SOURCES.items()}


class GeoTransitionAttributionTests(unittest.TestCase):
    def test_brier_change_decomposition(self):
        entries = [
            {"origin_state": 0, "outcome": 1, "p_model": .4,
             "p_global_markov": .2, "p_baseline_global_5y": .1},
            {"origin_state": 1, "outcome": 0, "p_model": .6,
             "p_global_markov": .7, "p_baseline_global_5y": .2},
            {"origin_state": 0, "outcome": 0, "p_model": .1,
             "p_global_markov": .2, "p_baseline_global_5y": .3},
        ]
        out = describe(entries)
        self.assertEqual(out["n"], 3)
        self.assertEqual(out["transitions"], 2)
        self.assertEqual(out["newly_active"], 1)
        self.assertEqual(out["resolved"], 1)
        self.assertEqual(out["brier"]["hard_origin_persistence"], 2 / 3)
        self.assertAlmostEqual(out["brier"]["p_model"], (.36+.36+.01)/3)

    def test_frozen_origin_and_target_release_separation(self):
        vintages = fake_archives()
        rows = make_holdout_rows(vintages)
        self.assertEqual(len(rows), 392)
        self.assertEqual({r["target_year"] for r in rows}, {2024, 2025})
        self.assertEqual(sum(r["outcome"] for r in rows), 69)
        self.assertEqual(len({(r["country_id"], r["target_year"]) for r in rows}), 392)
        self.assertEqual(
            sum(r["origin_year"] == 2022 and r["outcome"] == 1 for r in rows), 35)
        report = summarize(rows, fake_metadata())
        self.assertEqual(report["overall"]["n"], 392)
        self.assertEqual(report["overall"]["positives"], 69)
        self.assertEqual(report["prospective_2027_outcomes_resolved"], 0)
        self.assertEqual(report["prospective_2027_forecast_modified"], False)
        for category in ("0", "1"):
            self.assertIn(category, report["ex_ante_origin_state"])
        self.assertEqual(
            report["ex_post_outcome_class_descriptive_only"]["changed"]["n"] +
            report["ex_post_outcome_class_descriptive_only"]["unchanged"]["n"], 392)

    def test_missing_target_does_not_become_negative(self):
        vintages = fake_archives()
        del vintages["25.1"][1][2024]
        with self.assertRaisesRegex(ValueError, "Unresolved later-vintage"):
            make_holdout_rows(vintages)

    def test_future_source_leak_fails_closed(self):
        vintages = fake_archives()
        vintages["23.1"][1][2023] = 1
        with self.assertRaisesRegex(ValueError, "chronology"):
            make_holdout_rows(vintages)
        vintages = fake_archives()
        vintages["25.1"][1][2025] = 1
        with self.assertRaisesRegex(ValueError, "chronology"):
            make_holdout_rows(vintages)

    def test_unexpected_metadata_fails_closed(self):
        rows = make_holdout_rows(fake_archives())
        metadata = fake_metadata()
        metadata["23.1"]["sha256"] = "not-official"
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            summarize(rows, metadata)
        altered = copy.deepcopy(rows)
        altered[0]["outcome"] = 1 - altered[0]["outcome"]
        with self.assertRaisesRegex(ValueError, "392/69"):
            summarize(altered, fake_metadata())


if __name__ == "__main__":
    unittest.main()
