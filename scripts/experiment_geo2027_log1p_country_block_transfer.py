#!/usr/bin/env python3
"""Country-block logistic calibration transfer under historical 1–24 deaths.

No retrospective variant can become a reissued 2027 forecast. For each
historical target t, fit LOG1P ridge=5 using outcomes through t-2 only,
then refit the LOGISTIC calibration with all years of one subthreshold
target-country withheld. Evaluate the country held out from that regression.

Original GEO Markov H2 offset DOES retain that country's pre-origin history,
as is legitimate for an established-country risk forecast, including its
global contribution. Thus this is country-block calibration transfer, NOT
cold-start prediction or LOCO refitting of the Markov estimator.

Compare all nine distinct target years 2017..25 in 26.1, 2017 in 23.1,
24.1,25.1, and 2024 in 25.1. Editions reuse target-year events; not iid.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from audit_geo2027_log1p_shadow_issue import (
    ISSUE, ORIGINAL, MANIFEST, FROZEN_ISSUE_SHA256,
    audit as audit_issued_shadow,
)
from audit_geo2027_log1p_issued_death_stress import ALERTS, ALERT_SHA
from backtest_archived_country_vintages import SOURCES
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD, parse_counts, VERSION_ORDER,
)
from experiment_geo2027_log1p_nested_h2 import fit
from experiment_geo2027_log1p_inactive_attenuation_frontier import (
    p_scaled,
)
from experiment_geo2027_log1p_rolling_year_vintage import (
    historical_ledger, fit_target, year_scores, sha, RIDGE, START_TRAIN,
)
from prepare_geo2027_transition_alerts import SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo2027-log1p-subthreshold-country-block-transfer.json"
REFERENCE=ROOT/"data/geo2027-log1p-rolling-year-vintage-stability.json"
CONTRIBUTIONS=ROOT/"data/geo2027-log1p-country-year-reversal-attribution.json"
TARGETS=tuple(range(2017,2026))
# Nine distinct years in 26.1, plus 2017 in three older editions and
# 2024 in 25.1. Research variants fixed *before* looking at this report.
COMPARISONS=(tuple(("26.1",target) for target in TARGETS)
             +tuple((edition,2017) for edition in ("23.1","24.1","25.1"))
             +( ("25.1",2024), ))
FOCUS=(2017,2024,2025)
TOL=6e-10


def score_gap(p_zero,p_full,y):
    if (not all(type(p) in (int,float) and math.isfinite(p)
                and 0<p<1 for p in (p_zero,p_full))
        or y not in (0,1)):
        raise ValueError("Bad probability or outcome in paired score")
    return ((p_full-y)**2-(p_zero-y)**2)


def calibration_training(ledger,target):
    """Held-out country's ALL historical supervised rows are eliminated."""
    if target not in ledger or target<2017:
        raise ValueError("Unknown country-heldout target")
    origin=target-2
    rows=[r for year in range(START_TRAIN,origin+1) for r in ledger[year]]
    if (len(rows)<500 or
        max(r["target_year"] for r in rows)!=origin or
        max(r["origin_year"] for r in rows)!=origin-2 or
        any(r["target_year"]>origin for r in rows)):
        raise ValueError("Future training label or feature leaked")
    return rows


def omit_country_fit(rows,cid,target):
    if type(cid) is not int or not 2017<=target<=2025:
        raise ValueError("Bad country or target")
    original_n=sum(r["country_id"]==cid for r in rows)
    kept=[r for r in rows if r["country_id"]!=cid]
    if (original_n<3 or len(kept)<500 or
        any(r["country_id"]==cid or r["target_year"]>target-2
            or r["origin_year"]>target-4 for r in kept)):
        raise ValueError("Historical country exclusion or time cutoff violated")
    return fit(kept,RIDGE), {
        "country_id":cid,"removed_historical_rows":original_n,
        "remaining_historical_train_n":len(kept),
        "last_training_label_year":max(r["target_year"] for r in kept),
        "last_training_feature_year":max(r["origin_year"] for r in kept),
        "markov_offset_stays_original_with_country_history":True,
    }


def one_year(ledger,target,names,reference,*,full_details=False):
    beta,meta=fit_target(ledger,target)
    historical=ledger[target]
    metrics,_=year_scores(historical,beta)
    prior=reference["rolling_result"]["by_version"] # passed full report
    edition=reference["current_edition"]
    prior_row=next(r for r in prior[edition]["annual"]
                   if r["target_year"]==target)
    if (meta["coefficients"]!=prior_row["fit"]["coefficients"]
        or meta["training_n"]!=prior_row["fit"]["training_n"]
        or abs(metrics["1.0"]["brier"]-
               prior_row["by_alpha"]["1.0"]["brier"])>TOL):
        raise AssertionError("Prior annual rolling-forecast coefficients/score differ")
    training=calibration_training(ledger,target)
    affected=[r for r in historical if 1<=r["origin_deaths"]<=24]
    if not affected or len(affected)>196:
        raise ValueError("No eligible subthreshold effect countries")
    reports=[]
    for row in affected:
        cid=row["country_id"]; death=row["origin_deaths"]; y=row["outcome"]
        recal,trainmeta=omit_country_fit(training,cid,target)
        # Original Markov country-state history remains known by design.
        pzero=round(p_scaled(row["p_original_binary"],death,recal,0.0),12)
        pfull=round(p_scaled(row["p_original_binary"],death,recal,1.0),12)
        full_p0=round(p_scaled(row["p_original_binary"],death,beta,0.0),12)
        full_p1=round(p_scaled(row["p_original_binary"],death,beta,1.0),12)
        d=score_gap(pzero,pfull,y)
        base=score_gap(full_p0,full_p1,y)
        reports.append({
            "country_id":cid,"country":names[cid],
            "origin_deaths":death,
            "origin_state":0,
            "target_binary_outcome":y,
            "original_markov_p_h2":row["p_original_binary"],
            "fullfit_alpha0_p":full_p0,"fullfit_alpha1_p":full_p1,
            "country_excluded_alpha0_p":pzero,
            "country_excluded_alpha1_p":pfull,
            "fullfit_paired_Brier_delta":round(base,12),
            "country_excluded_paired_Brier_delta":round(d,12),
            "country_exclusion_changed_delta":round(d-base,12),
            "country_excluded_beta":[round(x,12) for x in recal],
            "fullfit_beta":[round(x,12) for x in beta],
            "absolute_inactive_beta_shift":round(abs(recal[1]-beta[1]),12),
            "absolute_active_beta_shift":round(abs(recal[2]-beta[2]),12),
            "absolute_intercept_shift":round(abs(recal[0]-beta[0]),12),
            "historical_country_removed_for_calibration":trainmeta,
            "Markov_country_history_retained":True,
        })
    country_full=sum(x["fullfit_paired_Brier_delta"] for x in reports)
    country_cross=sum(x["country_excluded_paired_Brier_delta"] for x in reports)
    delta_original=metrics["1.0"]["brier"]-metrics["0.0"]["brier"]
    if abs(country_full/len(historical)-delta_original)>TOL:
        raise AssertionError("Fullfit 1–24 countries must exactly reproduce annual Brier")
    n=len(affected)
    def describe(x):
        return "full_intensity_better" if x<-1e-12 else (
            "no_inactive_intensity_better" if x>1e-12 else "effectively_equal")
    full_sign=describe(country_full)
    blocked_sign=describe(country_cross)
    abs_shift=[x["absolute_inactive_beta_shift"] for x in reports]
    signed_delta=[x["country_excluded_paired_Brier_delta"] for x in reports]
    by_outcome={}
    for state in (0,1):
        subgroup=[r for r in reports if r["target_binary_outcome"]==state]
        by_outcome[str(state)]={
            "n":len(subgroup),
            "fullfit_paired_Brier_delta_sum":round(sum(
                r["fullfit_paired_Brier_delta"] for r in subgroup),12),
            "blocked_calibration_paired_Brier_delta_sum":round(sum(
                r["country_excluded_paired_Brier_delta"] for r in subgroup),12),
            "blocked_conditional_mean_delta":round(sum(
                r["country_excluded_paired_Brier_delta"] for r in subgroup
            )/len(subgroup),12) if subgroup else None,
        }
    ordered=sorted(reports,key=lambda x:(
        -abs(x["country_exclusion_changed_delta"]),x["country_id"]))
    return {
        "target_year":target,"origin_year":target-2,
        "source_version":edition,
        "risk_n":len(historical),
        "subthreshold_1_to_24_n":n,
        "subthreshold_actual_active_target_n":sum(
            x["target_binary_outcome"] for x in reports),
        "fixed_ridge_lambda":RIDGE,
        "training_labels_latest_year":meta["max_supervised_training_label_year"],
        "training_features_latest_year":meta["max_training_feature_year"],
        "no_target_year_training_outcome":True,
        "country_historical_calibration_rows_excluded_per_case":True,
        "country_markov_history_not_excluded":True,
        "fullfit_delta_Brier_annual":round(delta_original,12),
        "blocked_delta_Brier_on_full_risk_n":round(country_cross/len(historical),12),
        "fullfit_delta_Brier_within_subthreshold":round(country_full/n,12),
        "blocked_delta_Brier_within_subthreshold":round(country_cross/n,12),
        "fullfit_winner":full_sign,
        "country_blocked_winner":blocked_sign,
        "country_blocking_flips_annual_winner":full_sign!=blocked_sign,
        "blocked_country_delta_sum":round(country_cross,12),
        "fullfit_country_delta_sum":round(country_full,12),
        "mean_absolute_calibration_beta_inactive_shift":round(
            sum(abs_shift)/n,12),
        "max_absolute_calibration_beta_inactive_shift":max(abs_shift),
        "country_blocked_Brier_contribution_by_future_outcome":by_outcome,
        "n_blocked_individual_effect_sign_changes":sum(
            describe(x["fullfit_paired_Brier_delta"])!=
            describe(x["country_excluded_paired_Brier_delta"])
            for x in reports),
        "largest_5_absolute_changes_due_to_country_blocking":ordered[:5],
        "all_subthreshold_cases":reports if full_details else [],
        "all_cases_stored":full_details,
        "not_an_untouched_prospective_holdout":True,
    }


def study(sources,names,reference,prior_contributions):
    if (reference.get("schema")!="idealab.psico.geo2027_log1p_annual_rolling_h2_vintage_stability.v1"
        or reference.get("future_2027_outcomes_resolved")!=0
        or prior_contributions.get("schema")!=
            "idealab.psico.geo2027_log1p_annual_country_reversal_attribution.v1"
        or prior_contributions.get("resolved_official_2027_labels")!=0
        or len(names)!=196 or set(sources)!=set(VERSION_ORDER)):
        raise ValueError("Official prior annual and country attribution provenance changed")
    ledgers={
        version:historical_ledger(counts,SOURCES[version]["last_year"],names)
        for version,counts in sources.items()
    }
    blocks=[]
    for version,target in COMPARISONS:
        prior={**reference,"current_edition":version}
        result=one_year(
            ledgers[version],target,names,prior,
            full_details=(target in FOCUS))
        blocks.append(result)
    latest=[b for b in blocks if b["source_version"]=="26.1"]
    if (len(latest)!=9 or len(blocks)!=13 or
        [x["target_year"] for x in latest]!=list(TARGETS)):
        raise AssertionError("Must reconstruct nine 26.1 years and four vintage replicates")
    return {
        "schema":"idealab.psico.geo2027_log1p_country_block_calibration_transfer.v1",
        "status":"POST_HOC_COUNTRY_BLOCK_LOGISTIC_CALIBRATION_ONLY",
        "purpose":"Assess whether historical 1-24-origin-death intensity signal depends on the calibration labels of each evaluated country",
        "baseline_forecast_original_sha256":SOURCE_SHA256,
        "baseline_forecast_shadow_sha256":FROZEN_ISSUE_SHA256,
        "baseline_issued_15_alerts_sha256":ALERT_SHA,
        "source_sha256":{v:SOURCES[v]["sha256"] for v in VERSION_ORDER},
        "ridge_5_selected_in_prior_exploratory_work_not_retuned":True,
        "full_original_GEO_markov_country_history_is_retained":True,
        "country_block_is_logistic_calibrator_only":True,
        "all_training_country_labels_removed_before_country_scoring":True,
        "each_target_training_label_cutoff_t_minus_2":True,
        "each_target_training_feature_cutoff_t_minus_4":True,
        "not_a_fully_country_unseen_Markov_model":True,
        "historical_2017_to_2025_editions_revised_not_asof_issued":True,
        "three_years_with_detail":list(FOCUS),
        "n_distinct_target_years_26_1":9,
        "n_year_edition_blocks":13,
        "replications_2017_editions":["23.1","24.1","25.1","26.1"],
        "replications_2024_editions":["25.1","26.1"],
        "edition_replications_not_independent":True,
        "no_model_or_alpha_selected_with_expost_results":True,
        "no_2027_forecasts_issued_or_reissued":True,
        "no_prospective_2027_outcomes":True,
        "prospective_skill_not_established":True,
        "baseline_orig_geo_not_modified":True,
        "baseline_log1p_shadow_not_modified":True,
        "baseline_alerts_not_modified":True,
        "all_blocks":blocks,
        "latest_26_1_country_block_summary":[{
            "target_year":x["target_year"],
            "affected_country_n":x["subthreshold_1_to_24_n"],
            "subthreshold_target_active_n":x["subthreshold_actual_active_target_n"],
            "annual_Brier_delta_fullfit":x["fullfit_delta_Brier_annual"],
            "annual_Brier_delta_country_blocked_logistic":x["blocked_delta_Brier_on_full_risk_n"],
            "sign_flip_when_calibration_country_excluded":
                x["country_blocking_flips_annual_winner"],
            "mean_abs_inactive_beta_shift":
                x["mean_absolute_calibration_beta_inactive_shift"],
        } for x in latest],
        "limitations":"This is ex post blocked-country CALIBRATOR transfer at fixed historical t-2 origin, not cold-start prediction: the GEO Markov baseline legitimately uses the target country's earlier transitions. Country-excluded training changes both alpha0 and alpha1 probabilities through the shared re-fitted intercept, but only their intensity difference is being compared. The variants/penalty were devised in 2026 after inspecting past outcomes; retrospective results do not validate prospective effectiveness. Same countries and shared revised editions are correlated; no iid statistical certainty or future 2027 labels. Historical 1-24 countries are selected by PAST source counts only, not by future outcome."
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    args=ap.parse_args()
    audit_issued_shadow(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes())
    if sha(ALERTS.read_bytes())!=ALERT_SHA:
        raise ValueError("Frozen 15 alerts SHA mismatch")
    issue=json.loads(ISSUE.read_text(encoding="utf8"))
    names={r["country_id"]:r["country"] for r in issue["countries"]}
    sources={
        v:parse_counts(request(SOURCES[v]["url"],MAX_DOWNLOAD),v)
        for v in VERSION_ORDER}
    reference=json.loads(REFERENCE.read_text(encoding="utf8"))
    prior=json.loads(CONTRIBUTIONS.read_text(encoding="utf8"))
    report=study(sources,names,reference,prior)
    payload=json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    print("GEO2027_COUNTRY_BLOCK_TRANSFER_BEGIN")
    print(payload,end="")
    print("GEO2027_COUNTRY_BLOCK_TRANSFER_END")
    if args.check_report and REPORT.read_bytes()!=payload.encode():
        raise ValueError("Country-block logistic transfer UCDP replay differs from published exact report")


if __name__=="__main__":
    main()
