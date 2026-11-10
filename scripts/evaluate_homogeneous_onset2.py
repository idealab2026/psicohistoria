#!/usr/bin/env python3
"""GEO Q-GEO-01: homogeneous UCDP intrastate-country onset2 vintage holdout.

Only UCDP 23.1 and 25.1 *intrastate country-level onset* editions, each
downloaded from official pinned URLs. 19.1 is excluded: its duplicated country-
years and uncertain analytical unit cannot be silently made comparable.

Train 2000–2022 (origin file 23.1), test 2023 and 2024 (later file 25.1).
This is an EX-POST cross-release reconstruction: the 23.1 edition was not
available before the end of 2022; training cutoff does not certify 1-2 years
of operational lead time. Neither year was issued as a prospective forecast.

Compare country empirical Bayes shrinkage (alpha=20) against full and last-
five-year global baselines, report Brier, log-loss, AP/ROC-AUC and top10
alert precision. The no-onset classifier is scored by Brier only. No
country risks or private sources are published.
"""
from __future__ import annotations
import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

from inspect_ucdp_archives import fetch,digest,onset_labels,compare_revisions
from run_legacy_vintage_holdout import SOURCES,START_TRAIN_YEAR,REGULARIZATION
from evaluate_2027_new_entries import average_precision,roc_auc

ORIGIN_VERSION="23.1"
TARGET_VERSION="25.1"
CUTOFF=2022
TRAIN_START=2000
RECENT_START=2018
TEST_YEARS=(2023,2024)
REPS=2000
SEED=20261110
ALERT_K=(5,10,20)

def load_homogeneous_sources(fetcher=fetch):
    result={}
    for version in (ORIGIN_VERSION,TARGET_VERSION):
        info=SOURCES[version]
        raw=fetcher(info["url"],6_000_000)
        if digest(raw)!=info["sha256"]:
            raise ValueError("Official UCDP intrastate onset2 source digest mismatch: "+version)
        labels=onset_labels(raw)
        if max(y for y,_ in labels)!=info["last_year"]:
            raise ValueError("Historical onset edition coverage changed")
        if len(labels)<9000:
            raise ValueError("Unexpectedly incomplete official onset archive")
        result[version]=labels
    return result

def predict(src,final):
    if max(y for y,_ in src)!=CUTOFF or max(y for y,_ in final)!=2024:
        raise ValueError("Origin or outcome edition has unexpected last year")
    training=[(y,code,outcome) for (y,code),outcome in src.items()
              if TRAIN_START<=y<=CUTOFF]
    five=[outcome for y,code,outcome in training if RECENT_START<=y<=CUTOFF]
    if len(training)<4000 or len(five)<850:
        raise ValueError("Insufficient origin-only training exposures")
    origin_universe={code for y,code in src if y==CUTOFF}
    if len(origin_universe)!=196:
        raise ValueError("Official origin country universe changed")
    global_p=(sum(event for _,_,event in training)+1)/(len(training)+2)
    recent_p=(sum(five)+1)/(len(five)+2)
    by_country=defaultdict(lambda:[0,0])
    for _,code,outcome in training:
        by_country[code][0]+=outcome
        by_country[code][1]+=1
    fit={code:(by_country[code][0]+REGULARIZATION*global_p)/
               (by_country[code][1]+REGULARIZATION) for code in origin_universe}
    rows=[]
    folds=[]
    for year in TEST_YEARS:
        target={code:event for (y,code),event in final.items() if y==year}
        covered=sorted(origin_universe & target.keys())
        if len(covered)<190:
            raise ValueError("Unresolved origin population greater than allowed")
        for code in covered:
            rows.append({
                "target_year":year,
                "country":code,
                "outcome":target[code],
                "model":fit[code],
                "global":global_p,
                "recent_global":recent_p,
                "no_onset":0.0,
            })
        folds.append({
            "year":year,"origin_countries":len(origin_universe),
            "resolved":len(covered),
            "unresolved":len(origin_universe)-len(covered),
            "events":sum(target[code] for code in covered),
        })
    return rows,folds,{
        "training_country_years":len(training),
        "training_onset2_events":sum(event for _,_,event in training),
        "recent_country_years":len(five),
        "recent_onset2_events":sum(five),
        "origin_country_universe":len(origin_universe),
        "global_probability":global_p,
        "recent_global_probability":recent_p,
        "regularization":REGULARIZATION,
        "source_last_year":CUTOFF,
        "future_outcome_labels_used_in_fit":False,
    }

def score(rows,key):
    if not rows:raise ValueError("Empty onset2 sample")
    loss=sum((r[key]-r["outcome"])**2 for r in rows)/len(rows)
    if key=="no_onset":
        return {"brier":loss,"logloss":None}
    ll=0
    for row in rows:
        p=min(1-1e-12,max(1e-12,row[key]))
        ll-=row["outcome"]*math.log(p)+(1-row["outcome"])*math.log1p(-p)
    return {"brier":loss,"logloss":ll/len(rows)}

def ranking(rows):
    n=len(rows)
    positives=sum(r["outcome"] for r in rows)
    bymodel=sorted(rows,key=lambda r:(-r["model"],r["country"]))
    return {
        "n":n,"events":positives,
        "base_rate":positives/n,
        "average_precision_country_model":average_precision(rows,"model"),
        "auc_country_model":roc_auc(rows,"model"),
        "top_k_country_model":{
            str(k):{
                "k":k,
                "hits":sum(r["outcome"] for r in bymodel[:k]),
                "precision":sum(r["outcome"] for r in bymodel[:k])/k,
                "random_expected_hits":k*positives/n,
                "ties_at_k":bymodel[k-1]["model"]==bymodel[k]["model"]
            }
            for k in ALERT_K
        }
    }

def bootstrap(rows,comp,reps=REPS,seed=SEED):
    if reps<100:raise ValueError("Bootstrap requires at least 100 replicates")
    bycountry=defaultdict(list)
    for row in rows:
        bycountry[row["country"]].append(row)
    codes=sorted(bycountry)
    if len(codes)<150:raise ValueError("Insufficient countries for uncertainty")
    rng=random.Random(seed)
    values=[]
    for _ in range(reps):
        summed=0;n=0
        for _ in codes:
            code=rng.choice(codes)
            for row in bycountry[code]:
                summed+=(row["model"]-row["outcome"])**2-(row[comp]-row["outcome"])**2
                n+=1
        values.append(summed/n)
    values.sort()
    return [values[int(.025*(reps-1))],values[int(.975*(reps-1))]]

def run(src):
    older,latest=src[ORIGIN_VERSION],src[TARGET_VERSION]
    rows,folds,training=predict(older,latest)
    if len(rows)<380:raise ValueError("Incomplete post-release onset2 holdout")
    out={
       "schema":"idealab.psico.onset2_homogeneous_231_to_251.v1",
       "study_id":"EMP-GEO-ONSET2-231-251-HOMOGENEOUS-20261110",
       "status":"EX_POST_HOMOGENEOUS_CROSS_RELEASE_NOT_PROSPECTIVE",
       "question":"Q-GEO-01: intrastate country onset2; NOT 25 deaths state-based threshold",
       "source_vintages":{
          ver:{"url":SOURCES[ver]["url"],"sha256":SOURCES[ver]["sha256"],
               "last_year":SOURCES[ver]["last_year"]}
          for ver in (ORIGIN_VERSION,TARGET_VERSION)
       },
       "training":training,
       "years":[],
       "n":len(rows),
       "events":sum(r["outcome"] for r in rows),
       "model_vs_baselines":{key:score(rows,key) for key in
           ("model","global","recent_global","no_onset")},
       "ranking_pooled":ranking(rows),
       "bootstrap_country_95pct_delta_brier":{
           comp:bootstrap(rows,comp) for comp in ("global","recent_global","no_onset")
       },
       "historical_revisions":compare_revisions(older,latest,CUTOFF),
       "historical_forecasts_issued":False,
       "independent_release_timestamp_proof":False,
       "forecast_2027_changed":False,
       "actual_2027_results":0,
       "skill_demonstrated_prospectively":False,
       "legacy_19_1_included":False,
       "caution":"The 19.1 edition is deliberately excluded because of duplicate country-years and potentially different analytical unit. 23.1/25.1 is a consistent country-level onset2 family, but 23.1 was not issued before the end of 2022. Two tested outcomes and few onset events do not certify predictive skill, even if ranking or Brier were favorable. Study reconstructed ex post in 2026; no issued historical forecasts. Country bootstrap omits common year shocks.",
    }
    for fold in folds:
        annual=[r for r in rows if r["target_year"]==fold["year"]]
        out["years"].append({**fold,
           "scores":{key:score(annual,key) for key in ("model","global","recent_global","no_onset")},
           "ranking":ranking(annual)})
    m=out["model_vs_baselines"]
    out["brier_skill_vs_global"]=1-m["model"]["brier"]/m["global"]["brier"]
    out["brier_skill_vs_recent_global"]=1-m["model"]["brier"]/m["recent_global"]["brier"]
    out["brier_skill_vs_no_onset"]=1-m["model"]["brier"]/m["no_onset"]["brier"]
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--check-report")
    args=p.parse_args()
    result=run(load_homogeneous_sources())
    payload=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if args.check_report and Path(args.check_report).read_bytes()!=payload.encode():
        raise ValueError("Onset2 homogeneous report differs from pinned official sources")
    print("HOMOGENEOUS_ONSET2_EVIDENCE_BEGIN")
    print(payload,end="")
    print("HOMOGENEOUS_ONSET2_EVIDENCE_END")
    print("HOMOGENEOUS_ONSET2_COMPLETE",result["n"],result["events"],
          "prospective_results",result["actual_2027_results"])

if __name__=="__main__":main()
