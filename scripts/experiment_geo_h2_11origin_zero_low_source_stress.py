#!/usr/bin/env python3
"""11 pseudo-origin GEO H2 zero/low source-vintage threshold sensitivity.

Official UCDP 23.1 vs 24.1 origins, 26.1 target labels; 2012..2022
origins and 2014..2024 targets. Both editions postdate some pseudoorigins,
so this is retrospective stress and NOT prospective forecast validation.
2x2 exact source interventions (Z: 0<->1..24; O: all other edits)
reconstruct the unchanged original four-state H2 model for each origin.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit as audit_issued,
)
from backtest_archived_country_vintages import SOURCES
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD, EXPECTED_ROWS, intensity_state, parse_counts,
    four_state_forecast,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
REFERENCE=ROOT/"data/geo-h2-origin-vintage-only-brier-rank.json"
RWANDA=ROOT/"data/geo-h2-196-zero-low-origin-vintage-sensitivity.json"
OUTPUT=ROOT/"data/geo-h2-11-origin-zero-low-sensitivity.json"
ORIGINS=tuple(range(2012,2023))
COHORT_N=196
TRAIN_N=199
VERSIONS=("23.1","24.1","26.1")
EPS=1e-10


def zero_low(a,b):
    if type(a) is not int or type(b) is not int or min(a,b)<0:
        raise ValueError("UCDP best-count input not a nonnegative integer")
    return {intensity_state(a),intensity_state(b)}=={0,1}


def shapley(a,b,c,d):
    z=((b-a)+(d-c))/2
    o=((c-a)+(d-b))/2
    if not math.isclose(z+o,d-a,abs_tol=1e-12,rel_tol=0):
        raise AssertionError("Two-factor source attribution not additive")
    return z,o


def edit_list(old,new,origin):
    if set(old)!=set(new) or len(old)!=TRAIN_N:
        raise ValueError("Country training universe mismatch across editions")
    edits=[]
    for cid in sorted(old):
        past_old={y:v for y,v in old[cid].items() if y<=origin}
        past_new={y:v for y,v in new[cid].items() if y<=origin}
        if past_old.keys()!=past_new.keys():
            raise ValueError("Historically comparable country-years differ")
        for year,a in sorted(past_old.items()):
            b=past_new[year]
            if a!=b:
                edits.append({"GWNO":cid,"year":year,"old_best_deaths":a,
                    "new_best_deaths":b,"zero_low":zero_low(a,b),
                    "state_changed":intensity_state(a)!=intensity_state(b)})
    return edits


def analyze(sources,reference,anchor,ids):
    if (reference.get("schema")!="idealab.psico.geo_h2_origin_vintage_only_brier_rank.v1"
        or reference.get("historical_issued_asof_evidence") is not False
        or reference.get("old_origin_release")!="23.1"
        or reference.get("later_origin_release")!="24.1"
        or reference.get("held_fixed_outcome_release")!="26.1"
        or reference.get("historical_targets")!=list(range(2014,2025))
        or reference.get("country_n")!=COHORT_N
        or reference.get("official_UCDP_ZIP_sha256")["23.1"]!=SOURCES["23.1"]["sha256"]
        or reference.get("official_UCDP_ZIP_sha256")["24.1"]!=SOURCES["24.1"]["sha256"]
        or reference.get("official_UCDP_ZIP_sha256")["26.1"]!=SOURCES["26.1"]["sha256"]
        or reference.get("original_GEO2027_issue_SHA256")!=SOURCE_SHA256
        or anchor.get("schema")!="idealab.psico.geo_h2_196_zero_low_source_factorial.v1"
        or anchor.get("historical_origins_issued_at_actual_date") is not False
        or anchor.get("origin_year")!=2021
        or anchor.get("target_year")!=2023
        or anchor.get("source_SHA256")!={v:SOURCES[v]["sha256"] for v in ("23.1","24.1")}
        or len(ids)!=COHORT_N or len(set(ids))!=COHORT_N
        or any(len(sources[v])!=TRAIN_N for v in ("23.1","24.1"))):
        raise ValueError("Archived source or prior experimental contract changed")
    scores_ref={r["target_year"]:r for r in reference["annual"]}
    rows=[]
    for origin in ORIGINS:
        target=origin+2
        edits=edit_list(sources["23.1"],sources["24.1"],origin)
        zero_edits=[e for e in edits if e["zero_low"]]
        f={}
        for z,o in ((0,0),(1,0),(0,1),(1,1)):
            mixed={cid:{y:v for y,v in hist.items() if y<=origin}
                   for cid,hist in sources["23.1"].items()}
            for e in edits:
                if (e["zero_low"] and z) or (not e["zero_low"] and o):
                    mixed[e["GWNO"]][e["year"]]=e["new_best_deaths"]
            pred,meta=four_state_forecast(
                mixed,origin,historical_rolling_diagnostic=True)
            if (meta["cutoff_max"]!=origin
                or meta["training_countries"]!=TRAIN_N
                or set(pred)!=set(ids)):
                raise AssertionError("Origin cutoff, 199 training or 196 scored changed")
            f[f"{z}{o}"]=pred
        y={cid:int(sources["26.1"][cid][target]>=25) for cid in ids}
        country_rows=[]
        for cid in sorted(ids):
            p={key:f[key][cid]["p_intensity_markov"]
               for key in ("00","10","01","11")}
            zp,op=shapley(p["00"],p["10"],p["01"],p["11"])
            b={key:(p[key]-y[cid])**2 for key in p}
            zb,ob=shapley(b["00"],b["10"],b["01"],b["11"])
            country_rows.append({
                "GWNO":cid,"official_outcome_26_1":y[cid],
                "p23_1":p["00"],"p24_1":p["11"],
                "delta_p":p["11"]-p["00"],
                "zero_low_source_shapley_p":zp,
                "other_source_shapley_p":op,
                "zero_low_source_shapley_brier":zb,
                "other_source_shapley_brier":ob,
                "origin_state_23_1":f["00"][cid]["origin_intensity_state"],
                "origin_state_24_1":f["11"][cid]["origin_intensity_state"],
            })
        mean=lambda field:sum(r[field] for r in country_rows)/COHORT_N
        old_brier=sum((r["p23_1"]-r["official_outcome_26_1"])**2
                      for r in country_rows)/COHORT_N
        new_brier=sum((r["p24_1"]-r["official_outcome_26_1"])**2
                      for r in country_rows)/COHORT_N
        fixed=scores_ref[target]
        if (not math.isclose(old_brier,
                fixed["old_origin_fixed_target_26_1_brier"]["four_state_intensity"],
                abs_tol=EPS,rel_tol=0)
            or not math.isclose(new_brier,
                fixed["new_origin_fixed_target_26_1_brier"]["four_state_intensity"],
                abs_tol=EPS,rel_tol=0)
            or not math.isclose(mean("zero_low_source_shapley_brier")
                    +mean("other_source_shapley_brier"),
                new_brier-old_brier,abs_tol=EPS,rel_tol=0)):
            raise AssertionError("Original 11-year ranking experiment not reproduced")
        if origin==2021:
            check={r["GWNO"]:r for r in anchor["country_rows"]}
            if len(check)!=COHORT_N or any(
                not math.isclose(r["p23_1"],check[r["GWNO"]]["p_fourstate"]["00"],abs_tol=EPS,rel_tol=0)
                or not math.isclose(r["p24_1"],check[r["GWNO"]]["p_fourstate"]["11"],abs_tol=EPS,rel_tol=0)
                or not math.isclose(r["zero_low_source_shapley_p"],
                    check[r["GWNO"]]["p_zero_low_shapley"],abs_tol=EPS,rel_tol=0)
                for r in country_rows):
                raise AssertionError("2021 source-threshold study not exactly reconstructed")
        direct=sorted({e["GWNO"] for e in zero_edits if e["GWNO"] in ids})
        rows.append({
            "origin_year":origin,"target_year":target,
            "source_total_revision_n":len(edits),
            "source_zero_low_revision_n":len(zero_edits),
            "source_zero_low_direct_evaluation_GWNO":direct,
            "source_zero_low_direct_evaluation_country_n":len(direct),
            "origin_zero_low_reclassified_GWNO":sorted(cid for cid in ids
                if {f["00"][cid]["origin_intensity_state"],
                    f["11"][cid]["origin_intensity_state"]}=={0,1}),
            "mean_p_zero_low_shapley":mean("zero_low_source_shapley_p"),
            "mean_p_other_source_shapley":mean("other_source_shapley_p"),
            "max_abs_p_zero_low_shapley":max(abs(r["zero_low_source_shapley_p"])
                                              for r in country_rows),
            "mean_brier_zero_low_shapley":mean("zero_low_source_shapley_brier"),
            "mean_brier_other_source_shapley":mean("other_source_shapley_brier"),
            "four_state_brier_origin23_1":old_brier,
            "four_state_brier_origin24_1":new_brier,
            "max_abs_p_any_source_revision":max(abs(r["delta_p"]) for r in country_rows),
            "nonzero_zero_low_spillover_country_n":sum(
                abs(r["zero_low_source_shapley_p"])>1e-10 for r in country_rows
                if r["GWNO"] not in direct),
            "source_zero_low_revisions":zero_edits,
            "top5_abs_p_zero_low":sorted(
                [{"GWNO":r["GWNO"],
                  "zero_low_source_shapley_p":r["zero_low_source_shapley_p"]}
                 for r in country_rows],
                key=lambda x:(-abs(x["zero_low_source_shapley_p"]),x["GWNO"]))[:5],
            "country_rows":country_rows,
        })
    pooled_old=sum(r["four_state_brier_origin23_1"] for r in rows)/len(rows)
    pooled_new=sum(r["four_state_brier_origin24_1"] for r in rows)/len(rows)
    return {
        "schema":"idealab.psico.geo_h2_11_origin_zero_low_source_factorial.v1",
        "status":"RETROSPECTIVE_11_YEAR_UCDP_THRESHOLD_STRESS_NOT_PROSPECTIVE",
        "source_editions":{"origin_old":"23.1","origin_new":"24.1","target":"26.1"},
        "source_SHA256":{v:SOURCES[v]["sha256"] for v in VERSIONS},
        "original_GEO2027_SHA256":SOURCE_SHA256,
        "origin_years":list(ORIGINS),
        "unique_target_years":[o+2 for o in ORIGINS],
        "evaluation_GWNO_n":COHORT_N,
        "training_source_country_n":TRAIN_N,
        "country_year_n":len(ORIGINS)*COHORT_N,
        "annual":rows,
        "overall_unique_direct_zero_low_source_revisions":len({
            (x["GWNO"],x["year"]) for row in rows
            for x in row["source_zero_low_revisions"]}),
        "annual_origins_with_at_least_one_zero_low_edit_n":sum(
            r["source_zero_low_revision_n"]>0 for r in rows),
        "annual_origins_with_origin_year_zero_low_edit_n":sum(
            len(r["origin_zero_low_reclassified_GWNO"])>0 for r in rows),
        "max_country_absolute_p_zero_low_effect":max(
            r["max_abs_p_zero_low_shapley"] for r in rows),
        "pooled_origin23_1_four_state_brier":pooled_old,
        "pooled_origin24_1_four_state_brier":pooled_new,
        "pooled_zero_low_effect_brier":sum(
            r["mean_brier_zero_low_shapley"] for r in rows)/len(rows),
        "pooled_other_source_effect_brier":sum(
            r["mean_brier_other_source_shapley"] for r in rows)/len(rows),
        "frozen_2027_2028_forecasts_modified":False,
        "actual_historical_asof_issues_demonstrated":False,
        "limitations":"Same two late-published source releases are compared across 11 pseudo-origins; repeated histories accumulate revisions, so years are not independent and this is not 11 new source-edition pairs. Source model unmodified, target labels fixed at 26.1. Country probability changes include shared-global-prior propagation.",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    ap.add_argument("--print-report",action="store_true")
    args=ap.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Original GEO2027 source issue altered")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    raws={v:request(SOURCES[v]["url"],MAX_DOWNLOAD) for v in VERSIONS}
    sources={v:parse_counts(raws[v],v) for v in VERSIONS}
    if any(sum(map(len,sources[v].values()))!=EXPECTED_ROWS[v] for v in VERSIONS):
        raise ValueError("UCDP country-year source row count changed")
    ids=[r["country_id"] for r in json.loads(ISSUE.read_text())["countries"]]
    report=analyze(
        sources,json.loads(REFERENCE.read_text(encoding="utf-8")),
        json.loads(RWANDA.read_text(encoding="utf-8")),ids)
    payload=json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    if args.check_report and json.loads(OUTPUT.read_text(encoding="utf-8"))!=report:
        raise ValueError("Stored 11-origin threshold study no longer replays")
    if args.print_report:
        print("GEO_11_ORIGINS_BEGIN",flush=True)
        print(payload,end="")
        print("GEO_11_ORIGINS_END",flush=True)
    else:
        print(json.dumps({
            "affected_origins":report["annual_origins_with_at_least_one_zero_low_edit_n"],
            "origin_state_change_years":report["annual_origins_with_origin_year_zero_low_edit_n"],
            "max_probability_shapley":report["max_country_absolute_p_zero_low_effect"],
        },sort_keys=True))


if __name__=="__main__":
    main()
