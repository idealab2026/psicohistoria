#!/usr/bin/env python3
"""Retrospective source-vintage sensitivity of historical GEO top10/top5 lists.

Uses six SHA-pinned official UCDP 23.1--26.1 comparisons at identical
historical origins (2022--2024), NOT substitutions for issued 2027 alerts.
No 2027 results and no historical prediction issuance are claimed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from backtest_archived_country_vintages import SOURCES, fetch_archives
from decompose_geo2028_origin2026_update import nstep
from diagnose_geo2028_historical_forecast_vintage_drift import (
    PAIRS, VERSION_ORDER, _fit_at_origin, _verify_records,
)
from prepare_geo2027_transition_alerts import (
    FORECAST_PATH, SOURCE_SHA256,
)

ROOT = Path(__file__).resolve().parents[1]
ALERTS = ROOT / "data/forecast-2027-transition-alerts.json"
ALERT_SHA = "309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb"
REPORT = ROOT / "data/geo2027-historical-alert-vintage-overlap.json"
BUDGETS = {0: 10, 1: 5}
HORIZON = 2


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def admissible_topk(scores, k):
    """Exact mandatory/possible members under arbitrary boundary-tie order."""
    if len(scores) <= k or not all(0 < v < 1 for v in scores.values()):
        raise ValueError("Malformed top-k country probability population")
    order = sorted(scores, key=lambda cid: (-scores[cid], cid))
    cutoff = scores[order[k - 1]]
    higher = {cid for cid, score in scores.items() if score > cutoff}
    tied = {cid for cid, score in scores.items() if score == cutoff}
    seats = k - len(higher)
    mandatory = higher | (tied if seats == len(tied) else set())
    possible = higher | tied
    if not mandatory.issubset(order[:k]) or not set(order[:k]).issubset(possible):
        raise AssertionError("Top-k tie set inconsistent")
    return {
        "ordered": order[:k],
        "mandatory": mandatory,
        "possible": possible,
        "cutoff_probability": cutoff,
        "cutoff_tied_country_count": len(tied),
        "cutoff_tied_seats": seats,
        "boundary_selection_unique": len(possible) == k,
    }


def group_comparison(first, revised, state, names, *, k):
    """Fixed old-origin-state risk group; only historical kernel is revised."""
    ids = sorted(cid for cid, r in first.items() if r["origin_state"] == state)
    if len(ids) <= k:
        raise ValueError("Historical risk group too small")
    a = {cid: first[cid]["p_model_h2"] if state == 0
         else round(1 - first[cid]["p_model_h2"], 12) for cid in ids}
    # For a changed origin state, retain OLD source origin classification
    # and recompute the new kernel at that fixed state (source-only effect).
    b = {
        cid: round(nstep(state, revised[cid]["q_local"], HORIZON), 12)
        if state == 0 else
        round(1 - round(nstep(state, revised[cid]["q_local"], HORIZON), 12), 12)
        for cid in ids
    }
    old, new = admissible_topk(a, k), admissible_topk(b, k)
    gone = set(old["ordered"]) - set(new["ordered"])
    entered = set(new["ordered"]) - set(old["ordered"])
    definite_gone = old["mandatory"] - new["possible"]
    definite_entered = new["mandatory"] - old["possible"]
    changed_origin = [
        cid for cid in ids if first[cid]["origin_state"] != revised[cid]["origin_state"]
    ]
    def listing(country_ids):
        return [{"country_id": cid, "country": names.get(cid, str(cid))}
                for cid in sorted(country_ids)]
    return {
        "origin_state": state,
        "historical_original_eligible_n": len(ids),
        "budget": k,
        "fixed_original_origin_risk_set": True,
        "changed_origin_state_n": len(changed_origin),
        "changed_origin_state": listing(changed_origin),
        "old_topk": listing(old["ordered"]),
        "revised_topk": listing(new["ordered"]),
        "deterministic_tie_break": "numeric GWNO ascending",
        "deterministic_topk_retained_n": k - len(gone),
        "deterministic_swaps_n": len(gone),
        "deterministic_exited": listing(gone),
        "deterministic_entered": listing(entered),
        "definite_exits_independent_of_boundary_tiebreak": listing(definite_gone),
        "definite_entries_independent_of_boundary_tiebreak": listing(definite_entered),
        "definite_exits_n": len(definite_gone),
        "definite_entries_n": len(definite_entered),
        "old_cutoff": old["cutoff_probability"],
        "revised_cutoff": new["cutoff_probability"],
        "old_cutoff_tie_n": old["cutoff_tied_country_count"],
        "new_cutoff_tie_n": new["cutoff_tied_country_count"],
        "old_boundary_unique": old["boundary_selection_unique"],
        "new_boundary_unique": new["boundary_selection_unique"],
        "outcomes_observed_2027": 0,
    }


def study(vintages, metadata, names):
    _verify_records(vintages, metadata)
    if not names or len(names) != 196 or len(set(names)) != 196:
        raise ValueError("Expected frozen 196 GWNO country names")
    comparisons = []
    for year, old_v, new_v in PAIRS:
        first, oldinfo = _fit_at_origin(vintages[old_v], year)
        revised, newinfo = _fit_at_origin(
            vintages[new_v], year, fixed_cohort=list(first))
        if set(first) != set(names) or set(revised) != set(names):
            raise ValueError("Historical original risk set differs from issued GWNO universe")
        if oldinfo["last_training_year"] != year or newinfo["last_training_year"] != year:
            raise ValueError("Temporal data leakage from later source")
        groups = {
            str(state): group_comparison(first, revised, state, names, k=k)
            for state, k in BUDGETS.items()
        }
        comparisons.append({
            "fixed_origin_year": year,
            "original_UCDP_version": old_v,
            "revised_UCDP_version": new_v,
            "target_year_if_simulated": year + HORIZON,
            "original_source_cutoff": SOURCES[old_v]["last_year"],
            "later_edition_future_years_removed_before_fit": True,
            "groups": groups,
        })
    return {
        "schema": "idealab.psico.geo2027_historical_topk_vintage_overlap.v1",
        "status": "RETROSPECTIVE_RECONSTRUCTION_NOT_PROSPECTIVELY_ISSUED",
        "sources_sha256": {v: SOURCES[v]["sha256"] for v in VERSION_ORDER},
        "original_2027_forecast_sha256": SOURCE_SHA256,
        "original_2027_alert_sha256": ALERT_SHA,
        "matched_origins": [2022, 2023, 2024],
        "six_overlapping_edition_pairs_not_independent": True,
        "horizon_years": HORIZON,
        "k_initially_inactive": 10,
        "k_initially_active": 5,
        "paired_comparisons": comparisons,
        "comparisons_with_any_deterministic_topk_change": sum(
            any(g["deterministic_swaps_n"] > 0 for g in row["groups"].values())
            for row in comparisons),
        "comparisons_with_any_tie_independent_definite_entry": sum(
            any(g["definite_entries_n"] > 0 for g in row["groups"].values())
            for row in comparisons),
        "original_2025_to_2027_alerts_reissued": False,
        "current_2027_alert_change_directly_measured": False,
        "no_first_complete_post_2025_2027_origin_vintage": True,
        "n_historical_predictions_actually_issued": 0,
        "n_2027_outcomes_resolved": 0,
        "prospective_skill_demonstrated": False,
        "not_confidence_interval_or_future_revision_probability": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-report", action="store_true")
    args = parser.parse_args()
    raw = FORECAST_PATH.read_bytes()
    alerts = ALERTS.read_bytes()
    if sha(raw) != SOURCE_SHA256 or sha(alerts) != ALERT_SHA:
        raise ValueError("Original first-issued GEO2027 forecasts/alerts have changed")
    issued = json.loads(raw)
    if issued.get("forecast_id") != "PSICO-GEO2027-STATEBASED25-V1":
        raise ValueError("Wrong original model ID")
    names = {r["country_id"]: r["country"] for r in issued["countries"]}
    vintages, metadata = fetch_archives()
    report = study(vintages, metadata, names)
    payload = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.check_report:
        if not REPORT.exists() or REPORT.read_bytes() != payload.encode():
            raise ValueError("Historical vintage alert overlap report differs from SHA-pinned calculation")
    print("GEO2027_HISTORICAL_ALERT_VINTAGE_OVERLAP_BEGIN")
    print(payload, end="")
    print("GEO2027_HISTORICAL_ALERT_VINTAGE_OVERLAP_END")


if __name__ == "__main__":
    main()
