#!/usr/bin/env python3
"""Source-free ex-ante disagreement audit across SHA-frozen GEO2027 issues.

Pure risk forecast comparison; outcomes for 2027 remain UNRESOLVED. This
diagnostic NEVER creates forecasts or reissues the original 15 alerts.
It computes all 196 paired issued probability deltas and exactly how these
would contribute to the pre-registered future paired Brier, conditional on
each country's as-yet-unknown binary outcome.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, FROZEN_SHA256, FIRST_COMMIT,
    audit as audit_new, sha,
)
from audit_geo2027_log1p_shadow_issue import (
    ISSUE as OLD_SHADOW, MANIFEST as OLD_SHADOW_MANIFEST,
    ORIGINAL, FROZEN_ISSUE_SHA256,
)
from audit_geo2027_log1p_issued_death_stress import ALERTS, ALERT_SHA
from prepare_geo2027_transition_alerts import SOURCE_SHA256

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo2027-global-only-issued-disagreement.json"
GROUP_ORDER=("origin_zero","origin_1_to_24","origin_active")
VARIANTS={
    "original_GEO":"original_GEO2027_p_active_frozen",
    "old_LOG1P":"original_LOG1P2027_p_active_frozen",
    "original_intercept_control":"original_intercept_control_p_active_frozen",
    "global_only_alpha0":"global_only_alpha0_p_active_2027",
    "global_only_alpha1":"global_only_alpha1_p_active_2027",
}


def group(r):
    d=r["origin_deaths_best_2025"]
    if type(d) is not int or d<0:
        raise ValueError("Invalid first-issued annual death count")
    return "origin_zero" if d==0 else ("origin_1_to_24" if d<25 else
                                      "origin_active")


def score_sensitivity(new,old):
    """Per-country prospective Brier(A)-Brier(B), conditional on future y."""
    if (any(type(x) not in (int,float) or not math.isfinite(x)
            or not 0<x<1 for x in (new,old))):
        raise ValueError("Need strictly probabilistic paired forecasts")
    pdelta=new-old
    no_event=(new*new-old*old)
    event=(new-1)**2-(old-1)**2
    if abs(no_event-pdelta*(new+old))>1e-12:
        raise AssertionError("Brier y=0 identity failed")
    if abs(event-pdelta*(new+old-2))>1e-12:
        raise AssertionError("Brier y=1 identity failed")
    return {"no_event_y0":no_event,"event_y1":event,
            "risk_delta":pdelta}


def _fmt(x):
    return round(x,12)


def _ranks(rows,field,filter_group,n):
    take=[r for r in rows if filter_group is None or
          (filter_group=="inactive" and
           r["origin_binary_state_2025"]==0) or
          (filter_group=="active" and
           r["origin_binary_state_2025"]==1)]
    return sorted(take,key=lambda r:(-r[field],r["country_id"]))[:n]


def _rank_entry(rows,field,n):
    return [{"country_id":r["country_id"],"country":r["country"],
             "origin_deaths_2025":r["origin_deaths_best_2025"],
             "forecast_probability":r[field]} for r in rows[:n]]


def _rank_comparison(rows,field_old,field_new,n,cohort):
    old=_ranks(rows,field_old,cohort,n)
    new=_ranks(rows,field_new,cohort,n)
    old_ids=[r["country_id"] for r in old]
    new_ids=[r["country_id"] for r in new]
    return {
        "n":n,
        "cohort":cohort or "full196",
        "overlap_n":len(set(old_ids)&set(new_ids)),
        "old_only":[r["country"] for r in old if r["country_id"] not in new_ids],
        "new_only":[r["country"] for r in new if r["country_id"] not in old_ids],
        "old_rank":[r["country"] for r in old],
        "new_rank":[r["country"] for r in new],
        "old_probability_ordered":_rank_entry(old,field_old,n),
        "new_probability_ordered":_rank_entry(new,field_new,n),
        "not_a_new_issued_alert_list":True,
    }


def analyze(new_issue,old_issue,original):
    if (new_issue.get("schema")!=
        "idealab.psico.geo2027_global_only_country_block_shadow.v1"
        or old_issue.get("schema")!=
        "idealab.psico.geo2027_log1p_intensity_shadow.v1"
        or original.get("forecast_id")!="PSICO-GEO2027-STATEBASED25-V1"
        or new_issue.get("official_2027_outcomes_resolved")!=0
        or old_issue.get("outcomes_2027_resolved")!=0
        or new_issue.get("n_countries")!=196
        or new_issue.get("prospective_scoring_precommitment",{}).get(
            "primary_pair")!=
        "full196_Brier_global_only_alpha1_minus_frozen_original_LOG1P_shadow"):
        raise ValueError("First-issued prospective 196-country model lineage mismatch")
    rows=new_issue["countries"]
    oldrows={r["country_id"]:r for r in old_issue["countries"]}
    first={r["country_id"]:r for r in original["countries"]}
    if (len(rows)!=196 or len(oldrows)!=196 or len(first)!=196
        or [r["country_id"] for r in rows]!=sorted(first)
        or set(oldrows)!=set(first)):
        raise ValueError("Original 196 GWNO risk universe must be identical")
    allcases=[]
    for row in rows:
        cid=row["country_id"]
        old=oldrows[cid];initial=first[cid]
        if (row["country"]!=initial["country"] or
            old["country"]!=initial["country"] or
            row["origin_deaths_best_2025"]!=
            old["origin_deaths_best_2025"] or
            row["origin_binary_state_2025"]!=
            initial["last_observed_state_2025"] or
            row["original_GEO2027_p_active_frozen"]!=initial["p_model"] or
            row["original_LOG1P2027_p_active_frozen"]!=
            old["log1p_shadow_p_active_2027"]):
            raise ValueError("Country-issued source reconciliation invalid")
        pc=row[VARIANTS["global_only_alpha1"]]
        po=row[VARIANTS["old_LOG1P"]]
        s=score_sensitivity(pc,po)
        allcases.append({
            "country_id":cid,"country":row["country"],
            "origin_deaths_best_2025":row["origin_deaths_best_2025"],
            "origin_state":row["origin_binary_state_2025"],
            "group":group(row),
            "old_LOG1P_p":po,
            "new_global_only_alpha0_p":row[VARIANTS["global_only_alpha0"]],
            "new_global_only_alpha1_p":pc,
            "original_GEO_p":row[VARIANTS["original_GEO"]],
            "primary_probability_delta_pp":round(100*s["risk_delta"],9),
            "primary_Brier_delta_if_no_event_y0":_fmt(s["no_event_y0"]),
            "primary_Brier_delta_if_event_y1":_fmt(s["event_y1"]),
            "primary_delta_explains_both_conditional_outcomes":True,
        })
    abs_diff=[abs(r["primary_probability_delta_pp"]) for r in allcases]
    oldfld=VARIANTS["old_LOG1P"]
    newfld=VARIANTS["global_only_alpha1"]
    cohorts={}
    for label in GROUP_ORDER:
        selected=[r for r in rows if group(r)==label]
        if not selected:raise ValueError("Empty official origin-death stratum")
        pold=[r[oldfld] for r in selected]
        pnew=[r[newfld] for r in selected]
        changes=[b-a for a,b in zip(pold,pnew)]
        cohorts[label]={
            "country_n":len(selected),
            "mean_old_LOG1P_probability":_fmt(sum(pold)/len(pold)),
            "mean_new_global_only_probability":_fmt(sum(pnew)/len(pnew)),
            "range_old_LOG1P_pp":round(100*(max(pold)-min(pold)),9),
            "range_new_global_only_pp":round(100*(max(pnew)-min(pnew)),9),
            "min_old_LOG1P_probability":min(pold),
            "max_old_LOG1P_probability":max(pold),
            "min_new_global_only_probability":min(pnew),
            "max_new_global_only_probability":max(pnew),
            "sum_old_expected_active":_fmt(sum(pold)),
            "sum_new_expected_active":_fmt(sum(pnew)),
            "mean_probability_delta_pp":round(100*sum(changes)/len(changes),9),
            "mean_absolute_delta_pp":round(
                100*sum(abs(x) for x in changes)/len(changes),9),
        }
    if [cohorts[x]["country_n"] for x in GROUP_ORDER]!=[154,8,34]:
        raise AssertionError("Previously issued 2025 intensity strata changed")
    if not all(r["new_global_only_alpha0_p"]==
               r["new_global_only_alpha1_p"] for r in allcases
               if r["group"]!="origin_1_to_24"):
        raise AssertionError("Alpha0 and alpha1 should differ only at 1–24 deaths")
    expected=new_issue["expected_active_countries_sum_probabilities"]
    for key,field in (("original_GEO",VARIANTS["original_GEO"]),
                      ("original_LOG1P",oldfld),
                      ("global_only_alpha0",VARIANTS["global_only_alpha0"]),
                      ("global_only_alpha1",newfld)):
        if abs(sum(r[field] for r in rows)-expected[key])>1e-9:
            raise AssertionError("Original issue expected-active sums differ")

    ranks={
        "all_country_top15":_rank_comparison(rows,oldfld,newfld,15,None),
        "origin_inactive_top10":_rank_comparison(
            rows,oldfld,newfld,10,"inactive"),
        "origin_active_top5":_rank_comparison(
            rows,oldfld,newfld,5,"active"),
    }
    d0=sum(r["primary_Brier_delta_if_no_event_y0"]
           for r in allcases)/len(allcases)
    riskdelta=sum(r["primary_probability_delta_pp"]/100
                  for r in allcases)
    # For each unknown y_i, delta_i = delta_if_y0 - 2*(pnew-pold)*y_i.
    # The bounds below are algebraic over ALL POSSIBLE 196 binary outcomes,
    # NOT probability intervals and NOT historical estimates.
    max_possible=sum(max(r["primary_Brier_delta_if_no_event_y0"],
                         r["primary_Brier_delta_if_event_y1"])
                     for r in allcases)/196
    min_possible=sum(min(r["primary_Brier_delta_if_no_event_y0"],
                         r["primary_Brier_delta_if_event_y1"])
                     for r in allcases)/196
    ordered=sorted(allcases,key=lambda x:(
        -abs(x["primary_probability_delta_pp"]),x["country_id"]))
    return {
        "schema":"idealab.psico.geo2027_issued_global_only_probability_disagreement.v1",
        "status":"SOURCE_FREE_POST_ISSUE_EX_ANTE_DIAGNOSTIC_NO_NEW_PREDICTION",
        "original_forecast_sha256":SOURCE_SHA256,
        "original_LOG1P_shadow_sha256":FROZEN_ISSUE_SHA256,
        "new_global_only_first_issue_sha256":FROZEN_SHA256,
        "new_global_only_first_public_commit":FIRST_COMMIT,
        "frozen_15_transition_alerts_sha256":ALERT_SHA,
        "both_issued_before_any_official_2027_outcome":True,
        "source_year":2025,
        "target_year":2027,
        "fixed_original_GWNO_country_n":196,
        "official_2027_outcomes_resolved":0,
        "no_new_forecasts_or_alerts_issued":True,
        "historical_model_selection_already_explored":True,
        "unknown_future_labels_not_scored":True,
        "primary_pair_registered_before_outcomes":
            "Brier_global_only_matched_alpha1_minus_original_LOG1P_shadow",
        "alpha1_minus_alpha0_differs_only_for_8_subthreshold_countries":True,
        "model_country_probability_fields":VARIANTS,
        "group_by_origin_deaths":cohorts,
        "expected_active_totals":expected,
        "mean_absolute_primary_probability_delta_pp":round(
            sum(abs_diff)/len(abs_diff),9),
        "max_absolute_primary_probability_delta_pp":max(abs_diff),
        "n_primary_absolute_delta_at_least_5_pp":sum(
            x>=5-1e-9 for x in abs_diff),
        "n_primary_absolute_delta_at_least_10_pp":sum(
            x>=10-1e-9 for x in abs_diff),
        "rank_disagreement_diagnostics_not_reissued_alerts":ranks,
        "top15_countries_by_absolute_probability_disagreement":ordered[:15],
        "all_country_probability_and_future_Brier_conditional_effects":allcases,
        "future_primary_paired_Brier_exact_algebra":{
            "constant_if_all_country_outcomes_were_zero":_fmt(d0),
            "risk_delta_sum_across_196_countries":_fmt(riskdelta),
            "formula":"DeltaBrier_2027 = constant_y_all0 - (2/196)*sum_i[(p_globalonly_alpha1_i - p_original_LOG1P_i)*y_i]; only first complete official 2027 UCDP supplies y_i",
            "logical_min_over_all_2_power_196_possible_binary_labels":
                _fmt(min_possible),
            "logical_max_over_all_2_power_196_possible_binary_labels":
                _fmt(max_possible),
            "logical_extrema_not_statistical_intervals":True,
            "never_interpret_binary_outcome_scenarios_as_observed_2027":True,
        },
        "limitations":"All 2027 outcomes unresolved. Disagreements are deterministic differences between previously issued probabilities, NOT actual errors or empirical skill. Small global-only risk spread among zero-origin-death countries is structurally expected after dropping country-local transition history; this is not proof that differentiated original probabilities are better calibrated. Original 2027 15 alert list is NOT reconstructed or changed. Rank order of probability is descriptive and not a new issued alert selection. Conditional future score algebra is exact for a fixed set of 196 labels but does not estimate which labels will be positive. Four other shadows and controls mean ex-post winner selection and IID country p-values are invalid."
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    args=ap.parse_args()
    raw=ISSUE.read_bytes()
    original=ORIGINAL.read_bytes()
    older=OLD_SHADOW.read_bytes()
    audit_new(raw,MANIFEST.read_bytes(),original,older,
              OLD_SHADOW_MANIFEST.read_bytes(),ALERTS.read_bytes())
    if sha(ALERTS.read_bytes())!=ALERT_SHA:
        raise ValueError("First-issued GEO2027 alerts changed")
    result=analyze(json.loads(raw),json.loads(older),json.loads(original))
    text=json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n"
    print("GEO2027_ISSUED_DISAGREEMENT_BEGIN")
    print(text,end="")
    print("GEO2027_ISSUED_DISAGREEMENT_END",flush=True)
    if args.check_report and REPORT.read_bytes()!=text.encode():
        raise ValueError("Frozen issued forecast disagreement differs from committed report")


if __name__=="__main__":
    main()
