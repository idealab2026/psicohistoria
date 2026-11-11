#!/usr/bin/env python3
"""Ex-ante transition alert ranking in source-separated GEO-2027 historical holdouts.

A country inactive at origin is at risk of an entry (2027 target state 1);
an active origin is at risk of resolution (target state 0). Historical targets
are 2024/2025 in separately hash-pinned later editions, never 2027.
All metrics are retrospective, post-hoc exploratory, NOT proven prospective skill.

No country-level rows/identifiers/probabilities or future labels are emitted.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

from backtest_archived_country_vintages import SOURCES, fetch_archives
from diagnose_geo2027_transition_skill import make_holdout_rows, EXPECTED_ROWS, EXPECTED_EVENTS

SEED = 20261111
BOOTSTRAPS = 1000
ALERT_BUDGET_BY_ORIGIN_STATE = {0: 10, 1: 5}
MODELS = ("country_markov", "global_markov")
YEARS = (2024, 2025)
EXPECTED_EVENTS_BY_GROUP = {0: 8, 1: 10}
SOURCE_REPORT = Path("data/geo2027-transition-attribution-archival.json")


def score_for_transition(row, model):
    """Probability and outcome of CHANGING from the known origin state."""
    origin = row["origin_state"]
    if origin not in (0, 1) or row["outcome"] not in (0, 1):
        raise ValueError("Origin and observed target must be binary")
    if model not in MODELS:
        raise ValueError("Unregistered comparator")
    p = row["p_model" if model == "country_markov" else "p_global_markov"]
    if not isinstance(p, (float, int)) or not math.isfinite(p) or not 0 < p < 1:
        raise ValueError("Invalid frozen transition probability")
    return (p if origin == 0 else 1.0 - p), int(origin != row["outcome"])


def tie_group_average_precision(scored):
    """Tie-invariant right-endpoint step PR area; all tied cases enter together.

    This is NOT usual sequential AP with an arbitrary ordering of equal scores.
    It equals base prevalence for a constant-score classifier, unlike arbitrary
    country-ID tie-breaking.
    """
    n_positive = sum(y for p, y in scored)
    if not scored or n_positive == 0:
        return None
    ordering = sorted(scored, key=lambda x: -x[0])
    cum_positive = cum_n = 0
    area = 0.0
    cursor = 0
    while cursor < len(ordering):
        score = ordering[cursor][0]
        step_pos = step_n = 0
        while cursor < len(ordering) and ordering[cursor][0] == score:
            step_pos += ordering[cursor][1]
            step_n += 1
            cursor += 1
        cum_positive += step_pos
        cum_n += step_n
        area += (step_pos / n_positive) * (cum_positive / cum_n)
    return area


def auc_with_midrank_ties(scored):
    """ROC AUC = P(score_positive > score_negative) + .5 * tied pairs."""
    positives = sum(y for score, y in scored)
    negatives = len(scored) - positives
    if not positives or not negatives:
        return None
    ordered = sorted(scored, key=lambda x: x[0])
    below_negatives = 0
    wins = 0.0
    i = 0
    while i < len(ordered):
        current = ordered[i][0]
        pos = neg = 0
        while i < len(ordered) and ordered[i][0] == current:
            pos += ordered[i][1]
            neg += 1 - ordered[i][1]
            i += 1
        wins += pos * (below_negatives + 0.5 * neg)
        below_negatives += neg
    return wins / (positives * negatives)


def tie_safe_top_k(scored, k):
    """Worst/best attainable hits at fixed alert capacity with boundary ties.

    No alphabetical or arbitrary country ranking can certify one hit count.
    """
    n = len(scored)
    if not isinstance(k, int) or isinstance(k, bool) or k <= 0 or k > n:
        raise ValueError("Fixed alert capacity must be between 1 and n")
    ordered = sorted(scored, key=lambda x: -x[0])
    boundary_score = ordered[k - 1][0]
    strictly_above = [x for x in ordered if x[0] > boundary_score]
    tied = [x for x in ordered if x[0] == boundary_score]
    places = k - len(strictly_above)
    ties_positives = sum(y for _, y in tied)
    fixed_hits = sum(y for _, y in strictly_above)
    worst = fixed_hits + max(0, places - (len(tied) - ties_positives))
    best = fixed_hits + min(places, ties_positives)
    return {
        "budget": k,
        "hits_min": worst,
        "hits_max": best,
        "precision_min": worst / k,
        "precision_max": best / k,
        "precision_random_expectation": sum(y for _, y in scored) / n,
        "random_expected_hits": k * sum(y for _, y in scored) / n,
        "boundary_tie": len(tied) > places,
        "boundary_tied_candidates": len(tied),
        "remaining_slots_in_boundary": places,
    }


def cluster_brier_interval(rows, draws=BOOTSTRAPS):
    """Country cluster bootstrap, only as sensitivity; does NOT model common shocks."""
    by_country = defaultdict(list)
    for row in rows:
        by_country[row["country_id"]].append(row)
    keys = sorted(by_country)
    if len(keys) < 25 or draws < 100:
        raise ValueError("Insufficient country diversity or resamples")
    d = {}
    for country in keys:
        d[country] = (
            len(by_country[country]),
            sum((score_for_transition(r, "country_markov")[0] -
                 score_for_transition(r, "country_markov")[1]) ** 2 -
                (score_for_transition(r, "global_markov")[0] -
                 score_for_transition(r, "global_markov")[1]) ** 2
                for r in by_country[country])
        )
    rng = random.Random(SEED)
    samples = []
    for _ in range(draws):
        count = 0
        delta = 0.0
        for _ in keys:
            n, loss = d[keys[rng.randrange(len(keys))]]
            count += n
            delta += loss
        samples.append(delta / count)
    samples.sort()
    return [samples[int(.025 * (draws - 1))], samples[int(.975 * (draws - 1))]]


def metrics_by_group(rows, state, year=None):
    if state not in ALERT_BUDGET_BY_ORIGIN_STATE:
        raise ValueError("Unknown origin-state risk set")
    group = [r for r in rows if r["origin_state"] == state and
             (year is None or r["target_year"] == year)]
    budget = ALERT_BUDGET_BY_ORIGIN_STATE[state]
    if len(group) <= budget:
        raise ValueError("Risk set too small for the fixed alert capacity")
    observed_events = sum(score_for_transition(r, "country_markov")[1] for r in group)
    result = {
        "origin_state": state,
        "target_year": year,
        "question": "entry_0_to_1" if state == 0 else "resolution_1_to_0",
        "n": len(group),
        "transitions": observed_events,
        "event_rate": observed_events / len(group),
        "fixed_alert_capacity": budget,
        "models": {},
    }
    for model in MODELS:
        pairs = [score_for_transition(r, model) for r in group]
        brier = sum((p - y) ** 2 for p, y in pairs) / len(pairs)
        result["models"][model] = {
            "mean_predicted_transition_probability": sum(p for p, y in pairs) / len(pairs),
            "brier": brier,
            "roc_auc_midrank": auc_with_midrank_ties(pairs),
            "tie_group_pr_area": tie_group_average_precision(pairs),
            "top_k": tie_safe_top_k(pairs, budget),
        }
    result["brier_delta_country_minus_global"] = (
        result["models"]["country_markov"]["brier"] -
        result["models"]["global_markov"]["brier"]
    )
    if year is None:
        result["bootstrap_country_delta_brier_95pct"] = cluster_brier_interval(group)
    return result


def run(rows, metadata, prior_report):
    if len(rows) != EXPECTED_ROWS or sum(r["outcome"] for r in rows) != EXPECTED_EVENTS:
        raise ValueError("Original source-separated GEO historical holdout altered")
    if {r["target_year"] for r in rows} != set(YEARS):
        raise ValueError("Unexpected target-year set")
    if len({(r["country_id"], r["target_year"]) for r in rows}) != EXPECTED_ROWS:
        raise ValueError("Duplicated country-year risk rows")
    if set(metadata) != set(SOURCES) or any(
        metadata[v].get("sha256") != SOURCES[v]["sha256"] for v in SOURCES
    ):
        raise ValueError("Official source provenance mismatch")
    if prior_report.get("schema") != "idealab.psico.geo2027_transition_attribution_cross_release.v1":
        raise ValueError("Original state-change attribution report missing")
    groups = {str(s): metrics_by_group(rows, s) for s in (0, 1)}
    yearly = {str(y): {str(s): metrics_by_group(rows, s, y) for s in (0, 1)} for y in YEARS}
    if {s: groups[str(s)]["transitions"] for s in (0, 1)} != EXPECTED_EVENTS_BY_GROUP:
        raise ValueError("Source-backed 8/10 state transition totals changed")
    if any(groups[str(s)]["n"] != prior_report["ex_ante_origin_state"][str(s)]["n"]
           for s in (0, 1)):
        raise ValueError("Risk-set sizes disagree with pinned change report")
    if any(abs(groups[str(s)]["models"]["country_markov"]["brier"] -
               prior_report["ex_ante_origin_state"][str(s)]["brier"]["p_model"]) > 1e-12
           for s in (0, 1)):
        raise ValueError("Country Markov scores differ from original Brier")
    return {
        "schema": "idealab.psico.geo2027_transition_alerts_archival.v1",
        "status": "EXPLORATORY_SOURCE_SEPARATED_NOT_PROSPECTIVELY_VERIFIED",
        "question": "Can the issued GEO2027 country Markov score rank state transitions beyond the global Markov comparator?",
        "target": "GEO >=25 deaths state change (NOT newconf or onset2)",
        "source_sha256": {v: SOURCES[v]["sha256"] for v in sorted(SOURCES)},
        "fixed_origin_to_target_vintages": ["23.1→25.1 (2022→2024)", "24.1→26.1 (2023→2025)"],
        "risk_sets_are_known_at_origin": True,
        "posthoc_hypothesis_after_outcomes_inspected": True,
        "all_predictions_ex_post_not_issued_in_the_past": True,
        "tie_group_pr_area_not_standard_arbitrarily_tiebroken_average_precision": True,
        "alert_capacity_predefined": {"entry": 10, "resolution": 5},
        "per_origin_risk_group": groups,
        "per_target_year": yearly,
        "confidence_intervals_miss_shared_shocks": True,
        "prospective_2027_prediction_documents_modified": False,
        "prospective_2027_results_observed": 0,
        "interpretation_limits": ("Only 8 entries and 10 resolutions in two externally "
            "source-separated target years. Rankings can be dominated by ties. "
            "Fixed-budget top-k best/worst are descriptive, not future performance. "
            "Global Markov has no within-year country discrimination conditional "
            "on origin state. Retrospective releases are not independently "
            "timestamp-notarized. Never select a threshold ex post."),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-report")
    args = parser.parse_args()
    old = json.loads(SOURCE_REPORT.read_text(encoding="utf8"))
    vintages, metadata = fetch_archives()
    result = run(make_holdout_rows(vintages), metadata, old)
    content = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    print("GEO2027_TRANSITION_ALERTS_BEGIN")
    print(content, end="")
    print("GEO2027_TRANSITION_ALERTS_END")
    if args.check_report and Path(args.check_report).read_bytes() != content.encode("utf8"):
        raise ValueError("Fixed source-separated transition-alert report changed")


if __name__ == "__main__":
    main()
