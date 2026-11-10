#!/usr/bin/env python3
"""GEO-2027 scientific diagnostic: same-specification 2-year rolling-origin backtest.

Uses ONLY hash-verified UCDP OrganizedViolenceCY 26.1 (records through 2025).
Each historical origin uses records <= origin, and compares origin+2 labels.
The entire source vintage was released in 2026: archived/revised historical
labels are NOT the releases available at earlier origins. This does not
constitute historically issued, as-of verified, or prospective skill.

This analysis is strictly observational: never change the SHA-pinned original
2027 cohort, its 196 probabilities, or its preregistered comparison model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path

from build_official_countries import (
    OFFICIAL_URL,PINNED_SOURCE_SHA256,MAX_ZIP,EXPECTED_ROWS,read_zip,parse_public_source
)
from forecast_2027_statebased import download_official

TARGET_YEARS=tuple(range(2012,2026))
HORIZON=2
SHRINK=20
LAPLACE=1
RECENT_WINDOW=5
MIN_FOLD=175
BOOTSTRAPS=2000
SEED=20261110
BINS=(0,.05,.1,.2,.4,.6,.8,1)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def from_zip(raw):
    if digest(raw)!=PINNED_SOURCE_SHA256:
        raise ValueError("UCDP OrganizedViolenceCY 26.1 ZIP SHA-256 mismatch")
    return parse_public_source(read_zip(raw))

def _score(records,field):
    if not records: raise ValueError("No country-year outcomes evaluated")
    brier=sum((r[field]-r["outcome"])**2 for r in records)/len(records)
    logloss=0.
    for r in records:
        p=min(1-1e-12,max(1e-12,r[field]))
        logloss-=r["outcome"]*math.log(p)+(1-r["outcome"])*math.log1p(-p)
    return {"brier":brier,"logloss":logloss/len(records)}

def _metrics(rows):
    return {k:_score(rows,k) for k in (
        "p_model","p_global_markov","p_baseline_global_5y")}

def _reliability(rows,field):
    result=[]
    for lo,hi in zip(BINS,BINS[1:]):
        matched=[r for r in rows if lo<=r[field]<(hi if hi<1 else 1.000000001)]
        result.append({
            "lower":lo,"upper":hi,"n":len(matched),
            "predicted":sum(r[field] for r in matched)/len(matched) if matched else None,
            "observed":sum(r["outcome"] for r in matched)/len(matched) if matched else None
        })
    if sum(row["n"] for row in result)!=len(rows):
        raise ValueError("Calibration bins exclude observations")
    return result

def _pairwise_uncertainty(rows,comparand,replications=BOOTSTRAPS,seed=SEED):
    if replications<100:raise ValueError("Insufficient bootstrap draws")
    by_country=defaultdict(lambda:[0,0.0])
    for row in rows:
        slot=by_country[row["country_id"]]
        slot[0]+=1
        slot[1]+=(row["p_model"]-row["outcome"])**2-(row[comparand]-row["outcome"])**2
    samples=list(by_country.values())
    rng=random.Random(seed)
    delta=[]
    for _ in range(replications):
        count=0
        loss=0.
        for _ in range(len(samples)):
            n,d=samples[rng.randrange(len(samples))]
            count+=n;loss+=d
        delta.append(loss/count)
    delta.sort()
    return [delta[int(.025*(replications-1))],delta[int(.975*(replications-1))]]

def _annual_frame(records,origin):
    """Faithful adaptation of the 2027 preregistered equations, no future fit."""
    target=origin+HORIZON
    if origin<2010 or target>2025:
        raise ValueError("Outside fixed historical origin window")
    if any(not h or max(h)>2025 or any(value not in (0,1) for value in h.values())
           for h in records.values()):
        raise ValueError("Invalid official binary source")
    cohort=sorted(cid for cid,h in records.items()
                  if origin in h and origin-1 in h)
    if len(cohort)<MIN_FOLD:
        raise ValueError("Origin cohort is not complete")
    all_counts=[[0,0],[0,0]]
    own={}
    for cid,h in records.items():
        c=[[0,0],[0,0]]
        for year,value in h.items():
            if year>origin or year-1 not in h: continue
            prev=h[year-1]
            c[prev][value]+=1
            all_counts[prev][value]+=1
        own[cid]=c
    if any(sum(row)<100 for row in all_counts):
        raise ValueError("Insufficient global training transitions")
    g=[(row[1]+LAPLACE)/(sum(row)+2*LAPLACE) for row in all_counts]
    exposures=[records[cid][year] for cid in cohort for year in range(origin-RECENT_WINDOW+1,origin+1)
               if year in records[cid]]
    if len(exposures)<.95*len(cohort)*RECENT_WINDOW:
        raise ValueError("Incomplete 5-year baseline source")
    baseline=(sum(exposures)+LAPLACE)/(len(exposures)+2*LAPLACE)
    rows=[]
    for cid in cohort:
        h=records[cid]
        if target not in h:
            continue  # Never assume absent country-year is a non-event
        q=[(own[cid][s][1]+SHRINK*g[s])/(sum(own[cid][s])+SHRINK) for s in (0,1)]
        last=h[origin]
        first=q[last]
        gfirst=g[last]
        probs={
            "p_model":round((1-first)*q[0]+first*q[1],12),
            "p_global_markov":round((1-gfirst)*g[0]+gfirst*g[1],12),
            "p_baseline_global_5y":round(baseline,12)
        }
        if not all(0<v<1 and math.isfinite(v) for v in probs.values()):
            raise ValueError("Invalid historical probability")
        rows.append({"country_id":cid,"target_year":target,
                     "outcome":h[target],**probs})
    if len(rows)<MIN_FOLD:
        raise ValueError("Target outcomes do not cover fixed country cohort")
    return rows,{
        "target_year":target,"origin_cutoff":origin,
        "origin_cohort":len(cohort),"resolved":len(rows),
        "unresolved":len(cohort)-len(rows),
        "positives":sum(x["outcome"] for x in rows),
        "baseline_probability":round(baseline,12)
    }

def evaluate(records):
    all_rows=[]
    folds=[]
    for target in TARGET_YEARS:
        rows,details=_annual_frame(records,target-HORIZON)
        all_rows.extend(rows)
        folds.append({**details,"scores":_metrics(rows)})
    scores=_metrics(all_rows)
    baseline=scores["p_baseline_global_5y"]
    brier_skill=1-scores["p_model"]["brier"]/baseline["brier"]
    delta=scores["p_model"]["brier"]-baseline["brier"]
    year_blocks={}
    for comp in ("p_baseline_global_5y","p_global_markov"):
        year_blocks[comp]=[
            {
                "excluded_year":y,
                "delta_brier":_score([r for r in all_rows if r["target_year"]!=y],"p_model")["brier"]-
                              _score([r for r in all_rows if r["target_year"]!=y],comp)["brier"]
            }
            for y in TARGET_YEARS
        ]
    return {
        "schema":"idealab.psico.statebased_two_year_backtest.v1",
        "question":"GEO-2027 methodological diagnostic",
        "analysis_type":"RETROSPECTIVE_REVISED_26_1_NOT_ASOF_OR_PROSPECTIVE",
        "target_rule":"sb_total_deaths_best >=25; state-based organized violence country-year",
        "source":{"url":OFFICIAL_URL,"version":"26.1","sha256":PINNED_SOURCE_SHA256,
                  "observed_through":2025,"historical_revisions_not_asof":True},
        "model":"SAME_EQUATIONS_AS_FROZEN_2027_WITH_EARLIER_CUTOFF",
        "horizon_years":HORIZON,
        "parameters":{"shrinkage":SHRINK,"laplace":LAPLACE,"global_baseline_years":RECENT_WINDOW},
        "target_years":list(TARGET_YEARS),
        "country_years":len(all_rows),
        "positive_events":sum(x["outcome"] for x in all_rows),
        "unique_countries":len(set(r["country_id"] for r in all_rows)),
        "cohorts_by_year":folds,
        "pooled_scores":scores,
        "brier_skill_vs_global_5y":brier_skill,
        "delta_brier_vs_global_5y":delta,
        "delta_logloss_vs_global_5y":scores["p_model"]["logloss"]-baseline["logloss"],
        "paired_country_bootstrap_95pct":{
            "model_minus_global_5y":_pairwise_uncertainty(all_rows,"p_baseline_global_5y"),
            "model_minus_global_markov":_pairwise_uncertainty(all_rows,"p_global_markov")
        },
        "leave_one_target_year_out_deltas":year_blocks,
        "reliability":{
            "model":_reliability(all_rows,"p_model"),
            "global_markov":_reliability(all_rows,"p_global_markov"),
            "global_5y":_reliability(all_rows,"p_baseline_global_5y")
        },
        "confidence_limitations":"Country bootstrap ignores shared shocks across countries and dependence across overlapping two-year horizons. Intervals are exploratory, not independently calibrated.",
        "interpretation":"Temporal holdout by observation year within a 2026 revised archival edition: historical source availability in each origin year is NOT verified. Same model is now prospectively issued for 2027, but this study does not score or alter that commitment.",
        "prospective_2027_outcomes_resolved":0,
        "prospective_skill_demonstrated":False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-zip")
    ap.add_argument("--check-report")
    args=ap.parse_args()
    source=Path(args.source_zip).read_bytes() if args.source_zip else download_official()
    records,_=from_zip(source)
    result=evaluate(records)
    rendered=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    if args.check_report and Path(args.check_report).read_bytes()!=rendered.encode("utf8"):
        raise ValueError("Published historic diagnostic differs from actual official source calculation")
    print("GEO2027_RETROSPECTIVE_BACKTEST_BEGIN")
    print(rendered,end="")
    print("GEO2027_RETROSPECTIVE_BACKTEST_END")
    print("GEO2027_BACKTEST_COMPLETE",len(TARGET_YEARS),"years",
          result["country_years"],"observations",
          result["positive_events"],"events",
          "prospective_2027_resolved",0)

if __name__=="__main__":main()
