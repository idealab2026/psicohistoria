#!/usr/bin/env python3
"""IDEA LAB · Q-GEO-01 prospective NEWCONFLICT forecast, target calendar 2027.

Independent of the ALREADY ISSUED statebased GEO-2027 forecast.
Target: ANY(newconf=1) in Intrastate Country Level Multiple Onset by
government country (GW id), not UCDP country-onset2, NOT total deaths.

Origin: ACD 26.1 through 2025, exclusively conflict activity (types 3/4).
Training: Multiple Onset 25.1 NEWCONF 2000-2024 and ACD 25.1 activity
for lag=2 historical pairs. Never infer NEWCONF outcomes 2025 from ACD.
The generator pre-registers a full 196-row probability issue; only a
PUBLIC GIT COMMIT before the event can establish an issued forecast.
2023/2024 have already been inspected and therefore model selection is
exploratory; no independent or proven predictive skill is asserted.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from collections import defaultdict
from experiment_multiple_newconf import load_multiple
from experiment_onset2_conflict_incidence import load_activity
from probe_newconf_2027_acd261 import activity_2025,PINNED_SHA as ACD261_SHA,URL as ACD261_URL
from probe_multiple_onset_vintages import PINNED as MULTI
from probe_ucdp_prio_incidence import PINNED_SHA as ACDHIST,SOURCES as ACDURL

ISSUE_ID="PSICO-QGEO01-NEWCONF2027-ORIGIN2025-V1"
SCHEMA="idealab.psico.prospective_newconf_2027.v1"
TARGET_YEAR=2027
TRAINING_LAST_YEAR=2024
ORIGIN_YEAR=2025
HORIZON=2
TRAIN_START=2000
FIVE_YEARS=(2020,2021,2022,2023,2024)
ALPHA=20
N=196

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def calculate(panel,training_activity,origin_activity):
    if max(max(h) for h in panel.values())!=TRAINING_LAST_YEAR:
        raise ValueError("Future newconf training labels forbidden")
    if max(y for _,y in training_activity)!=2024:
        raise ValueError("Only frozen ACD 25.1 may fit historical activity priors")
    cohort=sorted(cid for cid,h in panel.items() if TRAINING_LAST_YEAR in h)
    if len(cohort)!=N or any(not cid.isdecimal() for cid in cohort):
        raise ValueError("Wrong fixed official 196-country Multiple Onset cohort")
    if not origin_activity.issubset(set(cohort)) or len(origin_activity)!=32:
        raise ValueError("2025 activity includes unmapped countries or changed 2025 origin counts")
    counts=defaultdict(lambda:[0,0])
    global_event=0;global_n=0
    recent_event=0;recent_n=0
    for cid,h in panel.items():
        for year,row in h.items():
            if TRAIN_START<=year<=TRAINING_LAST_YEAR:
                y=row["newconf"]
                if y not in (0,1):raise ValueError("Invalid historical newconf outcome")
                global_event+=y;global_n+=1
                counts[cid][0]+=y;counts[cid][1]+=1
                if year in FIVE_YEARS:
                    recent_event+=y;recent_n+=1
    if global_n<4600 or recent_n<900:
        raise ValueError("Training history unexpectedly incomplete")
    p_global=(global_event+1)/(global_n+2)
    p_recent=(recent_event+1)/(recent_n+2)
    group=defaultdict(lambda:[0,0])
    for cid,h in panel.items():
        for year in h:
            future=year+HORIZON
            if TRAIN_START<=year and future<=TRAINING_LAST_YEAR and future in h:
                state=int((cid,year) in training_activity)
                group[state][0]+=h[future]["newconf"]
                group[state][1]+=1
    if min(group[i][1] for i in (0,1))<200:
        raise ValueError("Not enough eligible training origin-target pairs by activity")
    p_condition={
        i:(group[i][0]+ALPHA*p_global)/(group[i][1]+ALPHA)
        for i in (0,1)
    }
    entries=[]
    for cid in cohort:
        history=counts[cid]
        current=int(cid in origin_activity)
        p_activity=p_condition[current]
        p_country=(history[0]+ALPHA*p_global)/(history[1]+ALPHA)
        p_main=(history[0]+ALPHA*p_activity)/(history[1]+ALPHA)
        vals=[p_main,p_country,p_global,p_recent,p_activity]
        if not all(0<v<1 and math.isfinite(v) for v in vals):
            raise ValueError("Unsafe probability in released issue")
        entries.append({
            "country_id":cid,
            "active_intrastate_2025":current,
            "p_model":round(p_main,12),
            "p_baseline_global_5y":round(p_recent,12),
            "p_country_eb":round(p_country,12),
            "p_activity_global":round(p_activity,12)
        })
    return entries,{
        "countries":len(cohort),"active_in_origin_2025":len(origin_activity),
        "inactive_in_origin_2025":len(cohort)-len(origin_activity),
        "training_country_years":global_n,"historical_newconf_positive_country_years":global_event,
        "baseline_recent_n":recent_n,"baseline_recent_events":recent_event,
        "global_full_probability":round(p_global,12),
        "baseline_recent_probability":round(p_recent,12),
        "historical_paired_horizon2_active_exposures":group[1][1],
        "historical_paired_horizon2_active_newconf":group[1][0],
        "historical_paired_horizon2_inactive_exposures":group[0][1],
        "historical_paired_horizon2_inactive_newconf":group[0][0],
        "expected_positive_countries_model":round(sum(x["p_model"] for x in entries),9),
        "expected_positive_countries_baseline":round(sum(x["p_baseline_global_5y"] for x in entries),9)
    }

def build(scriptbytes,panel,acd_historical,acd2025):
    rows,stats=calculate(panel,acd_historical,acd2025)
    return {
      "schema":SCHEMA,
      "forecast_id":ISSUE_ID,
      "state":"PREPARED_FOR_FIRST_PUBLIC_ISSUE",
      "target":{
         "year":TARGET_YEAR,
         "unit":"government-country-year",
         "binary_label":"1 iff ANY newconf=1 among multiple episode rows for country in UCDP Intrastate Country Level Multiple Onset covering year 2027",
         "source_variant":"INTRASTATE_COUNTRY_LEVEL_MULTIPLE_ONSET",
         "label_column":"newconf",
         "not_equivalent_to":"country-onset2 or statebased 25 deaths",
         "future_evaluation_release":"first complete official UCDP Intrastate Country Level Multiple Onset release covering calendar year 2027; unavailability remains unresolved",
         "outcome_missing_rule":"country not present or source edition incomplete = unresolved, never impute 0",
         "revision_policy":"first complete release primary; later revisions reported as sensitivity without changing issue"
      },
      "source":{
         "multiple_onset_training_version":"25.1",
         "multiple_onset_training_sha256":MULTI["25.1"]["sha256"],
         "multiple_onset_training_url":MULTI["25.1"]["url"],
         "historical_acd_version":"25.1",
         "historical_acd_sha256":ACDHIST["25.1"],
         "historical_acd_url":ACDURL["25.1"],
         "origin_acd_version":"26.1",
         "origin_acd_sha256":ACD261_SHA,
         "origin_acd_url":ACD261_URL,
         "training_newconf_last_year":TRAINING_LAST_YEAR,
         "origin_conflict_activity_year":ORIGIN_YEAR,
         "future_newconf_2025_observed":False,
         "future_newconf_2026_observed":False,
         "newconf_2027_outcome_observed":False,
         "sources_are_ucdp_public":True
      },
      "protocol":{
         "calendar_horizon_years":HORIZON,
         "training_first_year":TRAIN_START,
         "training_last_year":TRAINING_LAST_YEAR,
         "cohort_rule":"196 countries appearing in 2024 of the SHA-pinned UCDP Multiple Onset 25.1",
         "activity_rule":"binary UCDP PRIO ACD 26.1 type 3/4 intrastate conflict active at year 2025, singleton gwno_a",
         "model_primary":"country_newconf_eb_shrink20_to_2year_origin_activity_prior",
         "historical_group_prior":"global country-year newconf 2000-2024 Laplace1, then shrink group historical 2-year origin-activity event rates by alpha20",
         "country_prior_alpha":ALPHA,
         "baseline_primary":"global_laplace_newconf_prevalence_2020_2024",
         "additional_comparators":["country_eb_global_prior","origin_activity_group_global_prior"],
         "primary_metric":"Brier loss on frozen model minus frozen baseline across all resolved 2027 countries",
         "secondary_metrics":["logloss","calibration","Brier against country EB and activity global","baseline-negative Brier"],
         "inference":"bootstrap countries with replacement; few events => no retrospective significance assertion",
         "selection":"one frozen primary model and baseline, not adjusted after observing 2027 outcomes",
         "rank_tie_policy":"do not claim unique top-k alert hits if probability ties overlap cutoff; report best-worst hit range or omit",
         "unit_policy":"multiple conflict episode rows collapsed to ANY(newconf) per government-country-year; never count episode rows as countries",
         "horizon_limitation":"newconf outcomes last observed 2024, origin activity observed 2025, outcome 2027; no newconf 2025 labels available",
         "skill_demonstrated":False
      },
      "training_summary":stats,
      "provenance":{
         "generator_sha256":sha(scriptbytes),
         "first_public_forecast_commit":"the first public GitHub commit containing the exact 196 probabilities, not the pull request date",
         "independent_timestamp_notary":False,
         "historical_models_selected_after_2023_2024_outcomes_seen":True,
         "forecasts_issued_before_current":0,
         "statebased_geo2027_separate_and_unchanged":True
      },
      "countries":rows
    }

def validate(doc):
    if doc.get("schema")!=SCHEMA or doc.get("forecast_id")!=ISSUE_ID or \
      doc.get("state")!="PREPARED_FOR_FIRST_PUBLIC_ISSUE":
        raise ValueError("Wrong newconf issue protocol or state")
    rows=doc.get("countries",[])
    if len(rows)!=N or len({x["country_id"] for x in rows})!=N or \
       [x["country_id"] for x in rows]!=sorted(x["country_id"] for x in rows):
        raise ValueError("Newconf issue cohort incomplete, duplicated or unsorted")
    if doc["source"]["training_newconf_last_year"]!=2024 or \
       doc["source"]["origin_conflict_activity_year"]!=2025 or \
       doc["target"]["year"]!=2027:
        raise ValueError("Prospective newconf chronology invalid")
    if doc["protocol"]["skill_demonstrated"] is not False:
        raise ValueError("Must not assert skill before outcome")
    if any(any(not 0<x[key]<1 for key in (
        "p_model","p_baseline_global_5y","p_country_eb","p_activity_global"))
        for x in rows):raise ValueError("Predictions not valid probabilities")
    if sum(x["active_intrastate_2025"] for x in rows)!=32:
        raise ValueError("2025 source activity cohort changed")
    return True

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    ap.add_argument("--print-chunks",action="store_true")
    args=ap.parse_args()
    code=Path(__file__).read_bytes()
    labels,_=load_multiple("25.1")
    activity,_=load_activity("25.1")
    current=activity_2025()
    document=build(code,labels,activity,current)
    validate(document)
    content=(json.dumps(document,sort_keys=True,ensure_ascii=False,separators=(",",":"))+"\n")
    Path(args.output).write_text(content,encoding="utf8")
    print("NEWCONF2027_FORECAST_PREPARED",sha(content.encode()),"rows",len(document["countries"]),
          "expected_positives",document["training_summary"]["expected_positive_countries_model"],
          "origin_active",document["training_summary"]["active_in_origin_2025"])
    if args.print_chunks:
        print("NEWCONF2027_FORECAST_BEGIN")
        for i in range(0,len(content),1900):
            print("NEWCONF2027_FORECAST_PART",i//1900,content[i:i+1900])
        print("NEWCONF2027_FORECAST_END")

if __name__=="__main__":
    main()
