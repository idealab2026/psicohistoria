#!/usr/bin/env python3
"""Annual GED 2024 label drift across original GED25.1 and GED26.1 releases.

Retrospective measurement audit ONLY, not a forecast, 2026 target resolution,
an as-of reconstruction, or an independent validation after model selection.
Both original archive SHA-256 hashes are locked in the preceding #151 study.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

import audit_candidate_to_annual_ged as old

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / "data/candidate-to-annual-ged-resolution.json"
REPORT = ROOT / "data/ged2024-annual-vintage-drift.json"
EVENT_YEAR = 2024
LATER_RELEASE_YEAR = 2025


def strict_sha_pins(report, configured):
    if (set(configured) != {2024, 2025} or any(
        not isinstance(configured[y], str)
        or len(configured[y]) != 64
        or any(ch not in "0123456789abcdef" for ch in configured[y])
        for y in configured
    )):
        raise old.SourceError("Original GED ZIP SHA-256 pins missing or malformed")
    found = {}
    for item in report.get("source_details", []):
        if item.get("source_family") == "annual_GED":
            year = item.get("year")
            if year in found:
                raise old.SourceError("Duplicate frozen annual-source registry entry")
            found[year] = (item.get("url"), item.get("sha256"))
    if found != {
        y: (old.GED_URL[y], configured[y]) for y in (2024, 2025)
    }:
        raise old.SourceError("Earlier source registry disagrees with both frozen GED ZIPs")
    return True


def rename_confusion(m, first, second):
    # Keep the underlying deterministic confusion arithmetic, but avoid calling
    # either annual release "truth" and avoid the misleading generic key names.
    return {
        "n_at_risk": m["n_at_risk"],
        first + "_positive": m["candidate_positive"],
        second + "_positive": m["ged_positive"],
        "both_positive": m["both_positive"],
        "first_only": m["candidate_only"],
        "later_only": m["ged_only"],
        "both_negative": m["both_negative"],
        "disagreements": m["disagreements"],
        "first_only_country_ids": m["candidate_only_country_ids"],
        "later_only_country_ids": m["ged_only_country_ids"],
        "positive_overlap_share_of_first": m["candidate_positive_matching_ged_share"],
    }


def build_report(annual_fetcher=old.fetch_annual_zip, previous=None,
                 raw_universe=None, source_pins=None):
    # The previous frozen result is treated as a hard dependency. We do not
    # silently redefine its 196 country universe, risk sets, or Q3 labels.
    report_bytes = PREVIOUS.read_bytes() if previous is None else json.dumps(
        previous, sort_keys=True, ensure_ascii=False
    ).encode("utf8")
    previous_report = json.loads(report_bytes.decode("utf8"))
    if (previous_report.get("status") !=
            "RETROSPECTIVE_FINAL_VINTAGE_COMPARISON_NOT_PROSPECTIVE"
        or previous_report.get("annual_version_by_year") !=
            {"2024": "GED 25.1", "2025": "GED 26.1"}
        or previous_report.get("prospective_issued_probabilities") != 0
        or previous_report.get("cohorts_modified") != 0):
        raise old.SourceError("Original Candidate-to-annual study contract drifted")

    raw_universe = old.COUNTRY_SOURCE.read_bytes() if raw_universe is None else raw_universe
    names = dict(old.universe_from_bytes(raw_universe))
    if (len(names) != 196 or previous_report.get("n_countries") != 196
        or hashlib.sha256(raw_universe).hexdigest() !=
            previous_report.get("country_universe_sha256")):
        raise old.SourceError("Original cohort is not exactly the frozen 196-country universe")

    pins = dict(old.ANNUAL_ZIP_SHA if source_pins is None else source_pins)
    strict_sha_pins(previous_report, pins)

    orig = {}
    for row in previous_report.get("country_vectors", []):
        key = (row["year"], row["country_id"])
        if key in orig or key[1] not in names or row["country"] != names[key[1]]:
            raise old.SourceError("Duplicate, outside-universe or renamed original country vector")
        orig[key] = row
    if len(orig) != 392 or set(y for y, _ in orig) != {2024, 2025}:
        raise old.SourceError("Original study must contain 392 distinct country-year rows")

    parsed = {}
    sources = []
    selected = {}
    for release_year in (2024, 2025):
        url = old.GED_URL[release_year]
        raw = annual_fetcher(url)
        actual_sha = hashlib.sha256(raw).hexdigest()
        if actual_sha != pins[release_year]:
            raise old.SourceError(f"Official annual GED {release_year} ZIP has changed bytes")
        meta, events, indexed = old.read_annual(
            raw, EVENT_YEAR, set(names), release_year=release_year
        )
        parsed[release_year] = {h: old.rollup(events, EVENT_YEAR, h)
                                for h in (30, 90)}
        sources.append({"event_year": EVENT_YEAR,
                        "edition": "25.1" if release_year == 2024 else "26.1",
                        "release_year": release_year,
                        "url": url, "sha256": actual_sha, "bytes": len(raw),
                        "target_year_metadata": meta})
        selected[release_year] = indexed

    # For EVERY country and horizon verify the earlier annual release was read
    # identically to #151, before looking at the consequences of the new edition.
    for country in names:
        row = orig[(EVENT_YEAR, country)]
        for h, field in ((30, "ged_annual_may30_best"), (90, "ged_annual_90_best")):
            if parsed[2024][h][0][country] != row[field]:
                raise old.SourceError("GED25.1 replay disagrees with #151 frozen country vector")

    prior = defaultdict(int, {c: orig[(2024, c)]["candidate_q1_prior_best"] for c in names})
    grid = {}
    for threshold in old.THRESHOLDS:
        grid[str(threshold)] = {}
        for horizon in old.HORIZONS:
            first = parsed[2024][horizon][0]
            later = parsed[2025][horizon][0]
            q3_field = "candidate_q3_may30_best" if horizon == 30 else "candidate_q3_90_best"
            q3 = defaultdict(int, {c: orig[(2024, c)][q3_field] for c in names})
            m = old.paired_metrics(prior, q3, first, threshold, names)
            expected = previous_report["by_year_threshold_and_horizon"]["2024"][
                str(threshold)][str(horizon)]["q3_vs_annual"]
            if m != expected:
                raise old.SourceError("Prior Candidate-vs-GED confusion changed")
            f_to_l = old.paired_metrics(prior, first, later, threshold, names)
            q_to_l = old.paired_metrics(prior, q3, later, threshold, names)
            grid[str(threshold)][str(horizon)] = {
                "first_annual_vs_later_annual": rename_confusion(
                    f_to_l, "first_annual", "later_annual"
                ),
                "candidate_q3_vs_later_annual": rename_confusion(
                    q_to_l, "candidate_q3", "later_annual"
                ),
                "candidate_q3_vs_first_annual_previous_replayed": m,
            }

    # Country-level adjustments are an audit trail, not forecast country alerts.
    changes = []
    for country in sorted(names):
        old30, new30 = (parsed[y][30][0][country] for y in (2024, 2025))
        old90, new90 = (parsed[y][90][0][country] for y in (2024, 2025))
        if old30 != new30 or old90 != new90:
            row = orig[(EVENT_YEAR, country)]
            changes.append({
                "country_id": country, "country": names[country],
                "candidate_q1_prior_best": row["candidate_q1_prior_best"],
                "candidate_q3_may30_best": row["candidate_q3_may30_best"],
                "first_annual_may30_best": old30, "later_annual_may30_best": new30,
                "first_annual_90_best": old90, "later_annual_90_best": new90,
            })

    event_overlap = {}
    for horizon in (30, 90):
        earlier_by_country = parsed[2024][horizon][1]
        later_by_country = parsed[2025][horizon][1]
        event_overlap[str(horizon)] = old.matching_event_ids(
            earlier_by_country, selected[2025], later_by_country, names
        )
        # This helper's native keys refer to Q3 Candidate. Replace with
        # explicit earlier/later GED release labels.
        data = event_overlap[str(horizon)]
        event_overlap[str(horizon)] = {
            "first_annual_eligible_event_ids": data[
                "q3_candidate_eligible_may_event_ids"],
            "first_annual_ids_in_later_same_event_year": data[
                "candidate_id_in_annual_target_year_any_type_any_date"],
            "first_annual_ids_in_later_same_country_window": data[
                "candidate_id_in_annual_same_country_same_window"],
            "first_annual_ids_missing_in_later_exact_id": data[
                "not_matched_by_exact_id_in_annual_target_year"],
            "warning": "Exact IDs track coding revisions, not the existence of real-world incidents.",
        }

    return {
        "schema": "idealab.psico.ged2024_annual_vintage_drift.v1",
        "status": "RETROSPECTIVE_ANNUAL_VINTAGE_DRIFT_NOT_PROSPECTIVE",
        "design_fixed_date": "2026-11-20",
        "event_year": EVENT_YEAR,
        "editions": ["GED 25.1", "GED 26.1"],
        "original_previous_report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "source_archives_byte_pinned": True,
        "sources": sources,
        "country_universe_sha256": hashlib.sha256(raw_universe).hexdigest(),
        "n_countries": len(names),
        "thresholds": list(old.THRESHOLDS),
        "horizons": list(old.HORIZONS),
        "source_of_risk_set": "Candidate Q1 2024 from earlier frozen study",
        "risk_set_uses_later_ged": False,
        "by_threshold_and_horizon": grid,
        "country_annual_best_changes": changes,
        "first_to_later_annual_exact_event_id_overlap": event_overlap,
        "prospective_issued_probabilities": 0,
        "cohorts_modified": 0,
        "original_candidate_release_dates_verified": False,
        "interpretation": (
            "Post-selection sensitivity of the 2024 outcome definition, not a "
            "forecasting benchmark. Neither GED edition is ground truth. "
            "GED26.1 revises 2024 and is NOT an available 2024 as-of source. "
            "Missing exact IDs do not mean the historical events did not occur."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--summary", action="store_true")
    mode.add_argument("--print-report", action="store_true")
    mode.add_argument("--check-report", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = build_report()
        if args.print_report:
            print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        elif args.summary:
            summary = {
                "status": result["status"],
                "sources": [{"edition": x["edition"], "sha256": x["sha256"],
                             "target_year_rows": x["target_year_metadata"]["target_year_rows"]}
                            for x in result["sources"]],
                "changed_countries_total": len(result["country_annual_best_changes"]),
                "changes": result["country_annual_best_changes"],
                "threshold_grid": result["by_threshold_and_horizon"],
                "event_id_overlap": result["first_to_later_annual_exact_event_id_overlap"],
            }
            print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            frozen = json.loads(REPORT.read_text("utf8"))
            if frozen != result:
                raise old.SourceError("Frozen annual-vintage outcome revision report disagrees with official sources")
            print("OK: GED25.1/GED26.1 original SHA replay, original Candidate Q1 and full 196 checked")
    except (old.SourceError, OSError, KeyError, TypeError, ValueError, TimeoutError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
