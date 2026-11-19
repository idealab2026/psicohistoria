#!/usr/bin/env python3
"""Synthetic-only adversarial tests: none of these rows describe real events."""
from datetime import date
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_candidate_onset_label_stability as audit
from check_ucdp_candidate_asof import SourceError


def make_csv(rows):
    names = ["id", "country_id", "type_of_violence", "date_prec", "date_start", "date_end", "best"]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=names)
    writer.writeheader()
    for row in rows:
        writer.writerow(dict(zip(names, row)))
    return stream.getvalue().encode("utf8")


def universe_bytes():
    return json.dumps({"countries": [
        {"country_id": i, "country": "Synthetic " + str(i)} for i in range(1, 197)
    ]}).encode("utf8")


class OnsetAuditTests(unittest.TestCase):
    def test_may_window_excludes_outside_and_multiday_spanning(self):
        records = [
            ("a", 1, date(2026, 5, 1), date(2026, 5, 2), 26),
            ("b", 1, date(2026, 4, 30), date(2026, 5, 2), 100),
            ("c", 1, date(2026, 5, 30), date(2026, 5, 31), 100),
        ]
        sums, retained = audit.summation(records, date(2026, 5, 1), date(2026, 5, 30))
        self.assertEqual(sums[1], 26)
        self.assertEqual(set(retained), {"a"})

    def test_label_revision_same_may_and_q1_at_risk(self):
        q1 = [("q1", 1, date(2026, 3, 2), date(2026, 3, 2), 2)]
        q2 = [("q2", 1, date(2026, 5, 12), date(2026, 5, 12), 26)]
        q3 = [("q2", 1, date(2026, 5, 12), date(2026, 5, 12), 13),
              ("other", 2, date(2026, 5, 4), date(2026, 5, 4), 25)]
        stats, prior, q3best = audit.compare_may(2026, q1, q2, q3, {1: "A", 2: "B"})
        self.assertEqual(stats["risk_set_q1_under25"], 2)
        self.assertEqual(stats["risk_label_0_to_1"], 1)
        self.assertEqual(stats["risk_label_1_to_0"], 1)
        self.assertEqual(stats["matched_may_best_changed_ids"], 1)
        self.assertEqual(stats["only_q3_may_statebased_ids"], 1)
        self.assertEqual(stats["risk_label_changed_country_ids"], [1, 2])
        self.assertEqual(prior[1], 2)
        self.assertEqual(q3best[1], 13)

    def test_topk_ties_not_confused_with_ranking_skill(self):
        rows = [
            {"country_id": 1, "target": 1, "p": .9},
            {"country_id": 2, "target": 0, "p": .9},
            {"country_id": 3, "target": 1, "p": .9},
            {"country_id": 4, "target": 0, "p": .2},
            {"country_id": 5, "target": 0, "p": .2},
        ]
        k1 = audit.tie_aware_k(rows, "p", 1)
        self.assertEqual(k1["min_hits_across_valid_tie_breaks"], 0)
        self.assertEqual(k1["max_hits_across_valid_tie_breaks"], 1)
        self.assertAlmostEqual(k1["expected_hits_random_tie_break"], 2 / 3, places=7)
        self.assertEqual(k1["cutoff_tie"]["tied_countries"], 3)
        k2 = audit.tie_aware_k(rows, "p", 2)
        self.assertEqual((k2["min_hits_across_valid_tie_breaks"],
                          k2["max_hits_across_valid_tie_breaks"]), (1, 2))
        k4 = audit.tie_aware_k(rows, "p", 4)
        self.assertEqual(k4["min_hits_across_valid_tie_breaks"], 2)
        self.assertEqual(k4["max_hits_across_valid_tie_breaks"], 2)
        with self.assertRaises(SourceError):
            audit.tie_aware_k(rows, "p", 6)

    def test_nine_sources_sha_and_frozen_2026_replay(self):
        universe = universe_bytes()
        raw_sources, baseline_sources, revisions_years, vector = {}, [], [], []
        for year in audit.YEARS:
            entries = {}
            for month in (3, 6, 9):
                source = (audit.archive_url(year, month) if month in (3, 9)
                          else audit.url_for(year, 2))
                rows = [(f"id-{year}-{month}", 1, 1, 1,
                         f"{year}-03-02" if month == 3 else f"{year}-05-04",
                         f"{year}-03-02" if month == 3 else f"{year}-05-04",
                         3 if month == 3 else 26)]
                raw_sources[source] = make_csv(rows)
                entries[month] = {
                    "url": source, "sha256": hashlib.sha256(raw_sources[source]).hexdigest()
                }
                if month in (3, 9):
                    baseline_sources.append({
                        "year": year, "month": month,
                        "source_url": source, "source_sha256": entries[month]["sha256"]
                    })
            revisions_years.append({
                "year": year, "q2": entries[6], "q3": entries[9]
            })
        for country in range(1, 197):
            vector.append({
                "country_id": country, "country": "Synthetic " + str(country),
                "prior_best_q1_2026": 3 if country == 1 else 0,
                "h30": {"target_best_q3_2026": 26 if country == 1 else 0,
                        "target": int(country == 1)},
                "h90": {"target_best_q3_2026": 26 if country == 1 else 0,
                        "target": int(country == 1),
                        "predicted_probabilities": {
                            "global": .1,
                            "persistence": .02,
                            "recent_volume": .14 if country == 1 else .005,
                        }},
            })
        baseline = {
            "status": "RETROSPECTIVE_ONLY_NOT_ISSUED",
            "universe_sha256": hashlib.sha256(universe).hexdigest(),
            "sources": baseline_sources,
            "retrospective_2026_country_vector": vector,
        }
        revisions = {
            "status": "ARCHIVED_SOURCE_REVISIONS_NOT_PREDICTIVE_VALIDATION",
            "years": revisions_years,
        }
        result = audit.build_report(fetcher=raw_sources.__getitem__, baseline=baseline,
                                    revisions=revisions, universe=universe)
        self.assertEqual(len(result["nine_official_archives"]), 9)
        self.assertEqual(result["may30_revision_by_year"][2]["q3_30day_recorded_threshold_subthreshold"], 1)
        self.assertEqual(result["holdout_2026_subthreshold_90d"]["positives"], 1)
        self.assertFalse(result["historical_vintage_first_release_dates_verified"])
        self.assertTrue(result["no_model_refit"])
        self.assertEqual(result["prospective_issued_probabilities"], 0)
        source = audit.archive_url(2026, 9)
        raw_sources[source] += b"\n"
        with self.assertRaises(SourceError):
            audit.build_report(fetcher=raw_sources.__getitem__, baseline=baseline,
                               revisions=revisions, universe=universe)
        del raw_sources[source]
        with self.assertRaises(KeyError):
            audit.build_report(fetcher=raw_sources.__getitem__, baseline=baseline,
                               revisions=revisions, universe=universe)


if __name__ == "__main__":
    unittest.main()
