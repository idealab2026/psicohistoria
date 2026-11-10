#!/usr/bin/env python3
"""UCDP Onset2: does real intrastate conflict incidence add predictive value?

EXPLORATORY EX-POST ABLATION. 23.1 official UCDP/PRIO Armed Conflict Dataset
is conflict-year, not country-year; aggregate type 3 and 4 rows by singleton
gwno_a before joining the separate UCDP onset country-year series.

Model uses ONLY both 23.1 source editions (ACD + Onset) for origins, features
and historical training. 25.1 onset labels 2023/24 are evaluation only; a
25.1 ACD source is used EXCLUSIVELY for aggregate revision diagnostics.
Never allow revisions or future conflict incidence to affect any forecasts.

This is not a country-level released forecast or prospectively verified
war onset prediction. Existing GEO-2027 country probabilities remain intact.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path
from experiment_onset2_lagged_signals import (
    load_panel,_fit,TRAIN_CUTOFFS,EXTERNAL_CUTOFF,HORIZONS,
    START,PRIOR_STRENGTH,_pooled_bootstrap
)
from evaluate_homogeneous_onset2 import score,ranking
from probe_ucdp_prio_incidence import (
    SOURCES,PINNED_SHA,MAX_ZIP,source_zip,parse_country_code,ALLOWED_TYPES
)
from inspect_ucdp_archives import fetch

CANDIDATES=(
    "global_recent5","global_h","country_eb","lag1_country",
    "active_global","active_country","recent3_country"
)
SEED=20261110
BOOTSTRAPS=2000

def load_activity(version,fetcher=fetch):
    if version not in SOURCES:
        raise ValueError("Unapproved armed-conflict vintage")
    blob=fetcher(SOURCES[version],MAX_ZIP)
    if hashlib.sha256(blob).hexdigest()!=PINNED_SHA[version]:
        raise ValueError("UCDP/PRIO conflict-year original vintage hash changed")
    rows,header=source_zip(blob)
    active=set()
    conflict_ids=set()
    for row in rows:
        if row["type_of_conflict"].strip() not in ALLOWED_TYPES:
            continue
        cid=parse_country_code(row["gwno_a"])
        loc=parse_country_code(row["gwno_loc"])
        if cid is None or loc!=cid:
            raise ValueError("Intrastate conflict not safely mapped to singleton government country")
        year=int(row["year"])
        if year<1946 or year>({"23.1":2022,"25.1":2024}[version]):
            raise ValueError("Invalid original UCDP country-year coverage")
        conflict=row["conflict_id"].strip()
        if not conflict.isdigit():
            raise ValueError("Official conflict ID not numeric")
        key=(cid,year,conflict)
        if key in conflict_ids:
            raise ValueError("Repeated original conflict-year prevents safe counting")
        conflict_ids.add(key)
        active.add((cid,year))
    if len(active)<1500 or max(y for _,y in active)!=({"23.1":2022,"25.1":2024}[version]):
        raise ValueError("Intrastate conflict country-years unexpectedly missing")
    return active,{
        "edition":version,"url":SOURCES[version],
        "sha256":PINNED_SHA[version],
        "raw_conflict_year_rows":len(rows),
        "intrastate_conflict_year_rows":len(conflict_ids),
        "country_years_with_intrastate_conflict":len(active),
        "latest_year":max(y for _,y in active)
    }

def _group_prior(panel,active,cutoff,horizon,cohort):
    """Two fixed features derived only from year t or earlier in source 23.1."""
    if cutoff<2014 or horizon not in HORIZONS:
        raise ValueError("Origin/horizon outside fixed training protocol")
    if max(y for _,y in active)!=2022:
        raise ValueError("Only vintage 23.1 incidence is permitted in feature fit")
    if max(max(h) for h in panel.values())!=2022:
        raise ValueError("Only source 23.1 onset panel permitted in feature fit")
    pred,base_info=_fit(panel,cutoff,horizon,cohort)
    counts={"active":defaultdict(lambda:[0,0]),
            "active3":defaultdict(lambda:[0,0])}
    for cid,h in panel.items():
        for y,(_,_) in h.items():
            if START<=y and y+horizon<=cutoff and y+horizon in h:
                outcome=h[y+horizon][1]
                now=int((cid,y) in active)
                trailing=int(any((cid,y-k) in active for k in range(3)))
                for field,val in (("active",now),("active3",trailing)):
                    counts[field][val][0]+=outcome
                    counts[field][val][1]+=1
    global_p=base_info["global_rate"]
    if sum(v[1] for v in counts["active"].values()) != base_info["historical_origin_target_pairs"]:
        raise ValueError("Historical training pairs differ from frozen baseline")
    probabilities={}
    for field in ("active","active3"):
        probabilities[field]={
            g:(counts[field][g][0]+PRIOR_STRENGTH*global_p)/
              (counts[field][g][1]+PRIOR_STRENGTH)
            for g in (0,1)
        }
    for cid in cohort:
        h=panel[cid]
        if cutoff not in h:raise ValueError("Missing original country-year origin")
        now=int((cid,cutoff) in active)
        prior3=int(any((cid,cutoff-k) in active for k in range(3)))
        total=sum(1 for y in h if START<=y<=cutoff)
        events=sum(v[1] for y,v in h.items() if START<=y<=cutoff)
        pred[cid]["active_global"]=probabilities["active"][now]
        pred[cid]["active_country"]=(events+PRIOR_STRENGTH*probabilities["active"][now])/(total+PRIOR_STRENGTH)
        pred[cid]["recent3_country"]=(events+PRIOR_STRENGTH*probabilities["active3"][prior3])/(total+PRIOR_STRENGTH)
        if not all(0<p<1 for p in pred[cid].values()):
            raise ValueError("Unsafe likelihood outside probability domain")
    info={
      "cutoff":cutoff,"horizon":horizon,
      "latest_feature_year":cutoff,
      "latest_training_target_year":cutoff,
      "conflict_activity_source":"UCDP/PRIO 23.1",
      "conflict_year_aggregation":"type 3/4, singleton gwno_a, any active conflict in country-year",
      "active_prior_counts":{
          str(g):{"n":counts["active"][g][1],"onsets":counts["active"][g][0],
                  "prior":probabilities["active"][g]} for g in (0,1)
      },
      "trailing3_prior_counts":{
          str(g):{"n":counts["active3"][g][1],"onsets":counts["active3"][g][0],
                  "prior":probabilities["active3"][g]} for g in (0,1)
      },
      "future_incidence_used":False,
      "future_onset2_outcomes_used":False
    }
    return pred,info

def evaluate_origin(onset,truth,activity,cutoff):
    cohort=sorted(cid for cid,h in onset.items() if cutoff in h)
    if len(cohort)!=196:
        raise ValueError("Historical country universe changed")
    folds=[]
    observations=[]
    for horizon in HORIZONS:
        target=cutoff+horizon
        predictions,details=_group_prior(onset,activity,cutoff,horizon,cohort)
        rows=[]
        for cid in cohort:
            if target not in truth.get(cid,{}):continue
            rows.append({
                "country":cid,"origin":cutoff,"target":target,"horizon":horizon,
                "outcome":truth[cid][target][1],
                "active_at_origin":int((cid,cutoff) in activity),
                **predictions[cid]
            })
        if len(rows)<190:raise ValueError("Unresolved target countries cannot be converted to no onset")
        folds.append({
            "origin":cutoff,"target":target,"horizon":horizon,
            "n":len(rows),"events":sum(v["outcome"] for v in rows),
            "origin_active_n":sum(v["active_at_origin"] for v in rows),
            "onset2_events_among_origin_active":
                sum(v["outcome"] for v in rows if v["active_at_origin"]),
            "fit":details,
            "scores":{key:score(rows,key) for key in CANDIDATES},
            "ranking_active_country":ranking([
                {"country":v["country"],"outcome":v["outcome"],"model":v["active_country"]}
                for v in rows
            ])
        })
        observations.extend(rows)
    return observations,folds

def uncertainty(rows,competitor,challenger="active_country"):
    # Use the same country-block bootstrap as the existing lag ablation;
    # repeated historical origin/target combinations share outcomes and
    # yearly macro shocks are not resampled, so CI is descriptive only.
    return _pooled_bootstrap(rows,competitor,challenger=challenger,
                             draws=BOOTSTRAPS,seed=SEED)

def summary(rows,folds):
    distinct={}
    for v in rows:
        key=(v["country"],v["target"])
        if key in distinct and distinct[key]!=v["outcome"]:
            raise ValueError("Conflicting repeated country-year outcomes")
        distinct[key]=v["outcome"]
    return {
        "n_forecast_evaluations":len(rows),
        "positive_forecast_evaluations":sum(v["outcome"] for v in rows),
        "unique_country_year_targets":len(distinct),
        "unique_onset2_positive_targets":sum(distinct.values()),
        "repeated_target_evaluations":len(rows)-len(distinct),
        "scores":{key:score(rows,key) for key in CANDIDATES},
        "delta_brier_ci_country_bootstrap":{
            "active_country_minus_country_eb":uncertainty(rows,"country_eb"),
            "active_country_minus_global_recent5":uncertainty(rows,"global_recent5"),
            "recent3_country_minus_country_eb":uncertainty(rows,"country_eb","recent3_country")
        },
        "folds":folds
    }

def run(onset_old,onset_later,activity_old,activity_later):
    if max(max(h) for h in onset_old.values())!=2022 or \
       max(max(h) for h in onset_later.values())!=2024 or \
       max(y for _,y in activity_old)!=2022 or max(y for _,y in activity_later)!=2024:
        raise ValueError("Official source vintages do not match the frozen protocol")
    inside=[];inside_folds=[]
    for cutoff in TRAIN_CUTOFFS:
        rows,folds=evaluate_origin(onset_old,onset_old,activity_old,cutoff)
        inside.extend(rows);inside_folds.extend(folds)
    outside,outside_folds=evaluate_origin(onset_old,onset_later,activity_old,EXTERNAL_CUTOFF)
    shared={v for v in activity_old if v[1]<=2022}
    newer={v for v in activity_later if v[1]<=2022}
    shared_common_codes={cid for cid,_ in shared}&{cid for cid,_ in newer}
    revised_additions=len(newer-shared)
    revised_removals=len(shared-newer)
    internal=summary(inside,inside_folds)
    external=summary(outside,outside_folds)
    if internal["unique_country_year_targets"]!=1568 or \
       external["n_forecast_evaluations"]!=392 or \
       external["positive_forecast_evaluations"]!=2:
        raise ValueError("Incompatible onset2 country-year evaluation universe")
    return {
       "schema":"idealab.psico.ucdp_prio_activity_onset2_ablation.v1",
       "status":"EXPLORATORY_EX_POST_NO_PROSPECTIVE_CLAIMS",
       "question":"Does active intrastate conflict by origin predict country-level UCDP onset2?",
       "target_is_onset2_not_threshold_entry":True,
       "source_families":{
          "acd":["23.1","25.1"],
          "country_onset":["23.1","25.1"]
       },
       "model_definitions":{
          "global_recent5":"Origin-frozen global rate, target years in the five most recent eligible historical years",
          "global_h":"Origin-frozen overall global rate for target horizon",
          "country_eb":"Country onset2 history since 2000, shrinkage20 towards global_h",
          "lag1_country":"Country onset2 history shrunk to origin-year onset1-group prior",
          "active_global":"Active intrastate armed conflict in origin year, group conditional rate, shrinkage20 towards global_h",
          "active_country":"Country onset2 history shrunk to active-in-origin group prior20",
          "recent3_country":"Country onset2 history shrunk to any-active-in-past-three-origin-years group prior20"
       },
       "internal":internal,"external":external,
       "historical_conflict_incidence_revision_diagnostic":{
          "old_23_1_unique_active_country_years":len(activity_old),
          "new_25_1_active_country_years_through_2022":len(newer),
          "added_in_later_vintage_through_2022":revised_additions,
          "removed_in_later_vintage_through_2022":revised_removals,
          "historical_label_revisions_used_for_model_fitting":False
       },
       "predefined_original_cutoffs":list(TRAIN_CUTOFFS),
       "external_origin_year":EXTERNAL_CUTOFF,
       "horizons":list(HORIZONS),
       "model_grid_chosen_after_prior_2023_2024_outcomes_inspected":True,
       "old_acd_conflict_year_collapsed_to_country_year":True,
       "unit_semantics":"ACD conflict-year type 3/4 -> singleton gwno_a country-year; onset2 target separately country-year. A country may have active conflicts AND a new onset of another conflict.",
       "original_editions_independently_time_notarized":False,
       "real_historically_issued_forecasts":False,
       "real_2027_country_forecast_modified":False,
       "actual_2027_outcomes_resolved":0,
       "certified_predictive_skill":False,
       "risk_conclusion":"Post-hoc hypothesis test on two previously inspected external onset2 positives; results must not be called independent validation. Internal repeated origin/horizon evaluations share country-year targets and newer edition revises historical incidence. Country-bootstrap does not model global shocks. Pre-registered original GEO-2027 probabilities are not modified."
    }

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--check-report")
    args=arg.parse_args()
    o,metadata1=load_panel("23.1")
    later,metadata2=load_panel("25.1")
    a,ma=load_activity("23.1")
    later_a,mb=load_activity("25.1")
    result=run(o,later,a,later_a)
    result["source_provenance"]={
        "onset23_sha256":metadata1["sha256"],
        "onset25_sha256":metadata2["sha256"],
        "acd23":ma,
        "acd25":mb
    }
    text=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    print("ONSET2_CONFLICT_INCIDENCE_BEGIN")
    print(text,end="")
    print("ONSET2_CONFLICT_INCIDENCE_END")
    if args.check_report and Path(args.check_report).read_text(encoding="utf8")!=text:
        raise ValueError("Published conflict incidence diagnostic differs from verified official source reproduction")
    print("ONSET2_CONFLICT_INCIDENCE_OK",result["internal"]["unique_country_year_targets"],
          result["external"]["n_forecast_evaluations"],
          "future_results",result["actual_2027_outcomes_resolved"])

if __name__=="__main__":
    main()
