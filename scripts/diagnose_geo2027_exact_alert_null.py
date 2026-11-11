#!/usr/bin/env python3
"""Exact year-stratified random-ranking benchmark for frozen GEO transition alerts.

The archived historical source releases are hash-pinned. All quantities are
ex-post diagnostics, not independent confirmatory p-values or evidence that a
forecast for 2027 has succeeded. No individual country records are emitted.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from backtest_archived_country_vintages import fetch_archives
from diagnose_geo2027_transition_skill import make_holdout_rows
from evaluate_geo2027_transition_alerts import (
    ALERT_BUDGET_BY_ORIGIN_STATE, YEARS, auc_with_midrank_ties,
    run as original_study, score_for_transition, tie_safe_top_k,
)

ORIGINAL_REPORT = Path("data/geo2027-transition-alert-ranking-archival.json")
EXPECTED = {0: (321, 8), 1: (71, 10)}
MODELS = ("country_markov", "global_markov")


def hypergeom_pmf(population, events, slots):
    """X successes in slots drawn from population with events successes."""
    if any(isinstance(x, bool) or not isinstance(x, int) for x in
           (population, events, slots)) or not (0 <= events <= population and
           0 <= slots <= population and population > 0):
        raise ValueError("Invalid hypergeometric risk set")
    denom = math.comb(population, slots)
    lo = max(0, slots - (population - events))
    hi = min(events, slots)
    return {k: (math.comb(events, k) *
                math.comb(population - events, slots - k)) / denom
            for k in range(lo, hi + 1)}


def convolve(x, y):
    out = defaultdict(float)
    for a, pa in x.items():
        for b, pb in y.items():
            out[a + b] += pa * pb
    return dict(sorted(out.items()))


def quantile(pmf, q):
    if not 0 <= q <= 1:
        raise ValueError("Invalid quantile")
    acc = 0.0
    for hits, prob in sorted(pmf.items()):
        acc += prob
        if acc + 1e-12 >= q:
            return hits
    raise ValueError("Probability distribution not normalized")


def fixed_budget_null(rows, origin_state, year=None, model="country_markov"):
    """Exact random-ranking tail given events/year and slots selected/year.

    A pooled top-k can select unequal counts from 2024 and 2025. We condition
    on the resulting slots per target year, and independently randomize labels
    *within* origin-state/year cells, keeping each year's positive count fixed.
    Never break a boundary tie with country IDs to manufacture a p-value.
    """
    if origin_state not in EXPECTED or model not in MODELS or year not in (None, *YEARS):
        raise ValueError("Unregistered origin state, year or model")
    group = [row for row in rows if row["origin_state"] == origin_state and
             (year is None or row["target_year"] == year)]
    k = ALERT_BUDGET_BY_ORIGIN_STATE[origin_state]
    pairs = [score_for_transition(row, model) for row in group]
    if len(pairs) <= k:
        raise ValueError("Risk set unexpectedly too small")
    boundary = tie_safe_top_k(pairs, k)
    answer = {
        "risk_set_n": len(group),
        "observed_total_events": sum(y for _, y in pairs),
        "alert_capacity": k,
        "top_k_hits_min": boundary["hits_min"],
        "top_k_hits_max": boundary["hits_max"],
        "cutoff_tie": boundary["boundary_tie"],
    }
    if boundary["boundary_tie"]:
        # No unique alert set, no unique within-year allocation or tail area.
        return {**answer, "null_status": "UNDEFINED_BOUNDARY_TIE",
                "year_conditional_null": None}
    ranked = sorted(group, key=lambda row: -score_for_transition(row, model)[0])
    selected = ranked[:k]
    pmf = {0: 1.0}
    cells = []
    for target_year in YEARS:
        cell = [row for row in group if row["target_year"] == target_year]
        if not cell:
            continue
        n = len(cell)
        positives = sum(score_for_transition(row, model)[1] for row in cell)
        slots = sum(row["target_year"] == target_year for row in selected)
        cells.append({
            "year": target_year,
            "population": n,
            "events": positives,
            "selected_slots": slots,
            "expected_random_hits": slots * positives / n,
        })
        pmf = convolve(pmf, hypergeom_pmf(n, positives, slots))
    if len(cells) != (1 if year is not None else len(YEARS)):
        raise ValueError("Missing outcome-year cell")
    if abs(sum(pmf.values()) - 1) > 1e-10:
        raise ValueError("Exact conditional null did not normalize")
    hits = sum(score_for_transition(row, model)[1] for row in selected)
    if hits != boundary["hits_min"] or hits != boundary["hits_max"]:
        raise ValueError("Incorrect tie-safe observed hits")
    return {
        **answer, "null_status": "EXACT_YEAR_CONDITIONAL_EXCHANGEABILITY",
        "year_conditional_null": {
            "cells": cells,
            "observed_hits": hits,
            "expected_hits": sum(c["expected_random_hits"] for c in cells),
            "one_sided_probability_random_hits_at_least_observed":
                min(1.0, sum(p for h, p in pmf.items() if h >= hits)),
            "central_95pct_random_hit_range":
                [quantile(pmf, .025), quantile(pmf, .975)],
            "hit_count_probability_mass": {
                str(h): p for h, p in sorted(pmf.items())
            },
        },
    }


def within_year_auc(rows, state, model):
    """Pair-count-weighted AUC, excluding incomparable cross-year pairs."""
    numerator = denominator = 0.0
    cell_details = []
    for y in YEARS:
        cell = [score_for_transition(r, model) for r in rows
                if r["origin_state"] == state and r["target_year"] == y]
        positives = sum(target for _, target in cell)
        negatives = len(cell) - positives
        auc = auc_with_midrank_ties(cell)
        comparable_pairs = positives * negatives
        cell_details.append({
            "year": y, "n": len(cell), "events": positives,
            "comparable_positive_negative_pairs": comparable_pairs,
            "roc_auc_midrank": auc,
        })
        if auc is not None:
            numerator += auc * comparable_pairs
            denominator += comparable_pairs
    return {
        "auc_pair_weighted": numerator / denominator if denominator else None,
        "positive_negative_pairs": denominator,
        "by_year": cell_details,
    }


def analyze(rows, existing):
    if existing.get("schema") != "idealab.psico.geo2027_transition_alerts_archival.v1":
        raise ValueError("Previous committed alert evaluation schema changed")
    if len(rows) != 392 or sum(row["outcome"] for row in rows) != 69:
        raise ValueError("Original source-separated holdout changed")
    answer = {}
    for state in (0, 1):
        group = [row for row in rows if row["origin_state"] == state]
        events = sum(score_for_transition(r, "country_markov")[1] for r in group)
        if (len(group), events) != EXPECTED[state]:
            raise ValueError("Known-at-origin group or transition totals changed")
        key = str(state)
        ref = existing["per_origin_risk_group"][key]
        if (ref["n"], ref["transitions"]) != EXPECTED[state]:
            raise ValueError("Previously committed risk-set totals disagree")
        rank = {}
        for model in MODELS:
            fixed = fixed_budget_null(rows, state, model=model)
            original = ref["models"][model]["top_k"]
            if fixed["top_k_hits_min"] != original["hits_min"] or (
                fixed["top_k_hits_max"] != original["hits_max"]):
                raise ValueError("Original tie-safe alert hits do not reproduce")
            rank[model] = {
                "pooled_fixed_capacity": fixed,
                "per_year_fixed_capacity": {
                    str(y): fixed_budget_null(rows, state, y, model)
                    for y in YEARS
                },
                "within_year_auc": within_year_auc(rows, state, model),
            }
        answer[key] = {"risk_set_n": len(group), "transitions": events,
                       "models": rank}
    return {
        "schema": "idealab.psico.geo2027_exact_conditional_ranking_null.v1",
        "status": "POST_HOC_EXPLORATORY_DESCRIPTIVE_RANDOMIZATION",
        "source_prior_sha256": existing["source_sha256"],
        "source_separation": existing["fixed_origin_to_target_vintages"],
        "null_hypothesis": "exchangeable transition labels within each known origin-state and target-year cell, conditional on event counts and alert allocations by year",
        "candidate_ranking_chosen_after_external_labels_seen": True,
        "probabilities_are_not_confirmatory_p_values": True,
        "alert_budget_selection_not_optimized": True,
        "risk_sets": answer,
        "prospective_2027_forecasts_unchanged": True,
        "prospective_2027_outcomes_observed": 0,
        "limits": "Conditional random-ranking reference is an exact combinatorial benchmark, not independent predictive-skill significance: model family and questions explored after historical outcomes inspected. Only two years, rare transitions and non-independent countries; within-year AUC excludes cross-year prevalence effects. No country-level scores, labels or IDs are published.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-report")
    args = parser.parse_args()
    previous = json.loads(ORIGINAL_REPORT.read_text(encoding="utf8"))
    editions, metadata = fetch_archives()
    rows = make_holdout_rows(editions)
    # Independently reproduce every field of the prior source-separated report,
    # including the number of events and exact unrounded Brier, before analysis.
    if original_study(rows, metadata,
                      json.loads(Path("data/geo2027-transition-attribution-archival.json").read_text(
                          encoding="utf8"))) != previous:
        raise ValueError("Previously verified source-separation report changed")
    result = analyze(rows, previous)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    print("GEO2027_EXACT_CONDITIONAL_NULL_BEGIN")
    print(text, end="")
    print("GEO2027_EXACT_CONDITIONAL_NULL_END")
    if args.check_report and Path(args.check_report).read_bytes() != text.encode("utf8"):
        raise ValueError("Source-verified exact randomization report mismatch")


if __name__ == "__main__":
    main()
