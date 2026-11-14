#!/usr/bin/env python3
"""Historical GEO / NEWCONF year-level count-residual audit; NO 2027 labels.

NEWCONF country onset has seven *single-edition retrospectively reconstructed*
two-year-horizon target years 2016-2022, and exactly ONE source-separated
23.1-origin => 25.1-target year 2024. Do NOT duplicate 2023 horizon-1 as
a second 2-year-horizon observation. GEO comparator uses the already source-
verified archived 12-year revised + 2 separate-release count report. Report
decomposes observed count residual squared into systematic directional bias
vs centered year variation, but CANNOT identify country dependence/correlation.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import build_2027_prospective_registry as issued
from experiment_multiple_newconf import (
    fold, load_multiple, load_activity, CANDIDATES, EXTERNAL_ORIGIN
)
from probe_multiple_onset_vintages import PINNED
from diagnose_geo2027_historical_count_dispersion import (
    REVISED_TARGET_YEARS, SEPARATED_TARGET_YEARS,
)
from backtest_archived_country_vintages import SOURCES as GEO_SOURCES

ROOT=Path(__file__).resolve().parents[1]
NEWCONF_REFERENCE=ROOT/"data/country-multiple-newconf-experiment.json"
GEO_REFERENCE=ROOT/"data/geo2027-historical-count-dispersion-archival.json"
REPORT=ROOT/"data/historical-geo-newconf-annual-residuals.json"
ORIGINS=tuple(range(2014,2021))
TARGET_YEARS=tuple(year+2 for year in ORIGINS)
NEWCONF_MODELS=("activity_country","global_last5")
EPS=1e-11


def count_residual(rows:list[dict],year:int,model:str)->dict:
    if model not in NEWCONF_MODELS or year not in (*TARGET_YEARS,2024):
        raise ValueError("Unsupported historical NEWCONF year or model")
    if (len(rows)!=196 or
        len({r.get("country") for r in rows})!=196 or
        any(r.get("target_year")!=year or
            r.get("horizon")!=2 or
            r.get("origin_year")!=year-2 for r in rows)):
        raise ValueError("NEWCONF 196 country 2-year horizon risk set changed")
    total=0;expect=0.;variance=0.
    for r in rows:
        k=r.get("outcome")
        p=r.get(model)
        if type(k) is not int or k not in (0,1):
            raise ValueError("Missing or invalid NEWCONF outcome cannot be zero")
        if type(p) not in (int,float) or not math.isfinite(p) or not 0<p<1:
            raise ValueError("Invalid origin-only prediction")
        total+=k;expect+=p;variance+=p*(1-p)
    if variance<=0:
        raise ValueError("No independent-Bernoulli count variance")
    z=(total-expect)/math.sqrt(variance)
    return {
        "target_year":year,
        "origin_year":year-2,
        "n_eligible_countries":len(rows),
        "observed_newconf_country_years":total,
        "expected_count_from_origin_only_model":expect,
        "independence_count_variance_for_model":variance,
        "observed_minus_expected":total-expect,
        "standardized_count_residual":z,
        "squared_standardized_count_residual":z*z,
        "source_issues_outcomes_observed_2027":0,
    }


def annual_decomposition(annual:list[dict], *, zkey:str,
                         first_target_year:int,
                         expected_years:int,
                         forward_min_history:int)->dict:
    """Exact empirical mean-bias + centered mean-square identity.

    Forward-only correction is an exploratory *count diagnostic*, not an
    alteration to forecasts or an operational predictive calibration.
    Counts are one realization per year; no IID sampling or effective n.
    """
    if (not isinstance(annual,list) or len(annual)!=expected_years or
        not 1<=forward_min_history<expected_years):
        raise ValueError("Invalid year panel size/history")
    years=[x.get("target_year") for x in annual]
    if years!=list(range(first_target_year,first_target_year+expected_years)):
        raise ValueError("Out-of-order, overlapping or incomplete target years")
    z=[]
    for x in annual:
        val=x.get(zkey)
        if type(val) not in (float,int) or not math.isfinite(val):
            raise ValueError("Invalid source-derived standardized count residual")
        z.append(float(val))
    bias=sum(z)/len(z)
    total=sum(v*v for v in z)/len(z)
    centered=sum((v-bias)**2 for v in z)/len(z)
    if abs(total-(bias*bias+centered))>EPS:
        raise ValueError("Count bias/variance decomposition identity broken")
    forward=[]
    for ix in range(forward_min_history,len(z)):
        old_mean=sum(z[:ix])/ix
        forward.append({
            "target_year":years[ix],
            "n_earlier_years_used_for_count_bias":ix,
            "count_bias_estimate_from_earlier_target_years_only":old_mean,
            "uncorrected_standardized_residual":z[ix],
            "posthoc_bias_adjusted_standardized_residual":z[ix]-old_mean,
        })
    return {
        "n_target_years":len(z),
        "target_years":years,
        "mean_signed_standardized_count_residual":bias,
        "mean_squared_standardized_count_residual":total,
        "mean_squared_directional_bias_component":bias*bias,
        "mean_centered_squared_year_residual":centered,
        "fraction_of_raw_squared_residual_due_to_mean_bias":(
            bias*bias/total if total else None),
        "positive_count_residual_years":sum(v>0 for v in z),
        "negative_count_residual_years":sum(v<0 for v in z),
        "raw_independence_pearson_ratio_years":total,
        "forward_only_pseudo_bias_adjusted_diagnostics":{
            "first_scored_target_year":years[forward_min_history],
            "n_scored_years":len(forward),
            "raw_mean_squared_residual_scored_years":
                sum(d["uncorrected_standardized_residual"]**2
                    for d in forward)/len(forward),
            "adjusted_mean_squared_residual_scored_years":
                sum(d["posthoc_bias_adjusted_standardized_residual"]**2
                    for d in forward)/len(forward),
            "annual_adjustment_trace":forward,
            "independently_issued_historical_forecasts":False,
            "revised_historical_labels_available_asof_origins":False,
            "is_not_a_new_model_or_unbiased_out_of_sample_score":True,
        },
    }


def _cross_year_only(annual:list[dict], prior_bias:float,zkey:str)->dict:
    """One or two separately versioned target years: NEVER estimate covariance."""
    if not annual or len(annual)>2 or not math.isfinite(prior_bias):
        raise ValueError("Require one/two fixed distinct historical source years")
    result=[]
    for a in annual:
        z=a[zkey]
        if type(z) not in (int,float) or not math.isfinite(z):
            raise ValueError("Invalid annual residual")
        result.append({
            "target_year":a["target_year"],
            "standardized_count_residual":z,
            "earlier_revised_block_mean_bias_applied_only_as_sensitivity":prior_bias,
            "posthoc_bias_centered_residual":z-prior_bias,
        })
    return {
        "n_separate_release_target_years":len(result),
        "annual":result,
        "raw_mean_squared_standardized_residual":
            sum(v["standardized_count_residual"]**2 for v in result)/len(result),
        "bias_centered_mean_squared_standardized_residual":
            sum(v["posthoc_bias_centered_residual"]**2
                for v in result)/len(result),
        "cannot_estimate_covariance_from_one_or_two_target_years":True,
    }


def geo_existing_frozen_report()->dict:
    g=json.loads(GEO_REFERENCE.read_text(encoding="utf8"))
    if (g["schema"]!="idealab.psico.geo2027_historical_count_dispersion.v1"
        or g["2027_outcomes_observed"]!=0
        or g["rolling_origin_reference_years"]!=list(REVISED_TARGET_YEARS)
        or g["separate_release_target_years"]!=list(SEPARATED_TARGET_YEARS)
        or g["source_rolling_sha256"]!=GEO_SOURCES["26.1"]["sha256"]
        or g["cross_release_source_sha256"]!={v:x["sha256"]
            for v,x in GEO_SOURCES.items()}):
        raise ValueError("Original source-pinned GEO historical count record changed")
    out={}
    for state in ("0","1"):
        original=g["rolling_origin_12_year_count_diagnostics"][state]
        external=g["cross_release_2_year_count_diagnostics"][state]
        yr=original["yearly_aggregate_count_residuals"]
        extra=external["yearly_aggregate_count_residuals"]
        if (len(yr)!=12 or len(extra)!=2 or
            any(x["origin_state"]!=int(state) for x in yr+extra) or
            sum(x["n"] for x in yr)!=original["n_country_years"] or
            sum(x["n"] for x in extra)!=external["n_country_years"]):
            raise ValueError("GEO historical state/time cohort changed")
        analyzed=annual_decomposition(
            yr,zkey="normalized_count_residual",
            first_target_year=2012,expected_years=12,
            forward_min_history=4)
        if (abs(analyzed["mean_squared_standardized_count_residual"]-
                original["pearson_dispersion_ratio_model"])>EPS):
            raise ValueError("GEO source-pinned Pearson ratio identity broken")
        independent=_cross_year_only(
            extra,analyzed["mean_signed_standardized_count_residual"],
            "normalized_count_residual")
        out[state]={
            "definition":"entry 0->1" if state=="0" else "resolution 1->0",
            "revised_2012_2023":analyzed,
            "source_separated_2024_2025":independent,
            "distinct_from_NEWCONF2027_endpoint":True,
        }
    return out


def diagnose_from_annual(newconf_revised:dict,newconf_external:dict,
                         geo:dict,meta:dict)->dict:
    """Pure aggregation; source acquisition is separately SHA-pinned."""
    if (set(newconf_revised)!=set(NEWCONF_MODELS) or
        set(newconf_external)!=set(NEWCONF_MODELS) or
        set(geo)!={"0","1"} or
        set(meta)!={"23.1","25.1","activity_23.1"}):
        raise ValueError("Historical source model or endpoint scope changed")
    out={}
    for model in NEWCONF_MODELS:
        annual=newconf_revised[model]
        external=newconf_external[model]
        if len(external)!=1 or external[0]["target_year"]!=2024:
            raise ValueError("Only first later-edition 2024 horizon-2 year permitted")
        if (sum(r["n_eligible_countries"] for r in annual)!=1372
            or sum(r["observed_newconf_country_years"] for r in annual)!=18
            or external[0]["n_eligible_countries"]!=196 or
            external[0]["observed_newconf_country_years"]!=1):
            raise ValueError("Source-verified NEWCONF fixed historical sample changed")
        results=annual_decomposition(
            annual,zkey="standardized_count_residual",
            first_target_year=2016,expected_years=7,
            forward_min_history=3)
        separate=_cross_year_only(
            external,results["mean_signed_standardized_count_residual"],
            "standardized_count_residual")
        out[model]={
            "source_revised_2016_2022":results,
            "separate_source_2024":separate,
            "annual_horizon_2_revised_years":annual,
            "annual_horizon_2_separate_source_years":external,
        }
    return {
        "schema":"idealab.psico.geo_newconf2027_empirical_historical_count_bias_v1",
        "status":"EX_POST_HISTORICAL_YEAR_COUNT_MISFIT_NOT_IDENTIFIED_COUNTRY_DEPENDENCE",
        "historical_newconf_source_hashes":meta,
        "historical_geo_source_hashes":{
            v:x["sha256"] for v,x in GEO_SOURCES.items()},
        "n_2027_country_endpoint_questions_preserved":424,
        "2027_outcomes_used":0,
        "historical_newconf_definition":"ANY(newconf=1) country-year per UCDP Intrastate Country Level Multiple Onset; repeated episode rows collapsed, not onset2",
        "historical_geo_definition":"GEO state-based violence >=25 annual deaths; 2-year transition 0->1 and 1->0 stratified",
        "newconf_origin_only_model_comparison_revised_and_separated":out,
        "geo_pinned_existing_annual_count_reanalysis_by_origin_state":geo,
        "full_joint_country_copula_estimated":False,
        "structural_country_correlation_estimated":False,
        "temporal_correlation_estimated":False,
        "sampled_target_years_are_independent_or_confirmatory":False,
        "n_independent_historical_2027_validation_years":0,
        "mean_count_bias_is_not_country_dependence":True,
        "limitations":(
            "Seven NEWCONF 2016-22 years use a single retrospectively revised "
            "23.1 release, not independently issued origins; 2024 is only ONE "
            "target from independent 25.1 release, origin 23.1 (horizon=2). "
            "Do not include 2023 horizon-1 as another independent horizon-2 "
            "target. GEO has 12 revised 2012-23 and two separate-release "
            "2024-25 years but source vintage revisions and shared countries. "
            "Observed-vs-expected Pearson count residuals mix marginal "
            "forecast calibration, year effects, regime shifts, dependence, "
            "country selection and revisions. The squared mean signed "
            "standardized residual is an ALGEBRAIC bias component, not a "
            "causal identification of correlation. Historical pseudo-forward "
            "count corrections are retrospective diagnostics, never emitted "
            "forecasts, verified operational calibration or permission to "
            "modify 2027 first-issued forecasts. Models and endpoints differ "
            "and their metrics must not be pooled. There are too few "
            "source-separated year replicates to estimate structural or "
            "temporal correlations; no p-values or predictive intervals."
        ),
    }


def evaluate()->dict:
    docs,manifests=issued.read_issued()
    registry=issued.make_registry(docs,manifests)
    if (registry["n_unique_country_endpoint_rows"]!=424
        or registry["n_verified_future_2027_outcomes"]!=0):
        raise ValueError("Immutable first-issued future cohort registry mismatch")
    frozen=json.loads(NEWCONF_REFERENCE.read_text(encoding="utf8"))
    if (frozen["schema"]!="idealab.psico.country_multiple_newconf_v231_v251_exploratory.v1"
        or frozen["2027_outcomes_evaluated"]!=0
        or frozen["rolling_internal_origin_years"]!=list(ORIGINS)
        or frozen["target_years"]!=[2023,2024]
        or frozen["source_multiple_onset_sha256"]!={
            v:PINNED[v]["sha256"] for v in PINNED}
        or frozen["external"]["positive_forecast_evaluations"]!=3):
        raise ValueError("Original officially pinned historical NEWCONF study changed")
    source_old,meta_old=load_multiple("23.1")
    source_later,meta_later=load_multiple("25.1")
    active,meta_active=load_activity("23.1")
    # Frozen prior study reproducibility is separately required by existing
    # workflow; current study authenticates all 3 original source ZIP/CSV
    # bytes via load_multiple/load_activity SHA-pins.
    old={model:[] for model in NEWCONF_MODELS}
    later={model:[] for model in NEWCONF_MODELS}
    for origin in ORIGINS:
        rows,details=fold(source_old,source_old,active,origin,2)
        if (details["origin_year"]!=origin or
            details["positive_country_years"]!=sum(r["outcome"] for r in rows)):
            raise ValueError("Reconstructed revised NEWCONF fold changes")
        for model in NEWCONF_MODELS:
            old[model].append(count_residual(rows,origin+2,model))
    rows,details=fold(source_old,source_later,active,EXTERNAL_ORIGIN,2)
    if details["positive_country_years"]!=1 or details["target_year"]!=2024:
        raise ValueError("External UCDP 25.1 target sample changed")
    for model in NEWCONF_MODELS:
        later[model].append(count_residual(rows,2024,model))
    report=diagnose_from_annual(old,later,geo_existing_frozen_report(),{
        "23.1":meta_old.get("source_sha256",PINNED["23.1"]["sha256"]),
        "25.1":meta_later.get("source_sha256",PINNED["25.1"]["sha256"]),
        "activity_23.1":meta_active["sha256"],
    })
    # Treat the previous 23.1 ACD activity SHA as a separate source pin,
    # not as a new country/newconf endpoint.
    if (report["historical_newconf_source_hashes"]["activity_23.1"]!=
        frozen["source_metadata"]["acd_23_sha256"] or
        report["historical_newconf_source_hashes"]["23.1"]!=PINNED["23.1"]["sha256"] or
        report["historical_newconf_source_hashes"]["25.1"]!=PINNED["25.1"]["sha256"]):
        raise ValueError("Original SHA-frozen NEWCONF source provenance changed")
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--check-report")
    args=p.parse_args()
    report=evaluate()
    body=issued.canonical(report)
    if args.check_report and Path(args.check_report).read_bytes()!=body:
        raise ValueError("Frozen historical GEO+NEWCONF annual residual audit changed")
    print("HISTORICAL_GEO_NEWCONF_COUNT_RESIDUALS_BEGIN")
    print(body.decode(),end="")
    print("HISTORICAL_GEO_NEWCONF_COUNT_RESIDUALS_END")


if __name__=="__main__":
    main()
