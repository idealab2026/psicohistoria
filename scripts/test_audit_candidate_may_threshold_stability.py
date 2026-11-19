#!/usr/bin/env python3
"""Adversarial synthetic-only tests: no real events or actual predicted outcomes."""
import csv
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_candidate_may_threshold_stability as audit
from check_ucdp_candidate_asof import SourceError


def synthetic_csv(year, month):
    stream = io.StringIO(newline="")
    w = csv.DictWriter(stream, fieldnames=[
        "id", "country_id", "type_of_violence", "date_prec",
        "date_start", "date_end", "best"
    ])
    w.writeheader()
    if month == 3:
        w.writerow({"id": f"{year}-q1-1", "country_id": 1, "type_of_violence": 1,
                    "date_prec": 1, "date_start": f"{year}-03-05",
                    "date_end": f"{year}-03-05", "best": 3})
    else:
        w.writerow({"id": f"{year}-may-1", "country_id": 1, "type_of_violence": 1,
                    "date_prec": 1, "date_start": f"{year}-05-10",
                    "date_end": f"{year}-05-10", "best": 6 if month == 6 else 5})
        if month == 9:
            w.writerow({"id": f"{year}-may-2", "country_id": 2, "type_of_violence": 1,
                        "date_prec": 1, "date_start": f"{year}-05-10",
                        "date_end": f"{year}-05-10", "best": 8})
    return stream.getvalue().encode("utf8")


class VintageStabilityTests(unittest.TestCase):
    def test_posthoc_labels_gained_and_lost_do_not_look_like_new_events(self):
        d = lambda x: date(2026, 5, x)
        q1 = [("a", 1, date(2026, 3, 1), date(2026, 3, 1), 3)]
        q2 = [("b", 1, d(12), d(12), 5)]
        q3 = [("b", 1, d(12), d(12), 3), ("c", 2, d(12), d(12), 8)]
        result, prior, may2, may3 = audit.compare_year(
            2026, q1, q2, q3, {1:"X", 2:"Y"}
        )
        t5 = result["thresholds"]["5"]
        self.assertEqual(t5["risk_set"], 2)
        self.assertEqual(t5["q2_positives"], 1)
        self.assertEqual(t5["q3_positives"], 1)
        self.assertEqual(t5["gained_ids"], [2])
        self.assertEqual(t5["lost_ids"], [1])
        self.assertEqual(result["countries_with_best_revision_may_196"], 2)
        self.assertEqual(result["total_abs_best_revision_may_196"], 10)

    def test_requires_exact_original_sha_registry(self):
        registry = {"status": "RETROSPECTIVE_REVISIONS_NOT_ASOF_NOT_PROSPECTIVE",
                    "nine_official_archives": [
                        {"year": year, "month": month, "source_sha256": "0"*64}
                        for year in audit.YEARS for month in (3, 6, 9)
                    ]}
        pins = audit.pinned_sources(registry)
        self.assertEqual(len(pins), 9)
        registry["nine_official_archives"].append(registry["nine_official_archives"][0])
        with self.assertRaises(SourceError):
            audit.pinned_sources(registry)

    def test_full_report_sha_replay_and_2026_grid_immutable(self):
        universe = json.dumps({"countries": [
            {"country_id": i, "country": f"Synthetic {i}"} for i in range(1, 197)
        ]}).encode("utf8")
        raws = {}
        manifest = []
        for year in audit.YEARS:
            for month in (3, 6, 9):
                url = (audit.archive_url(year, month) if month != 6 else
                       audit.url_for(year, 2))
                raw = synthetic_csv(year, month)
                raws[url] = raw
                manifest.append({"year": year, "month": month,
                                 "source_sha256": hashlib.sha256(raw).hexdigest()})
        registry = {
            "status": "RETROSPECTIVE_REVISIONS_NOT_ASOF_NOT_PROSPECTIVE",
            "nine_official_archives": manifest,
        }
        vec = [{"country_id": c, "country": f"Synthetic {c}",
                "q1_state_best": 3 if c == 1 else 0,
                "q1_other_best": 0,
                "future_best_30": 5 if c == 1 else 8 if c == 2 else 0}
               for c in range(1, 197)]
        groups = {
            state + "|" + other: {"p": .05}
            for state in ("zero","1-4","5-9","10+")
            for other in ("False","True")
        }
        frozen = {
            "status": "EXPLORATORY_HISTORICAL_NOT_ASOF_NOT_ISSUED",
            "universe_sha256": hashlib.sha256(universe).hexdigest(),
            "holdout_2026_country_observations": vec,
            "trained_models": {
                str(t): {"30": {"groups": {"combined": groups}}}
                for t in audit.THRESHOLDS
            },
        }
        r = audit.build_report(fetcher=raws.__getitem__, frozen_sources=registry,
                               frozen_grid=frozen, universe_raw=universe)
        self.assertEqual(len(r["nine_original_sha_pinned_sources"]), 9)
        self.assertEqual(r["may_label_revision_by_year"][2]["thresholds"]["5"]["q2_positives"], 1)
        self.assertEqual(r["may_label_revision_by_year"][2]["thresholds"]["5"]["q3_positives"], 2)
        self.assertFalse(r["original_release_dates_independently_verified"])
        self.assertFalse(r["retraining_performed"])
        self.assertEqual(r["new_prospective_predictions"], 0)
        raws[audit.archive_url(2026, 9)] += b"\n"
        with self.assertRaises(SourceError):
            audit.build_report(fetcher=raws.__getitem__, frozen_sources=registry,
                               frozen_grid=frozen, universe_raw=universe)


if __name__ == "__main__":
    unittest.main()
