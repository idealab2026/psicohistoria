"""Synthetic ONLY 2027 outcomes; no actually observed 2027 results are used."""
from __future__ import annotations

import copy
import json
import unittest

from evaluate_geo2027_transition_alerts_official import (
    evaluate, holm_pair, load_authenticated, parse_future_csv,
    validate_candidate_source, FIRST_ISSUE_COMMIT, ISSUE_SHA,
)


class GeoFutureAlertEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.forecast, cls.alerts, cls.manifest = load_authenticated()
        cls.ids = sorted(row["country_id"] for row in cls.forecast["countries"])
        cls.entry_alerts = [x["country_id"] for x in
            cls.alerts["risk_groups"]["0"]["selected_countries"]]
        cls.resolution_alerts = [x["country_id"] for x in
            cls.alerts["risk_groups"]["1"]["selected_countries"]]

    def fake_outcomes(self):
        # Distinct synthetic events; never factual claims about countries.
        result = {cid: int(row["last_observed_state_2025"])
                  for row in self.forecast["countries"]
                  for cid in [row["country_id"]]}
        # Two selected synthetic entries plus two unselected entries.
        selected_entry = set(self.entry_alerts)
        selected_resolution = set(self.resolution_alerts)
        rest_entry = [r["country_id"] for r in self.forecast["countries"]
                      if r["last_observed_state_2025"] == 0 and
                      r["country_id"] not in selected_entry]
        rest_resolution = [r["country_id"] for r in self.forecast["countries"]
                           if r["last_observed_state_2025"] == 1 and
                           r["country_id"] not in selected_resolution]
        for cid in self.entry_alerts[:2] + rest_entry[:2]:
            result[cid] = 1
        for cid in self.resolution_alerts[:1] + rest_resolution[:2]:
            result[cid] = 0
        return result

    def test_manifest_and_first_public_alert_identity_are_authentic(self):
        self.assertEqual(self.manifest["first_public_issue_commit"], FIRST_ISSUE_COMMIT)
        self.assertEqual(self.manifest["issue_sha256"], ISSUE_SHA)
        self.assertEqual(self.alerts["2027_outcomes_resolved"], 0)
        self.assertEqual(len(self.entry_alerts), 10)
        self.assertEqual(len(self.resolution_alerts), 5)

    def test_parse_missing_blank_never_assumed_zero(self):
        csvtext = "country_id,year,sb_total_deaths_best\\n1,2026,999\\n1,2027,24\\n2,2027,25\\n3,2027,\\n"
        # Literal escaped newlines are decoded here to avoid accidental CSV formatting.
        labels, audit = parse_future_csv(csvtext.replace("\\n", "\n"))
        self.assertEqual(labels, {1: 0, 2: 1})
        self.assertEqual(audit["source_2027_blank_labels"], 1)
        self.assertEqual(audit["source_2027_unique_ids"], 3)
        with self.assertRaisesRegex(ValueError, "Duplicated"):
            parse_future_csv("country_id,year,sb_total_deaths_best\n1,2027,1\n1,2027,2\n")
        with self.assertRaisesRegex(ValueError, "integer"):
            parse_future_csv("country_id,year,sb_total_deaths_best\n1,2027,-1\n")
        with self.assertRaisesRegex(ValueError, "No official 2027"):
            parse_future_csv("country_id,year,sb_total_deaths_best\n1,2026,0\n")
        with self.assertRaisesRegex(ValueError, "Duplicate official"):
            parse_future_csv("country_id,country_id,year,sb_total_deaths_best\n1,1,2027,0\n")

    def test_future_date_and_exact_zip_hash_required(self):
        digest = "f" * 64
        good = "https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-281-csv.zip"
        self.assertTrue(validate_candidate_source(good, digest, "2028-06-01"))
        for bad_url in (
            "https://attacker.invalid/downloads/organizedviolencecy/organizedviolencecy-281-csv.zip",
            "https://ucdp.uu.se.evil.invalid/downloads/organizedviolencecy/organizedviolencecy-281-csv.zip",
            "https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-261-csv.zip",
            "https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-281-csv.zip?rev=1",
        ):
            with self.subTest(url=bad_url):
                with self.assertRaises(ValueError):
                    validate_candidate_source(bad_url, digest, "2028-06-01")
        with self.assertRaises(ValueError):
            validate_candidate_source(good, digest, "2027-11-01")
        with self.assertRaises(ValueError):
            validate_candidate_source(good, "0"*20, "2028-06-01")

    def test_exact_holm_pair(self):
        self.assertEqual(holm_pair({"entry": 0.01, "resolution": 0.04}),
                         {"entry": 0.02, "resolution": 0.04})
        self.assertEqual(holm_pair({"entry": 0.04, "resolution": 0.01}),
                         {"resolution": 0.02, "entry": 0.04})
        self.assertEqual(holm_pair({"entry": 0.4, "resolution": 0.4}),
                         {"entry": 0.8, "resolution": 0.8})
        for invalid in ({"entry": 0.1}, {"entry": 0.1, "resolution": float("nan")},
                        {"entry": 0.1, "resolution": 1.01}):
            with self.assertRaisesRegex(ValueError, "Exactly two"):
                holm_pair(invalid)

    def test_full_synthetic_cohort_and_two_endpoints(self):
        outcomes = self.fake_outcomes()
        report = evaluate(self.forecast, self.alerts, outcomes,
                          {"fake": "synthetic"}, {"source_2027_rows": 196})
        self.assertEqual(report["status"], "CANDIDATE_FULL_COVERAGE_STILL_UNCERTIFIED")
        self.assertEqual(report["resolved"], 196)
        self.assertEqual(report["unresolved"], 0)
        self.assertFalse(report["prospective_skill_independently_certified"])
        entry = report["endpoints"]["entry"]
        resolution = report["endpoints"]["resolution"]
        self.assertEqual((entry["target_transitions"], entry["alert_hits"]), (4, 2))
        self.assertEqual((resolution["target_transitions"], resolution["alert_hits"]), (3, 1))
        self.assertEqual((entry["eligible"], resolution["eligible"]), (162, 34))
        self.assertEqual((entry["issued_alert_budget"], resolution["issued_alert_budget"]), (10, 5))
        self.assertAlmostEqual(entry["alert_precision"], .2)
        self.assertAlmostEqual(resolution["alert_precision"], .2)
        self.assertAlmostEqual(entry["alert_recall"], .5)
        self.assertAlmostEqual(resolution["alert_recall"], 1/3)
        self.assertIn("brier", entry["models"]["p_model"])
        self.assertIn("auc_roc_midrank", resolution["models"]["p_model"])
        self.assertEqual(set(report["holm_adjusted_upper_tails"]), {"entry", "resolution"})
        self.assertEqual(report["original_issue_sha256"], ISSUE_SHA)

    def test_partial_missing_source_stops_ALL_scores(self):
        outcome = self.fake_outcomes()
        missing_id = self.entry_alerts[0]
        del outcome[missing_id]
        report = evaluate(self.forecast, self.alerts, outcome,
                          {"fake": "missing"}, {"source_2027_rows": 195})
        self.assertEqual(report["status"], "CANDIDATE_PARTIAL_COVERAGE_NO_SCORES")
        self.assertEqual((report["resolved"], report["unresolved"]), (195, 1))
        self.assertEqual(report["unresolved_country_ids"], [missing_id])
        self.assertIsNone(report["endpoints"])
        self.assertIsNone(report["holm_adjusted_upper_tails"])
        # Even if missingness happens outside the top-15, no scores are emitted.
        outcome2 = self.fake_outcomes()
        other_id = next(cid for cid in self.ids
                        if cid not in set(self.entry_alerts + self.resolution_alerts))
        del outcome2[other_id]
        result = evaluate(self.forecast, self.alerts, outcome2, {}, {})
        self.assertIsNone(result["endpoints"])
        self.assertEqual(result["unresolved"], 1)

    def test_null_event_cohort_undefined_recall_and_auc(self):
        none = {cid: row["last_observed_state_2025"]
                for row in self.forecast["countries"]
                for cid in [row["country_id"]]}
        result = evaluate(self.forecast, self.alerts, none, {}, {})
        for obj in result["endpoints"].values():
            self.assertEqual(obj["target_transitions"], 0)
            self.assertEqual(obj["alert_hits"], 0)
            self.assertIsNone(obj["alert_recall"])
            self.assertIsNone(obj["models"]["p_model"]["auc_roc_midrank"])
            self.assertEqual(obj["exact_upper_tail_given_observed_transitions"], 1.0)
        self.assertEqual(result["holm_adjusted_upper_tails"],
                         {"entry": 1.0, "resolution": 1.0})


if __name__ == "__main__":
    unittest.main()
