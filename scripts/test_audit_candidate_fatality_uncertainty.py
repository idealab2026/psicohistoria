#!/usr/bin/env python3
"""Synthetic adversarial controls: none of these observations are real UCDP."""
import csv
import hashlib
import io
import json
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_candidate_fatality_uncertainty as audit
from check_ucdp_candidate_asof import SourceError


COLS = ("id", "country_id", "type_of_violence", "date_prec", "date_start",
        "date_end", "low", "best", "high", "code_status")


def fixture(rows):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=COLS)
    writer.writeheader()
    for row in rows:
        writer.writerow(dict(zip(COLS, row)))
    return output.getvalue().encode("utf8")


def row(identifier, country, date, low, best, high, code_status="Clear",
        date_prec=1, type_of_violence=1, end=None):
    return (identifier, country, type_of_violence, date_prec,
            date, date if end is None else end, low, best, high, code_status)


def fake_universe():
    # 196 countries, including the frozen country IDs for Kenya and Libya.
    countries = [501, 620] + list(range(1000, 1194))
    return json.dumps({"countries": [
        {"country_id": x, "country": f"Synthetic {x}"} for x in countries
    ]}).encode("utf8")


class FatalityUncertaintyTests(unittest.TestCase):
    def test_low_best_high_and_clear_only_never_promoted(self):
        f = fixture([
            row("a", 501, "2026-05-10", 4, 6, 8, " Clear "),
            row("b", 620, "2026-05-12", 2, 5, 7, "Check deaths"),
            row("c", 501, "2026-05-16", 0, 99, 100, "Clear", date_prec=0),
            row("d", 501, "2026-04-30", 5, 5, 5, "Clear", end="2026-05-02"),
            row("e", 501, "2026-05-20", 1, 1, 1, "Clear", type_of_violence=3),
        ])
        stats, data = audit.audit_csv(f, 2026, 6, {501, 620})
        self.assertEqual(stats["checks"]["skip_date_prec_zero"], 1)
        self.assertEqual(data["may30"][501]["best"], 6)
        self.assertEqual(data["may30"][501]["low"], 4)
        self.assertEqual(data["may30"][501]["clear_best"], 6)
        self.assertEqual(data["may30"][620]["clear_best"], 0)
        self.assertEqual(data["may30"][620]["code_status_counts"], {"check deaths": 1})
        agg = audit.aggregate_window(data, "may30", [501, 620])
        self.assertEqual(agg["positive_counts"], {
            "low": 0, "best": 2, "high": 2, "clear_best": 1
        })
        self.assertEqual(agg["best_not_low_ids"], [501, 620])
        self.assertEqual(agg["best_not_clear_ids"], [620])

    def test_original_fatality_order_and_duplicate_ids_fail_closed(self):
        bad = [
            [row("x", 501, "2026-05-10", 8, 5, 9)],
            [row("x", 501, "2026-05-10", 1, 12, 10)],
            [row("x", 501, "2026-05-10", -1, 0, 1)],
            [row("x", 501, "2026-05-10", 1, 2, 3)] * 2,
            [row("x", 501, "2026-05-11", 1, 2, 3, end="2026-05-10")],
        ]
        for rows in bad:
            with self.subTest(rows=rows), self.assertRaises(SourceError):
                audit.audit_csv(fixture(rows), 2026, 6, {501})

    def test_90_day_window_only_exposed_from_q3(self):
        f = fixture([
            row("a", 501, "2026-05-30", 3, 6, 8),
            row("b", 501, "2026-07-29", 1, 2, 3),
            row("c", 501, "2026-07-30", 1, 50, 60),
        ])
        _, q2 = audit.audit_csv(f, 2026, 6, {501})
        _, q3 = audit.audit_csv(f, 2026, 9, {501})
        self.assertEqual(q2["may30"][501]["best"], 6)
        self.assertNotIn("may90", q2)
        self.assertEqual(q3["may90"][501]["best"], 8)

    def test_all_nine_original_sources_and_model_never_retrained(self):
        universe = fake_universe()
        raws, provenance, saved_years = {}, [], []
        countries = [501, 620] + list(range(1000, 1194))
        for year in audit.YEARS:
            for month in audit.MONTHS:
                url = audit.archive_url(year, month) if month != 6 else audit.url_for(year, 2)
                source_rows = (
                    [row(f"{year}-q1", 501, f"{year}-03-02", 2, 3, 4)]
                    if month == 3 else
                    [row(f"{year}-q2", 501, f"{year}-05-04", 4, 6, 8),
                     row(f"{year}-q2-l", 620, f"{year}-05-04", 2, 5, 7, "Check deaths")]
                )
                data = fixture(source_rows)
                raws[url] = data
                provenance.append({"year": year, "month": month,
                                   "source_url": url, "source_rows": len(source_rows),
                                   "source_sha256": hashlib.sha256(data).hexdigest()})
            saved_years.append({
                "year": year, "thresholds": {"5": {
                    "risk_set": 196,
                    "q2_positive_country_ids": [501, 620],
                    "q3_positive_country_ids": [501, 620],
                }}
            })
        registry = {
            "status": "POST_SELECTION_SOURCE_REVISION_SENSITIVITY_NOT_PROSPECTIVE",
            "nine_original_sha_pinned_sources": provenance,
            "may_label_revision_by_year": saved_years,
        }
        vector = [
            {"country_id": country, "country": f"Synthetic {country}",
             "q1_state_best": 3 if country == 501 else 0,
             "q1_other_best": 0,
             "future_best_30": 6 if country == 501 else 5 if country == 620 else 0,
             "future_best_90": 6 if country == 501 else 5 if country == 620 else 0}
            for country in countries
        ]
        bins = {
            state + "|" + other: {"p": 0.2}
            for state in ("zero", "1-4", "5-9", "10+")
            for other in ("False", "True")
        }
        grid = {
            "status": "EXPLORATORY_HISTORICAL_NOT_ASOF_NOT_ISSUED",
            "universe_sha256": hashlib.sha256(universe).hexdigest(),
            "holdout_2026_country_observations": vector,
            "trained_models": {"5": {"30": {"groups": {"combined": bins}}}},
        }
        result = audit.build_report(fetcher=raws.__getitem__, registry=registry,
                                    grid=grid, universe_raw=universe)
        self.assertEqual(len(result["original_source_provenance"]), 9)
        self.assertEqual(result["holdout_2026"]["may90_q3"]["positive_counts"]["best"], 2)
        self.assertEqual(result["may30_vintage_sensitivity"][2]["may30_from_q3"]["positive_counts"]["low"], 0)
        self.assertEqual(result["may30_vintage_sensitivity"][2]["may30_from_q3"]["positive_counts"]["clear_best"], 1)
        self.assertFalse(result["forecast_issued"])
        self.assertFalse(result["historical_model_refit"])
        changed = audit.archive_url(2026, 9)
        raws[changed] += b"\n"
        with self.assertRaises(SourceError):
            audit.build_report(fetcher=raws.__getitem__, registry=registry,
                               grid=grid, universe_raw=universe)


if __name__ == "__main__":
    unittest.main()
