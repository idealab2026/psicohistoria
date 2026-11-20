#!/usr/bin/env python3
"""Only synthetic fixtures. No historical labels or network requests in tests."""
from collections import defaultdict
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_candidate_to_annual_ged as old
import audit_ged2024_annual_vintage_drift as study
from test_audit_candidate_to_annual_ged import ged_zip


def fixture():
    countries = [{"country_id": i, "country": f"Synthetic country {i}"}
                 for i in range(1, 197)]
    universe = json.dumps({"countries": countries}).encode()
    first = ged_zip(2024, [
        ("a", 2024, 1, 1, 1, "2024-05-12", "2024-05-12", 5),
        ("irrelevant", 2023, 1, 1, 1, "2023-05-12", "2023-05-12", 900),
    ])
    later = ged_zip(2025, [
        ("b", 2024, 2, 1, 1, "2024-05-13", "2024-05-13", 7),
        ("future", 2025, 1, 1, 1, "2025-05-12", "2025-05-12", 999),
    ])
    pinned = {2024: hashlib.sha256(first).hexdigest(),
              2025: hashlib.sha256(later).hexdigest()}
    sources = {old.GED_URL[2024]: first, old.GED_URL[2025]: later}
    vectors = []
    for year in (2024, 2025):
        for c in countries:
            i = c["country_id"]
            active = int(year == 2024 and i == 1)
            vectors.append({
                "year": year, "country_id": i, "country": c["country"],
                "candidate_q1_prior_best": 0,
                "candidate_q3_may30_best": 5 * active,
                "candidate_q3_90_best": 5 * active,
                "ged_annual_may30_best": 5 * active,
                "ged_annual_90_best": 5 * active,
            })
    previous_metrics = {}
    for threshold in old.THRESHOLDS:
        previous_metrics[str(threshold)] = {}
        for h in old.HORIZONS:
            prior = defaultdict(int)
            q3 = defaultdict(int, {1: 5})
            annual = defaultdict(int, {1: 5})
            previous_metrics[str(threshold)][str(h)] = {
                "q3_vs_annual": old.paired_metrics(
                    prior, q3, annual, threshold,
                    {c["country_id"]: c["country"] for c in countries})
            }
    previous = {
        "status": "RETROSPECTIVE_FINAL_VINTAGE_COMPARISON_NOT_PROSPECTIVE",
        "annual_version_by_year": {"2024": "GED 25.1", "2025": "GED 26.1"},
        "prospective_issued_probabilities": 0, "cohorts_modified": 0,
        "n_countries": 196,
        "country_universe_sha256": hashlib.sha256(universe).hexdigest(),
        "country_vectors": vectors,
        "by_year_threshold_and_horizon": {"2024": previous_metrics},
        "source_details": [
            {"source_family": "annual_GED", "year": y,
             "url": old.GED_URL[y], "sha256": pinned[y]}
            for y in (2024, 2025)
        ],
    }
    return universe, sources, pinned, previous


class LaterAnnualVintageSyntheticTests(unittest.TestCase):
    def build(self, universe, sources, pinned, previous):
        return study.build_report(
            annual_fetcher=sources.__getitem__, raw_universe=universe,
            source_pins=pinned, previous=previous
        )

    def test_event_year_from_later_release_is_not_release_year(self):
        universe, sources, pins, previous = fixture()
        raw = sources[old.GED_URL[2025]]
        _, rows, ids = old.read_annual(raw, 2024, set(range(1,197)),
                                      release_year=2025)
        death, selected, _ = old.rollup(rows, 2024, 30)
        self.assertEqual(death[2], 7)
        self.assertEqual(death[1], 0)
        self.assertNotIn("future", ids)
        self.assertEqual(selected[2], ["b"])
        with self.assertRaises(old.SourceError):
            old.read_annual(raw, 2025, set(range(1,197)), release_year=2024)
        with self.assertRaises(old.SourceError):
            old.read_annual(raw, 2024, set(range(1,197)), release_year=2023)

    def test_full_196_country_comparison_and_label_flips(self):
        universe, sources, pins, previous = fixture()
        report = self.build(universe, sources, pins, previous)
        self.assertEqual(report["status"], "RETROSPECTIVE_ANNUAL_VINTAGE_DRIFT_NOT_PROSPECTIVE")
        self.assertEqual(report["n_countries"], 196)
        self.assertFalse(report["risk_set_uses_later_ged"])
        self.assertEqual(report["prospective_issued_probabilities"], 0)
        self.assertEqual(report["cohorts_modified"], 0)
        cell = report["by_threshold_and_horizon"]["5"]["30"]
        self.assertEqual(cell["first_annual_vs_later_annual"]["disagreements"], 2)
        self.assertEqual(cell["first_annual_vs_later_annual"]["first_only_country_ids"], [1])
        self.assertEqual(cell["first_annual_vs_later_annual"]["later_only_country_ids"], [2])
        self.assertEqual(cell["candidate_q3_vs_later_annual"]["both_positive"], 0)
        self.assertEqual(len(report["country_annual_best_changes"]), 2)
        self.assertEqual(report["first_to_later_annual_exact_event_id_overlap"]["30"][
            "first_annual_ids_missing_in_later_exact_id"], 1)

    def test_original_source_sha_change_blocks_without_scoring(self):
        universe, sources, pins, previous = fixture()
        sources = dict(sources)
        sources[old.GED_URL[2025]] += b"extra"
        with self.assertRaisesRegex(old.SourceError, "changed bytes"):
            self.build(universe, sources, pins, previous)

    def test_missing_or_duplicate_original_country_blocks(self):
        universe, sources, pins, previous = fixture()
        previous = copy.deepcopy(previous)
        previous["country_vectors"].append(copy.deepcopy(previous["country_vectors"][0]))
        with self.assertRaises(old.SourceError):
            self.build(universe, sources, pins, previous)

    def test_original_ged251_country_level_replay_mismatch_blocks(self):
        universe, sources, pins, previous = fixture()
        previous = copy.deepcopy(previous)
        previous["country_vectors"][0]["ged_annual_may30_best"] = 20
        with self.assertRaisesRegex(old.SourceError, "GED25.1 replay"):
            self.build(universe, sources, pins, previous)

    def test_prior_risk_set_never_uses_later_ged(self):
        universe, sources, pins, previous = fixture()
        previous = copy.deepcopy(previous)
        previous["country_vectors"][0]["candidate_q1_prior_best"] = 5
        with self.assertRaisesRegex(old.SourceError, "Prior Candidate-vs-GED"):
            self.build(universe, sources, pins, previous)

    def test_old_registry_source_pin_disagreement_blocks(self):
        universe, sources, pins, previous = fixture()
        previous = copy.deepcopy(previous)
        previous["source_details"][1]["sha256"] = "0" * 64
        with self.assertRaisesRegex(old.SourceError, "registry"):
            self.build(universe, sources, pins, previous)

    def test_no_cross_year_violence_leakage_or_undocumented_precision(self):
        universe, sources, pins, previous = fixture()
        raw = sources[old.GED_URL[2025]]
        meta, rows, ids = old.read_annual(raw, 2024, set(range(1,197)),
                                          release_year=2025)
        self.assertEqual(meta["target_year_rows"], 1)
        self.assertNotIn("future", ids)
        self.assertEqual({r[0] for r in rows}, {"b"})


if __name__ == "__main__":
    unittest.main()
