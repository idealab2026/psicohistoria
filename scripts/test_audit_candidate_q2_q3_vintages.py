#!/usr/bin/env python3
"""Synthetic controls only; these fixtures are not UCDP historical results."""
import csv
import hashlib
import io
from datetime import date
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_candidate_q2_q3_vintages as audit
from check_ucdp_candidate_asof import SourceError


def fixture(year, rows):
    cols = ["id", "country_id", "type_of_violence", "date_start", "date_end", "best"]
    f = io.StringIO(newline="")
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for item in rows:
        w.writerow(dict(zip(cols, item)))
    return f.getvalue().encode("utf8")


class VintageRevisionsTests(unittest.TestCase):
    def test_synthetic_changes_additions_and_25_threshold(self):
        y = 2025
        q2 = fixture(y, [
            ("a", 450, 1, f"{y}-06-01 00:00:00.000", f"{y}-06-01 00:00:00.000", 20),
            ("b", 451, 1, f"{y}-05-02", f"{y}-05-02", 30),
            ("c", 450, 3, f"{y}-06-01", f"{y}-06-01", 3),
            ("e", 452, 1, f"{y}-06-28", f"{y}-07-02", 500),
        ])
        q3 = fixture(y, [
            ("a", 450, 1, f"{y}-06-01 00:00:00.000", f"{y}-06-01 00:00:00.000", 26),
            ("c", 450, 1, f"{y}-06-03", f"{y}-06-03", 3),
            ("d", 453, 1, f"{y}-04-02", f"{y}-04-02", 4),
            ("e", 452, 1, f"{y}-06-28", f"{y}-07-02", 500),
        ])
        m2, a = audit.extract(q2, y)
        m3, b = audit.extract(q3, y)
        self.assertEqual(m2["eligible_rows"], 3)
        self.assertEqual(m3["eligible_rows"], 3)
        result = audit.contrast(a, b)
        self.assertEqual(result["same_id_events"], 2)
        self.assertEqual(result["only_q2_ids"], 1)
        self.assertEqual(result["only_q3_ids"], 1)
        self.assertEqual(result["matched_best_changed_ids"], 1)
        self.assertEqual(result["matched_sum_absolute_best_change"], 6)
        self.assertEqual(result["matched_type_changed_ids"], 1)
        self.assertEqual(result["matched_date_changed_ids"], 1)
        self.assertEqual(result["statebased"]["country_crosses_up_25"], 1)
        self.assertEqual(result["statebased"]["country_crosses_down_25"], 1)
        self.assertEqual(result["statebased"]["q2_fatalities_best"], 50)
        self.assertEqual(result["statebased"]["q3_fatalities_best"], 33)

    def test_cross_border_and_bad_rows(self):
        y = 2024
        for rows in (
            [("a", 450, 1, "2024-06-02", "2024-05-02", 3)],
            [("a", 450, 1, "2024-01-01", "2024-01-02", -1)],
            [("a", 450, 1, "2024-01-01", "2024-01-02", 1),
             ("a", 450, 1, "2024-01-03", "2024-01-04", 2)],
            [("a", 450, 7, "2024-01-01", "2024-01-02", 1)],
            [("a", 0, 1, "2024-01-01", "2024-01-02", 1)],
        ):
            with self.subTest(rows=rows), self.assertRaises(SourceError):
                audit.extract(fixture(y, rows), y)

    def test_window_is_fixed_in_both_vintages(self):
        y = 2024
        data = fixture(y, [
            ("a", 450, 1, "2023-12-28", "2024-01-02", 5),
            ("b", 450, 1, "2024-06-30", "2024-07-01", 100),
            ("c", 450, 1, "2024-06-30", "2024-06-30", 1),
        ])
        metadata, eligible = audit.extract(data, y)
        self.assertEqual(metadata["eligible_rows"], 1)
        self.assertEqual(set(eligible), {"c"})

    def test_original_bytes_sha_and_contract(self):
        registry = {}
        for year in audit.YEARS:
            for quarter in (2, 3):
                url = audit.url_for(year, quarter)
                registry[url] = fixture(year, [
                    (f"{year}-a", 450, 1, f"{year}-02-01", f"{year}-02-01", 25),
                ])
        digest = hashlib.sha256(registry[audit.url_for(2026, 3)]).hexdigest()
        with patch.object(audit, "Q3_2026_SHA", digest):
            report = audit.build_report(fetcher=registry.__getitem__)
        self.assertEqual(report["year_count"], 3)
        self.assertFalse(report["independent_vintage_publication_dates_verified"])
        self.assertEqual(report["outcomes_resolved"], 0)
        self.assertEqual(report["prospective_issued_probabilities"], 0)
        self.assertEqual(report["pooled_event_accounting_descriptive_only"]["only_q3_ids"], 0)

    def test_out_of_protocol_urls(self):
        for year, quarter in ((2023, 3), (2026, 4), (2027, 2)):
            with self.assertRaises(SourceError):
                audit.url_for(year, quarter)


if __name__ == "__main__":
    unittest.main()
