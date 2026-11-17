#!/usr/bin/env python3
"""GEO H2: intensity-aware four-state Markov vs exact first-issued binary protocol.

Two independent SOURCE-RELEASE-SEPARATED historical origin/outcome pairs:
official UCDP 23.1 (through 2022) -> UCDP 25.1 2024 outcomes and
24.1 (through 2023) -> UCDP 26.1 2025 outcomes.

Model and hypothesis are fixed before looking at model comparison results:
four states = [0 deaths, 1..24, 25..99, >=100], pooled Dirichlet(1)
global rows, country shrinkage strength 20, and exactly two steps to 2024/25.
Only ORIGINAL origin vintage data at or before cutoff enter either model.
A separate same-cohort exact binary Markov baseline is replayed from issued
GEO formula. No shadow model is prospectively issued by this script.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

from audit_geo2027_indonesia_original_fatalities import exact_nonnegative_int
from backtest_archived_country_vintages import (
    FOLDS, SOURCES, read_xlsx_rows,
)
from build_official_countries import read_zip
from diagnose_geo2028_historical_forecast_vintage_drift import _fit_at_origin
from probe_ucdp_organized_vintages import request
from prepare_geo2027_transition_alerts import (
    FORECAST_PATH, SOURCE_SHA256,
)

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo2027-intensity-markov-cross-release.json"
REFERENCE=ROOT/"data/forecast-2027-archival-cross-release.json"
VERSION_ORDER=("23.1","24.1","25.1","26.1")
EXPECTED_ROWS={"23.1":6544,"24.1":6740,"25.1":6936,"26.1":7132}
STATES=4
ACTIVE=(2,3)
LAPLACE=1
SHRINK=20
HORIZON=2
BINS=("zero","low_1_to_24","active_25_to_99","high_100_plus")
MAX_DOWNLOAD=8_000_000
MIN_YEAR=1989


def intensity_state(deaths):
    if type(deaths) is not int or deaths<0:
        raise ValueError("Negative/noninteger official death count")
    if deaths==0:
        return 0
    if deaths<25:
        return 1
    if deaths<100:
        return 2
    return 3


def parse_counts(raw,version):
    """Read ALL country-year original best fatality counts, preserving zero."""
    if version not in VERSION_ORDER:
        raise ValueError("Unsupported source edition")
    if hashlib.sha256(raw).hexdigest()!=SOURCES[version]["sha256"]:
        raise ValueError("UCDP official source SHA-256 mismatch")
    if version=="23.1":
        rows=read_xlsx_rows(raw)
    else:
        if version=="26.1":
            csv_text=read_zip(raw)
            fields=("country_id","year","sb_total_deaths_best")
        else:
            with ZipFile(io.BytesIO(raw)) as z:
                members=[i for i in z.infolist()
                         if not i.is_dir() and i.filename.lower().endswith(".csv")]
                if (len(members)!=1 or members[0].file_size>12_000_000
                    or members[0].file_size<100_000):
                    raise ValueError("Unexpected official CSV ZIP members/size")
                csv_text=z.read(members[0]).decode("utf-8-sig")
            fields=("country_id_cy","year_cy","sb_total_deaths_best_cy")
        reader=csv.DictReader(io.StringIO(csv_text))
        if not set(fields).issubset(reader.fieldnames or []):
            raise ValueError("Missing official fatalities schema")
        rows=((r[fields[0]],r[fields[1]],r[fields[2]]) for r in reader)
    result=defaultdict(dict)
    n=0
    cutoff=SOURCES[version]["last_year"]
    for country,year,deaths in rows:
        cid=exact_nonnegative_int(country,"country ID")
        y=exact_nonnegative_int(year,"year")
        d=exact_nonnegative_int(deaths,"sb_total_deaths_best")
        if not 1<=cid<=2000 or not MIN_YEAR<=y<=cutoff:
            raise ValueError("Unexpected official GWNO/year range")
        if y in result[cid]:
            raise ValueError("Duplicate source country-year")
        result[cid][y]=d
        n+=1
    if n!=EXPECTED_ROWS[version] or max(max(h) for h in result.values())!=cutoff:
        raise ValueError("Original source row count or cutoff mismatch")
    if sum(cutoff in h and cutoff-1 in h for h in result.values())!=196:
        raise ValueError("Original 196-country risk set unavailable")
    return result


def counts_to_binary(records):
    return {cid:{year:int(d>=25) for year,d in h.items()}
            for cid,h in records.items()}


def four_state_forecast(records,origin,*,historical_rolling_diagnostic=False):
    """H2 categorical forecasts, with origin-only data; historical opt-in.

    The original 2022/2023 fixed comparison keeps its exact default contract.
    Historical rolling diagnostics may start in 2012 after 2011 full GWNO.
    These are explicitly ex-post pseudo-origins, never issued forecasts.
    """
    if (type(origin) is not int or
        (not historical_rolling_diagnostic and origin not in (2022,2023)) or
        (historical_rolling_diagnostic and not 2012<=origin<=2023)):
        raise ValueError("Unsupported historical four-state origin year")
    if not records:
        raise ValueError("Empty original official source")
    clipped={}
    for cid,h in records.items():
        if type(cid) is not int or not 1<=cid<=2000 or not h:
            raise ValueError("Invalid GWNO source history")
        history={y:intensity_state(deaths) for y,deaths in h.items()
                 if y<=origin}
        if history:
            clipped[cid]=history
    cohort=sorted(cid for cid,h in clipped.items()
                  if origin in h and origin-1 in h)
    if len(cohort)!=196:
        raise ValueError("Intensity origin risk-set mismatch")
    global_counts=[[0]*STATES for _ in range(STATES)]
    local={}
    for cid,h in clipped.items():
        c=[[0]*STATES for _ in range(STATES)]
        for year in sorted(h):
            if year-1 in h:
                s,t=h[year-1],h[year]
                c[s][t]+=1
                global_counts[s][t]+=1
        local[cid]=c
    if any(sum(row)<10 for row in global_counts):
        raise ValueError("Insufficient transitions for one intensity state")
    g=[[(global_counts[s][t]+LAPLACE)/
        (sum(global_counts[s])+STATES*LAPLACE) for t in range(STATES)]
       for s in range(STATES)]
    forecasts={}
    for cid in cohort:
        c=local[cid]
        q=[[(c[s][t]+SHRINK*g[s][t])/
            (sum(c[s])+SHRINK) for t in range(STATES)]
           for s in range(STATES)]
        initial=clipped[cid][origin]
        p=sum(q[initial][j]*sum(q[j][a] for a in ACTIVE)
              for j in range(STATES))
        if not math.isfinite(p) or not 0<p<1:
            raise ValueError("Invalid four-state H2 probability")
        forecasts[cid]={"p_intensity_markov":round(p,12),
                        "origin_intensity_state":initial,
                        "origin_state":int(initial in ACTIVE)}
    return forecasts,{
        "origin_year":origin,
        "cutoff_max":max(max(h) for h in clipped.values()),
        "training_countries":len(clipped),
        "eligible_countries":len(cohort),
        "global_4x4_transitions":global_counts,
        "global_4x4_dirichlet_rows":g,
        "country_shrinkage":SHRINK,
        "dirichlet_global_pseudocount_per_category":LAPLACE,
    }


def scores(rows,field):
    if not rows:
        raise ValueError("No resolved outcomes")
    brier=sum((r[field]-r["outcome"])**2 for r in rows)/len(rows)
    logloss=-sum(
        r["outcome"]*math.log(min(1-1e-12,max(1e-12,r[field])))+
        (1-r["outcome"])*math.log1p(-min(1-1e-12,max(1e-12,r[field])))
        for r in rows)/len(rows)
    return {"brier":brier,"logloss":logloss}


def compare_scores(rows):
    baseline=scores(rows,"p_original_binary")
    new=scores(rows,"p_intensity_markov")
    return {
        "n":len(rows),"positives":sum(r["outcome"] for r in rows),
        "original_binary":baseline,
        "intensity_four_state":new,
        "intensity_minus_binary_delta_brier":new["brier"]-baseline["brier"],
        "intensity_minus_binary_delta_logloss":new["logloss"]-baseline["logloss"],
        "intensity_brier_better_on_this_sample":
            new["brier"]<baseline["brier"],
        "absolute_probability_difference_mean":
            sum(abs(r["p_intensity_markov"]-r["p_original_binary"])
                for r in rows)/len(rows)
    }


def replay(sources,reference):
    if (reference.get("schema")!="idealab.psico.statebased_archival_cross_release_v1"
        or reference.get("historical_forecasts_actually_issued") is not False
        or reference.get("prospective_skill_demonstrated") is not False
        or reference.get("2027_issued_model_or_probabilities_modified") is not False):
        raise ValueError("Original historical reference experiment changed")
    allrows=[];folds=[]
    for spec in FOLDS:
        origin_year=spec["origin_year"]
        target_year=spec["target_year"]
        orig=spec["origin_release"]
        target=spec["target_release"]
        if SOURCES[orig]["last_year"]!=origin_year or SOURCES[target]["last_year"]!=target_year:
            raise ValueError("Source vintage horizon/origin mismatch")
        origin_records=sources[orig]
        outcomes=sources[target]
        categorical, details=four_state_forecast(origin_records,origin_year)
        original, origdetails=_fit_at_origin(
            counts_to_binary(origin_records),origin_year)
        if (details["cutoff_max"]!=origin_year or
            origdetails["last_training_year"]!=origin_year or
            set(categorical)!=set(original)):
            raise ValueError("Post-origin leakage or differing GEO cohorts")
        country_rows=[]
        unresolved=[]
        for cid in sorted(original):
            last=origin_records[cid][origin_year]
            if target_year not in outcomes.get(cid,{}):
                unresolved.append(cid)
                continue
            row={"country_id":cid,
                 "origin_year":origin_year,
                 "target_year":target_year,
                 "origin_state":int(last>=25),
                 "origin_intensity_state":intensity_state(last),
                 "outcome":int(outcomes[cid][target_year]>=25),
                 "p_original_binary":original[cid]["p_model_h2"],
                 "p_intensity_markov":categorical[cid]["p_intensity_markov"]}
            country_rows.append(row)
        if len(country_rows)!=196 or unresolved:
            raise ValueError("Official target labels incomplete; never impute negatives")
        prior=next(f for f in reference["folds"]
                   if f["origin_cutoff"]==origin_year and
                   f["origin_version"]==orig and f["outcome_version"]==target)
        original_brier=scores(country_rows,"p_original_binary")["brier"]
        original_logloss=scores(country_rows,"p_original_binary")["logloss"]
        if (abs(original_brier-prior["scores"]["p_model"]["brier"])>1e-10
            or abs(original_logloss-prior["scores"]["p_model"]["logloss"])>1e-10
            or sum(r["outcome"] for r in country_rows)!=prior["positives"]):
            raise AssertionError("Original GEO binary backtest was not exactly reproduced")
        result=compare_scores(country_rows)
        folds.append({"origin_release":orig,"target_release":target,
            "origin_year":origin_year,"target_year":target_year,
            "resolved":len(country_rows),"unresolved":unresolved,
            "original_binary_exact_reference_reproduced":True,
            "transition_summary":details,
            "metrics":result,
            "by_origin_binary_state":{
                str(st):compare_scores([r for r in country_rows if r["origin_state"]==st])
                for st in (0,1)},
            "by_origin_death_intensity":{
                BINS[st]:compare_scores([r for r in country_rows if r["origin_intensity_state"]==st])
                for st in range(4) if any(r["origin_intensity_state"]==st for r in country_rows)
            }})
        allrows.extend(country_rows)
    if len(allrows)!=392:
        raise ValueError("Expected two fixed 196-country historical folds")
    pooled=compare_scores(allrows)
    if abs(pooled["original_binary"]["brier"]-reference["metrics"]["p_model"]["brier"])>1e-10:
        raise AssertionError("Original pooled cross-release binary baseline mismatch")
    contributions=[{
        "country_id":cid,
        "outcomes_by_target_year":[
            {"target_year":r["target_year"],"observed_state":r["outcome"],
             "original_p":r["p_original_binary"],
             "intensity_p":r["p_intensity_markov"],
             "delta_brier":round((r["p_intensity_markov"]-r["outcome"])**2-
                                 (r["p_original_binary"]-r["outcome"])**2,12)}
            for r in allrows if r["country_id"]==cid],
        "mean_country_paired_delta_brier":sum(
            (r["p_intensity_markov"]-r["outcome"])**2-
            (r["p_original_binary"]-r["outcome"])**2
            for r in allrows if r["country_id"]==cid)/2
        } for cid in sorted(set(r["country_id"] for r in allrows))]
    if len(contributions)!=196 or any(len(r["outcomes_by_target_year"])!=2 for r in contributions):
        raise ValueError("Unbalanced paired country effects")
    ranked=sorted(contributions,key=lambda r:(r["mean_country_paired_delta_brier"],r["country_id"]))
    return {
        "schema":"idealab.psico.geo2027_four_state_intensity_cross_release.v1",
        "status":"EX_POST_SOURCE_SEPARATED_INTENSITY_ABLATION_NOT_PROSPECTIVE_ISSUE",
        "original_forecast_2027_sha256":SOURCE_SHA256,
        "official_origin_target_editions":[
            {"origin":f["origin_release"],"target":f["target_release"],
             "origin_year":f["origin_year"],"outcome_year":f["target_year"]}
            for f in folds],
        "sources_sha256":{v:SOURCES[v]["sha256"] for v in VERSION_ORDER},
        "horizon_years":2,
        "four_state_bins":list(BINS),
        "state_cutoffs_deaths":[0,1,25,100],
        "state_based_25_death_binary_target_unchanged":True,
        "hyperparameter_grid_searched":False,
        "four_state_global_dirichlet_pseudocount_per_category":LAPLACE,
        "four_state_local_shrinkage":SHRINK,
        "binary_original_protocol":"Markov two-state Laplace1 global shrink20 H2",
        "model_selection_using_holdout_outcomes":False,
        "cohorts":folds,
        "pooled":pooled,
        "by_origin_binary_state":{
            str(st):compare_scores([r for r in allrows if r["origin_state"]==st])
            for st in (0,1)},
        "by_origin_death_intensity":{
            BINS[st]:compare_scores([r for r in allrows if r["origin_intensity_state"]==st])
            for st in range(4) if any(r["origin_intensity_state"]==st for r in allrows)},
        "n_countries_with_lower_country_mean_brier_using_intensity":
            sum(r["mean_country_paired_delta_brier"]<0 for r in contributions),
        "n_countries_with_higher_country_mean_brier_using_intensity":
            sum(r["mean_country_paired_delta_brier"]>0 for r in contributions),
        "largest_10_country_mean_brier_improvements":ranked[:10],
        "largest_10_country_mean_brier_worsenings":list(reversed(ranked[-10:])),
        "two_annual_blocks_are_not_a_basis_for_country_iid_confidence_intervals":True,
        "retrospective_archive_sources_do_not_independently_prove_original_release_times":True,
        "prospective_skill_demonstrated":False,
        "original_2027_2028_issued_forecasts_or_alerts_changed":False,
        "historical_predictions_issued_at_origin":False,
        "outcomes_2027_resolved":0,
        "limitations":"Only two ex-post source-separated target years, with overlapping GWNO and macro shocks. No 2022/2023 forecast issued then; archive release times not independently notarized. Four-state categories and common shrinkage are one fixed exploratory alternative, not optimized model selection. Contrasts have no causal or prospective interpretation."
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report",action="store_true")
    args=parser.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("First-issued 2027 GEO probabilities have changed")
    ref=json.loads(REFERENCE.read_text(encoding="utf8"))
    data={}
    for version in VERSION_ORDER:
        raw=request(SOURCES[version]["url"],MAX_DOWNLOAD)
        data[version]=parse_counts(raw,version)
    report=replay(data,ref)
    payload=json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    print("GEO2027_FOUR_STATE_INTENSITY_REPLAY_BEGIN")
    print(payload,end="")
    print("GEO2027_FOUR_STATE_INTENSITY_REPLAY_END")
    if args.check_report and REPORT.read_bytes()!=payload.encode():
        raise ValueError("Four-state intensity report does not match source-replayed result")


if __name__=="__main__":
    main()
