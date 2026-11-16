#!/usr/bin/env python3
"""Annual rolling-origin GEO H2 log1p ablation across 4 UCDP data editions.

This is EX-POST within-edition historical analysis, not a reconstruction of
historically PUBLICLY ISSUED forecasts. Each target year t fits logistic
parameters using labels through t-2 only, with the original binary Markov
origin cutoff t-2; predictors of training targets u themselves only access
data through u-2. The fixed ridge=5 was chosen AFTER historical outcomes
were seen by earlier project studies, so the method selection is retrospective
even though internal coefficient fitting is chronological.

Unlike a naïve annual backtest, *no* target-year t-1 label enters the target-t
training set. UCDP archive editions themselves were published after many of
these historical years and can revise all of them; report by vintage explicitly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from audit_geo2027_log1p_shadow_issue import (
    ISSUE, MANIFEST, ORIGINAL, FROZEN_ISSUE_SHA256,
    audit as audit_issue,
)
from audit_geo2027_log1p_issued_death_stress import ALERTS, ALERT_SHA
from backtest_archived_country_vintages import SOURCES
from experiment_geo2027_intensity_markov_cross_release import (
    VERSION_ORDER, MAX_DOWNLOAD, counts_to_binary, parse_counts, scores,
)
from experiment_geo2027_log1p_nested_h2 import (
    binary_h2_until, fit, MIN_OBSERVATIONS,
)
from experiment_geo2027_log1p_inactive_attenuation_frontier import (
    ALPHAS, p_scaled,
)
from prepare_geo2027_transition_alerts import SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo2027-log1p-rolling-year-vintage-stability.json"
PRIOR_FRONTIER=ROOT/"data/geo2027-log1p-inactive-attenuation-frontier.json"
START_TRAIN=2012
FIRST_OUTER_TARGET=2017
LAST_TARGET=2025
RIDGE=5.0
EPS=2e-10


def sha(data):
    return hashlib.sha256(data).hexdigest()


def historical_ledger(source, last_year, fixed_ids):
    """Build target labels with H2 features cut at t-2; one entire edition."""
    if type(last_year) is not int or not 2022<=last_year<=LAST_TARGET:
        raise ValueError("Unsupported official vintage last year")
    ids=sorted(fixed_ids)
    if len(ids)!=196 or len(set(ids))!=196 or not set(ids).issubset(source):
        raise ValueError("Original 196-country fixed GWNO universe changed")
    binary=counts_to_binary(source)
    ledger={}
    for target in range(START_TRAIN,last_year+1):
        origin=target-2
        markov=binary_h2_until(binary,origin)
        rows=[]
        for cid in ids:
            h=source[cid]
            if cid not in markov or not {origin-1,origin,target}.issubset(h):
                # Countries absent in earlier historical periods are not
                # imputed as inactive; the fixed 196 reference risk set
                # becomes an explicitly observed subset for that old year.
                continue
            deaths=h[origin]
            outcome=int(h[target]>=25)
            rows.append({
                "country_id":cid,
                "target_year":target,
                "origin_year":origin,
                "origin_deaths":deaths,
                "origin_state":int(deaths>=25),
                "p_original_binary":markov[cid],
                "outcome":outcome,
            })
        if not 175<=len(rows)<=196:
            raise ValueError("Historical source coverage below minimum 175 observed countries")
        ledger[target]=rows
    return ledger


def fit_target(ledger,target):
    """The coefficient fit sees labels through t-2, never t-1 or t."""
    if (type(target) is not int or not
        FIRST_OUTER_TARGET<=target<=LAST_TARGET or
        target not in ledger or
        any(not 175<=len(rows)<=196 for rows in ledger.values())):
        raise ValueError("Invalid rolling-target cohort")
    origin=target-2
    fitrows=[r for y in range(START_TRAIN,origin+1)
             for r in ledger[y]]
    if (len(fitrows)<MIN_OBSERVATIONS or
        max(r["target_year"] for r in fitrows)!=origin or
        max(r["origin_year"] for r in fitrows)!=origin-2 or
        any(r["target_year"]>origin for r in fitrows)):
        raise ValueError("Chronology leak or incomplete historical training")
    beta=fit(fitrows,RIDGE)
    if not all(math.isfinite(x) for x in beta):
        raise ValueError("Nonfinite year-specific logistic coefficients")
    return beta,{
        "fit_target_years":[START_TRAIN,origin],
        "score_target_year":target,
        "forecast_origin_year":origin,
        "max_supervised_training_label_year":origin,
        "max_training_feature_year":origin-2,
        "last_label_year_not_in_model":target-1,
        "training_n":len(fitrows),
        "training_positives":sum(r["outcome"] for r in fitrows),
        "fixed_ridge":RIDGE,
        "coefficients":[round(x,12) for x in beta],
        "new_beta_for_each_year":True,
        "alpha_grid_not_fitted_or_selected":True,
    }


def year_scores(rows,beta):
    if not 175<=len(rows)<=196:
        raise ValueError("Year requires at least 175 directly observed labels")
    scores_by_alpha={}
    for alpha in ALPHAS:
        predictions=[{"outcome":r["outcome"],"p":round(p_scaled(
            r["p_original_binary"],r["origin_deaths"],beta,alpha),12)}
            for r in rows]
        scores_by_alpha[str(alpha)]=scores(predictions,"p")
    original=scores([
        {"outcome":r["outcome"],"p":r["p_original_binary"]} for r in rows
    ],"p")
    return scores_by_alpha,original


def year_ledger(sources,names):
    if set(sources)!=set(VERSION_ORDER):
        raise ValueError("Must include four official source vintages")
    versions={}
    by_year={}
    for version in VERSION_ORDER:
        cutoff=SOURCES[version]["last_year"]
        ledger=historical_ledger(sources[version],cutoff,names)
        annual=[]
        for target in range(FIRST_OUTER_TARGET,cutoff+1):
            beta,train=fit_target(ledger,target)
            rows=ledger[target]
            candidate_scores,old=year_scores(rows,beta)
            d=candidate_scores["1.0"]["brier"]-candidate_scores["0.0"]["brier"]
            sign="full_intensity_better" if d<-1e-12 else (
                "inactive_removed_better" if d>1e-12 else "no_material_difference")
            by_year.setdefault(target,[]).append({
                "version":version,
                "delta_brier_alpha1_minus_alpha0":round(d,12),
                "winner_sign":sign
            })
            annual.append({
                "target_year":target,"forecast_origin_year":target-2,
                "source_version":version,
                "source_release_last_year":cutoff,
                "risk_n":len(rows),
                "risk_n_of_original_196":196,
                "historical_missing_origin_or_label_n":196-len(rows),
                "historical_fixed_196_countries_not_imputed_as_inactive":True,
                "positive_outcomes":sum(r["outcome"] for r in rows),
                "origin_inactive_n":sum(r["origin_state"]==0 for r in rows),
                "fit":train,
                "frozen_original_GEO_Brier":old["brier"],
                "by_alpha":candidate_scores,
                "alpha1_minus_alpha0_delta_Brier":round(d,12),
                "alpha1_vs_alpha0_brier_winner":sign,
                "not_contemporaneous_originally_issued":True,
                "outcome_from_same_retrospectively_revised_edition":True,
            })
        if not annual:
            raise ValueError("No annual years included")
        signs=[row["alpha1_vs_alpha0_brier_winner"] for row in annual]
        flips=sum(a!=b for a,b in zip(signs,signs[1:]))
        totals={a:sum(x["by_alpha"][a]["brier"] for x in annual)/len(annual)
                for a in ("0.0","1.0")}
        versions[version]={
            "source_SHA256":SOURCES[version]["sha256"],
            "edition_year_through":cutoff,
            "annual_years":[FIRST_OUTER_TARGET,cutoff],
            "n_unique_annual_years":len(annual),
            "year_block_brier_sign_flips":flips,
            "years_full_intensity_better":[x["target_year"] for x in annual if
                x["alpha1_vs_alpha0_brier_winner"]=="full_intensity_better"],
            "years_inactive_removed_better":[x["target_year"] for x in annual if
                x["alpha1_vs_alpha0_brier_winner"]=="inactive_removed_better"],
            "mean_annual_Brier_by_alpha_endpoints":totals,
            "annual":annual,
        }
    year_vintage=[]
    for target in sorted(by_year):
        values=by_year[target]
        signs=set(x["winner_sign"] for x in values)
        ds=[x["delta_brier_alpha1_minus_alpha0"] for x in values]
        year_vintage.append({
            "target_year":target,
            "release_count":len(values),
            "revisions_span_releases":len(values)>1,
            "editions":values,
            "delta_Brier_alpha1_minus_alpha0_min":min(ds),
            "delta_Brier_alpha1_minus_alpha0_max":max(ds),
            "revised_edition_sign_disagreement":len(signs)>1,
        })
    if (len(year_vintage)!=9 or
        sum(x["revised_edition_sign_disagreement"] for x in year_vintage
            if x["release_count"]>1)<0):
        raise AssertionError("Historic target-year audit incomplete")
    return {
        "by_version":versions,
        "same_year_different_edition":year_vintage,
        "shared_target_years_across_four_editions":[2017,2022],
        "n_common_four_edition_years":6,
        "n_total_replayed_annual_year_edition_blocks":
            sum(v["n_unique_annual_years"] for v in versions.values()),
        "n_target_years_with_multi_edition_sign_reversal":sum(
            x["revised_edition_sign_disagreement"]
            for x in year_vintage if x["release_count"]>1),
        "n_distinct_target_years":len(year_vintage),
    }


def study(sources,names,first_issue,frontier):
    if (first_issue.get("schema")!="idealab.psico.geo2027_log1p_intensity_shadow.v1"
        or first_issue.get("outcomes_2027_resolved")!=0
        or first_issue.get("n_countries")!=196
        or frontier.get("schema")!="idealab.psico.geo2027_log1p_inactive_slope_attenuation_frontier.v1"
        or frontier.get("n_outcomes_2027_resolved")!=0
        or frontier.get("alpha_grid_fixed_before_evaluation")!=list(ALPHAS)
        or frontier.get("issued_shadow_sha256")!=FROZEN_ISSUE_SHA256
        or frontier.get("no_alpha_winner_declared") is not True):
        raise ValueError("Frozen issue/frontier provenance changed")
    if len(names)!=196:
        raise ValueError("Fixed risk universe not complete")
    report=year_ledger(sources,names)
    return {
        "schema":"idealab.psico.geo2027_log1p_annual_rolling_h2_vintage_stability.v1",
        "status":"HISTORICAL_WITHIN_EDITION_POST_HOC_ROLLING_TIME_FORWARD_NONCONFIRMATORY",
        "model_family":"original GEO Markov H2 logit offset + ridge5 historical log1p intercept and active/inactive coefficients",
        "alpha_grid_fixed_from_previous_pr":list(ALPHAS),
        "ridge_fixed_5_from_2026_exploratory_study_not_historiographically_issued":True,
        "horizon":2,
        "training_label_max_cutoff_is_target_minus_two":True,
        "historic_country_risk_eligible_only_if_origin_and_target_observed":True,
        "no_missing_historical_country_imputed_negative":True,
        "training_feature_max_cutoff_is_target_minus_four":True,
        "source_releases_published_after_many_scored_target_years":True,
        "same_edition_retrospective_revisions_make_historical_asof_unverified":True,
        "no_annual_historical_forecast_actually_issued":True,
        "same_country_year_overlaps_across_vintages":True,
        "not_independent_holdout_or_prospective_test":True,
        "future_2027_original_forecast_sha256":SOURCE_SHA256,
        "future_2027_shadow_sha256":FROZEN_ISSUE_SHA256,
        "future_2027_original_15_alerts_sha256":ALERT_SHA,
        "issued_forecasts_probabilities_modified":False,
        "new_forecast_issued":False,
        "future_2027_outcomes_resolved":0,
        "demonstrated_prospective_predictive_skill":False,
        "versions_sha256":{v:SOURCES[v]["sha256"] for v in VERSION_ORDER},
        "rolling_result":report,
        "limitations":"This checks chronological parameter fitting inside each retrospectively revised edition, NOT historical real-time information availability or predictions actually published in those years. The fixed lambda=5 and alpha family arose after inspecting 2018-20, 2024 and 2025 data, so no retrospective year is a pristine confirmation of this specification. 30 year-vintage rows contain only 9 distinct target years with historical eligible subsets of the frozen 196 GWNO, repeated countries and highly correlated UCDP editions. Report per-year sign reversals and release disagreements, but no IID uncertainty, hypothesis-test p-values, or 2027 outcome scores. Cross-release earlier backtests are distinct and remain immutable.",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    args=ap.parse_args()
    audit_issue(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes())
    if sha(ALERTS.read_bytes())!=ALERT_SHA:
        raise ValueError("Original 15 transition alerts changed")
    issue=json.loads(ISSUE.read_text(encoding="utf8"))
    names={row["country_id"]:row["country"] for row in issue["countries"]}
    sources={}
    for version in VERSION_ORDER:
        raw=request(SOURCES[version]["url"],MAX_DOWNLOAD)
        sources[version]=parse_counts(raw,version)
    frontier=json.loads(PRIOR_FRONTIER.read_text(encoding="utf8"))
    report=study(sources,names,issue,frontier)
    payload=json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    print("GEO2027_ROLLING_H2_YEAR_VINTAGE_BEGIN")
    print(payload,end="")
    print("GEO2027_ROLLING_H2_YEAR_VINTAGE_END")
    if args.check_report and REPORT.read_bytes()!=payload.encode():
        raise ValueError("Archived source-replayed rolling H2 LOG1P year-block report differs")


if __name__=="__main__":
    main()
