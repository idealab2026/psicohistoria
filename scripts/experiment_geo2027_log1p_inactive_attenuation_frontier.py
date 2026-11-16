#!/usr/bin/env python3
"""GEO2027 inactive-source-intensity coefficient attenuation Pareto ablation.

Five PREDECLARED fixed multipliers alpha on the INACTIVE-origin LOG1P slope
(0,.25,.5,.75,1). All remaining parameters unchanged. No model refitting
per alpha, no 2027 reissue and no choosing a retrospective "winner".

Historical retrospective Brier/logloss: official source-separated 2022->24
and 2023->25 outcomes, already viewed by the project and NOT untouched.
Pre-2021 (2018..20) inner validation metrics ALSO reported for context,
without selecting alpha. 2027 stress: exact +/-10 source-death endpoints with
original GEO Markov offset and original fitted coefficients, compared against
SHA-frozen issued 196-country LOG1P stress. No future outcomes scored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from audit_geo2027_log1p_shadow_issue import (
    FROZEN_ISSUE_SHA256, MANIFEST, ORIGINAL, ISSUE, audit as audit_issue,
)
from audit_geo2027_log1p_issued_death_stress import (
    ALERTS, ALERT_SHA, certified_topk, death_range, percentile,
)
from backtest_archived_country_vintages import FOLDS, SOURCES
from diagnose_geo2028_historical_forecast_vintage_drift import _fit_at_origin
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD, VERSION_ORDER, counts_to_binary, parse_counts, scores,
)
from experiment_geo2027_log1p_nested_h2 import (
    fit, inner_rows, predict, select_and_fit,
)
from prepare_geo2027_transition_alerts import SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo2027-log1p-inactive-attenuation-frontier.json"
PRIOR=ROOT/"data/geo2027-log1p-nested-h2.json"
PRIOR_STRESS=ROOT/"data/geo2027-log1p-issued-death-count-stress.json"
ALPHAS=(0.0,0.25,0.5,0.75,1.0)
INTERNAL_TARGET_YEARS=(2018,2019,2020)
DEATH_MARGIN=10
EPS=3e-10


def sha(data):
    return hashlib.sha256(data).hexdigest()


def scaled_beta(beta,alpha):
    """Never optimise or change the frozen intercept and active coefficient."""
    if (type(alpha) is not float or alpha not in ALPHAS
        or len(beta)!=3 or any(type(x) not in (float,int) or
            not math.isfinite(x) for x in beta)):
        raise ValueError("Unexpected preregistered coefficient scale")
    return (beta[0],alpha*beta[1],beta[2])


def p_scaled(baseline,deaths,beta,alpha):
    if not 0<baseline<1 or type(deaths) is not int or deaths<0:
        raise ValueError("Invalid original H2 probability/annual deaths")
    return predict({"p_original_binary":baseline,
                    "origin_deaths":deaths},scaled_beta(beta,alpha))


def fold_scores(rows,beta):
    """Same cohort, same labels for all alpha; DO NOT optimise alpha on these."""
    if not rows:
        raise ValueError("Empty paired cohort")
    return {str(alpha):scores([
        {"outcome":r["outcome"],"p":round(
            p_scaled(r["p_original_binary"],r["origin_deaths"],beta,alpha),12)}
        for r in rows],"p") for alpha in ALPHAS}


def historical(sources,prior):
    if (prior.get("schema")!="idealab.psico.geo2027_log1p_nested_h2_research.v1"
        or prior.get("prospective_predictive_skill_demonstrated") is not False
        or prior.get("n_2027_outcomes_resolved")!=0
        or len(prior.get("folds",[]))!=2):
        raise ValueError("Prior already-examined LOG1P comparison provenance failed")
    foldreports=[]
    full_by_alpha={str(a):[] for a in ALPHAS}
    dev_by_alpha={str(a):[] for a in ALPHAS}
    for spec in FOLDS:
        older=spec["origin_release"]
        later=spec["target_release"]
        origin=spec["origin_year"]
        target=spec["target_year"]
        if (SOURCES[older]["last_year"]!=origin or
            SOURCES[later]["last_year"]!=target or target!=origin+2):
            raise ValueError("Source release origin/outcome timing changed")
        old=sources[older]
        new=sources[later]
        nested,summary=inner_rows(old,origin)
        final_beta,intercept,metadata=select_and_fit(nested,origin)
        prior_fold=next(x for x in prior["folds"]
                        if x["origin_vintage"]==older and
                        x["outcome_vintage"]==later)
        if (metadata["final_beta_log1p"]!=prior_fold[
                "nested_training_and_selection"]["final_beta_log1p"]
            or metadata["selected_ridge_lambda"]!=prior_fold[
                "nested_training_and_selection"]["selected_ridge_lambda"]):
            raise AssertionError("Exact frozen family fit not reproduced")
        internal_fit=[r for r in nested if 2012<=r["target_year"]<=2017]
        internal_validation=[r for r in nested if
                             r["target_year"] in INTERNAL_TARGET_YEARS]
        development_beta=fit(internal_fit,float(metadata["selected_ridge_lambda"]))
        development_scores=fold_scores(internal_validation,development_beta)
        for alpha in ALPHAS:
            a=str(alpha)
            dev_by_alpha[a].extend([
                {"outcome":r["outcome"],"p":round(
                    p_scaled(r["p_original_binary"],r["origin_deaths"],
                             development_beta,alpha),12)}
                for r in internal_validation])
        binary,_=_fit_at_origin(counts_to_binary(old),origin)
        if len(binary)!=196:
            raise ValueError("Official fixed historical cohort lost country")
        country_rows=[]
        for cid in sorted(binary):
            if target not in new.get(cid,{}):
                raise ValueError("Future outcome missing, not imputed zero")
            deaths=old[cid][origin]
            row={"country_id":cid,"origin_deaths":deaths,
                 "p_original_binary":binary[cid]["p_model_h2"],
                 "outcome":int(new[cid][target]>=25),
                 "origin_state":int(deaths>=25)}
            country_rows.append(row)
        fold_metrics=fold_scores(country_rows,final_beta)
        for alpha in ALPHAS:
            a=str(alpha)
            full_by_alpha[a].extend([
                {"outcome":r["outcome"],"p":round(
                    p_scaled(r["p_original_binary"],r["origin_deaths"],
                             final_beta,alpha),12)}
                for r in country_rows])
        expected=prior_fold["metrics"]["scores"]["p_offset_log1p"]
        for key in ("brier","logloss"):
            if abs(fold_metrics["1.0"][key]-expected[key])>EPS:
                raise AssertionError("alpha=1 failed issued LOG1P historical reproducibility")
        foldreports.append({
            "origin_year":origin,"target_year":target,
            "old_UCDP":older,"outcome_UCDP":later,
            "n":len(country_rows),
            "positives":sum(r["outcome"] for r in country_rows),
            "origin_inactive_n":sum(r["origin_state"]==0 for r in country_rows),
            "selected_ridge_before_target":metadata["selected_ridge_lambda"],
            "final_beta_reused_not_refitted_per_alpha":metadata["final_beta_log1p"],
            "development_fit_target_years":[2012,2017],
            "development_validation_target_years":[2018,2020],
            "development_validation_n":len(internal_validation),
            "development_validation_alpha_scores":development_scores,
            "reused_target_year_alpha_scores":fold_metrics,
            "per_origin_state":{
                str(state):fold_scores(
                    [r for r in country_rows if r["origin_state"]==state],
                    final_beta) for state in (0,1)
            },
            "historical_report_reproduced":True,
        })
    pooled={alpha:scores(rows,"p") for alpha,rows in full_by_alpha.items()}
    development_pooled={alpha:scores(rows,"p") for alpha,rows in dev_by_alpha.items()}
    expected=prior["pooled"]["scores"]["p_offset_log1p"]
    if (len(full_by_alpha["1.0"])!=392 or
        sum(r["outcome"] for r in full_by_alpha["1.0"])!=69 or
        any(abs(pooled["1.0"][metric]-expected[metric])>EPS
            for metric in ("brier","logloss"))):
        raise AssertionError("Pooled 2024/25 historical comparator changed")
    return {
        "historical_folds":foldreports,
        "development_validation_2018_2020_pooled_two_correlated_vintages":development_pooled,
        "reused_2024_2025_outcome_metrics_pooled":pooled,
        "n_reused_holdout_observations":392,"n_reused_positives":69,
        "outcome_years_previously_inspected_in_project":[2024,2025],
        "development_editions_not_independent":True,
        "not_an_independent_confirmatory_backtest":True,
    }


def issued_counterfactual(issue,prior_stress,alerts):
    if (issue.get("schema")!="idealab.psico.geo2027_log1p_intensity_shadow.v1"
        or issue.get("outcomes_2027_resolved")!=0 or
        prior_stress.get("schema")!="idealab.psico.geo2027_issued_log1p_source_death_stress.v1"
        or prior_stress.get("first_issued_log1p_shadow_sha256")!=FROZEN_ISSUE_SHA256
        or prior_stress.get("perturbation_absolute_death_margins")!=[1,5,10]
        or alerts.get("2027_outcomes_resolved")!=0):
        raise ValueError("Unmodified prospective issue/stress provenance invalid")
    rows=issue["countries"]
    if len(rows)!=196 or len({r["country_id"] for r in rows})!=196:
        raise ValueError("Incomplete first-issue 196-country cohort")
    beta=issue["training"]["final_beta_log1p"]
    old_bounds={r["country_id"]:r["bands"]["10"]
                for r in prior_stress["country_envelopes"]}
    reports=[]
    results={}
    for alpha in ALPHAS:
        series=[]
        for r in rows:
            cid=r["country_id"]
            deaths=r["origin_deaths_best_2025"]
            state=r["origin_binary_state_2025"]
            reference=r["original_2027_p_active"]
            lo,hi=death_range(deaths,state,DEATH_MARGIN)
            centre=p_scaled(reference,deaths,beta,alpha)
            candidates=[p_scaled(reference,dd,beta,alpha)
                        for dd in (lo,hi)]
            minimum=min(candidates)
            maximum=max(candidates)
            width=100*(maximum-minimum)
            if not minimum-EPS<=centre<=maximum+EPS:
                raise AssertionError("Nominal model outside its own death envelope")
            if alpha==1.0:
                frozen=r["log1p_shadow_p_active_2027"]
                old=old_bounds[cid]
                if (abs(centre-frozen)>EPS or
                    abs(round(minimum,12)-old["low_p_active"])>EPS or
                    abs(round(maximum,12)-old["high_p_active"])>EPS):
                    raise AssertionError("2027 unmodified alpha=1 source stress differs")
            series.append({"country_id":cid,"country":r["country"],
                "origin_state":state,"origin_deaths_best_2025":deaths,
                "original_fixed_p_GEO":reference,
                "issued_p_LOG1P":r["log1p_shadow_p_active_2027"],
                "counterfactual_centre":round(centre,12),
                "counterfactual_low":round(minimum,12),
                "counterfactual_high":round(maximum,12),
                "width_pp":round(width,9)})
        bands={}
        for state,k in ((0,10),(1,5)):
            risk={}
            for r in series:
                if r["origin_state"]!=state:
                    continue
                if state==0:
                    risk[r["country_id"]]={
                        "lo":r["counterfactual_low"],
                        "centre":r["counterfactual_centre"],
                        "hi":r["counterfactual_high"]}
                else:
                    risk[r["country_id"]]={
                        "lo":round(1-r["counterfactual_high"],12),
                        "centre":round(1-r["counterfactual_centre"],12),
                        "hi":round(1-r["counterfactual_low"],12)}
            ranks=certified_topk(risk,k)
            bands[str(state)]={
                "state":state,"k":k,"risk_set_n":len(risk),
                "nominal_topk":[r["country"] for r in series
                    if r["country_id"] in ranks["nominal_ordered"]],
                "mandatory_n":ranks["mandatory_n"],
                "possible_n":ranks["possible_n"],
                "mandatory_country_ids":ranks["mandatory"],
                "possible_country_ids":ranks["possible"],
                "nominal_country_ids":ranks["nominal_ordered"],
            }
        if alpha==1.0:
            issued_summary=prior_stress["scenario_summaries"][2]
            for state in (0,1):
                expected_ranks=issued_summary["risk_group_rank_certification"][str(state)]
                if (bands[str(state)]["mandatory_n"]!=expected_ranks["mandatory_n"]
                    or bands[str(state)]["possible_n"]!=expected_ranks["possible_n"]
                    or bands[str(state)]["mandatory_country_ids"]!=expected_ranks["mandatory"]):
                    raise AssertionError("First-issue rank certification changed")
        widths=[r["width_pp"] for r in series]
        report={
            "inactive_slope_multiplier":alpha,"n_countries":196,
            "inactive_zero_deaths_n":sum(r["origin_state"]==0 and
                r["origin_deaths_best_2025"]==0 for r in series),
            "active_n":sum(r["origin_state"]==1 for r in series),
            "counterfactual_expected_active_sum":round(sum(
                r["counterfactual_centre"] for r in series),10),
            "issued_expected_active_sum":issue["expected_active_countries_log1p_sum_p"],
            "counterfactual_expected_sum_lower":round(sum(
                r["counterfactual_low"] for r in series),10),
            "counterfactual_expected_sum_upper":round(sum(
                r["counterfactual_high"] for r in series),10),
            "mean_10death_full_width_pp":round(sum(widths)/196,9),
            "median_10death_full_width_pp":percentile(widths,.5),
            "p95_10death_full_width_pp":percentile(widths,.95),
            "max_10death_full_width_pp":max(widths),
            "n_possible_change_5pp":sum(max(
                abs(r["counterfactual_centre"]-r["counterfactual_low"]),
                abs(r["counterfactual_high"]-r["counterfactual_centre"])
                )>=.05-1e-10 for r in series),
            "topk_mandatory_possible":bands,
            "Burundi_2025_0_to_10_case":next({
                "issued_deaths_2025":r["origin_deaths_best_2025"],
                "issued_p":r["issued_p_LOG1P"],
                "alpha_p_at_0_deaths":r["counterfactual_centre"],
                "alpha_p_at_10_deaths":r["counterfactual_high"],
                "alpha_10death_shift_pp":r["width_pp"]}
                for r in series if r["country"]=="Burundi"),
            "all_country_counterfactual_bands":series,
        }
        reports.append(report)
        results[str(alpha)]=report
    # Attenuation is an explicit tradeoff. A candidate is Pareto-dominated
    # if another has both <= historical pooled Brier and <= sensitivity width.
    return results


def nondominated(historical,stress):
    result=[]
    for alpha in ALPHAS:
        a=str(alpha)
        brier=historical[a]["brier"]
        width=stress[a]["mean_10death_full_width_pp"]
        dominated_by=[]
        for other in ALPHAS:
            if other==alpha:
                continue
            key=str(other)
            b2=historical[key]["brier"]
            w2=stress[key]["mean_10death_full_width_pp"]
            if (b2<=brier+1e-14 and w2<=width+1e-9
                and (b2<brier-1e-14 or w2<width-1e-9)):
                dominated_by.append(other)
        result.append({"alpha":alpha,"reused_holdout_brier":brier,
                       "issued_counterfactual_width_pp":width,
                       "non_dominated_on_these_two_exploratory_axes":
                           not dominated_by,
                       "dominated_by_alpha":dominated_by})
    return result


def study(sources,issue,prior,prior_stress,alerts):
    hist=historical(sources,prior)
    stress=issued_counterfactual(issue,prior_stress,alerts)
    frontier=nondominated(
        hist["reused_2024_2025_outcome_metrics_pooled"],stress)
    base=stress["1.0"]
    for alpha in ALPHAS:
        r=stress[str(alpha)]
        if alpha<1 and (r["mean_10death_full_width_pp"]>
            base["mean_10death_full_width_pp"]+1e-9):
            raise AssertionError("Inactive slope attenuation unexpectedly increases mean stress")
        if alpha==0:
            if (r["topk_mandatory_possible"]["0"]["mandatory_n"]!=10
                or r["topk_mandatory_possible"]["0"]["possible_n"]!=10):
                raise AssertionError("Zero inactive slope must stabilize inactive top10")
    return {
        "schema":"idealab.psico.geo2027_log1p_inactive_slope_attenuation_frontier.v1",
        "status":"AFTER_ISSUE_EXPLORATORY_ABLATION_NOT_NEW_FORECAST",
        "issued_shadow_sha256":FROZEN_ISSUE_SHA256,
        "original_geo_sha256":SOURCE_SHA256,
        "original_15_alerts_sha256":ALERT_SHA,
        "first_issued_2027_shadow_probabilities_modified":False,
        "first_issued_2027_original_probabilities_modified":False,
        "first_issued_15_transition_alerts_modified":False,
        "model_reissued":False,
        "counterfactual_variants_are_not_issued_forecasts":True,
        "n_outcomes_2027_resolved":0,
        "demonstrated_prospective_skill":False,
        "alpha_grid_fixed_before_evaluation":list(ALPHAS),
        "model_definition":"same frozen intercept, active intensity coefficient and original Markov logit offset; multiply ONLY inactive intensity slope by alpha",
        "source_death_revision_margin_2025":DEATH_MARGIN,
        "source_death_scenario_clipped_to_original_25_state":True,
        "all_2027_stress_bands_are_mathematical_not_statistical":True,
        "historical_outcomes_previously_seen":True,
        "no_alpha_winner_declared":True,
        "no_model_selected_or_fitted_on_2024_2025_outcomes":True,
        "no_2027_outcome_used":True,
        "source_edition_sha256":{v:SOURCES[v]["sha256"] for v in VERSION_ORDER},
        "historical":hist,
        "issued_shadow_counterfactuals_by_alpha":stress,
        "two_axis_exploratory_Pareto_frontier":frontier,
        "limitations":"The same two 2024/25 outcomes were already inspected in earlier research and cannot independently confirm an alpha choice. The 2018-20 validation period has also previously selected regularization. Fixed coefficient attenuation is NOT re-fitting a new predictive model; it is a post-issuance mechanistic stress ablation. Prospective 2027 issue is unchanged and must be scored independently. +/-10 integer death perturbations are hypothetical, independently feasible, state-preserving and do not refit source revisions; these are not uncertainty or forecast intervals. Two annual outcomes with correlated countries cannot support IID significance."
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    args=ap.parse_args()
    issue_bytes=ISSUE.read_bytes()
    manifest_bytes=MANIFEST.read_bytes()
    original_bytes=ORIGINAL.read_bytes()
    alerts_bytes=ALERTS.read_bytes()
    audit_issue(issue_bytes,manifest_bytes,original_bytes)
    if sha(alerts_bytes)!=ALERT_SHA:
        raise ValueError("Original 15 transition alerts changed")
    source={}
    for ver in VERSION_ORDER:
        source[ver]=parse_counts(
            request(SOURCES[ver]["url"],MAX_DOWNLOAD),ver)
    result=study(
        source,json.loads(issue_bytes),
        json.loads(PRIOR.read_text(encoding="utf8")),
        json.loads(PRIOR_STRESS.read_text(encoding="utf8")),
        json.loads(alerts_bytes))
    payload=json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    print("GEO2027_INACTIVE_ATTENUATION_FRONTIER_BEGIN")
    print(payload,end="")
    print("GEO2027_INACTIVE_ATTENUATION_FRONTIER_END")
    if args.check_report and REPORT.read_bytes()!=payload.encode():
        raise ValueError("Replayed GEO2027 inactive attenuation frontier differs from committed report")


if __name__=="__main__":
    main()
