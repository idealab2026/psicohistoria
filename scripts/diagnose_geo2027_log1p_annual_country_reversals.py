#!/usr/bin/env python3
"""Exact country/year Brier reversal attribution for frozen GEO2027 LOG1P family.

This is a post-hoc explanation of why inactive log1p alpha=1 beats alpha=0
for 2018–24 but not for 2017 and 2025 in previous rolling-origin research.

For every 2017..2025 target in each of four SHA-pinned UCDP editions:
  * compute original strict t-2 rolling-origin H2 forecast & logistic fit;
  * compute exact per-country paired squared-error difference with fixed fit;
  * decompose into origin deaths 0, 1–24, >=25 and eventual binary outcome;
  * audit concentrated countries and no-refit leave-one-out sign flips;
  * compare signed 2017/2024/2025 country effects across vintage revisions.

ZERO 2027 outcomes; ZERO new issued forecasts. Historical editions are
retrospectively revised; ridge lambda=5 and alpha family were chosen after
some historical outcomes were already observed by the research programme.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from audit_geo2027_log1p_shadow_issue import (
    ISSUE, MANIFEST, ORIGINAL, FROZEN_ISSUE_SHA256,
    audit as audit_issued_shadow,
)
from audit_geo2027_log1p_issued_death_stress import ALERTS, ALERT_SHA
from backtest_archived_country_vintages import SOURCES
from experiment_geo2027_intensity_markov_cross_release import (
    VERSION_ORDER, MAX_DOWNLOAD, parse_counts,
)
from experiment_geo2027_log1p_inactive_attenuation_frontier import (
    ALPHAS, p_scaled,
)
from experiment_geo2027_log1p_rolling_year_vintage import (
    FIRST_OUTER_TARGET, LAST_TARGET, historical_ledger, fit_target,
    year_scores, sha,
)
from prepare_geo2027_transition_alerts import SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo2027-log1p-country-year-reversal-attribution.json"
PRIOR=ROOT/"data/geo2027-log1p-rolling-year-vintage-stability.json"
FOCUS_YEARS=(2017,2024,2025)
EPS=4e-10


def brier_effect(p_zero,p_full,outcome):
    """Exact *signed* Brier difference per country for alpha1 minus alpha0."""
    if (not all(type(x) in (float,int) and math.isfinite(x) and 0<x<1
                for x in (p_zero,p_full))
        or outcome not in (0,1)):
        raise ValueError("Malformed paired Brier case")
    direct=(p_full-outcome)**2-(p_zero-outcome)**2
    product=(p_full-p_zero)*(p_full+p_zero-2*outcome)
    if abs(direct-product)>1e-12:
        raise AssertionError("Brier difference identity broken")
    return direct


def sign(delta):
    if not math.isfinite(delta):
        raise ValueError("Nonfinite Brier difference")
    return "full_intensity_better" if delta < -1e-12 else (
        "inactive_removed_better" if delta > 1e-12 else "effectively_equal")


def bucket(deaths):
    if type(deaths) is not int or deaths<0:
        raise ValueError("Invalid official fatalities")
    if deaths==0:
        return "zero"
    if deaths<25:
        return "inactive_1_to_24"
    return "active_25_plus"


def compute_case(row,beta,name):
    deaths=row["origin_deaths"]
    state=row["origin_state"]
    y=row["outcome"]
    if (state not in (0,1) or y not in (0,1) or
        state!=int(deaths>=25)):
        raise ValueError("Historical annual origin/outcome mismatch")
    p0=round(p_scaled(row["p_original_binary"],deaths,beta,0.0),12)
    p1=round(p_scaled(row["p_original_binary"],deaths,beta,1.0),12)
    delta=brier_effect(p0,p1,y)
    # NO country with zero deaths or in original active state can contribute
    # to the alpha1-alpha0 contrast, by exact model algebra.
    if (deaths==0 or state==1) and abs(p1-p0)>1e-12:
        raise AssertionError("Unchanged LOG1P feature inexplicably altered risk")
    if deaths==0 or state==1:
        if abs(delta)>1e-12:
            raise AssertionError("Zero-intensity or active state cannot affect Brier")
    return {
        "country_id":row["country_id"],
        "country":name,
        "origin_deaths_best":deaths,
        "origin_state":state,
        "target_outcome_state":y,
        "origin_deaths_bucket":bucket(deaths),
        "original_markov_h2_p_active":row["p_original_binary"],
        "alpha0_p_active":p0,
        "alpha1_p_active":p1,
        "alpha1_minus_alpha0_delta_Brier_sum":round(delta,12),
        "alpha1_minus_alpha0_delta_Brier_exact_for_aggregation":delta,
        "event_class":("inactive_to_active" if state==0 and y==1 else
            "inactive_to_inactive" if state==0 else
            "active_to_active" if y==1 else "active_to_inactive"),
    }


def _aggregate(rows):
    if not rows:
        return {
            "n":0,"positive_outcomes":0,
            "brier_sum_delta":0.0,"brier_delta_mean":None,
            "gain_alpha1_sum":0.0,"harm_alpha1_sum":0.0,
            "nonzero_delta_n":0,
        }
    deltas=[r["alpha1_minus_alpha0_delta_Brier_exact_for_aggregation"]
            for r in rows]
    total=sum(deltas)
    return {
        "n":len(rows),
        "positive_outcomes":sum(r["target_outcome_state"] for r in rows),
        "brier_sum_delta":round(total,12),
        "brier_delta_mean":round(total/len(rows),12),
        "gain_alpha1_sum":round(sum(d for d in deltas if d<0),12),
        "harm_alpha1_sum":round(sum(d for d in deltas if d>0),12),
        "nonzero_delta_n":sum(abs(d)>1e-12 for d in deltas),
    }


def explain_year(rows,beta,names,prior):
    if not 175<=len(rows)<=196:
        raise ValueError("Fixed historical riskset insufficient")
    by_id=[compute_case(r,beta,names[r["country_id"]]) for r in rows]
    delta=sum(r["alpha1_minus_alpha0_delta_Brier_exact_for_aggregation"]
              for r in by_id)
    annual_mean=delta/len(by_id)
    metrics,_=year_scores(rows,beta)
    direct=metrics["1.0"]["brier"]-metrics["0.0"]["brier"]
    if abs(annual_mean-direct)>EPS:
        raise AssertionError("Per-country paired Brier effects do not sum to exact annual score")
    if abs(annual_mean-prior["alpha1_minus_alpha0_delta_Brier"])>EPS:
        raise AssertionError("Cannot reproduce immutable rolling H2 annual source report")
    if sign(direct)!=prior["alpha1_vs_alpha0_brier_winner"]:
        raise AssertionError("Published year sign differs from country audit")
    bins={b:_aggregate([r for r in by_id if r["origin_deaths_bucket"]==b])
          for b in ("zero","inactive_1_to_24","active_25_plus")}
    events={event:_aggregate([r for r in by_id if r["event_class"]==event])
            for event in ("inactive_to_inactive","inactive_to_active",
                          "active_to_inactive","active_to_active")}
    if bins["zero"]["nonzero_delta_n"] or bins["active_25_plus"]["nonzero_delta_n"]:
        raise AssertionError("The two mathematically inactive buckets have nonzero effect")
    if abs(bins["inactive_1_to_24"]["brier_sum_delta"]-delta)>EPS:
        raise AssertionError("All alpha contrast must be within 1–24 deaths")
    affected=[r for r in by_id if r["origin_deaths_bucket"]=="inactive_1_to_24"]
    ranked=sorted(affected,key=lambda r:(
        -abs(r["alpha1_minus_alpha0_delta_Brier_exact_for_aggregation"]),
        r["country_id"]))
    gain=sorted(affected,key=lambda r:(
        r["alpha1_minus_alpha0_delta_Brier_exact_for_aggregation"],
        r["country_id"]))
    harm=list(reversed(gain))
    flips=[]
    for r in affected:
        # Leave ONE country OUT of the *score*, NOT the fitted model;
        # not an estimate of a counterfactual training response.
        remainder=(delta-r["alpha1_minus_alpha0_delta_Brier_exact_for_aggregation"])/(len(by_id)-1)
        if sign(remainder)!=sign(delta):
            flips.append({
                "country_id":r["country_id"],
                "country":r["country"],
                "outcome":r["target_outcome_state"],
                "origin_deaths":r["origin_deaths_best"],
                "delta_without_country":round(remainder,12),
            })
    abs_mass=sum(abs(r["alpha1_minus_alpha0_delta_Brier_exact_for_aggregation"])
                 for r in affected)
    active_n=bins["active_25_plus"]["n"]
    zero_n=bins["zero"]["n"]
    nonzero_n=bins["inactive_1_to_24"]["n"]
    if active_n+zero_n+nonzero_n!=len(by_id):
        raise AssertionError("Not all country cases partitioned")
    def serial(r):
        return {k:v for k,v in r.items()
                if k!="alpha1_minus_alpha0_delta_Brier_exact_for_aggregation"}
    return {
        "country_n":len(by_id),
        "year_brier_delta_alpha1_minus_alpha0":round(annual_mean,12),
        "sign":sign(annual_mean),
        "positive_outcomes":sum(r["target_outcome_state"] for r in by_id),
        "origin_zero_n":zero_n,
        "origin_1_to_24_n":nonzero_n,
        "origin_active_25_plus_n":active_n,
        "source_signal_affected_fraction":round(nonzero_n/len(by_id),9),
        "only_origin_1_to_24_can_change_alpha_contrast":True,
        "by_origin_deaths_bucket":bins,
        "by_origin_outcome_transition":events,
        "sum_alpha1_benefits_negative":bins["inactive_1_to_24"]["gain_alpha1_sum"],
        "sum_alpha1_harms_positive":bins["inactive_1_to_24"]["harm_alpha1_sum"],
        "paired_total_sum_difference":round(delta,12),
        "n_affected_historical_country_rows":len(affected),
        "n_nonzero_effects":bins["inactive_1_to_24"]["nonzero_delta_n"],
        "absolute_influence_mass":round(abs_mass,12),
        "top1_share_of_absolute_country_effects":
            round(abs(ranked[0]["alpha1_minus_alpha0_delta_Brier_exact_for_aggregation"])/abs_mass,9)
            if abs_mass else 0,
        "top3_share_of_absolute_country_effects":
            round(sum(abs(r["alpha1_minus_alpha0_delta_Brier_exact_for_aggregation"])
                      for r in ranked[:3])/abs_mass,9) if abs_mass else 0,
        "n_leave_one_country_out_sign_changes_no_refit":len(flips),
        "leave_one_country_out_sign_changes_no_refit":flips,
        "top8_abs_country_effects":[serial(r) for r in ranked[:8]],
        "top5_helping_full_intensity":[serial(r) for r in gain[:5]],
        "top5_hurting_full_intensity":[serial(r) for r in harm[:5]],
        "all_origin_1_to_24_country_effects":[serial(r) for r in
            sorted(affected,key=lambda r:r["country_id"])],
    }


def replay(sources,names,prior):
    if (prior.get("schema")!="idealab.psico.geo2027_log1p_annual_rolling_h2_vintage_stability.v1"
        or prior.get("future_2027_outcomes_resolved")!=0
        or prior.get("issued_forecasts_probabilities_modified") is not False
        or prior.get("rolling_result",{}).get(
            "n_total_replayed_annual_year_edition_blocks")!=30):
        raise ValueError("Rolling year-block provenance mismatch")
    if set(sources)!=set(VERSION_ORDER) or len(names)!=196:
        raise ValueError("Need four official source vintages and original 196 GWNOs")
    blocks={}
    by_target={}
    for version in VERSION_ORDER:
        cutoff=SOURCES[version]["last_year"]
        history=historical_ledger(sources[version],cutoff,names)
        existing=prior["rolling_result"]["by_version"][version]
        annual=[]
        for target in range(FIRST_OUTER_TARGET,cutoff+1):
            beta,meta=fit_target(history,target)
            reference=next(x for x in existing["annual"] if x["target_year"]==target)
            if (meta["coefficients"]!=reference["fit"]["coefficients"]
                or meta["training_n"]!=reference["fit"]["training_n"]):
                raise AssertionError("Historical year-origin fitted parameters changed")
            effect=explain_year(history[target],beta,names,reference)
            keep=target in FOCUS_YEARS
            block={
                "source_version":version,
                "target_year":target,
                "origin_year":target-2,
                "source_year_through":cutoff,
                "trained_label_year_max":meta["max_supervised_training_label_year"],
                "training_feature_year_max":meta["max_training_feature_year"],
                "ridge_fixed":meta["fixed_ridge"],
                "logistic_coefficients":meta["coefficients"],
                "detailed_focus_year":keep,
                "country_n":effect["country_n"],
                "positive_outcomes":effect["positive_outcomes"],
                "origin_zero_n":effect["origin_zero_n"],
                "origin_1_to_24_n":effect["origin_1_to_24_n"],
                "origin_active_25_plus_n":effect["origin_active_25_plus_n"],
                "by_origin_deaths_bucket":effect["by_origin_deaths_bucket"],
                "by_origin_outcome_transition":effect["by_origin_outcome_transition"],
                "year_brier_delta_alpha1_minus_alpha0":effect[
                    "year_brier_delta_alpha1_minus_alpha0"],
                "sign":effect["sign"],
                "sum_alpha1_benefits_negative":effect["sum_alpha1_benefits_negative"],
                "sum_alpha1_harms_positive":effect["sum_alpha1_harms_positive"],
                "n_leave_one_country_out_sign_changes_no_refit":effect[
                    "n_leave_one_country_out_sign_changes_no_refit"],
                "top1_share_of_absolute_country_effects":effect[
                    "top1_share_of_absolute_country_effects"],
                "top3_share_of_absolute_country_effects":effect[
                    "top3_share_of_absolute_country_effects"],
                "largest_abs_country_effect":effect["top8_abs_country_effects"][0]
                    if effect["top8_abs_country_effects"] else None,
            }
            if keep:
                block["focus_country_contributions"]=effect[
                    "all_origin_1_to_24_country_effects"]
                block["focus_top8_absolute"]=effect["top8_abs_country_effects"]
                block["focus_leave_one_out_sign_flips"]=effect[
                    "leave_one_country_out_sign_changes_no_refit"]
            annual.append(block)
            by_target.setdefault(target,[]).append(block)
        blocks[version]=annual
    diagnostics={}
    for target in FOCUS_YEARS:
        arr=by_target[target]
        if len(arr)!={2017:4,2024:2,2025:1}[target]:
            raise AssertionError("Expected official-vintage target-year coverage changed")
        country_versions={}
        for item in arr:
            version=item["source_version"]
            for r in item["focus_country_contributions"]:
                country_versions.setdefault(r["country_id"],[]).append({
                    "version":version,
                    "country":r["country"],
                    "origin_deaths":r["origin_deaths_best"],
                    "outcome":r["target_outcome_state"],
                    "delta":r["alpha1_minus_alpha0_delta_Brier_sum"],
                })
        changed_country_effect_signs=[]
        for cid,rr in sorted(country_versions.items()):
            if len({sign(r["delta"]) for r in rr})>1:
                changed_country_effect_signs.append({
                    "country_id":cid,
                    "country":rr[0]["country"],"per_version":rr,
                })
        diagnostics[str(target)]={
            "year":target,
            "n_vintages":len(arr),
            "versions":[r["source_version"] for r in arr],
            "all_editions_same_aggregate_Brier_sign":
                len({r["sign"] for r in arr})==1,
            "min_affected_country_n":min(r["origin_1_to_24_n"] for r in arr),
            "max_affected_country_n":max(r["origin_1_to_24_n"] for r in arr),
            "n_country_ids_with_nonzero_1_to_24_in_any_version":
                len(country_versions),
            "n_country_ids_with_vintage_effect_sign_change":
                len(changed_country_effect_signs),
            "country_effect_sign_changes_across_editions":
                changed_country_effect_signs,
        }
    return {
        "schema":"idealab.psico.geo2027_log1p_annual_country_reversal_attribution.v1",
        "status":"EX_POST_ANNUAL_COUNTRY_BRIER_CONTRIBUTION_AUDIT_NOT_NEW_ISSUE",
        "original_forecast_sha256":SOURCE_SHA256,
        "issued_log1p_shadow_sha256":FROZEN_ISSUE_SHA256,
        "original_15_alerts_sha256":ALERT_SHA,
        "source_sha256":{v:SOURCES[v]["sha256"] for v in VERSION_ORDER},
        "trained_label_cutoff_max_t_minus_two":True,
        "all_training_features_cutoff_max_t_minus_four":True,
        "alpha_candidates_from_previous_research":list(ALPHAS),
        "only_alpha0_vs_alpha1_country_contributions_audited":True,
        "only_countries_with_origin_deaths_1_to_24_can_contribute":True,
        "Brier_identity":"(p_alpha1-y)^2-(p_alpha0-y)^2=(p_alpha1-p_alpha0)*(p_alpha1+p_alpha0-2*y)",
        "year_country_leave_one_out_does_not_refit_model":True,
        "no_multiple_testing_significance_claims":True,
        "historical_UCDP_vintages_not_original_asof_issuances":True,
        "prior_historical_outcomes_and_lambda_already_explored":True,
        "distinct_target_years":9,
        "year_vintage_blocks":30,
        "focus_years":list(FOCUS_YEARS),
        "by_version_annual_diagnostics":blocks,
        "focus_year_vintage_sign_diagnostics":diagnostics,
        "issued_2027_original_probabilities_changed":False,
        "issued_2027_shadow_probabilities_changed":False,
        "issued_2027_15_alerts_changed":False,
        "resolved_official_2027_labels":0,
        "prospective_skill_demonstrated":False,
        "limitations":"All paired country Brier effects are algebraic score attributions, NOT causal accounts of geopolitical events. Only countries with 1–24 origin-year state-based best deaths can differ between these two coefficient attenuations; countries with zero or >=25 deaths contribute identically to both. Removing one country from an annual score is a descriptive influence analysis with fitted parameters kept fixed, not leave-one-country-out training or independent validation. Data editions are ex-post revised and multi-edition country-years correlated; lambda and alpha family were chosen after past outcomes were inspected. No new issued 2027 probabilities or 2027 official outcomes."
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    args=ap.parse_args()
    audit_issued_shadow(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes())
    if sha(ALERTS.read_bytes())!=ALERT_SHA:
        raise ValueError("Original 15 issued alerts modified")
    issue=json.loads(ISSUE.read_text(encoding="utf8"))
    names={r["country_id"]:r["country"] for r in issue["countries"]}
    sources={}
    for ver in VERSION_ORDER:
        sources[ver]=parse_counts(request(SOURCES[ver]["url"],MAX_DOWNLOAD),ver)
    prior=json.loads(PRIOR.read_text(encoding="utf8"))
    report=replay(sources,names,prior)
    payload=json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    print("GEO2027_LOG1P_COUNTRY_REVERSAL_BEGIN")
    print(payload,end="")
    print("GEO2027_LOG1P_COUNTRY_REVERSAL_END")
    if args.check_report and REPORT.read_bytes()!=payload.encode():
        raise ValueError("Official source annual-country Brier attribution report differs")


if __name__=="__main__":
    main()
