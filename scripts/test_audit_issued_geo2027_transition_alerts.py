"""Synthetic manifest tests; no 2027 observations enter the issued cohort."""
import copy
import json
import unittest

from audit_issued_geo2027_transition_alerts import audit
from prepare_geo2027_transition_alerts import (
    FORECAST_PATH, MANIFEST_PATH, ISSUE_ID, SOURCE_SHA256, build, sha,
)


def dummy_manifest(raw):
    return {
        "schema": "idealab.psico.prospective_transition_alert_manifest.v1",
        "cohort_id": ISSUE_ID,
        "status": "ISSUED_PROSPECTIVE_UNRESOLVED",
        "issued_alert_count": 15,
        "outcomes_resolved": 0,
        "original_geo2027_forecast_sha256": SOURCE_SHA256,
        "issue_sha256": sha(raw),
        "first_public_issue_commit": "a" * 40,
        "first_public_issue_commit_utc": "2026-11-11T18:00:00Z",
        "independently_notarized": False,
    }


def fixture():
    original = FORECAST_PATH.read_bytes()
    prior_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf8"))
    script_bytes = b"test generator bytes"
    doc = build(original, prior_manifest, script_bytes)
    content = (json.dumps(doc, ensure_ascii=False,
             sort_keys=True, separators=(",", ":")) + "\n").encode()
    return content, dummy_manifest(content), script_bytes, original, prior_manifest


class ProspectiveAlertAuditTests(unittest.TestCase):
    def test_strict_source_replay(self):
        raw, manifest, generator, original, prior = fixture()
        report = audit(raw, manifest, generator, original, prior)
        self.assertEqual(report["alerts_entry"], 10)
        self.assertEqual(report["alerts_resolution"], 5)
        self.assertEqual(report["origin_inactive"], 162)
        self.assertEqual(report["origin_active"], 34)
        self.assertEqual(report["outcomes_2027_resolved"], 0)
        self.assertFalse(report["prospective_skill_demonstrated"])

    def test_fails_on_altered_issue_bytes_or_generator(self):
        raw, manifest, generator, original, prior = fixture()
        with self.assertRaisesRegex(ValueError, "source-reproducible"):
            audit(raw[:-1] + b" \n", manifest, generator, original, prior)
        with self.assertRaisesRegex(ValueError, "source-reproducible"):
            audit(raw, manifest, generator + b"edited", original, prior)
        wrong = copy.deepcopy(manifest)
        wrong["issue_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            audit(raw, wrong, generator, original, prior)

    def test_fails_on_future_or_unverified_timestamp(self):
        raw, manifest, generator, original, prior = fixture()
        for timestamp in ("2027-01-01T00:00:00Z", "2026-10-01T00:00:00Z",
                          "not-real"):
            wrong = copy.deepcopy(manifest)
            wrong["first_public_issue_commit_utc"] = timestamp
            with self.assertRaises(ValueError):
                audit(raw, wrong, generator, original, prior)
        wrong = copy.deepcopy(manifest)
        wrong["independently_notarized"] = True
        with self.assertRaisesRegex(ValueError, "notarization"):
            audit(raw, wrong, generator, original, prior)

    def test_fails_if_any_outcome_claimed_or_risk_set_missing(self):
        raw, manifest, generator, original, prior = fixture()
        wrong = copy.deepcopy(manifest)
        wrong["outcomes_resolved"] = 1
        with self.assertRaisesRegex(ValueError, "manifest invalid"):
            audit(raw, wrong, generator, original, prior)
        wrong = copy.deepcopy(manifest)
        wrong["issued_alert_count"] = 16
        with self.assertRaisesRegex(ValueError, "manifest invalid"):
            audit(raw, wrong, generator, original, prior)


if __name__ == "__main__":
    unittest.main()
