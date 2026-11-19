#!/usr/bin/env python3
"""Preregistered 24-anchor, two-year UCDP GED25.1 temporal-spatial ambiguity audit.

Designed using source schema and strata before retrieving rows for this study.
Near events are candidates for manual review, NEVER proof of GED duplication.
Preserves both issued GEO forecast vectors and the prior Burundi evidence.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import date
from hashlib import sha256
from io import BytesIO, TextIOWrapper
import json
from math import asin, cos, isfinite, radians, sin, sqrt
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data/geo-ged251-2021-22-linkage-sample24.json"
FORECAST = ROOT / "data/forecast-2027-ucdp261.json"
GED_URL = "https://ucdp.uu.se/downloads/ged/ged251-csv.zip"
GED_SHA = "e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d"
SEED = "IDEALAB-20261119-GED251-2021-22-FOUR-STRATA-V1"
YEARS = (2021, 2022)
N_PER_STRATUM = 6
MAX_ZIP = 90_000_000
STRATA = ("day_highgeo", "day_lowgeo", "interval_highgeo", "interval_lowgeo")


def haversine(a, b):
    lat1, lon1, lat2, lon2 = map(radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    x = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 12742 * asin(sqrt(min(1.0, max(0.0, x))))


def gap_days(a, b):
    if a["end"] < b["start"]:
        return (b["start"] - a["end"]).days
    if b["end"] < a["start"]:
        return (a["start"] - b["end"]).days
    return 0


def classify_stratum(ev):
    return ("day" if ev["start"] == ev["end"] else "interval") + (
        "_highgeo" if ev["where_prec"] <= 2 else "_lowgeo")


def parse_row(r, frame_gwno):
    try:
        if int(r["type_of_violence"]) != 1:
            return None
        year, gwno, best, eid = (int(r["year"]), int(r["country_id"]),
                                   int(r["best"]), int(r["id"]))
        if year not in YEARS or gwno not in frame_gwno or eid <= 0 or best < 1:
            return None
        start = date.fromisoformat(r["date_start"][:10])
        end = date.fromisoformat(r["date_end"][:10])
        where_prec = int(r["where_prec"])
        lat, lon = float(r["latitude"]), float(r["longitude"])
    except (TypeError, ValueError, OverflowError):
        return None
    if (start > end or start.year != year or end.year != year
            or where_prec not in range(1, 8)
            or not isfinite(lat) or not isfinite(lon)
            or not -90 <= lat <= 90 or not -180 <= lon <= 180):
        return None
    return dict(id=eid, GWNO=gwno, year=year, best=best,
                start=start, end=end, where_prec=where_prec, lat=lat, lon=lon)


def parse_ged(raw, frame_gwno):
    digest = sha256(raw).hexdigest()
    if digest != GED_SHA:
        raise ValueError("Official GED25.1 ZIP SHA-256 changed")
    if len(raw) > MAX_ZIP or not raw.startswith(b"PK"):
        raise ValueError("Official UCDP archive missing or too large")
    required = {"id", "type_of_violence", "year", "country_id", "best",
                "date_start", "date_end", "latitude", "longitude", "where_prec"}
    events, seen = [], set()
    with ZipFile(BytesIO(raw)) as archive:
        members = [x for x in archive.infolist()
                   if x.filename.lower().endswith(".csv") and not x.is_dir()]
        if len(members) != 1 or members[0].file_size > 900_000_000:
            raise ValueError("Expected single bounded official GED CSV")
        with TextIOWrapper(archive.open(members[0]), encoding="utf-8-sig",
                           newline="") as stream:
            rows = csv.DictReader(stream)
            if not required.issubset(rows.fieldnames or []):
                raise ValueError("Official GED source missing precision/date fields")
            total = 0
            for row in rows:
                total += 1
                ev = parse_row(row, frame_gwno)
                if ev:
                    if ev["id"] in seen:
                        raise ValueError("Duplicate eligible GED event ID")
                    seen.add(ev["id"])
                    events.append(ev)
    if total < 100_000:
        raise ValueError("Unexpectedly small official GED25.1 dataset")
    return total, events


def pick_sample(events, n=N_PER_STRATUM):
    # Sampling uses only stratum, GWNO, and event ID. It does not inspect
    # geographical/time collisions, other IDs, model probabilities or outcomes.
    groups = defaultdict(list)
    for ev in events:
        groups[classify_stratum(ev)].append(ev)
    sample = []
    for stratum in STRATA:
        ranked = sorted(groups[stratum], key=lambda e: (
            sha256(f"{SEED}|{e['id']}".encode()).hexdigest(), e["id"]))
        if len(ranked) < n:
            raise ValueError("Insufficient predeclared sampling stratum")
        chosen, gwno_seen, ids = [], set(), set()
        # Prefer country diversity; deterministic fill if fewer than n countries.
        for ev in ranked:
            if ev["GWNO"] not in gwno_seen:
                chosen.append(ev)
                ids.add(ev["id"])
                gwno_seen.add(ev["GWNO"])
                if len(chosen) == n:
                    break
        if len(chosen) < n:
            for ev in ranked:
                if ev["id"] not in ids:
                    chosen.append(ev)
                    ids.add(ev["id"])
                    if len(chosen) == n:
                        break
        sample.extend(chosen)
    if len({e["id"] for e in sample}) != len(sample):
        raise ValueError("Sample event repeated across strata")
    return sample, {s: len(groups[s]) for s in STRATA}


def inspect_anchor(anchor, by_country_year):
    other = [ev for ev in by_country_year[(anchor["GWNO"], anchor["year"])]
             if ev["id"] != anchor["id"]]
    at_25, temporal_3, both_25_3, both_100_3, strict_25_3 = 0, 0, [], 0, 0
    exact_5_0 = 0
    for ev in other:
        days = gap_days(anchor, ev)
        # Coordinates may be administrative centroids, not incident points.
        km = haversine(anchor, ev)
        at_25 += (km <= 25)
        temporal_3 += (days <= 3)
        both_100_3 += (days <= 3 and km <= 100)
        if days == 0 and km <= 5:
            exact_5_0 += 1
        if days <= 3 and km <= 25:
            precise = anchor["where_prec"] <= 2 and ev["where_prec"] <= 2
            strict_25_3 += precise
            both_25_3.append((round(km, 3), days, ev["id"], ev["where_prec"]))
    both_25_3.sort()
    return {
        "ged_id": anchor["id"],
        "GWNO": anchor["GWNO"],
        "year": anchor["year"],
        "start": anchor["start"].isoformat(),
        "end": anchor["end"].isoformat(),
        "where_prec": anchor["where_prec"],
        "best_deaths": anchor["best"],
        "stratum": classify_stratum(anchor),
        "same_country_year_other_GED_events": len(other),
        "location_only_neighbors_25km": at_25,
        "time_only_neighbors_gap3d": temporal_3,
        "space_time_neighbors_gap0d_5km": exact_5_0,
        "space_time_neighbors_gap3d_25km": len(both_25_3),
        "space_time_neighbors_gap3d_100km": both_100_3,
        "both_high_geo_precision_neighbors_gap3d_25km": strict_25_3,
        "closest_three_candidate_neighbors": [
            {"ged_id": eid, "distance_km": km, "interval_gap_days": days,
             "where_prec": wp} for km, days, eid, wp in both_25_3[:3]],
        "identity_or_duplicate_proven": False,
    }


def build(events, total_ged_rows, original_forecast_digest):
    sample, population_by_stratum = pick_sample(events)
    by_country_year = defaultdict(list)
    for ev in events:
        by_country_year[(ev["GWNO"], ev["year"])].append(ev)
    results = [inspect_anchor(e, by_country_year) for e in sample]
    if len(results) != N_PER_STRATUM * len(STRATA):
        raise ValueError("Unexpected audit sample size")
    summary = {
        "anchors_with_any_25km_place_only_neighbor": sum(
            e["location_only_neighbors_25km"] > 0 for e in results),
        "anchors_with_any_gap3d_25km_candidate": sum(
            e["space_time_neighbors_gap3d_25km"] > 0 for e in results),
        "anchors_with_any_gap3d_100km_candidate": sum(
            e["space_time_neighbors_gap3d_100km"] > 0 for e in results),
        "anchors_with_any_gap0d_5km_candidate": sum(
            e["space_time_neighbors_gap0d_5km"] > 0 for e in results),
        "anchors_with_high_precision_gap3d_25km_candidate": sum(
            e["both_high_geo_precision_neighbors_gap3d_25km"] > 0 for e in results),
        "verified_duplicate_GED_events": 0,
        "manual_case_reviews_completed": 0,
    }
    return {
        "schema": "idealab.psico.geo_ged251_2021_22_temporal_spatial_sample.v1",
        "research_design_date": "2026-11-19",
        "phase": "SCREENING_ONLY_NOT_MANUAL_VALIDATION",
        "preregistered_sampling_seed": SEED,
        "source": GED_URL,
        "official_GED25_1_zip_SHA256": GED_SHA,
        "original_issued_GEO2027_SHA256": original_forecast_digest,
        "country_frame": "196 GWNO in issued GEO2027; use IDs only, no probabilities",
        "years": list(YEARS),
        "violence_type": 1,
        "n_per_stratum": N_PER_STRATUM,
        "population_total_GED_events": total_ged_rows,
        "eligible_events": len(events),
        "eligible_by_stratum": population_by_stratum,
        "sampled_anchors_n": len(results),
        "sampled_distinct_GWNO_n": len({r["GWNO"] for r in results}),
        "selection_is_without_GEO2027_probabilities": True,
        "geographic_precision_high": "where_prec=1/2 only; 2 is approximate <=25km",
        "geographic_precision_low": "where_prec=3..7; coordinates may represent large zones",
        "candidate_definition": "same country and year, interval gap <=3 days, coordinate separation <=25km; no identity inference",
        "summary": summary,
        "sampled_anchors": results,
        "source_fatality_rosters_verified": False,
        "external_documentary_verification_performed": False,
        "population_duplication_rate_estimated": False,
        "forecast_vectors_or_GED_labels_modified": False,
        "limitations": "Stratified SHA deterministic sample, not representative random population survey; on-disk GED25.1 official ZIP content SHA verified but publication-era bytes are not independently timestamped. Nearby state-based GED rows need not share people or episode, especially where_prec>=3. Coincident date/place is a screening signal, not an adjudicated duplicate. No news independence, true victim counts, forecasting skill or Brier change established.",
    }


def read_frame():
    from prepare_geo2027_transition_alerts import SOURCE_SHA256, FORECAST_PATH
    payload = FORECAST_PATH.read_bytes()
    digest = sha256(payload).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError("Issued GEO2027 source changed")
    j = json.loads(payload)
    ids = {int(x["country_id"]) for x in j["countries"]}
    if len(ids) != 196:
        raise ValueError("Frozen 196-country cohort changed")
    return ids, digest


def audit_existing_forecasts():
    from audit_geo2027_global_only_matched_issue import (
        ISSUE, MANIFEST, ORIGINAL, OLD_SHADOW, OLD_MANIFEST, ALERTS,
        audit as audit_issued)
    audit_issued(ISSUE.read_bytes(), MANIFEST.read_bytes(), ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(), OLD_MANIFEST.read_bytes(), ALERTS.read_bytes())


def get_official_bytes():
    with urlopen(Request(GED_URL, headers={
        "User-Agent": "IDEA-LAB-GEO-SCIENCE-HISTORICAL-AUDIT/1.0"
    }), timeout=100) as resp:
        raw = resp.read(MAX_ZIP + 1)
    if len(raw) > MAX_ZIP:
        raise ValueError("Official GED archive unexpectedly oversized")
    return raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit-report", action="store_true")
    ap.add_argument("--check-report", action="store_true")
    args = ap.parse_args()
    frame, frozen = read_frame()
    audit_existing_forecasts()
    total, events = parse_ged(get_official_bytes(), frame)
    report = build(events, total, frozen)
    if args.check_report:
        if not REPORT.is_file():
            raise ValueError("Published sample report missing; use --emit-report first")
        if json.loads(REPORT.read_text(encoding="utf-8")) != report:
            raise ValueError("Published stratified sample differs from official replay")
    if args.emit_report:
        print("GED251_LINKAGE_SAMPLE_BEGIN")
        print(json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
        print("GED251_LINKAGE_SAMPLE_END")
    else:
        print(json.dumps({"sampled": report["sampled_anchors_n"],
                          "eligible": report["eligible_events"],
                          "summary": report["summary"]}, sort_keys=True))


if __name__ == "__main__":
    main()
