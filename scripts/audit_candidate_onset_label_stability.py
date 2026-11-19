#!/usr/bin/env python3
"""Candidate May-label revision and tie-aware onset analysis; retrospective ONLY.

Protocol fixed before running this experiment. Compares Q2 vs Q3 recordings
of identical May events; 2026 alert probabilities remain frozen from #146.
A historical Candidate vintage URL does NOT prove original publication date.
"""
import argparse
from collections import defaultdict
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import sys

from check_ucdp_candidate_asof import SourceError
from audit_candidate_q2_q3_vintages import get_source, url_for
from experiment_candidate_30_90_holdout import (
    YEARS, archive_url, extract_state_based, universe_from_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "data/candidate-30-90-baseline-holdout.json"
REVISIONS = ROOT / "data/candidate-q2-q3-vintage-revisions.json"
UNIVERSE = ROOT / "data/forecast-2027-ucdp261.json"
REPORT = ROOT / "data/candidate-onset-label-revision-ties.json"
K_VALUES = (5, 10, 20, 50)


def source_manifest(baseline, revisions):
    if baseline.get("status") != "RETROSPECTIVE_ONLY_NOT_ISSUED":
        raise SourceError("Historical baseline status invalid")
    if revisions.get("status") != "ARCHIVED_SOURCE_REVISIONS_NOT_PREDICTIVE_VALIDATION":
        raise SourceError("Historical revision status invalid")
    result = {}
    for item in baseline["sources"]:
        key = (item["year"], item["month"])
        if key in result:
            raise SourceError("Repeated frozen source")
        result[key] = {"source_url": item["source_url"], "sha256": item["source_sha256"]}
    for item in revisions["years"]:
        for q, month in (("q2", 6), ("q3", 9)):
            prior = item[q]
            key = (item["year"], month)
            if key in result and result[key] != {
                "source_url": prior["url"], "sha256": prior["sha256"]
            }:
                raise SourceError("Source provenance conflicts between pinned studies")
            result[key] = {"source_url": prior["url"], "sha256": prior["sha256"]}
    expected = {(year, month) for year in YEARS for month in (3, 6, 9)}
    if set(result) != expected:
        raise SourceError("Need EXACTLY nine 2024–2026 quarter archives")
    for (year, month), source in result.items():
        target_url = archive_url(year, month) if month in (3, 9) else url_for(year, 2)
        if source["source_url"] != target_url:
            raise SourceError("Source URL mismatches fixed archive path")
    return result


def summation(events, start, end):
    """Only entire GED event intervals, avoiding date leakage at boundaries."""
    by_country = defaultdict(int)
    matching = {}
    for event_id, country, event_start, event_end, deaths in events:
        if event_start >= start and event_end <= end:
            by_country[country] += deaths
            matching[event_id] = (country, deaths)
    return by_country, matching


def compare_may(year, q1, q2, q3, countries):
    ids = set(countries)
    origin, _ = summation(q1, date(year, 1, 1), date(year, 3, 31))
    early, event_early = summation(q2, date(year, 5, 1), date(year, 5, 30))
    late, event_late = summation(q3, date(year, 5, 1), date(year, 5, 30))
    risks = sorted(country for country in countries if origin[country] < 25)
    p2 = {c for c in countries if early[c] >= 25}
    p3 = {c for c in countries if late[c] >= 25}
    r2 = p2 & set(risks)
    r3 = p3 & set(risks)
    overlap = set(event_early) & set(event_late)
    changed_best = {event for event in overlap if event_early[event][1] != event_late[event][1]}
    changed_country = {event for event in overlap if event_early[event][0] != event_late[event][0]}
    return {
        "year": year,
        "month": "May 1-30",
        "risk_set_q1_under25": len(risks),
        "q2_30day_recorded_threshold_all196": len(p2),
        "q3_30day_recorded_threshold_all196": len(p3),
        "q2_30day_recorded_threshold_subthreshold": len(r2),
        "q3_30day_recorded_threshold_subthreshold": len(r3),
        "all196_label_0_to_1": len(p3 - p2),
        "all196_label_1_to_0": len(p2 - p3),
        "risk_label_0_to_1": len(r3 - r2),
        "risk_label_1_to_0": len(r2 - r3),
        "risk_label_changed_country_ids": sorted(r2 ^ r3),
        "all196_label_changed_country_ids": sorted(p2 ^ p3),
        "matched_may_statebased_ids": len(overlap),
        "only_q2_may_statebased_ids": len(set(event_early) - set(event_late)),
        "only_q3_may_statebased_ids": len(set(event_late) - set(event_early)),
        "matched_may_best_changed_ids": len(changed_best),
        "matched_may_country_changed_ids": len(changed_country),
        "may_statebased_best_total_q2": sum(early.values()),
        "may_statebased_best_total_q3": sum(late.values()),
        "countries_with_changed_may_best": sum(early[c] != late[c] for c in ids),
        "sum_abs_country_may_best_revision": sum(abs(early[c] - late[c]) for c in ids),
    }, origin, late


def tie_aware_k(rows, probability_field, k):
    if not 1 <= k <= len(rows):
        raise SourceError("Top K outside risk-set bounds")
    ordered = sorted(rows, key=lambda r: (-r[probability_field], r["country_id"]))
    remaining = k
    guaranteed = 0
    bound_min = bound_max = None
    expected = 0.0
    group_at_cutoff = None
    start = 0
    while start < len(ordered):
        p = ordered[start][probability_field]
        end = start
        while end < len(ordered) and ordered[end][probability_field] == p:
            end += 1
        group = ordered[start:end]
        positives = sum(row["target"] for row in group)
        selected = min(remaining, len(group))
        expected += selected * positives / len(group)
        if remaining <= len(group):
            forced = max(0, selected - (len(group) - positives))
            permitted = min(selected, positives)
            bound_min = guaranteed + forced
            bound_max = guaranteed + permitted
            group_at_cutoff = {
                "risk_probability": p,
                "tied_countries": len(group),
                "positive_countries_in_tie": positives,
                "selected_from_tie": selected,
            }
            break
        guaranteed += positives
        remaining -= len(group)
        start = end
    if bound_min is None or bound_max is None:
        raise SourceError("Top K tie bounds could not be calculated")
    positives_total = sum(r["target"] for r in rows)
    deterministic = sum(r["target"] for r in ordered[:k])
    return {
        "k": k,
        "deterministic_country_id_tiebreak_hits_not_skill": deterministic,
        "min_hits_across_valid_tie_breaks": bound_min,
        "max_hits_across_valid_tie_breaks": bound_max,
        "expected_hits_random_tie_break": round(expected, 8),
        "expected_precision": round(expected / k, 8),
        "expected_recall": round(expected / positives_total, 8) if positives_total else None,
        "cutoff_tie": group_at_cutoff,
    }


def alert_diagnostics(frozen_baseline):
    vector = frozen_baseline["retrospective_2026_country_vector"]
    if len(vector) != 196:
        raise SourceError("Expected exact frozen 196-country 2026 holdout")
    alerts = []
    for row in vector:
        if row["prior_best_q1_2026"] >= 25:
            continue
        prediction = row["h90"]
        alerts.append({
            "country_id": row["country_id"],
            "country": row["country"],
            "prior_best_q1": row["prior_best_q1_2026"],
            "target": prediction["target"],
            "target_best_90d": prediction["target_best_q3_2026"],
            "p_global": prediction["predicted_probabilities"]["global"],
            "p_persistence": prediction["predicted_probabilities"]["persistence"],
            "p_recent_volume": prediction["predicted_probabilities"]["recent_volume"],
        })
    positive = [r for r in alerts if r["target"] == 1]
    return {
        "horizon_days": 90,
        "holdout_year": 2026,
        "at_risk": len(alerts),
        "positives": len(positive),
        "country_positive_cases": sorted(
            [{"country_id": r["country_id"], "country": r["country"],
              "prior_best_q1": r["prior_best_q1"], "target_best_90d": r["target_best_90d"],
              "p_recent_volume": r["p_recent_volume"], "p_persistence": r["p_persistence"]}
             for r in positive], key=lambda item: item["country_id"]
        ),
        "alert_tie_aware": {
            model: [tie_aware_k(alerts, model, k) for k in K_VALUES]
            for model in ("p_global", "p_persistence", "p_recent_volume")
        },
        "interpretation": (
            "Only 2026 Q1-subthreshold countries. Probabilities were fitted without 2026 outcomes. "
            "A 10-country list tied at the boundary has non-identifiable precision: use bounds "
            "and random-tie expectation, not country-ID tiebreak as evidence of new-onset skill."
        ),
    }


def build_report(fetcher=get_source, baseline=None, revisions=None, universe=None):
    baseline = json.loads(BASELINE.read_text("utf8")) if baseline is None else baseline
    revisions = json.loads(REVISIONS.read_text("utf8")) if revisions is None else revisions
    universe = UNIVERSE.read_bytes() if universe is None else universe
    if hashlib.sha256(universe).hexdigest() != baseline["universe_sha256"]:
        raise SourceError("Prospective GEO2027 universe bytes changed")
    names = dict(universe_from_bytes(universe))
    manifest = source_manifest(baseline, revisions)
    timeline = []
    scans = []
    year_rebuild = {}
    for year in YEARS:
        parsed = {}
        for month in (3, 6, 9):
            src = manifest[(year, month)]
            raw = fetcher(src["source_url"])
            sha = hashlib.sha256(raw).hexdigest()
            if sha != src["sha256"]:
                raise SourceError(f"Original UCDP archive SHA mismatch in {year} m{month:02d}")
            role = "origin" if month == 3 else "outcome"
            scan, events = extract_state_based(raw, year, role, set(names))
            parsed[month] = events
            scans.append({
                "year": year, "month": month, "source_sha256": sha,
                "source_bytes": len(raw), "audit": scan,
            })
        stats, prior, q3_may_best = compare_may(
            year, parsed[3], parsed[6], parsed[9], names
        )
        timeline.append(stats)
        year_rebuild[year] = (prior, q3_may_best)
    if len(timeline) != 3:
        raise SourceError("Incomplete 2024-2026 source horizon")
    # Prevent any quiet drift from the first predeclared #146 2026 holdout.
    for row in baseline["retrospective_2026_country_vector"]:
        country = row["country_id"]
        if year_rebuild[2026][0][country] != row["prior_best_q1_2026"]:
            raise SourceError("Drift in 2026 Q1 origin from frozen baseline")
        if year_rebuild[2026][1][country] != row["h30"]["target_best_q3_2026"]:
            raise SourceError("Drift in 2026 Q3 May target from frozen baseline")
    return {
        "schema": "idealab.psico.candidate.onset_label_stability_tie_v1",
        "status": "RETROSPECTIVE_REVISIONS_NOT_ASOF_NOT_PROSPECTIVE",
        "protocol_date": "2026-11-19",
        "outcome": "UCDP Candidate 25+ recorded state-based best, full May1-30 events date_prec in {1,2}",
        "nine_official_archives": scans,
        "may30_revision_by_year": timeline,
        "risk30_all_years_summary": {
            "at_risk_country_years": sum(r["risk_set_q1_under25"] for r in timeline),
            "q2_positive_country_years": sum(r["q2_30day_recorded_threshold_subthreshold"] for r in timeline),
            "q3_positive_country_years": sum(r["q3_30day_recorded_threshold_subthreshold"] for r in timeline),
            "risk_labels_gained": sum(r["risk_label_0_to_1"] for r in timeline),
            "risk_labels_lost": sum(r["risk_label_1_to_0"] for r in timeline),
            "sum_abs_country_may_best_revision": sum(
                r["sum_abs_country_may_best_revision"] for r in timeline
            ),
        },
        "holdout_2026_subthreshold_90d": alert_diagnostics(baseline),
        "historical_vintage_first_release_dates_verified": False,
        "no_model_refit": True,
        "prospective_issued_probabilities": 0,
        "prospective_outcomes_resolved": 0,
        "warning": (
            "May outcome is measured in Q2 and Q3 later vintages, not two independent "
            "outcomes. 2026 positives are just Candidate provisional recorded thresholds. "
            "Some tied ranking positions are arbitrary and are not evidence of foresight."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--print-report", action="store_true")
    mode.add_argument("--check-report", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = build_report()
        if args.print_report:
            print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            frozen = json.loads(REPORT.read_text(encoding="utf8"))
            if frozen != report:
                raise SourceError("Official nine-vintage revision report drifted from pinned SHA")
            print("OK: official UCDP Q1/Q2/Q3 May labels, 2026 tied onset alerts and privacy-safe aggregates reproduced")
    except (SourceError, ValueError, OSError, TimeoutError, KeyError, TypeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
