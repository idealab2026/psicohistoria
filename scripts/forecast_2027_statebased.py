#!/usr/bin/env python3
"""IDEA LAB • Q-GEO-2027: immutable-parameter prospective country-year protocol.

This tool prepares a deterministic JSON forecast from ONE hash-pinned 2026 UCDP
edition (year-end 2025). It contains no 2026/2027 observations. The output is
NOT ISSUED until GitHub publicly records the full output in a commit before 2027.
No retrospective predictions are rebranded as issued forecasts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.request import Request, urlopen
from build_official_countries import (
    OFFICIAL_URL, PINNED_SOURCE_SHA256, MAX_ZIP, EXPECTED_ROWS,
    read_zip, parse_public_source,
)

PROTOCOL_ID = "PSICO-GEO2027-STATEBASED25-V1"
TARGET_YEAR = 2027
CUTOFF_YEAR = 2025
SOURCE_VERSION = "26.1"
RECENT_YEARS = (2021, 2022, 2023, 2024, 2025)
TRANSITION_PRIOR = 20
LAPLACE = 1
MIN_COHORT = 190
MAX_COHORT = 210

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def estimate_from_history(records, names):
    if set(records)!=set(names) or not records:
        raise ValueError("Country dictionary mismatch")
    for history in records.values():
        if not history or max(history)>CUTOFF_YEAR:
            raise ValueError("Future or empty historical source forbidden")
        if any(y not in (0,1) for y in history.values()):
            raise ValueError("Invalid binary source outcome")

    cohort=sorted(cid for cid,h in records.items()
                  if CUTOFF_YEAR in h and CUTOFF_YEAR-1 in h)
    if not (MIN_COHORT<=len(cohort)<=MAX_COHORT):
        raise ValueError("2025 frozen country cohort incomplete")
    global_transition=[[0,0],[0,0]]
    per_country={}
    for cid,h in sorted(records.items()):
        local=[[0,0],[0,0]]
        for year in sorted(h):
            if year>1989 and year-1 in h:
                a,b=h[year-1],h[year]
                global_transition[a][b]+=1
                local[a][b]+=1
        per_country[cid]=local
    if min(sum(row) for row in global_transition)<100:
        raise ValueError("Insufficient global transition training data")
    # Beta(1,1) makes global probabilities strictly inside (0,1).
    global_q=[
        (global_transition[s][1]+LAPLACE)/(sum(global_transition[s])+2*LAPLACE)
        for s in (0,1)
    ]
    # Baseline is the Laplace-smoothed pooled 2021-2025 prevalence
    # of the SAME frozen countries; no target-year information.
    exposures=[records[cid][year] for cid in cohort for year in RECENT_YEARS
               if year in records[cid]]
    if len(exposures)<len(cohort)*len(RECENT_YEARS)*0.95:
        raise ValueError("Recent baseline data incomplete")
    baseline=(sum(exposures)+LAPLACE)/(len(exposures)+2*LAPLACE)

    def two_steps(last,rows):
        first=rows[last]
        return (1-first)*rows[0]+first*rows[1]

    country_forecasts=[]
    for cid in cohort:
        history=records[cid]
        last=history[CUTOFF_YEAR]
        local=per_country[cid]
        q=[(local[s][1]+TRANSITION_PRIOR*global_q[s])/
           (sum(local[s])+TRANSITION_PRIOR) for s in (0,1)]
        p=two_steps(last,q)
        global_markov=two_steps(last,global_q)
        if not all(math.isfinite(x) and 0<x<1 for x in (p,global_markov,baseline)):
            raise ValueError("Invalid probability from official data")
        country_forecasts.append({
            "country_id":cid,
            "country":names[cid],
            "last_observed_state_2025":last,
            "p_model":round(p,12),
            "p_global_markov":round(global_markov,12),
            "p_baseline_global_5y":round(baseline,12),
        })
    return country_forecasts, {
        "cohort_n":len(cohort),
        "global_transition_counts":global_transition,
        "global_transition_p_active": [round(x,12) for x in global_q],
        "global_5y_exposures":len(exposures),
        "global_5y_positive":sum(exposures),
        "baseline_global_5y":round(baseline,12),
    }

def build_forecast(source_zip,script_bytes):
    if sha256(source_zip)!=PINNED_SOURCE_SHA256:
        raise ValueError("Pinned official UCDP 26.1 ZIP SHA-256 mismatch")
    records,names=parse_public_source(read_zip(source_zip))
    rows,metadata=estimate_from_history(records,names)
    document={
      "schema":"idealab.psico.prospective_country_2027.v1",
      "forecast_id":PROTOCOL_ID,
      "state":"PREPARED_FOR_PUBLIC_GIT_COMMIT",
      "source":{
        "dataset":"UCDP OrganizedViolenceCY",
        "version":SOURCE_VERSION,
        "url":OFFICIAL_URL,
        "sha256":PINNED_SOURCE_SHA256,
        "license":"CC BY 4.0",
        "records_in_edition":EXPECTED_ROWS,
        "data_last_year":CUTOFF_YEAR,
      },
      "target":{
        "year":TARGET_YEAR,
        "source_field":"sb_total_deaths_best",
        "binary_rule":"1 iff UCDP official 2027 country-year sb_total_deaths_best >= 25; otherwise 0",
        "unit":"country-year",
        "geography":"Gleditsch-Ward country_id from source 2025",
        "not_onset2":True,
        "not_state_violence_against_civilians":True,
        "evaluation_release":"first official annual UCDP OrganizedViolenceCY release covering all 2027 data, after 2027",
        "revisions_policy":"First complete release is primary; later revised releases only as separately marked sensitivity.",
        "missing_policy":"Absent country ID or unavailable official label remains unresolved, never assumed 0.",
      },
      "protocol":{
        "horizon_years":2,
        "training_last_year":CUTOFF_YEAR,
        "country_cohort_rule":"countries with both 2024 and 2025 records in the hash-pinned source",
        "model_primary":"country_markov_2step_laplace_global_shrink20",
        "model_explanation":"Estimate 1-year binary transitions through 2025 separately by country; shrink each row to global Laplace transition rate with strength 20. Compose transition matrix twice from observed 2025 state.",
        "baseline_primary":"global_laplace_5y_2021_2025",
        "secondary_comparator":"global_markov_2step_laplace",
        "primary_loss":"Brier score of frozen p_model minus frozen p_baseline_global_5y over resolved cohort",
        "secondary_losses":["log-loss","Brier vs global Markov","calibration bins"],
        "inference":"Country-cluster bootstrap 2000 resamples; exploratory until outcome observed.",
        "comparison_policy":"All 196 forecasts and baseline probabilities are frozen before 2027; no post-hoc model swapping.",
        "denominator_policy":"Report total issued, resolved, unresolved and each outcome; do not convert missing outcomes to negatives.",
        "skill_not_demonstrated":True,
      },
      "provenance":{
        "generator_sha256":sha256(script_bytes),
        "independent_timestamp_authority":False,
        "official_source_available_before_target_year":True,
        "first_public_issue_time":"GitHub's first publicly accessible commit containing the complete forecast; not the generator execution time",
        "historical_forecasts_issued":False,
      },
      "training_summary":metadata,
      "countries":rows,
    }
    return document

def validate_candidate(document):
    if document.get("forecast_id")!=PROTOCOL_ID or document.get("state")!="PREPARED_FOR_PUBLIC_GIT_COMMIT":
        raise ValueError("Invalid freeze protocol state")
    countries=document.get("countries",[])
    if len(countries)!=document.get("training_summary",{}).get("cohort_n") or len(countries)<MIN_COHORT:
        raise ValueError("Invalid cohort")
    ids=[c["country_id"] for c in countries]
    if sorted(ids)!=ids or len(set(ids))!=len(ids):
        raise ValueError("Duplicate/unsorted frozen country IDs")
    required=("p_model","p_global_markov","p_baseline_global_5y")
    for row in countries:
        if any(not isinstance(row.get(key),(int,float)) or
               not 0<row[key]<1 or not math.isfinite(row[key]) for key in required):
            raise ValueError("Invalid issued probability")
        if row.get("last_observed_state_2025") not in (0,1):
            raise ValueError("Invalid 2025 state")
    if document["target"]["year"]!=2027 or document["source"]["data_last_year"]!=2025:
        raise ValueError("Unsafe temporal window")
    if document["protocol"]["skill_not_demonstrated"] is not True:
        raise ValueError("Cannot claim unverified skill")
    return True

def download_official():
    req=Request(OFFICIAL_URL,headers={"User-Agent":"IDEA-LAB-PSICOHISTORIA prospective country-year v1"})
    with urlopen(req,timeout=55) as response:
        if response.geturl()!=OFFICIAL_URL:
            raise ValueError("Official UCDP unexpected redirect")
        raw=response.read(MAX_ZIP+1)
    if len(raw)>MAX_ZIP:raise ValueError("Source exceeds allowed ZIP size")
    return raw

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True,help="Deterministic candidate output, never self-certifies issuance")
    parser.add_argument("--source-zip",help="Optional offline official ZIP for independent reproduction")
    parser.add_argument("--print-chunks",action="store_true",help="Print JSON in labeled chunks for institutional commit")
    args=parser.parse_args()
    script=Path(__file__).read_bytes()
    zip_bytes=Path(args.source_zip).read_bytes() if args.source_zip else download_official()
    document=build_forecast(zip_bytes,script)
    validate_candidate(document)
    payload=json.dumps(document,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n"
    Path(args.output).write_text(payload,encoding="utf-8")
    print("IDEALAB_FORECAST_READY",document["forecast_id"],"countries",len(document["countries"]),
          "source_sha256",PINNED_SOURCE_SHA256,"document_sha256",sha256(payload.encode()))
    if args.print_chunks:
        print("IDEALAB_FORECAST_BEGIN")
        for i in range(0,len(payload),2000):
            print("IDEALAB_FORECAST_PART",i//2000,payload[i:i+2000])
        print("IDEALAB_FORECAST_END")

if __name__=="__main__":main()
