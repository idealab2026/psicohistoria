"""Synthetic immutability + original country invariants for future LOG1P shadow."""
from __future__ import annotations

import hashlib
import json
import unittest

from audit_geo2027_log1p_shadow_issue import (
    ORIGINAL, ID, SOURCE_SHA, SOURCE_SHA256, FIRST_PUBLIC_COMMIT, FIRST_PUBLIC_UTC, audit,
)


def fixture():
    original_raw=ORIGINAL.read_bytes()
    original=json.loads(original_raw)
    rows=sorted(original["countries"],key=lambda x:x["country_id"])
    countries=[{
        "country_id":r["country_id"],"country":r["country"],
        "origin_binary_state_2025":r["last_observed_state_2025"],
        "origin_deaths_best_2025":25 if r["last_observed_state_2025"] else 0,
        "original_2027_p_active":r["p_model"],
        "intercept_only_control_p_active_2027":r["p_model"],
        "log1p_shadow_p_active_2027":r["p_model"],
    } for r in rows]
    issue={
        "schema":"idealab.psico.geo2027_log1p_intensity_shadow.v1",
        "forecast_id":ID,
        "status":"ISSUED_PROSPECTIVE_UNRESOLVED",
        "target":{"year":2027,"final_metrics_require_all_196_resolved":True},
        "source":{"last_observed_year":2025,"sha256":SOURCE_SHA},
        "original_2027_immutable_sha256":SOURCE_SHA256,
        "countries":countries,"n_countries":196,
        "outcomes_2027_resolved":0,
        "demonstrated_prospective_skill":False,
        "original_2027_probabilities_or_15_alerts_modified":False,
        "new_transition_alert_list_issued":False,
    }
    raw=json.dumps(issue,sort_keys=True).encode()
    sha=hashlib.sha256(raw).hexdigest()
    manifest={
        "schema":"idealab.psico.geo2027_log1p_shadow_manifest.v1",
        "forecast_id":ID,"status":"ISSUED_PROSPECTIVE_UNRESOLVED",
        "target_year":2027,"issued_country_count":196,
        "outcomes_resolved":0,"demonstrated_predictive_skill":False,
        "original_forecast_sha256":SOURCE_SHA256,
        "source_26_1_sha256":SOURCE_SHA,
        "first_complete_forecast_commit":FIRST_PUBLIC_COMMIT,
        "first_complete_forecast_commit_utc":FIRST_PUBLIC_UTC,
        "shadow_file_sha256":sha,
    }
    return issue,manifest,original_raw,sha


def check(issue,manifest,original_raw,sha):
    return audit(json.dumps(issue,sort_keys=True).encode(),
                 json.dumps(manifest,sort_keys=True).encode(),
                 original_raw,frozen_sha=sha)


class FrozenShadowAuditTests(unittest.TestCase):
    def test_full_fixed_original_country_and_sha_pass(self):
        result=check(*fixture())
        self.assertEqual(result["country_n"],196)
        self.assertEqual(result["future_2027_outcomes_resolved"],0)

    def test_probability_change_is_tampering(self):
        issue,manifest,orig,sha=fixture()
        issue["countries"][0]["log1p_shadow_p_active_2027"]+=0.01
        with self.assertRaisesRegex(ValueError,"bytes changed"):
            check(issue,manifest,orig,sha)

    def test_manifest_sha_change_does_not_reissue(self):
        issue,manifest,orig,sha=fixture()
        manifest["shadow_file_sha256"]="b"*64
        with self.assertRaisesRegex(ValueError,"bytes changed"):
            check(issue,manifest,orig,sha)

    def test_missing_country_not_scored_as_inactive(self):
        issue,manifest,orig,sha=fixture()
        issue["countries"]=issue["countries"][:-1]
        raw=json.dumps(issue,sort_keys=True).encode()
        sha=hashlib.sha256(raw).hexdigest()
        manifest["shadow_file_sha256"]=sha
        with self.assertRaisesRegex(ValueError,"not complete"):
            check(issue,manifest,orig,sha)

    def test_future_resolved_claim_rejected(self):
        issue,manifest,orig,sha=fixture()
        issue["outcomes_2027_resolved"]=1
        raw=json.dumps(issue,sort_keys=True).encode()
        sha=hashlib.sha256(raw).hexdigest()
        manifest["shadow_file_sha256"]=sha
        with self.assertRaisesRegex(ValueError,"specification altered"):
            check(issue,manifest,orig,sha)

    def test_modified_original_sha_rejected(self):
        issue,manifest,orig,sha=fixture()
        with self.assertRaisesRegex(ValueError,"Original 2027"):
            check(issue,manifest,orig+b"tampered",sha)


if __name__=="__main__":
    unittest.main()
