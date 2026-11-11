#!/usr/bin/env python3
"""Audit actual change detection in GEO-2027's source-separated 2y historical holdout.

Ex-post retrospective diagnosis: original UCDP OrganizedViolenceCY 23.1
(origin 2022) -> 25.1 (outcome 2024), and 24.1 (origin 2023) -> 26.1
(outcome 2025). First-seen dates of archival bytes are NOT notarized.
No country names, codes, predictions, or outcomes are emitted as records.

The frozen prospective GEO-2027/NEWCONF-2027 issue is never read, updated,
recalibrated, evaluated, or presented as historically issued.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from backtest_archived_country_vintages import FOLDS, SOURCES, fetch_archives
from backtest_statebased_2027_spec import _annual_frame, _pairwise_uncertainty

EXPECTED_TARGETS = (2024, 2025)
EXPECTED_ROWS = 392
EXPECTED_EVENTS = 69
MIN_PER_FOLD = 196
SEED = 20261111
N_BOOT = 1000
PROBABILITY_COLUMNS = ("p_model", "p_global_markov", "p_baseline_global_5y")


def make_holdout_rows(vintages):
    """Origin-only fitting, later-vintage *target label* only."""
    rows = []
    if [(x["origin_release"], x["target_release"],
         x["origin_year"], x["target_year"]) for x in FOLDS] != [
         ("23.1", "25.1", 2022, 2024),
         ("24.1", "26.1", 2023, 2025)]:
        raise ValueError("Frozen historical holdout pairing changed")
    for spec in FOLDS:
        origin_year, target_year = spec["origin_year"], spec["target_year"]
        origin = vintages[spec["origin_release"]]
        target_vintage = vintages[spec["target_release"]]
        if not origin or max(max(v) for v in origin.values()) != origin_year:
            raise ValueError("Origin release chronology changed")
        if not target_vintage or max(max(v) for v in target_vintage.values()) != target_year:
            raise ValueError("Later source chronology changed")
        cohort = sorted(cid for cid, h in origin.items()
                        if origin_year in h and origin_year - 1 in h)
        if len(cohort) != MIN_PER_FOLD:
            raise ValueError("Origin country's full official risk set missing")
        for cid in cohort:
            if target_year not in target_vintage.get(cid, {}):
                raise ValueError("Unresolved later-vintage outcome must not become negative")
        # _annual_frame uses ONLY <= origin_year to fit the global/local
        # transition probabilities. Append only the later-release target label.
        synthetic = {cid: dict(h) for cid, h in origin.items()}
        for cid, h in synthetic.items():
            y = target_vintage.get(cid, {}).get(target_year)
            if y is not None:
                h[target_year] = y
        predictions, audit = _annual_frame(synthetic, origin_year)
        if len(predictions) != MIN_PER_FOLD or audit["unresolved"] != 0:
            raise ValueError("Original 196-country source-separated fold changed")
        for x in predictions:
            cid = x["country_id"]
            if cid not in cohort or x["outcome"] != target_vintage[cid][target_year]:
                raise ValueError("Target label/ID mismatch between separate releases")
            rows.append({
                **x, "origin_year": origin_year,
                "origin_state": origin[cid][origin_year],
                "origin_release": spec["origin_release"],
                "outcome_release": spec["target_release"],
            })
    return rows


def describe(rows):
    """All group membership determined by origin or target as labeled."""
    if not rows:
        return {"n": 0, "positives": 0, "transitions": 0}
    for r in rows:
        if r["origin_state"] not in (0, 1) or r["outcome"] not in (0, 1):
            raise ValueError("Origin/target must be binary")
        if any(not 0 < r[k] < 1 for k in PROBABILITY_COLUMNS):
            raise ValueError("Expected valid strictly interior probability")
    n = len(rows)
    brier = {p: sum((r[p] - r["outcome"]) ** 2 for r in rows) / n
             for p in PROBABILITY_COLUMNS}
    brier["hard_origin_persistence"] = sum(
        (r["origin_state"] - r["outcome"]) ** 2 for r in rows) / n
    return {
        "n": n,
        "positives": sum(r["outcome"] for r in rows),
        "origin_active": sum(r["origin_state"] for r in rows),
        "newly_active": sum(r["origin_state"] == 0 and r["outcome"] == 1 for r in rows),
        "resolved": sum(r["origin_state"] == 1 and r["outcome"] == 0 for r in rows),
        "transitions": sum(r["origin_state"] != r["outcome"] for r in rows),
        "brier": brier,
        "delta_model_minus_global_markov": brier["p_model"] - brier["p_global_markov"],
        "delta_model_minus_hard_persistence": brier["p_model"] - brier["hard_origin_persistence"],
        "mean_prediction_model": sum(r["p_model"] for r in rows) / n,
        "empirical_outcome_rate": sum(r["outcome"] for r in rows) / n,
    }


def summarize(rows, metadata):
    if len(rows) != EXPECTED_ROWS or sum(r["outcome"] for r in rows) != EXPECTED_EVENTS:
        raise ValueError("Original UCDP source-separated 392/69 historical holdout changed")
    if sorted({r["target_year"] for r in rows}) != list(EXPECTED_TARGETS):
        raise ValueError("Unexpected target year")
    if len({(r["country_id"], r["target_year"]) for r in rows}) != EXPECTED_ROWS:
        raise ValueError("Target country-years duplicated")
    if set(metadata) != set(SOURCES):
        raise ValueError("Historic source provenance incomplete")
    if any(metadata[v].get("sha256") != SOURCES[v]["sha256"] for v in SOURCES):
        raise ValueError("Official archive source digest mismatch")
    ex_ante = {str(s): [r for r in rows if r["origin_state"] == s] for s in (0, 1)}
    ex_post = {
        "changed": [r for r in rows if r["origin_state"] != r["outcome"]],
        "unchanged": [r for r in rows if r["origin_state"] == r["outcome"]],
    }
    return {
        "schema": "idealab.psico.geo2027_transition_attribution_cross_release.v1",
        "status": "RETROSPECTIVE_EX_POST_DIAGNOSTIC_NO_PROSPECTIVE_SKILL",
        "target": "UCDP OrganizedViolenceCY sb_total_deaths_best >=25 per GW country-year",
        "horizon_years": 2,
        "source_versions_and_sha256": {
            v: SOURCES[v]["sha256"] for v in sorted(SOURCES)
        },
        "frozen_comparison": "Original GEO2027 country two-step Markov vs global two-step Markov, global 5-year rate and hard persistence",
        "overall": describe(rows),
        "ex_ante_origin_state": {s: describe(ex_ante[s]) for s in sorted(ex_ante)},
        "ex_post_outcome_class_descriptive_only": {
            k: describe(ex_post[k]) for k in ("changed", "unchanged")
        },
        "by_target_year": {
            str(y): describe([r for r in rows if r["target_year"] == y])
            for y in EXPECTED_TARGETS
        },
        "country_bootstrap_95_model_minus_global_markov": {
            s: _pairwise_uncertainty(
                ex_ante[s], "p_global_markov", replications=N_BOOT, seed=SEED
            ) for s in sorted(ex_ante)
        },
        "source_release_dates_independently_notarized": False,
        "hypothesis_posthoc_after_both_targets_known": True,
        "historical_forecasts_actually_issued": False,
        "outcome_conditioned_slices_not_predictive_subgroups": True,
        "prospective_2027_forecast_modified": False,
        "prospective_2027_outcomes_resolved": 0,
        "limitations": ("Results are retrospective source-separated reconstructions, "
            "not historically time-stamped forecasts. Forecasting ANY conflict "
            "is easier than predicting a change; evaluation conditional on "
            "observed changes is retrospective only. Bootstrap by country "
            "does not handle shared global or year shocks. Do not infer "
            "NEWCONF or onset2 skill from state-based conflict incidence."),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-report")
    args = parser.parse_args()
    archives, metadata = fetch_archives()
    report = summarize(make_holdout_rows(archives), metadata)
    content = json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    print("GEO2027_TRANSITION_ATTRIBUTION_BEGIN")
    print(content, end="")
    print("GEO2027_TRANSITION_ATTRIBUTION_END")
    if args.check_report and Path(args.check_report).read_bytes() != content.encode("utf8"):
        raise ValueError("Source-separated transition attribution does not reproduce pinned report")


if __name__ == "__main__":
    main()
