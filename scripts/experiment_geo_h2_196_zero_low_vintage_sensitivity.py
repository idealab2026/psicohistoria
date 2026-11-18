#!/usr/bin/env python3
"""196-country H2 sensitivity to 0<->1..24 source-state reclassifications.

The two UCDP official origin editions are SHA pinned. Cut at historical
pseudo-origin 2021. Compare exactly two blocks of source edits:
 Z: all zero<->low changes, O: all other count changes. Evaluate 2x2
factorial, exact symmetric Shapley by country and Brier score under a
fixed UCDP 26.1 target label. Do not infer prospective predictive skill.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit as audit_issued,
)
from backtest_archived_country_vintages import SOURCES
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD, EXPECTED_ROWS, VERSION_ORDER, intensity_state, parse_counts,
    four_state_forecast,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
RANK_REFERENCE=ROOT/"data/geo-h2-2023-country-origin-vintage-rank-influence.json"
RWANDA_REFERENCE=ROOT/"data/geo-h2-rwanda-2021-23-24-source-shapley.json"
OUTPUT=ROOT/"data/geo-h2-196-zero-low-origin-vintage-sensitivity.json"
ORIGIN=2021
TARGET=2023
N=196
EPS=1e-11


def zero_low(old,new):
    if type(old) is not int or type(new) is not int or old<0 or new<0:
        raise ValueError("Invalid historical fatality data")
    return {intensity_state(old),intensity_state(new)}=={0,1}


def two_block_shapley(p00,p10,p01,p11):
    zero=.5*((p10-p00)+(p11-p01))
    other=.5*((p01-p00)+(p11-p10))
    if not math.isclose(zero+other,p11-p00,rel_tol=0,abs_tol=1e-12):
        raise AssertionError("Source-block Shapley is not additive")
    return zero,other


def evaluate(old_source,new_source,rank_reference,rwanda_reference,issue_ids):
    if (rank_reference.get("schema")!=
        "idealab.psico.geo_h2_2023_country_origin_vintage_rank_attribution.v1"
        or rwanda_reference.get("schema")!=
        "idealab.psico.geo_h2_rwanda_origin_vintage_twofactor_shapley.v1"
        or rank_reference.get("common_official_outcome_release")!="26.1"
        or rank_reference.get("original_GEO2027_issued_sha256")!=SOURCE_SHA256
        or rwanda_reference.get("original_GEO2027_issue_sha256")!=SOURCE_SHA256
        or rank_reference.get("source_ZIP_sha256")!=
        {v:SOURCES[v]["sha256"] for v in VERSION_ORDER}
        or rwanda_reference.get("source_SHA256")!=
        {v:SOURCES[v]["sha256"] for v in ("23.1","24.1")}
        or rank_reference.get("historical_forecasts_issued_at_actual_origin") is not False
        or rank_reference.get("prospective_skill_claimed") is not False
        or rwanda_reference.get("new_prospective_forecasts_emitted")!=0
        or rank_reference.get("origin_year")!=ORIGIN
        or rank_reference.get("target_year")!=TARGET
        or len(issue_ids)!=N or len(set(issue_ids))!=N):
        raise ValueError("Official prior fixed-outcome vintage attribution invalid")
    old={cid:{y:d for y,d in hist.items() if y<=ORIGIN}
         for cid,hist in old_source.items()}
    new={cid:{y:d for y,d in hist.items() if y<=ORIGIN}
         for cid,hist in new_source.items()}
    if (set(old)!=set(new) or len(old)!=199
        or not set(issue_ids).issubset(old)
        or any(set(old[cid])!=set(new[cid]) for cid in old)
        or any(ORIGIN not in old[cid] or ORIGIN-1 not in old[cid]
               for cid in issue_ids)):
        raise ValueError("Official original 199 source countries or 196 issue cohort changed")
    edits=[]
    for cid in sorted(old):
        for year in sorted(old[cid]):
            before=old[cid][year]
            after=new[cid][year]
            if before==after:
                continue
            edits.append({
                "GWNO":cid,"year":year,"old_best_deaths":before,
                "new_best_deaths":after,
                "old_state":intensity_state(before),
                "new_state":intensity_state(after),
                "zero_low_reclassification":zero_low(before,after),
            })
    zedits=[e for e in edits if e["zero_low_reclassification"]]
    if (len(edits)!=rwanda_reference["historical_source_country_year_death_count_edit_n"]
        or sum(e["old_state"]!=e["new_state"] for e in edits)!=
        rwanda_reference["historical_source_four_state_label_edit_n"]):
        raise AssertionError("Original UCDP edit cardinality does not match source replay")
    predictions={}
    meta={}
    for z,o in ((0,0),(1,0),(0,1),(1,1)):
        # Combine Z and other source edits without dropping unedited histories.
        mixed={cid:dict(hist) for cid,hist in old.items()}
        for e in edits:
            if (e["zero_low_reclassification"] and z) or (
                not e["zero_low_reclassification"] and o):
                mixed[e["GWNO"]][e["year"]]=e["new_best_deaths"]
        forecast,details=four_state_forecast(
            mixed,ORIGIN,historical_rolling_diagnostic=True)
        if (set(forecast)!=set(issue_ids)
            or details["cutoff_max"]!=ORIGIN
            or details["training_countries"]!=199
            or details["eligible_countries"]!=N):
            raise AssertionError("Four-state H2 cohort or cutoff changed")
        predictions[f"{z}{o}"]=forecast
        meta[f"{z}{o}"]={
            "zero_low_source_revisions_enabled":bool(z),
            "other_source_revisions_enabled":bool(o),
            "global_four_state_transition_matrix_counts":details["global_4x4_transitions"],
        }
    prior={r["GWNO"]:r for r in rank_reference["country_observations"]}
    if set(prior)!=set(issue_ids):
        raise ValueError("Country-year observation label roster altered")
    rows=[]
    for cid in sorted(issue_ids):
        r=prior[cid]
        if (r["origin_year"]!=ORIGIN or r["target_year"]!=TARGET
            or r["label_best_26_1"] not in (0,1)):
            raise ValueError("Original frozen target label invalid")
        probs={key:predictions[key][cid]["p_intensity_markov"]
               for key in ("00","10","01","11")}
        if (not math.isclose(probs["00"],r["p_fourstate_origin23_1"],rel_tol=0,abs_tol=EPS)
            or not math.isclose(probs["11"],r["p_fourstate_origin24_1"],rel_tol=0,abs_tol=EPS)):
            raise AssertionError("Previous 196-country original model forecasts mismatch")
        zero,other=two_block_shapley(
            probs["00"],probs["10"],probs["01"],probs["11"])
        y=r["label_best_26_1"]
        brier={k:(p-y)**2 for k,p in probs.items()}
        zb,ob=two_block_shapley(
            brier["00"],brier["10"],brier["01"],brier["11"])
        rows.append({
            "GWNO":cid,"origin_year":ORIGIN,"target_year":TARGET,
            "origin_four_state_23_1":predictions["00"][cid]["origin_intensity_state"],
            "origin_four_state_24_1":predictions["11"][cid]["origin_intensity_state"],
            "fixed_outcome_26_1":y,
            "p_fourstate":probs,
            "p_revision_total":probs["11"]-probs["00"],
            "p_zero_low_shapley":zero,
            "p_other_source_shapley":other,
            "brier_fourstate":brier,
            "brier_revision_total":brier["11"]-brier["00"],
            "brier_zero_low_shapley":zb,
            "brier_other_source_shapley":ob,
            "own_zero_low_revisions":[{"year":e["year"],
                                       "old_best_deaths":e["old_best_deaths"],
                                       "new_best_deaths":e["new_best_deaths"]}
                                      for e in zedits if e["GWNO"]==cid],
        })
    rw=next(row for row in rows if row["GWNO"]==517)
    if (not math.isclose(rw["p_fourstate"]["00"],
                         rwanda_reference["p_fourstate_original"],abs_tol=EPS,rel_tol=0)
        or not math.isclose(rw["p_fourstate"]["11"],
                            rwanda_reference["p_fourstate_revised"],abs_tol=EPS,rel_tol=0)):
        raise AssertionError("Rwanda point estimate changed in full cohort source replay")
    stats={}
    for key in ("p_revision_total","p_zero_low_shapley","p_other_source_shapley",
                "brier_revision_total","brier_zero_low_shapley",
                "brier_other_source_shapley"):
        stats[key]={
            "mean":sum(r[key] for r in rows)/N,
            "max_abs":max(abs(r[key]) for r in rows),
            "nonzero_abs_gt_1e_10_n":sum(abs(r[key])>1e-10 for r in rows),
        }
    biggest=sorted(rows,key=lambda r:(-abs(r["p_zero_low_shapley"]),r["GWNO"]))
    direct=sorted({e["GWNO"] for e in zedits if e["GWNO"] in issue_ids})
    return {
        "schema":"idealab.psico.geo_h2_196_zero_low_source_factorial.v1",
        "status":"SHA_REPLAYED_RETROSPECTIVE_196_COUNTRY_SOURCE_SENSITIVITY_NOT_PROSPECTIVE",
        "source_versions":["23.1","24.1"],
        "source_SHA256":{"23.1":SOURCES["23.1"]["sha256"],
                         "24.1":SOURCES["24.1"]["sha256"]},
        "original_GEO2027_SHA256":SOURCE_SHA256,
        "origin_year":ORIGIN,"target_year":TARGET,
        "target_label_source":"26.1",
        "evaluation_countries":N,
        "training_source_countries":199,
        "total_revised_source_country_years":len(edits),
        "zero_low_revised_source_country_years":len(zedits),
        "zero_low_directly_revised_eval_GWNO":direct,
        "zero_low_directly_revised_eval_countries_n":len(direct),
        "all_zero_low_source_revisions":zedits,
        "four_factorial_scenarios":meta,
        "country_rows":rows,
        "aggregate":stats,
        "top20_absolute_zero_low_shapley_probability_countries":[
            {"GWNO":r["GWNO"],"p_zero_low_shapley":r["p_zero_low_shapley"],
             "own_zero_low_revisions":r["own_zero_low_revisions"]}
            for r in biggest[:20]],
        "n_forecasts_from_original_endpoints_reproduced":N*2,
        "no_prospective_forecasts_reissued":True,
        "historical_origins_issued_at_actual_date":False,
        "limitations":"2x2 exact factorization of five zero-to-low source edits and all other official source edits; Shapley is mechanical, not causal. Global transition priors propagate a country's edit to other countries. Fixed target labels 26.1, and official source releases postdate simulated origin 2021. Original 196-country cohort is not 196 independent samples.",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report",action="store_true")
    parser.add_argument("--print-report",action="store_true")
    args=parser.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("GEO2027 original forecast SHA changed")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    raw={v:request(SOURCES[v]["url"],MAX_DOWNLOAD) for v in ("23.1","24.1")}
    counts={v:parse_counts(raw[v],v) for v in raw}
    if any(sum(map(len,counts[v].values()))!=EXPECTED_ROWS[v] for v in counts):
        raise ValueError("Official source row counts changed")
    issue_ids=[r["country_id"] for r in json.loads(ISSUE.read_text())["countries"]]
    report=evaluate(
        counts["23.1"],counts["24.1"],
        json.loads(RANK_REFERENCE.read_text(encoding="utf-8")),
        json.loads(RWANDA_REFERENCE.read_text(encoding="utf-8")),
        issue_ids)
    payload=json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+"\n"
    if args.check_report and json.loads(OUTPUT.read_text(encoding="utf-8"))!=report:
        raise ValueError("Published source edit sensitivity report changed")
    if args.print_report:
        print("GEO_196_ZERO_LOW_BEGIN",flush=True)
        print(payload,end="")
        print("GEO_196_ZERO_LOW_END",flush=True)
    else:
        print(json.dumps({
            "zero_low_revisions":report["zero_low_revised_source_country_years"],
            "direct_countries":report["zero_low_directly_revised_eval_GWNO"],
            "max_abs_p_change":report["aggregate"]["p_zero_low_shapley"]["max_abs"],
        },sort_keys=True))


if __name__=="__main__":
    main()
