#!/usr/bin/env python3
"""Matched target-country-blocked GLOBAL-ONLY Markov -> LOG1P ridge pipeline.

Fixes PR #98's calibration covariate-shift flaw: its global-only H2 Markov
offsets were fed to ridge betas learned using country-local Markov offsets.

For each country c with 1..24 origin best state-based fatalities:
  - all supervised c rows removed from LOG1P training;
  - all transitions of c excluded from global Markov at EVERY training origin;
  - for each training country i != c, its transitions are ALSO excluded
    from the pooled prior used for its own row, preventing self-leakage;
  - logistic is fit on the resulting global-only H2 offsets through t-2;
  - evaluation c is scored with global-only prior excluding c, using only
    its known origin state and known origin best fatality count.
Compare alpha0 vs alpha1 and mismatched vs matched re-fit (absolute Brier).
Original model and 2027 196-country issues remain SHA-frozen.

Historic lambda=5 and alpha family selected after historical labels seen, and
editions are ex-post revised. Not a fresh prospective test or a forecast issue.
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
    VERSION_ORDER, MAX_DOWNLOAD, parse_counts, counts_to_binary,
)
from experiment_geo2027_log1p_nested_h2 import fit
from experiment_geo2027_log1p_inactive_attenuation_frontier import p_scaled
from experiment_geo2027_log1p_rolling_year_vintage import (
    historical_ledger, sha, RIDGE,
)
from experiment_geo2027_log1p_country_block_transfer import (
    COMPARISONS, FOCUS, calibration_training, omit_country_fit, score_gap,
)
from experiment_geo2027_log1p_markov_country_history_ablation import (
    _count_transitions, _nstep_two, VARIANTS, markov_counterfactual_offsets,
)
from prepare_geo2027_transition_alerts import SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo2027-log1p-matched-global-only-calibration.json"
PRIOR=ROOT/"data/geo2027-log1p-markov-country-history-ablation.json"
STATES=(0,1)
TOL=5e-10


def markov_global_only_offset(global_counts,locals_by_country,origin_state,
                              heldout_country,training_country=None):
    """Full cross-fitted global-only H2 probability.

    Training rows exclude BOTH their own source-country transitions and
    target evaluation-country transitions. At evaluation we exclude only
    target country's transitions. The target origin state is observed in both
    settings. No country-local Markov transition likelihood or shrinkage.
    """
    if (origin_state not in STATES or type(heldout_country) is not int
        or heldout_country not in locals_by_country or
        (training_country is not None and
         (type(training_country) is not int or
          training_country not in locals_by_country or
          training_country==heldout_country))):
        raise ValueError("Invalid heldout/source country or origin state")
    excluded=(heldout_country,) if training_country is None else (
        heldout_country,training_country)
    residual=[[global_counts[s][j]-
               sum(locals_by_country[c][s][j] for c in excluded)
               for j in STATES] for s in STATES]
    if (any(type(x) is not int or x<0 for row in residual for x in row)
        or min(sum(row) for row in residual)<100):
        raise ValueError("Insufficient valid excluding-country transition pool")
    q=[(row[1]+1)/(sum(row)+2) for row in residual]
    if not all(0<z<1 for z in q):
        raise ValueError("Invalid global-only transition probability")
    return round(_nstep_two(origin_state,q),12)


def make_snapshots(binary,training_rows,evaluation_origin):
    """Precompute pre-target Markov counts for each observed training origin."""
    cutoffs=sorted({r["origin_year"] for r in training_rows}
                   | {evaluation_origin})
    if (not cutoffs or cutoffs[0]<2010 or cutoffs[-1]!=evaluation_origin
        or any(y>evaluation_origin for y in cutoffs)):
        raise ValueError("Training feature uses future information")
    return {y:_count_transitions(binary,y) for y in cutoffs}


def matched_training_rows(training_rows,snapshots,heldout_country,target):
    """Remove heldout labels AND history from every other training offset."""
    if type(target) is not int or not 2017<=target<=2025:
        raise ValueError("Target outside chronological H2 experiment")
    if not any(r["country_id"]==heldout_country for r in training_rows):
        raise ValueError("The target country had no historical rows to exclude")
    transformed=[]
    for r in training_rows:
        if r["country_id"]==heldout_country:
            continue
        if (r["target_year"]>target-2
            or r["origin_year"]>target-4
            or r["origin_year"]!=r["target_year"]-2):
            raise ValueError("Historical t-2/t-4 cutoff leakage")
        counts,locals_by_country=snapshots[r["origin_year"]]
        new_p=markov_global_only_offset(
            counts,locals_by_country,
            int(r["origin_deaths"]>=25),heldout_country,r["country_id"])
        transformed.append({**r,"p_original_binary":new_p})
    if (len(transformed)<500 or
        any(r["country_id"]==heldout_country for r in transformed)
        or max(r["target_year"] for r in transformed)!=target-2
        or max(r["origin_year"] for r in transformed)!=target-4):
        raise ValueError("Incomplete matched target-country-blocked model")
    return transformed


def matched_fit(training_rows,snapshots,heldout_country,target):
    rows=matched_training_rows(training_rows,snapshots,heldout_country,target)
    beta=fit(rows,RIDGE)
    return beta,{
        "heldout_country":heldout_country,
        "fit_n":len(rows),
        "last_training_label_year":max(r["target_year"] for r in rows),
        "last_training_feature_year":max(r["origin_year"] for r in rows),
        "global_prior_excludes_target_and_training_row_country":True,
        "local_training_country_history_used_for_own_offset":False,
        "target_country_training_labels_used":False,
        "target_country_training_transition_counts_used":False,
        "ridge_fixed":RIDGE,
    }


def scoring_pair(offset,deaths,beta,y):
    p0=round(p_scaled(offset,deaths,beta,0.0),12)
    p1=round(p_scaled(offset,deaths,beta,1.0),12)
    return {
        "alpha0_p":p0,"alpha1_p":p1,
        "alpha0_loss":(p0-y)**2,
        "alpha1_loss":(p1-y)**2,
        "delta_alpha1_minus_alpha0":score_gap(p0,p1,y),
    }


def _summary(case_rows,field,denominator):
    if not case_rows or denominator<len(case_rows):
        raise ValueError("Short matched country riskset")
    a0=sum(r[field]["alpha0_loss"] for r in case_rows)
    a1=sum(r[field]["alpha1_loss"] for r in case_rows)
    delta=sum(r[field]["delta_alpha1_minus_alpha0"] for r in case_rows)
    if abs((a1-a0)-delta)>TOL:
        raise AssertionError("Paired Brier score mismatch")
    return {
        "n_affected":len(case_rows),
        "mean_Brier_alpha0_only_affected":round(a0/len(case_rows),12),
        "mean_Brier_alpha1_only_affected":round(a1/len(case_rows),12),
        "delta_alpha1_minus_alpha0_on_full_reference_risk_n":
            round(delta/denominator,12),
        "delta_alpha1_minus_alpha0_within_affected":
            round(delta/len(case_rows),12),
        "winner":"alpha1_full_better" if delta<-1e-12 else
                 "alpha0_no_subthreshold_better" if delta>1e-12 else
                 "effectively_equal",
        "sum_loss_alpha0":round(a0,12),
        "sum_loss_alpha1":round(a1,12),
    }


def one_block(source,edition,target,names,prior):
    old=next(x for x in prior["blocks"] if
             x["source_version"]==edition and x["target_year"]==target)
    cutoff=target-2
    ledger=historical_ledger(source,SOURCES[edition]["last_year"],names)
    training=calibration_training(ledger,target)
    by_country={r["country_id"]:r for r in ledger[target]
                if 1<=r["origin_deaths"]<=24}
    if len(by_country)!=old["origin_1_to_24_country_n"]:
        raise AssertionError("Historical 1-24 source riskset changed")
    binary=counts_to_binary(source)
    snapshots=make_snapshots(binary,training,cutoff)
    evaluation_counts,evaluation_locals=snapshots[cutoff]
    old_focus={r["country_id"]:r for r in old["all_subthreshold_countries"]}
    cases=[]
    for cid in sorted(by_country):
        r=by_country[cid]
        mismatch_beta,_=omit_country_fit(training,cid,target)
        fitted,meta=matched_fit(training,snapshots,cid,target)
        p=markov_global_only_offset(
            evaluation_counts,evaluation_locals,r["origin_state"],cid)
        original_off=markov_counterfactual_offsets(
            evaluation_counts,evaluation_locals[cid],r["origin_state"])
        if (p!=original_off[VARIANTS[2]]
            or r["origin_state"]!=0
            or meta["last_training_label_year"]!=target-2
            or meta["last_training_feature_year"]!=target-4):
            raise AssertionError("Matched Markov H2 global-only offset differs")
        y=r["outcome"]
        original=scoring_pair(original_off[VARIANTS[0]],
                              r["origin_deaths"],mismatch_beta,y)
        mismatched=scoring_pair(p,r["origin_deaths"],mismatch_beta,y)
        matched=scoring_pair(p,r["origin_deaths"],fitted,y)
        if old_focus:
            prev=old_focus[cid]["by_variant"]
            for field,x in (("alpha0_p","alpha0_p"),
                            ("alpha1_p","alpha1_p")):
                if (abs(original[field]-prev[VARIANTS[0]][x])>TOL
                    or abs(mismatched[field]-prev[VARIANTS[2]][x])>TOL):
                    raise AssertionError("Previously issued scientific audit changed")
        cases.append({
            "country_id":cid,"country":names[cid],
            "origin_year":cutoff,"origin_deaths":r["origin_deaths"],
            "target_year":target,"target_outcome":y,
            "original_local_markov_probability":original_off[VARIANTS[0]],
            "heldout_global_only_markov_probability":p,
            "country_training_rows_excluded":sum(
                x["country_id"]==cid for x in training),
            "matched_training_rows":meta["fit_n"],
            "beta_country_excluded_original_offsets":
                [round(x,12) for x in mismatch_beta],
            "beta_country_excluded_global_only_offsets":
                [round(x,12) for x in fitted],
            "absolute_matched_beta_inactive_shift":round(
                abs(fitted[1]-mismatch_beta[1]),12),
            "original_markov_country_blocked_calibration":original,
            "global_only_markov_unmatched_calibration":mismatched,
            "global_only_markov_matched_calibration":matched,
        })
    ref_n=len(ledger[target])
    summaries={
        key:_summary(cases,key,ref_n)
        for key in ("original_markov_country_blocked_calibration",
                    "global_only_markov_unmatched_calibration",
                    "global_only_markov_matched_calibration")
    }
    first=summaries["original_markov_country_blocked_calibration"]
    former=summaries["global_only_markov_unmatched_calibration"]
    if (abs(first[
        "delta_alpha1_minus_alpha0_on_full_reference_risk_n"]-
        old["by_variant"][VARIANTS[0]][
        "delta_brier_alpha1_minus_alpha0_on_full_evaluable_risk_n"])>TOL or
        abs(former[
        "delta_alpha1_minus_alpha0_on_full_reference_risk_n"]-
        old["by_variant"][VARIANTS[2]][
        "delta_brier_alpha1_minus_alpha0_on_full_evaluable_risk_n"])>TOL):
        raise AssertionError("Exact prior historical country-block report mismatch")
    return {
        "source_version":edition,
        "target_year":target,
        "forecast_origin_year":cutoff,
        "n_full_reference":ref_n,
        "n_subthreshold_affected":len(cases),
        "n_future_binary_positive_affected":sum(x["target_outcome"]
                                                for x in cases),
        "last_training_label_year":cutoff,
        "last_training_feature_year":target-4,
        "mean_abs_beta_inactive_shift":round(sum(
            x["absolute_matched_beta_inactive_shift"] for x in cases
        )/len(cases),12),
        "max_abs_beta_inactive_shift":max(
            x["absolute_matched_beta_inactive_shift"] for x in cases),
        "by_design":summaries,
        "matched_retraining_changes_alpha_winner_from_unmatched":
            former["winner"]!=summaries[
                "global_only_markov_matched_calibration"]["winner"],
        "matched_retraining_changes_alpha_winner_from_original":
            first["winner"]!=summaries[
                "global_only_markov_matched_calibration"]["winner"],
        "all_country_pairs":cases if target in FOCUS else [],
        "country_pairs_published":target in FOCUS,
        "not_an_independent_validation":True,
    }


def study(sources,names,prior):
    if (prior.get("schema")!="idealab.psico.geo2027_log1p_Markov_country_history_ablation.v1"
        or prior.get("official_2027_outcomes_resolved")!=0
        or prior.get("issued_LOG1P_shadow_SHA256")!=FROZEN_ISSUE_SHA256
        or prior.get("n_year_edition_blocks")!=13
        or len(names)!=196 or set(sources)!=set(VERSION_ORDER)):
        raise ValueError("Original scientific source/forecast provenance invalid")
    blocks=[one_block(sources[ver],ver,target,names,prior)
            for ver,target in COMPARISONS]
    if (len(blocks)!=13 or sum(x["n_subthreshold_affected"]
                              for x in blocks)!=143):
        raise AssertionError("Original 13 source-vintage case composition changed")
    latest=[x for x in blocks if x["source_version"]=="26.1"]
    return {
        "schema":"idealab.psico.geo2027_LOG1P_matched_global_only_country_block.v1",
        "status":"HISTORICAL_POST_HOC_MATCHED_OFFSET_RETRAINING_NOT_PROSPECTIVE",
        "issued_original_geo_SHA256":SOURCE_SHA256,
        "issued_LOG1P_shadow_SHA256":FROZEN_ISSUE_SHA256,
        "issued_15_alerts_SHA256":ALERT_SHA,
        "archive_source_SHA256":{v:SOURCES[v]["sha256"] for v in VERSION_ORDER},
        "n_vintage_year_blocks":len(blocks),
        "n_distinct_target_years":len(latest),
        "n_heldout_country_cases":sum(x["n_subthreshold_affected"]
                                     for x in blocks),
        "nested_logistic_ridge_lambda_already_chosen_post_hoc":RIDGE,
        "alpha0_and_alpha1_previously_examined":True,
        "no_alpha_or_model_selected":True,
        "all_training_labels_heldout_country_removed":True,
        "all_training_global_markov_offsets_exclude_target_country":True,
        "all_training_global_markov_offsets_exclude_training_row_country":True,
        "all_training_country_local_markov_shrinkage_removed":True,
        "evaluation_markov_excludes_target_country_transitions":True,
        "evaluation_does_observe_target_state_and_origin_deaths":True,
        "strict_H2_training_labels_last_t_minus_2":True,
        "strict_H2_training_features_last_t_minus_4":True,
        "matched_beta_refitted_for_each_target_country":True,
        "absolute_Brier_scored_ONLY_on_subthreshold_affected_countries":True,
        "paired_alpha_Brier_196_denominator_is_descriptive_not_full_crossfit_score":True,
        "historical_source_versions_not_available_asof_forecast":True,
        "source_revisions_and_country_year_dependence_preclude_IID_inference":True,
        "no_original_2027_forecast_mutation":True,
        "no_shadow_2027_forecast_mutation":True,
        "no_alert_reissue":True,
        "no_new_forecast_issue":True,
        "2027_resolved_official_outcomes":0,
        "prospective_skill_demonstrated":False,
        "latest_26_1_summary":[{
            "target_year":x["target_year"],
            "subthreshold_n":x["n_subthreshold_affected"],
            "original_country_block_delta":x["by_design"][
                "original_markov_country_blocked_calibration"][
                    "delta_alpha1_minus_alpha0_on_full_reference_risk_n"],
            "global_only_unmatched_delta":x["by_design"][
                "global_only_markov_unmatched_calibration"][
                    "delta_alpha1_minus_alpha0_on_full_reference_risk_n"],
            "global_only_matched_delta":x["by_design"][
                "global_only_markov_matched_calibration"][
                    "delta_alpha1_minus_alpha0_on_full_reference_risk_n"],
            "matched_minus_unmatched_alpha1_mean_subthreshold_Brier":
                round(x["by_design"][
                    "global_only_markov_matched_calibration"][
                        "mean_Brier_alpha1_only_affected"]-
                      x["by_design"][
                    "global_only_markov_unmatched_calibration"][
                        "mean_Brier_alpha1_only_affected"],12),
            "matched_retraining_changed_sign":
                x["matched_retraining_changes_alpha_winner_from_unmatched"],
        } for x in latest],
        "blocks":blocks,
        "limitations":"COUNTRY-BLOCKED global-only matching: for every historical training row (source country i), Markov global transitions exclude heldout evaluation country c AND country i, at that row's origin u-2, while using origin-state from i; logistic is fit excluding all c labels through t-2. Evaluation c uses global excluding c with only c origin state and best deaths. Fixed lambda5 and alpha family chosen AFTER some outcomes examined and 4 revised UCDP vintages not as-of real-time sources, hence no valid independent prospective confirmation. Full riskset 196 Brier isn't crossfitted for active/zero counts; only subthreshold alpha contrast is compared. No 2027 outcomes or forecast changes."
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    args=ap.parse_args()
    audit_issued_shadow(ISSUE.read_bytes(),MANIFEST.read_bytes(),
                        ORIGINAL.read_bytes())
    if sha(ALERTS.read_bytes())!=ALERT_SHA:
        raise ValueError("Frozen 15 alerts SHA mismatch")
    issue=json.loads(ISSUE.read_text(encoding="utf8"))
    names={r["country_id"]:r["country"] for r in issue["countries"]}
    sources={v:parse_counts(request(SOURCES[v]["url"],MAX_DOWNLOAD),v)
             for v in VERSION_ORDER}
    prior=json.loads(PRIOR.read_text(encoding="utf8"))
    results=study(sources,names,prior)
    payload=json.dumps(results,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    print("GEO2027_MATCHED_GLOBAL_ONLY_BEGIN")
    print(payload,end="")
    print("GEO2027_MATCHED_GLOBAL_ONLY_END",flush=True)
    if args.check_report and REPORT.read_bytes()!=payload.encode():
        raise ValueError("Matched global-only source replay differs from published bytes")


if __name__=="__main__":
    main()
