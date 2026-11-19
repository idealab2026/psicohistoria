#!/usr/bin/env python3
"""Post-selection label stability: UCDP Candidate Q2 vs Q3 May, 2024–2026.

All sources SHA-pinned by earlier research. No model fit or prospectively
issued probability is created; the favorable five-death result was known.
"""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import sys

from check_ucdp_candidate_asof import SourceError
from audit_candidate_q2_q3_vintages import get_source, url_for
from audit_candidate_onset_label_stability import summation, tie_aware_k
from experiment_candidate_30_90_holdout import archive_url, extract_state_based, universe_from_bytes

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data/candidate-onset-label-revision-ties.json"
GRID = ROOT / "data/candidate-reactivation-threshold-grid.json"
UNIVERSE = ROOT / "data/forecast-2027-ucdp261.json"
REPORT = ROOT / "data/candidate-may-threshold-vintage-stability.json"
YEARS = (2024, 2025, 2026)
THRESHOLDS = (1, 5, 10, 25)


def pinned_sources(revisions):
    if revisions.get("status") != "RETROSPECTIVE_REVISIONS_NOT_ASOF_NOT_PROSPECTIVE":
        raise SourceError("Source registry must be the prior SHA-frozen onset stability audit")
    sources = {}
    for row in revisions.get("nine_official_archives", []):
        key = (row["year"], row["month"])
        if key in sources:
            raise SourceError("Duplicate original UCDP source in frozen registry")
        sources[key] = row["source_sha256"]
    expected = {(y, m) for y in YEARS for m in (3, 6, 9)}
    if set(sources) != expected:
        raise SourceError("Not exactly nine previously verified 2024–2026 originals")
    return sources


def compare_year(year, q1, q2, q3, names, grid=None):
    start_q1, end_q1 = date(year, 1, 1), date(year, 3, 31)
    start_may, end_may = date(year, 5, 1), date(year, 5, 30)
    origin, _ = summation(q1, start_q1, end_q1)
    may_q2, _ = summation(q2, start_may, end_may)
    may_q3, _ = summation(q3, start_may, end_may)
    if grid is not None:
        vector = grid["holdout_2026_country_observations"]
        if len(vector) != len(names):
            raise SourceError("Frozen 2026 grid country count changed")
        for row in vector:
            country = row["country_id"]
            if (origin[country] != row["q1_state_best"] or
                    may_q3[country] != row["future_best_30"]):
                raise SourceError("Source revisions modify the frozen original 2026 grid")
    outcome = {}
    for t in THRESHOLDS:
        risks = {country for country in names if origin[country] < t}
        pos_q2 = {country for country in risks if may_q2[country] >= t}
        pos_q3 = {country for country in risks if may_q3[country] >= t}
        outcome[str(t)] = {
            "risk_set": len(risks),
            "q2_positives": len(pos_q2),
            "q3_positives": len(pos_q3),
            "gained_q3": len(pos_q3 - pos_q2),
            "lost_q3": len(pos_q2 - pos_q3),
            "gained_ids": sorted(pos_q3 - pos_q2),
            "lost_ids": sorted(pos_q2 - pos_q3),
            "q2_positive_country_ids": sorted(pos_q2),
            "q3_positive_country_ids": sorted(pos_q3),
        }
    return {
        "year": year,
        "thresholds": outcome,
        "total_abs_best_revision_may_196": sum(
            abs(may_q2[c] - may_q3[c]) for c in names
        ),
        "countries_with_best_revision_may_196": sum(
            may_q2[c] != may_q3[c] for c in names
        ),
    }, origin, may_q2, may_q3


def score_original_combined_ties(grid, origin, may_q2, may_q3):
    year = 2026
    names = {
        r["country_id"]: r["country"]
        for r in grid["holdout_2026_country_observations"]
    }
    results = {}
    for t in THRESHOLDS:
        fitted = grid["trained_models"][str(t)]["30"]
        records = grid["holdout_2026_country_observations"]
        a, b = [], []
        for r in records:
            country = r["country_id"]
            if origin[country] >= t:
                continue
            v = r["q1_state_best"]
            state = ("zero" if v == 0 else "1-4" if v < 5 else
                     "5-9" if v < 10 else "10+")
            other = "True" if r["q1_other_best"] >= 1 else "False"
            p = fitted["groups"]["combined"][state + "|" + other]["p"]
            a.append({"country_id": country, "p": p, "target": int(may_q2[country] >= t)})
            b.append({"country_id": country, "p": p, "target": int(may_q3[country] >= t)})
        if len(a) <= 10:
            raise SourceError("Empty or undersized 2026 risk set")
        results[str(t)] = {
            "positive_q2": sum(x["target"] for x in a),
            "positive_q3": sum(x["target"] for x in b),
            "top10_q2": tie_aware_k(a, "p", 10),
            "top10_q3": tie_aware_k(b, "p", 10),
        }
    return results


def build_report(fetcher=get_source, frozen_sources=None, frozen_grid=None,
                 universe_raw=None):
    raw = UNIVERSE.read_bytes() if universe_raw is None else universe_raw
    countries = dict(universe_from_bytes(raw))
    sources = json.loads(SOURCES.read_text("utf8")) if frozen_sources is None else frozen_sources
    grid = json.loads(GRID.read_text("utf8")) if frozen_grid is None else frozen_grid
    if grid.get("status") != "EXPLORATORY_HISTORICAL_NOT_ASOF_NOT_ISSUED":
        raise SourceError("Expected frozen historical, non-prospective grid")
    if grid["universe_sha256"] != hashlib.sha256(raw).hexdigest():
        raise SourceError("Canonical country universe SHA differs")
    original = pinned_sources(sources)
    annual = []
    provenance = []
    last = None
    for year in YEARS:
        data = {}
        for month in (3, 6, 9):
            url = archive_url(year, month) if month != 6 else url_for(year, 2)
            raw_csv = fetcher(url)
            hashval = hashlib.sha256(raw_csv).hexdigest()
            if hashval != original[(year, month)]:
                raise SourceError(f"Official Candidate vintage changed SHA year={year} month={month}")
            meta, records = extract_state_based(
                raw_csv, year, "origin" if month == 3 else "outcome", set(countries)
            )
            provenance.append({
                "year": year, "month": month, "source_url": url,
                "source_sha256": hashval, "source_rows": meta["source_rows"],
            })
            data[month] = records
        summary, origin, may2, may3 = compare_year(
            year, data[3], data[6], data[9], countries,
            grid if year == 2026 else None
        )
        annual.append(summary)
        if year == 2026:
            last = score_original_combined_ties(grid, origin, may2, may3)
    return {
        "schema": "idealab.psico.candidate.may_threshold_vintage_stability.v1",
        "status": "POST_SELECTION_SOURCE_REVISION_SENSITIVITY_NOT_PROSPECTIVE",
        "protocol_date": "2026-11-19",
        "years": list(YEARS),
        "thresholds": list(THRESHOLDS),
        "country_universe_sha256": hashlib.sha256(raw).hexdigest(),
        "source_grid_sha256": hashlib.sha256(
            (GRID.read_bytes() if frozen_grid is None else json.dumps(
                grid, ensure_ascii=False, sort_keys=True).encode("utf8"))
        ).hexdigest(),
        "nine_original_sha_pinned_sources": provenance,
        "may_label_revision_by_year": annual,
        "original_2026_combined_model_tie_aware_top10": last,
        "original_release_dates_independently_verified": False,
        "retraining_performed": False,
        "new_prospective_predictions": 0,
        "limitations": (
            "This is a post-hoc sensitivity triggered by favorable threshold-5 "
            "results previously inspected. May candidate labels in Q2 and Q3 are "
            "not final events or ground truth. Source vintage first-public dates "
            "have not been certified. Rankings are not new country forecasts."
        ),
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--print-report", action="store_true")
    g.add_argument("--check-report", action="store_true")
    args = p.parse_args(argv)
    try:
        result = build_report()
        if args.print_report:
            print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            saved = json.loads(REPORT.read_text("utf8"))
            if result != saved:
                raise SourceError("Original-source Q2→Q3 label stability drifted from frozen result")
            print("OK: nine source hashes and frozen 2026 grid match UCDP May label revision sensitivity")
    except (SourceError, OSError, ValueError, TypeError, KeyError, TimeoutError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
