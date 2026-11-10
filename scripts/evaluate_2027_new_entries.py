#!/usr/bin/env python3
"""GEO-2027: historical threshold-entry performance with an entry-specific baseline.

EXPLORATORY / DESIGNED AFTER INSPECTION OF 2024-25 OUTCOMES.
This study is NOT a pre-registered holdout, NOT UCDP onset2, and cannot be
used to recalibrate the 196 issued forecasts for 2027.

Use original hash-verified UCDP 23.1/24.1 for all fitting and 25.1/26.1
strictly for later year labels. Compare the already frozen two-step country
Markov and global Markov with the simple 2-year historical entry rate
estimated from eligible initially-inactive countries in the origin edition.
Evaluate only countries BELOW the >=25-deaths threshold at origin.

No outcome-year prevalence, future-vintage country membership, or
future-revised data can enter the new conditional reference.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from backtest_archived_country_vintages import FOLDS,fetch_archives
from diagnose_2027_origin_state import rows_from_vintages
from backtest_statebased_2027_spec import _score,_reliability,_pairwise_uncertainty

RELEASE_TARGET_YEARS=(2024,2025)
TOP_K=(5,10,20)
PRIOR_ALPHA=1
PRIOR_BETA=1
MIN_TRAIN_PAIRS=100

def frozen_two_year_entry_prior(origin_records, origin_year):
    """Beta(1,1) two-calendar-year entry frequency. NO target labels."""
    if not origin_records:
        raise ValueError("Missing historical origin edition")
    if max(max(h) for h in origin_records.values())!=origin_year:
        raise ValueError("Training data extend beyond edition cutoff")
    cohort=sorted(cid for cid,h in origin_records.items()
                  if origin_year in h and origin_year-1 in h)
    if len(cohort)!=196:
        raise ValueError("The immutable 196-country origin cohort is incomplete")
    entries=0
    exposure=0
    for cid in cohort:
        hist=origin_records[cid]
        for year,state in hist.items():
            if year+2<=origin_year and state==0 and year+2 in hist:
                exposure+=1
                entries+=hist[year+2]
    if exposure<MIN_TRAIN_PAIRS or entries<1 or entries>=exposure:
        raise ValueError("No valid historical 2-year entry-rate training sample")
    p=(entries+PRIOR_ALPHA)/(exposure+PRIOR_ALPHA+PRIOR_BETA)
    if not 0<p<1:
        raise ValueError("Entry baseline must be a proper probability")
    return {
        "probability":round(p,12),
        "eligible_countries_at_origin":len(cohort),
        "historical_inactive_exposures":exposure,
        "historical_two_year_entries":entries,
        "historical_last_eligible_origin_year":origin_year-2,
        "future_outcomes_used":False,
    }

def average_precision(rows, key):
    """Tie-aware non-interpolated average precision, bounded and deterministic."""
    if not rows or sum(r["outcome"] for r in rows)==0:
        return None
    ordered=sorted(rows,key=lambda r:-r[key])
    positives=sum(r["outcome"] for r in ordered)
    count=0;hits=0;average_precision_score=0
    i=0
    while i<len(ordered):
        j=i+1
        while j<len(ordered) and ordered[j][key]==ordered[i][key]:
            j+=1
        batch_pos=sum(r["outcome"] for r in ordered[i:j])
        hits+=batch_pos
        count+=j-i
        average_precision_score+=(batch_pos/positives)*(hits/count)
        i=j
    return average_precision_score

def roc_auc(rows,key):
    pos=[r[key] for r in rows if r["outcome"]==1]
    neg=[r[key] for r in rows if r["outcome"]==0]
    if not pos or not neg:return None
    favorable=sum((p>n)+0.5*(p==n) for p in pos for n in neg)
    return favorable/(len(pos)*len(neg))

def top_alerts(rows):
    """Only countries initially below threshold, top-K by ORIGINAL forecast."""
    if not rows or len(rows)<max(TOP_K):
        raise ValueError("Insufficient countries in originally-inactive cohort")
    ranked=sorted(rows,key=lambda r:(-r["p_model"],r["country_id"]))
    positives=sum(r["outcome"] for r in rows)
    return {
       str(k):{
         "budget":k,
         "hits":sum(r["outcome"] for r in ranked[:k]),
         "precision":sum(r["outcome"] for r in ranked[:k])/k,
         "recall":sum(r["outcome"] for r in ranked[:k])/positives if positives else None,
         "random_expected_hits":k*positives/len(rows),
         "ties_at_threshold":sum(r["p_model"]==ranked[k-1]["p_model"] for r in ranked)>1
       }
       for k in TOP_K
    }

def _format_fold(fold,rows,entry_prior):
    scored=[{**r,"p_entry_prior_2y":entry_prior["probability"]} for r in rows
            if r["origin_active"]==0]
    if not scored or len(scored)<145:
        raise ValueError("Missing conditional initially-inactive evaluation cohort")
    scores={key:_score(scored,key) for key in (
        "p_model","p_global_markov","p_entry_prior_2y")}
    observed=sum(r["outcome"] for r in scored)
    return scored,{
        "origin_version":fold["origin_release"],
        "evaluation_version":fold["target_release"],
        "origin_year":fold["origin_year"],
        "outcome_year":fold["target_year"],
        "n":len(scored),
        "new_entries":observed,
        "observed_entry_rate":observed/len(scored),
        "mean_model_prediction":sum(r["p_model"] for r in scored)/len(scored),
        "mean_global_markov_prediction":sum(r["p_global_markov"] for r in scored)/len(scored),
        "entry_training":entry_prior,
        "scores":scores,
        "average_precision":{
          "country_markov":average_precision(scored,"p_model"),
          "global_markov":average_precision(scored,"p_global_markov"),
          "entry_prior":average_precision(scored,"p_entry_prior_2y"),
        },
        "roc_auc":{
          "country_markov":roc_auc(scored,"p_model"),
          "global_markov":roc_auc(scored,"p_global_markov"),
          "entry_prior":roc_auc(scored,"p_entry_prior_2y")
        },
        "alert_budgets":top_alerts(scored),
    }

def evaluate(files,metadata):
    for version in ("23.1","24.1","25.1","26.1"):
        if version not in files or version not in metadata:
            raise ValueError("A pinned UCDP vintage is missing")
    batches=rows_from_vintages(files)
    if len(batches)!=2:
        raise ValueError("Expected precisely two predefined historical holdouts")
    all_rows=[]
    folds=[]
    for fold,rows,details in batches:
        origin=files[fold["origin_release"]]
        training=frozen_two_year_entry_prior(origin,fold["origin_year"])
        sample,metrics=_format_fold(fold,rows,training)
        all_rows.extend(sample)
        folds.append(metrics)
    if len(all_rows)!=321 or sum(r["outcome"] for r in all_rows)!=8:
        raise ValueError("Published 2024/25 threshold-entry cohort changed")
    pooled={
      key:_score(all_rows,key)
      for key in ("p_model","p_global_markov","p_entry_prior_2y")
    }
    base=pooled["p_entry_prior_2y"]["brier"]
    by_year=[]
    for m in folds:
        by_year.append({
          "year":m["outcome_year"],
          "brier_delta_model_minus_conditional_prior":
              m["scores"]["p_model"]["brier"]-m["scores"]["p_entry_prior_2y"]["brier"],
          "brier_delta_model_minus_global_markov":
              m["scores"]["p_model"]["brier"]-m["scores"]["p_global_markov"]["brier"]
        })
    return {
      "schema":"idealab.psico.geo2027_threshold_entry_comparator.v1",
      "study_id":"EMP-GEO2027-THRESHOLD-ENTRY-SPECIFIC-20261110",
      "status":"EXPLORATORY_EX_POST_TWO_TARGET_YEARS_NOT_PROSPECTIVE",
      "data_source":"UCDP OrganizedViolenceCY",
      "source_vintages":{
          v:{"url":metadata[v]["url"],"sha256":metadata[v]["sha256"],
             "last_year":metadata[v]["last_year"]}
          for v in ("23.1","24.1","25.1","26.1")
      },
      "target_rule":"at least 25 state-based organized-violence deaths in later country-year",
      "entry_definition":"below 25 in origin year and >=25 in target year, NOT conflict onset2",
      "target_years":list(RELEASE_TARGET_YEARS),
      "horizon_calendar_steps":2,
      "baseline_definition":"Beta(1,1) smoothed historical direct 2-year inactive-to-active event fraction, using only prior edition and countries eligible in origin year",
      "prior_configuration":{"alpha":PRIOR_ALPHA,"beta":PRIOR_BETA},
      "primary_forecast_is_unmodified":True,
      "candidate_model_tuning_performed":False,
      "new_model_hypothesis_only_after_seen_outcomes":True,
      "future_source_asof_provenance_certified":False,
      "country_years":len(all_rows),
      "positive_threshold_entries":sum(r["outcome"] for r in all_rows),
      "pooled_observed_entry_rate":sum(r["outcome"] for r in all_rows)/len(all_rows),
      "pooled_mean_model_probability":sum(r["p_model"] for r in all_rows)/len(all_rows),
      "pooled_mean_global_markov_probability":sum(r["p_global_markov"] for r in all_rows)/len(all_rows),
      "folds":folds,
      "pooled_scores":pooled,
      "brier_skill_vs_entry_prior":1-pooled["p_model"]["brier"]/base,
      "brier_skill_vs_global_markov":1-pooled["p_model"]["brier"]/pooled["p_global_markov"]["brier"],
      "country_cluster_bootstrap_95pct_model_minus_entry_prior":
          _pairwise_uncertainty(all_rows,"p_entry_prior_2y"),
      "country_cluster_bootstrap_95pct_model_minus_global_markov":
          _pairwise_uncertainty(all_rows,"p_global_markov"),
      "mean_probability_over_outcome_ratio":
          (sum(r["p_model"] for r in all_rows)/sum(r["outcome"] for r in all_rows)),
      "annual_brier_deltas":by_year,
      "calibration_country_markov":_reliability(all_rows,"p_model"),
      "real_2027_predictions_changed":0,
      "real_2027_outcomes_resolved":0,
      "prospective_skill_demonstrated":False,
      "limitations":"Exploratory comparator specified after 2024/25 labels were inspected, not independent confirmatory holdout. Eight positive entries only, two target years and country-cluster intervals ignore common year shocks. No verified historical original issue times or historically issued forecasts. Two annual steps do not imply two years of live lead time. Crossing 25 state-based deaths is neither new-war onset nor state violence against civilians."
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report")
    args=ap.parse_args()
    vintages,metadata=fetch_archives()
    report=evaluate(vintages,metadata)
    content=json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    if args.check_report and content.encode()!=Path(args.check_report).read_bytes():
        raise ValueError("Pinned new-entry comparison report does not match reproduction")
    print("GEO2027_NEW_ENTRY_COMPARISON_BEGIN")
    print(content,end="")
    print("GEO2027_NEW_ENTRY_COMPARISON_END")
    print("GEO2027_NEW_ENTRY_COMPLETE",report["country_years"],report["positive_threshold_entries"],
          "2027_resolved",report["real_2027_outcomes_resolved"])

if __name__=="__main__":
    main()
