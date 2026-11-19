#!/usr/bin/env python3
"""Adversarial synthetic fixtures; NEVER use these as real Candidate events."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_ucdp_candidate_asof import SourceError, expected_vintage, validate

HEADER = "id,country_id,type_of_violence,date_start,date_end,best\n"
RECORDS = (
    "1001,510,1,2026-07-20,2026-07-20,3\n"
    "1002,510,1,2026-09-05,2026-09-05,10\n"
    "1003,550,2,2026-09-15,2026-09-16,2\n"
)
URL = "https://ucdp.uu.se/downloads/candidateged/GEDEvent_v26_01_26_09.csv"


class CandidateVintageGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "candidate.csv"
        self._source(HEADER + RECORDS)
        self.meta = {
            "source_url": URL,
            "source_version": "26.01.26.09",
            "coverage_start": "2026-01-01",
            "coverage_end": "2026-09-30",
            "released_on": "2026-10-10",
            "release_evidence_url": "https://ucdp.uu.se/downloads/",
            "review_status": "operator_attested",
            "source_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
        }

    def _source(self, body):
        self.source.write_text(body, encoding="utf8")

    def _run(self, meta=None, issued="2026-10-20", horizon=30):
        return validate(self.source, self.meta if meta is None else meta, issued, horizon)

    def _blocked(self, meta=None, issued="2026-10-20", horizon=30):
        with self.assertRaises(SourceError):
            self._run(meta, issued, horizon)

    def test_success_both_horizons_but_never_forecast(self):
        for h in (30, 90):
            report = self._run(horizon=h)
            self.assertEqual(report["status"], "SOURCE_ELIGIBLE_NO_FORECAST")
            self.assertEqual(report["issued_probabilities"], 0)
            self.assertEqual(report["outcomes_resolved"], 0)
            self.assertFalse(report["release_date_is_independently_verified"])
            self.assertEqual(report["target_start"], "2026-10-21")
            self.assertEqual(report["target_end"], "2026-11-19" if h == 30 else "2027-01-18")
            self.assertEqual(report["event_counts"]["state_based"], 2)

    def test_sha_mismatch_fails_closed(self):
        self._source(HEADER + RECORDS + "1004,551,1,2026-09-17,2026-09-17,1\n")
        self._blocked()

    def test_no_future_release_or_same_day_assumption(self):
        for day in ("2026-10-20", "2026-10-21", "2026-09-30"):
            meta = deepcopy(self.meta)
            meta["released_on"] = day
            self._blocked(meta)

    def test_missing_release_review_and_malicious_evidence(self):
        for value in ("unreviewed", "", None):
            meta = deepcopy(self.meta)
            meta["review_status"] = value
            self._blocked(meta)
        for value in ("https://example.com/x", "http://ucdp.uu.se/downloads/", "https://ucdp.uu.se.evil.test/x"):
            meta = deepcopy(self.meta)
            meta["release_evidence_url"] = value
            self._blocked(meta)

    def test_explicit_stale_source_rejected(self):
        self._blocked(issued="2026-11-19")

    def test_cannot_make_single_month_claim_ninety_day_history(self):
        meta = deepcopy(self.meta)
        meta["source_url"] = "https://ucdp.uu.se/downloads/candidateged/GEDEvent_v26_0_9.csv"
        meta["source_version"] = "26.0.9"
        meta["coverage_start"] = "2026-09-01"
        self._blocked(meta)

    def test_reject_filename_traversal_mismatched_version_and_false_coverage(self):
        for url in ("https://evil.test/downloads/candidateged/GEDEvent_v26_01_26_09.csv",
                    "https://ucdp.uu.se/downloads/candidateged/../../private.csv",
                    "https://ucdp.uu.se/downloads/candidateged/GEDEvent_v26_01_25_09.csv",
                    "https://ucdp.uu.se/downloads/candidateged/GEDEvent_v26_01_26_09.csv?token=1"):
            meta = deepcopy(self.meta)
            meta["source_url"] = url
            self._blocked(meta)
        meta = deepcopy(self.meta)
        meta["coverage_start"] = "2026-02-01"
        self._blocked(meta)

    def test_unknown_horizon_and_date_rejected(self):
        self._blocked(horizon=60)
        self._blocked(issued="2026-10-xx")
        self._blocked(issued="2026-09-28")

    def test_spanning_cutoff_event_quarantined_not_attributed_to_september(self):
        self._source(HEADER + RECORDS +
                     "1005,550,1,2026-09-28 00:00:00.000,2026-10-04 00:00:00.000,99\n")
        meta = deepcopy(self.meta)
        meta["source_sha256"] = hashlib.sha256(self.source.read_bytes()).hexdigest()
        report = self._run(meta)
        self.assertEqual(report["event_counts"]["total"], 4)
        self.assertEqual(report["event_counts"]["retained"], 3)
        self.assertEqual(report["event_counts"]["state_based"], 2)
        self.assertEqual(report["event_counts"]["post_cutoff_quarantined"], 1)

    def test_invalid_date_order_and_release_after_event_requirement(self):
        for row in ("1005,550,1,2026-09-30,2026-09-01,1\n",
                    "1005,550,1,2026-10-01,2026-10-10,1\n"):
            self._source(HEADER + RECORDS + row)
            meta = deepcopy(self.meta)
            meta["source_sha256"] = hashlib.sha256(self.source.read_bytes()).hexdigest()
            self._blocked(meta)

    def test_real_ged_datetime_syntax_is_parsed_without_future_date(self):
        self._source(HEADER + "1008,510,1,2026-09-10 00:00:00.000,2026-09-10 00:00:00.000,3\n")
        meta = deepcopy(self.meta)
        meta["source_sha256"] = hashlib.sha256(self.source.read_bytes()).hexdigest()
        report = self._run(meta)
        self.assertEqual(report["event_counts"]["state_based"], 1)

    def test_duplicate_ged_event_and_invalid_casualties(self):
        for row in ("1001,550,1,2026-09-01,2026-09-01,1\n",
                    "1005,550,1,2026-09-01,2026-09-01,-2\n",
                    "1005,550,4,2026-09-01,2026-09-01,1\n"):
            self._source(HEADER + RECORDS + row)
            meta = deepcopy(self.meta)
            meta["source_sha256"] = hashlib.sha256(self.source.read_bytes()).hexdigest()
            self._blocked(meta)

    def test_missing_columns_and_empty_file_fails(self):
        self._source("id,country_id,best\n")
        meta = deepcopy(self.meta)
        meta["source_sha256"] = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self._blocked(meta)

    def test_monthly_source_inferred_calendar_and_q1_inclusive_90(self):
        m = expected_vintage("https://ucdp.uu.se/downloads/candidateged/GEDEvent_v25_0_12.csv")
        self.assertEqual(m["coverage_start"].isoformat(), "2025-12-01")
        self.assertEqual(m["coverage_end"].isoformat(), "2025-12-31")
        q = expected_vintage("https://ucdp.uu.se/downloads/candidateged/GEDEvent_v25_01_25_03.csv")
        self.assertEqual((q["coverage_end"] - q["coverage_start"]).days + 1, 90)


if __name__ == "__main__":
    unittest.main()
