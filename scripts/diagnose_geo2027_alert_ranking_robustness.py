#!/usr/bin/env python3
"""Exact adversarial robustness of *already first-issued* 2027 GEO transition alerts.

Assess fixed 2025 origin states and the two budgets (10 of 162 inactive,
5 of 34 active) under hypothetical coordinate-wise abs probability changes
<= epsilon. ALL country scores may vary independently within these bounds:
a worst-case scenario, NOT an empirical independence claim, confidence band,
real UCDP vintage, issued replacement ranking, source correction or skill test.

For each candidate i, its WORST rank obtains by placing i at its lower
feasible transition score and ALL other countries at their upper feasible
scores. Its BEST rank obtains with i at its upper feasible score and all
others at their lower feasible scores. Deterministic exact ties use numeric
GWNO ascending as in original issue. Thus:
 guaranteed i iff worst_rank_i <= k;
 possible i iff best_rank_i <= k.
These statements are SHARP for independently bounded coordinate perturbations
and hold for any actual joint dependence inside that rectangular set.

Historical UCDP H2 revision maxima are inputs only to nominate scenarios,
not estimates of future confidence or uncertainty bounds.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from audit_issued_geo2027_transition_alerts import audit
from prepare_geo2027_transition_alerts import (
    FORECAST_PATH,MANIFEST_PATH, SOURCE_SHA256, BUDGETS, ORIGIN_ACTIVE,
    ORIGIN_INACTIVE, sha, transition_score,
)

ROOT=Path(__file__).resolve().parents[1]
ALERTS=ROOT/"data/forecast-2027-transition-alerts.json"
ALERT_MANIFEST=ROOT/"data/forecast-2027-transition-alerts-manifest.json"
VINTAGE=ROOT/"data/geo2028-historical-forecast-vintage-drift.json"
REPORT=ROOT/"data/geo2027-issued-alert-perturbation-robustness.json"
ALERT_SHA="309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb"
EPS_FIXED=(0.0,0.002,0.005,0.01,0.025,0.10)
EXPECTED_PAIR_IDS=((2022,"23.1","24.1"),(2022,"23.1","25.1"),
                   (2022,"23.1","26.1"),(2023,"24.1","25.1"),
                   (2023,"24.1","26.1"),(2024,"25.1","26.1"))


def canonical(d):
    return (json.dumps(d,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode()


def rank_ahead(other_score,other_id,my_score,my_id):
    return other_score>my_score or other_score==my_score and other_id<my_id


def membership_sets(rows,k,epsilon):
    """Sharp membership-by-country certificates for a fixed top-k budget."""
    if (type(k) is not int or not isinstance(rows,list) or
        not 1<=k<len(rows) or
        type(epsilon) not in (float,int) or
        not math.isfinite(epsilon) or not 0<=epsilon<=1):
        raise ValueError("Top-k perturbation scenario malformed")
    ids=[r.get("country_id") for r in rows]
    if len(ids)!=len(set(ids)) or any(type(i) is not int or not 1<=i<=2000
                                      for i in ids):
        raise ValueError("GWNO group invalid or repeated")
    score={}
    lower={}
    upper={}
    for r in rows:
        cid=r["country_id"]
        p=r.get("score")
        if type(p) not in (float,int) or not math.isfinite(p) or not 0<p<1:
            raise ValueError("Invalid frozen transition score")
        score[cid]=p
        lower[cid]=max(0.0,p-epsilon)
        upper[cid]=min(1.0,p+epsilon)
    ordered=sorted(ids,key=lambda cid:(-score[cid],cid))
    selected=set(ordered[:k])
    guaranteed=[]
    possible=[]
    ranks={}
    for cid in ids:
        worst_rank=1+sum(rank_ahead(upper[other],other,lower[cid],cid)
                         for other in ids if other!=cid)
        best_rank=1+sum(rank_ahead(lower[other],other,upper[cid],cid)
                        for other in ids if other!=cid)
        if not 1<=best_rank<=worst_rank<=len(ids):
            raise ValueError("Impossible adversarial rank bounds")
        ranks[cid]=(best_rank,worst_rank)
        if worst_rank<=k:
            guaranteed.append(cid)
        if best_rank<=k:
            possible.append(cid)
    guaranteed=set(guaranteed)
    possible=set(possible)
    if not guaranteed.issubset(selected) or not selected.issubset(possible):
        raise ValueError("Perturbation certificates contradict frozen issued ranking")
    if not len(guaranteed)<=k<=len(possible):
        raise ValueError("Invalid finite risk budget")
    return {
        "epsilon_probability_absolute":epsilon,
        "epsilon_percentage_points":round(100*epsilon,9),
        "risk_group_n":len(ids),
        "budget_k":k,
        "issued_topk_country_ids":ordered[:k],
        "guaranteed_issued_topk_country_ids":sorted(guaranteed),
        "guaranteed_issued_topk_n":len(guaranteed),
        "issued_selected_members_that_may_exit":sorted(selected-guaranteed),
        "issued_selected_members_that_may_exit_n":len(selected-guaranteed),
        "outsiders_that_may_enter":sorted(possible-selected),
        "outsiders_that_may_enter_n":len(possible-selected),
        "potential_members_including_issued":len(possible),
        "selection_invariant_for_all_allowed_score_perturbations":
            guaranteed==selected,
        "sharp_individual_possible_and_guaranteed_membership":True,
        "total_replacements_not_assumed_jointly_independent":True,
        "rank_bounds_for_original_selected":[{
            "country_id":cid,
            "original_rank":i+1,
            "best_possible_rank":ranks[cid][0],
            "worst_possible_rank":ranks[cid][1],
            "guaranteed_member":cid in guaranteed,
        } for i,cid in enumerate(ordered[:k])],
        "not_confidence_probability_or_real_future_revision":True,
    }


def historical_scenario_scales(vintage):
    if (not isinstance(vintage,dict) or
        vintage.get("schema")!=
            "idealab.psico.geo_historical_fixed_origin_vintage_probability_drift.v1" or
        vintage.get("status")!=
            "OFFICIAL_SHA_PINNED_RETROSPECTIVE_VINTAGE_SENSITIVITY_NOT_2027_2028_OUTCOME" or
        vintage.get("fixed_origins")!=[2022,2023,2024] or
        vintage.get("horizons")!=[2,3] or
        vintage.get("n_comparisons_six_overlapping_source_pairs")!=6 or
        vintage.get("n_independent_prospective_tests_contributed")!=0 or
        vintage.get("prospective_2027_2028_skill_demonstrated") is not False or
        vintage.get("no_historical_2027_or_2028_target_outcomes_used") is not True or
        vintage.get("first_2025_origin_newer_27_1_available") is not False):
        raise ValueError("Expected frozen original historical UCDP vintage research")
    if vintage.get("source_versions_and_sha256")!={
        "23.1":"6c7dc09cc3173b21568a88d70862bee6a9199b2c6b217719698d9298ca8ecaff",
        "24.1":"00410bdb65023d1bc8799f47f188677965046bb73447ee33094782db30076260",
        "25.1":"564ce9a33652a5d7adef30f00ce6ac86411dedbcc10ef60ca9bdfbfeb9fea917",
        "26.1":"66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34",
    }:
        raise ValueError("Historical UCDP revision source provenance changed")
    folds=vintage.get("historical_comparisons")
    if type(folds) is not list or len(folds)!=6 or tuple(
        (f["origin_year_fixed"],f["original_edition"],f["later_revision_edition"])
        for f in folds)!=EXPECTED_PAIR_IDS:
        raise ValueError("Historical study no longer matches preregistered six pairs")
    h2=[]
    for fold in folds:
        h=fold.get("horizons")
        if type(h) is not list or len(h)!=2 or [
            x.get("horizon_years") for x in h]!=[2,3]:
            raise ValueError("Historical horizon cohorts changed")
        m=h[0]["max_absolute_probability_change"]
        p=h[0]["p95_absolute_probability_change"]
        if (any(type(v) not in (float,int) or not math.isfinite(v) or
                 not 0<=v<=1 for v in (m,p)) or
            p>m or h[0]["country_count"]!=196):
            raise ValueError("Invalid original official revision sensitivity")
        h2.append(h[0])
    largest=max(x["max_absolute_probability_change"] for x in h2)
    largest_p95=max(x["p95_absolute_probability_change"] for x in h2)
    if not (.05<largest<.06 and .002<largest_p95<.003 and
            vintage.get("horizon3_max_absolute_change_across_overlapping_pairs")>
            largest):
        raise ValueError("Historical source H2 envelope changed")
    return {
        "empirical_largest_H2_country_probability_change":largest,
        "empirical_largest_H2_within_pair_P95_country_change":largest_p95,
        "which_H2_pair_attained_largest":next({
            "origin":fold["origin_year_fixed"],
            "original_edition":fold["original_edition"],
            "later_edition":fold["later_revision_edition"],
        } for fold in folds if fold["horizons"][0]["max_absolute_probability_change"]==largest),
        "P95_and_max_are_historical_descriptives_not_future_probabilistic_bounds":True,
        "countrywise_rectangular_stress_does_not_assume_independent_real_revision_events":True,
    }


def build(raw_forecast,original_manifest,alert_raw,alert_manifest,generator,
          vintage):
    # Integrity check EXACT original issue, including all 196 frozen rows.
    d,_=__import__("prepare_geo2027_transition_alerts").verify_source(
        raw_forecast,original_manifest)
    if hashlib.sha256(alert_raw).hexdigest()!=ALERT_SHA:
        raise ValueError("First public 15-alert document SHA has changed")
    audit(alert_raw,alert_manifest,generator,raw_forecast,original_manifest)
    issued=json.loads(alert_raw)
    if (issued.get("cohort_id")!="PSICO-GEO2027-TRANSITION-ALERTS-V1" or
        issued.get("target_year")!=2027 or
        issued.get("2027_outcomes_resolved")!=0 or
        issued.get("demonstrated_prospective_skill") is not False):
        raise ValueError("Original issued future alert study changed")
    rows=d["countries"]
    if len(rows)!=196:
        raise ValueError("Original GEO source missing countries")
    scale=historical_scenario_scales(vintage)
    scenario=[("NO_PERTURBATION",0.0),
              ("TWO_TENTHS_PP",.002),
              ("HISTORICAL_H2_LARGEST_WITHIN_PAIR_P95",scale[
                  "empirical_largest_H2_within_pair_P95_country_change"]),
              ("HALF_PP",.005),
              ("ONE_PP",.01),("TWO_AND_HALF_PP",.025),
              ("HISTORICAL_H2_MAX_SINGLE_COUNTRY",scale[
                  "empirical_largest_H2_country_probability_change"]),
              ("TEN_PP",.10)]
    if len(set(name for name,_ in scenario))!=len(scenario) or any(
        e<0 or e>1 for _,e in scenario):
        raise ValueError("Invalid fixed stress scenario grid")
    groups={}
    for state,n in ((0,ORIGIN_INACTIVE),(1,ORIGIN_ACTIVE)):
        members=[r for r in rows if r["last_observed_state_2025"]==state]
        if len(members)!=n:
            raise ValueError("2025 frozen country risk group count changed")
        k=BUDGETS[state]
        scores=[{"country_id":r["country_id"],
                 "score":transition_score(r,state,"p_model"),
                 "country":r["country"]} for r in members]
        ordered=sorted(scores,key=lambda r:(-r["score"],r["country_id"]))
        selected_ids=[r["country_id"] for r in
                      issued["risk_groups"][str(state)]["selected_countries"]]
        if len(selected_ids)!=k or selected_ids!=[
            r["country_id"] for r in ordered[:k]]:
            raise ValueError("Issued 15-alert ranking contradicted by frozen GEO p")
        cutoff,first_excluded=ordered[k-1]["score"],ordered[k]["score"]
        if (cutoff<=first_excluded or
            abs(cutoff-issued["risk_groups"][str(state)]["alert_cutoff_score"])>1e-12 or
            abs(first_excluded-issued["risk_groups"][str(state)]["next_not_selected_score"])>1e-12):
            raise ValueError("Issued original alert cutoff gap drifted")
        results=[]
        for label,eps in scenario:
            cert=membership_sets(scores,k,eps)
            cert["scenario"]=label
            results.append(cert)
        if (results[0]["guaranteed_issued_topk_n"]!=k or
            not results[0]["selection_invariant_for_all_allowed_score_perturbations"]):
            raise ValueError("No-perturbation original alert ranking not recovered")
        if any(results[i+1]["guaranteed_issued_topk_n"]>
               results[i]["guaranteed_issued_topk_n"] for i in range(len(results)-1)
               if scenario[i+1][1]>=scenario[i][1]):
            raise ValueError("Guaranteed members can only decrease with stress magnitude")
        groups[str(state)]={
            "risk_group":"entry_0_to_1" if state==0 else "resolution_1_to_0",
            "origin_state_2025":state,
            "eligible_country_count":n,
            "issued_country_alert_budget":k,
            "issued_country_alert_ids":selected_ids,
            "last_issued_cutoff_transition_probability":cutoff,
            "first_excluded_transition_probability":first_excluded,
            "issued_boundary_gap_probability":round(cutoff-first_excluded,12),
            "issued_boundary_gap_percentage_points":round(
                100*(cutoff-first_excluded),9),
            "symmetric_uniform_change_first_can_affect_membership_if_around_boundary":
                round((cutoff-first_excluded)/2,12),
            "strictly_less_than_half_boundary_gap_guarantees_full_selection_unchanged":True,
            "perturbation_scenarios":results,
        }
    return {
        "schema":"idealab.psico.geo2027_issued_alert_adversarial_ranking_robustness.v1",
        "status":"ISSUED_ORIGINAL_15_ALERTS_UNCHANGED_ZERO_OFFICIAL_2027_OUTCOMES",
        "issued_alert_source_sha256":ALERT_SHA,
        "issued_alert_first_public_commit":alert_manifest["first_public_issue_commit"],
        "issued_original_GEO2027_sha256":SOURCE_SHA256,
        "origin_year":2025,"target_year":2027,"horizon_years":2,
        "n_origin_country_risk_set":196,
        "n_original_issued_alerts":15,
        "risk_group_budget_entry":10,
        "risk_group_budget_resolution":5,
        "n_new_alerts_or_reissued_frozen_probabilities":0,
        "n_certified_2027_outcome_labels":0,
        "prospective_predictive_skill_demonstrated":False,
        "perturbation_set":"Every fixed 2025-state country transition score may independently vary by <=epsilon; clamp to [0,1], tie-break by numeric GWNO.",
        "uncertainty_claim":"DETERMINISTIC_ADVERSARIAL_RECTANGLE_NOT_A_CONFIDENCE_INTERVAL",
        "historical_H2_editional_scale":scale,
        "scenario_order":[name for name,_ in scenario],
        "cohort_2025_fixed_both_stages":True,
        "joint_country_dependence_estimated":False,
        "real_source_revision_2027_observed":False,
        "historical_archive_forecast_sensitivity_is_not_a_future_bound":True,
        "original_forecasts_alert_budgets_and_rankings_modified":False,
        "countrywise_topk_robustness_claims_are_exact_for_the_artificial_rectangle":True,
        "group_results":groups,
        "limitations":(
            "Per-country +/-epsilon independent coordinate control is a "
            "worst-case mathematical perturbation SET, NOT a fitted empirical "
            "joint distribution, UCDP first-complete-release revision or "
            "uncertainty interval. Historical 23.1..26.1 H2 country-max and "
            "within-fold P95 merely NOMINATE two stress magnitudes; neither "
            "predicts a future 27.1 revision rate nor guarantees a true "
            "2027 alert selection. Top-k robustness is about RANKING "
            "membership only, not hit counts or prospective skill. Original "
            "risk groups are frozen by 2025 state, not redefined when later "
            "editions reclassify country-year origins. No 2027 outcome used."
        ),
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--check-report")
    args=p.parse_args()
    report=build(
        FORECAST_PATH.read_bytes(),
        json.loads(MANIFEST_PATH.read_text(encoding="utf8")),
        ALERTS.read_bytes(),
        json.loads(ALERT_MANIFEST.read_text(encoding="utf8")),
        (ROOT/"scripts/prepare_geo2027_transition_alerts.py").read_bytes(),
        json.loads(VINTAGE.read_text(encoding="utf8")),
    )
    raw=canonical(report)
    if args.check_report and REPORT.read_bytes()!=raw:
        raise ValueError("Source-authenticated issued GEO alert scenario report byte drift")
    print("GEO2027_ALERT_RANKING_STRESS_BEGIN")
    print(raw.decode(),end="")
    print("GEO2027_ALERT_RANKING_STRESS_END")


if __name__=="__main__":
    main()
