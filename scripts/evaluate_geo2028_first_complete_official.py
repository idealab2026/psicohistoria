#!/usr/bin/env python3
"""GEO2028 H=3: future UCDP first-complete-source scoring CANDIDATE contract.

Before 2029: NO eligible 2028 annual UCDP source, no outcomes and no scores.
After 2028: operator can supply UCDP source ZIP bytes, SHA, date and exact
official URL; those SELF-REPORTED fields cannot certify "first complete"
publication. Never silently turn missing labels into negative outcomes.

The ORIGINAL 196-probability issue stays SHA-frozen and is authenticated
against the separately preregistered 2027 issue. Scores only for exact 196
resolved GWNO countries. No IID bootstrap, p value, model promotion, pooled
GEO2027+GEO2028 tests or independent skill claim.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
import hashlib
import io
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

import audit_geo2028_first_public_issue as first_issue
import build_2027_prospective_registry as registry
from build_official_countries import read_zip

ROOT=Path(__file__).resolve().parents[1]
YEAR=2028
ORIGIN_YEAR=2025
HORIZON=3
COHORT=196
FIRST_ELIGIBLE_DATE=date(2029,1,1)
VALID_URL=re.compile(
    r"/downloads/organizedviolencecy/organizedviolencecy-(\d{3})-csv\.zip"
)
MODEL_NAMES=("p_model","p_baseline_global_5y","p_global_markov_3step")
EPS=1e-10


def sha256(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def load_immutable_issue(
    forecast_path=ROOT/first_issue.SOURCE_PATH,
    manifest_path=ROOT/first_issue.MANIFEST_PATH,
):
    """First-emission SHA, exact cohort and original 2027 comparators."""
    raw=Path(forecast_path).read_bytes()
    manifest=json.loads(Path(manifest_path).read_text(encoding="utf8"))
    docs,manifests=registry.read_issued()
    ledger=registry.make_registry(docs,manifests)
    first_issue.check_raw(raw,manifest,docs["geo"],ledger)
    return json.loads(raw),manifest


def validate_candidate_source(url:str,source_sha:str,release_date:str,*,as_of=None):
    """Reject nonofficial endpoints, wrong vintage, pretarget/future issue dates.

    Source fields remain OPERATOR-SUPPLIED and NEVER constitute independently
    verified proof of first complete annual dataset publication.
    """
    if any(type(x) is not str for x in (url,source_sha,release_date)):
        raise ValueError("Missing literal source provenance strings")
    parts=urlsplit(url)
    m=VALID_URL.fullmatch(parts.path)
    if (parts.scheme!="https" or parts.netloc!="ucdp.uu.se" or
        parts.username is not None or parts.password is not None or
        parts.query or parts.fragment or not m or
        int(m.group(1))<291):
        raise ValueError("Only post-2028 official UCDP OrganizedViolenceCY ZIP URL admitted")
    if not re.fullmatch(r"[0-9a-f]{64}",source_sha):
        raise ValueError("SHA-256 of the complete future source ZIP required")
    try:
        released=date.fromisoformat(release_date)
    except (ValueError,TypeError):
        raise ValueError("Future UCDP release date must be ISO yyyy-mm-dd") from None
    current=as_of or date.today()
    if type(current) is not date:
        raise ValueError("Invalid verification clock")
    if released<FIRST_ELIGIBLE_DATE or released>current:
        raise ValueError("2028 outcomes cannot have an official released date before 2029 or in the future")
    return {
        "official_url_operator_supplied":url,
        "source_zip_sha256_operator_supplied":source_sha,
        "release_date_operator_supplied":released.isoformat(),
        "claimed_release_version_from_filename":m.group(1),
        "first_complete_release_independently_certified":False,
        "url_hash_date_are_not_independent_source_attestation":True,
    }


def _whole(text,field):
    if type(text) is not str or not re.fullmatch(r"[0-9]+",text.strip()):
        raise ValueError("Invalid official "+field+" numeric field (no imputation)")
    return int(text.strip())


def parse_target_2028_csv(raw_csv):
    """Parse explicit 2028 rows only; retain incomplete countries unresolved."""
    text=(raw_csv.decode("utf-8-sig") if isinstance(raw_csv,bytes) else raw_csv)
    if type(text) is not str or len(text)>100000000:
        raise ValueError("Official CSV invalid or unexpectedly large")
    reader=csv.DictReader(io.StringIO(text))
    header=reader.fieldnames or []
    if len(set(header))!=len(header):
        raise ValueError("Duplicate official CSV header names")
    def choose(name,alt):
        found=[k for k in (name,alt) if k in header]
        if len(found)!=1:
            raise ValueError("Missing or ambiguous official "+name+" field")
        return found[0]
    key=choose("country_id","country_id_cy")
    year_col=choose("year","year_cy")
    best=choose("sb_total_deaths_best","sb_total_deaths_best_cy")
    result={}
    for row in reader:
        if None in row:
            raise ValueError("Malformed future official CSV row")
        yr=_whole(row[year_col],"year")
        if yr!=YEAR:
            continue
        cid=_whole(row[key],"country_id")
        deaths=_whole(row[best],"sb_total_deaths_best")
        if not (1<=cid<=2000 and 0<=deaths<=10000000):
            raise ValueError("2028 official country or deaths out of range")
        if cid in result:
            raise ValueError("Duplicate 2028 official country-year")
        result[cid]=int(deaths>=25)
    if not result:
        raise ValueError("Future official CSV has no year-2028 country observations")
    return result


def _scores(rows:list[dict],column:str)->dict:
    if not rows or column not in MODEL_NAMES:
        raise ValueError("Invalid scored cohort or model")
    brier=0.;logloss=0.
    for r in rows:
        p=r[column];y=r["observed_2028"]
        if type(p) not in (float,int) or not math.isfinite(p) or not 0<p<1:
            raise ValueError("Original probability invalid")
        if type(y) is not int or y not in (0,1):
            raise ValueError("Future label is not explicitly certified binary")
        brier+=(p-y)**2
        logloss-=(y*math.log(p)+(1-y)*math.log1p(-p))
    return {"brier":brier/len(rows),"log_loss":logloss/len(rows)}


def _calibration(rows:list[dict])->dict:
    by_origin={}
    for s in (0,1):
        part=[r for r in rows if r["last_observed_state_2025"]==s]
        by_origin[str(s)]={
            "n":len(part),
            "sum_forecast_probabilities":sum(r["p_model"] for r in part),
            "mean_forecast_probability":(
                sum(r["p_model"] for r in part)/len(part) if part else None),
            "observed_2028_events":sum(r["observed_2028"] for r in part),
            "observed_event_rate":(
                sum(r["observed_2028"] for r in part)/len(part) if part else None),
        }
    bins=[]
    for i in range(5):
        group=[r for r in rows if min(4,int(r["p_model"]*5))==i]
        bins.append({
            "probability_bin":[i/5,(i+1)/5],
            "n":len(group),
            "mean_model_probability":(
                sum(r["p_model"] for r in group)/len(group) if group else None),
            "observed_2028_event_rate":(
                sum(r["observed_2028"] for r in group)/len(group) if group else None),
        })
    if sum(v["n"] for v in by_origin.values())!=COHORT or sum(
        v["n"] for v in bins)!=COHORT:
        raise ValueError("Calibration denominator disagrees with original issue")
    return {"by_origin_2025_state":by_origin,"five_fixed_probability_bins":bins}


def score_eligible_candidate(forecast:dict,outcomes:dict,provenance:dict)->dict:
    """Self-reported first-complete candidate. NEVER certify own source.

    Pure scoring is synthetic-testable before 2029; released CLI additionally
    rejects source dates pre-2029/future and ZIP hash mismatch.
    """
    if (forecast.get("forecast_id")!=first_issue.preparation.PROTOCOL_ID or
        forecast.get("target",{}).get("year")!=YEAR or
        forecast.get("origin",{}).get("year")!=ORIGIN_YEAR or
        forecast.get("protocol",{}).get("horizon_years")!=HORIZON or
        forecast.get("2028_outcomes_resolved")!=0 or
        forecast.get("prospective_predictive_skill_demonstrated") is not False):
        raise ValueError("Unsupported or altered prospective 2028 issue")
    rows=forecast.get("countries")
    if type(rows) is not list or len(rows)!=COHORT or not isinstance(outcomes,dict):
        raise ValueError("Original 196-country issue required")
    ids=[r["country_id"] for r in rows]
    if (any(type(cid) is not int or not 1<=cid<=2000 for cid in ids)
        or len(set(ids))!=COHORT
        or ids!=sorted(ids)):
        raise ValueError("Invalid original GWNO fixed risk set")
    if (not isinstance(provenance,dict) or
        provenance.get("first_complete_release_independently_certified") is not False or
        provenance.get("url_hash_date_are_not_independent_source_attestation") is not True):
        raise ValueError("No self-certification of first official complete release allowed")
    if any(type(cid) is not int or type(y) is not int or y not in (0,1)
           for cid,y in outcomes.items()):
        raise ValueError("Invalid future country-year binary outcomes")
    resolved=[{**r,"observed_2028":outcomes[r["country_id"]]} for r in rows
              if r["country_id"] in outcomes]
    missing=[r["country_id"] for r in rows if r["country_id"] not in outcomes]
    if len(resolved)+len(missing)!=COHORT:
        raise ValueError("Future cohort resolution denominator corrupted")
    result={
        "schema":"idealab.psico.geo2028_first_complete_official_candidate.v1",
        "status":("SOURCE_PRESENT_COVERAGE_INCOMPLETE_UNCERTIFIED" if missing else
                  "COMPLETE_196_SOURCE_CANDIDATE_UNCERTIFIED"),
        "forecast_id":first_issue.preparation.PROTOCOL_ID,
        "forecast_sha256":first_issue.ISSUE_SHA,
        "first_public_forecast_commit":first_issue.FIRST,
        "original_GEO2027_forecast_sha256":registry.EXPECTED["geo"][1],
        "origin_data_year":ORIGIN_YEAR,
        "target_year":YEAR,
        "horizon_years":HORIZON,
        "issued_countries":COHORT,
        "resolved_country_outcomes":len(resolved),
        "unresolved_country_outcomes":len(missing),
        "unresolved_country_gwno":missing,
        "extra_future_source_gwno_ignored":len(set(outcomes)-set(ids)),
        "first_complete_release_independently_attested":False,
        "prospective_skill_demonstrated":False,
        "automatic_primary_model_change_authorized":False,
        "country_outcomes_assumed_iid":False,
        "iid_bootstrap_or_confidence_intervals_present":False,
        "2027_outcomes_used":0,
        "official_source_self_reported":provenance,
        "scores":None,
        "paired_brier_delta_model_minus_global5y":None,
        "paired_brier_delta_model_minus_global_markov":None,
        "calibration_by_origin_state_and_probability_bin":None,
        "mean_forecast_2028_count":sum(r["p_model"] for r in rows),
        "observed_2028_event_count":None,
        "limitation":(
            "Operator-supplied source hash/URL/release date do not independently "
            "establish first complete UCDP annual 2028 edition. No certified "
            "prospective skill is possible from this report alone. An absent "
            "GWNO is not an observed zero. A single 2028 joint country panel "
            "does not justify IID uncertainty, p-values or generalizable skill. "
            "GEO2027 shares 2025 origin and is not independent replication."
        ),
    }
    if missing:
        return result
    scores={name:_scores(resolved,name) for name in MODEL_NAMES}
    model,b0,bm=(scores[x]["brier"] for x in MODEL_NAMES)
    result["scores"]=scores
    result["paired_brier_delta_model_minus_global5y"]=model-b0
    result["paired_brier_delta_model_minus_global_markov"]=model-bm
    result["calibration_by_origin_state_and_probability_bin"]=_calibration(resolved)
    result["observed_2028_event_count"]=sum(r["observed_2028"] for r in resolved)
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--official-zip",required=True)
    p.add_argument("--official-url",required=True)
    p.add_argument("--official-sha256",required=True)
    p.add_argument("--release-date",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    # Force date source validation BEFORE opening external ZIP or outputs.
    metadata=validate_candidate_source(
        args.official_url,args.official_sha256,args.release_date
    )
    doc,_=load_immutable_issue()
    raw=Path(args.official_zip).read_bytes()
    if sha256(raw)!=args.official_sha256:
        raise ValueError("Future official UCDP ZIP bytes differ from claimed SHA-256")
    labels=parse_target_2028_csv(read_zip(raw))
    report=score_eligible_candidate(doc,labels,metadata)
    dest=Path(args.output).resolve()
    if dest==ROOT or ROOT in dest.parents:
        raise ValueError("Candidate scoring report must remain outside immutable repository")
    dest.write_text(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n",
                    encoding="utf8")
    print("GEO2028_CANDIDATE_ONLY",json.dumps({
        "issued":report["issued_countries"],
        "resolved":report["resolved_country_outcomes"],
        "scores_present":report["scores"] is not None,
        "source_first_release_independently_attested":False,
        "prospective_skill_demonstrated":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
