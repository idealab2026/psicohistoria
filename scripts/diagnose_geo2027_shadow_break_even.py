#!/usr/bin/env python3
"""Exact, dependence-free pre-2027 Brier break-even frontier: GEO vs shadow.

Compute every possible TOTAL number K of 2025->2027 country-state changes
(0..196) without observing or fabricating any 2027 outcomes. Conditional on K,
min/max paired Brier difference are attained by changing the K smallest/largest
country-specific Brier penalties. This is sharp combinatorial partial
identification over all K-subsets, NOT an empirically calibrated dependence
model, future probability, or proof of forecast skill.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from evaluate_geo2027_calibrated_shadow_official import (
    EXPECTED_SHADOW_FIRST_COMMIT, EXPECTED_SHADOW_SHA256, load_authenticated,
)
from prepare_geo2027_transition_alerts import SOURCE_SHA256, sha
from prepare_geo2027_calibrated_shadow import SHADOW_ID

COUNT = 196
TOLERANCE = 1e-11


def score_leverage(original, shadow):
    """An exact Brier difference affine in unknown transition indicator."""
    if (original.get("forecast_id") != "PSICO-GEO2027-STATEBASED25-V1"
        or shadow.get("forecast_id") != SHADOW_ID
        or len(original.get("countries", [])) != COUNT
        or len(shadow.get("countries", [])) != COUNT
        or shadow.get("2027_outcomes_resolved") != 0):
        raise ValueError("Expected frozen, unresolved GEO2027 model pair")
    old = original["countries"]
    new = shadow["countries"]
    if (len(set(r["country_id"] for r in old)) != COUNT
        or [r["country_id"] for r in old] !=
           [r["country_id"] for r in new]):
        raise ValueError("Original and shadow must pair exactly 196 IDs")
    rows = []
    for a, b in zip(old, new):
        state = a["last_observed_state_2025"]
        p = a["p_model"]
        q = b["shadow_p_active_2027"]
        if (type(state) is not int or state not in (0, 1)
            or type(p) not in (int, float) or type(q) not in (int, float)
            or not math.isfinite(p) or not math.isfinite(q)
            or not 0 < p < 1 or not 0 < q < 1
            or a["country_id"] != b["country_id"]
            or a["country"] != b["country"]
            or b["origin_state_2025"] != state
            or b["original_issued_p_active_2027"] != p):
            raise ValueError("Mismatch/invalid original vs issued shadow country")
        original_switch = p if state == 0 else 1-p
        shadow_switch = q if state == 0 else 1-q
        if not 0 < shadow_switch < original_switch < 1:
            raise ValueError("Shadow is not monotone shrinkage toward known 2025 state")
        persistence_delta = (q-state)**2-(p-state)**2
        transition_delta = (q-(1-state))**2-(p-(1-state))**2
        penalty = transition_delta-persistence_delta
        if (not persistence_delta < 0 < transition_delta
            or not penalty > 0
            or abs(penalty-2*abs(q-p)) > 2e-12):
            raise ValueError("Brier difference affine-decomposition invariant failed")
        rows.append({
            "country_id": a["country_id"],
            "country": a["country"],
            "origin_state_2025": state,
            "p_original_transition": original_switch,
            "p_shadow_transition": shadow_switch,
            "persistence_delta_sse": persistence_delta,
            "transition_penalty_sse": penalty,
        })
    if sum(r["origin_state_2025"] == 0 for r in rows) != 162:
        raise ValueError("Country original inactive risk-set size changed")
    if sum(r["origin_state_2025"] == 1 for r in rows) != 34:
        raise ValueError("Country original active risk-set size changed")
    return rows


def frontier(rows):
    """Sharp Brier bounds given EXACT total K changes, with no independence."""
    if not rows or len({x["country_id"] for x in rows}) != len(rows):
        raise ValueError("Full unique cohort is required for exact transition frontier")
    n=len(rows)
    if any(
        not math.isfinite(x["transition_penalty_sse"]) or
        x["transition_penalty_sse"] <= 0 or
        not math.isfinite(x["persistence_delta_sse"]) or
        x["persistence_delta_sse"] >= 0
        for x in rows
    ):
        raise ValueError("Invalid original/shadow transition leverage values")
    base = sum(x["persistence_delta_sse"] for x in rows)
    low=sorted(x["transition_penalty_sse"] for x in rows)
    high=list(reversed(low))
    prefix_low=[0.]
    prefix_high=[0.]
    for i in range(n):
        prefix_low.append(prefix_low[-1]+low[i])
        prefix_high.append(prefix_high[-1]+high[i])
    counts=[]
    for k in range(n+1):
        lower=base+prefix_low[k]
        upper=base+prefix_high[k]
        if lower>upper+TOLERANCE:
            raise ValueError("Sharp frontier inverted")
        if upper < -TOLERANCE:
            decision="SHADOW_BEATS_ORIGINAL_FOR_ANY_K_COUNTRIES"
        elif lower > TOLERANCE:
            decision="ORIGINAL_BEATS_SHADOW_FOR_ANY_K_COUNTRIES"
        else:
            decision="IDENTITY_OF_TRANSITIONING_COUNTRIES_MATTERS_OR_TIE_POSSIBLE"
        counts.append({
            "n_actual_transitions":k,
            "best_case_shadow_delta_brier":lower/n,
            "worst_case_shadow_delta_brier":upper/n,
            "classification":decision,
        })
    first_possible=next((x["n_actual_transitions"] for x in counts
                         if x["worst_case_shadow_delta_brier"]>TOLERANCE),None)
    first_guaranteed=next((x["n_actual_transitions"] for x in counts
                           if x["best_case_shadow_delta_brier"]>TOLERANCE),None)
    if first_possible is None or first_guaranteed is None:
        raise ValueError("Expected a valid break-even with both potential outcomes")
    if not 0 < first_possible <= first_guaranteed <= n:
        raise ValueError("Break-even thresholds cannot be interpreted")
    return {
        "n":n,
        "all_persist_delta_brier_shadow_minus_original":base/n,
        "all_transition_delta_brier_shadow_minus_original":
            (base+prefix_high[-1])/n,
        "fewest_transitions_original_can_beat_shadow":first_possible,
        "fewest_transitions_original_must_beat_shadow":first_guaranteed,
        "sharp_bounds_by_total_number_of_transitions":counts,
    }


def diagnose(original, shadow, manifest):
    if (manifest.get("first_public_shadow_commit") !=
        EXPECTED_SHADOW_FIRST_COMMIT
        or manifest.get("shadow_forecast_sha256") != EXPECTED_SHADOW_SHA256
        or manifest.get("original_forecast_sha256") != SOURCE_SHA256
        or manifest.get("2027_outcomes_resolved") != 0):
        raise ValueError("Original 2027 shadow issuance changed")
    rows=score_leverage(original,shadow)
    bounds=frontier(rows)
    groups={str(state):frontier([r for r in rows if r["origin_state_2025"]==state])
            for state in (0,1)}
    total_squared=sum((r["p_original_transition"]-
                       r["p_shadow_transition"])**2 for r in rows)
    orig_expected=sum(
        r["persistence_delta_sse"]+
        r["transition_penalty_sse"]*r["p_original_transition"]
        for r in rows
    )
    shadow_expected=sum(
        r["persistence_delta_sse"]+
        r["transition_penalty_sse"]*r["p_shadow_transition"]
        for r in rows
    )
    if (abs(orig_expected-total_squared)>TOLERANCE
        or abs(shadow_expected+total_squared)>TOLERANCE):
        raise ValueError("Strict proper Brier score identity failed")
    top=sorted(rows,key=lambda x:(-x["transition_penalty_sse"],x["country_id"]))[:10]
    return {
        "schema":"idealab.psico.geo2027_shadow_break_even.v1",
        "status":"PRE_OUTCOME_EXACT_COMBINATORIAL_SENSITIVITY_NOT_EVIDENCE_OF_SKILL",
        "original_issued_forecast_sha256":SOURCE_SHA256,
        "shadow_issued_forecast_sha256":EXPECTED_SHADOW_SHA256,
        "first_public_shadow_commit":EXPECTED_SHADOW_FIRST_COMMIT,
        "target_year":2027,
        "2027_outcomes_observed":0,
        "original_forecast_or_shadow_modified":False,
        "all_196_country_scores_required_for_future_actual_evaluation":True,
        "observed_2027_scenarios_used":False,
        "target_definition":"Change in state-based UCDP OrganizedViolenceCY 25+ deaths threshold from 2025 status to 2027 status; not war onset or negotiated peace",
        "exact_math":(
            "For country i with original p_i, shadow q_i, known state s_i, "
            "define Delta_i(Y)=(q_i-Y)^2-(p_i-Y)^2. With binary transition "
            "T_i=1[Y_i != s_i], Delta_i=base_i+T_i*w_i, "
            "base_i=(q_i-s_i)^2-(p_i-s_i)^2<0, w_i=2*abs(q_i-p_i)>0. "
            "For K changes among n fixed countries, sharp min/max of "
            "SUM Delta_i / n use K smallest/largest w_i, respectively."
        ),
        "total_196_country_exact_frontier":bounds,
        "by_known_2025_origin_state":groups,
        "expected_paired_brier_delta_if_original_probabilities_are_true":
            orig_expected/len(rows),
        "expected_paired_brier_delta_if_shadow_probabilities_are_true":
            shadow_expected/len(rows),
        "per_country_squared_forecast_differences_mean":
            total_squared/len(rows),
        "highest_brier_leverage_not_highest_probability_of_transition":[{
            "country_id":x["country_id"],
            "country":x["country"],
            "2025_origin_state":x["origin_state_2025"],
            "penalty_to_shadow_brier_if_country_transitions":
                x["transition_penalty_sse"]/len(rows),
            "original_p_transition":x["p_original_transition"],
            "shadow_p_transition":x["p_shadow_transition"],
        } for x in top],
        "limitations":(
            "SHARP conditional on an arbitrary K-subset: no geopolitical "
            "feasibility constraint, independence assumption, estimated "
            "correlation or probability assigned to K or to any switching "
            "combination. All 2027 labels remain unknown. Probability-weighted "
            "score expectation under the original and under the shadow "
            "are mutually exclusive hypothetical data-generating assumptions. "
            "The secondary shadow was chosen post hoc after looking at "
            "historical 2024/25 labels, even though its 2027 outcomes are future."
        ),
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--check-report")
    args=p.parse_args()
    original,shadow,manifest=load_authenticated()
    report=diagnose(original,shadow,manifest)
    rendered=json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    print("GEO2027_SHADOW_BREAK_EVEN_BEGIN")
    print(rendered,end="")
    print("GEO2027_SHADOW_BREAK_EVEN_END")
    if args.check_report and Path(args.check_report).read_bytes()!=rendered.encode("utf8"):
        raise ValueError("Frozen original-shadow combinatorial break-even report differs")


if __name__=="__main__":
    main()
