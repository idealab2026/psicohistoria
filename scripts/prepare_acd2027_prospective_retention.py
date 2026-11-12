#!/usr/bin/env python3
"""Source-frozen prospective 2027 intrastate ACD persistence, 2025 origin.

Separate UCDP/PRIO ACD country-presence endpoint: NOT GEO2027 state-based
25-death labels, onset, peace, or a prediction for all 196 world countries.
"""
import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

from inspect_ucdp_archives import fetch
from probe_ucdp_prio_incidence import MAX_ZIP, ALLOWED_TYPES, parse_country_code, source_zip
from backtest_ucdp_prio_retention_four_vintages import (
    START, HORIZON, PRIOR_STRENGTH, RECENT_ORIGIN_YEARS,
)
from evaluate_geo2027_calibrated_shadow_official import load_authenticated
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256 as ORIGINAL_GEO_SHA256, sha

SOURCE_URL = "https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-261-csv.zip"
ACD_SOURCE_SHA256 = None  # Pin only from official ZIP bytes in first CI source probe.
ISSUE_PATH = Path("data/forecast-2027-acd-retention.json")
FORECAST_ID = "PSICO-ACD2027-INTRASTATE-T2-PERSISTENCE-V1"
ORIGIN = 2025
TARGET = 2027
PRIMARY = "p_global_recent5"
COMPARATORS = ("p_country_eb", "p_lag1_group")


def official_source(raw, probe=False):
    digest=hashlib.sha256(raw).hexdigest()
    if ACD_SOURCE_SHA256 is None and not probe:
        raise ValueError("26.1 UCDP/PRIO archive not SHA-pinned yet")
    if ACD_SOURCE_SHA256 is not None and digest != ACD_SOURCE_SHA256:
        raise ValueError("26.1 official ACD original source hash changed")
    rows,fields=source_zip(raw)
    active=set()
    seen=set()
    for r in rows:
        y_text=r["year"].strip()
        if not y_text.isdigit():
            raise ValueError("Non-numeric official conflict year")
        y=int(y_text)
        if not 1946<=y<=ORIGIN:
            raise ValueError("A 2026/27 or earlier-than-1946 label was used")
        if r["type_of_conflict"].strip() not in ALLOWED_TYPES:
            continue
        cid=parse_country_code(r["gwno_a"])
        loc=parse_country_code(r["gwno_loc"])
        if cid is None or cid!=loc or not 1<=int(cid)<=2000:
            raise ValueError("Ambiguous intrastate government country code")
        conflict_id=r["conflict_id"].strip()
        if not conflict_id.isdigit():
            raise ValueError("Invalid official conflict id")
        k=(cid,y,conflict_id)
        if k in seen:
            raise ValueError("Duplicated original conflict-year")
        seen.add(k)
        active.add((cid,y))
    risk={cid for cid,y in active if y==ORIGIN}
    if (len(rows)<2400 or len(active)<1750 or
        len({cid for cid,y in active})<95 or
        not 20<=len(risk)<=75 or max(y for cid,y in active)!=ORIGIN):
        raise ValueError("Original ACD 26.1 source coverage unexpectedly sparse")
    return active,{
        "official_url":SOURCE_URL,
        "source_zip_sha256":digest,
        "pinned":ACD_SOURCE_SHA256 is not None,
        "last_observed_year":ORIGIN,
        "total_conflict_year_records":len(rows),
        "intrastate_active_country_years":len(active),
        "intrastate_2025_risk_countries":len(risk),
        "csv_schema":fields,
        "no_actual_2027_outcomes":True,
    }


def forecast(active,source):
    if (source["pinned"] is not True or
        source["last_observed_year"]!=ORIGIN or
        source["no_actual_2027_outcomes"] is not True):
        raise ValueError("Unpinned historical or future contaminated data")
    if any(y>ORIGIN for _,y in active):
        raise ValueError("Future outcomes in original ACD source")
    examples=[
        (cid,y,int((cid,y+HORIZON) in active),int((cid,y-1) in active))
        for cid,y in sorted(active) if START<=y<=ORIGIN-HORIZON
    ]
    if len(examples)<250 or len({cid for cid,_,_,_ in examples})<35:
        raise ValueError("Insufficient historical origin risk exposure")
    hits=sum(x[2] for x in examples)
    if not 0<hits<len(examples):
        raise ValueError("Single-class original training labels")
    global_p=(hits+.5)/(len(examples)+1)
    recent=[
        x for x in examples
        if x[1]>=ORIGIN-HORIZON-RECENT_ORIGIN_YEARS+1
    ]
    if len(recent)<50:
        raise ValueError("Missing training recent years")
    recent_p=(sum(x[2] for x in recent)+.5)/(len(recent)+1)
    country=defaultdict(lambda:[0,0])
    lag=defaultdict(lambda:[0,0])
    for cid,y,label,prior in examples:
        country[cid][0]+=label;country[cid][1]+=1
        lag[prior][0]+=label;lag[prior][1]+=1
    def precision(p):
        if not math.isfinite(p) or not 0<p<1:
            raise ValueError("Invalid prospective 2027 ACD probability")
        v=round(p,12)
        if not 0<v<1:
            raise ValueError("Invalid rounded prospective probability")
        return v
    rows=[]
    for cid in sorted((cid for cid,y in active if y==ORIGIN),
                      key=lambda k:int(k)):
        h,n=country[cid]
        prior=int((cid,ORIGIN-1) in active)
        hl,nl=lag[prior]
        rows.append({
            "country_id":int(cid),
            "conflict_present_in_origin_2025":True,
            "also_active_in_2024":bool(prior),
            "origin_only_historical_country_training_rows":n,
            "p_global_recent5":precision(recent_p),
            "p_country_eb":precision(
                (h+PRIOR_STRENGTH*global_p)/(n+PRIOR_STRENGTH)),
            "p_lag1_group":precision(
                (hl+PRIOR_STRENGTH*global_p)/(nl+PRIOR_STRENGTH)),
        })
    return {
        "schema":"idealab.psico.acd2027_intrastate_retention_forecast.v1",
        "forecast_id":FORECAST_ID,
        "status":"CANDIDATE_PRIOR_TO_FIRST_PUBLIC_ISSUE",
        "source_release":"UCDP/PRIO Armed Conflict Dataset 26.1",
        "source_official_url":SOURCE_URL,
        "source_zip_sha256":source["source_zip_sha256"],
        "origin_year":ORIGIN,
        "target_year":TARGET,
        "source_data_last_year":ORIGIN,
        "target":"Presence of >=1 type 3/4 intrastate ACD conflict in 2027 among countries with such a conflict in 2025; NOT >=25 deaths GEO, onset, or peace",
        "n_origin_active_countries":len(rows),
        "primary_model":PRIMARY,
        "secondary_models":list(COMPARATORS),
        "historical_model_selection_exploratory_post_hoc":True,
        "actual_2027_outcomes_used":False,
        "2027_outcomes_resolved":0,
        "prospective_skill_demonstrated":False,
        "forecast_not_for_full_196_country_universe":True,
        "source_facts":source,
        "training_n_country_years":len(examples),
        "training_n_persisted":hits,
        "training_target_latest_year":ORIGIN,
        "training_origin_latest_year":ORIGIN-HORIZON,
        "training_recent_origin_years":list(range(2019,2024)),
        "model_expected_2027_persistence":{
            k:round(sum(x[k] for x in rows),12)
            for k in (PRIMARY,*COMPARATORS)
        },
        "countries":rows,
        "interpretation":"Original 2027 forecast awaits first public GitHub commit. Secondary models not independently validated, and no 2027 outcome is observed.",
    }


def canonical(doc):
    return (json.dumps(doc,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode()


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--probe-source",action="store_true")
    p.add_argument("--print-canonical",action="store_true")
    p.add_argument("--check-issued",action="store_true")
    args=p.parse_args()
    if args.probe_source and (args.print_canonical or args.check_issued):
        raise ValueError("Cannot publish from unpinned source probe")
    original,shadow,_=load_authenticated()
    if (len(original["countries"])!=196 or len(shadow["countries"])!=196
        or shadow["2027_outcomes_resolved"]!=0
        or sha(FORECAST_PATH.read_bytes())!=ORIGINAL_GEO_SHA256):
        raise ValueError("Existing GEO2027 original/shadow must remain immutable")
    active,source=official_source(fetch(SOURCE_URL,MAX_ZIP),args.probe_source)
    if args.probe_source:
        print("ACD261_SOURCE_PROBE_BEGIN")
        print(json.dumps(source,indent=2,sort_keys=True,ensure_ascii=False))
        print("ACD261_SOURCE_PROBE_END")
        return
    doc=forecast(active,source)
    data=canonical(doc)
    print("ACD2027_RETENTION_CANONICAL_SHA256",hashlib.sha256(data).hexdigest())
    if args.print_canonical:
        print("ACD2027_RETENTION_CANONICAL_BEGIN")
        print(data.decode(),end="")
        print("ACD2027_RETENTION_CANONICAL_END")
    if args.check_issued and ISSUE_PATH.read_bytes()!=data:
        raise ValueError("Published 2027 ACD probabilities differ from source-canonical issue")


if __name__=="__main__":
    main()
