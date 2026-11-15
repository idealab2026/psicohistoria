#!/usr/bin/env python3
"""GEO2028 three-year prospective horizon candidate — protocol BEFORE issue.

Origin UCDP OrganizedViolenceCY 26.1 through 2025 only, 196 GWNO countries.
New 2028 endpoint is a THREE-year projection of the *same* state-based
>=25 annual deaths indicator as GEO2027. It is NOT a rolling-origin 2026
two-year replication, NOT independent of original 2027 issued GEO, and NOT
a fourth independent 2027 endpoint. No outcomes after 2025 loaded.
The first publicly committed full output, NOT script execution, is issuance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import build_2027_prospective_registry as registry
import forecast_2027_statebased as geo2027
from build_official_countries import (
    PINNED_SOURCE_SHA256, OFFICIAL_URL, read_zip, parse_public_source
)

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL_ID="PSICO-GEO2028-STATEBASED25-H3-ORIGIN2025-V1"
SCHEMA="idealab.psico.prospective_geo2028_three_year.v1"
TARGET=2028
ORIGIN=2025
HORIZON=3
SOURCE_VERSION="26.1"
N=196
EXPECTED_ORIGIN=registry.EXPECTED["geo"][1]
OUT=ROOT/"data/forecast-2028-geo3.json"
SOURCE_SHA=PINNED_SOURCE_SHA256


def interior(p):
    if type(p) not in (int,float) or not math.isfinite(p) or not 0<p<1:
        raise ValueError("Issued model probability not strictly in (0,1)")
    v=round(p,12)
    if not 0<v<1:
        raise ValueError("Issued precision invalid")
    return v


def nsteps(initial,q,steps):
    """Transition P(active at t+h) = q0+(q1-q0)*P(active at t+h-1)."""
    if type(initial) is not int or initial not in (0,1) or steps not in (2,3):
        raise ValueError("Wrong horizon or nonbinary known origin")
    q0,q1=q
    if any(type(x) not in (int,float) or
           not math.isfinite(x) or not 0<x<1 for x in (q0,q1)):
        raise ValueError("Malformed 1-year transition probabilities")
    p=float(initial)
    for _ in range(steps):
        p=q0+(q1-q0)*p
    return interior(p)


def build_from_records(records,names,issued2027):
    """Re-estimate EXACT original 2027 model, then add one Markov step."""
    if (issued2027.get("forecast_id")!=geo2027.PROTOCOL_ID
        or issued2027.get("target",{}).get("year")!=2027
        or issued2027.get("source",{}).get("sha256")!=SOURCE_SHA
        or issued2027.get("source",{}).get("data_last_year")!=ORIGIN
        or len(issued2027.get("countries",[]))!=N):
        raise ValueError("Original GEO2027 issuance not authenticated")
    rows2027,oldsummary=geo2027.estimate_from_history(records,names)
    if rows2027!=issued2027["countries"]:
        raise ValueError("2027 model is not reproducible from origin-only 26.1")
    gc=oldsummary["global_transition_counts"]
    global_q=[(gc[s][1]+geo2027.LAPLACE)/
              (sum(gc[s])+2*geo2027.LAPLACE) for s in (0,1)]
    if any(abs(round(p,12)-v)>1e-12 for p,v in zip(
            global_q,oldsummary["global_transition_p_active"])):
        raise ValueError("Source transition counts inconsistent")
    by_old={r["country_id"]:r for r in rows2027}
    ids=[r["country_id"] for r in rows2027]
    if (len(set(ids))!=N or ids!=sorted(ids) or
        any(max(h)>ORIGIN for h in records.values() if h) or
        any(ORIGIN not in records[cid] or ORIGIN-1 not in records[cid]
            for cid in ids)):
        # A historical UCDP archive may also retain retired countries that
        # are NOT among the 196 current GWNO risk countries. Do not require
        # an obsolete country to have a 2025 row; require both recent years
        # for EVERY registered country and no post-origin data anywhere.
        raise ValueError("Origin coverage or country identifiers changed")
    per={cid:[[0,0],[0,0]] for cid in records}
    for cid,h in sorted(records.items()):
        for year in sorted(h):
            if year>1989 and year-1 in h:
                per[cid][h[year-1]][h[year]]+=1
    newrows=[]
    for cid in ids:
        last=records[cid][ORIGIN]
        local=per[cid]
        q=[(local[s][1]+geo2027.TRANSITION_PRIOR*global_q[s])/
           (sum(local[s])+geo2027.TRANSITION_PRIOR) for s in (0,1)]
        # Two-step exact agreement independently proves the Markov kernel
        # matches FIRST-issued 2027 probabilities before 2028 projection.
        if (abs(nsteps(last,q,2)-by_old[cid]["p_model"])>1e-11 or
            abs(nsteps(last,global_q,2)-by_old[cid]["p_global_markov"])>1e-11):
            raise ValueError("Three-step kernel diverges from original 2027 issue")
        newrows.append({
            "country_id":cid,
            "country":names[cid],
            "last_observed_state_2025":last,
            "p_model":nsteps(last,q,3),
            "p_global_markov_3step":nsteps(last,global_q,3),
            "p_baseline_global_5y":by_old[cid]["p_baseline_global_5y"],
            "p_issued_geo2027_2step_for_temporal_comparison_only":
                by_old[cid]["p_model"],
        })
    if (len(newrows)!=N or
        any(type(x["country_id"]) is not int for x in newrows)):
        raise ValueError("GEO2028 cohort not complete")
    return newrows,oldsummary


def build_forecast(source_bytes,original_issued):
    if hashlib.sha256(source_bytes).hexdigest()!=SOURCE_SHA:
        raise ValueError("UCDP 26.1 official source SHA mismatch")
    records,names=parse_public_source(read_zip(source_bytes))
    rows,summary=build_from_records(records,names,original_issued)
    return {
        "schema":SCHEMA,
        "forecast_id":PROTOCOL_ID,
        "state":"CANDIDATE_BEFORE_FIRST_PUBLIC_2028_ISSUE",
        "target":{
            "year":TARGET,
            "binary_rule":"1 iff UCDP OrganizedViolenceCY official 2028 country-year state-based best fatalities >=25",
            "unit":"Gleditsch-Ward government country-year",
            "source_release":"first complete post-2028 UCDP OrganizedViolenceCY edition; later revisions sensitivity only",
            "missing_country_rule":"unresolved, never assume absence is zero",
            "not_newconf_or_ACD_conflict_presence":True,
        },
        "origin":{
            "year":ORIGIN,
            "official_data_last_year":ORIGIN,
            "source_version":SOURCE_VERSION,
            "official_url":OFFICIAL_URL,
            "official_sha256":SOURCE_SHA,
            "cohort_rule":"196 original 2025 source GWNO countries with both 2024 and 2025 data",
            "same_2025_origin_as_GEO2027":True,
        },
        "protocol":{
            "horizon_years":HORIZON,
            "primary_model":"country_markov_3step_laplace_global_shrink20",
            "training_rule":"same 1-year country/state global-Laplace/shrink20 Markov transitions trained only through 2025; compose exactly three steps",
            "primary_baseline":"global_laplace_5y_2021_2025",
            "secondary_comparator":"global_markov_3step_laplace",
            "primary_metric":"paired mean Brier p_model minus p_baseline_global_5y over all 196 fixed country endpoints on first complete official source",
            "secondary_metrics":["log-loss","Brier against global Markov 3-step","predeclared origin-stratum calibration"],
            "first_complete_2028_source_required":True,
            "original_2027_forecast_immutable":True,
            "not_independent_rolling_origin_two_year_replication":True,
            "cannot_pool_with_GEO2027_as_independent_forecasts":True,
            "no_automatic_promotion_or_model_selection":True,
            "posthoc_prior_2024_2025_history_inspected":True,
            "statistical_generalization_not_established":True,
        },
        "first_issue_provenance":{
            "protocol_preregistered_before_probability_issue":True,
            "original_GEO2027_SHA256":EXPECTED_ORIGIN,
            "original_GEO2027_first_public_commit":registry.EXPECTED["geo"][2],
            "independent_timestamp_notary":False,
            "GitHub_first_public_file_commit_required_before_target_year":True,
            "official_2028_outcomes_observed":0,
        },
        "n_countries":len(rows),
        "model_expected_2028_active_countries":{
            "p_model":round(sum(r["p_model"] for r in rows),12),
            "p_global_markov_3step":round(sum(r["p_global_markov_3step"] for r in rows),12),
            "p_baseline_global_5y":round(sum(r["p_baseline_global_5y"] for r in rows),12),
        },
        "origin_2025_training_summary":summary,
        "countries":rows,
        "2028_outcomes_resolved":0,
        "prospective_predictive_skill_demonstrated":False,
    }


def validate_forecast(doc):
    if (doc.get("schema")!=SCHEMA or
        doc.get("forecast_id")!=PROTOCOL_ID or
        doc.get("state")!="CANDIDATE_BEFORE_FIRST_PUBLIC_2028_ISSUE" or
        doc.get("origin",{}).get("year")!=ORIGIN or
        doc.get("origin",{}).get("official_data_last_year")!=ORIGIN or
        doc.get("origin",{}).get("official_sha256")!=SOURCE_SHA or
        doc.get("target",{}).get("year")!=TARGET or
        doc.get("protocol",{}).get("horizon_years")!=3 or
        doc.get("protocol",{}).get("not_independent_rolling_origin_two_year_replication") is not True or
        doc.get("first_issue_provenance",{}).get("original_GEO2027_SHA256")!=EXPECTED_ORIGIN or
        doc.get("2028_outcomes_resolved")!=0 or
        doc.get("prospective_predictive_skill_demonstrated") is not False):
        raise ValueError("Unsafe source, horizon, cohort or outcome issue")
    rows=doc.get("countries")
    if type(rows) is not list or len(rows)!=N or doc.get("n_countries")!=N:
        raise ValueError("Incomplete original 196-country risk cohort")
    ids=[r.get("country_id") for r in rows]
    if (any(type(cid) is not int for cid in ids) or
        sorted(ids)!=ids or len(set(ids))!=N):
        raise ValueError("Invalid GWNO country identifiers")
    for r in rows:
        if (r.get("last_observed_state_2025") not in (0,1) or
            any(type(r.get(k)) not in (int,float) or
                not math.isfinite(r[k]) or not 0<r[k]<1 for k in
                ("p_model","p_global_markov_3step","p_baseline_global_5y",
                 "p_issued_geo2027_2step_for_temporal_comparison_only"))):
            raise ValueError("Invalid first-issued GEO2028 probability")
    for k,expected in doc.get("model_expected_2028_active_countries",{}).items():
        if k not in ("p_model","p_global_markov_3step","p_baseline_global_5y") or (
            abs(sum(r[k] for r in rows)-expected)>1e-10):
            raise ValueError("2028 expected active count not consistent with rows")
    if len(doc.get("model_expected_2028_active_countries",{}))!=3:
        raise ValueError("2028 missing baseline or comparison totals")
    return True


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--print-canonical",action="store_true")
    parser.add_argument("--check-issued",action="store_true")
    parser.add_argument("--summary",action="store_true")
    args=parser.parse_args()
    docs,manifests=registry.read_issued()
    original=registry.make_registry(docs,manifests)
    if (original["n_unique_country_endpoint_rows"]!=424 or
        original["n_verified_future_2027_outcomes"]!=0):
        raise ValueError("Existing 2027 issue set was altered")
    raw=geo2027.download_official()
    doc=build_forecast(raw,docs["geo"])
    validate_forecast(doc)
    body=registry.canonical(doc)
    if args.check_issued and OUT.read_bytes()!=body:
        raise ValueError("GEO2028 original first-issued canonical bytes differ")
    if args.summary:
        print("GEO2028_CANDIDATE_SUMMARY",json.dumps({
            "n":doc["n_countries"],
            "target_year":doc["target"]["year"],
            "horizon":doc["protocol"]["horizon_years"],
            "origin_year":doc["origin"]["year"],
            "expected":doc["model_expected_2028_active_countries"],
            "canonical_sha256":hashlib.sha256(body).hexdigest(),
            "issued_2027_frozen":True,"2028_outcomes_observed":0,
        },sort_keys=True))
    if args.print_canonical:
        print("GEO2028_ISSUE_CANONICAL_BEGIN")
        print(body.decode("utf8"),end="")
        print("GEO2028_ISSUE_CANONICAL_END")


if __name__=="__main__":
    main()
