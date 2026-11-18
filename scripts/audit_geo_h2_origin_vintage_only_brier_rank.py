#!/usr/bin/env python3
"""Source-vintage factorial decomposition: origin-version vs outcome-version.

For 11 historical H2 targets 2014--2024, both origin-release tracks are
evaluated on the SAME official 26.1 outcome labels. The primary track uses
origin edition 23.1 and the later track 24.1. The fixed origin23.1 target
25.1->26.1 label-only Brier shifts are taken from a source-replayed, already
locked report. Hence score(origin24,outcome26)-score(origin23,outcome26) is
origin-vintage-only score drift, not target label drift. Nothing was genuinely
issued at the historical forecast dates: editions postdate those dates.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ROLLING=ROOT/"data/geo-h2-rolling-historical-2014-2025.json"
FIXED=ROOT/"data/geo-h2-fixed-vector-2526-outcome-revision.json"
REPORT=ROOT/"data/geo-h2-origin-vintage-only-brier-rank.json"
FIELDS={
    "original_binary":("comparison","scenarios","best","original_binary","brier"),
    "four_state_intensity":("comparison","scenarios","best","four_state_intensity","brier"),
    "global_markov":("baseline_scores","best","global_markov_h2","brier"),
    "global_prevalence_5y":("baseline_scores","best","global_prevalence_5y","brier"),
}
SHIFT={
    "original_binary":"p_original_binary",
    "four_state_intensity":"p_intensity_markov",
    "global_markov":"p_global_markov",
    "global_prevalence_5y":"p_baseline_global_5y",
}
YEARS=tuple(range(2014,2025))


def rank(scores):
    return sorted(FIELDS,key=lambda key:(scores[key],key))


def scores(fold):
    out={}
    for model,parts in FIELDS.items():
        obj=fold
        for k in parts:
            obj=obj[k]
        if type(obj) not in (int,float) or not math.isfinite(obj) or not 0<=obj<=1:
            raise ValueError("Non-finite or impossible historical Brier")
        out[model]=obj
    return out


def contrast(early,late):
    a=rank(early)
    b=rank(late)
    pair_flips=[]
    for i,one in enumerate(sorted(FIELDS)):
        for two in sorted(FIELDS)[i+1:]:
            old=early[one]-early[two]
            new=late[one]-late[two]
            if (old==0)!=(new==0) or old*new<0:
                pair_flips.append({
                    "model_a":one,"model_b":two,
                    "delta_origin23_1":old,"delta_origin24_1":new,
                })
    return {
        "origin23_1_rank":a,"origin24_1_rank":b,
        "rank_changed":a!=b,"pairwise_reversals_or_tie_changes":pair_flips,
        "winner_origin23_1":a[0],"winner_origin24_1":b[0],
        "winner_changed":a[0]!=b[0],
    }


def audit(rolling,fixed):
    if (rolling.get("schema")!="idealab.psico.geo_h2_rolling_historical_2014_2025.v1"
        or fixed.get("schema")!="idealab.psico.geo_h2_fixed_origin_outcome_revision_brier.v1"
        or fixed.get("status")!="OBSERVED_EX_POST_BRIER_LABEL_REVISION_FIXED_MODEL_NOT_PROSPECTIVE"
        or rolling.get("not_prospective_or_independently_timestamped_skill") is not True
        or rolling.get("primary_frozen_2027_probabilities_changed") is not False
        or fixed.get("original_2027_2028_predictions_modified") is not False
        or rolling.get("original_GEO2027_SHA256")!=fixed.get("original_GEO2027_SHA256")
        or rolling.get("source_archives_sha256")!=fixed.get("source_archives_sha256")
        or fixed.get("years")!=list(YEARS)
        or fixed.get("unique_country_year_n")!=196*len(YEARS)
        or rolling.get("fixed_original_GWNO_n")!=196
        or rolling.get("horizon_years")!=2):
        raise ValueError("Historical source/forecast provenance guard")
    old_folds=rolling["primary_unique_year_series"]["folds"]
    late_folds=rolling["later_vintage_same_year_sensitivity_NOT_second_sample"]["folds"]
    deltas=fixed["yearly"]
    if len(old_folds)!=12 or len(late_folds)!=12 or len(deltas)!=len(YEARS):
        raise ValueError("Wrong number of annual source observations")
    oldmap={f["target_year"]:f for f in old_folds}
    latemap={f["target_year"]:f for f in late_folds}
    deltmap={f["target_year"]:f for f in deltas}
    if (len(oldmap)!=12 or len(latemap)!=12 or len(deltmap)!=len(YEARS)
        or set(oldmap)!=set(range(2014,2026))
        or set(latemap)!=set(range(2014,2026))
        or set(deltmap)!=set(YEARS)):
        raise ValueError("Missing/duplicated historical calendar year")
    sums={key:{"origin23_1":0.,"origin24_1":0.,"outcome_label_shift":0.} for key in FIELDS}
    yearly=[]
    for year in YEARS:
        orig,later,delta=oldmap[year],latemap[year],deltmap[year]
        if (orig["origin_release"]!="23.1"
            or later["origin_release"]!="24.1"
            or orig["outcome_release"]!="25.1"
            or later["outcome_release"]!="26.1"
            or delta["old_target_release"]!="25.1"
            or delta["new_target_release"]!="26.1"
            or delta["frozen_origin_release"]!="23.1"
            or orig["country_n"]!=196 or later["country_n"]!=196
            or delta["country_n"]!=196
            or orig["origin_year"]!=year-2
            or later["origin_year"]!=year-2
            or delta["origin_year"]!=year-2
            or delta["label_revisions_n"]!=len(delta["revised_countries"])):
            raise ValueError("Incorrect 2x2 fixed cohorts, origin or target source editions")
        origin23_target25=scores(orig)
        origin24_target26=scores(later)
        shift=delta["observed_brier_shift_new_minus_old"]
        if set(shift)!=set(SHIFT.values()):
            raise ValueError("Missing exactly paired fixed label-only score changes")
        origin23_target26={}
        for name in FIELDS:
            change=shift[SHIFT[name]]
            if type(change) not in (int,float) or not math.isfinite(change):
                raise ValueError("Non-finite or missing label-only revision score")
            value=origin23_target25[name]+change
            if not -1e-12<=value<=1+1e-12:
                raise ValueError("Invalid Brier after target outcome revision")
            if abs(change)>delta["label_revisions_n"]/196+1e-12:
                raise ValueError("Label revision exceeds mathematical bound")
            origin23_target26[name]=value
            sums[name]["origin23_1"]+=value
            sums[name]["origin24_1"]+=origin24_target26[name]
            sums[name]["outcome_label_shift"]+=change
        origin_only={name:origin24_target26[name]-origin23_target26[name] for name in FIELDS}
        combined={name:origin24_target26[name]-origin23_target25[name] for name in FIELDS}
        for name in FIELDS:
            if not math.isclose(
                origin_only[name]+shift[SHIFT[name]],
                combined[name],rel_tol=0,abs_tol=1e-12):
                raise AssertionError("2x2 factorial score decomposition fails")
        yearly.append({
            "target_year":year,"origin_year":year-2,"country_n":196,
            "old_origin_release":"23.1","new_origin_release":"24.1",
            "fixed_target_release":"26.1",
            "old_origin_old_target_25_1_brier":origin23_target25,
            "old_origin_fixed_target_26_1_brier":origin23_target26,
            "new_origin_fixed_target_26_1_brier":origin24_target26,
            "outcome_label_only_brier_shift":{name:shift[SHIFT[name]] for name in FIELDS},
            "origin_vintage_only_brier_shift":origin_only,
            "combined_old_to_later_brier_shift":combined,
            "outcome_label_revisions_n":delta["label_revisions_n"],
            **contrast(origin23_target26,origin24_target26),
        })
    n=len(YEARS)
    avg_old={key:sums[key]["origin23_1"]/n for key in FIELDS}
    avg_late={key:sums[key]["origin24_1"]/n for key in FIELDS}
    pooled_origin={key:avg_late[key]-avg_old[key] for key in FIELDS}
    for key in FIELDS:
        if not math.isclose(sums[key]["outcome_label_shift"]/n,
                             fixed["observed_brier_shift_new_minus_old"][SHIFT[key]],
                             rel_tol=0,abs_tol=1e-12):
            raise ValueError("Pooled target-only label change differs from official replay")
    # The previous fixed-label comparison also used 11 years with 196 GWNO.
    return {
        "schema":"idealab.psico.geo_h2_origin_vintage_only_brier_rank.v1",
        "status":"RETROSPECTIVE_ORIGIN_VINTAGE_ONLY_SCORE_ATTRIBUTION_NOT_PROSPECTIVE",
        "source_rolling_report":"data/geo-h2-rolling-historical-2014-2025.json",
        "source_fixed_outcome_label_report":"data/geo-h2-fixed-vector-2526-outcome-revision.json",
        "official_UCDP_ZIP_sha256":fixed["source_archives_sha256"],
        "original_GEO2027_issue_SHA256":fixed["original_GEO2027_SHA256"],
        "old_origin_release":"23.1","later_origin_release":"24.1",
        "held_fixed_outcome_release":"26.1",
        "historical_targets":list(YEARS),"country_n":196,"pooled_country_year_n":196*n,
        "annual_winner_changes_n":sum(z["winner_changed"] for z in yearly),
        "annual_ranking_changes_n":sum(z["rank_changed"] for z in yearly),
        "annual_pairwise_reversal_or_tie_count":sum(len(z["pairwise_reversals_or_tie_changes"]) for z in yearly),
        "pooled_old_origin_fixed_outcome_Brier":avg_old,
        "pooled_new_origin_fixed_outcome_Brier":avg_late,
        "pooled_origin_only_Brier_shift":pooled_origin,
        "pooled_ranking":contrast(avg_old,avg_late),
        "annual":yearly,
        "no_2027_2028_forecasts_reissued":True,
        "historical_issued_asof_evidence":False,
        "limitations":"Both origin releases were retrospective for many years; this isolates revision of the origin dataset holding outcome release 26.1 fixed, not model hyperparameter tuning, causal attribution within a source revision, or prospective skill. Country-years correlated; 2025 excluded from pooled results.",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    ap.add_argument("--print-report",action="store_true")
    args=ap.parse_args()
    result=audit(json.loads(ROLLING.read_text(encoding="utf-8")),
                 json.loads(FIXED.read_text(encoding="utf-8")))
    payload=json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    if args.check_report and json.loads(REPORT.read_text(encoding="utf-8"))!=result:
        raise ValueError("Frozen origin-vintage factorial ranking report differs")
    if args.print_report:
        print("GEO_ORIGIN_VINTAGE_RANK_BEGIN",flush=True)
        print(payload,end="")
        print("GEO_ORIGIN_VINTAGE_RANK_END",flush=True)
    else:
        print(json.dumps({
            "annual_winner_changes":result["annual_winner_changes_n"],
            "pooled_origin_only_Brier_shift":result["pooled_origin_only_Brier_shift"],
        },sort_keys=True))


if __name__=="__main__":
    main()
