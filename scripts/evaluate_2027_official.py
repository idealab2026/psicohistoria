#!/usr/bin/env python3
"""IDEA LAB GEO-2027 • evaluation gate for a future official UCDP 2027 release.

This is a PREPARED scoring tool, not evidence that 2027 has been observed.
It refuses unpinned source bytes and never upgrades self-reported source
provenance to independently verified prospective skill.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import random
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from build_official_countries import read_zip

FORECAST_SHA="5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5"
FORECAST_ID="PSICO-GEO2027-STATEBASED25-V1"
COHORT=196
YEAR=2027
MIN_RESOLVED=187  # ceil(0.95 * 196)
REPLICATIONS=2000
SEED=20261110

def digest(content):
    return hashlib.sha256(content).hexdigest()

def load_frozen_issue(document_path,manifest_path):
    raw=Path(document_path).read_bytes()
    forecast=json.loads(raw)
    manifest=json.loads(Path(manifest_path).read_text(encoding="utf8"))
    if digest(raw)!=FORECAST_SHA or manifest.get("forecast_sha256")!=FORECAST_SHA or \
       manifest.get("status")!="ISSUED_PROSPECTIVE_UNRESOLVED" or \
       manifest.get("first_public_forecast_commit")!="3bb3561c8d6182c30624591276c705fb76ce99dc" or \
       manifest.get("canonical_document_commit")!="8b924e0b0c7a07e27977160c9658cfed77940aff" or \
       manifest.get("preregistered_protocol_main_commit")!="87959a117e1b30323392a488c48c9afb1cb0bffc" or \
       forecast.get("forecast_id")!=FORECAST_ID or \
       forecast.get("state")!="PREPARED_FOR_PUBLIC_GIT_COMMIT" or \
       forecast.get("target",{}).get("year")!=YEAR or \
       forecast.get("source",{}).get("data_last_year")!=2025 or \
       len(forecast.get("countries",[]))!=COHORT:
        raise ValueError("Frozen prospective issue or its public SHA-256 is not verifiable")
    countries=forecast["countries"]
    ids=[c["country_id"] for c in countries]
    if sorted(ids)!=ids or len(set(ids))!=COHORT or any(
       not all(0<c[k]<1 for k in ("p_model","p_baseline_global_5y","p_global_markov"))
       for c in countries):
        raise ValueError("Issued probabilities or immutable country cohort invalid")
    return forecast,manifest

def validate_future_source(url,source_sha,release_date):
    parts=urlsplit(url)
    if parts.scheme!="https" or parts.netloc!="ucdp.uu.se" or \
       not parts.path.startswith("/downloads/organizedviolencecy/") or \
       not parts.path.endswith("-csv.zip") or parts.query or parts.fragment:
        raise ValueError("Only literal official future UCDP ZIP URLs admitted")
    if len(source_sha)!=64 or any(c not in "0123456789abcdef" for c in source_sha):
        raise ValueError("Future source SHA-256 required")
    parsed=date.fromisoformat(release_date)
    if parsed<=date(2027,12,31):
        raise ValueError("2027 outcome dataset cannot have been published before the year ended")
    return True

def parse_2027_outcomes(source_csv):
    text=source_csv.decode("utf-8-sig") if isinstance(source_csv,bytes) else source_csv
    reader=csv.DictReader(io.StringIO(text))
    header=set(reader.fieldnames or [])
    def chosen(*names):
        return next((name for name in names if name in header),None)
    key=chosen("country_id","country_id_cy")
    ykey=chosen("year","year_cy")
    measure=chosen("sb_total_deaths_best","sb_total_deaths_best_cy")
    if None in (key,ykey,measure):
        raise ValueError("Missing official country/year/best state-based deaths columns")
    outcomes={}
    for row in reader:
        year=int(row[ykey])
        if year!=YEAR:
            continue
        cid=int(row[key]); deaths=int(row[measure])
        if not (1<=cid<=2000 and 0<=deaths<=10000000):
            raise ValueError("Out of-range official 2027 outcome")
        if cid in outcomes:
            raise ValueError("Duplicate 2027 country-year in official candidate release")
        outcomes[cid]=int(deaths>=25)
    if not outcomes:
        raise ValueError("Official candidate source does not contain target year 2027")
    return outcomes

def summary_scores(rows,field):
    if not rows:
        raise ValueError("Empty resolved forecast panel")
    brier=sum((r[field]-r["outcome"])**2 for r in rows)/len(rows)
    logloss=0.
    for row in rows:
        p=max(1e-12,min(1-1e-12,row[field]))
        logloss-=row["outcome"]*math.log(p)+(1-row["outcome"])*math.log1p(-p)
    return {"brier":brier,"logloss":logloss/len(rows)}

def bootstrap_interval(rows,replications=REPLICATIONS,seed=SEED):
    if not rows or replications<100:
        raise ValueError("Too few observations or replicates")
    rng=random.Random(seed)
    values=[(row["p_model"]-row["outcome"])**2-
            (row["p_baseline_global_5y"]-row["outcome"])**2 for row in rows]
    n=len(values)
    draws=sorted(sum(values[rng.randrange(n)] for _ in range(n))/n
                 for _ in range(replications))
    return [draws[int(.025*(replications-1))],draws[int(.975*(replications-1))]]

def evaluate(forecast,outcomes,metadata):
    if forecast.get("forecast_id")!=FORECAST_ID or forecast.get("target",{}).get("year")!=YEAR:
        raise ValueError("Wrong frozen forecast target")
    issued=forecast["countries"]
    if len(issued)!=COHORT:
        raise ValueError("Changed issued cohort")
    resolved=[{**row,"outcome":outcomes[row["country_id"]]} for row in issued
              if row["country_id"] in outcomes]
    unresolved=[row["country_id"] for row in issued if row["country_id"] not in outcomes]
    total=len(issued)
    all_outcome_ids={row["country_id"] for row in issued}
    result={
        "schema":"idealab.psico.2027_resolution_candidate.v1",
        "status":"SELF_REPORTED_OFFICIAL_SOURCE_NEEDS_FIRST_RELEASE_ATTESTATION",
        "forecast_id":FORECAST_ID,
        "target_year":YEAR,
        "issued":total,
        "resolved":len(resolved),
        "unresolved":len(unresolved),
        "missing_issued_country_ids":unresolved,
        "outcome_source_country_years":len(outcomes),
        "unissued_future_country_ids_ignored":len(set(outcomes)-all_outcome_ids),
        "events":sum(r["outcome"] for r in resolved),
        "coverage_95pct_gate_passed":len(resolved)>=MIN_RESOLVED,
        "first_official_release_independently_attested":False,
        "prospective_skill_independently_verified":False,
        "source":metadata,
        "scores":None,
        "interval_delta_brier_model_minus_baseline":None,
        "calibration_bins":None,
        "limitations":"Only a candidate evaluation. A release URL, hash, and date supplied by an operator do not independently establish this is UCDP's first complete 2027 release. No performance claim is certified until external source provenance and full cohort coverage are checked."
    }
    if len(resolved)<MIN_RESOLVED:
        return result
    result["scores"]={
        "model":summary_scores(resolved,"p_model"),
        "baseline_global_5y":summary_scores(resolved,"p_baseline_global_5y"),
        "secondary_global_markov":summary_scores(resolved,"p_global_markov")
    }
    result["interval_delta_brier_model_minus_baseline"]=bootstrap_interval(resolved)
    bins=[]
    for i in range(5):
        part=[r for r in resolved if min(4,int(r["p_model"]*5))==i]
        bins.append({
            "range":[i/5,(i+1)/5],
            "n":len(part),
            "avg_prediction":sum(r["p_model"] for r in part)/len(part) if part else None,
            "observed_positive_rate":sum(r["outcome"] for r in part)/len(part) if part else None
        })
    result["calibration_bins"]=bins
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--issued",required=True)
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--official-zip",required=True)
    ap.add_argument("--official-url",required=True)
    ap.add_argument("--official-sha256",required=True)
    ap.add_argument("--release-date",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    validate_future_source(args.official_url,args.official_sha256,args.release_date)
    forecast,_=load_frozen_issue(args.issued,args.manifest)
    raw=Path(args.official_zip).read_bytes()
    if digest(raw)!=args.official_sha256:
        raise ValueError("Future official source bytes do not match declared SHA-256")
    outcomes=parse_2027_outcomes(read_zip(raw))
    report=evaluate(forecast,outcomes,{
        "url":args.official_url,"sha256":args.official_sha256,
        "release_date_self_reported":args.release_date,
        "data_year":YEAR
    })
    Path(args.output).write_text(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("GEO_2027_EVALUATION_CANDIDATE", "issued",report["issued"],"resolved",report["resolved"],
          "outcomes",report["events"],"gate",report["coverage_95pct_gate_passed"],
          "official_provenance_independently_attested",False)

if __name__=="__main__":main()
