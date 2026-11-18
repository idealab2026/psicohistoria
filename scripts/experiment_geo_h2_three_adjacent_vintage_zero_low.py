#!/usr/bin/env python3
"""GEO H2 fixed-label stress across three consecutive UCDP archival pairs.

33 pseudo-origin × pair comparisons; archive-vintage effects are not
independent and the archive editions postdate the early simulated origins.
For each pair and origin, exact 2x2 source intervention (Z=zero<->1..24
count revisions, O=all other revisions), fixed H2 4-state estimator.
The shared 26.1 outcome labels never vary. No prospective reissuance.
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
    MAX_DOWNLOAD, EXPECTED_ROWS, VERSION_ORDER, intensity_state,
    parse_counts, four_state_forecast,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
ANCHOR=ROOT/"data/geo-h2-origin-vintage-only-brier-rank.json"
PAIRS=(("23.1","24.1"),("24.1","25.1"),("25.1","26.1"))
ORIGINS=tuple(range(2012,2023))
TARGET_RELEASE="26.1"
COHORT=196
TRAIN=199
OUTPUT=ROOT/"data/geo-h2-three-adjacent-vintage-zero-low-11-origin.json"
EPS=1e-10


def zero_low(a,b):
    if type(a) is not int or type(b) is not int or a<0 or b<0:
        raise ValueError("Invalid UCDP best fatality count")
    return {intensity_state(a),intensity_state(b)}=={0,1}


def source_edits(old,new,origin):
    if set(old)!=set(new) or len(old)!=TRAIN:
        raise ValueError("Original source 199-country training roster not comparable")
    edits=[]
    for cid in sorted(old):
        a={y:v for y,v in old[cid].items() if y<=origin}
        b={y:v for y,v in new[cid].items() if y<=origin}
        if set(a)!=set(b):
            raise ValueError("Source country-year coverage changed: cannot impute 0")
        for y,val in sorted(a.items()):
            if val!=b[y]:
                edits.append((cid,y,val,b[y],zero_low(val,b[y]),
                              intensity_state(val)!=intensity_state(b[y])))
    return edits


def shapley(p00,p10,p01,p11):
    z=((p10-p00)+(p11-p01))/2
    o=((p01-p00)+(p11-p10))/2
    if not math.isclose(z+o,p11-p00,abs_tol=1e-12,rel_tol=0):
        raise AssertionError("Source attribution arithmetic mismatch")
    return z,o


def analyze(data,issue_ids,anchor):
    if (len(issue_ids)!=COHORT or len(set(issue_ids))!=COHORT
        or anchor.get("schema")!="idealab.psico.geo_h2_origin_vintage_only_brier_rank.v1"
        or anchor.get("historical_issued_asof_evidence") is not False
        or anchor.get("country_n")!=COHORT
        or anchor.get("old_origin_release")!="23.1"
        or anchor.get("later_origin_release")!="24.1"
        or anchor.get("held_fixed_outcome_release")!=TARGET_RELEASE
        or anchor.get("original_GEO2027_issue_SHA256")!=SOURCE_SHA256
        or anchor.get("official_UCDP_ZIP_sha256")!=
            {v:SOURCES[v]["sha256"] for v in VERSION_ORDER}):
        raise ValueError("Original registered GEO H2 archival anchors not verified")
    original={f["target_year"]:f for f in anchor["annual"]}
    folds=[]
    all_edits={}
    for old_v,new_v in PAIRS:
        pair=old_v+"->"+new_v
        for origin in ORIGINS:
            target=origin+2
            edits=source_edits(data[old_v],data[new_v],origin)
            zero=[e for e in edits if e[4]]
            forecasts={}
            # Count edits, not one per source event: globally fitted prior
            # can propagate source changes to all 196 scored countries.
            for z,o in ((0,0),(1,0),(0,1),(1,1)):
                mixed={cid:{y:v for y,v in h.items() if y<=origin}
                       for cid,h in data[old_v].items()}
                for cid,yr,a,b,is_z,changed_state in edits:
                    if (is_z and z) or (not is_z and o):
                        mixed[cid][yr]=b
                forecast,meta=four_state_forecast(
                    mixed,origin,historical_rolling_diagnostic=True)
                if (meta["cutoff_max"]!=origin
                    or meta["training_countries"]!=TRAIN
                    or meta["eligible_countries"]!=COHORT
                    or set(forecast)!=set(issue_ids)):
                    raise AssertionError("Source or cutoff changed model cohort")
                forecasts[f"{z}{o}"]=forecast
            vals=[]
            for cid in sorted(issue_ids):
                y=int(data[TARGET_RELEASE][cid][target]>=25)
                probs={k:forecasts[k][cid]["p_intensity_markov"]
                       for k in ("00","10","01","11")}
                zp,op=shapley(*[probs[k] for k in ("00","10","01","11")])
                brier={k:(probs[k]-y)**2 for k in probs}
                zb,ob=shapley(*[brier[k] for k in ("00","10","01","11")])
                vals.append({
                    "GWNO":cid,"p_old":probs["00"],"p_new":probs["11"],
                    "delta_p":probs["11"]-probs["00"],
                    "zero_low_p":zp,"other_p":op,
                    "zero_low_brier":zb,"other_brier":ob,
                    "origin_state_old":forecasts["00"][cid]["origin_intensity_state"],
                    "origin_state_new":forecasts["11"][cid]["origin_intensity_state"],
                })
            mean=lambda k:sum(x[k] for x in vals)/COHORT
            old_brier=sum((r["p_old"]-int(data[TARGET_RELEASE][r["GWNO"]][target]>=25))**2
                          for r in vals)/COHORT
            new_brier=sum((r["p_new"]-int(data[TARGET_RELEASE][r["GWNO"]][target]>=25))**2
                          for r in vals)/COHORT
            if not math.isclose(mean("zero_low_brier")+mean("other_brier"),
                                new_brier-old_brier,rel_tol=0,abs_tol=EPS):
                raise AssertionError("Four-scenario Brier decomposition failed")
            if pair=="23.1->24.1":
                ref=original[target]
                if (not math.isclose(old_brier,
                     ref["old_origin_fixed_target_26_1_brier"]["four_state_intensity"],
                     rel_tol=0,abs_tol=EPS)
                    or not math.isclose(new_brier,
                     ref["new_origin_fixed_target_26_1_brier"]["four_state_intensity"],
                     rel_tol=0,abs_tol=EPS)):
                    raise AssertionError("Previous 11-year original Brier cannot be reproduced")
            key=(old_v,new_v)
            all_edits.setdefault(key,set()).update((cid,year) for cid,year,a,b,is_z,c in zero)
            direct={x[0] for x in zero if x[0] in issue_ids}
            top=sorted(vals,key=lambda r:(-abs(r["zero_low_p"]),r["GWNO"]))[:5]
            folds.append({
                "source_pair":pair,"origin_year":origin,"target_year":target,
                "training_death_count_revision_n":len(edits),
                "training_four_state_revision_n":sum(e[5] for e in edits),
                "training_zero_low_revision_n":len(zero),
                "training_zero_low_events":[
                    {"GWNO":cid,"year":yr,"old":a,"new":b}
                    for cid,yr,a,b,iz,sc in zero],
                "direct_zero_low_scored_GWNO":sorted(direct),
                "origin_zero_low_reclassified_GWNO":sorted(
                    r["GWNO"] for r in vals if
                    {r["origin_state_old"],r["origin_state_new"]}=={0,1}),
                "mean_shapley_p_zero_low":mean("zero_low_p"),
                "mean_shapley_brier_zero_low":mean("zero_low_brier"),
                "mean_shapley_brier_other":mean("other_brier"),
                "old_four_state_brier_fixed_26_1":old_brier,
                "new_four_state_brier_fixed_26_1":new_brier,
                "max_abs_shapley_p_zero_low":max(abs(v["zero_low_p"]) for v in vals),
                "top5_abs_zero_low":[
                    {"GWNO":x["GWNO"],"effect":x["zero_low_p"],
                     "p_old":x["p_old"],"p_new":x["p_new"],
                     "origin_state_old":x["origin_state_old"],
                     "origin_state_new":x["origin_state_new"]}
                    for x in top],
            })
    pair_summaries=[]
    for old,new in PAIRS:
        pair=old+"->"+new
        fs=[f for f in folds if f["source_pair"]==pair]
        pair_summaries.append({
            "pair":pair,"fold_n":len(fs),
            "unique_zero_low_revised_training_country_years":len(all_edits[old,new]),
            "origins_with_any_zero_low_revision_n":sum(f["training_zero_low_revision_n"]>0 for f in fs),
            "origins_with_zero_low_initial_state_revision_n":sum(
                bool(f["origin_zero_low_reclassified_GWNO"]) for f in fs),
            "max_abs_zero_low_probability_attribution":max(
                f["max_abs_shapley_p_zero_low"] for f in fs),
            "mean_brier_zero_low_attribution":sum(
                f["mean_shapley_brier_zero_low"] for f in fs)/len(fs),
            "mean_brier_other_attribution":sum(
                f["mean_shapley_brier_other"] for f in fs)/len(fs),
            "mean_brier_total_revision":sum(
                f["new_four_state_brier_fixed_26_1"]-
                f["old_four_state_brier_fixed_26_1"] for f in fs)/len(fs),
        })
    return {
        "schema":"idealab.psico.geo_h2_three_adjacent_vintage_zero_low_11_origin.v1",
        "status":"SHA_REPLAYED_RETROSPECTIVE_SOURCE_STRESS_NOT_PROSPECTIVE",
        "source_SHA256":{v:SOURCES[v]["sha256"] for v in VERSION_ORDER},
        "original_GEO2027_SHA256":SOURCE_SHA256,
        "source_pairs":[list(pair) for pair in PAIRS],
        "origin_years":list(ORIGINS),"target_years":[y+2 for y in ORIGINS],
        "fixed_target_release":TARGET_RELEASE,
        "scored_GWNO_n":COHORT,"training_source_countries_n":TRAIN,
        "origin_pair_folds_n":len(folds),
        "country_year_pair_evaluations_n":len(folds)*COHORT,
        "pairs":pair_summaries,"folds":folds,
        "historical_asof_issues_genuinely_timestamped":False,
        "prospective_GEO2027_GEO2028_reissued":False,
        "limitations":"All source editions 23.1..26.1 postdate many pseudo-origins; neither the 33 fold comparisons nor the 3 adjacent edition comparisons are independent, and the held-fixed 26.1 outcome labels share the final source vintage with one origin pair. This measures archive-revision sensitivity, not unbiased forecast skill or causal source effects.",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    ap.add_argument("--print-report",action="store_true")
    args=ap.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Prospective issued GEO2027 vector altered")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    raw={v:request(SOURCES[v]["url"],MAX_DOWNLOAD) for v in VERSION_ORDER}
    data={v:parse_counts(raw[v],v) for v in VERSION_ORDER}
    if any(sum(map(len,data[v].values()))!=EXPECTED_ROWS[v] for v in VERSION_ORDER):
        raise ValueError("Original UCDP source ZIP row counts changed")
    ids=[r["country_id"] for r in json.loads(ISSUE.read_text())["countries"]]
    report=analyze(data,ids,json.loads(ANCHOR.read_text(encoding="utf-8")))
    payload=json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    if args.check_report and json.loads(OUTPUT.read_text(encoding="utf-8"))!=report:
        raise ValueError("Stored 33-fold source sensitivity report differs from SHA-replay")
    if args.print_report:
        print("GEO_33FOLD_BEGIN",flush=True)
        print(payload,end="")
        print("GEO_33FOLD_END",flush=True)
    else:
        print(json.dumps({"folds":len(report["folds"]),
                          "pairs":report["pairs"]},sort_keys=True))


if __name__=="__main__":
    main()
