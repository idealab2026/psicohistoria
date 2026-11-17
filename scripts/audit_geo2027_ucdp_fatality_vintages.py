#!/usr/bin/env python3
"""Source-pinned historical UCDP low/best/high threshold audit, not a forecast.

Separate within-edition 25-death estimate ambiguity from cross-edition
retrospective revision. Audit the same 196 GWNO countries as frozen GEO2027,
with 2011+ full country-year panels. No 2027 labels, future scoring, model
selection, new probability vector or independence assumption.
"""
from __future__ import annotations

import argparse
from itertools import combinations
import json
from pathlib import Path

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    FROZEN_SHA256, audit as audit_issued,
)
from audit_geo2027_log1p_shadow_issue import FROZEN_ISSUE_SHA256
from audit_geo2027_log1p_issued_death_stress import ALERT_SHA
from audit_geo2027_ucdp_zero_coding import (
    _xlsx_named_rows, _csv_named_rows, strict_int,
)
from backtest_archived_country_vintages import SOURCES
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD, VERSION_ORDER, EXPECTED_ROWS, parse_counts,
)
from prepare_geo2027_transition_alerts import SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data/geo2027-ucdp-fatality-vintage-intervals.json"
FIELDS = {
    "23.1": ("country_id_cy", "year_cy",
             "sb_total_deaths_low_cy", "sb_total_deaths_best_cy",
             "sb_total_deaths_high_cy"),
    "24.1": ("country_id_cy", "year_cy",
             "sb_total_deaths_low_cy", "sb_total_deaths_best_cy",
             "sb_total_deaths_high_cy"),
    "25.1": ("country_id_cy", "year_cy",
             "sb_total_deaths_low_cy", "sb_total_deaths_best_cy",
             "sb_total_deaths_high_cy"),
    "26.1": ("country_id", "year",
             "sb_total_deaths_low", "sb_total_deaths_best",
             "sb_total_deaths_high"),
}
THRESHOLD = 25
FULL_COHORT_START = 2011
RECENT_YEARS = (2022, 2023, 2024, 2025)
N = 196


def read_verified_intervals(raw, version):
    """Read EVERY source country-year and reconcile exact best deaths to SHA source."""
    if version not in VERSION_ORDER:
        raise ValueError("Unknown UCDP source version")
    verified = parse_counts(raw, version)  # SHA-256 and original row count/cutoff
    columns = FIELDS[version]
    iterator = (_xlsx_named_rows(raw, columns) if version == "23.1"
                else _csv_named_rows(raw, version, columns))
    out = {}
    cutoff = SOURCES[version]["last_year"]
    for row in iterator:
        cid, year, lo, mid, hi = (
            strict_int(value, field)
            for value, field in zip(row, columns)
        )
        if not (1 <= cid <= 2000 and 1989 <= year <= cutoff):
            raise ValueError("Unexpected original UCDP country or year")
        if not lo <= mid <= hi:
            raise ValueError("Official UCDP estimate order low <= best <= high failed")
        if mid != verified.get(cid, {}).get(year):
            raise ValueError("Low/best/high row cannot reconcile to verified best deaths")
        if (cid, year) in out:
            raise ValueError("Duplicate original UCDP country-year in interval table")
        out[(cid, year)] = (lo, mid, hi)
    if (len(out) != EXPECTED_ROWS[version] or
        len(out) != sum(len(history) for history in verified.values())):
        raise ValueError("UCDP interval source row-count mismatch")
    return out


def classify(triple):
    if (not isinstance(triple, tuple) or len(triple) != 3
        or any(type(x) is not int or x < 0 for x in triple)
        or not triple[0] <= triple[1] <= triple[2]):
        raise ValueError("Invalid country-year official estimate interval")
    lo, best, hi = triple
    return (int(lo >= THRESHOLD), int(best >= THRESHOLD),
            int(hi >= THRESHOLD))


def snapshot(panel, ids, year, *, show_ids=False):
    """Fail closed: never assume that an absent historical country is 0."""
    missing = sorted(cid for cid in ids if (cid, year) not in panel)
    if missing:
        raise ValueError(f"Incomplete {year} fixed196 country-year data: {missing}")
    labels = {cid: classify(panel[(cid, year)]) for cid in ids}
    low_n = sum(x[0] for x in labels.values())
    best_n = sum(x[1] for x in labels.values())
    high_n = sum(x[2] for x in labels.values())
    best_not_low = [cid for cid, (lo, b, hi) in labels.items() if lo == 0 and b == 1]
    high_not_best = [cid for cid, (lo, b, hi) in labels.items() if b == 0 and hi == 1]
    ambiguous = sorted(best_not_low + high_not_best)
    sure_no = sum(hi == 0 for lo, b, hi in labels.values())
    sure_yes = sum(lo == 1 for lo, b, hi in labels.values())
    obj = {
        "year": year,
        "explicit_first_issued_GWNO_n": N,
        "active_low_n": low_n,
        "active_best_n": best_n,
        "active_high_n": high_n,
        "ambiguous_threshold_n": len(ambiguous),
        "best_active_but_low_inactive_n": len(best_not_low),
        "best_inactive_but_high_active_n": len(high_not_best),
        "certain_inactive_across_low_high_n": sure_no,
        "certain_active_across_low_high_n": sure_yes,
    }
    if show_ids:
        obj.update({
            "ambiguous_GWNO": ambiguous,
            "best_active_but_low_inactive_GWNO": sorted(best_not_low),
            "best_inactive_but_high_active_GWNO": sorted(high_not_best),
        })
    if (not low_n <= best_n <= high_n or
        len(ambiguous) != high_n - low_n or
        sure_no + sure_yes + len(ambiguous) != N or
        len(best_not_low) != best_n - low_n or
        len(high_not_best) != high_n - best_n):
        raise AssertionError("Inconsistent source death-estimate threshold partition")
    return obj


def compare_editions(old, new, ids, year, oldv, newv):
    """Compare SAME historical year, not independent trial outcomes."""
    diffs = {"active_low": [], "active_best": [], "active_high": [],
             "threshold_ambiguous": []}
    state_before = {}
    state_after = {}
    for cid in ids:
        before = classify(old[(cid, year)])
        after = classify(new[(cid, year)])
        state_before[cid] = before
        state_after[cid] = after
        for i, name in enumerate(("active_low", "active_best", "active_high")):
            if before[i] != after[i]:
                diffs[name].append(cid)
        if (before[0] != before[2]) != (after[0] != after[2]):
            diffs["threshold_ambiguous"].append(cid)
    return {
        "year": year, "older_edition": oldv, "later_edition": newv,
        "same_196_GWNO_country_years_not_independent": True,
        "changed_low_indicator_n": len(diffs["active_low"]),
        "changed_best_indicator_n": len(diffs["active_best"]),
        "changed_high_indicator_n": len(diffs["active_high"]),
        "changed_ambiguous_indicator_n": len(diffs["threshold_ambiguous"]),
        "changed_best_indicator_GWNO": sorted(diffs["active_best"]),
        "changed_ambiguous_indicator_GWNO": sorted(diffs["threshold_ambiguous"]),
        "best_classification_differences_within_old_ambiguous_n": sum(
            cid in diffs["active_best"] and state_before[cid][0] != state_before[cid][2]
            for cid in ids),
        "best_classification_differences_within_new_ambiguous_n": sum(
            cid in diffs["active_best"] and state_after[cid][0] != state_after[cid][2]
            for cid in ids),
        "unambiguous_opposite_classification_n": sum(
            (b[0] == 1 and a[2] == 0) or (b[2] == 0 and a[0] == 1)
            for cid in ids
            for b, a in [(state_before[cid], state_after[cid])]),
    }


def study(panels, issue):
    if set(panels) != set(VERSION_ORDER):
        raise ValueError("Exactly four verified UCDP editions required")
    if issue.get("official_2027_outcomes_resolved") != 0:
        raise ValueError("GEO2027 first-issued forecast must remain unresolved")
    ids = sorted(row["country_id"] for row in issue["countries"])
    if len(ids) != N or len(set(ids)) != N:
        raise ValueError("Original 196 GWNO universe changed")
    for version in VERSION_ORDER:
        if SOURCES[version]["last_year"] > 2025:
            raise ValueError("Historical release includes post-2025 data")
        years = range(FULL_COHORT_START, SOURCES[version]["last_year"] + 1)
        if any((cid, year) not in panels[version] for cid in ids for year in years):
            raise ValueError("Fixed 196 country-year historical panel incomplete")
    snapshots = {}
    recent = {}
    for version in VERSION_ORDER:
        snapshots[version] = [
            snapshot(panels[version], ids, year)
            for year in range(FULL_COHORT_START, SOURCES[version]["last_year"] + 1)
        ]
        recent[version] = [
            snapshot(panels[version], ids, year, show_ids=True)
            for year in RECENT_YEARS if year <= SOURCES[version]["last_year"]
        ]
    cross = []
    for older, newer in combinations(VERSION_ORDER, 2):
        upto = min(SOURCES[older]["last_year"], SOURCES[newer]["last_year"])
        for year in RECENT_YEARS:
            if year <= upto:
                cross.append(compare_editions(
                    panels[older], panels[newer], ids, year, older, newer))
    return {
        "schema": "idealab.psico.geo2027_ucdp_fatality_interval_historical_vintages.v1",
        "status": "FOUR_OFFICIAL_ARCHIVED_EDITIONS_HISTORICAL_ONLY_NOT_A_PROSPECTIVE_OUTCOME",
        "original_issued_GEO2027_sha256": SOURCE_SHA256,
        "original_issued_LOG1P_sha256": FROZEN_ISSUE_SHA256,
        "global_only_matched_issued_sha256": FROZEN_SHA256,
        "original_fifteen_alerts_sha256": ALERT_SHA,
        "official_UCDP_source_sha256": {
            v: SOURCES[v]["sha256"] for v in VERSION_ORDER},
        "official_source_last_year": {
            v: SOURCES[v]["last_year"] for v in VERSION_ORDER},
        "fixed_first_issued_GWNO_n": N,
        "full_196_country_year_panel_starts": FULL_COHORT_START,
        "threshold_deaths": THRESHOLD,
        "low_best_high_are_not_confidence_limits": True,
        "retrospective_revisions_are_not_independent": True,
        "2027_official_outcomes_observed": 0,
        "no_2027_forecast_or_alert_changed": True,
        "no_historical_model_selection_or_future_Brier_scoring": True,
        "all_historical_year_edition_snapshots": snapshots,
        "recent_2022_2025_countrywise_snapshots": recent,
        "recent_all_edition_pair_comparisons": cross,
        "limitations": (
            "Threshold disagreement in low/best/high estimates measures "
            "operational sensitivity of the >=25 UCDP-coded target; it is not "
            "a statistical confidence level, an estimate of all real violence, "
            "or model performance. Revised country-year observations are not "
            "independent. Historic 2011+ risksets preserve the 196 first-issued "
            "GWNOs; no 2027 labels are observed or scored."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-report", action="store_true")
    parser.add_argument("--print-report", action="store_true")
    args = parser.parse_args()
    audit_issued(
        ISSUE.read_bytes(), MANIFEST.read_bytes(), ORIGINAL.read_bytes(),
        OLD_SHADOW.read_bytes(), OLD_MANIFEST.read_bytes(), ALERTS.read_bytes())
    raw = {v: request(SOURCES[v]["url"], MAX_DOWNLOAD) for v in VERSION_ORDER}
    panels = {v: read_verified_intervals(raw[v], v) for v in VERSION_ORDER}
    result = study(panels, json.loads(ISSUE.read_text(encoding="utf-8")))
    document = json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    if args.check_report and REPORT.read_bytes() != document.encode("utf-8"):
        raise ValueError("Historical low/best/high report is not source-byte-identical")
    if args.print_report:
        print("GEO2027_INTERVAL_VINTAGE_REPORT_BEGIN")
        print(document, end="")
        print("GEO2027_INTERVAL_VINTAGE_REPORT_END", flush=True)
    else:
        print("Official source hashes: verified 23.1, 24.1, 25.1, 26.1")
        print("Historical country-year snapshots:",
              sum(len(x) for x in result["all_historical_year_edition_snapshots"].values()))
        for edition, rows in result["recent_2022_2025_countrywise_snapshots"].items():
            for row in rows:
                print(edition, row["year"], "low/best/high:",
                      row["active_low_n"], row["active_best_n"],
                      row["active_high_n"], "ambiguous:", row["ambiguous_threshold_n"])
        print("Cross-edition recent-year comparisons:",
              len(result["recent_all_edition_pair_comparisons"]))


if __name__ == "__main__":
    main()
