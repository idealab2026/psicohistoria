#!/usr/bin/env python3
"""GEO-2027: does archived-country skill measure persistence or entry?

Re-evaluates the exact fixed 2027 Markov equations using archived origin
editions (23.1,24.1) and later outcome editions (25.1,26.1).
Origin-inactive => target-active means crossing the >=25 state-based deaths
threshold, NOT onset2, creation of a new war, or civilian victimization.

One archive download per pinned source. All metrics are aggregate and ex-post;
the authentic 196 issued country probabilities for 2027 remain unchanged.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from backtest_archived_country_vintages import SOURCES,FOLDS,fetch_archives
from backtest_statebased_2027_spec import (
    _annual_frame,_metrics,_pairwise_uncertainty,_reliability
)

GROUP_LABELS={
    0:"BELOW_25_AT_ORIGIN",
    1:"AT_LEAST_25_AT_ORIGIN",
}
TOP_K=(10,20,35)

def rows_from_vintages(files):
    batches=[]
    for fold in FOLDS:
        source=files[fold["origin_release"]]
        outcome=files[fold["target_release"]]
        cutoff=fold["origin_year"]
        target=fold["target_year"]
        if target-cutoff!=2:
            raise ValueError("Historical state transition must have exactly 2 calendar steps")
        if max(max(h) for h in source.values())!=cutoff or \
           max(max(h) for h in outcome.values())!=target:
            raise ValueError("Different archived editions do not match cutoffs")
        combined={cid:dict(h) for cid,h in source.items()}
        for cid,h in combined.items():
            if target in outcome.get(cid,{}):
                h[target]=outcome[cid][target]
        scored,meta=_annual_frame(combined,cutoff)
        if len(scored)!=meta["resolved"]:
            raise ValueError("Incomplete scored cohort")
        for item in scored:
            cid=item["country_id"]
            item["origin_active"]=source[cid][cutoff]
        batches.append((fold,scored,meta))
    return batches

def group_stats(rows):
    if not rows:
        raise ValueError("No observations in origin-state cohort")
    losses=_metrics(rows)
    mean_prob={key:sum(v[key] for v in rows)/len(rows)
       for key in ("p_model","p_global_markov","p_baseline_global_5y")}
    return {
        "country_years":len(rows),
        "positive_threshold_outcomes":sum(v["outcome"] for v in rows),
        "observed_rate":sum(v["outcome"] for v in rows)/len(rows),
        "mean_probabilities":mean_prob,
        "scores":losses,
        "brier_skill_model_vs_global_markov":
            1-losses["p_model"]["brier"]/losses["p_global_markov"]["brier"],
        "delta_brier_model_minus_global_markov":
            losses["p_model"]["brier"]-losses["p_global_markov"]["brier"],
        "calibration_bins":_reliability(rows,"p_model"),
    }

def rank_summary(rows):
    """Fixed alert budgets by target year; no model tuning or re-ranking."""
    targets=len(rows)
    positives=sum(v["outcome"] for v in rows)
    ranked=sorted(rows,key=lambda v:(-v["p_model"],v["country_id"]))
    report={}
    for k in TOP_K:
        if k>targets:raise ValueError("Budget exceeds target country cohort")
        n=sum(v["outcome"] for v in ranked[:k])
        report[str(k)]={
            "budget":k,"true_positives":n,"precision_at_k":n/k,
            "recall_at_k":n/positives if positives else None,
            "target_positives":positives,
            "random_ranking_expected_hits":k*positives/targets,
        }
    return report

def evaluate(files,source_details):
    batches=rows_from_vintages(files)
    if len(batches)!=2:
        raise ValueError("Fixed two historical targets required")
    pooled=[v for _,rows,_ in batches for v in rows]
    groups={}
    for state,label in GROUP_LABELS.items():
        cohort=[v for v in pooled if v["origin_active"]==state]
        groups[label]=group_stats(cohort)
        groups[label]["country_cluster_bootstrap_95pct_delta_brier_model_minus_global_markov"]=\
            _pairwise_uncertainty(cohort,"p_global_markov")
    per_year=[]
    for fold,rows,meta in batches:
        if len(rows)<190:
            raise ValueError("Target coverage unexpectedly low")
        state0=[v for v in rows if v["origin_active"]==0]
        state1=[v for v in rows if v["origin_active"]==1]
        per_year.append({
            "origin_release":fold["origin_release"],
            "target_release":fold["target_release"],
            "origin_year":fold["origin_year"],
            "target_year":fold["target_year"],
            "country_years":len(rows),
            "origin_inactive":len(state0),
            "origin_active":len(state1),
            "inactive_to_active":sum(v["outcome"] for v in state0),
            "active_to_active":sum(v["outcome"] for v in state1),
            "active_to_inactive":sum(1-v["outcome"] for v in state1),
            "inactive_to_inactive":sum(1-v["outcome"] for v in state0),
            "inactive_cohort":group_stats(state0),
            "active_cohort":group_stats(state1),
            "top_k":rank_summary(rows),
        })
    observed_positive=sum(v["outcome"] for v in pooled)
    if len(pooled)!=392 or observed_positive!=69:
        raise ValueError("Reconstructed historical outcomes contradict pinned study")
    if sum(x["country_years"] for x in per_year)!=392 or \
       sum(x["inactive_to_active"]+x["active_to_active"] for x in per_year)!=69:
        raise ValueError("Conditional state accounting inconsistent")
    return {
        "schema":"idealab.psico.geo2027_origin_state_skill_diagnostic.v1",
        "study_type":"POST_HOC_PERSISTENCE_VS_THRESHOLD_ENTRY_ARCHIVED_COUNTRY_VINTAGES",
        "source":"UCDP OrganizedViolenceCY",
        "source_editions":source_details,
        "target_years":[2024,2025],
        "observation_horizon_calendar_steps":2,
        "first_historical_release_timestamps_verified":False,
        "true_issued_prospective_forecasts_evaluated":0,
        "original_2027_forecast_unchanged":True,
        "target_definition":"1 if sb_total_deaths_best >=25 in target year",
        "origin_definition":"1 if sb_total_deaths_best >=25 in source cutoff year",
        "false_interpretation_prohibited":"Origin 0 to target 1 is threshold entry, not necessarily conflict onset, war initiation, or civilians killed by governments.",
        "conditional_groups":groups,
        "annual":per_year,
        "pooled_total":len(pooled),
        "pooled_positive":observed_positive,
        "ex_post_status":"Not historically issued. Source editions were acquired during 2026. Vintage dated 23.1/24.1 describes data through origin year but was published after the corresponding year's end; two calendar transition steps are NOT two years of verified prospective notice.",
        "uncertainty_limits":"Only two target years. Country bootstrap cannot estimate global year shocks; per-year subgroup skill may differ and negative results must not be concealed."
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report")
    args=parser.parse_args()
    sources,metadata=fetch_archives()
    study=evaluate(sources,metadata)
    payload=json.dumps(study,sort_keys=True,indent=2,ensure_ascii=False)+"\n"
    if args.check_report and Path(args.check_report).read_bytes()!=payload.encode("utf8"):
        raise ValueError("Published conditional diagnostic does not match pinned official UCDP vintages")
    print("GEO2027_ORIGIN_STATE_AUDIT_BEGIN")
    print(payload,end="")
    print("GEO2027_ORIGIN_STATE_AUDIT_END")
    print("GEO2027_ORIGIN_STATE_AUDIT_OK",study["pooled_total"],study["pooled_positive"],
          "real_2027_evaluated",study["true_issued_prospective_forecasts_evaluated"])

if __name__=="__main__":
    main()
