#!/usr/bin/env python3
"""Synthetic adversarial tests. NO rows in this file are actual UCDP observations."""
from datetime import date
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiment_candidate_30_90_holdout as research
from check_ucdp_candidate_asof import SourceError


def csv_bytes(rows):
    names = ("id", "country_id", "type_of_violence", "date_prec", "date_start", "date_end", "best")
    s = io.StringIO(newline="")
    w = csv.DictWriter(s, fieldnames=names)
    w.writeheader()
    for row in rows:
        w.writerow(dict(zip(names, row)))
    return s.getvalue().encode("utf8")


def fake_universe():
    return json.dumps({"countries": [
        {"country_id": i, "country": f"Synthetic country {i}"} for i in range(1, 197)
    ]}).encode("utf8")


class ShortHorizonTests(unittest.TestCase):
    def test_predeclared_exact_windows_and_ambiguous_dates(self):
        rows = [
            ("a", 1, 1, 1, "2026-05-01", "2026-05-01", 25),
            ("b", 1, 1, 1, "2026-05-30", "2026-05-30", 25),
            ("c", 1, 1, 1, "2026-05-31", "2026-05-31", 25),
            ("d", 1, 1, 1, "2026-07-29", "2026-07-29", 25),
            ("e", 1, 1, 1, "2026-07-30", "2026-07-30", 25),
            ("f", 1, 1, 3, "2026-06-01", "2026-06-01", 25),
            ("g", 1, 1, 1, "2026-04-30", "2026-05-01", 25),
            ("h", 2, 3, 1, "2026-05-12", "2026-05-12", 900),
        ]
        m, events = research.extract_state_based(csv_bytes(rows), 2026, "outcome", set(range(1, 197)))
        self.assertEqual(m["retained_statebased_high_precision_within_outer_window"], 5)
        self.assertEqual(m["excluded_type1_low_date_precision"], 1)
        start = date(2026, 5, 1)
        self.assertEqual(sum(best for _, country, s, e, best in events
                             if s >= start and e <= date(2026, 5, 30)), 50)
        self.assertEqual(sum(best for _, country, s, e, best in events
                             if s >= start and e <= date(2026, 7, 29)), 100)

    def test_duplicate_date_inversion_invalid_precision(self):
        good = ("a", 1, 1, 1, "2026-03-01", "2026-03-01", 25)
        bads = [
            [good, good],
            [("a", 1, 1, 1, "2026-03-02", "2026-03-01", 1)],
            [("a", 1, 1, 0, "2026-03-01", "2026-03-01", 1)],
            [("a", 1, 1, 1, "2026-03-01", "2026-03-01", -5)],
            [("a", 1, 1, 1, "2026-03-01", "2026-03-01", 5),
             ("b", 1, 1, 1, "2026-03-01", "2026-03-01", 1)],
        ]
        for index, rows in enumerate(bads[:-1]):
            with self.subTest(index=index), self.assertRaises(SourceError):
                research.extract_state_based(csv_bytes(rows), 2026, "origin", {1})

    def test_probabilities_are_shrunk_and_fit_uses_exactly_two_years(self):
        train = [
            {"prior_best": 0 if i % 2 == 0 else 200, "y30": int(i % 4 == 0)}
            for i in range(392)
        ]
        fit = research.estimates(train, "y30")
        for x in (0, 5, 26, 999):
            p = research.predict(x, fit)
            self.assertTrue(all(0 < value < 1 for value in p.values()))
        with self.assertRaises(SourceError):
            research.estimates(train[:391], "y30")

    def test_temporal_holdout_cannot_influence_fit(self):
        universe = fake_universe()
        archives = {}
        for year in research.YEARS:
            for month in (3, 9):
                rows = [
                    (f"a-{year}-{month}", 1, 1, 1, f"{year}-03-05" if month == 3 else f"{year}-05-10",
                     f"{year}-03-05" if month == 3 else f"{year}-05-10", 26),
                    (f"b-{year}-{month}", 2, 1, 1, f"{year}-02-01" if month == 3 else f"{year}-06-01",
                     f"{year}-02-01" if month == 3 else f"{year}-06-01", 3),
                ]
                archives[research.archive_url(year, month)] = csv_bytes(rows)
        sha = {year: hashlib.sha256(archives[research.archive_url(year, 9)]).hexdigest()
               for year in research.YEARS}
        report = research.build_report(fetcher=archives.__getitem__,
                                       universe_raw=universe, q3_sha=sha)
        self.assertEqual(report["n_countries"], 196)
        self.assertEqual(report["retrospective_2026_metrics"]["30"]["holdout_positive_count"], 1)
        self.assertEqual(report["retrospective_2026_metrics"]["90"]["holdout_positive_count"], 1)
        self.assertEqual(report["prospective_issued_probabilities"], 0)
        self.assertFalse(report["historical_issue_dates_independently_verified"])
        baseline = report["fit_2024_2025"]
        archives[research.archive_url(2026, 9)] = csv_bytes([
            ("a-new-2026", 1, 1, 1, "2026-05-10", "2026-05-10", 1),
        ])
        changed_sha = {**sha, 2026: hashlib.sha256(archives[research.archive_url(2026, 9)]).hexdigest()}
        changed = research.build_report(fetcher=archives.__getitem__,
                                        universe_raw=universe, q3_sha=changed_sha)
        self.assertEqual(changed["fit_2024_2025"], baseline)
        self.assertEqual(changed["retrospective_2026_metrics"]["30"]["holdout_positive_count"], 0)

    def test_missing_country_records_mean_no_registered_threshold_not_certified_peace(self):
        fake = fake_universe()
        countries = research.universe_from_bytes(fake)
        self.assertEqual(len(countries), 196)
        m, rows = research.extract_state_based(csv_bytes([
            ("x", 999, 1, 1, "2026-01-01", "2026-01-01", 200),
        ]), 2026, "origin", {x[0] for x in countries})
        self.assertEqual(rows, [])
        self.assertEqual(m["excluded_type1_high_precision_outside_196"], 1)
        self.assertNotIn("skill", research.__doc__.lower())


if __name__ == "__main__":
    unittest.main()
