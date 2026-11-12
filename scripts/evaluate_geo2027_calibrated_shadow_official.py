#!/usr/bin/env python3
"""Future official 2027 GEO shadow vs ORIGINAL paired evaluation contract.

Not a current forecast scoring task: 2027 is unobserved. The first official
complete UCDP OrganizedViolenceCY country-year label source must be independently
verified before any resulting scores could be certified.
NO missing original 196 country label can be imputed or silently omitted.
Two historical selection intercepts are frozen; no retraining is allowed.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from audit_issued_geo2027_shadow import audit as audit_issued_shadow
from build_official_countries import read_zip
from evaluate_geo2027_transition_alerts_official import (
    parse_future_csv, validate_candidate_source,
)
from prepare_geo2027_calibrated_shadow import (
    ALERT_PATH, FORECAST_PATH, MANIFEST_PATH, REPORT_PATH,
    SHADOW_ID, SHADOW_PATH, SOURCE_SHA256, sha,
)

SHADOW_MANIFEST=Path("data/forecast-2027-geo-shadow-manifest.json")
SHADOW_ISSUE_AUDIT=Path("data/forecast-2027-geo-shadow-audit.json")
SHADOW_GENERATOR=Path("scripts/prepare_geo2027_calibrated_shadow.py")
EXPECTED_SHADOW_SHA256="1d0880f6e95e77d5e203b186e45a035676c7f724ecbe6a8b323f776b9eaa9188"
EXPECTED_SHADOW_FIRST_COMMIT="ed3e764a191b24bc2a01f4d877b115db2e247a20"
COUNTRIES=196


def load_authenticated():
    original_raw=FORECAST_PATH.read_bytes()
    original_manifest=json.loads(MANIFEST_PATH.read_text(encoding="utf8"))
    source_report_raw=REPORT_PATH.read_bytes()
    alerts_raw=ALERT_PATH.read_bytes()
    shadow_raw=SHADOW_PATH.read_bytes()
    shadow_manifest=json.loads(SHADOW_MANIFEST.read_text(encoding="utf8"))
    document_audit=audit_issued_shadow(
        shadow_raw,shadow_manifest,original_raw,original_manifest,
        source_report_raw,alerts_raw,SHADOW_GENERATOR.read_bytes())
    original=json.loads(original_raw)
    shadow=json.loads(shadow_raw)
    if (sha(original_raw)!=SOURCE_SHA256
        or sha(shadow_raw)!=EXPECTED_SHADOW_SHA256
        or shadow_manifest["first_public_shadow_commit"]!=EXPECTED_SHADOW_FIRST_COMMIT
        or document_audit!=json.loads(SHADOW_ISSUE_AUDIT.read_text(encoding="utf8"))
        or shadow["2027_outcomes_resolved"]!=0):
        raise ValueError("Shadow and original first-public issues have changed")
    return original,shadow,shadow_manifest


def pair_metrics(rows, labels):
    """Exactly same denominator, without scores, outcomes or IDs in output."""
    if not rows:
        raise ValueError("Cannot score an empty original/shadow cohort")
    if any(row["country_id"] not in labels for row in rows):
        raise ValueError("Cannot score a missing original 2027 country outcome")
    n=len(rows)
    s_orig=s_shadow=s_orig_log=s_shadow_log=0.
    wins=losses=ties=0
    observed_positives=0
    for row in rows:
        cid=row["country_id"]
        y=labels[cid]
        if type(y) is not int or y not in (0,1):
            raise ValueError("Country outcomes must be complete binary labels")
        p=row["p_original"]
        q=row["p_shadow"]
        if any(type(v) not in (float,int) or not math.isfinite(v) or not 0<v<1
               for v in (p,q)):
            raise ValueError("Corrupt issued original/shadow probability")
        observed_positives+=y
        lp=(p-y)**2
        lq=(q-y)**2
        s_orig+=lp
        s_shadow+=lq
        s_orig_log+=-(y*math.log(p)+(1-y)*math.log1p(-p))
        s_shadow_log+=-(y*math.log(q)+(1-y)*math.log1p(-q))
        if lq<lp-1e-14:
            wins+=1
        elif lq>lp+1e-14:
            losses+=1
        else:
            ties+=1
    return {
        "country_years":n,
        "observed_active_2027":observed_positives,
        "original_brier":s_orig/n,
        "shadow_brier":s_shadow/n,
        "primary_delta_brier_shadow_minus_original":(s_shadow-s_orig)/n,
        "original_log_loss":s_orig_log/n,
        "shadow_log_loss":s_shadow_log/n,
        "secondary_delta_log_loss_shadow_minus_original":
            (s_shadow_log-s_orig_log)/n,
        "per_country_brier_shadow_better_count":wins,
        "per_country_brier_shadow_worse_count":losses,
        "per_country_brier_equal_count":ties,
        "conclusion":("negative delta favors SHADOW; positive favors ORIGINAL; "
                      "not a significance test and not independently certified"),
    }


def evaluate(original,shadow,labels,source_claim,source_audit):
    if (original.get("forecast_id")!="PSICO-GEO2027-STATEBASED25-V1"
        or shadow.get("forecast_id")!=SHADOW_ID
        or len(original.get("countries",[]))!=COUNTRIES
        or len(shadow.get("countries",[]))!=COUNTRIES
        or shadow.get("2027_outcomes_resolved")!=0):
        raise ValueError("Frozen original/shadow cohort identity altered")
    orig=original["countries"]
    shadow_rows=shadow["countries"]
    original_ids=[r["country_id"] for r in orig]
    shadow_ids=[r["country_id"] for r in shadow_rows]
    if (len(set(original_ids))!=COUNTRIES or original_ids!=shadow_ids):
        raise ValueError("Original and shadow country ID ordering differs")
    if any(type(y) is not int or y not in (0,1) for y in labels.values()):
        raise ValueError("Malformed target-year country label")
    joined=[]
    for a,b in zip(orig,shadow_rows):
        if (a["country"]!=b["country"] or
            a["last_observed_state_2025"]!=b["origin_state_2025"] or
            a["p_model"]!=b["original_issued_p_active_2027"]):
            raise ValueError("Original/shadow forecasts cannot be paired")
        joined.append({
            "country_id":a["country_id"],
            "origin_state":a["last_observed_state_2025"],
            "p_original":a["p_model"],
            "p_shadow":b["shadow_p_active_2027"],
        })
    fixed=set(original_ids)
    unresolved=sorted(fixed-set(labels))
    report={
        "schema":"idealab.psico.geo2027_shadow_future_paired_candidate.v1",
        "forecast_id":SHADOW_ID,
        "status":"SOURCE_CANDIDATE_NOT_INDEPENDENTLY_CERTIFIED",
        "source_claim":source_claim,
        "source_schema_audit":source_audit,
        "first_public_shadow_commit":EXPECTED_SHADOW_FIRST_COMMIT,
        "issued_shadow_sha256":EXPECTED_SHADOW_SHA256,
        "original_issued_sha256":SOURCE_SHA256,
        "expected_country_years":COUNTRIES,
        "resolved_country_years":COUNTRIES-len(unresolved),
        "unresolved_country_years":len(unresolved),
        "unresolved_country_ids":unresolved,
        "unissued_extra_country_ids_ignored":len(set(labels)-fixed),
        "primary_196_country_paired_comparison":None,
        "by_2025_known_origin_state":None,
        "primary_must_be_all_196_not_best_subgroup":True,
        "source_first_complete_release_independently_certified":False,
        "prospective_skill_independently_certified":False,
        "original_forecast_or_shadow_modified":False,
        "2027_outcomes_observed_at_first_shadow_issue":0,
        "limitations":("Candidate official source and claimed date must be independently "
            "authenticated as the FIRST complete 2027 release; forecasts are "
            "immutable, but selection of the shadow method followed inspection "
            "of prior evaluation outcomes. Shared geopolitical shocks prevent "
            "iid country-level significance claims."),
    }
    if unresolved:
        report["status"]="PARTIAL_OFFICIAL_2027_COVERAGE_NO_SCORES"
        return report
    report["primary_196_country_paired_comparison"]=pair_metrics(joined,labels)
    report["by_2025_known_origin_state"]={
        str(state):pair_metrics([r for r in joined if r["origin_state"]==state],labels)
        for state in (0,1)
    }
    if (report["by_2025_known_origin_state"]["0"]["country_years"]!=162
        or report["by_2025_known_origin_state"]["1"]["country_years"]!=34):
        raise ValueError("Issued risk groups changed")
    report["status"]="FULL_COVERAGE_CANDIDATE_STILL_UNCERTIFIED"
    return report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--official-zip",required=True)
    ap.add_argument("--official-url",required=True)
    ap.add_argument("--official-sha256",required=True)
    ap.add_argument("--claimed-release-date",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    validate_candidate_source(args.official_url,args.official_sha256,
                              args.claimed_release_date)
    raw=Path(args.official_zip).read_bytes()
    if sha(raw)!=args.official_sha256:
        raise ValueError("Future official ZIP fails declared SHA-256")
    orig,shadow,manifest=load_authenticated()
    labels,parse_report=parse_future_csv(read_zip(raw))
    result=evaluate(orig,shadow,labels,{
        "official_url_operator_claim":args.official_url,
        "official_zip_sha256_verified_against_claim":args.official_sha256,
        "claimed_publication_date":args.claimed_release_date,
        "independent_first_complete_release_provenance_certified":False,
    },parse_report)
    Path(args.output).write_text(
        json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        encoding="utf8")
    print("GEO2027_SHADOW_FUTURE_EVALUATION",
          result["status"],"resolved",result["resolved_country_years"],
          "unresolved",result["unresolved_country_years"],
          "certified",False)


if __name__=="__main__":
    main()
