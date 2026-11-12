#!/usr/bin/env python3
"""Audit SECOND public 2027 calibrated GEO shadow forecast issuance.

Checks exact original forecast SHA, prior historical calibration, original
alerts, generator SHA, every issued shadow byte, and public commit metadata.
Does NOT authenticate GitHub commit timestamps independently nor imply any
2027 result was observed. No forecast mutation is permitted.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

from prepare_geo2027_calibrated_shadow import (
    ALERT_PATH, FORECAST_PATH, MANIFEST_PATH, ORIGINAL_FIRST_COMMIT,
    REPORT_PATH, SHADOW_ID, SHADOW_PATH, SOURCE_SHA256, canonical, construct, sha,
)

SHADOW_MANIFEST = Path("data/forecast-2027-geo-shadow-manifest.json")
SHADOW_AUDIT = Path("data/forecast-2027-geo-shadow-audit.json")
GENERATOR = Path("scripts/prepare_geo2027_calibrated_shadow.py")
SCHEMA = "idealab.psico.geo2027_calibrated_shadow_issued_manifest.v1"


def audit(raw, manifest, original_raw, original_manifest, historical_raw,
          alerts_raw, generator_raw):
    if manifest.get("schema") != SCHEMA or manifest.get("forecast_id") != SHADOW_ID:
        raise ValueError("Wrong secondary forecast issue manifest")
    if (manifest.get("status") != "ISSUED_PROSPECTIVE_SHADOW_UNRESOLVED"
        or manifest.get("issued_country_count") != 196
        or manifest.get("2027_outcomes_resolved") != 0
        or manifest.get("prospective_skill_demonstrated") is not False
        or manifest.get("original_forecast_modified") is not False
        or manifest.get("original_15_alerts_modified") is not False
        or manifest.get("original_forecast_sha256") != SOURCE_SHA256):
        raise ValueError("Cannot certify prospective shadow issue contract")
    doc=construct(original_raw, original_manifest, historical_raw,
                  alerts_raw, generator_raw)
    expected=canonical(doc)
    if raw!=expected:
        raise ValueError("Published shadow forecast differs from source-canonical bytes")
    digest=sha(raw)
    if (manifest.get("shadow_forecast_sha256")!=digest
        or manifest.get("calibration_report_sha256")!=sha(historical_raw)
        or manifest.get("generator_sha256")!=sha(generator_raw)
        or manifest.get("original_alerts_sha256")!=sha(alerts_raw)):
        raise ValueError("Published shadow/source SHA-256 mismatch")
    commit=manifest.get("first_public_shadow_commit")
    timestamp=manifest.get("first_public_shadow_commit_utc")
    if not isinstance(commit,str) or re.fullmatch(r"[0-9a-f]{40}",commit) is None:
        raise ValueError("First public shadow issue GitHub commit SHA is required")
    if (not isinstance(timestamp,str) or
        re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ",timestamp) is None):
        raise ValueError("First public shadow timestamp is not syntactically verifiable")
    issue_time=dt.datetime.fromisoformat(timestamp.replace("Z","+00:00"))
    if not (dt.datetime(2026,11,12,tzinfo=dt.timezone.utc) <= issue_time <
            dt.datetime(2027,1,1,tzinfo=dt.timezone.utc)):
        raise ValueError("Shadow issue timestamp is outside preregistered window")
    if (manifest.get("independently_notarized") is not False
        or manifest.get("original_forecast_first_public_commit") != ORIGINAL_FIRST_COMMIT
        or manifest.get("source_last_observed_year") != 2025):
        raise ValueError("Unsupported provenance/notarization claim")
    if doc["2027_outcomes_resolved"] != 0 or doc["original_forecast_altered"]:
        raise ValueError("No resolved future outcomes may appear in secondary issue")
    return {
        "schema":"idealab.psico.geo2027_shadow_issued_audit.v1",
        "status":"ISSUED_SHADOW_NO_2027_RESULTS",
        "forecast_id":SHADOW_ID,
        "shadow_forecast_sha256":digest,
        "first_public_github_commit":commit,
        "first_public_github_commit_utc":timestamp,
        "original_forecast_sha256":SOURCE_SHA256,
        "calibration_report_sha256":sha(historical_raw),
        "original_alerts_sha256":sha(alerts_raw),
        "generator_sha256":sha(generator_raw),
        "issued_country_count":196,
        "issued_target_year":2027,
        "historical_intercepts_fit_only_through_target_year":2019,
        "historical_method_devised_after_2024_2025_outcomes_seen":True,
        "original_forecast_and_alert_issues_unchanged":True,
        "2027_outcomes_resolved":0,
        "demonstrated_prospective_skill":False,
        "independently_notarized":False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report")
    args=parser.parse_args()
    report=audit(
        SHADOW_PATH.read_bytes(),
        json.loads(SHADOW_MANIFEST.read_text(encoding="utf8")),
        FORECAST_PATH.read_bytes(),
        json.loads(MANIFEST_PATH.read_text(encoding="utf8")),
        REPORT_PATH.read_bytes(),
        ALERT_PATH.read_bytes(),
        GENERATOR.read_bytes(),
    )
    body=json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    print("GEO2027_SHADOW_ISSUE_AUDIT_BEGIN")
    print(body,end="")
    print("GEO2027_SHADOW_ISSUE_AUDIT_END")
    if args.check_report and SHADOW_AUDIT.read_bytes()!=body.encode("utf8"):
        raise ValueError("Published shadow issue audit has changed")


if __name__=="__main__":
    main()
