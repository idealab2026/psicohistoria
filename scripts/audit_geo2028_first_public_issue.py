#!/usr/bin/env python3
"""Audit first-public GEO2028 H=3 original via Git ancestry and source chain.

Never declare independent time notarization: git committer timestamps are
public metadata but can be controlled by the writer and are not a trusted
third-party before-event service. Git/GitHub original first commit and bytes
must remain inspectable after subsequent institutional PR merges.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess

import build_2027_prospective_registry as registry
import prepare_geo2028_three_year as preparation

ROOT=Path(__file__).resolve().parents[1]
SOURCE_PATH="data/forecast-2028-geo3.json"
MANIFEST_PATH="data/forecast-2028-geo3-manifest.json"
FIRST="5a7c949f6fe9a352ecb27c4e4193f2f3e92b64d0"
PREREG_MAIN="83c1be9a03f31c38993350b26ff0ff1e678cb0c5"
ISSUE_SHA="fd5832c6896548b053202f2f84bd0f7cd4a75df44462fbd4f259b9d8d4c39bde"
ISSUE_UTC="2026-11-15T18:27:05Z"


def check_raw(raw,manifest,original_2027,registry_2027):
    if hashlib.sha256(raw).hexdigest()!=ISSUE_SHA:
        raise ValueError("GEO2028 original first-public file SHA-256 changed")
    if raw!=registry.canonical(json.loads(raw)):
        raise ValueError("GEO2028 issued bytes are not exactly canonical")
    doc=json.loads(raw)
    preparation.validate_forecast(doc)
    expected={
        "schema":"idealab.psico.geo2028_three_year_first_public_attestation.v1",
        "status":"ISSUED_PROSPECTIVE_THREE_YEAR_UNRESOLVED",
        "forecast_file":SOURCE_PATH,
        "forecast_id":preparation.PROTOCOL_ID,
        "forecast_sha256":ISSUE_SHA,
        "first_public_forecast_commit":FIRST,
        "first_public_forecast_commit_utc":ISSUE_UTC,
        "first_public_commit_added_file":True,
        "preregistered_protocol_pr":75,
        "preregistered_protocol_main_commit":PREREG_MAIN,
        "independently_notarized":False,
        "GitHub_commit_time_is_public_metadata_not_independent_notary":True,
        "origin_source_version":"26.1",
        "origin_source_sha256":preparation.SOURCE_SHA,
        "origin_last_year":2025,
        "target_year":2028,
        "horizon_years":3,
        "n_issued_country_probabilities":196,
        "primary_model":"p_model",
        "primary_baseline":"p_baseline_global_5y",
        "comparator_markov_global":"p_global_markov_3step",
        "main_evaluation_metric":"paired country mean Brier p_model minus p_baseline_global_5y",
        "original_GEO2027_first_public_sha256":registry.EXPECTED["geo"][1],
        "original_GEO2027_issuance_unchanged":True,
        "cross_horizon_2027_2028_outcomes_statistically_independent":False,
        "actual_2028_outcomes_observed":0,
        "prospective_predictive_skill_demonstrated":False,
        "operator_declared_first_complete_2028_official_source_verified":False,
        "new_2028_TWO_year_origin_2026_forecast_included":False,
    }
    if manifest!=expected:
        raise ValueError("GEO2028 first-public source provenance manifest changed")
    if (registry_2027["n_unique_country_endpoint_rows"]!=424 or
        registry_2027["n_verified_future_2027_outcomes"]!=0 or
        registry_2027["observational_skill_demonstrated"] is not False):
        raise ValueError("Original three 2027 cohorts no longer issued-unresolved")
    rows2027=original_2027["countries"]
    if (len(rows2027)!=196 or
        len({r["country_id"] for r in rows2027})!=196 or
        doc["n_countries"]!=196):
        raise ValueError("Original first-issued GEO risk sets not 196")
    older={r["country_id"]:r for r in rows2027}
    if (len(doc["countries"])!=len(older) or
        {r["country_id"] for r in doc["countries"]}!=set(older)):
        raise ValueError("2028 group is not the exact 2027 origin GWNO cohort")
    for r in doc["countries"]:
        old=older[r["country_id"]]
        if (r["country"]!=old["country"] or
            r["last_observed_state_2025"]!=old["last_observed_state_2025"] or
            r["p_issued_geo2027_2step_for_temporal_comparison_only"]!=old["p_model"] or
            r["p_baseline_global_5y"]!=old["p_baseline_global_5y"]):
            raise ValueError("2028 issuance reclassified or rewrote original 2027 country")
    if (doc["origin"]["year"]!=2025 or doc["target"]["year"]!=2028 or
        doc["first_issue_provenance"]["original_GEO2027_SHA256"]!=
        registry.EXPECTED["geo"][1] or
        doc["protocol"]["cannot_pool_with_GEO2027_as_independent_forecasts"] is not True):
        raise ValueError("Future horizon or dependence warning compromised")
    return {
        "schema":"idealab.psico.geo2028_first_public_issue_integrity.v1",
        "status":"PROSPECTIVE_GEO2028_H3_ISSUED_UNRESOLVED_NOT_VALIDATED",
        "forecast_sha256":ISSUE_SHA,
        "first_public_commit":FIRST,
        "first_public_commit_utc":ISSUE_UTC,
        "preregistered_protocol_main_commit":PREREG_MAIN,
        "n_2028_country_issues":196,
        "n_2027_country_endpoint_issues_still_unresolved":424,
        "original_2027_horizon_2_forecasts_preserved":True,
        "2028_independently_notarized":False,
        "observed_2028_labels_used":0,
        "cross_year_country_origin_independence_demonstrated":False,
    }


def _git(*args,check=True):
    return subprocess.run(["git","-C",str(ROOT),*args],
                          capture_output=True,check=check)


def audit_git_first_commit(manifest,raw):
    # Verify commit is actually present and its ORIGINAL tree bytes match
    # all current emitted probabilities, even after later commits/merges.
    first=_git("show",FIRST+":"+SOURCE_PATH).stdout
    if first!=raw:
        raise ValueError("Original first-Git-commit forecast bytes differ")
    parent=_git("rev-parse",FIRST+"^").stdout.decode().strip()
    if _git("cat-file","-e",parent+":"+SOURCE_PATH,check=False).returncode==0:
        raise ValueError("Claimed first issue already existed in parent")
    changed=_git("diff-tree","--no-commit-id","--name-status","-r",FIRST).stdout.decode().strip()
    if changed!="A\t"+SOURCE_PATH:
        raise ValueError("First public issue commit is not a single file addition")
    if _git("merge-base","--is-ancestor",PREREG_MAIN,FIRST,check=False).returncode!=0:
        raise ValueError("2028 model preregistration not ancestral to issuance")
    if _git("merge-base","--is-ancestor",FIRST,"HEAD",check=False).returncode!=0:
        raise ValueError("First public issue commit cannot be found in HEAD ancestry")
    when=_git("show","-s","--format=%cI",FIRST).stdout.decode().strip()
    at=datetime.fromisoformat(when)
    utc=at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if (utc!=ISSUE_UTC or
        at>=datetime(2028,1,1,tzinfo=timezone.utc) or
        manifest["first_public_forecast_commit_utc"]!=utc):
        raise ValueError("Git first issuance date disagrees or is after target starts")
    author=_git("show","-s","--format=%an|%ae",FIRST).stdout.decode().strip()
    if (not author.startswith("Idea Lab|") or
        not author.endswith("+idealab2026@users.noreply.github.com")):
        raise ValueError("First public issue has non-institutional author")
    return True


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--no-git",action="store_true",
                   help="Local canonical source check only; CI must test Git provenance")
    args=p.parse_args()
    raw=(ROOT/SOURCE_PATH).read_bytes()
    manifest=json.loads((ROOT/MANIFEST_PATH).read_text(encoding="utf8"))
    docs,manifests=registry.read_issued()
    ledger=registry.make_registry(docs,manifests)
    report=check_raw(raw,manifest,docs["geo"],ledger)
    if not args.no_git:
        audit_git_first_commit(manifest,raw)
    print("GEO2028_FIRST_ISSUE_AUDIT",json.dumps(report,sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    main()
