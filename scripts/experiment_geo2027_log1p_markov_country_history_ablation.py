#!/usr/bin/env python3
"""Post-issuance GEO H2 Markov local-history and global-own-leakage ablation.

For each retrospective H2 target and origin subthreshold (1..24) country:
  1. Keep held-out-calibrator beta from the previously audited protocol.
  2. Compare original Markov offset; Markov global transitions with the
     country removed but still local country transitions; and pure globally
     pooled Markov with the country removed, given its observed origin state.
  3. Keep beta FIXED across the three Markov offset variants. Thus this
     isolates predictive sensitivity to the target country's history without
     claiming a globally re-trained matched predictor.
No 2027 forecast reissue. All old source releases were published later than
some examined historical outcomes. Ridge/alpha family already inspected.
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
    MAX_DOWNLOAD, VERSION_ORDER, parse_counts, counts_to_binary,
)
from experiment_geo2027_log1p_nested_h2 import binary_h2_until
from experiment_geo2027_log1p_inactive_attenuation_frontier import p_scaled
from experiment_geo2027_log1p_rolling_year_vintage import (
    historical_ledger, fit_target, sha, RIDGE,
)
from experiment_geo2027_log1p_country_block_transfer import (
    COMPARISONS, FOCUS, calibration_training, omit_country_fit, score_gap,
)
from prepare_geo2027_transition_alerts import SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo2027-log1p-markov-country-history-ablation.json"
PRIOR=ROOT/"data/geo2027-log1p-subthreshold-country-block-transfer.json"
GEO_PRIOR_LAPLACE=1
GEO_OWN_PRIOR_WEIGHT=20
TOL=5e-10
VARIANTS=("original_with_own_global_and_local",
          "exclude_own_global_keep_local",
          "exclude_own_global_and_local_global_only")
FOCUS_YEARS=(2017,2024,2025)


def _empty():
    return [[0,0],[0,0]]


def _count_transitions(binary,cutoff):
    """Transition count sufficient statistics, no post-cutoff observations."""
    if type(cutoff) is not int or not 2010<=cutoff<=2023:
        raise ValueError("Outside original historical cutoff")
    glob=_empty()
    locals={}
    for cid,h in binary.items():
        if type(cid) is not int or not isinstance(h,dict):
            raise ValueError("Invalid archived GWNO source")
        own=_empty()
        for year in sorted(h):
            if year>cutoff or year-1 not in h:
                continue
            s1,s2=h[year-1],h[year]
            if s1 not in (0,1) or s2 not in (0,1):
                raise ValueError("Invalid official state-based count")
            own[s1][s2]+=1
            glob[s1][s2]+=1
        locals[cid]=own
    if min(sum(row) for row in glob)<100:
        raise ValueError("Insufficient global transition exposures")
    return glob,locals


def _nstep_two(state,q):
    if state not in (0,1) or len(q)!=2 or not all(0<p<1 for p in q):
        raise ValueError("Malformed two-step transition estimator")
    start=q[state]
    return (1-start)*q[0]+start*q[1]


def markov_counterfactual_offsets(global_counts,local_counts,origin_state):
    """Exact frozen-law 2-state Markov LOO country decomposition.

    Output in original with local+global (baseline), global-LOO with local,
    global-LOO with no local prior (cold-ish origin-state only). Historical
    country is withheld from global denominator even if not scored.
    """
    if (origin_state not in (0,1) or
        len(global_counts)!=2 or len(local_counts)!=2):
        raise ValueError("Malformed state/transition counts")
    for arr in (global_counts,local_counts):
        if any(len(row)!=2 or any(type(x) is not int or x<0 for x in row)
               for row in arr):
            raise ValueError("Invalid transition count table")
    without=[[global_counts[i][j]-local_counts[i][j] for j in (0,1)]
             for i in (0,1)]
    if any(x<0 for row in without for x in row):
        raise ValueError("Country count exceeds global transitions")
    if min(sum(x) for x in without)<100:
        raise ValueError("Insufficient leave-country-out global prior")
    if (GEO_PRIOR_LAPLACE!=1 or GEO_OWN_PRIOR_WEIGHT!=20):
        raise AssertionError("Frozen original GEO estimator law changed")
    original_global=[(row[1]+1)/(sum(row)+2) for row in global_counts]
    omit_global=[(row[1]+1)/(sum(row)+2) for row in without]
    def local_q(g):
        return [(local_counts[i][1]+20*g[i])/(sum(local_counts[i])+20)
                for i in (0,1)]
    p_original=round(_nstep_two(origin_state,local_q(original_global)),12)
    p_excl_global_local=round(_nstep_two(origin_state,local_q(omit_global)),12)
    p_excl_global_local_none=round(_nstep_two(origin_state,omit_global),12)
    return {
        VARIANTS[0]:p_original,
        VARIANTS[1]:p_excl_global_local,
        VARIANTS[2]:p_excl_global_local_none,
        "removed_global_transitions":sum(sum(row) for row in local_counts),
        "original_global_transition_probabilities":
            [round(g,12) for g in original_global],
        "heldout_global_transition_probabilities":
            [round(g,12) for g in omit_global],
        "own_transition_matrix":local_counts,
        "global_transition_matrix":global_counts,
        "heldout_global_transition_matrix":without,
    }


def _sign(delta):
    if not math.isfinite(delta):
        raise ValueError("Non-finite Brier")
    return ("full_intensity_better" if delta<-1e-12 else
            "no_subthreshold_intensity_better" if delta>1e-12 else
            "effectively_equal")


def one_block(source,edition,target,names,prior):
    old=next(r for r in prior["all_blocks"]
             if r["source_version"]==edition and r["target_year"]==target)
    cutoff=target-2
    ledger=historical_ledger(source,SOURCES[edition]["last_year"],names)
    full_beta,meta=fit_target(ledger,target)
    if (meta["max_supervised_training_label_year"]!=cutoff or
        meta["max_training_feature_year"]!=target-4 or
        meta["coefficients"]!=next(r for r in json.loads(
            (ROOT/"data/geo2027-log1p-rolling-year-vintage-stability.json").read_text(
                encoding="utf8"))["rolling_result"]["by_version"][edition]["annual"]
            if r["target_year"]==target)["fit"]["coefficients"]):
        raise AssertionError("Published annual H2 benchmark changed")
    training=calibration_training(ledger,target)
    history=ledger[target]
    affected=[r for r in history if 1<=r["origin_deaths"]<=24]
    if not affected or len(affected)!=old["subthreshold_1_to_24_n"]:
        raise AssertionError("Original historical subthreshold cohort changed")
    binary=counts_to_binary(source)
    global_counts,locals=_count_transitions(binary,cutoff)
    reference=binary_h2_until(binary,cutoff)
    by_country={}
    exact=[]
    for r in affected:
        cid=r["country_id"]
        beta,fitmeta=omit_country_fit(training,cid,target)
        off=markov_counterfactual_offsets(
            global_counts,locals[cid],r["origin_state"])
        if (off[VARIANTS[0]]!=r["p_original_binary"]
            or reference[cid]!=r["p_original_binary"]):
            raise AssertionError("Baseline country Markov p does not reproduce")
        if (fitmeta["last_training_label_year"]!=cutoff or
            fitmeta["last_training_feature_year"]!=target-4 or
            fitmeta["removed_historical_rows"]<3):
            raise AssertionError("Country-block calibrator temporal cutoff failed")
        y=r["outcome"]
        d={}
        for variant in VARIANTS:
            base=off[variant]
            pzero=round(p_scaled(base,r["origin_deaths"],beta,0.0),12)
            pfull=round(p_scaled(base,r["origin_deaths"],beta,1.0),12)
            delta=score_gap(pzero,pfull,y)
            d[variant]={
                "markov_p_h2":base,
                "alpha0_p":pzero,
                "alpha1_p":pfull,
                "alpha0_brier":round((pzero-y)**2,12),
                "alpha1_brier":round((pfull-y)**2,12),
                "delta_alpha1_minus_alpha0":round(delta,12),
                "delta_unrounded":delta,
            }
        original_case=next((
            row for row in old["all_subthreshold_cases"]
            if row["country_id"]==cid),None) if old["all_cases_stored"] else None
        if original_case and (
            d[VARIANTS[0]]["alpha0_p"]!=original_case["country_excluded_alpha0_p"]
            or d[VARIANTS[0]]["alpha1_p"]!=original_case["country_excluded_alpha1_p"]
            or abs(d[VARIANTS[0]]["delta_alpha1_minus_alpha0"]-
                   original_case["country_excluded_paired_Brier_delta"])>TOL):
            raise AssertionError("Prior country-excluded logistic prediction mutated")
        by_country[cid]={"country_id":cid,"country":names[cid],
            "origin_deaths":r["origin_deaths"],
            "binary_outcome":y,
            "calibration_country_removed_rows":fitmeta["removed_historical_rows"],
            "calibration_beta_country_excluded":[round(x,12) for x in beta],
            "Markov_own_country_transition_count":off["removed_global_transitions"],
            "Markov_global_probability_shift_excluding_own_country_pp":round(
                100*(off[VARIANTS[1]]-off[VARIANTS[0]]),9),
            "Markov_local_history_effect_given_global_country_exclusion_pp":round(
                100*(off[VARIANTS[1]]-off[VARIANTS[2]]),9),
            "by_variant":{k:{j:v for j,v in d[k].items()
                          if j!="delta_unrounded"} for k in VARIANTS}}
        exact.append((cid,d))
    if len(exact)!=len(affected):
        raise AssertionError("Failed to score every subthreshold country")
    by_variant={}
    for variant in VARIANTS:
        z=[x[variant] for _,x in exact]
        gap=sum(row["delta_unrounded"] for row in z)
        b0=sum((row["alpha0_p"]-by_country[cid]["binary_outcome"])**2
               for cid,x in exact for row in [x[variant]])
        b1=sum((row["alpha1_p"]-by_country[cid]["binary_outcome"])**2
               for cid,x in exact for row in [x[variant]])
        n=len(affected);total=len(history)
        if abs((b1-b0)-gap)>TOL:
            raise AssertionError("Score gap not additive across country pairings")
        by_variant[variant]={
            "subthreshold_affected_n":n,
            "subthreshold_target_active_n":sum(r["outcome"] for r in affected),
            "sum_brier_alpha0":round(b0,12),
            "sum_brier_alpha1":round(b1,12),
            "mean_brier_alpha0_subthreshold":round(b0/n,12),
            "mean_brier_alpha1_subthreshold":round(b1/n,12),
            "delta_brier_alpha1_minus_alpha0_on_full_evaluable_risk_n":
                round(gap/total,12),
            "delta_brier_alpha1_minus_alpha0_within_subthreshold":
                round(gap/n,12),
            "winner_sign":_sign(gap),
        }
    if abs(by_variant[VARIANTS[0]][
        "delta_brier_alpha1_minus_alpha0_on_full_evaluable_risk_n"]-
        old["blocked_delta_Brier_on_full_risk_n"])>TOL:
        raise AssertionError("Prior country-blocked logistic annual Brier differs")
    diag=[]
    for cid,d in exact:
        base=d[VARIANTS[0]]["delta_unrounded"]
        for variant in VARIANTS[1:]:
            new=d[variant]["delta_unrounded"]
            diag.append({"country_id":cid,"country":names[cid],
                "variant":variant,"absolute_change_delta_brier":
                round(abs(new-base),12),"change_delta_brier":round(new-base,12)})
    diag.sort(key=lambda z:(-z["absolute_change_delta_brier"],z["country_id"],z["variant"]))
    glob_shifts=[abs(x["Markov_global_probability_shift_excluding_own_country_pp"])
                 for x in by_country.values()]
    local_shifts=[abs(x["Markov_local_history_effect_given_global_country_exclusion_pp"])
                  for x in by_country.values()]
    def describe_case(x):
        return {k:v for k,v in x.items()}
    return {
        "source_version":edition,"target_year":target,
        "origin_year":cutoff,
        "evaluated_country_n":len(history),
        "origin_1_to_24_country_n":len(affected),
        "country_blocked_logistic_calibration_with_original_markov":
            old["blocked_delta_Brier_on_full_risk_n"],
        "training_labels_max_year":meta["max_supervised_training_label_year"],
        "training_features_max_year":meta["max_training_feature_year"],
        "Markov_cutoff_max_year":cutoff,
        "separate_training_rows_each_holdout_country":True,
        "Markov_global_counts_remove_heldout_country_before_shrinkage":True,
        "Markov_local_history_frozen_except_in_global_only_variant":True,
        "same_country_excluded_logistic_coefficients_across_Markov_variants":True,
        "by_variant":by_variant,
        "any_winner_changed_across_markov_scenarios":
            len({v["winner_sign"] for v in by_variant.values()})>1,
        "mean_abs_markov_global_own_exclusion_effect_pp":
            round(sum(glob_shifts)/len(glob_shifts),9),
        "max_abs_markov_global_own_exclusion_effect_pp":
            max(glob_shifts),
        "mean_abs_markov_local_history_effect_pp":
            round(sum(local_shifts)/len(local_shifts),9),
        "max_abs_markov_local_history_effect_pp":
            max(local_shifts),
        "top8_most_changed_country_paired_losses":diag[:8],
        "all_subthreshold_countries":
            [describe_case(by_country[cid]) for cid in sorted(by_country)]
            if target in FOCUS_YEARS else [],
        "all_cases_included":target in FOCUS_YEARS,
        "limitation":"Country held out of GLOBAL transition pool and logistic calibration. For third variant, no local country transition counts are used in Markov, but its observed origin state is retained. Logistic coefficients are those fitted using ORIGINAL per-country Markov offsets for the other training countries. Therefore the global-only ablation suffers potential calibration offset covariate shift and is not a separately trained cold-start pipeline."
    }


def study(sources,names,prior):
    if (prior.get("schema")!="idealab.psico.geo2027_log1p_country_block_calibration_transfer.v1"
        or not prior.get("no_prospective_2027_outcomes")
        or prior.get("n_year_edition_blocks")!=13
        or prior.get("baseline_forecast_shadow_sha256")!=FROZEN_ISSUE_SHA256
        or len(names)!=196 or set(sources)!=set(VERSION_ORDER)):
        raise ValueError("Prior issued country-block calibration/source provenance invalid")
    blocks=[]
    for edition,target in COMPARISONS:
        blocks.append(one_block(sources[edition],edition,target,names,prior))
    if len(blocks)!=13:
        raise AssertionError("Incomplete predefined source/target pairs")
    yearly=[r for r in blocks if r["source_version"]=="26.1"]
    if len(yearly)!=9:
        raise AssertionError("Nine distinct target years required")
    return {
        "schema":"idealab.psico.geo2027_log1p_Markov_country_history_ablation.v1",
        "status":"EX_POST_FIXED_BETA_MARKOV_COUNTRY_HISTORY_SOURCE_ABLATION_NOT_2027_ISSUE",
        "issued_original_GEO_SHA256":SOURCE_SHA256,
        "issued_LOG1P_shadow_SHA256":FROZEN_ISSUE_SHA256,
        "issued_15_alerts_SHA256":ALERT_SHA,
        "UCDP_archive_SHA256":{v:SOURCES[v]["sha256"] for v in VERSION_ORDER},
        "not_a_contemporaneously_issued_historical_forecast":True,
        "lambda_5_selected_after_historical_outcomes_seen":True,
        "same_alpha0_alpha1_family_as_prior":True,
        "year_target_training_label_cutoff_t_minus_2":True,
        "inner_row_feature_cutoff_t_minus_4":True,
        "heldout_country_all_logistic_training_labels_removed":True,
        "Markov_global_country_transition_counts_removed_by_subtraction":True,
        "Markov_state_at_origin_known_by_all_scenarios":True,
        "Markov_local_country_transitions_deleted_only_in_global_only_variant":True,
        "country_specific_calibration_coefficients_unchanged_across_offsets":True,
        "NOT_full_retrained_matched_global_only_pipeline":True,
        "global_only_markov_offset_covariate_shift_possible":True,
        "original_2027_forecasts_changed":False,
        "LOG1P_2027_shadow_forecasts_changed":False,
        "issued_2027_alerts_changed":False,
        "new_2027_forecast_issued":False,
        "official_2027_outcomes_resolved":0,
        "prospective_skill_demonstrated":False,
        "source_edition_year_overlap_not_independent":True,
        "n_year_edition_blocks":len(blocks),
        "n_distinct_target_years":len(yearly),
        "n_country_markov_heldout_cases":sum(r["origin_1_to_24_country_n"] for r in blocks),
        "markov_scenario_keys":list(VARIANTS),
        "yearly_latest_26_1":[{
            "target_year":r["target_year"],"affected_country_n":
                r["origin_1_to_24_country_n"],
            "blocked_calibration_paired_gap":r[
                "country_blocked_logistic_calibration_with_original_markov"],
            "global_excluded_keep_local_paired_gap":r["by_variant"][VARIANTS[1]][
                "delta_brier_alpha1_minus_alpha0_on_full_evaluable_risk_n"],
            "global_excluded_no_local_paired_gap":r["by_variant"][VARIANTS[2]][
                "delta_brier_alpha1_minus_alpha0_on_full_evaluable_risk_n"],
            "flip_excluding_markov_history":r[
                "any_winner_changed_across_markov_scenarios"],
        } for r in yearly],
        "blocks":blocks,
        "limitations":"Historical same-edition sources are retrospectively revised, not as-of contemporary; 13 blocks overlap 9 years. The nine-year alpha family and lambda5 have been inspected earlier, thus exploratory. All country-specific logistic coefficient refits see only other countries' historical supervised rows through t-2. The original Markov relies on local country history and globally pooled transitions, and the counterfactuals isolate excluding own transitions from global and then local q, while retaining observed origin state. For global-only the original fitted logistic calibrator is applied out of its training offset distribution, so this is not a separately trained/matched cold-start model. No country/edition IID inference, no prospective 2027 labels, no alteration to already issued original/shadow/alerts."
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report",action="store_true")
    args=parser.parse_args()
    audit_issued_shadow(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes())
    if sha(ALERTS.read_bytes())!=ALERT_SHA:
        raise ValueError("Frozen 15 issue-alert SHA changed")
    names={r["country_id"]:r["country"] for r in json.loads(
        ISSUE.read_text(encoding="utf8"))["countries"]}
    sources={v:parse_counts(request(SOURCES[v]["url"],MAX_DOWNLOAD),v)
             for v in VERSION_ORDER}
    prior=json.loads(PRIOR.read_text(encoding="utf8"))
    report=study(sources,names,prior)
    payload=json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    print("GEO2027_MARKOV_HISTORY_ABLATION_BEGIN")
    print(payload,end="")
    print("GEO2027_MARKOV_HISTORY_ABLATION_END",flush=True)
    if args.check_report and REPORT.read_bytes()!=payload.encode():
        raise ValueError("Published global/local Markov source ablation differs from SHA-pinned UCDP replay")


if __name__=="__main__":
    main()
