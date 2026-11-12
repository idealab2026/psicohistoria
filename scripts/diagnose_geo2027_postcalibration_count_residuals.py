#!/usr/bin/env python3
"""Historical GEO2027 count residuals BEFORE/AFTER original frozen odds calibration.

Only evaluate the disjoint 2020-23 REVISED-edition and 2024-25 cross-release
historical cohorts. The odds intercepts are the values already fit to 2012-19;
they are NOT refit, retuned or applied to published 2027 forecasts.

Poisson-binomial tails use an ILLUSTRATIVE country-independence assumption,
not a frequentist significance test or fitted cross-country dependence.
Observed overdispersion may be marginal miscalibration, shocks or revision.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from backtest_archived_country_vintages import SOURCES, fetch_archives
from backtest_statebased_2027_spec import from_zip
from diagnose_geo2027_historical_count_dispersion import (
    diagnose as original_count_diagnostic, revised_reference,
)
from diagnose_geo2027_transition_skill import make_holdout_rows
from diagnose_newconf2027_event_count import poisson_binomial
from evaluate_geo2027_calibrated_shadow_official import load_authenticated
from experiment_geo2027_temporal_calibration import (
    COUNT_ARCHIVE, REPORT_PATH, TRAIN_YEARS,
    REVISED_VALIDATION_YEARS, SEPARATE_VALIDATION_YEARS,
    evaluate as original_calibration_evaluate, logistic_shift, transition_pair,
)
from forecast_2027_statebased import download_official
from prepare_geo2027_transition_alerts import SOURCE_SHA256, sha
from build_official_countries import PINNED_SOURCE_SHA256

REPORT = Path("data/geo2027-postcalibration-count-residuals-archival.json")
MIN_PER_GROUP_YEAR = 15
ORIGINAL_SHADOW_SHA = "1d0880f6e95e77d5e203b186e45a035676c7f724ecbe6a8b323f776b9eaa9188"


def annual_metrics(rows, year, state, alpha):
    """Per-year original/global/shift comparisons with IDENTICAL labels and IDs."""
    if year not in (*REVISED_VALIDATION_YEARS, *SEPARATE_VALIDATION_YEARS):
        raise ValueError("Requested year is outside frozen secondary evaluation")
    if state not in (0, 1) or type(state) is not int:
        raise ValueError("Invalid known origin state")
    if type(alpha) is not float or not math.isfinite(alpha):
        raise ValueError("Calibrator has not been verified as a finite frozen scalar")
    selected = [row for row in rows if row["target_year"] == year
                and row["origin_state"] == state]
    if (len(selected) < MIN_PER_GROUP_YEAR
        or len({row["country_id"] for row in selected}) != len(selected)):
        raise ValueError("Missing or duplicated original state-country-year risk set")
    probabilities = {name: [] for name in (
        "issued_country_markov", "historical_odds_intercept",
        "original_global_markov"
    )}
    events = []
    for row in selected:
        q,y=transition_pair(row,"p_model")
        q_global,y_global=transition_pair(row,"p_global_markov")
        if y!=y_global:
            raise ValueError("Frozen model comparators disagree on label")
        events.append(y)
        probabilities["issued_country_markov"].append(q)
        probabilities["historical_odds_intercept"].append(logistic_shift(q,alpha))
        probabilities["original_global_markov"].append(q_global)
    n=len(events)
    observed=sum(events)
    models={}
    for name,ps in probabilities.items():
        if any(type(p) is not float or not math.isfinite(p) or not 0<p<1
               for p in ps):
            raise ValueError("Historical probabilities must be finite and interior")
        expected=sum(ps)
        variance=sum(p*(1-p) for p in ps)
        if variance<=0:
            raise ValueError("Independence count variance cannot be zero")
        pmf=poisson_binomial(ps)
        if abs(sum(pmf)-1)>1e-9:
            raise ValueError("Numerical Poisson-binomial probability mass lost")
        brier=sum((p-y)**2 for p,y in zip(ps,events))/n
        logloss=-sum(y*math.log(p)+(1-y)*math.log1p(-p)
                     for p,y in zip(ps,events))/n
        delta=observed-expected
        models[name]={
            "n":n,
            "observed_transitions":observed,
            "expected_transitions":expected,
            "independence_count_variance":variance,
            "observed_minus_expected_transitions":delta,
            "standardized_count_residual_independence":delta/math.sqrt(variance),
            "squared_standardized_count_residual_independence":delta*delta/variance,
            "brier":brier,
            "log_loss":logloss,
            "illustrative_poisson_binomial_independence_p_at_most_observed":
                min(1.,sum(pmf[:observed+1])),
            "illustrative_poisson_binomial_independence_p_at_least_observed":
                min(1.,sum(pmf[observed:])),
            "these_tails_are_valid_significance_p_values":False,
        }
    return {
        "year":year,
        "origin_state":state,
        "n":n,
        "observed_transitions":observed,
        "models":models,
        "delta_brier_calibrated_minus_original":
            models["historical_odds_intercept"]["brier"] -
            models["issued_country_markov"]["brier"],
        "delta_logloss_calibrated_minus_original":
            models["historical_odds_intercept"]["log_loss"] -
            models["issued_country_markov"]["log_loss"],
    }


def aggregate(rows, years, alpha_by_state, historic_report=None, calibration_report=None,
              *, period):
    years=tuple(years)
    if (period=="REVISED_2020_2023" and years!=REVISED_VALIDATION_YEARS
        or period=="SEPARATED_RELEASES_2024_2025" and
            years!=SEPARATE_VALIDATION_YEARS
        or period not in ("REVISED_2020_2023","SEPARATED_RELEASES_2024_2025")):
        raise ValueError("A fixed full evaluation period is mandatory")
    if set(alpha_by_state)!={0,1}:
        raise ValueError("Exactly two original training-only intercepts required")
    result={}
    for s in (0,1):
        annual=[annual_metrics(rows,year,s,alpha_by_state[s]) for year in years]
        model_metrics={}
        for name in annual[0]["models"]:
            ms=[x["models"][name] for x in annual]
            n_total=sum(x["n"] for x in ms)
            total_events=sum(x["observed_transitions"] for x in ms)
            expected=sum(x["expected_transitions"] for x in ms)
            count_bias=sum(x["observed_minus_expected_transitions"] for x in ms)
            pearson=sum(x["squared_standardized_count_residual_independence"]
                        for x in ms)/len(years)
            model_metrics[name]={
                "country_years":n_total,
                "observed_transitions":total_events,
                "expected_transitions":expected,
                "total_count_bias_observed_minus_expected":count_bias,
                "mean_annual_signed_standardized_count_residual":
                    sum(x["standardized_count_residual_independence"] for x in ms)
                    / len(years),
                "mean_annual_squared_standardized_count_residual":pearson,
                "brier_weighted_by_country_years":
                    sum(x["brier"]*x["n"] for x in ms)/n_total,
                "log_loss_weighted_by_country_years":
                    sum(x["log_loss"]*x["n"] for x in ms)/n_total,
            }
        old=model_metrics["issued_country_markov"]
        cal=model_metrics["historical_odds_intercept"]
        group={
            "n_target_years":len(years),
            "years":list(years),
            "target_year_by_year":annual,
            "models":model_metrics,
            "relative_reduction_in_abs_aggregate_count_bias":
                (abs(old["total_count_bias_observed_minus_expected"]) -
                 abs(cal["total_count_bias_observed_minus_expected"])) /
                abs(old["total_count_bias_observed_minus_expected"])
                if abs(old["total_count_bias_observed_minus_expected"])>1e-10
                else None,
            "calibrated_minus_original_mean_annual_squared_standardized_residual":
                cal["mean_annual_squared_standardized_count_residual"] -
                old["mean_annual_squared_standardized_count_residual"],
            "calibrated_minus_original_weighted_brier":
                cal["brier_weighted_by_country_years"] -
                old["brier_weighted_by_country_years"],
        }
        if historic_report is not None:
            reference=historic_report[str(s)]
            if (reference["number_of_target_years"]!=len(years)
                or reference["n_country_years"]!=old["country_years"]
                or reference["observed_transitions"]!=old["observed_transitions"]
                or abs(reference["expected_model_transitions"] -
                       old["expected_transitions"])>1e-8
                or abs(reference["pearson_dispersion_ratio_model"] -
                       old["mean_annual_squared_standardized_count_residual"])>1e-9):
                raise ValueError("Published historical count dispersion mismatch")
        if calibration_report is not None:
            published=calibration_report["per_known_origin_state"][str(s)][
                "validation_revised_2020_2023" if
                period=="REVISED_2020_2023" else
                "evaluation_separate_source_2024_2025"]
            if (published["country_years"]!=old["country_years"]
                or published["observed_transitions"]!=old["observed_transitions"]
                or abs(published["original_country_markov"]["brier"] -
                       old["brier_weighted_by_country_years"])>1e-10
                or abs(published["odds_intercept_calibrated"]["brier"] -
                       cal["brier_weighted_by_country_years"])>1e-10
                or abs(published["odds_intercept_calibrated"]["expected_events"] -
                       cal["expected_transitions"])>1e-8):
                raise ValueError("Published temporal calibration ablation mismatch")
            if period=="SEPARATED_RELEASES_2024_2025":
                for x in annual:
                    published_year=calibration_report["per_known_origin_state"][str(s)][
                        "cross_vintage_by_year"][str(x["year"])]
                    if (abs(published_year["odds_intercept_calibrated"]["brier"] -
                            x["models"]["historical_odds_intercept"]["brier"])>1e-10
                        or abs(published_year["original_country_markov"]["brier"] -
                               x["models"]["issued_country_markov"]["brier"])>1e-10):
                        raise ValueError("Published 2024/25 annual Brier changed")
        result[str(s)]=group
    return result


def diagnose(revised_rows, separated_rows, source_hashes, count_report,
             calibration_report, original_manifest, shadow_manifest):
    if (source_hashes!={k:SOURCES[k]["sha256"] for k in SOURCES}
        or calibration_report.get("train_years_revised_26_1")!=list(TRAIN_YEARS)
        or calibration_report.get("validation_years_revised_26_1")!=
            list(REVISED_VALIDATION_YEARS)
        or calibration_report.get("external_label_years_source_separated")!=
            list(SEPARATE_VALIDATION_YEARS)
        or calibration_report.get("external_holdout_confirmatory") is not False
        or calibration_report.get("prospective_2027_results_observed")!=0
        or original_manifest.get("forecast_id") not in
            ("PSICO-GEO2027-STATEBASED25-V1",None)
        or shadow_manifest.get("forecast_id")!=
            "PSICO-GEO2027-STATEBASED25-CALIBRATED-SHADOW-V1"
        or shadow_manifest.get("2027_outcomes_resolved")!=0
        or shadow_manifest.get("shadow_forecast_sha256")!=ORIGINAL_SHADOW_SHA):
        raise ValueError("Frozen historical training split or issued shadow changed")
    alpha={}
    for s in (0,1):
        report=calibration_report["per_known_origin_state"][str(s)]
        a=report["alpha_log_odds_shift_estimated_from_2012_2019_only"]
        if (report["origin_state"]!=s or type(a) is not float
            or not math.isfinite(a)):
            raise ValueError("Previously frozen state-only intercept unavailable")
        alpha[s]=a
    revised={y:[row for row in revised_rows if row["target_year"]==y]
             for y in REVISED_VALIDATION_YEARS}
    separated={y:[row for row in separated_rows if row["target_year"]==y]
               for y in SEPARATE_VALIDATION_YEARS}
    if (len(separated_rows)!=392 or sum(x["outcome"] for x in separated_rows)!=69
        or sorted({r["target_year"] for r in separated_rows})!=
            list(SEPARATE_VALIDATION_YEARS)
        or any(len({r["country_id"] for r in revised[y]})<175
               for y in REVISED_VALIDATION_YEARS)
        or any(len({r["country_id"] for r in separated[y]})!=196
               for y in SEPARATE_VALIDATION_YEARS)):
        raise ValueError("Historical source-separated or revised cohort changed")
    periods={
        "revised_2020_2023":aggregate(revised_rows,REVISED_VALIDATION_YEARS,alpha,
             count_report["rolling_origin_12_year_count_diagnostics"],calibration_report,
             period="REVISED_2020_2023"),
        "separated_2024_2025":aggregate(separated_rows,SEPARATE_VALIDATION_YEARS,alpha,
             count_report["cross_release_2_year_count_diagnostics"],calibration_report,
             period="SEPARATED_RELEASES_2024_2025"),
    }
    signs={}
    for period, report in periods.items():
        pairs=[]
        for i,year in enumerate(REVISED_VALIDATION_YEARS if
                                period=="revised_2020_2023" else
                                SEPARATE_VALIDATION_YEARS):
            e0=report["0"]["target_year_by_year"][i]
            e1=report["1"]["target_year_by_year"][i]
            if e0["year"]!=year or e1["year"]!=year:
                raise ValueError("Origin-state annual residual pairs not aligned")
            pairs.append({
                "year":year,
                "original_residual_product":
                    e0["models"]["issued_country_markov"][
                        "standardized_count_residual_independence"] *
                    e1["models"]["issued_country_markov"][
                        "standardized_count_residual_independence"],
                "calibrated_residual_product":
                    e0["models"]["historical_odds_intercept"][
                        "standardized_count_residual_independence"] *
                    e1["models"]["historical_odds_intercept"][
                        "standardized_count_residual_independence"],
                "structural_correlation_estimated":False,
            })
        signs[period]=pairs
    return {
        "schema":"idealab.psico.geo2027_postcalibration_count_residuals.v1",
        "status":"POSTHOC_RETROSPECTIVE_COUNTS_NOT_DEPENDENCE_IDENTIFICATION",
        "source_versions_and_sha256":source_hashes,
        "training_target_years_excluded":list(TRAIN_YEARS),
        "revised_validation_target_years":list(REVISED_VALIDATION_YEARS),
        "separate_release_target_years":list(SEPARATE_VALIDATION_YEARS),
        "three_models":["issued_country_markov","historical_odds_intercept",
                        "original_global_markov"],
        "historical_model_selected_after_outcomes_inspected":True,
        "cross_release_holdout_confirmatory":False,
        "calibration_refit_using_2020_to_2025_outcomes":False,
        "issued_original_forecast_modified":False,
        "issued_shadow_forecast_modified":False,
        "issued_15_alerts_modified":False,
        "2027_outcomes_observed":0,
        "independence_assumption_in_count_variance_and_poisson_binomial_tails":
            "CONDITIONAL_ILLUSTRATIVE_ONLY_NOT_TESTED",
        "periods":periods,
        "same_year_entry_resolution_residual_products_no_inference":signs,
        "structural_cross_country_correlation_estimated":False,
        "independent_p_values_computed":False,
        "limitations":(
            "Annual Pearson count ratio is mean Z_t^2 with Z=(K-E)/sqrt(sum p(1-p)); "
            "both denominator and numerator change after intercept calibration. "
            "No dispersion ratio measures dependence in isolation; a lower "
            "ratio can arise from removal of marginal bias. Poisson-binomial "
            "tails assume unverified conditional independence, are only "
            "descriptive scenarios, and are NOT reported as significance p-values. "
            "2020-23 labels derive from a 2026 REVISED archive (not as-of), "
            "2024-25 from only two separately archived outcomes; the method "
            "was selected after looking at those outcomes. Years overlap in "
            "two-year horizons, countries recur, temporal shocks can persist, "
            "and cross-state residual products are NOT an estimate of shared "
            "country or global shocks. No updates to any 2027 issue."
        ),
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--check-report")
    args=p.parse_args()
    original,shadow,shadow_manifest=load_authenticated()
    if (len(original["countries"])!=196 or len(shadow["countries"])!=196
        or shadow["2027_outcomes_resolved"]!=0):
        raise ValueError("Prospective issued 2027 cohorts not intact")
    raw=download_official()
    if sha(raw)!=PINNED_SOURCE_SHA256:
        raise ValueError("Historical revised 26.1 UCDP ZIP changed")
    records,_=from_zip(raw)
    archives,metadata=fetch_archives()
    recalibrated=json.loads(REPORT_PATH.read_text(encoding="utf8"))
    original_counts=json.loads(COUNT_ARCHIVE.read_text(encoding="utf8"))
    report=diagnose(
        revised_reference(records), make_holdout_rows(archives),
        {k:v["sha256"] for k,v in metadata.items()},
        original_counts,recalibrated,
        json.loads(Path("data/forecast-2027-manifest.json").read_text(encoding="utf8")),
        shadow_manifest,
    )
    raw_report=json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    print("GEO2027_POSTCALIBRATION_COUNT_RESIDUALS_BEGIN")
    print(raw_report,end="")
    print("GEO2027_POSTCALIBRATION_COUNT_RESIDUALS_END")
    if args.check_report and Path(args.check_report).read_bytes()!=raw_report.encode():
        raise ValueError("Frozen post-calibration residual report changed")


if __name__=="__main__":
    main()
