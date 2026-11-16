#!/usr/bin/env python3
"""Retrospective sensitivity of issued LOG1P model CLASS to UCDP vintage revisions.

Five paired UCDP OrganizedViolenceCY 23.1...26.1 reconstructions, origins
2022 and 2023 kept fixed. ALL later-edition labels after the historical origin
are removed before binary fit, log1p coefficient selection, or evaluation.
Three-factor Shapley arithmetic splits vintage changes into (a) original
Markov H2 probability, (b) origin-year best fatalities, (c) learned logistic
coefficients. This does NOT revise the 2025-origin issued 2027 forecast:
editions before 26.1 never saw year 2025. No new future outcomes are scored.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

from backtest_archived_country_vintages import SOURCES
from diagnose_geo2028_historical_forecast_vintage_drift import _fit_at_origin
from diagnose_geo2027_historical_alert_vintage_overlap import admissible_topk
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD, VERSION_ORDER, counts_to_binary, parse_counts,
)
from experiment_geo2027_log1p_nested_h2 import inner_rows, predict, select_and_fit
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo2027-log1p-historical-vintage-robustness.json"
SHADOW=ROOT/"data/forecast-2027-log1p-shadow.json"
SHADOW_MANIFEST=ROOT/"data/forecast-2027-log1p-shadow-manifest.json"
PREVIOUS=ROOT/"data/geo2027-log1p-nested-h2.json"
ALERTS=ROOT/"data/forecast-2027-transition-alerts.json"
SHADOW_SHA256="52686923315854557a796f8f192d376dab77a4e03b14c1aeb6b4091e48104f90"
ALERT_SHA256="309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb"
PAIRS=((2022,"23.1","24.1"),(2022,"23.1","25.1"),
       (2022,"23.1","26.1"),(2023,"24.1","25.1"),
       (2023,"24.1","26.1"))
FACTORS=("binary_markov_kernel","origin_annual_deaths","trained_logistic_coefficients")
BUDGETS={0:10,1:5}
EPS=2e-10


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def clipped_original_counts(source,origin):
    """No post-origin row can enter any of the nested supervised targets."""
    if origin not in (2022,2023):
        raise ValueError("Unsupported historical origin")
    clipped={}
    for cid,h in source.items():
        if type(cid) is not int or not isinstance(h,dict):
            raise ValueError("Invalid country history")
        current={}
        for year, deaths in h.items():
            if type(year) is not int or type(deaths) is not int or deaths<0:
                raise ValueError("Invalid original-source annual fatalities")
            if year<=origin:
                current[year]=deaths
        if current:
            clipped[cid]=current
    if not clipped or max(max(h) for h in clipped.values())!=origin:
        raise ValueError("Missing historical origin")
    return clipped


def snapshot(source,origin,ids):
    """Fit both models using ONE UCDP edition, truncated to origin."""
    clipped=clipped_original_counts(source,origin)
    markov,markov_info=_fit_at_origin(
        counts_to_binary(clipped),origin,fixed_cohort=list(ids))
    rows,summary=inner_rows(clipped,origin)
    beta,control,train=select_and_fit(rows,origin)
    if (markov_info["last_training_year"]!=origin
        or len(markov)!=196 or set(markov)!=set(ids)
        or train["final_train_targets"]!=[2012,origin]
        or train["inner_select_targets"]!=[2018,2020]
        or max(x["target_year"] for x in rows)!=origin
        or max(x["max_training_cutoff"] for x in summary)!=origin-2):
        raise ValueError("Nested temporal fit or country cohort changed")
    forecasts={}
    for cid in sorted(ids):
        deaths=clipped[cid][origin]
        p=markov[cid]["p_model_h2"]
        shadow_p=round(predict(
            {"p_original_binary":p,"origin_deaths":deaths},beta),12)
        if not 0<shadow_p<1:
            raise ValueError("Invalid historical shadow probability")
        forecasts[cid]={
            "origin_state":int(deaths>=25),
            "origin_deaths_best":deaths,
            "p_original_binary_h2":p,
            "p_log1p_h2":shadow_p,
        }
    return forecasts,{
        "origin":origin,
        "training_countries":markov_info["training_country_ids"],
        "training_cutoff":markov_info["last_training_year"],
        "inner_target_years":[2012,origin],
        "training_n":train["final_train_n"],
        "selected_ridge_lambda":train["selected_ridge_lambda"],
        "final_beta_log1p":train["final_beta_log1p"],
        "final_beta_intercept_only":train["final_beta_intercept_only"],
        "beta_raw":beta,
        "inner_validation_min_year":train["inner_select_targets"][0],
        "inner_validation_max_year":train["inner_select_targets"][1],
        "post_origin_training_observations":0,
    }


def shapley_three(old_p,new_p,old_deaths,new_deaths,old_beta,new_beta):
    """3! exact Shapley attribution of p = sigmoid(logit Markov + beta dot log1p).

    Mathematical cross-vintage mixtures are NOT genuine UCDP publications,
    and decomposition is algebraic, not geopolitical causal identification.
    """
    if (not all(0<p<1 for p in (old_p,new_p))
        or any(type(d) is not int or d<0 for d in (old_deaths,new_deaths))
        or len(old_beta)!=3 or len(new_beta)!=3):
        raise ValueError("Malformed Shapley factors")
    old=(old_p,old_deaths,old_beta)
    new=(new_p,new_deaths,new_beta)
    def value(flags):
        x=[new[i] if flags[i] else old[i] for i in range(3)]
        return predict({"p_original_binary":x[0],"origin_deaths":x[1]},x[2])
    contributions=[0.0]*3
    for order in itertools.permutations(range(3)):
        flags=[False]*3
        before=value(flags)
        for index in order:
            flags[index]=True
            after=value(flags)
            contributions[index]+=(after-before)/6
            before=after
    total=value([True,True,True])-value([False,False,False])
    if abs(sum(contributions)-total)>EPS:
        raise AssertionError("Exact 3-factor Shapley telescope failed")
    return {
        "delta_probability_pp":round(total*100,9),
        "binary_markov_kernel_pp":round(contributions[0]*100,9),
        "origin_annual_deaths_pp":round(contributions[1]*100,9),
        "trained_logistic_coefficients_pp":round(contributions[2]*100,9),
        "algebraic_not_causal":True,
    }


def quantile(data,prob):
    if not data or not 0<prob<=1:
        raise ValueError("Unspecified quantile")
    return sorted(data)[math.ceil(prob*len(data))-1]


def statistics(rows):
    if len(rows)!=196:
        raise ValueError("Inconsistent fixed cohort")
    deltas=[r["revised_shadow_p"]-r["old_shadow_p"] for r in rows]
    markov=[r["revised_binary_markov_p"]-r["old_binary_markov_p"]
            for r in rows]
    absdiff=sorted(abs(x) for x in deltas)
    abs_binary=sorted(abs(x) for x in markov)
    return {
        "n":len(rows),
        "n_revised_origin_death_counts":sum(
            r["old_origin_deaths"]!=r["revised_origin_deaths"] for r in rows),
        "n_revised_origin_binary_states":sum(
            r["old_origin_state"]!=r["revised_origin_state"] for r in rows),
        "mean_absolute_log1p_revision_pp":round(100*sum(absdiff)/len(rows),9),
        "mean_absolute_original_binary_revision_pp":
            round(100*sum(abs_binary)/len(rows),9),
        "p50_absolute_log1p_revision_pp":round(100*quantile(absdiff,.5),9),
        "p95_absolute_log1p_revision_pp":round(100*quantile(absdiff,.95),9),
        "max_absolute_log1p_revision_pp":round(100*absdiff[-1],9),
        "max_absolute_original_binary_revision_pp":round(100*abs_binary[-1],9),
        "n_shadow_change_at_least_2_5pp":sum(abs(x)>=.025 for x in deltas),
        "n_shadow_change_at_least_5pp":sum(abs(x)>=.05 for x in deltas),
        "old_sum_expected_active":round(sum(r["old_shadow_p"] for r in rows),9),
        "revised_sum_expected_active":round(
            sum(r["revised_shadow_p"] for r in rows),9),
        "sum_probability_revision":round(sum(deltas),9),
        "sum_absolute_shapley_factor_pp":{
            factor:round(sum(abs(r["shapley"][factor+"_pp"]) for r in rows),9)
            for factor in FACTORS
        },
        "sum_signed_shapley_factor_pp":{
            factor:round(sum(r["shapley"][factor+"_pp"] for r in rows),9)
            for factor in FACTORS
        },
    }


def topk_shadow_comparison(rows,state,k,names):
    group=[r for r in rows if r["old_origin_state"]==state]
    if len(group)<=k:
        raise ValueError("Too few historical risk countries")
    if any(r["old_origin_state"]!=r["revised_origin_state"] for r in group):
        raise ValueError("Origin risk state changed: must treat as separate ambiguity")
    old={r["country_id"]:round(
        r["old_shadow_p"] if state==0 else 1-r["old_shadow_p"],12)
        for r in group}
    later={r["country_id"]:round(
        r["revised_shadow_p"] if state==0 else 1-r["revised_shadow_p"],12)
        for r in group}
    a,b=admissible_topk(old,k),admissible_topk(later,k)
    exited=set(a["ordered"])-set(b["ordered"])
    entered=set(b["ordered"])-set(a["ordered"])
    def name(ids):
        return [{"country_id":cid,"country":names.get(cid,str(cid))}
                for cid in sorted(ids)]
    return {
        "origin_state":state,
        "risk_n":len(group),"budget":k,
        "ranking_question":"entry_2024_2025_if_origin_inactive" if state==0
            else "exit_2024_2025_if_origin_active",
        "old_topk":name(a["ordered"]),
        "revised_topk":name(b["ordered"]),
        "deterministic_swaps_n":len(exited),
        "deterministic_exited":name(exited),
        "deterministic_entered":name(entered),
        "definite_exits_not_dependent_on_ties":
            name(a["mandatory"]-b["possible"]),
        "definite_entries_not_dependent_on_ties":
            name(b["mandatory"]-a["possible"]),
        "old_boundary_unique":a["boundary_selection_unique"],
        "new_boundary_unique":b["boundary_selection_unique"],
        "rank_deterministic_tiebreak":"ascending_GWNO",
        "never_a_new_issued_2027_alert":True,
    }


def study(all_sources,names,reference):
    if (reference.get("schema")!="idealab.psico.geo2027_log1p_nested_h2_research.v1"
        or reference.get("n_2027_outcomes_resolved")!=0
        or reference.get("historical_predictions_actually_issued") is not False):
        raise ValueError("Frozen nested H2 study provenance invalid")
    if len(names)!=196 or len(set(names))!=196:
        raise ValueError("Original fixed 196-country universe changed")
    snapshots={}
    pairs=[]
    for year,old_version,new_version in PAIRS:
        def get(version):
            key=(year,version)
            if key not in snapshots:
                snapshots[key]=snapshot(all_sources[version],year,names)
            return snapshots[key]
        old,old_info=get(old_version)
        revised,new_info=get(new_version)
        previous=next(f for f in reference["folds"]
                      if f["origin_cutoff"]==year and
                      f["origin_vintage"]==old_version)
        if any(abs(v-w)>EPS for v,w in zip(
            old_info["final_beta_log1p"],
            previous["nested_training_and_selection"]["final_beta_log1p"])):
            raise AssertionError("Original vintage log1p coefficients fail prior study reproduction")
        if old_info["selected_ridge_lambda"]!=previous[
            "nested_training_and_selection"]["selected_ridge_lambda"]:
            raise AssertionError("Source predeclared inner lambda changed")
        results=[]
        for cid in sorted(names):
            a,b=old[cid],revised[cid]
            if a["origin_state"]!=b["origin_state"]:
                raise ValueError("Historical binary origin reclassified: split separately")
            split=shapley_three(
                a["p_original_binary_h2"],b["p_original_binary_h2"],
                a["origin_deaths_best"],b["origin_deaths_best"],
                old_info["beta_raw"],new_info["beta_raw"])
            if (abs(split["delta_probability_pp"]/100-
                    (b["p_log1p_h2"]-a["p_log1p_h2"]))>2e-10):
                raise AssertionError("Historical shadow arithmetic attribution mismatch")
            results.append({
                "country_id":cid,"country":names[cid],
                "old_origin_state":a["origin_state"],
                "revised_origin_state":b["origin_state"],
                "old_origin_deaths":a["origin_deaths_best"],
                "revised_origin_deaths":b["origin_deaths_best"],
                "old_binary_markov_p":a["p_original_binary_h2"],
                "revised_binary_markov_p":b["p_original_binary_h2"],
                "old_shadow_p":a["p_log1p_h2"],
                "revised_shadow_p":b["p_log1p_h2"],
                "shapley":split,
            })
        ranked=sorted(results,key=lambda r:(-
            abs(r["revised_shadow_p"]-r["old_shadow_p"]),r["country_id"]))
        stats=statistics(results)
        pairs.append({
            "origin":year,"forecast_horizon":2,
            "old_edition":old_version,"revised_edition":new_version,
            "post_origin_years_from_later_source_removed":True,
            "same_old_origin_riskset":True,
            "all_origin_states_unchanged":True,
            "old_training":{
                key:value for key,value in old_info.items() if key!="beta_raw"},
            "revised_training":{
                key:value for key,value in new_info.items() if key!="beta_raw"},
            "summary":stats,
            "top10_entry":topk_shadow_comparison(results,0,10,names),
            "top5_resolution":topk_shadow_comparison(results,1,5,names),
            "largest_12_absolute_shadow_probability_revisions":ranked[:12],
            "countries_with_changed_origin_best_deaths":[
                {"country_id":r["country_id"],"country":r["country"],
                 "old_deaths":r["old_origin_deaths"],
                 "revised_deaths":r["revised_origin_deaths"]}
                for r in results if r["old_origin_deaths"]!=r["revised_origin_deaths"]
            ],
        })
    return {
        "schema":"idealab.psico.geo2027_log1p_historical_vintage_robustness.v1",
        "status":"RETROSPECTIVE_UCDP_VINTAGE_STRESS_EX_POST_NOT_2027_FORECAST_REVISION",
        "original_geo2027_immutable_sha256":SOURCE_SHA256,
        "log1p_shadow2027_first_issued_sha256":SHADOW_SHA256,
        "all_source_editions_sha256":{
            version:SOURCES[version]["sha256"] for version in VERSION_ORDER},
        "origin_years":[2022,2023],
        "paired_comparisons":[
            {"old":old,"revised":new,"origin":year}
            for year,old,new in PAIRS],
        "repeated_old_edition_snapshots_and_correlated_versions_not_independent":True,
        "horizon_years":2,
        "fixed_old_country_ids_n":196,
        "three_shapley_factors":list(FACTORS),
        "full_three_factor_counterfactual_shapley_not_causal":True,
        "later_editions_never_have_2025_origin_for_2027_original_issuance":True,
        "historical_simulations_not_2022_2023_issued_predictions":True,
        "comparison_count":len(pairs),
        "comparisons":pairs,
        "actual_2027_forecast_shadow_probabilities_replaced":False,
        "actual_2027_frozen_alerts_reissued":False,
        "outcomes_2027_observed":0,
        "prospective_predictive_skill_demonstrated":False,
        "limitations":"The five matched vintage comparisons share origins, country-years and model fits: they are not five independent replication samples. Newer UCDP editions may change past deaths even after historical origin; only old-year values at or below origin enter any fit. Shapley mathematically attributes changes to p_GEO, origin deaths and refitted coefficients, not distinct causal mechanisms or forecast uncertainty. Zero 2027 labels observed; 2025-origin 2027 shadow cannot be restated using editions ending 2022-2024. No future predictive performance is measured.",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    args=ap.parse_args()
    original=FORECAST_PATH.read_bytes()
    issued_shadow=SHADOW.read_bytes()
    issued_alerts=ALERTS.read_bytes()
    if (sha(original)!=SOURCE_SHA256 or sha(issued_shadow)!=SHADOW_SHA256
        or sha(issued_alerts)!=ALERT_SHA256):
        raise ValueError("Frozen original 2027, LOG1P shadow or alerts SHA changed")
    issue=json.loads(original)
    shadow_doc=json.loads(issued_shadow)
    manifest=json.loads(SHADOW_MANIFEST.read_text(encoding="utf8"))
    if (manifest.get("shadow_file_sha256")!=SHADOW_SHA256
        or manifest.get("first_complete_forecast_commit")!=
           "a2af84346bd223d2a105cf727b3462cd0955fdac"
        or shadow_doc.get("outcomes_2027_resolved")!=0
        or shadow_doc.get("forecast_id")!=
           "PSICO-GEO2027-STATEBASED25-LOG1P-INTENSITY-SHADOW-V1"
        or len(shadow_doc.get("countries",[]))!=196):
        raise ValueError("First-issued prospective shadow manifest or cohort changed")
    names={x["country_id"]:x["country"] for x in issue["countries"]}
    if set(names)!={x["country_id"] for x in shadow_doc["countries"]}:
        raise ValueError("Old and shadow GWNO universe mismatch")
    vintages={}
    for version in VERSION_ORDER:
        raw=request(SOURCES[version]["url"],MAX_DOWNLOAD)
        vintages[version]=parse_counts(raw,version)
    prior=json.loads(PREVIOUS.read_text(encoding="utf8"))
    result=study(vintages,names,prior)
    payload=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    print("GEO2027_LOG1P_VINTAGE_ROBUSTNESS_BEGIN")
    print(payload,end="")
    print("GEO2027_LOG1P_VINTAGE_ROBUSTNESS_END")
    if args.check_report and REPORT.read_bytes()!=payload.encode():
        raise ValueError("UCDP source-replayed LOG1P historical stress report differs")


if __name__=="__main__":
    main()
