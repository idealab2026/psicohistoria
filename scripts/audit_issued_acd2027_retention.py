#!/usr/bin/env python3
"""Fail-closed attestation for first public 2027 intrastate ACD issue.

GitHub commit time is verified externally when assembling the first issue
manifest; code only checks its syntax, frozen identity and input provenance.
Exact future 2027 outcome labels do NOT exist in this issuance.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

from prepare_acd2027_prospective_retention import (
    FORECAST_ID, PRIMARY, COMPARATORS, ORIGIN, TARGET,
    SOURCE_URL, ACD_SOURCE_SHA256, ISSUE_PATH, canonical,
    official_source, forecast,
)
from inspect_ucdp_archives import fetch
from probe_ucdp_prio_incidence import MAX_ZIP

MANIFEST=Path("data/forecast-2027-acd-retention-manifest.json")
AUDIT_PATH=Path("data/forecast-2027-acd-retention-audit.json")
GENERATOR=Path("scripts/prepare_acd2027_prospective_retention.py")
EXPECTED_FIRST_COMMIT="41db7bd154e0140ced15abd8727a7d52d998852c"
EXPECTED_ISSUE_SHA256="6cf7d0340a4c25062af7a040586fb6a73a98c9e6ab80473527171c0a5a963d9c"
EXPECTED_SOURCE_SHA256="5f951743222964674a446e32a5a871077b29bd13349588d85fc59953d89c878a"
EXPECTED_GENERATOR_BLOB="4feffa1d138b41231dc52db4e418c8e9018eb64a"
SCHEMA="idealab.psico.acd2027_intrastate_retention_first_issue_manifest.v1"


def git_blob_hash(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def audit(issue_raw,manifest,generator_raw,source_raw):
    if (not isinstance(manifest,dict) or manifest.get("schema")!=SCHEMA
        or manifest.get("forecast_id")!=FORECAST_ID
        or manifest.get("status")!="ISSUED_PROSPECTIVE_ACD2027_UNRESOLVED"
        or manifest.get("file")!=str(ISSUE_PATH)
        or manifest.get("source_zip_sha256")!=EXPECTED_SOURCE_SHA256
        or manifest.get("issue_forecast_sha256")!=EXPECTED_ISSUE_SHA256
        or manifest.get("first_public_git_commit")!=EXPECTED_FIRST_COMMIT
        or manifest.get("generator_git_blob_sha")!=EXPECTED_GENERATOR_BLOB
        or manifest.get("source_release")!="26.1"
        or manifest.get("source_url")!=SOURCE_URL
        or manifest.get("origin_year")!=ORIGIN
        or manifest.get("target_year")!=TARGET
        or manifest.get("source_data_last_year")!=2025
        or manifest.get("origin_risk_set_country_count")!=32
        or manifest.get("primary_model")!=PRIMARY
        or manifest.get("secondary_models")!=list(COMPARATORS)
        or manifest.get("2027_outcomes_resolved")!=0
        or manifest.get("prospective_predictive_skill_demonstrated") is not False
        or manifest.get("full_196_country_forecast") is not False
        or manifest.get("no_2026_labels_used") is not True
        or manifest.get("trained_on_2027_labels") is not False
        or manifest.get("original_geo2027_and_alerts_modified") is not False
        or manifest.get("newconf2027_modified") is not False
        or manifest.get("first_issue_timestamp_independently_notarized") is not False):
        raise ValueError("First-public ACD prospective issuance manifest altered")
    stamp=manifest.get("first_public_git_commit_utc")
    if not isinstance(stamp,str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",stamp
    ):
        raise ValueError("First-public GitHub timestamp invalid")
    parsed=dt.datetime.fromisoformat(stamp.replace("Z","+00:00"))
    if not (dt.datetime(2026,11,12,tzinfo=dt.timezone.utc)<=parsed<
            dt.datetime(2027,1,1,tzinfo=dt.timezone.utc)):
        raise ValueError("Prospective 2027 first-issue timestamp outside valid window")
    if hashlib.sha256(issue_raw).hexdigest()!=EXPECTED_ISSUE_SHA256:
        raise ValueError("Original first-public ACD2027 country forecast SHA-256 altered")
    if git_blob_hash(generator_raw)!=EXPECTED_GENERATOR_BLOB:
        raise ValueError("Source generator modified since first public issue")
    if (hashlib.sha256(source_raw).hexdigest()!=EXPECTED_SOURCE_SHA256
        or ACD_SOURCE_SHA256!=EXPECTED_SOURCE_SHA256):
        raise ValueError("UCDP official v26.1 source hash no longer pinned")
    active,meta=official_source(source_raw)
    expected=canonical(forecast(active,meta))
    if expected!=issue_raw:
        raise ValueError("Public forecast is not original-source reproducible")
    doc=json.loads(issue_raw)
    rows=doc["countries"]
    ids=[x["country_id"] for x in rows]
    if (doc["forecast_id"]!=FORECAST_ID or doc["origin_year"]!=ORIGIN
        or doc["target_year"]!=TARGET or len(rows)!=32
        or len(set(ids))!=32 or ids!=sorted(ids)
        or doc["2027_outcomes_resolved"]!=0
        or doc["actual_2027_outcomes_used"] is not False
        or doc["prospective_skill_demonstrated"] is not False
        or doc["primary_model"]!=PRIMARY
        or doc["secondary_models"]!=list(COMPARATORS)):
        raise ValueError("Forecast cohort identity/target or scientific caveat modified")
    if manifest.get("original_geo2027_issued_sha256")!=(
        "5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5"
    ) or manifest.get("original_geo2027_shadow_sha256")!=(
        "1d0880f6e95e77d5e203b186e45a035676c7f724ecbe6a8b323f776b9eaa9188"
    ):
        raise ValueError("GEO2027 original/shadow reference altered")
    return {
        "schema":"idealab.psico.acd2027_intrastate_retention_issued_audit.v1",
        "status":"ISSUED_ACD2027_FUTURE_LABELS_UNOBSERVED",
        "forecast_id":FORECAST_ID,
        "source_zip_sha256":EXPECTED_SOURCE_SHA256,
        "source_last_year":2025,
        "issued_json_sha256":EXPECTED_ISSUE_SHA256,
        "first_public_git_commit":EXPECTED_FIRST_COMMIT,
        "first_public_git_commit_utc":stamp,
        "generator_git_blob_sha":EXPECTED_GENERATOR_BLOB,
        "country_risk_set_size":32,
        "primary_model":PRIMARY,
        "primary_expected_persistent_2027":doc["model_expected_2027_persistence"][PRIMARY],
        "all_three_models_source_reproducible":True,
        "original_geo2027_and_shadow_unchanged":True,
        "2027_outcomes_resolved":0,
        "first_public_timestamp_independently_notarized":False,
        "prospective_skill_demonstrated":False,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    args=ap.parse_args()
    data=audit(ISSUE_PATH.read_bytes(),
               json.loads(MANIFEST.read_text(encoding="utf8")),
               GENERATOR.read_bytes(),fetch(SOURCE_URL,MAX_ZIP))
    rendered=json.dumps(data,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    print("ACD2027_RETENTION_FIRST_PUBLIC_AUDIT_BEGIN")
    print(rendered,end="")
    print("ACD2027_RETENTION_FIRST_PUBLIC_AUDIT_END")
    if args.check_report and AUDIT_PATH.read_bytes()!=rendered.encode():
        raise ValueError("Issued ACD2027 source attestation report differs byte-for-byte")


if __name__=="__main__":
    main()
