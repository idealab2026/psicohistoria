#!/usr/bin/env python3
"""Compare *identical* historical model score vectors under two UCDP labels.

Inputs: the previously source-replayed fixed-vector 25.1->26.1 score
attributions and the distinct rolling 2014..2025 audit's 25.1 primary
historical scores. Pool ONLY 2014..2024, not 2025. This is retrospective
source sensitivity; the pseudo-origin source editions postdate historical
forecast dates. No new forecast, no re-fitting, no prospective skill claim.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ATTRIBUTION=ROOT/"data/geo-h2-fixed-vector-2526-outcome-revision.json"
ROLLING=ROOT/"data/geo-h2-rolling-historical-2014-2025.json"
OUTPUT=ROOT/"data/geo-h2-2526-fixed-brier-ranking-stability.json"
MODELS={
    "p_original_binary":("comparison","scenarios","best","original_binary","brier"),
    "p_intensity_markov":("comparison","scenarios","best","four_state_intensity","brier"),
    "p_global_markov":("baseline_scores","best","global_markov_h2","brier"),
    "p_baseline_global_5y":("baseline_scores","best","global_prevalence_5y","brier"),
}
EXPECTED_YEARS=list(range(2014,2025))


def _value(fold,field):
    obj=fold
    for part in MODELS[field]:
        obj=obj[part]
    if type(obj) not in (int,float) or not math.isfinite(obj) or not 0<=obj<=1:
        raise ValueError("Invalid original historical Brier")
    return obj


def _rank(scores):
    return sorted(scores,key=lambda key:(scores[key],key))


def _margins(scores):
    rank=_rank(scores)
    return [
        {"better":rank[i],"worse":rank[i+1],
         "margin":scores[rank[i+1]]-scores[rank[i]]}
        for i in range(len(rank)-1)
    ]


def _compare(before,after):
    old=_rank(before)
    new=_rank(after)
    reversed_pairs=[]
    keys=sorted(MODELS)
    for i,a in enumerate(keys):
        for b in keys[i+1:]:
            x=before[a]-before[b]
            y=after[a]-after[b]
            if (x==0)!=(y==0) or x*y<0:
                reversed_pairs.append({"model_a":a,"model_b":b,
                                       "old_delta":x,"new_delta":y})
    return {"ranking_old":old,"ranking_new":new,
            "ranking_changed":old!=new,
            "pairwise_order_or_tie_reversed":reversed_pairs,
            "adjacent_margins_old":_margins(before),
            "adjacent_margins_new":_margins(after)}


def analyze(attribution,rolling):
    if (attribution.get("schema")!="idealab.psico.geo_h2_fixed_origin_outcome_revision_brier.v1"
        or attribution.get("status")!="OBSERVED_EX_POST_BRIER_LABEL_REVISION_FIXED_MODEL_NOT_PROSPECTIVE"
        or attribution.get("historical_model_issued_at_real_origin") is not False
        or attribution.get("same_source_origin_fixed_in_each_pair") is not True
        or attribution.get("original_2027_2028_predictions_modified") is not False
        or rolling.get("schema")!="idealab.psico.geo_h2_rolling_historical_2014_2025.v1"
        or rolling.get("not_prospective_or_independently_timestamped_skill") is not True
        or rolling.get("primary_frozen_2027_probabilities_changed") is not False
        or rolling.get("source_archives_sha256")!=attribution.get("source_archives_sha256")
        or rolling.get("original_GEO2027_SHA256")!=attribution.get("original_GEO2027_SHA256")
        or attribution.get("years")!=EXPECTED_YEARS
        or attribution.get("country_n")!=196
        or attribution.get("unique_country_year_n")!=196*len(EXPECTED_YEARS)):
        raise ValueError("Historic source provenance / frozen issuer mismatch")
    aa=attribution["yearly"]
    ff=rolling["primary_unique_year_series"]["folds"]
    if len(aa)!=len(EXPECTED_YEARS) or len(ff)!=12:
        raise ValueError("Country-year cohort, year count changed")
    folds={f["target_year"]:f for f in ff}
    updates={r["target_year"]:r for r in aa}
    if (len(folds)!=12 or len(updates)!=len(EXPECTED_YEARS)
        or sorted(folds)!=list(range(2014,2026))
        or sorted(updates)!=EXPECTED_YEARS):
        raise ValueError("Year source duplicated or omitted")
    report=[]
    totals_old={key:0.0 for key in MODELS}
    totals_new={key:0.0 for key in MODELS}
    changes={key:0.0 for key in MODELS}
    for year in EXPECTED_YEARS:
        f=folds[year]
        r=updates[year]
        if (f["country_n"]!=196 or r["country_n"]!=196
            or f["origin_release"]!=r["frozen_origin_release"]
            or f["outcome_release"]!="25.1"
            or r["old_target_release"]!="25.1"
            or r["new_target_release"]!="26.1"
            or f["origin_year"]!=r["origin_year"] or
            r["origin_year"]!=year-2 or
            r["label_revisions_n"]!=len(r["revised_countries"])):
            raise ValueError("Historical origin, target or frozen GWNO mismatch")
        old={key:_value(f,key) for key in MODELS}
        delta=r["observed_brier_shift_new_minus_old"]
        if set(delta)!=set(MODELS):
            raise ValueError("A fixed-model score revision is missing")
        new={}
        for key in MODELS:
            d=delta[key]
            if type(d) not in (int,float) or not math.isfinite(d):
                raise ValueError("Invalid measured Brier revision")
            new[key]=old[key]+d
            if not -1e-12<=new[key]<=1+1e-12:
                raise ValueError("Impossible Brier under revised labels")
            if abs(d)>r["label_revisions_n"]/196+1e-12:
                raise ValueError("Measured score exceeds algebraic label bound")
            totals_old[key]+=old[key]
            totals_new[key]+=new[key]
            changes[key]+=d
        report.append({
            "target_year":year,
            "origin_year":year-2,
            "official_country_n":196,
            "binary_label_revisions_n":r["label_revisions_n"],
            "score_25_1":old,
            "score_26_1_same_probabilities":new,
            "score_revision_new_minus_old":delta,
            **_compare(old,new),
        })
    n=len(EXPECTED_YEARS)
    pool_old={key:totals_old[key]/n for key in MODELS}
    pool_new={key:totals_new[key]/n for key in MODELS}
    for key in MODELS:
        if not math.isclose(
            changes[key]/n,
            attribution["observed_brier_shift_new_minus_old"][key],
            rel_tol=0,abs_tol=1e-12):
            raise ValueError("Aggregated score label shift differs from prior source replay")
        if not math.isclose(
            pool_new[key]-pool_old[key],
            attribution["observed_brier_shift_new_minus_old"][key],
            rel_tol=0,abs_tol=1e-12):
            raise ValueError("Pooled model Brier revision arithmetic failed")
    pooled=_compare(pool_old,pool_new)
    return {
        "schema":"idealab.psico.geo_h2_2526_fixed_brier_rank_robustness.v1",
        "status":"RETROSPECTIVE_FIXED_FORECAST_SOURCE_VINTAGE_RANKING_NOT_PROSPECTIVE_SKILL",
        "source_fixed_vector_measurement_report":str(ATTRIBUTION.relative_to(ROOT)),
        "source_rolling_historical_report":str(ROLLING.relative_to(ROOT)),
        "official_UCDP_zip_sha256":attribution["source_archives_sha256"],
        "original_GEO2027_issue_sha256":attribution["original_GEO2027_SHA256"],
        "countries_per_year":196,
        "years":EXPECTED_YEARS,
        "pooled_country_year_n":196*n,
        "excluded_2025_from_pooled_baseline":True,
        "models":list(MODELS),
        "annual_rank_changes_n":sum(r["ranking_changed"] for r in report),
        "annual_pairwise_order_reversals_n":sum(len(r["pairwise_order_or_tie_reversed"]) for r in report),
        "pooled_scores_25_1":pool_old,
        "pooled_scores_26_1_same_probabilities":pool_new,
        "pooled_measured_score_revision_new_minus_old":attribution["observed_brier_shift_new_minus_old"],
        "pooled_ranking":pooled,
        "annual":report,
        "historical_forecasts_issued_at_actual_origins":False,
        "new_2027_2028_forecasts_issued":0,
        "observed_future_outcomes_scored":False,
        "limitations":"Only 25.1 versus 26.1 outcome labels at fixed pseudo-origin model vectors. The older origin editions were published after many simulated origins. Country-year observations share time and geography. No causal inference, IID interpretation, significance test or evidence of prospective predictive skill.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--check-report",action="store_true")
    p.add_argument("--print-report",action="store_true")
    args=p.parse_args()
    report=analyze(json.loads(ATTRIBUTION.read_text(encoding="utf-8")),
                   json.loads(ROLLING.read_text(encoding="utf-8")))
    payload=json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    if args.check_report and json.loads(OUTPUT.read_text(encoding="utf-8"))!=report:
        raise ValueError("Published fixed-vector vintage ranking report changed")
    if args.print_report:
        print("GEO_H2_FIXED_RANK_BEGIN",flush=True)
        print(payload,end="")
        print("GEO_H2_FIXED_RANK_END",flush=True)
    else:
        print(json.dumps({
            "annual_rank_changes":report["annual_rank_changes_n"],
            "pooled_ranking_old":report["pooled_ranking"]["ranking_old"],
            "pooled_ranking_new":report["pooled_ranking"]["ranking_new"],
        },sort_keys=True))


if __name__=="__main__":
    main()
