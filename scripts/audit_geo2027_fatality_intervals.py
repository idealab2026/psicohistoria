#!/usr/bin/env python3
"""Secondary UCDP low/best/high fatality-threshold sensitivity for frozen GEO2027.

No 2027 result exists in 2026. The primary prospective outcome remains the
first-complete operator-attested UCDP best-deaths >=25 definition. This
secondary analysis quantifies how low/high *measurement estimates* could
change the exact paired Brier comparison. Sharp extrema are algebraic only:
they are NOT confidence intervals, predictive uncertainty or IID inference.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
import io
import json
import math
from pathlib import Path

from resolve_geo2027_first_complete_official import (
    FIRST_POSSIBLE_RELEASE_DATE, _csv_bytes, _strict_nonnegative_int,
    evaluate_release, extract_complete_2027_labels,
    loaded_immutable_issues, preflight, review_provenance,
)

SCHEMA = "idealab.psico.geo2027_ucdp_fatality_estimate_sensitivity.v1"
READINESS = "NOT_READY_NO_VERIFIED_OFFICIAL_2027_RELEASE"
FIELD_SETS = (
    ("country_id", "year", "sb_total_deaths_low",
     "sb_total_deaths_best", "sb_total_deaths_high"),
    ("country_id_cy", "year_cy", "sb_total_deaths_low_cy",
     "sb_total_deaths_best_cy", "sb_total_deaths_high_cy"),
)
PAIR_P = "global_only_alpha1_p_active_2027"
PAIR_Q = "original_LOG1P2027_p_active_frozen"
THRESHOLD = 25
N = 196


def extract_official_intervals(raw, ids):
    """Use exact same source and universe as immutable primary best scorer."""
    best_labels, _ = extract_complete_2027_labels(raw, ids)
    reader = csv.DictReader(io.StringIO(_csv_bytes(raw).decode("utf-8-sig")))
    header = set(reader.fieldnames or ())
    formats = [fields for fields in FIELD_SETS if set(fields) <= header]
    if len(formats) != 1:
        raise ValueError("Missing or ambiguous UCDP low/best/high columns")
    idkey, yearkey, lowkey, bestkey, highkey = formats[0]
    fixed = set(ids)
    intervals = {}
    for record in reader:
        if record.get(None):
            raise ValueError("Unexpected extra UCDP CSV fields")
        cid = _strict_nonnegative_int(record.get(idkey), idkey)
        year = _strict_nonnegative_int(record.get(yearkey), yearkey)
        if year != 2027 or cid not in fixed:
            continue
        if cid in intervals:
            raise ValueError("Duplicate 2027 interval country")
        lo = _strict_nonnegative_int(record.get(lowkey), lowkey)
        mid = _strict_nonnegative_int(record.get(bestkey), bestkey)
        hi = _strict_nonnegative_int(record.get(highkey), highkey)
        # Official UCDP low/best/high names are not a guaranteed numeric
        # order: best can exceed high in aggregation/double-count adjustments.
        if int(mid >= THRESHOLD) != best_labels[cid]:
            raise AssertionError("Interval and primary best labels disagree")
        intervals[cid] = (lo, mid, hi)
    if set(intervals) != fixed or len(ids) != N or len(fixed) != N:
        raise ValueError("Must cover all 196 explicit first-issued countries")
    return intervals


def _delta_brier(p, q, y):
    return (p - y) ** 2 - (q - y) ** 2


def sensitivity(issue, intervals):
    """Sharp finite-cohort extrema under low/high thresholds, fixed p/q.

    Independently choosing the binary outcome where any of the THREE named
    estimates straddles 25 constructs algebraic extrema only. The country outcomes are correlated,
    and the upper/lower fatality values are NOT statistical confidence bounds.
    """
    rows = issue.get("countries")
    if not isinstance(rows, list) or len(rows) != N:
        raise ValueError("Missing 196 first-issued countries")
    ids = [r["country_id"] for r in rows]
    if len(set(ids)) != N or set(intervals) != set(ids):
        raise ValueError("Interval source differs from frozen country cohort")
    sums = {"low": 0.0, "best": 0.0, "high": 0.0,
            "sharp_lower": 0.0, "sharp_upper": 0.0}
    n_low = n_best = n_high = 0
    certain_0 = certain_1 = 0
    ambiguous = []
    unordered = []
    best_above_high = []
    low_above_best = []
    for row in rows:
        cid = row["country_id"]
        p = row[PAIR_P]
        q = row[PAIR_Q]
        if (type(p) not in (int, float) or type(q) not in (int, float) or
            not math.isfinite(p) or not math.isfinite(q) or
            not 0 < p < 1 or not 0 < q < 1):
            raise ValueError("Invalid frozen probability")
        triple = intervals[cid]
        if (not isinstance(triple, tuple) or len(triple) != 3 or
            any(type(x) is not int or x < 0 for x in triple)):
            raise ValueError("Malformed official fatality estimate interval")
        if not triple[0] <= triple[1] <= triple[2]:
            unordered.append(cid)
        if triple[1] > triple[2]:
            best_above_high.append(cid)
        if triple[0] > triple[1]:
            low_above_best.append(cid)
        low, best, high = (int(x >= THRESHOLD) for x in triple)
        n_low += low
        n_best += best
        n_high += high
        d0, d1 = _delta_brier(p, q, 0), _delta_brier(p, q, 1)
        sums["low"] += d1 if low else d0
        sums["best"] += d1 if best else d0
        sums["high"] += d1 if high else d0
        if low == best == high == 0:
            certain_0 += 1
            sums["sharp_lower"] += d0
            sums["sharp_upper"] += d0
        elif low == best == high == 1:
            certain_1 += 1
            sums["sharp_lower"] += d1
            sums["sharp_upper"] += d1
        else:
            ambiguous.append(cid)
            sums["sharp_lower"] += min(d0, d1)
            sums["sharp_upper"] += max(d0, d1)
    result = {
        "schema": SCHEMA,
        "fixed_2027_cohort_n": N,
        "threshold_state_based_deaths": THRESHOLD,
        "paired_difference_order": "global_only_alpha1_MINUS_original_LOG1P",
        "best_remains_original_primary_outcome": True,
        "certain_inactive_across_all_estimates_n": certain_0,
        "certain_active_across_all_estimates_n": certain_1,
        "nonmonotonic_official_triples_n": len(unordered),
        "nonmonotonic_official_GWNO": sorted(unordered),
        "best_exceeds_high_GWNO": sorted(best_above_high),
        "low_exceeds_best_GWNO": sorted(low_above_best),
        "threshold_ambiguous_countries_n": len(ambiguous),
        "threshold_ambiguous_GWNO": sorted(ambiguous),
        "low_scenario_active_n": n_low,
        "best_scenario_active_n": n_best,
        "high_scenario_active_n": n_high,
        "delta_brier_low": sums["low"] / N,
        "delta_brier_best": sums["best"] / N,
        "delta_brier_high": sums["high"] / N,
        "sharp_algebraic_lower_delta_brier": sums["sharp_lower"] / N,
        "sharp_algebraic_upper_delta_brier": sums["sharp_upper"] / N,
        "all_bounds_are_finite_cohort_and_not_confidence_intervals": True,
        "no_independence_or_probability_assigned_to_ambiguous_labels": True,
        "not_a_model_selection_or_forecast_reissue": True,
        "interpretation": (
            "UCDP named low/best/high are alternative estimates and can be "
            "numerically nonmonotonic (including best > high), NOT confidence "
            "limits. The algebraic envelope covers the binary labels of ALL "
            "THREE estimates. Only best is the preregistered primary outcome. "
            "No independence, feasible joint configuration, confidence "
            "level, or prospective skill is claimed."
        ),
    }
    if certain_0 + certain_1 + len(ambiguous) != N:
        raise AssertionError("Threshold partition is not disjoint")
    # Named estimates need not be ordered; never impose low <= best <= high.
    for scenario in ("low", "best", "high"):
        val = result["delta_brier_" + scenario]
        if not (result["sharp_algebraic_lower_delta_brier"] - 1e-12 <=
                val <= result["sharp_algebraic_upper_delta_brier"] + 1e-12):
            raise AssertionError("Measured scenario escaped sharp algebraic bounds")
    return result


def evaluate_intervals(raw, provenance, *, as_of_date=None):
    """Require all existing primary official-source gates before sensitivity."""
    primary = evaluate_release(raw, provenance, as_of_date)
    issue, ids = loaded_immutable_issues()
    intervals = extract_official_intervals(raw, ids)
    report = sensitivity(issue, intervals)
    official_primary = primary["score"]["predeclared_paired_differences"][
        "primary_Brier_globalonly_alpha1_minus_original_LOG1P"]
    if abs(report["delta_brier_best"] - official_primary) > 1e-11:
        raise AssertionError("Secondary best scenario changed primary Brier")
    return {
        "status": "SECONDARY_OPERATOR_ATTESTED_SOURCE_NOT_MACHINE_AUTHENTICATED",
        "2027_primary_score_unchanged": True,
        "primary_review": primary["source_review"],
        "source_coverage": primary["source_coverage"],
        "secondary_sensitivity": report,
        "primary_Brier_identity_reverified": True,
        "not_an_official_2027_result_until_real_verified_source": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path)
    parser.add_argument("--provenance", type=Path)
    args = parser.parse_args()
    if (args.source is None) != (args.provenance is None):
        parser.error("--source and --provenance must be supplied together")
    if args.source is None:
        state = preflight()
        if state["status"] != READINESS or state["n_official_2027_labels_resolved"] != 0:
            raise AssertionError("Premature 2027 evaluation")
        print(json.dumps({
            "schema": SCHEMA,
            "status": READINESS,
            "fixed_country_n": N,
            "low_best_high_outcomes_resolved": 0,
            "no_brier_or_confidence_interval": True,
            "first_complete_official_source_priority_requires_human_review": True,
            "new_probabilities_or_alerts_issued": False,
        }, indent=2, sort_keys=True))
        return
    if date.today() < FIRST_POSSIBLE_RELEASE_DATE:
        raise ValueError("Cannot evaluate 2027 low/best/high before 2028")
    raw = args.source.read_bytes()
    metadata = json.loads(args.provenance.read_text(encoding="utf-8"))
    report = evaluate_intervals(raw, metadata)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
