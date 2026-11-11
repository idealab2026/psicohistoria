#!/usr/bin/env python3
"""NEWCONF-2027: FUTURE-ONLY independent outcome resolution candidate evaluator.

This tool is prepared before the outcome year, not a resolution or monitoring
service. It cannot attest that an operator-supplied source is UCDP's FIRST
complete edition covering 2027. Accordingly its reports NEVER claim
independent prospective skill.

Target: ANY(newconf=1) per GW government-country-year. Unlike country-onset2,
UCDP Multiple Onset contains legitimate repeated country-year episode rows.
These are aggregated by logical OR; blank or missing labels are unresolved,
NEVER imputed to zero. The ORIGINAL 196-country forecast, generator and manifest
are checked against cryptographic fingerprints before any score is calculated.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import random
import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from audit_frozen_newconf_2027 import (
    FORECAST, MANIFEST, GENERATOR, audit as audit_issued,
    FROZEN_SHA, FIRST_COMMIT, PREREG_COMMIT
)

YEAR=2027
COHORT=196
MIN_RESOLVED=187  # ceil(.95 * 196); a diagnostic score is not certification.
REPLICATIONS=2000
RANDOM_SEED=20261111
FIELDS=("p_model","p_baseline_global_5y","p_country_eb","p_activity_global")
CALIBRATION_EDGES=(0.0,0.01,0.025,0.05,0.1,1.0)
ALERT_BUDGETS=(5,10,20)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def load_issued(forecast_path=FORECAST, manifest_path=MANIFEST,
                generator_path=GENERATOR):
    raw=Path(forecast_path).read_bytes()
    manifest=json.loads(Path(manifest_path).read_bytes())
    code=Path(generator_path).read_bytes()
    check=audit_issued(raw,manifest,code)
    doc=json.loads(raw)
    if check["issued_country_count"]!=COHORT or sha(raw)!=FROZEN_SHA or \
       doc["provenance"]["generator_sha256"]!=manifest["generator_sha256"]:
        raise ValueError("Immutable 196-country NEWCONF-2027 issue not authenticated")
    return doc,manifest

def validate_future_source(url, claimed_sha, claimed_publication_date):
    """Validate source shape, not the veracity of date/first-release claim."""
    parsed=urlsplit(url)
    if parsed.scheme!="https" or parsed.netloc!="ucdp.uu.se" or \
       parsed.username is not None or parsed.password is not None or \
       parsed.query or parsed.fragment or not re.fullmatch(
          r"/downloads/onset/ucdp-intrastate-country-multiple-onset-(\d{3})\.csv",
          parsed.path):
        raise ValueError("Future input must be a literal UCDP official Multiple Onset CSV URL")
    release=int(re.search(r"-(\d{3})\.csv$",parsed.path).group(1))
    if release<281:
        raise ValueError("A pre-2028 UCDP Onset vintage cannot resolve calendar 2027")
    if not re.fullmatch(r"[0-9a-f]{64}",claimed_sha):
        raise ValueError("Exact original CSV SHA-256 required")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",claimed_publication_date):
        raise ValueError("Actual ISO release date required")
    published=date.fromisoformat(claimed_publication_date)
    if published<=date(YEAR,12,31):
        raise ValueError("Official 2027 annual outcomes cannot be complete before 2028")
    return True

def parse_official_2027_csv(source):
    """Aggregate episode rows; no missing field, country or row is a negative."""
    if isinstance(source,bytes):
        source=source.decode("utf-8-sig")
    reader=csv.DictReader(io.StringIO(source, newline=""))
    fields=reader.fieldnames or []
    if len(fields)!=len(set(fields)) or not {"gwno_a","year","newconf"}.issubset(fields):
        raise ValueError("UCDP Multiple Onset CSV requires unique gwno_a/year/newconf columns")
    by_country=defaultdict(list)
    n_episode_rows=0
    for row in reader:
        if None in row or row.get(None) is not None:
            raise ValueError("Malformed future CSV row cannot be scored")
        y=(row.get("year") or "").strip()
        if not re.fullmatch(r"\d{4}",y):
            raise ValueError("Unusable UCDP country-year calendar field")
        if int(y)!=YEAR:
            continue
        code=(row.get("gwno_a") or "").strip()
        if not re.fullmatch(r"[0-9]{1,5}",code) or not 1<=int(code)<=2000:
            raise ValueError("Invalid or unmapped GW country identifier")
        cid=str(int(code))
        raw=(row.get("newconf") or "").strip()
        if raw not in ("0","1",""):
            raise ValueError("Official newconf is binary or explicitly missing")
        by_country[cid].append(None if raw=="" else int(raw))
        n_episode_rows+=1
    if not by_country:
        raise ValueError("No target-year 2027 rows in submitted source")
    # A country-year with one missing episode remains unresolved even if another
    # observed episode is negative or positive. Never silently impute that row.
    outcomes={
        cid:max(flags) for cid,flags in by_country.items()
        if flags and all(flag in (0,1) for flag in flags)
    }
    missing_label_ids=sorted(cid for cid,flags in by_country.items()
                             if any(flag is None for flag in flags))
    return outcomes,{
       "source_episode_rows_2027":n_episode_rows,
       "source_country_year_groups_2027":len(by_country),
       "source_duplicate_country_year_groups_2027":sum(
           len(flags)>1 for flags in by_country.values()),
       "source_extra_episode_rows_over_country_years":n_episode_rows-len(by_country),
       "country_years_with_incomplete_newconf_label":len(missing_label_ids),
       "source_country_years_resolved":len(outcomes),
       "source_newconf_positive_country_years":sum(outcomes.values()),
       "source_newconf_positive_episode_rows":sum(
           sum(int(v==1) for v in flags)
           for flags in by_country.values() if all(v is not None for v in flags)),
    }

def score(rows,field):
    n=len(rows)
    if not n:
        raise ValueError("Cannot score an empty cohort")
    err=0.0;logloss=0.0
    for row in rows:
        p=row[field];y=row["outcome"]
        if isinstance(p,bool) or not isinstance(p,(float,int)) or \
           not math.isfinite(p) or not 0<p<1 or type(y)!=int or y not in (0,1):
            raise ValueError("Invalid issued probability or binary outcome")
        err+=(p-y)**2
        logloss-=y*math.log(p)+(1-y)*math.log1p(-p)
    return {"brier":err/n,"logloss":logloss/n}

def bootstrap_delta(rows,replications=REPLICATIONS,seed=RANDOM_SEED):
    if not rows or replications<100:
        raise ValueError("Too few resolved countries/replications for bootstrap")
    if len({r["country_id"] for r in rows})!=len(rows):
        raise ValueError("Bootstrap cannot use repeated country-year episodes")
    values=[(r["p_model"]-r["outcome"])**2-
            (r["p_baseline_global_5y"]-r["outcome"])**2 for r in rows]
    n=len(values)
    rng=random.Random(seed)
    draws=sorted(sum(values[rng.randrange(n)] for _ in range(n))/n
                 for _ in range(replications))
    return [draws[int(.025*(replications-1))],
            draws[int(.975*(replications-1))]]

def calibration(rows):
    bins=[]
    for lower,upper in zip(CALIBRATION_EDGES[:-1],CALIBRATION_EDGES[1:]):
        cohort=[r for r in rows if lower<=r["p_model"]<upper]
        bins.append({
            "probability_interval":[lower,upper],
            "n":len(cohort),
            "mean_issued_probability":sum(r["p_model"] for r in cohort)/len(cohort) if cohort else None,
            "event_count":sum(r["outcome"] for r in cohort),
            "observed_event_rate":sum(r["outcome"] for r in cohort)/len(cohort) if cohort else None,
        })
    if sum(b["n"] for b in bins)!=len(rows):
        raise ValueError("Predicted probabilities fall outside preregistered calibration bins")
    return bins

def topk_tie_bounds(rows,limit):
    """All 196 issued countries must have outcomes to prevent partial ranking."""
    if len(rows)!=COHORT:
        raise ValueError("Cannot score top-k if any issued country outcome is missing")
    ranked=sorted(rows,key=lambda r:-r["p_model"])
    threshold=ranked[limit-1]["p_model"]
    certain=[r for r in ranked if r["p_model"]>threshold]
    ties=[r for r in ranked if r["p_model"]==threshold]
    slots=limit-len(certain)
    successes_tie=sum(r["outcome"] for r in ties)
    certain_hits=sum(r["outcome"] for r in certain)
    low=certain_hits+max(0,successes_tie-(len(ties)-slots))
    high=certain_hits+min(successes_tie,slots)
    if not 0<=low<=high<=limit:
        raise ValueError("Invalid tied alert range")
    return {
        "k":limit,
        "higher_probability_countries":len(certain),
        "boundary_tied_countries":len(ties),
        "places_within_boundary_tie":slots,
        "lower_possible_hits":low,
        "upper_possible_hits":high,
        "unique_hit_count":low==high,
        "random_expected_hits":limit*sum(r["outcome"] for r in ranked)/COHORT,
        "not_a_proof_of_ranking_skill":True,
    }

def evaluate(issued,outcomes,source_metadata,source_row_metadata):
    if issued.get("forecast_id")!="PSICO-QGEO01-NEWCONF2027-ORIGIN2025-V1" or \
       issued.get("target",{}).get("year")!=YEAR or \
       len(issued.get("countries",[]))!=COHORT:
        raise ValueError("Outcome evaluation must use original frozen NEWCONF-2027 issue")
    rows=issued["countries"]
    ids=[r["country_id"] for r in rows]
    if len(set(ids))!=COHORT:
        raise ValueError("Issued forecast contains duplicate GW countries")
    if any(type(v)!=int or v not in (0,1) for v in outcomes.values()):
        raise ValueError("Future country outcomes must be binary")
    resolved=[{**row,"outcome":outcomes[row["country_id"]]} for row in rows
              if row["country_id"] in outcomes]
    missing=[row["country_id"] for row in rows
             if row["country_id"] not in outcomes]
    n=len(resolved)
    report={
        "schema":"idealab.psico.newconf_2027_official_resolution_candidate.v1",
        "status":"CANDIDATE_NEEDS_INDEPENDENT_FIRST_COMPLETE_RELEASE_ATTESTATION",
        "forecast_id":issued["forecast_id"],
        "forecast_sha256":FROZEN_SHA,
        "first_public_issue_commit":FIRST_COMMIT,
        "preregistered_protocol_commit":PREREG_COMMIT,
        "target_year":YEAR,
        "unit":"GW country-year; ANY(newconf) over episodes",
        "issued":COHORT,
        "resolved":n,
        "unresolved":COHORT-n,
        "unresolved_issued_country_ids":missing,
        "events_resolved":sum(row["outcome"] for row in resolved),
        "source_coverage":source_row_metadata,
        "source_claim":source_metadata,
        "unissued_official_country_years_ignored":len(set(outcomes)-set(ids)),
        "enough_coverage_for_exploratory_score":n>=MIN_RESOLVED,
        "complete_original_cohort_coverage":n==COHORT,
        "first_complete_official_2027_release_independently_attested":False,
        "future_predictive_skill_independently_verified":False,
        "model_or_baseline_ever_refit":False,
        "model_expected_events_issued":issued["training_summary"]["expected_positive_countries_model"],
        "baseline_expected_events_issued":issued["training_summary"]["expected_positive_countries_baseline"],
        "scores":None,
        "delta_brier_model_minus_global_recent":None,
        "bootstrap_country_delta_brier_95pct":None,
        "calibration":None,
        "alert_budgets_tie_safe":None,
        "limitations":"Operator supplies the official-looking URL, bytes, hash and claimed date. This tool cannot establish it is UCDP's FIRST COMPLETE RELEASE. A score passing the 95% coverage threshold is exploratory until its provenance and all exclusions are independently reviewed. No changes are permitted to the frozen model, comparator or cohort. Never score missing labels as zero.",
    }
    if n<MIN_RESOLVED:
        return report
    report["scores"]={key:score(resolved,key) for key in FIELDS}
    report["scores"]["no_newconf_brier_reference"]={
        "brier":sum(row["outcome"] for row in resolved)/n,
        "logloss":None,
    }
    report["delta_brier_model_minus_global_recent"]=(
        report["scores"]["p_model"]["brier"]-
        report["scores"]["p_baseline_global_5y"]["brier"])
    report["bootstrap_country_delta_brier_95pct"]=bootstrap_delta(resolved)
    report["calibration"]=calibration(resolved)
    if n==COHORT:
        report["alert_budgets_tie_safe"]=[
            topk_tie_bounds(resolved,k) for k in ALERT_BUDGETS]
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--official-csv",required=True,
                        help="Locally downloaded original future UCDP Multiple Onset CSV")
    parser.add_argument("--official-url",required=True)
    parser.add_argument("--official-sha256",required=True)
    parser.add_argument("--release-date",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    validate_future_source(args.official_url,args.official_sha256,args.release_date)
    frozen,_=load_issued()
    raw=Path(args.official_csv).read_bytes()
    if sha(raw)!=args.official_sha256:
        raise ValueError("Submitted original UCDP CSV does not match official SHA-256 claim")
    outcomes,counters=parse_official_2027_csv(raw)
    result=evaluate(frozen,outcomes,{
        "url":args.official_url,
        "sha256":args.official_sha256,
        "claimed_release_date_unverified":args.release_date,
        "first_official_release_independently_verified":False,
        "data_year":YEAR
    },counters)
    target=Path(args.output)
    target.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n",
                      encoding="utf8")
    print("NEWCONF_2027_CANDIDATE_EVALUATION",
          "issued",result["issued"],"resolved",result["resolved"],
          "events",result["events_resolved"],
          "enough_for_exploratory_score",result["enough_coverage_for_exploratory_score"],
          "first_release_independently_attested",False)

if __name__=="__main__":
    main()
