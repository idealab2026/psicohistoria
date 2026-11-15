#!/usr/bin/env python3
"""Preregistered ex ante GEO2028 2025->2026 origin-update attribution.

There is NO official 2026 annual UCDP 27.1 source as of this study
(2026-11-15): this module runs in CI ONLY on synthetic year-2026 data.

Three exact, ORDER-DEPENDENT algebraic components of a common country's
new 2026-origin/H2 p(2028) minus its first-issued 2025-origin/H3 p(2028):
  1. source vintage: reproduce 2025/H3 using revised 27.1 history <=2025;
  2. 2026 state surprise: condition frozen 2025 kernel on actual 2026 state,
     but do NOT refit model parameters, then forecast two years to 2028;
  3. model refit: fit the same Markov kernel with 2026 transitions included.

Telescoping is exact up to floating-point/12-digit issued roundoff.
These are NOT causal or independent statistical effects; vintage includes
revisions and population changes in global historical transition training.
Baseline's rolling five-year window is reported separately.

No 2028 outcome labels, no self-issue, no confidence interval or skill claim.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
import math
from pathlib import Path

import prepare_geo2028_origin2026 as origin
import prepare_geo2028_three_year as issued_2025
import forecast_2027_statebased as original_2027
from build_official_countries import read_zip
from evaluate_geo2028_first_complete_official import load_immutable_issue

ROOT=Path(__file__).resolve().parents[1]
SCHEMA="idealab.psico.geo2028_2025_to_2026_rollforward_attribution.v1"
METHOD="SEQUENTIAL_H3_2025_26_1_TO_H3_2025_27_1_TO_H2_OBS_2026_FROZEN_KERNEL_TO_H2_2026_REFIT"
PRIOR_SHA="fd5832c6896548b053202f2f84bd0f7cd4a75df44462fbd4f259b9d8d4c39bde"
MIN_COMMON=180
EPS=2e-10


def nstep(initial,q,steps):
    if type(initial) is not int or initial not in (0,1) or (
        type(steps) is not int or steps not in (1,2,3)):
        raise ValueError("Illegal state or horizon")
    if not (type(q) in (tuple,list) and len(q)==2 and
            all(type(x) in (float,int) and math.isfinite(x) and 0<x<1
                for x in q)):
        raise ValueError("Invalid probability kernel")
    p=float(initial)
    for _ in range(steps):
        p=q[0]+(q[1]-q[0])*p
    return p


def _fit_source_year(records,names,cutoff):
    """Independently reconstruct first-issued Markov transition q_s for each GWNO.

    Restrict a later annual source to <=2025 explicitly so re-estimation of
    2025/H3 CANNOT accidentally ingest any 2026 labels.
    """
    if cutoff not in (2025,2026) or not isinstance(records,dict):
        raise ValueError("Unsupported frozen source cutoff")
    clipped={
        cid:{y:s for y,s in h.items() if y<=cutoff}
        for cid,h in records.items() if any(y<=cutoff for y in h)
    }
    labels={cid:names[cid] for cid in clipped}
    rows,metadata=origin.estimate_from_origin(clipped,labels,origin=cutoff)
    transition=metadata["global_transition_counts"]
    lap=original_2027.LAPLACE
    shrink=original_2027.TRANSITION_PRIOR
    if lap!=1 or shrink!=20:
        raise ValueError("Original 2027 Markov estimator changed")
    global_q=[
        (transition[s][1]+lap)/(sum(transition[s])+2*lap) for s in (0,1)
    ]
    local={cid:[[0,0],[0,0]] for cid in clipped}
    for cid,h in clipped.items():
        for y in sorted(h):
            if y>1989 and y-1 in h:
                local[cid][h[y-1]][h[y]]+=1
    kernels={}
    ref={r["country_id"]:r for r in rows}
    for cid,baseline in ref.items():
        counts=local[cid]
        q=[(counts[s][1]+shrink*global_q[s])/
           (sum(counts[s])+shrink) for s in (0,1)]
        kernels[cid]=q
        if (abs(nstep(clipped[cid][cutoff],q,2)-baseline["p_model"])>1e-11 or
            abs(nstep(clipped[cid][cutoff],global_q,2)-
                baseline["p_global_markov"])>1e-11):
            raise ValueError("Counterfactual kernel differs from original H2 model")
    return kernels,ref,metadata


def _mean(rows,key):
    return sum(r[key] for r in rows)/len(rows) if rows else None


def decompose_for_source(records,names,original_2025_issued,candidate2026):
    """Pure deterministic algebra; original issuance must be authenticated by CLI.

    Given a hypothetical 27.1 panel, exposes what later changes *would mean*.
    Synthetic unit tests do NOT constitute a 2026-origin public forecast.
    """
    origin.validate_candidate(candidate2026)
    if (
        original_2025_issued.get("forecast_id")!=issued_2025.PROTOCOL_ID or
        original_2025_issued.get("origin",{}).get("year")!=2025 or
        original_2025_issued.get("origin",{}).get("official_sha256")!=
            issued_2025.SOURCE_SHA or
        original_2025_issued.get("target",{}).get("year")!=2028 or
        original_2025_issued.get("protocol",{}).get("horizon_years")!=3 or
        len(original_2025_issued.get("countries",[]))!=196 or
        original_2025_issued.get("2028_outcomes_resolved")!=0 or
        original_2025_issued.get(
            "prospective_predictive_skill_demonstrated") is not False or
        candidate2026["frozen_origin_2025_GEO2028_first_issue_sha256"]!=PRIOR_SHA or
        candidate2026["target_year"]!=2028 or
        candidate2026["source_provenance"]["first_release_independently_verified"]
             is not False or
        candidate2026["n_issued_country_questions"]!=0
    ):
        raise ValueError("Original issue/future source candidate not validated")
    if not records or set(records)!=set(names) or any(
        not history or max(history)>2026 for history in records.values()
    ):
        raise ValueError("Incomplete or contaminated official 27.1 source")
    origin_kernels,revised_2025,source_2025=_fit_source_year(
        records,names,2025)
    new_kernels,new_2026,source_2026=_fit_source_year(
        records,names,2026)
    candidate_rows=candidate2026["countries"]
    if (candidate_rows!=[new_2026[cid] for cid in sorted(new_2026)] or
        candidate2026["model_fit"]!=source_2026):
        raise ValueError("Unissued 2026 probabilities are not source reproducible")
    old_rows=original_2025_issued["countries"]
    original={r["country_id"]:r for r in old_rows}
    if len(original)!=196 or any(type(cid) is not int for cid in original):
        raise ValueError("2025 first-issued country IDs invalid")
    common=sorted(set(original)&set(revised_2025)&set(new_2026))
    if len(common)<MIN_COMMON:
        raise ValueError("Insufficient triple-matched countries to attribute")
    diffs=[]
    changed_2025=[]
    for cid in common:
        before=original[cid]
        q=origin_kernels[cid]
        h=records[cid]
        if any(y>2026 for y in h):
            raise ValueError("Post-2026 outcome cannot be used")
        old=before.get("p_model")
        old_state=before.get("last_observed_state_2025")
        new_state=h.get(2026)
        if (type(old) not in (float,int) or
            not 0<old<1 or type(old_state) is not int or
            old_state not in (0,1) or type(new_state) is not int or
            new_state not in (0,1)):
            raise ValueError("Original state or issued probability corrupted")
        if h[2025]!=old_state:
            changed_2025.append(cid)
        # A = first-issued forecast as of 26.1/2025, H3 => 2028.
        a=old
        # B = revised 27.1 source restricted to <=2025, H3 => 2028.
        b=nstep(h[2025],q,3)
        # C = 2026 observation replaces the *expected* 2026 state; q fixed.
        c=nstep(new_state,q,2)
        # D = same 2026-origin H2 model refitted through 2026, target=2028.
        d=new_2026[cid]["p_model"]
        # The Markov tower law gives B = E[H2(P2026)|state2025].
        pi_2026=nstep(h[2025],q,1)
        p2_0=nstep(0,q,2)
        p2_1=nstep(1,q,2)
        if abs(b-((1-pi_2026)*p2_0+pi_2026*p2_1))>1e-12:
            raise ValueError("Incorrect Markov conditional decomposition")
        vintage=b-a
        state_surprise=c-b
        refit=d-c
        total=d-a
        if (abs(vintage+state_surprise+refit-total)>1e-11 or
            abs(state_surprise-
                (new_state-pi_2026)*(p2_1-p2_0))>1e-11):
            raise ValueError("Telescoping source/observation/refit identity failed")
        if any(not 0<x<1 for x in (a,b,c,d)):
            raise ValueError("Unbounded counterfactual probability")
        diffs.append({
            "country_id":cid,
            "country_name_as_in_2026_source":names[cid],
            "2025_state_first_issued_source_26_1":old_state,
            "2025_state_revised_source_27_1":h[2025],
            "2026_state_source_27_1":new_state,
            "2026_state_expectation_under_2025_27_1_kernel":round(pi_2026,12),
            "A_p2028_first_issued_2025_h3":a,
            "B_p2028_revised_2025_h3":round(b,12),
            "C_p2028_observed_state2026_frozen_kernel_h2":round(c,12),
            "D_p2028_new_origin2026_refit_h2":d,
            "vintage_revision_plus_population_component":round(vintage,12),
            "2026_observed_state_surprise_component":round(state_surprise,12),
            "2026_model_refit_component":round(refit,12),
            "total_forecast_change_D_minus_A":round(total,12),
            "absolute_total_change":round(abs(total),12),
        })
    diffs.sort(key=lambda row:row["country_id"])
    for row in diffs:
        reconstructed=sum(row[key] for key in (
            "vintage_revision_plus_population_component",
            "2026_observed_state_surprise_component",
            "2026_model_refit_component"))
        if abs(reconstructed-row["total_forecast_change_D_minus_A"])>EPS:
            raise ValueError("Published rounded difference is not additive")
    # Baseline is NOT a state-conditional Markov model: its new-origin
    # difference contains rolling years, latest observation and population.
    old_base=next(iter(original.values()))["p_baseline_global_5y"]
    if any(abs(x["p_baseline_global_5y"]-old_base)>1e-12
           for x in original.values()):
        raise ValueError("Original 2025 global prevalence reference corrupted")
    b_base=source_2025["baseline_global_5y"]
    d_base=source_2026["baseline_global_5y"]
    return {
        "schema":SCHEMA,
        "status":"FUTURE_SOURCE_COUNTERFACTUAL_DIAGNOSTIC_CANDIDATE_NOT_ISSUED",
        "method":METHOD,
        "source_pin_is_independently_certified":False,
        "model_probabilities_origin2026_publicly_issued":False,
        "2028_official_outcomes_observed":0,
        "prospective_skill_demonstrated":False,
        "country_years_independent_replications":False,
        "decomposition_is_order_dependent_and_not_causal":True,
        "dataset":"UCDP OrganizedViolenceCY",
        "forecast_target_year":2028,
        "original_source_release":"26.1",
        "new_source_release":"27.1",
        "first_issued_GEO2028_2025_origin_sha256":PRIOR_SHA,
        "origin_2025_horizon_years":3,
        "origin_2026_horizon_years":2,
        "original_2025_origin_n":len(original),
        "revised_2025_origin_27_1_n":len(revised_2025),
        "new_2026_origin_27_1_n":len(new_2026),
        "fully_matched_country_count":len(common),
        "new_origin_only_country_ids":sorted(set(new_2026)-set(original)),
        "original_origin_no_longer_in_2026_cohort":sorted(
            set(original)-set(new_2026)),
        "triple_match_excluded_from_2025_revision_cohort":sorted(
            (set(original)&set(new_2026))-set(revised_2025)),
        "matched_2025_state_revisions":changed_2025,
        "matched_2025_state_revision_count":len(changed_2025),
        "mean_signed_total_forecast_probability_change":
            round(_mean(diffs,"total_forecast_change_D_minus_A"),12),
        "mean_absolute_total_forecast_probability_change":
            round(_mean(diffs,"absolute_total_change"),12),
        "mean_absolute_components":{
            k:round(_mean([{
                "abs":abs(r[k])} for r in diffs],"abs"),12)
            for k in ("vintage_revision_plus_population_component",
                      "2026_observed_state_surprise_component",
                      "2026_model_refit_component")
        },
        "original_global_baseline_2021_2025_26_1":old_base,
        "revised_global_baseline_2021_2025_27_1":b_base,
        "rolled_global_baseline_2022_2026_27_1":d_base,
        "baseline_vintage_population_component":round(b_base-old_base,12),
        "baseline_rolling_window_new_data_component":round(d_base-b_base,12),
        "baseline_total_change":round(d_base-old_base,12),
        "country_decomposition":diffs,
        "methodological_caveat":(
            "Exact algebra conditional on frozen model family; components "
            "depend on sequence of counterfactual interventions and cannot "
            "identify causal impact of source revisions or 2026 events. "
            "Vintage includes changes to global training country population. "
            "The 2026 state-surprise step is a Markov conditioning identity. "
            "Model refit includes 2026 transitions but not exogenous drivers. "
            "Different source vintages and same 2028 outcomes are NOT "
            "independent forecasting validation. No source independently "
            "attested, no 2026-origin public issue or 2028 outcome scored."
        ),
    }


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--official-zip",required=True)
    cli.add_argument("--source-pin-json",required=True)
    cli.add_argument("--output",required=True)
    args=cli.parse_args()
    dest=Path(args.output).resolve()
    if dest==ROOT or ROOT in dest.parents:
        raise ValueError("Unissued 2026-origin counterfactual cannot be saved inside repo")
    if not origin.FIRST_POSSIBLE_RELEASE<=date.today()<date(2028,1,1):
        raise ValueError("A complete official 2026 annual source is not yet eligible")
    original,_=load_immutable_issue()
    raw=Path(args.official_zip).read_bytes()
    pin=json.loads(Path(args.source_pin_json).read_text(encoding="utf8"))
    candidate=origin.build_candidate(raw,pin,original)
    origin.validate_candidate(candidate)
    records,names,_=origin.parse_annual_2026_csv(read_zip(raw))
    report=decompose_for_source(records,names,original,candidate)
    content=origin.canonical(report)
    if dest.exists():
        raise ValueError("Refuse silent overwrite of existing source-dependent analysis")
    dest.write_bytes(content)
    print("GEO2028_2026_ORIGIN_DECOMPOSITION_CANDIDATE_ONLY",
          json.dumps({
              "sha256":hashlib.sha256(content).hexdigest(),
              "source_release_independently_certified":False,
              "new_2026_origin_forecasts_publicly_issued":0,
              "n_original_geo2028_first_public_issues_untouched":196,
              "paired_country_counterfactuals":len(report["country_decomposition"]),
              "2028_labels_used":0,
          },sort_keys=True))


if __name__=="__main__":
    main()
