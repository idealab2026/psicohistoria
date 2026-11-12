#!/usr/bin/env python3
"""Ex-post 2-year intrastate ACD CONFLICT PRESENCE persistence backtest.

Question: among countries WITH an intrastate armed conflict recorded in
the origin edition at year t, was ANY intrastate conflict recorded in t+2
by a SEPARATE target edition? Four old origin/target edition pairs.
No inactive-world-country denominator is invented. The outcome is NOT UCDP
OrganizedViolenceCY GEO2027's >=25 state-based death threshold, not peace,
not NEWCONF onset. Model choices are exploratory, no historic issue notarized.

This exploratory line never modifies any original prospective 2027 forecast.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

from inspect_ucdp_archives import fetch
from probe_ucdp_prio_incidence import (
    ALLOWED_TYPES,MAX_ZIP,source_zip,parse_country_code,
)
from diagnose_ucdp_prio_older_vintages import HISTORICAL, parse_version
from prepare_geo2027_transition_alerts import (
    FORECAST_PATH, SOURCE_SHA256, sha,
)
from evaluate_geo2027_calibrated_shadow_official import load_authenticated

SOURCE_241={
    "url":"https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-241-csv.zip",
    "sha256":None,
    "last_year":2023,
}
PAIRS=(
    ("20.1","22.1",2019,2021),
    ("21.1","23.1",2020,2022),
    ("22.1","24.1",2021,2023),
    ("23.1","25.1",2022,2024),
)
START=1990
HORIZON=2
RECENT_ORIGIN_YEARS=5
PRIOR_STRENGTH=12.0
REPORT=Path("data/ucdp-prio-2021-2024-retention-four-vintage.json")


def load_241(raw,*,allow_probe=False):
    checksum=hashlib.sha256(raw).hexdigest()
    if SOURCE_241["sha256"] is None and not allow_probe:
        raise ValueError("UCDP/PRIO 24.1 must be SHA-pinned before scoring")
    if SOURCE_241["sha256"] is not None and checksum!=SOURCE_241["sha256"]:
        raise ValueError("UCDP/PRIO 24.1 official SHA-256 changed")
    table,fields=source_zip(raw)
    active=set()
    seen=set()
    for row in table:
        year_raw=row["year"].strip()
        if not year_raw.isdigit():
            raise ValueError("Invalid ACD 24.1 year")
        year=int(year_raw)
        if not 1946<=year<=2023:
            raise ValueError("UCDP 24.1 contains future or pre-1946 conflicts")
        if row["type_of_conflict"].strip() not in ALLOWED_TYPES:
            continue
        cid=parse_country_code(row["gwno_a"])
        loc=parse_country_code(row["gwno_loc"])
        if cid is None or cid!=loc:
            raise ValueError("UCDP 24.1 has ambiguous government location")
        conflict_id=row["conflict_id"].strip()
        if not conflict_id.isdigit():
            raise ValueError("UCDP 24.1 conflict ID invalid")
        key=(cid,year,conflict_id)
        if key in seen:
            raise ValueError("Duplicated UCDP/PRIO conflict-year in 24.1")
        seen.add(key)
        active.add((cid,year))
    if (len(table)<2000 or len(active)<1600 or
        len({cid for cid,_ in active})<95 or
        not any(y==2023 for _,y in active)):
        raise ValueError("UCDP 24.1 official ACD country-year coverage incomplete")
    return active,{
        "official_url":SOURCE_241["url"],
        "original_zip_sha256":checksum,
        "sha256_pinned_before_run":SOURCE_241["sha256"] is not None,
        "raw_conflict_year_records":len(table),
        "unique_intrastate_conflict_year_records":len(seen),
        "unique_active_intrastate_country_years":len(active),
        "last_year":2023,
    }


def clipped(p):
    if not math.isfinite(p) or not 0<p<1:
        raise ValueError("Historical forecast probability invalid")
    return p


def train_origin(active,cutoff):
    """Only country-year history with observed target <= cutoff can train."""
    if cutoff not in (2019,2020,2021,2022):
        raise ValueError("Unapproved historical origin year")
    training=[]
    for cid,y in sorted(active):
        if START<=y<=cutoff-HORIZON:
            training.append((cid,y,int((cid,y+HORIZON) in active),
                             int((cid,y-1) in active)))
    if len(training)<250 or len({cid for cid,_,_,_ in training})<35:
        raise ValueError("Insufficient origin-only training exposure")
    successes=sum(row[2] for row in training)
    if not 0<successes<len(training):
        raise ValueError("Original ACD origin-only training single-class")
    global_rate=(successes+.5)/(len(training)+1)
    recent=[row for row in training
            if row[1]>=cutoff-HORIZON-RECENT_ORIGIN_YEARS+1]
    if len(recent)<50:
        raise ValueError("Recent original ACD year rows unexpectedly absent")
    recent_rate=(sum(row[2] for row in recent)+.5)/(len(recent)+1)
    country_counts=defaultdict(lambda:[0,0])
    recent_status=defaultdict(lambda:[0,0])
    for cid,y,target,prior_active in training:
        country_counts[cid][0]+=target
        country_counts[cid][1]+=1
        recent_status[prior_active][0]+=target
        recent_status[prior_active][1]+=1
    return {
        "n_training_origin_target_country_pairs":len(training),
        "n_training_2year_persistent":successes,
        "latest_training_target_year":max(y+HORIZON for _,y,_,_ in training),
        "origin_max_year":cutoff,
        "global_rate":clipped(global_rate),
        "global_recent5_rate":clipped(recent_rate),
        "country_counts":country_counts,
        "last_year_status_counts":recent_status,
    }


def predict(active,origin):
    fit=train_origin(active,origin)
    cohort=sorted(cid for cid,y in active if y==origin)
    if not 20<=len(cohort)<=75:
        raise ValueError("Origin active country cohort is unexpectedly sparse")
    results={}
    for cid in cohort:
        hits,n=fit["country_counts"][cid]
        flag=int((cid,origin-1) in active)
        h,nflag=fit["last_year_status_counts"][flag]
        results[cid]={
            "p_global_recent5":fit["global_recent5_rate"],
            "p_country_eb":clipped(
                (hits+PRIOR_STRENGTH*fit["global_rate"])/
                (n+PRIOR_STRENGTH)),
            "p_lag1_group":clipped(
                (h+PRIOR_STRENGTH*fit["global_rate"])/
                (nflag+PRIOR_STRENGTH)),
        }
    return results,{
        "n_origin_country_risk_set":len(cohort),
        "n_training_origin_target_country_pairs":fit[
            "n_training_origin_target_country_pairs"],
        "n_training_2year_persistent":fit["n_training_2year_persistent"],
        "origin_max_year":origin,
        "latest_training_target_year":fit["latest_training_target_year"],
        "prior_strength_country_and_lag1_group":PRIOR_STRENGTH,
        "recent_global_training_origin_years":RECENT_ORIGIN_YEARS,
        "future_labels_used_in_training":False,
    }


def compare_pair(origin_active,target_active,origin_year,target_year):
    if target_year!=origin_year+HORIZON:
        raise ValueError("ACD target horizon changed")
    predictions,fit=predict(origin_active,origin_year)
    first_target_codes={cid for cid,_ in target_active}
    unresolved=[cid for cid in predictions if cid not in first_target_codes]
    if unresolved:
        raise ValueError("Origin country has no historical code presence in target ACD edition")
    outcomes={cid:int((cid,target_year) in target_active) for cid in predictions}
    n=len(outcomes);k=sum(outcomes.values())
    models={}
    for name in ("p_global_recent5","p_country_eb","p_lag1_group"):
        ps=[predictions[cid][name] for cid in sorted(outcomes)]
        ys=[outcomes[cid] for cid in sorted(outcomes)]
        models[name]={
            "n":n,
            "n_persisted_intrastate_country_conflict":k,
            "sum_model_expected_persisted":sum(ps),
            "brier":sum((p-y)**2 for p,y in zip(ps,ys))/n,
            "logloss":-sum(y*math.log(p)+(1-y)*math.log1p(-p)
                          for p,y in zip(ps,ys))/n,
        }
    return {
        "origin_year":origin_year,
        "target_year":target_year,
        "n_origin_active_countries":n,
        "n_target_persistent_country_incidence":k,
        "n_target_no_recorded_intrastate_conflict":n-k,
        "no_negative_countries_outside_origin_active_risk_set_added":True,
        "target_missingness_interpretation":
            "ACD complete global country-conflict year registry; only formerly active countries with recognizable codes included; absence of conflict record is no recorded type3/4 conflict, not peace",
        "origin_training_cutoff":fit,
        "models":models,
        "delta_brier_country_eb_minus_global_recent5":
            models["p_country_eb"]["brier"] -
            models["p_global_recent5"]["brier"],
        "delta_brier_lag1_group_minus_global_recent5":
            models["p_lag1_group"]["brier"] -
            models["p_global_recent5"]["brier"],
    }


def diagnose(active,meta,*,probe=False):
    if set(active)!={"20.1","21.1","22.1","23.1","24.1","25.1"}:
        raise ValueError("All independent origin/target ACD vintages are required")
    for version in active:
        if not active[version] or not meta[version].get("original_zip_sha256"):
            raise ValueError("Historic source not verified")
        if meta[version]["last_year"] != (
            SOURCE_241["last_year"] if version=="24.1"
            else HISTORICAL[version]["last_year"]
        ):
            raise ValueError("Wrong historical cutoff in archived ACD source")
    is_pinned=all(meta[v]["sha256_pinned_before_run"] for v in active)
    if not is_pinned and not probe:
        raise ValueError("Full 4-fold evaluation cannot be certified with unpinned source")
    folds=[]
    for orig,target,origin_year,target_year in PAIRS:
        if not (meta[orig]["last_year"]==origin_year and
                meta[target]["last_year"]==target_year):
            raise ValueError("Source dates cannot be used for requested fold")
        item=compare_pair(active[orig],active[target],origin_year,target_year)
        folds.append({
            "origin_edition":orig,
            "outcome_edition":target,
            **item,
        })
    n=sum(x["n_origin_active_countries"] for x in folds)
    k=sum(x["n_target_persistent_country_incidence"] for x in folds)
    total_models={}
    for name in folds[0]["models"]:
        total_models[name]={
            "n_country_year_fold_evaluations":n,
            "n_persisted":k,
            "expected_persisted":sum(x["models"][name][
                "sum_model_expected_persisted"] for x in folds),
            "pooled_brier":sum(x["models"][name]["brier"]*
                x["n_origin_active_countries"] for x in folds)/n,
            "pooled_logloss":sum(x["models"][name]["logloss"]*
                x["n_origin_active_countries"] for x in folds)/n,
        }
    return {
        "schema":"idealab.psico.ucdp_prio_intrastate_country_persistence_four_source_folds.v1",
        "status":"UNPINNED_EXPLORATORY_PROBE_NOT_CERTIFIED"
            if not is_pinned else "SHA_PINNED_EX_POST_FOUR_ORIGIN_TARGET_VINTAGES",
        "endpoint":"Any UCDP/PRIO ACD intrastate type3/4 conflict recorded for a country in t+2, among countries with such a conflict in year t",
        "not_geo2027_statebased_25_death_threshold":True,
        "not_onset2_or_newconf2027":True,
        "no_training_on_future_target_labels":True,
        "all_sources_sha_pinned":is_pinned,
        "source_sha256_by_version":{v:meta[v]["original_zip_sha256"] for v in sorted(active)},
        "source_archives_last_year":{v:meta[v]["last_year"] for v in sorted(active)},
        "fixed_pre_evaluation_horizon_years":HORIZON,
        "fixed_model_prior_strength":PRIOR_STRENGTH,
        "fixed_origin_fold_years":[x[2] for x in PAIRS],
        "target_years":[x[3] for x in PAIRS],
        "n_country_year_fold_evaluations":n,
        "n_country_year_persistence_positives":k,
        "folds":folds,
        "pooled_models":total_models,
        "historical_predictions_actually_issued_at_origin":False,
        "first_source_publication_dates_independently_notarized":False,
        "four_target_edition_years_distinct":True,
        "selection_after_other_history_seen":True,
        "valid_independent_forecast_claim":False,
        "cross_country_independence_tested":False,
        "2027_outcomes_observed":0,
        "original_geo2027_shadow_newconf_predictions_modified":False,
        "limitations":(
            "Exploratory ex-post reconstruction using historical source-edition "
            "separation, not contemporaneously published predictions. ACD unit "
            "is conflict-year; any intrastate conflict presence at t+2 for a "
            "country active at t, NOT OrganizedViolenceCY >=25 deaths, not "
            "country conflict onset and not a peace definition. Only countries "
            "historically active at origin in archived edition can enter; "
            "no negative controls for never-active countries, no claim of full "
            "196-country country-year denominator. Countries repeat across "
            "folds and geopolitical macro shocks persist. 2023 and 2024 "
            "have distinct 24.1 and 25.1 target editions, but timestamps "
            "are not independently notarized. No new model issued for 2027."
        ),
    }


def load_sources(*,probe=False,fetcher=fetch):
    all_active={};meta={}
    for version in ("20.1","21.1","22.1","23.1","25.1"):
        spec=HISTORICAL[version]
        data=fetcher(spec["url"],MAX_ZIP)
        all_active[version],m=parse_version(data,version)
        meta[version]=m
    raw=fetcher(SOURCE_241["url"],MAX_ZIP)
    all_active["24.1"],meta["24.1"]=load_241(raw,allow_probe=probe)
    return all_active,meta


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--probe",action="store_true",
                   help="Only first official source ZIP hash discovery; no scoring certification")
    p.add_argument("--check-report")
    args=p.parse_args()
    if args.probe and args.check_report:
        raise ValueError("Cannot certify unpinned probe as pinned archive")
    original,shadow,manifest=load_authenticated()
    if (len(original["countries"])!=196 or len(shadow["countries"])!=196
        or shadow["2027_outcomes_resolved"]!=0 or
        sha(FORECAST_PATH.read_bytes())!=SOURCE_SHA256):
        raise ValueError("Existing immutable 2027 original/shadow issue changed")
    versions,meta=load_sources(probe=args.probe)
    result=diagnose(versions,meta,probe=args.probe)
    body=json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n"
    print("ACD_RETENTION_FOUR_VINTAGES_BEGIN")
    print(body,end="")
    print("ACD_RETENTION_FOUR_VINTAGES_END")
    if args.check_report and Path(args.check_report).read_bytes()!=body.encode("utf8"):
        raise ValueError("Pinned ACD retrospective fourfold persistence report changed")


if __name__=="__main__":
    main()
