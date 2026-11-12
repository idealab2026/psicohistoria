"""Synthetic issue-manifest tests, NO actual 2027 outcomes."""
import copy
import json
import unittest

from audit_issued_geo2027_shadow import SCHEMA, audit
from prepare_geo2027_calibrated_shadow import (
    ALERT_PATH,FORECAST_PATH,MANIFEST_PATH,REPORT_PATH,SHADOW_ID,
    canonical,construct,sha,SOURCE_SHA256,ORIGINAL_FIRST_COMMIT,
)


def fixture():
    original=FORECAST_PATH.read_bytes()
    original_m=json.loads(MANIFEST_PATH.read_text(encoding="utf8"))
    calibration=REPORT_PATH.read_bytes()
    alerts=ALERT_PATH.read_bytes()
    generator=b"fixed-test-generator"
    document=construct(original,original_m,calibration,alerts,generator)
    issue=canonical(document)
    manifest={
        "schema":SCHEMA,
        "forecast_id":SHADOW_ID,
        "status":"ISSUED_PROSPECTIVE_SHADOW_UNRESOLVED",
        "issued_country_count":196,
        "2027_outcomes_resolved":0,
        "prospective_skill_demonstrated":False,
        "original_forecast_modified":False,
        "original_15_alerts_modified":False,
        "original_forecast_sha256":SOURCE_SHA256,
        "original_forecast_first_public_commit":ORIGINAL_FIRST_COMMIT,
        "source_last_observed_year":2025,
        "shadow_forecast_sha256":sha(issue),
        "calibration_report_sha256":sha(calibration),
        "original_alerts_sha256":sha(alerts),
        "generator_sha256":sha(generator),
        "first_public_shadow_commit":"a"*40,
        "first_public_shadow_commit_utc":"2026-11-12T19:00:00Z",
        "independently_notarized":False,
    }
    return issue,manifest,original,original_m,calibration,alerts,generator


class IssuedGeo2027ShadowAuditTests(unittest.TestCase):
    def test_issuer_reproduces_all_196_public_probabilities(self):
        args=fixture()
        d=audit(*args)
        self.assertEqual(d["status"],"ISSUED_SHADOW_NO_2027_RESULTS")
        self.assertEqual(d["issued_country_count"],196)
        self.assertEqual(d["2027_outcomes_resolved"],0)
        self.assertFalse(d["demonstrated_prospective_skill"])
        self.assertTrue(d["original_forecast_and_alert_issues_unchanged"])
        self.assertFalse(d["independently_notarized"])

    def test_modified_output_or_generator_fail_closed(self):
        args=list(fixture())
        with self.assertRaisesRegex(ValueError,"source-canonical"):
            audit(args[0][:-1]+b" \n",*args[1:])
        with self.assertRaisesRegex(ValueError,"source-canonical"):
            audit(args[0],*args[1:-1],args[-1]+b"mutated")
        args=list(fixture())
        args[1]["shadow_forecast_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            audit(*args)

    def test_claimed_time_must_precede_target_year(self):
        for bad in ("2027-01-01T00:00:00Z","2026-11-11T19:00:00Z","invalid"):
            args=list(fixture())
            args[1]["first_public_shadow_commit_utc"]=bad
            with self.subTest(time=bad):
                with self.assertRaises(ValueError):
                    audit(*args)
        args=list(fixture())
        args[1]["independently_notarized"]=True
        with self.assertRaisesRegex(ValueError,"notarization"):
            audit(*args)

    def test_outcomes_or_swap_not_allowed(self):
        for field,value in (
            ("2027_outcomes_resolved",1),
            ("prospective_skill_demonstrated",True),
            ("original_forecast_modified",True),
            ("original_15_alerts_modified",True),
            ("status","VERIFIED"),
        ):
            args=list(fixture())
            args[1][field]=value
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError,"shadow issue contract"):
                    audit(*args)


if __name__=="__main__":
    unittest.main()
