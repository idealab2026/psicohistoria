#!/usr/bin/env python3
"""UCDP Onset2: origin-frozen lagged-onset1 signal vs conservative baselines.

Scientific classification: exploratory, source-version-separated, NOT historically
issued and NOT an operational prediction of new wars. UCDP 23.1 official
intrastate-country onset dataset is the only source used for fitting.

Evaluation:
  A. Rolling internal retrospective cutoffs 2014..2020; labels from the same
     23.1 edition at horizons +1 and +2; this is revised-vintage validation.
  B. Heldout 2023/2024 outcomes from DIFFERENT official 25.1 edition, with
     every predictor (including onset1) observed <=2022 in 23.1. No 2023
     onset1 is used to score 2024. Both vintage files SHA-256 checked.

Five fixed, non-tuned candidates:
  - full-horizon global rate (Beta(1,1), source-origin-only pairs)
  - last-five-target-years global rate (Beta(1,1))
  - country EB onset2 rate (country 2000..cutoff; shrink20 towards full rate)
  - lag-onset1 group-specific horizon rate (group shrink20 towards full rate)
  - country EB shrink20 towards lag-onset1 group horizon rate

The 2023/24 labels have already been inspected in previous analyses. No new
variant may be called independent confirmation or prospectively validated.
No country-level scores, ranks, or identifiers may be printed or stored.
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
from pathlib import Path

from inspect_ucdp_archives import fetch
from evaluate_homogeneous_onset2 import SOURCES,score,ranking

START=2000
TRAIN_CUTOFFS=tuple(range(2014,2021))
EXTERNAL_CUTOFF=2022
HORIZONS=(1,2)
PRIOR_STRENGTH=20
LAPLACE=1
RECENT_YEARS=5
BOOTSTRAPS=2000
SEED=20261110
FIELDS=("year","gwno_a","onset1","onset2")
MODELS=("global_h","global_recent5","country_eb","lag1_global","lag1_country")

def load_panel(version,fetcher=fetch):
    if version not in ("23.1","25.1"):
        raise ValueError("Unapproved UCDP onset edition")
    url=SOURCES[version]["url"]
    blob=fetcher(url,6_000_000)
    if hashlib.sha256(blob).hexdigest()!=SOURCES[version]["sha256"]:
        raise ValueError("Historical UCDP onset edition changed: "+version)
    reader=csv.DictReader(io.StringIO(blob.decode("utf-8-sig")))
    fields=reader.fieldnames or []
    if not set(FIELDS).issubset(fields):
        raise ValueError("UCDP country-level onset data lacks onset1 or onset2")
    panel=defaultdict(dict)
    rows=0
    for data in reader:
        year=int(data["year"])
        cid=data["gwno_a"].strip()
        if not cid or not cid.isdigit():
            raise ValueError("Bad country identifier in official data")
        values=[]
        for name in ("onset1","onset2"):
            raw=data[name].strip()
            if raw not in ("0","1"):
                raise ValueError("Nonbinary official onset indicator")
            values.append(int(raw))
        if values[1]>values[0]:
            raise ValueError("onset2=1 and onset1=0: incompatible UCDP country onset flags")
        if year in panel[cid]:
            raise ValueError("Official UCDP source has duplicate country-year")
        panel[cid][year]=tuple(values)
        rows+=1
    if rows<12000 or max(max(y for y in h) for h in panel.values())!=SOURCES[version]["last_year"]:
        raise ValueError("UCDP source not fully covered")
    return panel,{"version":version,"url":url,"sha256":SOURCES[version]["sha256"],
                  "max_year":SOURCES[version]["last_year"],"rows":rows,
                  "has_onset1":True,"has_onset2":True}

def _fit(panel,cutoff,horizon,cohort):
    if cutoff < 2014 or horizon not in HORIZONS or \
       max(max(h) for h in panel.values())<cutoff:
        raise ValueError("Model training window invalid")
    # Never use historical outcome observations beyond cutoff, not even to
    # derive prior, eligible universe, risk set, or conditional feature values.
    outcomes=[]
    country=defaultdict(lambda:[0,0])
    paired=[]
    for code,h in panel.items():
        for year,(one,two) in h.items():
            if START<=year<=cutoff:
                country[code][0]+=two
                country[code][1]+=1
            if START<=year and year+horizon<=cutoff and year+horizon in h:
                paired.append((year,code,one,h[year+horizon][1]))
    if len(paired)<2000:
        raise ValueError("Too few historical origin-target pairs")
    global_p=(sum(y for _,_,_,y in paired)+LAPLACE) / (len(paired)+2*LAPLACE)
    recent=[y for t,c,one,y in paired if t+horizon>=cutoff-RECENT_YEARS+1]
    if len(recent)<850:
        raise ValueError("Recent global exposure insufficient")
    recent_p=(sum(recent)+LAPLACE)/(len(recent)+2*LAPLACE)
    group=defaultdict(lambda:[0,0])
    for year,code,one,y in paired:
        group[one][0]+=y
        group[one][1]+=1
    conditional={
        g:(group[g][0]+PRIOR_STRENGTH*global_p) /
          (group[g][1]+PRIOR_STRENGTH)
        for g in (0,1)
    }
    if len(cohort)<180:
        raise ValueError("Insufficient origin country coverage")
    predictions={}
    for cid in cohort:
        if cutoff not in panel.get(cid,{}):
            raise ValueError("Country origin label missing")
        own=country[cid]
        p_country=(own[0]+PRIOR_STRENGTH*global_p)/(own[1]+PRIOR_STRENGTH)
        one=panel[cid][cutoff][0]
        p_cond=conditional[one]
        p_comb=(own[0]+PRIOR_STRENGTH*p_cond)/(own[1]+PRIOR_STRENGTH)
        result={
            "global_h":global_p,
            "global_recent5":recent_p,
            "country_eb":p_country,
            "lag1_global":p_cond,
            "lag1_country":p_comb,
        }
        if not all(0<p<1 and math.isfinite(p) for p in result.values()):
            raise ValueError("Out-of-bounds fitted probabilities")
        predictions[cid]=result
    return predictions,{
        "cutoff":cutoff,"horizon":horizon,
        "historical_origin_target_pairs":len(paired),
        "global_rate":global_p,"global_recent5_rate":recent_p,
        "lag1_0_exposure":group[0][1],"lag1_0_events":group[0][0],
        "lag1_1_exposure":group[1][1],"lag1_1_events":group[1][0],
        "max_fitted_outcome_year":cutoff,
        "horizon_2_feature_not_from_intermediate_year":True
    }

def score_rows(rows):
    n=len(rows)
    if n<170:
        raise ValueError("Insufficient origin-matched outcome observations")
    result={}
    for key in MODELS:
        result[key]=score([{"outcome":r["outcome"],key:r[key]} for r in rows],key)
    return result

def _pooled_bootstrap(rows,competitor,challenger="lag1_country",draws=BOOTSTRAPS,seed=SEED):
    if draws<100:raise ValueError("Too few bootstrap samples")
    grouped=defaultdict(list)
    for r in rows:
        grouped[r["country"]].append(r)
    ids=sorted(grouped)
    if len(ids)<150:raise ValueError("Too few country blocks")
    rng=random.Random(seed)
    v=[]
    for _ in range(draws):
        total=0.0;n=0
        for _ in ids:
            cid=rng.choice(ids)
            for row in grouped[cid]:
                total+=(row[challenger]-row["outcome"])**2-(row[competitor]-row["outcome"])**2
                n+=1
        v.append(total/n)
    v.sort()
    return [v[int((draws-1)*.025)],v[int((draws-1)*.975)]]

def _ranking(rows,key):
    # AP tie-robust via existing rank_summary; no country names are exposed.
    transformed=[{"country":r["country"],"outcome":r["outcome"],"model":r[key]} for r in rows]
    # Ranking with equal scores has arbitrary topK boundary. Publish counts and
    # explicit tie flags rather than presenting them as unique actionable order.
    return ranking(transformed)

def evaluate_at_origin(origin,truth,cutoff):
    if not origin or not truth:
        raise ValueError("Missing historical origin/outcome source")
    if cutoff not in {2022,*TRAIN_CUTOFFS}:
        raise ValueError("Origin not in fixed grid")
    cohort=sorted(cid for cid,h in origin.items() if cutoff in h)
    if len(cohort)<190:
        raise ValueError("Missing required origin country observations")
    scored=[];folds=[]
    for horizon in HORIZONS:
        year=cutoff+horizon
        estimates,fit=_fit(origin,cutoff,horizon,cohort)
        rows=[]
        for cid in cohort:
            if year not in truth.get(cid,{}):
                continue
            rows.append({"country":cid,"year":year,"horizon":horizon,
                         "outcome":truth[cid][year][1],**estimates[cid]})
        if len(rows)<len(cohort)-6:
            raise ValueError("Too many unresolved outcome country-years")
        folds.append({
            "cutoff":cutoff,"year":year,"horizon":horizon,
            "origin_countries":len(cohort),"resolved":len(rows),
            "unresolved":len(cohort)-len(rows),
            "positive_onset2":sum(r["outcome"] for r in rows),
            "fit":fit,"scores":score_rows(rows),
            "ranking_country_eb":_ranking(rows,"country_eb"),
            "ranking_lag1_country":_ranking(rows,"lag1_country"),
        })
        scored.extend(rows)
    return scored,folds

def evaluate(source):
    base=source["23.1"]
    later=source["25.1"]
    if max(max(h) for h in base.values())!=2022 or max(max(h) for h in later.values())!=2024:
        raise ValueError("Source edition cutoff incompatible with analysis")
    # Within one revised edition, internal rolling origins. No future year
    # enters model fitting at the simulated cutoff, but historical data may
    # have been revised before edition 23.1 was published.
    internal=[];internal_folds=[]
    for cutoff in TRAIN_CUTOFFS:
        r,fs=evaluate_at_origin(base,base,cutoff)
        internal.extend(r)
        internal_folds.extend(fs)
    external,external_folds=evaluate_at_origin(base,later,EXTERNAL_CUTOFF)
    internal_scores=score_rows(internal)
    external_scores=score_rows(external)
    distinct_internal={}
    for row in internal:
        key=(row["country"],row["year"])
        if key in distinct_internal and distinct_internal[key]!=row["outcome"]:
            raise ValueError("Contradictory repeated historical target label")
        distinct_internal[key]=row["outcome"]
    internal_by_horizon={
        str(h):{
            "n":sum(row["horizon"]==h for row in internal),
            "events":sum(row["outcome"] for row in internal if row["horizon"]==h),
            "scores":score_rows([row for row in internal if row["horizon"]==h])
        }
        for h in HORIZONS
    }
    return {
        "schema":"idealab.psico.onset2_lagged_231_251_ablation.v1",
        "status":"POST_HOC_MODEL_FAMILY_EXPLORATION_NOT_PROSPECTIVE",
        "question":"UCDP Intrastate Country-Level Onset2 rather than state-based violence threshold",
        "source_vintages":{
           v:{"url":SOURCES[v]["url"],"sha256":SOURCES[v]["sha256"],
              "max_year":SOURCES[v]["last_year"]}
           for v in ("23.1","25.1")
        },
        "feature_definition":"Observed onset1 flag in origin-year country row only; never target-year or intermediate-year onset1",
        "model_definitions":{
           "global_h":"global onset2 rate in country origin-target pairs with horizon h, Laplace1",
           "global_recent5":"global onset2 rate in last five eligible target years, Laplace1",
           "country_eb":"country onset2 history since 2000, shrink20 to global_h",
           "lag1_global":"empirical onset2 rate conditioned on origin-year onset1, shrink20 to global_h",
           "lag1_country":"country onset2 count shrunk by 20 to lag1_global",
        },
        "sample_definitions":{
            "rolling_origins":list(TRAIN_CUTOFFS),"external_origin":EXTERNAL_CUTOFF,
            "horizons":list(HORIZONS),"start_train":START,
            "prior_strength":PRIOR_STRENGTH,"laplace":LAPLACE,
            "recent_baseline_years":RECENT_YEARS
        },
        "internal":{
            "source_edition":"23.1","n":len(internal),
            "events":sum(r["outcome"] for r in internal),
            "unique_country_target_years":len(distinct_internal),
            "unique_positive_country_target_years":sum(distinct_internal.values()),
            "repeated_target_evaluations":len(internal)-len(distinct_internal),
            "by_horizon":internal_by_horizon,
            "scores":internal_scores,"folds":internal_folds,
            "country_bootstrap_delta_vs_global_h":
                 _pooled_bootstrap(internal,"global_h"),
            "country_bootstrap_delta_vs_country_eb":
                 _pooled_bootstrap(internal,"country_eb"),
        },
        "external":{
            "origin_release":"23.1","assessment_release":"25.1",
            "n":len(external),"events":sum(r["outcome"] for r in external),
            "scores":external_scores,"folds":external_folds,
            "country_bootstrap_delta_vs_global_h":
                 _pooled_bootstrap(external,"global_h"),
            "country_bootstrap_delta_vs_country_eb":
                 _pooled_bootstrap(external,"country_eb"),
        },
        "model_selected_or_retrained_on_outcomes":False,
        "hypotheses_were_designated_after_previous_holdout_inspection":True,
        "historical_predictions_were_issued":False,
        "revised_internal_vintage_verified_asof":False,
        "independently_timestamped_original_release":False,
        "country_risks_published":False,
        "prospective_2027_issued_forecast_changed":False,
        "actual_2027_results_resolved":0,
        "predictive_skill_demonstrated":False,
        "caution":"This study compares several hypothesis models with previously seen 2023/24 outcomes; it cannot claim independent testing or any certified skill. UCDP onset1 is an event marker, not the full underlying active-conflict risk-set definition. Country-onset2 labels are not state-based threshold crossings. Source 23.1 retrospective rolling windows have revised historical information. Internal rolling folds reuse some target country-years under different origins/horizons, so 2744 forecast evaluations represent only 1568 distinct country-years and 22 distinct onsets; they are not independent cases. Country-bootstrap misses common-year shocks. The original 196 issued 2027 probabilities are untouched."
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report")
    args=ap.parse_args()
    original,info1=load_panel("23.1")
    later,info2=load_panel("25.1")
    study=evaluate({"23.1":original,"25.1":later})
    content=json.dumps(study,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    print("ONSET2_LAGGED_ABLATION_BEGIN")
    print(content,end="")
    print("ONSET2_LAGGED_ABLATION_END")
    if args.check_report and Path(args.check_report).read_bytes()!=content.encode("utf8"):
        raise ValueError("Archived onset2 lagged-signal report disagrees with pinned UCDP editions")
    print("ONSET2_LAGGED_ABLATION_SUMMARY",study["internal"]["n"],study["internal"]["events"],
          study["external"]["n"],study["external"]["events"],
          "prospective_2027_resolved",0)

if __name__=="__main__":
    main()
