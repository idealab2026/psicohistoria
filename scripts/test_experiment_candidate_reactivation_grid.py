#!/usr/bin/env python3
"""Adversarial synthetic fixtures only; NEVER actual UCDP predictions."""
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiment_candidate_reactivation_grid as e
from check_ucdp_candidate_asof import SourceError


def make_csv(rows):
    names = ("id", "country_id", "type_of_violence", "date_prec",
             "date_start", "date_end", "best")
    stream = io.StringIO(newline="")
    w = csv.DictWriter(stream, fieldnames=names)
    w.writeheader()
    for r in rows:
        w.writerow(dict(zip(names, r)))
    return stream.getvalue().encode("utf8")


class GridTests(unittest.TestCase):
    def test_all_years_and_missing_2023_explicit(self):
        self.assertEqual(e.YEARS, (2021, 2022, 2024, 2025, 2026))
        self.assertEqual(e.TRAIN, (2021, 2022, 2024, 2025))
        for year in e.YEARS:
            self.assertIn(f"{year%100:02d}_01_", e.source_url(year, 3))
        for year, month in ((2023, 3), (2021, 4), (2020, 9)):
            with self.assertRaises(SourceError):
                e.source_url(year, month)

    def test_q1_nonstate_signal_and_q3_exact_30_and_90_boundaries(self):
        origin = make_csv([
            ("s", 1, 1, 1, "2026-03-31", "2026-03-31", 3),
            ("n", 1, 2, 1, "2026-03-30", "2026-03-30", 12),
            ("u", 1, 3, 1, "2026-01-20", "2026-01-20", 8),
            ("z", 1, 1, 0, "2026-03-20", "2026-03-20", 10000),
            ("o", 1, 1, 1, "2026-03-31", "2026-04-01", 999),
        ])
        stats, values = e.parse_original(origin, 2026, 3, {1})
        self.assertEqual(values["prior_state"][1], 3)
        self.assertEqual(values["prior_other"][1], 20)
        self.assertEqual(stats["exclusions"]["unknown_precision_zero"], 1)
        future = make_csv([
            ("a", 1, 1, 1, "2026-05-01", "2026-05-01", 1),
            ("b", 1, 1, 1, "2026-05-30", "2026-05-30", 4),
            ("c", 1, 1, 1, "2026-05-31", "2026-05-31", 5),
            ("d", 1, 1, 1, "2026-07-29", "2026-07-29", 6),
            ("e", 1, 1, 1, "2026-07-30", "2026-07-30", 99),
            ("f", 1, 1, 1, "2026-04-30", "2026-05-02", 20),
            ("g", 1, 1, 3, "2026-05-01", "2026-05-01", 777),
        ])
        _, values = e.parse_original(future, 2026, 9, {1})
        self.assertEqual(values["30"][1], 5)
        self.assertEqual(values["90"][1], 16)

    def test_invalid_source_and_bad_dates_fail_closed(self):
        for rows in (
            [("a", 1, 1, 1, "2025-01-02", "2025-01-01", 2)],
            [("a", 1, 1, 1, "2025-01-02", "2025-01-02", -2)],
            [("a", 1, 1, 1, "2025-01-02", "2025-01-02", 2)] * 2,
            [("a", 1, 1, 9, "2025-01-02", "2025-01-02", 2)],
        ):
            with self.subTest(rows=rows), self.assertRaises(SourceError):
                e.parse_original(make_csv(rows), 2025, 3, {1})

    def test_fit_k20_both_model_families_and_tie_scores(self):
        train = []
        for year in (2021, 2022, 2024, 2025):
            for country in range(1, 197):
                train.append({
                    "country_id": country,
                    "q1_state_best": country % 11,
                    "q1_other_best": 15 if country % 3 == 0 else 0,
                    "future_best_30": 6 if country % 5 == 0 else 0,
                    "future_best_90": 30 if country % 7 == 0 else 0,
                })
        fit = e.fits(train, 10, 30)
        self.assertEqual(fit["shrinkage_k"], 20)
        self.assertEqual(fit["train_n_at_risk"], sum(r["q1_state_best"] < 10 for r in train))
        row = {"q1_state_best": 4, "q1_other_best": 22}
        p = e.predict(row, fit)
        self.assertEqual(set(p), set(e.MODELS))
        self.assertTrue(all(0 < x < 1 for x in p.values()))
        records = train[:196]
        metric = e.score(records, "other_violence", 10, 30, fit)
        self.assertGreater(metric["n"], 100)
        self.assertIn("expected_hits_random_tie_break", metric["top10_with_tie_bounds"])

    def test_frozen_2026_origin_outcomes_and_source_sha(self):
        names = [{"country_id": i, "country": f"synthetic-{i}"}
                 for i in range(1, 197)]
        universe = json.dumps({"countries": names}).encode("utf8")
        originals = {}
        for year in e.YEARS:
            for month in (3, 9):
                date = f"{year}-02-10" if month == 3 else f"{year}-05-12"
                originals[e.source_url(year, month)] = make_csv([
                    (f"state-{year}-{month}", 1, 1, 1, date, date, 3 if month == 3 else 25),
                    (f"other-{year}-{month}", 2, 2, 1, date, date, 2),
                ])
        vector = []
        for i in range(1, 197):
            vector.append({
                "country_id": i,
                "prior_best_q1_2026": 3 if i == 1 else 0,
                "h30": {"target_best_q3_2026": 25 if i == 1 else 0},
                "h90": {"target_best_q3_2026": 25 if i == 1 else 0},
            })
        frozen = {
            "status": "RETROSPECTIVE_ONLY_NOT_ISSUED",
            "universe_sha256": hashlib.sha256(universe).hexdigest(),
            "retrospective_2026_country_vector": vector,
        }
        pins = {(year, month): hashlib.sha256(originals[e.source_url(year, month)]).hexdigest()
                for year in e.YEARS for month in (3, 9)}
        report = e.build_report(fetcher=originals.__getitem__, universe_raw=universe,
                                frozen=frozen, source_pins=pins)
        self.assertEqual(report["n_countries"], 196)
        self.assertEqual(len(report["source_snapshots"]), 10)
        self.assertEqual(report["prospective_issued_probabilities"], 0)
        self.assertFalse(report["historical_original_release_dates_certified"])
        self.assertEqual(report["holdout_2026_model_scores"]["5"]["30"]["climatology"]["positive"], 1)
        originals[e.source_url(2026, 9)] += b"\n"
        with self.assertRaises(SourceError):
            e.build_report(fetcher=originals.__getitem__, universe_raw=universe,
                           frozen=frozen, source_pins=pins)


if __name__ == "__main__":
    unittest.main()
