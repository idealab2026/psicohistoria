#!/usr/bin/env python3
"""Prospective, separate 2027 GEO LOG1P SHADOW issuance; first public issue remains immutable.

The method was explored after seeing ex-post 2024/25 labels, but official
2027 labels do not yet exist. Freeze 196 future-facing probabilities generated
from official UCDP 26.1 up through 2025, with original GEO as an exact anchor.
This is a DISTINCT SHADOW, not a correction of already-issued forecasts or
15 transition alerts. Future UCDP 2027 scores must use the first complete
official release; evaluate both original and shadow on the same 196 countries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from backtest_archived_country_vintages import SOURCES
from diagnose_geo2028_historical_forecast_vintage_drift import _fit_at_origin
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD, counts_to_binary, parse_counts,
)
from experiment_geo2027_log1p_nested_h2 import (
    binary_h2_until, predict, select_and_fit,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL_MANIFEST=ROOT/"data/forecast-2027-manifest.json"
PRIOR=ROOT/"data/geo2027-log1p-nested-h2.json"
ISSUE=ROOT/"data/forecast-2027-log1p-shadow.json"
ID="PSICO-GEO2027-STATEBASED25-LOG1P-INTENSITY-SHADOW-V1"
SCHEMA="idealab.psico.geo2027_log1p_intensity_shadow.v1"
PREPARATION_DATE="2026-11-16"
TARGET=2027
ORIGIN=2025


def origin_internal_rows(history):
    """Pre-2027 supervised H2 labels and strictly two-year-delayed predictors."""
    original=counts_to_binary(history)
    rows=[]
    for target in range(2012,ORIGIN+1):
        cutoff=target-2
        preds=binary_h2_until(original,cutoff)
        annual=[]
        for cid,p in preds.items():
            h=history[cid]
            if target not in h:
                continue
            last=h[cutoff]
            annual.append({
                "country_id":cid,"target_year":target,"origin_year":cutoff,
                "origin_deaths":last,"origin_binary":int(last>=25),
                "p_original_binary":p,
                "outcome":int(h[target]>=25),
            })
        if len(annual)<175:
            raise ValueError("Historical inner-year coverage not sufficient")
        rows.extend(annual)
    if min(r["target_year"] for r in rows)!=2012 or max(
        r["target_year"] for r in rows)!=ORIGIN:
        raise ValueError("Inner time controls did not include official 2025 cutoff")
    return rows


def build(raw,original_raw,manifest_raw,prior_raw):
    if hashlib.sha256(raw).hexdigest()!=SOURCES["26.1"]["sha256"]:
        raise ValueError("Original 26.1 official zip changed")
    if hashlib.sha256(original_raw).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Original 2027 public forecast SHA changed")
    original=json.loads(original_raw)
    manifest=json.loads(manifest_raw)
    prior=json.loads(prior_raw)
    if (original.get("forecast_id")!="PSICO-GEO2027-STATEBASED25-V1"
        or original.get("state")!="PREPARED_FOR_PUBLIC_GIT_COMMIT"
        or original.get("target",{}).get("year")!=TARGET
        or original.get("source",{}).get("data_last_year")!=ORIGIN
        or manifest.get("forecast_sha256")!=SOURCE_SHA256
        or manifest.get("status")!="ISSUED_PROSPECTIVE_UNRESOLVED"
        or manifest.get("outcomes_resolved")!=0
        or prior.get("schema")!="idealab.psico.geo2027_log1p_nested_h2_research.v1"
        or prior.get("n_2027_outcomes_resolved")!=0
        or prior.get("evaluation_target_years_previously_inspected_in_prior_research") is not True
        or prior.get("prospective_predictive_skill_demonstrated") is not False):
        raise ValueError("Original GEO issue or prior log1p exploratory provenance altered")
    records=parse_counts(raw,"26.1")
    rows=origin_internal_rows(records)
    beta,control,study=select_and_fit(rows,ORIGIN)
    baseline,_=_fit_at_origin(counts_to_binary(records),ORIGIN)
    old={x["country_id"]:x for x in original["countries"]}
    if len(old)!=196 or set(old)!=set(baseline):
        raise ValueError("Original issued 196-country GEO cohort not reproduced")
    out=[]
    for cid in sorted(old):
        a=old[cid]
        original_p=a["p_model"]
        if (baseline[cid]["origin_state"]!=a["last_observed_state_2025"] or
            abs(baseline[cid]["p_model_h2"]-original_p)>2e-11):
            raise AssertionError("Source-reproduced H2 original differs from immutable issued GEO")
        deaths=records[cid][ORIGIN]
        if int(deaths>=25)!=a["last_observed_state_2025"]:
            raise AssertionError("2025 source intensity contradicts issued origin state")
        feature_row={"p_original_binary":original_p,"origin_deaths":deaths}
        adjusted=round(predict(feature_row,beta),12)
        calibrated=round(predict(feature_row,control),12)
        if not 0<adjusted<1 or not 0<calibrated<1:
            raise ValueError("Shadow probability invalid")
        out.append({
            "country_id":cid,
            "country":a["country"],
            "origin_deaths_best_2025":deaths,
            "origin_binary_state_2025":a["last_observed_state_2025"],
            "original_2027_p_active":original_p,
            "intercept_only_control_p_active_2027":calibrated,
            "log1p_shadow_p_active_2027":adjusted,
        })
    if len(out)!=196 or len({r["country_id"] for r in out})!=196:
        raise ValueError("Prospective shadow has missing/duplicate risk rows")
    if study["final_train_targets"]!=[2012,2025] or (
        study["inner_select_targets"]!=[2018,2020]):
        raise ValueError("Nested training/selection time contract violated")
    return {
        "schema":SCHEMA,
        "forecast_id":ID,
        "issue_class":"SEPARATE_PROSPECTIVE_RESEARCH_SHADOW_NOT_ORIGINAL_2027_ISSUE",
        "publication_date_claim":"NONE_GENERATION_DATE_IS_NOT_PUBLIC_GIT_COMMIT_TIMESTAMP",
        "preparation_calendar_date":PREPARATION_DATE,
        "status":"ISSUED_PROSPECTIVE_UNRESOLVED",
        "source":{"dataset":"UCDP OrganizedViolenceCY","version":"26.1",
                  "sha256":SOURCES["26.1"]["sha256"],
                  "last_observed_year":2025},
        "original_2027_forecast_id":original["forecast_id"],
        "original_2027_immutable_sha256":SOURCE_SHA256,
        "original_2027_issued_first_commit":manifest["first_public_forecast_commit"],
        "target":{"year":2027,"horizon_years":2,
                  "binary_rule":"UCDP official year-2027 country-year sb_total_deaths_best >=25",
                  "primary_first_complete_official_edition_only":True,
                  "unresolved_missing_labels_not_zero":True,
                  "evaluation_same_original_196_country_ids":True,
                  "final_metrics_require_all_196_resolved":True},
        "method":{"type":"logistic offset with two continuous log1p origin-death features",
                  "original_GEO_H2_logit_offset_fixed":True,
                  "inactive_feature":"log1p(d)/log(26), if d<25, else 0",
                  "active_feature":"(log1p(d)-log(26))/log(101), if d>=25, else 0",
                  "inner_fit_target_years":[2012,2017],
                  "inner_select_target_years":[2018,2020],
                  "ridge_candidates":[5.0,20.0,80.0],
                  "historical_holdouts_2024_2025_were_explored_before_method_selection":True,
                  "no_2026_or_2027_label_used":True},
        "training":study,
        "n_countries":len(out),
        "expected_active_countries_original_sum_p":round(
            sum(r["original_2027_p_active"] for r in out),10),
        "expected_active_countries_log1p_sum_p":round(
            sum(r["log1p_shadow_p_active_2027"] for r in out),10),
        "expected_active_countries_intercept_only_sum_p":round(
            sum(r["intercept_only_control_p_active_2027"] for r in out),10),
        "countries":out,
        "outcomes_2027_resolved":0,
        "demonstrated_prospective_skill":False,
        "new_transition_alert_list_issued":False,
        "original_2027_probabilities_or_15_alerts_modified":False,
        "reissuance_of_existing_forecast":False,
        "future_scoring_contract":{
            "primary_metric":"paired_Brier_shadow_minus_original_on_full_196_country_cohort",
            "secondary_metrics":["paired_logloss_shadow_minus_original",
                                 "Brier_shadow_minus_intercept_control",
                                 "logloss_shadow_minus_intercept_control"],
            "first_complete_2027_official_UCDP_edition_primary":True,
            "later_editions_revisions_only":True,
            "no_subgroup_selected_after_outcomes":True,
            "no_post_outcome_retraining_of_issued_shadow":True,
            "multiple_shadow_models_exist_exploratory_comparison_not_one_preselected_winner":True,
            "no_IID_country_significance_from_correlated_country_outcomes":True},
        "limitations":"Prepared after inspecting earlier 2024/25 historical outcomes, so historical model selection is not independently validated. Forecast 2027 is new and future-facing relative to official year-2027 outcome labels, but genuine prospective skill remains unobserved; first public GitHub commit, not preparation date, establishes issue time. Predicts >=25 state-based deaths country-year, not onsets, political changes or causal effects."
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report",action="store_true")
    args=parser.parse_args()
    source=request(SOURCES["26.1"]["url"],MAX_DOWNLOAD)
    forecast=build(source,FORECAST_PATH.read_bytes(),
                   ORIGINAL_MANIFEST.read_bytes(),PRIOR.read_bytes())
    payload=json.dumps(forecast,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    print("GEO2027_LOG1P_PROSPECTIVE_SHADOW_BEGIN")
    print(payload,end="")
    print("GEO2027_LOG1P_PROSPECTIVE_SHADOW_END")
    print("GEO2027_LOG1P_PROSPECTIVE_SHADOW_SHA256 "+
          hashlib.sha256(payload.encode()).hexdigest())
    if args.check_report and ISSUE.read_bytes()!=payload.encode():
        raise ValueError("Prospective 2027 log1p shadow differs from canonical issued bytes")


if __name__=="__main__":
    main()
