#!/usr/bin/env python3
"""Exact ex-ante ACD2027 Brier sign frontier; NO observed 2027 outcomes.

Compare first-issued 32-country ACD primary p_global_recent5 to its separately
labelled *exploratory secondary* p_lag1_group. Never replace the primary,
interpret retrospective model selection as confirmatory, or pool GEO/NEWCONF.
"""
from __future__ import annotations

import argparse
import json
import math

import build_2027_prospective_registry as registry


def brier_difference(p_primary: float, p_secondary: float, y: int) -> float:
    """Brier(primary) - Brier(secondary), for one hypothetical binary label."""
    if (type(y) is not int or y not in (0, 1)
        or not all(type(x) in (float, int) and math.isfinite(x) and 0 < x < 1
                   for x in (p_primary, p_secondary))):
        raise ValueError("Expected probabilities strictly inside (0,1) and binary y")
    return (p_primary - y) ** 2 - (p_secondary - y) ** 2


def diagnose(docs: dict, manifests: dict) -> dict:
    """Require already SHA-checked originals; validate the derived 424-row registry."""
    registered = registry.make_registry(docs, manifests)
    if (registered["n_verified_future_2027_outcomes"] != 0
        or registered["observational_skill_demonstrated"] is not False
        or registered["n_unique_country_endpoint_rows"] != 424):
        raise ValueError("Unexpected future outcome or cohort count")
    rows = docs["acd"]["countries"]
    if len(rows) != 32:
        raise ValueError("Exactly 32 original 2025-active ACD countries required")
    for r in rows:
        if (r["conflict_present_in_origin_2025"] is not True
            or type(r["also_active_in_2024"]) is not bool):
            raise ValueError("ACD origin activity / previous-year provenance missing")
    # The FIRST issued ACD cohort has exactly one previously-inactive country.
    newly_active = [r for r in rows if not r["also_active_in_2024"]]
    continuously_active = [r for r in rows if r["also_active_in_2024"]]
    if len(newly_active) != 1 or len(continuously_active) != 31:
        raise ValueError("Expected fixed 1+31 origin activity stratification")
    pivot = newly_active[0]
    if pivot["country_id"] != 626:
        raise ValueError("Unexpected changed first-issued pivotal country ID")
    if (len({r["p_global_recent5"] for r in rows}) != 1
        or len({r["p_lag1_group"] for r in continuously_active}) != 1
        or pivot["p_lag1_group"] == continuously_active[0]["p_lag1_group"]):
        raise ValueError("First-issued ACD model stratification changed")
    ids = [r["country_id"] for r in rows]
    if len(set(ids)) != 32:
        raise ValueError("Duplicate original ACD GWNO")
    for r in rows:
        brier_difference(r["p_global_recent5"], r["p_lag1_group"], 0)
    country = next((r["country"] for r in docs["geo"]["countries"]
                    if r["country_id"] == pivot["country_id"]), None)
    if country != "South Sudan":
        raise ValueError("Pivotal institutional country crosswalk changed")

    p, q = pivot["p_global_recent5"], pivot["p_lag1_group"]
    other = continuously_active[0]
    p_other, q_other = other["p_global_recent5"], other["p_lag1_group"]
    pivot_zero = brier_difference(p, q, 0)
    pivot_one = brier_difference(p, q, 1)
    other_zero = brier_difference(p_other, q_other, 0)
    other_one = brier_difference(p_other, q_other, 1)
    n = len(rows)
    squared_gap_pivot = (p - q) ** 2
    squared_gap_other = (p_other - q_other) ** 2
    share = squared_gap_pivot / (squared_gap_pivot + 31 * squared_gap_other)
    all_cases = []
    for pivot_2027_record in (0, 1):
        for other_2027_absences in range(32):
            # An absence of an ACD record is NOT a claim of peace.
            total = (pivot_one if pivot_2027_record else pivot_zero)
            total += other_2027_absences * other_zero
            total += (31 - other_2027_absences) * other_one
            delta = total / n
            all_cases.append({
                "pivotal_country_2027_acd_present": bool(pivot_2027_record),
                "other_31_2027_acd_absences": other_2027_absences,
                "delta_brier_primary_minus_lag1": delta,
                "winner": "primary_global" if delta < -1e-15
                          else "exploratory_lag1" if delta > 1e-15 else "tie",
            })

    by_pivot = {}
    for status in (False, True):
        scenarios = [r for r in all_cases
                     if r["pivotal_country_2027_acd_present"] is status]
        primary_wins = [r["other_31_2027_acd_absences"] for r in scenarios
                        if r["winner"] == "primary_global"]
        lag_wins = [r["other_31_2027_acd_absences"] for r in scenarios
                    if r["winner"] == "exploratory_lag1"]
        ties = [r["other_31_2027_acd_absences"] for r in scenarios
                if r["winner"] == "tie"]
        by_pivot["present" if status else "absent"] = {
            "primary_wins_if_other_absences": primary_wins,
            "lag1_wins_if_other_absences": lag_wins,
            "ties_if_other_absences": ties,
            "minimum_delta": min(r["delta_brier_primary_minus_lag1"] for r in scenarios),
            "maximum_delta": max(r["delta_brier_primary_minus_lag1"] for r in scenarios),
        }
    if (by_pivot["absent"]["primary_wins_if_other_absences"]
        or by_pivot["present"]["primary_wins_if_other_absences"] != list(range(13))):
        raise ValueError("Original exact pivotal-country Brier frontier changed")
    return {
        "schema": "idealab.psico.acd2027_conditional_brier_frontier.v1",
        "research_status": "DERIVED_EX_ANTE_HYPOTHETICAL_NOT_ISSUED_FORECAST",
        "source_issued_acd_sha256": registry.EXPECTED["acd"][1],
        "source_first_public_acd_commit": registry.EXPECTED["acd"][2],
        "source_all_originals_sha_checked_by": "build_2027_prospective_registry.read_issued",
        "2027_outcomes_used": 0,
        "n_original_acd_country_questions": n,
        "original_acd_primary_model": "p_global_recent5",
        "exploratory_secondary_model": "p_lag1_group",
        "comparison_is_not_a_new_primary_metric": True,
        "pivotal_country_name": country,
        "pivotal_country_gwno": pivot["country_id"],
        "pivotal_country_active_2024": pivot["also_active_in_2024"],
        "pivotal_country_active_2025": pivot["conflict_present_in_origin_2025"],
        "pivotal_country_p_primary": p,
        "pivotal_country_p_secondary_lag1": q,
        "other_31_p_primary": p_other,
        "other_31_p_secondary_lag1": q_other,
        "share_of_sum_squared_probability_differences_due_to_pivotal_country": share,
        "pivotal_one_country_gap_component": squared_gap_pivot,
        "other_31_gap_component_total": 31 * squared_gap_other,
        "brier_sign_convention": "negative favors first-issued primary global; positive favors exploratory lag1",
        "conditional_frontier": by_pivot,
        "all_64_count_conditioned_hypothetical_scenarios": all_cases,
        "limitations": (
            "All outcomes are hypothetical and 2027 has not been observed. "
            "Counts of absent ACD records cannot be read as peace; revisions and "
            "missing countries must be handled only by original official future evaluators. "
            "No 2027 country outcomes, joint dependence, event-count distribution, "
            "skill claims or ex-post model selection are inferred."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true",
                        help="Print only the pivotal-country and frontier summary.")
    args = parser.parse_args()
    # This call authenticates every 2027 issued source byte against its fixed SHA.
    docs, manifests = registry.read_issued()
    report = diagnose(docs, manifests)
    if args.summary:
        report = {key: report[key] for key in (
            "schema", "source_issued_acd_sha256", "2027_outcomes_used",
            "pivotal_country_name", "pivotal_country_gwno",
            "pivotal_country_p_primary", "pivotal_country_p_secondary_lag1",
            "share_of_sum_squared_probability_differences_due_to_pivotal_country",
            "conditional_frontier", "limitations"
        )}
    print(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
