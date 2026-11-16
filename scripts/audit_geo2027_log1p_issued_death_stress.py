#!/usr/bin/env python3
"""Exact finite-difference fragility of issued GEO2027 LOG1P, never reissued.

For each first-issued 2027 shadow probability, perturb ONLY the original
2025 country-year best deaths by ±{1,5,10}, clipped to preserve the 2025
binary origin state and nonnegative integer fatalities. Keep the original
SHA-frozen GEO H2 offset AND issued fitted logistic coefficients fixed.

Output: 196-country simultaneous rectangular sensitivity envelopes and
exact possible/mandatory top-K membership across independent counterfactual
perturbations. These are algebraic stress tests, NOT statistical intervals,
joint probabilities, data-revision likelihoods or new 2027 forecasts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from audit_geo2027_log1p_shadow_issue import (
    ISSUE, MANIFEST, ORIGINAL, audit as audit_issue,
    FROZEN_ISSUE_SHA256,
)
from experiment_geo2027_log1p_nested_h2 import predict, features
from prepare_geo2027_transition_alerts import SOURCE_SHA256

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo2027-log1p-issued-death-count-stress.json"
ALERTS=ROOT/"data/forecast-2027-transition-alerts.json"
ALERT_SHA="309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb"
MARGINS=(1,5,10)
ALERT_BUDGETS={0:10,1:5}
TOL=3e-11


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def death_range(deaths,state,margin):
    """Endpoint-complete finite perturbations CONDITIONAL on unchanged state."""
    if (type(deaths) is not int or deaths<0 or state not in (0,1)
        or type(margin) is not int or margin not in MARGINS
        or int(deaths>=25)!=state):
        raise ValueError("Invalid hypothetical fatality perturbation")
    lo=max(0 if state==0 else 25,deaths-margin)
    hi=min(24,deaths+margin) if state==0 else deaths+margin
    if not lo<=deaths<=hi or int(lo>=25)!=state or int(hi>=25)!=state:
        raise ValueError("Impossible state-preserving death interval")
    return lo,hi


def envelope(row,beta,margin):
    """Actual logistic monotone endpoints (not linearised approximation)."""
    death=row["origin_deaths_best_2025"]
    state=row["origin_binary_state_2025"]
    lo,hi=death_range(death,state,margin)
    p_original=row["original_2027_p_active"]
    p_issued=row["log1p_shadow_p_active_2027"]
    if type(p_original) not in (int,float) or not 0<p_original<1:
        raise ValueError("Missing original immutable baseline probability")
    exact_centre=predict({"p_original_binary":p_original,
                          "origin_deaths":death},beta)
    if abs(exact_centre-p_issued)>TOL:
        raise AssertionError("Logistic frozen-coefficient replay disagrees with issued 2027")
    lower_predict=predict({"p_original_binary":p_original,
                           "origin_deaths":lo},beta)
    upper_predict=predict({"p_original_binary":p_original,
                           "origin_deaths":hi},beta)
    minimum=min(p_issued,lower_predict,upper_predict)
    maximum=max(p_issued,lower_predict,upper_predict)
    norm=math.log(26) if state==0 else math.log(101)
    coefficient=beta[1] if state==0 else beta[2]
    logit_range=abs(coefficient*math.log1p(hi)/norm-
                    coefficient*math.log1p(lo)/norm)
    lip_bound=min(1.0,logit_range/4)
    if maximum-minimum>lip_bound+TOL:
        raise AssertionError("Exact logistic 1/4 Lipschitz bound violated")
    if not 0<minimum<=p_issued<=maximum<1:
        raise ValueError("Issued baseline not in counterfactual envelope")
    return {
        "low_deaths":lo,"high_deaths":hi,
        "low_p_active":round(minimum,12),
        "high_p_active":round(maximum,12),
        "max_abs_change_pp":round(
            100*max(p_issued-minimum,maximum-p_issued),9),
        "full_width_pp":round(100*(maximum-minimum),9),
        "certified_logistic_lipschitz_bound_width_pp":
            round(100*lip_bound,9),
        "source_revision_crossing_25_excluded_by_design":
            ((state==0 and death+margin>=25) or
             (state==1 and death-margin<25)),
    }


def outranks(score_a,id_a,score_b,id_b):
    """Deterministic exact ranking: higher score, then smaller GWNO ID."""
    return score_a>score_b or (score_a==score_b and id_a<id_b)


def certified_topk(risk_intervals,k):
    """Exact mandatory/possible membership for simultaneous independent ranges.

    i is possible iff at its optimistic score no >=k others outrank it at
    their pessimistic scores. i is mandatory iff at its pessimistic score
    <k others outrank it at their optimistic scores. All adversarial endpoint
    combinations are feasible independently under this rectangular scenario.
    """
    if not isinstance(risk_intervals,dict) or not k<len(risk_intervals):
        raise ValueError("Malformed ranking risk set")
    ids=sorted(risk_intervals)
    if len(set(ids))!=len(ids):
        raise ValueError("Duplicate ranking identities")
    for cid,x in risk_intervals.items():
        if (type(cid) is not int or cid<1 or not
            0<=x["lo"]<=x["centre"]<=x["hi"]<=1):
            raise ValueError("Malformed risk probability envelope")
    ranked=sorted(ids,key=lambda cid:(-risk_intervals[cid]["centre"],cid))
    issued_top=ranked[:k]
    possible=[];mandatory=[]
    for cid in ids:
        own=risk_intervals[cid]
        best_competition=sum(
            outranks(risk_intervals[other]["lo"],other,
                     own["hi"],cid)
            for other in ids if other!=cid)
        worst_competition=sum(
            outranks(risk_intervals[other]["hi"],other,
                     own["lo"],cid)
            for other in ids if other!=cid)
        if best_competition<k:
            possible.append(cid)
        if worst_competition<k:
            mandatory.append(cid)
    if (not set(mandatory).issubset(issued_top)
        or not set(issued_top).issubset(possible)
        or len(mandatory)>k or len(possible)<k):
        raise AssertionError("Impossible robust ranking sets")
    return {
        "k":k,"n":len(ids),
        "nominal_ordered":issued_top,
        "mandatory":mandatory,
        "possible":possible,
        "nominal_not_mandatory":[cid for cid in issued_top
                                 if cid not in mandatory],
        "possible_outside_nominal":[cid for cid in possible
                                    if cid not in issued_top],
        "mandatory_n":len(mandatory),
        "possible_n":len(possible),
        "nominal_members_not_certified_n":k-len(mandatory),
        "possible_alternatives_n":len(possible)-k,
        "all_nominal_members_certified_in_variant":len(mandatory)==k,
    }


def percentile(data,prob):
    if not data or not 0<prob<=1:
        raise ValueError("Bad percentile request")
    return sorted(data)[math.ceil(prob*len(data))-1]


def study(issue,original,alerts):
    rows=issue.get("countries")
    if not isinstance(rows,list) or len(rows)!=196:
        raise ValueError("Original issued LOG1P shadow must contain 196 countries")
    if (issue.get("status")!="ISSUED_PROSPECTIVE_UNRESOLVED"
        or issue.get("outcomes_2027_resolved")!=0
        or issue.get("n_countries")!=196
        or original.get("forecast_id")!="PSICO-GEO2027-STATEBASED25-V1"
        or original.get("target",{}).get("year")!=2027
        or alerts.get("2027_outcomes_resolved")!=0):
        raise ValueError("A source was changed or a future result was claimed")
    beta=issue["training"]["final_beta_log1p"]
    if (len(beta)!=3 or any(type(x) not in (int,float) or
         not math.isfinite(x) for x in beta)
        or issue["training"]["selected_ridge_lambda"]!=5
        or issue["training"]["final_train_targets"]!=[2012,2025]):
        raise ValueError("Issued coefficients and training contract changed")
    if len({r["country_id"] for r in rows})!=196:
        raise ValueError("Duplicate issued country risk")
    for state in (0,1):
        if (alerts["risk_groups"][str(state)]["budget"]!=ALERT_BUDGETS[state]
            or len(alerts["risk_groups"][str(state)]["selected_countries"])
               !=ALERT_BUDGETS[state]):
            raise ValueError("Original issued alert budget changed")

    strata={0:[r for r in rows if r["origin_binary_state_2025"]==0],
            1:[r for r in rows if r["origin_binary_state_2025"]==1]}
    if [len(strata[0]),len(strata[1])]!=[162,34]:
        raise ValueError("Issued 2025 origin risk distribution changed")
    country_bands={}
    stats=[]
    for margin in MARGINS:
        bounds={}
        for row in rows:
            bounds[row["country_id"]]=envelope(row,beta,margin)
            country_bands.setdefault(row["country_id"],{
                "country_id":row["country_id"],
                "country":row["country"],
                "origin_state":row["origin_binary_state_2025"],
                "issued_origin_deaths_best":row["origin_deaths_best_2025"],
                "original_issued_p_active_2027":row["original_2027_p_active"],
                "log1p_shadow_issued_p_active_2027":row["log1p_shadow_p_active_2027"],
                "bands":{},
            })["bands"][str(margin)]=bounds[row["country_id"]]
        risk_sets={}
        for state in (0,1):
            members=strata[state]
            interval={}
            for r in members:
                cid=r["country_id"]
                b=bounds[cid]
                centre=r["log1p_shadow_p_active_2027"]
                # The active risk group is ranked by odds of EXIT from >=25,
                # i.e. one minus the p(active). No reissue of original alerts.
                low=b["low_p_active"] if state==0 else round(1-b["high_p_active"],12)
                high=b["high_p_active"] if state==0 else round(1-b["low_p_active"],12)
                risk=centre if state==0 else round(1-centre,12)
                interval[cid]={"lo":low,"centre":risk,"hi":high}
            k=ALERT_BUDGETS[state]
            top=certified_topk(interval,k)
            orig_selected={
                r["country_id"] for r in
                alerts["risk_groups"][str(state)]["selected_countries"]
            }
            top.update({
                "group":"initially_inactive_entry" if state==0 else
                        "initially_active_resolution",
                "original_15_alerts_unchanged":True,
                "overlap_nominal_shadow_topk_with_original_issued_alerts":
                    len(set(top["nominal_ordered"])&orig_selected),
                "nominal_names":[{"country_id":cid,"country":country_bands[cid]["country"]}
                    for cid in top["nominal_ordered"]],
                "mandatory_names":[{"country_id":cid,"country":country_bands[cid]["country"]}
                    for cid in top["mandatory"]],
                "possible_alternative_names":[{"country_id":cid,"country":country_bands[cid]["country"]}
                    for cid in top["possible_outside_nominal"]],
            })
            risk_sets[str(state)]=top
        wid=[(bounds[r["country_id"]]["full_width_pp"],r["country_id"])
             for r in rows]
        ranked=sorted(wid,key=lambda z:(-z[0],z[1]))
        widths=[x[0] for x in wid]
        sum_lower=sum(bounds[r["country_id"]]["low_p_active"] for r in rows)
        sum_upper=sum(bounds[r["country_id"]]["high_p_active"] for r in rows)
        total=sum(r["log1p_shadow_p_active_2027"] for r in rows)
        if not sum_lower-TOL<=total<=sum_upper+TOL:
            raise AssertionError("Issued expected count not within scenario range")
        stats.append({
            "death_count_margin":margin,
            "country_n":196,
            "n_2025_origin_exact_zero_deaths":sum(r["origin_deaths_best_2025"]==0 for r in rows),
            "n_2025_origin_active":len(strata[1]),
            "n_deaths_changed_within_origin_state_allowed":sum(
                bounds[r["country_id"]]["low_deaths"]!=bounds[r["country_id"]]["high_deaths"]
                for r in rows),
            "n_at_risk_of_crossing_25_but_excluded":sum(
                bounds[r["country_id"]]["source_revision_crossing_25_excluded_by_design"]
                for r in rows),
            "mean_full_envelope_width_pp":round(sum(widths)/196,9),
            "median_full_envelope_width_pp":percentile(widths,.5),
            "p95_full_envelope_width_pp":percentile(widths,.95),
            "max_full_envelope_width_pp":max(widths),
            "n_countries_possible_shift_at_least_1pp":sum(
                bounds[r["country_id"]]["max_abs_change_pp"]>=1
                for r in rows),
            "n_countries_possible_shift_at_least_5pp":sum(
                bounds[r["country_id"]]["max_abs_change_pp"]>=5
                for r in rows),
            "issued_expected_active_count_sum":round(total,10),
            "counterfactual_expected_sum_low":round(sum_lower,10),
            "counterfactual_expected_sum_high":round(sum_upper,10),
            "simultaneous_deaths_perturbations_independent_by_assumption":True,
            "pinned_original_binary_GEO_unchanged_in_this_scenario":True,
            "risk_group_rank_certification":risk_sets,
            "top15_widest_prediction_envelopes":[
                {"country_id":cid,"country":country_bands[cid]["country"],
                 "width_pp":width,"original_deaths":country_bands[cid]["issued_origin_deaths_best"],
                 "issued_p":country_bands[cid]["log1p_shadow_issued_p_active_2027"],
                 "min_p":bounds[cid]["low_p_active"],
                 "max_p":bounds[cid]["high_p_active"]}
                for width,cid in ranked[:15]],
        })
    return {
        "schema":"idealab.psico.geo2027_issued_log1p_source_death_stress.v1",
        "status":"FIRST_ISSUED_PROBABILITY_SENSITIVITY_ONLY_NO_REISSUE",
        "first_issued_log1p_shadow_sha256":FROZEN_ISSUE_SHA256,
        "original_GEO_issued_sha256":SOURCE_SHA256,
        "original_15_alerts_issued_sha256":ALERT_SHA,
        "original_source":"UCDP OrganizedViolenceCY 26.1, observations through 2025",
        "target_year":2027,"origin_year":2025,"horizon_years":2,
        "n_issued_countries":196,
        "n_first_issued_alerts_changed":0,
        "any_first_issued_probability_changed":False,
        "future_2027_outcomes_resolved":0,
        "demonstrated_prospective_skill":False,
        "perturbation_absolute_death_margins":list(MARGINS),
        "keep_2025_state_binary_unchanged":True,
        "no_refitting_of_binary_GEO_or_log1p_coefficient":True,
        "scenario_bounds_are_not_confidence_intervals":True,
        "countrywise_independent_perturbations_not_empirically_justified":True,
        "perturbations_are_hypothetical_not_observed_ucdp_revision_probabilities":True,
        "ranking_mandatory_possible_assumes_independently_feasible_country_ranges":True,
        "baseline_active_count_original":round(sum(r["original_2027_p_active"] for r in rows),10),
        "baseline_active_count_shadow":round(sum(r["log1p_shadow_issued_p_active_2027"] for r in rows),10),
        "scenario_summaries":stats,
        "country_envelopes":[country_bands[r["country_id"]] for r in rows],
        "limitations":"These are hypothetical absolute best-fatality perturbations ±1,±5,±10 in 2025, clipped to preserve each country's state-based >=25 threshold and nonnegative counts. They are not estimates of source-revision distribution, probabilistic uncertainty, or achieved future skill. Original binary GEO probabilities and learned logistic coefficients stay fixed, even though real historical UCDP revisions may also affect older transition counts/coefficient fits. If 25-death threshold is crossed, these envelopes are NOT valid. TopK possible and mandatory membership only holds under independent simultaneous endpoint feasibility; actual data revisions can be correlated. No 2027 official outcomes were measured."
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report",action="store_true")
    args=parser.parse_args()
    issue_raw=ISSUE.read_bytes()
    original_raw=ORIGINAL.read_bytes()
    manifest_raw=MANIFEST.read_bytes()
    alerts_raw=ALERTS.read_bytes()
    audit_issue(issue_raw,manifest_raw,original_raw)
    if sha(alerts_raw)!=ALERT_SHA:
        raise ValueError("Original 15 issued GEO2027 alerts changed")
    report=study(json.loads(issue_raw),json.loads(original_raw),
                 json.loads(alerts_raw))
    payload=json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    print("GEO2027_ISSUED_LOG1P_DEATH_STRESS_BEGIN")
    print(payload,end="")
    print("GEO2027_ISSUED_LOG1P_DEATH_STRESS_END")
    if args.check_report and REPORT.read_bytes()!=payload.encode():
        raise ValueError("Pinned prospectively issued LOG1P stress differs from report")


if __name__=="__main__":
    main()
