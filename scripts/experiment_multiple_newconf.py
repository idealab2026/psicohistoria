#!/usr/bin/env python3
"""Q-GEO-01 / newconf: forecast NEW conflict appearance at country-year level.

This is NOT UCDP Country-Level Onset onset2. Labels are aggregated to
ANY(newconf=1) by (country,year) from the official multiple-onset variant
(V3), whose rows may represent several conflict episodes in one country-year.

Historical design: model origin is UCDP 23.1 Multiple Onset and UCDP/PRIO ACD
23.1. External labels are UCDP Multiple Onset 25.1 for 2023 and 2024 ONLY.
The 25.1 sources never influence fitting, feature engineering, eligible
countries or the candidate grid. All countries of origin are eligible,
including countries with ongoing intrastate conflict: unlike V2 Country Onset.

Post-hoc exploratory: 2023/2024 already examined in preceding experiments,
and this target was defined after those results. It is NOT independent
confirmatory testing or evidence of prospectively issued forecasts.
No country names, identifiers, individual forecasts or labels are printed.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

from probe_multiple_onset_vintages import PINNED,scan,MAX_CSV,fetch,digest
from experiment_onset2_conflict_incidence import load_activity
from evaluate_2027_new_entries import average_precision,roc_auc

TRAIN_START=2000
ROLLING_ORIGINS=tuple(range(2014,2021))
EXTERNAL_ORIGIN=2022
HORIZONS=(1,2)
PRIOR=20
EPS=1e-12
CANDIDATES=("global_full","global_last5","country_eb","activity_global","activity_country","no_newconf")
TOP_K=(5,10,20)
BOOTSTRAP_N=1000
BOOTSTRAP_SEED=20261111

def load_multiple(version,fetcher=fetch):
    if version not in PINNED:
        raise ValueError("Unapproved official UCDP Multiple Onset version")
    src=PINNED[version]
    blob=fetcher(src["url"],MAX_CSV)
    if digest(blob)!=src["sha256"]:
        raise ValueError("Official country multiple-onset file SHA-256 changed")
    rows,meta=scan(blob,src["last_year"])
    return {cid:{} for _,cid in rows} | _to_panel(rows),meta

def _to_panel(groups):
    panel=defaultdict(dict)
    for (year,cid),record in groups.items():
        panel[cid][year]={
          "newconf":int(record["new_conflict_episode_count"]>0),
          "onset2":int(record["onset2_episode_count"]>0),
          "newconf_episodes":record["new_conflict_episode_count"],
          "onset2_episodes":record["onset2_episode_count"],
          "multiple_episode_rows":record["rows"]
        }
    return dict(panel)

def _history(panel,activity,cutoff,horizon,universe):
    if cutoff<2014 or horizon not in HORIZONS or len(universe)!=196:
        raise ValueError("Unapproved country multiple-onset training origin")
    if max(max(h) for h in panel.values())!=2022 or max(y for _,y in activity)!=2022:
        raise ValueError("Only 23.1 Multiple Onset and 23.1 conflict activity may train")
    events=[]
    last5=[]
    countries=defaultdict(lambda:[0,0])
    for cid,hist in panel.items():
        for y,flags in hist.items():
            if TRAIN_START<=y<=cutoff:
                val=flags["newconf"]
                events.append(val)
                countries[cid][0]+=val
                countries[cid][1]+=1
                if cutoff-4<=y<=cutoff:
                    last5.append(val)
    if len(events)<2000 or len(last5)<850:
        raise ValueError("Not enough frozen historical data")
    global_full=(sum(events)+1)/(len(events)+2)
    global_last5=(sum(last5)+1)/(len(last5)+2)
    paired=defaultdict(lambda:[0,0])
    for cid,hist in panel.items():
        for origin in hist:
            target=origin+horizon
            if TRAIN_START<=origin and target<=cutoff and target in hist:
                group=int((cid,origin) in activity)
                paired[group][0]+=hist[target]["newconf"]
                paired[group][1]+=1
    if sum(paired[g][1] for g in (0,1))<2000 or min(paired[g][1] for g in (0,1))<200:
        raise ValueError("Historical risk groups have inadequate exposure")
    priors={
      group:(paired[group][0]+PRIOR*global_full)/(paired[group][1]+PRIOR)
      for group in (0,1)
    }
    estimates={}
    for cid in sorted(universe):
        if cutoff not in panel.get(cid,{}):
            raise ValueError("No origin record: cannot silently count as inactive")
        history=countries[cid]
        is_active=int((cid,cutoff) in activity)
        estimates[cid]={
          "global_full":global_full,
          "global_last5":global_last5,
          "country_eb":(history[0]+PRIOR*global_full)/(history[1]+PRIOR),
          "activity_global":priors[is_active],
          "activity_country":(history[0]+PRIOR*priors[is_active])/(history[1]+PRIOR),
          "no_newconf":0.0
        }
        if not all(0<value<1 for k,value in estimates[cid].items() if k!="no_newconf"):
            raise ValueError("Improper estimated occurrence probability")
    fit={
      "cutoff":cutoff,
      "horizon":horizon,
      "training_onsets":sum(events),
      "training_country_years":len(events),
      "training_recent5_positives":sum(last5),
      "training_recent5_n":len(last5),
      "training_paired_group_inactive_n":paired[0][1],
      "training_paired_group_inactive_positive":paired[0][0],
      "training_paired_group_active_n":paired[1][1],
      "training_paired_group_active_positive":paired[1][0],
      "prior_strength":PRIOR,
      "latest_training_year":cutoff,
      "later_release_activity_used":False,
      "later_release_labels_used_in_fit":False,
    }
    return estimates,fit

def metrics(rows,key):
    if not rows:
        raise ValueError("No evaluation rows")
    brier=sum((x[key]-x["outcome"])**2 for x in rows)/len(rows)
    if key=="no_newconf":
        return {"brier":brier,"logloss":None}
    logloss=-sum(x["outcome"]*math.log(max(EPS,x[key]))+
                 (1-x["outcome"])*math.log1p(-min(1-EPS,x[key]))
                 for x in rows)/len(rows)
    return {"brier":brier,"logloss":logloss}

def ranking(rows,key):
    if not rows or len(rows)<max(TOP_K):
        raise ValueError("Too few countries to rank")
    scored=sorted(rows,key=lambda r:(-r[key],r["country"]))
    positives=sum(r["outcome"] for r in rows)
    return {
      "n":len(rows),"positive_country_years":positives,
      "base_rate":positives/len(rows),
      "average_precision":average_precision(rows,key),
      "roc_auc":roc_auc(rows,key),
      "alert_budgets":{
        str(k):{
          "budget":k,
          "hits":sum(row["outcome"] for row in scored[:k]),
          "precision":sum(row["outcome"] for row in scored[:k])/k,
          "recall":sum(row["outcome"] for row in scored[:k])/positives if positives else None,
          "random_expected_hits":k*positives/len(rows),
          "tie_at_boundary":scored[k-1][key]==scored[k][key]
        } for k in TOP_K
      }
    }

def fold(origin,truth,activity,cutoff,horizon):
    universe={cid for cid,hist in origin.items() if cutoff in hist}
    if len(universe)!=196:
        raise ValueError("Pinned 196-country origin cohort unexpectedly changed")
    forecasts,fit=_history(origin,activity,cutoff,horizon,universe)
    target=cutoff+horizon
    rows=[]
    for cid in sorted(universe):
        record=truth.get(cid,{}).get(target)
        if record is None:continue
        rows.append({
            "country":cid,"target_year":target,"origin_year":cutoff,
            "horizon":horizon,"active_at_origin":int((cid,cutoff) in activity),
            "outcome":record["newconf"],
            "onset2_other_target":record["onset2"],
            "episode_events":record["newconf_episodes"],
            **forecasts[cid],
        })
    if len(rows)<190:
        raise ValueError("Missing target countries may not be mapped to zero")
    positives=sum(x["outcome"] for x in rows)
    return rows,{
       "origin_year":cutoff,
       "target_year":target,
       "horizon":horizon,
       "n":len(rows),
       "positive_country_years":positives,
       "new_conflict_episode_rows":sum(x["episode_events"] for x in rows),
       "origin_active_n":sum(x["active_at_origin"] for x in rows),
       "newconf_positive_origin_active":sum(x["outcome"] for x in rows if x["active_at_origin"]),
       "onset2_positive":sum(x["onset2_other_target"] for x in rows),
       "newconf_positive_without_onset2":sum(
           x["outcome"] and not x["onset2_other_target"] for x in rows),
       "scores":{key:metrics(rows,key) for key in CANDIDATES},
       "rank_country_eb":ranking(rows,"country_eb"),
       "rank_activity_country":ranking(rows,"activity_country"),
       "fit":fit,
    }

def ci(rows,competitor="global_last5",candidate="activity_country",n=BOOTSTRAP_N):
    by_country=defaultdict(list)
    for row in rows:by_country[row["country"]].append(row)
    codes=sorted(by_country)
    if len(codes)!=196:raise ValueError("CI origin universe not complete")
    rng=random.Random(BOOTSTRAP_SEED)
    samples=[]
    for _ in range(n):
        total=0;count=0
        for _ in codes:
            key=rng.choice(codes)
            for record in by_country[key]:
                total+=(record[candidate]-record["outcome"])**2-(record[competitor]-record["outcome"])**2
                count+=1
        samples.append(total/count)
    samples.sort()
    return [samples[int(.025*(n-1))],samples[int(.975*(n-1))]]

def summarize(rows,folds,with_ci=True):
    distinct={}
    for row in rows:
        k=(row["country"],row["target_year"])
        if k in distinct and distinct[k]!=row["outcome"]:
            raise ValueError("Repeated historical target has contradictory labels")
        distinct[k]=row["outcome"]
    return {
        "forecast_evaluations":len(rows),
        "positive_forecast_evaluations":sum(x["outcome"] for x in rows),
        "unique_country_years":len(distinct),
        "unique_positive_country_years":sum(distinct.values()),
        "overlapping_forecasts":len(rows)-len(distinct),
        "scores":{key:metrics(rows,key) for key in CANDIDATES},
        "bootstrap_country_delta_activity_minus_last5":ci(rows) if with_ci else None,
        "folds":folds
    }

def evaluate(old,later,activity):
    if max(max(x) for x in old.values())!=2022 or max(max(x) for x in later.values())!=2024:
        raise ValueError("Country Multiple Onset editions incompatible with historical cutoff")
    if max(y for _,y in activity)!=2022:
        raise ValueError("Only UCDP/PRIO 23.1 may form the activity feature")
    historical=[];hf=[]
    for cutoff in ROLLING_ORIGINS:
        for h in HORIZONS:
            part,details=fold(old,old,activity,cutoff,h)
            historical.extend(part);hf.append(details)
    latest=[];ef=[]
    for h in HORIZONS:
        part,details=fold(old,later,activity,EXTERNAL_ORIGIN,h)
        latest.extend(part);ef.append(details)
    hsum=summarize(historical,hf)
    esum=summarize(latest,ef)
    if hsum["unique_country_years"]!=1568 or esum["forecast_evaluations"]!=392:
        raise ValueError("Historic origin panel unexpectedly altered")
    if esum["positive_forecast_evaluations"]!=3:
        raise ValueError("Official observed new conflict labels changed; do not silently update a model")
    return {
      "schema":"idealab.psico.country_multiple_newconf_v231_v251_exploratory.v1",
      "study_id":"EMP-QGEO01-MULTIPLE-NEWCONF-20261111",
      "status":"POST_HOC_SOURCE_SEPARATED_NO_CONFIRMATORY_OR_PROSPECTIVE_SKILL",
      "target":"ANY(newconf=1) per country-year in UCDP Intrastate Country Level Multiple Onset",
      "separate_comparator_target":"Country Level Onset onset2; must NOT treat as identical",
      "source_multiple_onset_sha256":{v:PINNED[v]["sha256"] for v in PINNED},
      "source_activity_version":"UCDP/PRIO Armed Conflict Dataset 23.1 ONLY",
      "conflict_activity_origin_has_no_future_years":True,
      "rolling_internal_origin_years":list(ROLLING_ORIGINS),
      "external_origin_year":EXTERNAL_ORIGIN,
      "target_years":[2023,2024],
      "horizons":[1,2],
      "models":{
         "global_full":"smoothed prevalence of ANY(newconf) up to cutoff",
         "global_last5":"smoothed prevalence of ANY(newconf) in last five known years",
         "country_eb":"country historical ANY(newconf), regularized 20 to global_full",
         "activity_global":"group-specific future newconf probability conditioned on current active conflict at origin",
         "activity_country":"country rate regularized 20 to origin-activity group prior",
         "no_newconf":"zero-event Brier reference, log-loss undefined when positives exist"
      },
      "internal":hsum,
      "external":esum,
      "country_year_rows_are_unique_after_aggregating_episode_rows":True,
      "active_countries_eligible_for_newconf":True,
      "riskset_does_not_require_two_prior_conflict_free_years":True,
      "hypothesis_defined_after_external_outcomes_seen":True,
      "historical_pseudo_origins_use_revised_single_edition":True,
      "original_2027_prospective_country_risk_probabilities_changed":False,
      "2027_outcomes_evaluated":0,
      "predictive_skill_demonstrated":False,
      "limitations":"Retrospective exploratory exercise with only three 2023/24 newconf-positive country-years. Models were specified after the holdout was inspected. Newconf is not onset2 and not a count of all ongoing wars; episode-level duplicates are collapsed to country-year ANY labels for the classifier while episode counts are reported separately. Internal rolling origin-target assessments overlap. Country-block bootstrap does not model shared time shocks. No historical time-stamped issuance or independent prospective validation."
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report")
    args=ap.parse_args()
    old,meta23=load_multiple("23.1")
    newer,meta25=load_multiple("25.1")
    acd,meta_acd=load_activity("23.1")
    study=evaluate(old,newer,acd)
    study["source_metadata"]={
       "multiple_23_1":{key:meta23[key] for key in ("episode_rows","unique_country_years","duplicate_country_year_keys","total_newconf_episode_rows")},
       "multiple_25_1":{key:meta25[key] for key in ("episode_rows","unique_country_years","duplicate_country_year_keys","total_newconf_episode_rows")},
       "acd_23_sha256":meta_acd["sha256"]
    }
    content=json.dumps(study,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    print("MULTIPLE_NEWCONF_EVALUATION_BEGIN")
    print(content,end="")
    print("MULTIPLE_NEWCONF_EVALUATION_END")
    if args.check_report and Path(args.check_report).read_bytes()!=content.encode("utf8"):
        raise ValueError("Multiple-onset newconf evaluation fails official source reproduction")

if __name__=="__main__":
    main()
