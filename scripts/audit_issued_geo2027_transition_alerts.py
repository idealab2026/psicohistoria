#!/usr/bin/env python3
"""Verify exact-byte 2027 transition-alert issue and its public GitHub manifest.

Does not resolve outcomes, fetch data about 2027 or re-fit original forecast.
The manifest attests GitHub commit metadata, not an independent time notary.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

from prepare_geo2027_transition_alerts import (
    FORECAST_PATH, MANIFEST_PATH, ISSUE_ID, SCHEMA, SOURCE_SHA256,
    build, validate, sha,
)

ISSUE_FILE = Path("data/forecast-2027-transition-alerts.json")
ISSUE_MANIFEST = Path("data/forecast-2027-transition-alerts-manifest.json")


def audit(issue_raw, alert_manifest, generator_bytes, original_raw, original_manifest):
    if not isinstance(issue_raw, bytes) or not issue_raw.endswith(b"\n"):
        raise ValueError("Canonical public issue must end with newline")
    if (alert_manifest.get("schema") != "idealab.psico.prospective_transition_alert_manifest.v1"
        or alert_manifest.get("cohort_id") != ISSUE_ID
        or alert_manifest.get("status") != "ISSUED_PROSPECTIVE_UNRESOLVED"
        or alert_manifest.get("issued_alert_count") != 15
        or alert_manifest.get("outcomes_resolved") != 0
        or alert_manifest.get("original_geo2027_forecast_sha256") != SOURCE_SHA256):
        raise ValueError("Public 2027 alert issue manifest invalid")
    expected = build(original_raw, original_manifest, generator_bytes)
    validate(expected)
    canonical = (json.dumps(
        expected, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) + "\n").encode("utf8")
    if issue_raw != canonical:
        raise ValueError("Issued alert forecast bytes no longer source-reproducible")
    issue_digest = sha(issue_raw)
    if alert_manifest.get("issue_sha256") != issue_digest:
        raise ValueError("Issued alert document SHA-256 mismatches certified manifest")
    commit = alert_manifest.get("first_public_issue_commit", "")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Missing first-public GitHub issue commit SHA")
    timestamp = alert_manifest.get("first_public_issue_commit_utc", "")
    if not isinstance(timestamp, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", timestamp
    ):
        raise ValueError("First public issuance timestamp is unverified")
    instant = dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if not (dt.datetime(2026, 11, 10, tzinfo=dt.timezone.utc)
            <= instant < dt.datetime(2027, 1, 1, tzinfo=dt.timezone.utc)):
        raise ValueError("Alert issuance was not demonstrably before target year")
    if alert_manifest.get("independently_notarized") is not False:
        raise ValueError("Cannot claim independent timestamp notarization")
    groups = expected["risk_groups"]
    return {
        "schema": "idealab.psico.prospective_geo2027_transition_alert_audit.v1",
        "status": "PROSPECTIVE_ISSUED_UNRESOLVED",
        "cohort_id": ISSUE_ID,
        "issued_file_sha256": issue_digest,
        "first_public_github_commit": commit,
        "first_public_github_commit_utc": timestamp,
        "origin_2025_country_count": 196,
        "origin_inactive": groups["0"]["eligible_country_count"],
        "origin_active": groups["1"]["eligible_country_count"],
        "alerts_entry": len(groups["0"]["selected_countries"]),
        "alerts_resolution": len(groups["1"]["selected_countries"]),
        "source_original_geo2027_sha256": SOURCE_SHA256,
        "source_generator_sha256": sha(generator_bytes),
        "source_original_forecast_unchanged": True,
        "outcomes_2027_resolved": 0,
        "prospective_skill_demonstrated": False,
        "independently_notarized": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-report")
    args = parser.parse_args()
    report = audit(
        ISSUE_FILE.read_bytes(),
        json.loads(ISSUE_MANIFEST.read_text(encoding="utf8")),
        Path("scripts/prepare_geo2027_transition_alerts.py").read_bytes(),
        FORECAST_PATH.read_bytes(),
        json.loads(MANIFEST_PATH.read_text(encoding="utf8")),
    )
    text = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    print("GEO2027_ALERT_ISSUE_AUDIT_BEGIN")
    print(text, end="")
    print("GEO2027_ALERT_ISSUE_AUDIT_END")
    if args.check_report and Path(args.check_report).read_bytes() != text.encode("utf8"):
        raise ValueError("Issued prospective alert audit differs from canonical report")


if __name__ == "__main__":
    main()
