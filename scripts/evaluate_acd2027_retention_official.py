#!/usr/bin/env python3
"""ACD-2027: candidate-only future OFFICIAL persistence outcome evaluation.

First complete 2027 UCDP/PRIO Armed Conflict Dataset (ACD) is EXPECTED no
earlier than the 2028 release. An operator-supplied official ZIP is NOT an
independently certified first/full release. Never silently treat missing
country coverage as a non-conflict year. Never refit any issued probability.
This does not score GEO2027/NEWCONF and does not read any 2027 outcomes today.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import re
from pathlib import Path
from urllib.parse import urlsplit

from audit_issued_acd2027_retention import (
    AUDIT_PATH, EXPECTED_FIRST_COMMIT, EXPECTED_ISSUE_SHA256,
    EXPECTED_SOURCE_SHA256, EXPECTED_GENERATOR_BLOB, git_blob_hash,
    GENERATOR, MANIFEST,
)
from prepare_acd2027_prospective_retention import ISSUE_PATH, FORECAST_ID
from probe_ucdp_prio_incidence import ALLOWED_TYPES, source_zip
from diagnose_acd2027_exact_count_evidence import sharp_frontier, compare_labels

TARGET_YEAR=2027
REQUIRED_INITIAL_VERSION="281"  # 28.1: first candidate annual edition covering 2027.
EXPECTED_FIRST_SOURCE_YEAR=2027
COUNTRY_COUNT=32
MODELS=("p_global_recent5","p_country_eb","p_lag1_group")
ISSUED_AUDIT_SCHEMA="idealab.psico.acd2027_intrastate_retention_issued_audit.v1"


def validate_future_source(url, checksum, publication_date):
    """Operator-supplied source shape, not independent verification of provenance."""
    if not all(isinstance(x,str) for x in (url,checksum,publication_date)):
        raise ValueError("Source provenance requires URL, hash and stated date")
    p=urlsplit(url)
    if (p.scheme!="https" or p.hostname!="ucdp.uu.se"
        or p.port is not None or p.username or p.password or
        p.query or p.fragment or p.netloc!="ucdp.uu.se"):
        raise ValueError("Only direct HTTPS UCDP official ACD ZIP is allowed")
    m=re.fullmatch(r"/downloads/ucdpprio/ucdp-prio-acd-(\d{3})-csv\.zip",p.path)
    if not m or m.group(1)!=REQUIRED_INITIAL_VERSION:
        raise ValueError("Only first possible annual ACD 28.1 edition is admissible")
    if not re.fullmatch(r"[0-9a-f]{64}",checksum):
        raise ValueError("Official source must have an exact SHA-256 checksum")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",publication_date):
        raise ValueError("Claimed source release date must be YYYY-MM-DD")
    try:
        day=dt.date.fromisoformat(publication_date)
    except ValueError as e:
        raise ValueError("Invalid calendar date supplied for future source") from e
    if day<dt.date(2028,1,1):
        raise ValueError("2027 complete annual ACD data cannot be released before 2028")
    return {"candidate_url_operator_claim":url,
            "candidate_sha256_operator_claim":checksum,
            "candidate_release_date_operator_claim":publication_date,
            "edition":"28.1",
            "first_complete_publication_independently_verified":False}


def authenticated_issue(issue_raw=None,manifest=None,issued_audit=None,generator=None):
    """Check original immutable issue and its first-public documentary chain."""
    raw=ISSUE_PATH.read_bytes() if issue_raw is None else issue_raw
    metadata=json.loads(MANIFEST.read_text(encoding="utf8")) if manifest is None else manifest
    audit=json.loads(AUDIT_PATH.read_text(encoding="utf8")) if issued_audit is None else issued_audit
    generator_raw=GENERATOR.read_bytes() if generator is None else generator
    if (hashlib.sha256(raw).hexdigest()!=EXPECTED_ISSUE_SHA256
        or git_blob_hash(generator_raw)!=EXPECTED_GENERATOR_BLOB
        or metadata.get("issue_forecast_sha256")!=EXPECTED_ISSUE_SHA256
        or metadata.get("first_public_git_commit")!=EXPECTED_FIRST_COMMIT
        or metadata.get("first_public_git_commit_utc")!="2026-11-12T22:24:56Z"
        or metadata.get("source_zip_sha256")!=EXPECTED_SOURCE_SHA256
        or metadata.get("status")!="ISSUED_PROSPECTIVE_ACD2027_UNRESOLVED"
        or metadata.get("2027_outcomes_resolved")!=0
        or metadata.get("primary_model")!=MODELS[0]
        or metadata.get("secondary_models")!=list(MODELS[1:])
        or metadata.get("source_data_last_year")!=2025
        or metadata.get("target_year")!=TARGET_YEAR
        or metadata.get("origin_year")!=2025
        or metadata.get("origin_risk_set_country_count")!=COUNTRY_COUNT
        or metadata.get("prospective_predictive_skill_demonstrated") is not False
        or audit.get("schema")!=ISSUED_AUDIT_SCHEMA
        or audit.get("issued_json_sha256")!=EXPECTED_ISSUE_SHA256
        or audit.get("first_public_git_commit")!=EXPECTED_FIRST_COMMIT
        or audit.get("country_risk_set_size")!=COUNTRY_COUNT
        or audit.get("2027_outcomes_resolved")!=0
        or audit.get("all_three_models_source_reproducible") is not True):
        raise ValueError("Original 2026 first-public ACD2027 issue commitment changed")
    document=json.loads(raw)
    rows=document.get("countries",[])
    ids=[x["country_id"] for x in rows]
    if (document.get("forecast_id")!=FORECAST_ID
        or document.get("target_year")!=TARGET_YEAR
        or document.get("origin_year")!=2025
        or document.get("2027_outcomes_resolved")!=0
        or document.get("actual_2027_outcomes_used") is not False
        or document.get("primary_model")!=MODELS[0]
        or len(rows)!=COUNTRY_COUNT or len(set(ids))!=COUNTRY_COUNT
        or ids!=sorted(ids)):
        raise ValueError("Original ACD2027 prediction risk set altered")
    for row in rows:
        if (row.get("conflict_present_in_origin_2025") is not True
            or any(type(row.get(m)) is not float or
                   not math.isfinite(row[m]) or not 0<row[m]<1
                   for m in MODELS)):
            raise ValueError("Original published ACD2027 probabilities invalid")
    return document


def parse_future_archive(raw):
    """Parse exact 2027 conflict-year rows; never manufacture country zeros."""
    rows,fields=source_zip(raw)
    if len(set(fields))!=len(fields):
        raise ValueError("Ambiguous duplicate official ACD column names")
    seen_target=set()
    historically_seen=set()
    target_active=set()
    max_year=0
    target_rows=0
    ambiguous_target=0
    unsupported_target=0
    for row in rows:
        if None in row or row.get(None) is not None:
            raise ValueError("Malformed official future ACD CSV columns")
        ytext=(row.get("year") or "").strip()
        if not re.fullmatch(r"\d{4}",ytext):
            raise ValueError("Malformed official ACD annual year")
        y=int(ytext)
        if not 1946<=y<=TARGET_YEAR:
            raise ValueError("ACD 28.1 is missing a valid 1946–2027 annual coverage")
        max_year=max(max_year,y)
        typ=(row.get("type_of_conflict") or "").strip()
        if y==TARGET_YEAR:
            target_rows+=1
        if typ not in ("1","2","3","4"):
            if y==TARGET_YEAR:
                unsupported_target+=1
            continue
        if typ not in ALLOWED_TYPES:
            continue
        country=(row.get("gwno_a") or "").strip()
        location=(row.get("gwno_loc") or "").strip()
        conflict=(row.get("conflict_id") or "").strip()
        if (not re.fullmatch(r"\d{1,4}",country)
            or not re.fullmatch(r"\d{1,4}",location)
            or country!=location or
            not re.fullmatch(r"\d{1,8}",conflict)
            or not 1<=int(country)<=2000):
            if y==TARGET_YEAR:
                ambiguous_target+=1
            continue
        cid=int(country)
        historically_seen.add(cid)
        if y!=TARGET_YEAR:
            continue
        key=(cid,int(conflict))
        if key in seen_target:
            raise ValueError("Duplicated 2027 intrastate conflict-year record")
        seen_target.add(key)
        target_active.add(cid)
    if max_year!=TARGET_YEAR or target_rows==0:
        raise ValueError("This archive does not contain full-year 2027 ACD records")
    return {
        "target_conflict_country_ids":target_active,
        "historically_coded_intrastate_country_ids":historically_seen,
        "official_2027_conflict_year_rows_all_types":target_rows,
        "official_2027_valid_intrastate_conflict_year_rows":len(seen_target),
        "official_2027_ambiguous_intrastate_rows":ambiguous_target,
        "official_2027_unsupported_type_rows":unsupported_target,
        "source_last_year":max_year,
        "source_2027_country_year_zero_cannot_be_proven_from_ACD_alone":True,
    }


def score_same_issued_countries(document,labels):
    """Paired mean Brier/log loss, exactly 32 IDs, no IID hypothesis test."""
    rows=document["countries"]
    ids={row["country_id"] for row in rows}
    if set(labels)!=ids or len(rows)!=COUNTRY_COUNT:
        raise ValueError("Must score EXACTLY the 32 first-issued countries")
    if any(type(v) is not int or v not in (0,1) for v in labels.values()):
        raise ValueError("Unresolved/invalid future binary ACD country-year label")
    n=len(rows)
    k=sum(labels.values())
    models={}
    for name in MODELS:
        ps=[row[name] for row in rows]
        ys=[labels[row["country_id"]] for row in rows]
        models[name]={
            "n_issued_country_risk_set":n,
            "n_recorded_intrastate_2027":k,
            "expected_at_2026_issuance":sum(ps),
            "brier":sum((p-y)**2 for p,y in zip(ps,ys))/n,
            "log_loss":-sum(y*math.log(p)+(1-y)*math.log1p(-p)
                           for p,y in zip(ps,ys))/n,
        }
    # An independent algebraic certificate computed from FIRST-ISSUED
    # probabilities alone: future scores must lie inside the exact feasible
    # Brier interval for the observed event count, with no IID assumption.
    hypothetical_recorded={cid for cid,value in labels.items() if value==1}
    for secondary in ("p_country_eb","p_lag1_group"):
        bounds=sharp_frontier(rows,secondary)[
            "k_conditioned_sharp_frontier"][k]
        empirical=models[secondary]["brier"]-models[MODELS[0]]["brier"]
        arithmetic=compare_labels(rows,secondary,hypothetical_recorded)
        if (abs(empirical-arithmetic)>1e-12 or
            empirical<bounds["sharp_min_secondary_minus_primary_brier"]-1e-12 or
            empirical>bounds["sharp_max_secondary_minus_primary_brier"]+1e-12):
            raise ValueError("Observed future ACD Brier contradicts frozen exact k frontier")
    return {
        "ex_ante_sharp_brier_count_frontier_checked":True,
        "automatic_primary_model_switch_authorized":False,
        "n_issued_country_risk_set":n,
        "n_2027_intrastate_persistence_recorded":k,
        "n_no_recorded_intrastate_2027":n-k,
        "primary_model":MODELS[0],
        "models":models,
        "secondary_country_eb_delta_brier_minus_primary":
            models[MODELS[1]]["brier"]-models[MODELS[0]]["brier"],
        "secondary_lag1_delta_brier_minus_primary":
            models[MODELS[2]]["brier"]-models[MODELS[0]]["brier"],
        "secondary_country_eb_delta_logloss_minus_primary":
            models[MODELS[1]]["log_loss"]-models[MODELS[0]]["log_loss"],
        "secondary_lag1_delta_logloss_minus_primary":
            models[MODELS[2]]["log_loss"]-models[MODELS[0]]["log_loss"],
        "independent_iid_significance_test_performed":False,
    }


def candidate_evaluation(document,parsed,source_claim,hash_verified):
    """Return NULL scores if ANY issued origin country has missing code coverage."""
    if not hash_verified:
        raise ValueError("Source ZIP byte hash must be checked before evaluation")
    ids={row["country_id"] for row in document["countries"]}
    allcoded=parsed["historically_coded_intrastate_country_ids"]
    active=parsed["target_conflict_country_ids"]
    missing=sorted(ids-allcoded)
    bad=parsed["official_2027_ambiguous_intrastate_rows"]+parsed[
        "official_2027_unsupported_type_rows"]
    base={
        "schema":"idealab.psico.acd2027_future_official_outcome_candidate.v1",
        "forecast_id":FORECAST_ID,
        "source_candidate":source_claim,
        "zip_source_hash_checked_against_claim":True,
        "issued_forecast_sha256":EXPECTED_ISSUE_SHA256,
        "issued_first_public_commit":EXPECTED_FIRST_COMMIT,
        "original_2026_prospective_32_country_probabilities_unchanged":True,
        "target_year":TARGET_YEAR,
        "expected_fixed_issued_origin_countries":COUNTRY_COUNT,
        "source_report":{
            k:v for k,v in parsed.items() if k not in (
                "target_conflict_country_ids",
                "historically_coded_intrastate_country_ids",
            )},
        "n_issued_country_codes_seen_in_historical_source":COUNTRY_COUNT-len(missing),
        "missing_issued_country_ids":missing,
        "target_label_coverage_internally_complete":not missing and not bad,
        "independently_verified_first_complete_official_release":False,
        "source_completeness_independently_proven":False,
        "2027_scores_independently_certified":False,
        "prospective_skill_demonstrated_by_this_source":False,
        "published_original_2027_issue_modified":False,
        "metric_values_candidate_only":None,
        "status":"INSUFFICIENT_SOURCE_COVERAGE_NO_SCORE",
        "limitations":(
            "This ZIP, URL, date and checksum are operator provided; UCDP "
            "authority, first-complete-edition chronology, and complete "
            "country-negative reporting are NOT independently authenticated. "
            "A missing ACD conflict row can mean no ACD type3/4 conflict but "
            "also an archive omission. Scores remain exploratory and "
            "UNCERTIFIED even if all 32 IDs have historical codes. "
            "No claim of peace, country independence, or confirmed skill."
        ),
    }
    if missing or bad:
        return base
    labels={cid:int(cid in active) for cid in ids}
    base["status"]="ALL_32_CODED_CANDIDATE_SCORES_UNCERTIFIED"
    base["metric_values_candidate_only"]=score_same_issued_countries(document,labels)
    return base


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--audit-issuance",action="store_true",
                   help="CI-only: verify original issue, NO 2027 outcomes loaded")
    p.add_argument("--candidate-zip")
    p.add_argument("--official-url")
    p.add_argument("--official-sha256")
    p.add_argument("--claimed-publication-date")
    p.add_argument("--output")
    args=p.parse_args()
    issued=authenticated_issue()
    if args.audit_issuance:
        if any((args.candidate_zip,args.official_url,args.official_sha256,
                args.claimed_publication_date,args.output)):
            raise ValueError("No future candidate accepted in issuance-only audit")
        print(json.dumps({
            "status":"ACD2027_ISSUED_FUTURE_OUTCOME_UNOBSERVED",
            "country_count":COUNTRY_COUNT,"target_year":TARGET_YEAR,
            "first_public_commit":EXPECTED_FIRST_COMMIT,
            "scores_calculated":False,
            "source_2027_provided":False,
        },sort_keys=True))
        return
    if not all((args.candidate_zip,args.official_url,args.official_sha256,
                args.claimed_publication_date,args.output)):
        raise ValueError("A candidate future ZIP requires all four provenance fields and output")
    claim=validate_future_source(
        args.official_url,args.official_sha256,args.claimed_publication_date)
    raw=Path(args.candidate_zip).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=args.official_sha256:
        raise ValueError("Official 2027 candidate ZIP does not match its SHA256")
    report=candidate_evaluation(issued,parse_future_archive(raw),claim,True)
    out=Path(args.output)
    protected={
        ISSUE_PATH.resolve(),MANIFEST.resolve(),AUDIT_PATH.resolve(),
        GENERATOR.resolve(),
        Path("data/forecast-2027-ucdp261.json").resolve(),
        Path("data/forecast-2027-geo-shadow.json").resolve(),
        Path("data/forecast-2027-newconf.json").resolve(),
        Path("data/forecast-2027-transition-alerts.json").resolve(),
    }
    if out.resolve() in protected:
        raise ValueError("Candidate scoring can NEVER overwrite a frozen public issue")
    out.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n",
                   encoding="utf8")


if __name__=="__main__":
    main()
