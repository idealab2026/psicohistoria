#!/usr/bin/env python3
"""UCDP Candidate 2024/25 May outcomes vs annual GED 25.1/26.1.

AUDIT ONLY. No as-of forecast claim. Annual GED version is a different estimand.
Protocol fixed before the first analysis of annual ZIP content.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, timedelta
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
import urllib.request
import zipfile

from check_ucdp_candidate_asof import SourceError, ged_day
from experiment_candidate_30_90_holdout import extract_state_based, archive_url, universe_from_bytes
from audit_candidate_q2_q3_vintages import get_source, url_for

ROOT = Path(__file__).resolve().parents[1]
YEARS = (2024, 2025)
HORIZONS = (30, 90)
THRESHOLDS = (1, 5, 10, 25)
GED_URL = {
    2024: "https://ucdp.uu.se/downloads/ged/ged251-csv.zip",
    2025: "https://ucdp.uu.se/downloads/ged/ged261-csv.zip",
}
# These MUST be set using SHA of original official ZIPs in a source-only census,
# prior to calculating the outcome comparison. No unpinned calculation allowed.
ANNUAL_ZIP_SHA = {
    2024: None,
    2025: None,
}
COUNTRY_SOURCE = ROOT / "data/forecast-2027-ucdp261.json"
CANDIDATE_REGISTRY = ROOT / "data/candidate-onset-label-revision-ties.json"
PREVIOUS_THRESHOLD_STUDY = ROOT / "data/candidate-may-threshold-vintage-stability.json"
PREVIOUS_GRID = ROOT / "data/candidate-reactivation-threshold-grid.json"
REPORT = ROOT / "data/candidate-to-annual-ged-resolution.json"
MAX_ARCHIVE_BYTES = 110_000_000
MAX_UNCOMPRESSED = 750_000_000


def fetch_annual_zip(url):
    if url not in GED_URL.values():
        raise SourceError("Unregistered official GED annual ZIP URL")
    request = urllib.request.Request(url, headers={"User-Agent": "IDEA-LAB-institutional-science-audit/1.0"})
    parts = []
    total = 0
    with urllib.request.urlopen(request, timeout=110) as response:
        if response.url != url:
            raise SourceError("GED ZIP redirect unexpectedly changed the source")
        while True:
            piece = response.read(1024 * 1024)
            if not piece:
                break
            total += len(piece)
            if total > MAX_ARCHIVE_BYTES:
                raise SourceError("GED ZIP exceeds declared source size budget")
            parts.append(piece)
    raw = b"".join(parts)
    if not raw.startswith(bytes((80, 75, 3, 4))):
        raise SourceError("Downloaded GED archive is not a ZIP")
    return raw


def examine_zip(raw):
    if not isinstance(raw, bytes) or not raw.startswith(bytes((80, 75, 3, 4))):
        raise SourceError("GED official archive ZIP signature invalid")
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise SourceError("GED official archive ZIP too large")
    try:
        with zipfile.ZipFile(io.BytesIO(raw), "r") as archive:
            items = archive.infolist()
            if not items or sum(item.file_size for item in items) > MAX_UNCOMPRESSED:
                raise SourceError("GED decompressed size cap exceeded")
            result = [{"member": item.filename, "bytes": item.file_size,
                       "compressed": item.compress_size} for item in items]
            for item in items:
                if (item.file_size > MAX_UNCOMPRESSED or item.filename.startswith("/")
                    or ".." in PurePosixPath(item.filename).parts):
                    raise SourceError("Suspicious ZIP member path/size")
            return result
    except zipfile.BadZipFile as exc:
        raise SourceError("GED source is a corrupt ZIP") from exc


def annual_census(fetcher=fetch_annual_zip):
    census = []
    for year in YEARS:
        url = GED_URL[year]
        original = fetcher(url)
        members = examine_zip(original)
        census.append({"year": year, "url": url, "source_sha256": hashlib.sha256(original).hexdigest(),
                       "zip_bytes": len(original), "zip_members": members})
    return {"schema": "idealab.psico.ged_annual_source_census.v1",
            "status": "SOURCES_ONLY_NO_OUTCOMES_EVALUATED", "sources": census}


def csv_member(archive, year):
    # annual v25.1 or v26.1 should contain only one GEDEvent CSV.
    version = {2024: "25", 2025: "26"}[year]
    candidates = [
        item for item in archive.infolist()
        if re.fullmatch(r"GEDEvent_v" + version + r"[_\.]1\.csv",
                        PurePosixPath(item.filename).name, re.IGNORECASE)
    ]
    if len(candidates) != 1:
        raise SourceError("Expected exactly one official GED annual event CSV")
    return candidates[0]


def read_annual(raw, year, population):
    """Scan the annual GED ZIP, retaining target-year ID census and precise May/Jul windows."""
    if year not in YEARS:
        raise SourceError("Unplanned annual GED origin year")
    examine_zip(raw)
    event_window = []
    by_id_annual_year = {}
    counter = Counter()
    with zipfile.ZipFile(io.BytesIO(raw), "r") as zipped:
        item = csv_member(zipped, year)
        if item.file_size > MAX_UNCOMPRESSED:
            raise SourceError("GED annual CSV uncompressed too large")
        with zipped.open(item, "r") as stream:
            reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig", newline=""))
            required = {"id", "year", "country_id", "type_of_violence", "date_prec",
                        "date_start", "date_end", "best"}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise SourceError("Annual GED CSV missing required event schema")
            start_window = date(year, 5, 1)
            end_window = start_window + timedelta(days=89)
            for row in reader:
                counter["all_annual_rows"] += 1
                try:
                    row_year = int(row["year"])
                except (ValueError, TypeError) as exc:
                    raise SourceError("Unparseable GED annual row year") from exc
                if row_year != year:
                    continue
                counter["target_year_rows"] += 1
                event_id = (row.get("id") or "").strip()
                if not event_id or event_id in by_id_annual_year:
                    raise SourceError("GED annual repeated or missing id within target year")
                try:
                    country = int(row["country_id"])
                    violence = int(row["type_of_violence"])
                    precision = int(row["date_prec"])
                    best = int(row["best"])
                except (TypeError, ValueError) as exc:
                    raise SourceError("GED target year event coding unparseable") from exc
                if country <= 0 or violence not in (1, 2, 3) or best < 0 or precision not in (0,1,2,3,4,5):
                    raise SourceError("GED year event invalid type, deaths or date precision")
                beginning = ged_day(row["date_start"], "date_start")
                ending = ged_day(row["date_end"], "date_end")
                if ending < beginning:
                    raise SourceError("Annual event dates reversed")
                by_id_annual_year[event_id] = (country, violence, beginning, ending)
                if violence != 1:
                    counter["skip_nonstate"] += 1
                    continue
                if precision not in (1, 2):
                    counter["skip_date_precision"] += 1
                    continue
                if country not in population:
                    counter["skip_country_outside_196"] += 1
                    continue
                if beginning < start_window or ending > end_window:
                    counter["skip_outside_target_90_window"] += 1
                    continue
                counter["retained_statebased_may_to_july"] += 1
                event_window.append((event_id, country, beginning, ending, best, "annual_ged"))
    if not counter["target_year_rows"]:
        raise SourceError("Annual GED file contains no target-year records")
    return {
        "zip_member": item.filename, "zip_csv_bytes": item.file_size,
        **dict(sorted(counter.items())),
    }, event_window, by_id_annual_year


def candidate_with_status(raw, year, month, population):
    role = "origin" if month == 3 else "outcome"
    meta, events = extract_state_based(raw, year, role, population)
    valid = {ev[0] for ev in events}
    codes = {}
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    if not reader.fieldnames or "code_status" not in reader.fieldnames:
        raise SourceError("Candidate code_status missing")
    for row in reader:
        event_id = (row.get("id") or "").strip()
        if event_id in valid:
            codes[event_id] = (row.get("code_status") or "").strip().casefold() or "(blank)"
    if len(codes) != len(valid):
        raise SourceError("Candidate code-status coverage inconsistent with eligible IDs")
    return meta, [(id_,country,start,end,best,codes[id_])
                  for id_,country,start,end,best in events]


def rollup(events, year, horizon):
    start = date(year, 5, 1)
    finish = start + timedelta(days=horizon - 1)
    sums = defaultdict(int)
    selected = defaultdict(list)
    code_deaths = defaultdict(lambda: defaultdict(int))
    for event in events:
        event_id, country, e_start, e_end, best, *extra = event
        if start <= e_start and e_end <= finish:
            sums[country] += best
            selected[country].append(event_id)
            if extra:
                code_deaths[country][extra[0]] += best
    return sums, selected, code_deaths


def prior_sums(events, year):
    prior = defaultdict(int)
    for _, country, start, end, best, *_ in events:
        if start >= date(year,1,1) and end <= date(year,3,31):
            prior[country] += best
    return prior


def paired_metrics(prior, candidate, annual, threshold, countries):
    risk = sorted(c for c in countries if prior[c] < threshold)
    labels = {
        "candidate": {c for c in risk if candidate[c] >= threshold},
        "ged_annual": {c for c in risk if annual[c] >= threshold},
    }
    a, b = labels["candidate"], labels["ged_annual"]
    both = a & b
    return {
        "n_at_risk": len(risk), "candidate_positive": len(a),
        "ged_positive": len(b), "both_positive": len(both),
        "candidate_only": len(a-b), "ged_only": len(b-a),
        "both_negative": len(risk)-len(a|b), "disagreements": len(a^b),
        "candidate_positive_matching_ged_share": round(len(both)/len(a),8) if a else None,
        "candidate_sensitivity_to_ged_label": round(len(both)/len(b),8) if b else None,
        "candidate_only_country_ids": sorted(a-b),
        "ged_only_country_ids": sorted(b-a),
    }


def matching_event_ids(candidate_ids, annual_ids, annual_window_ids, country_names):
    unique = set()
    exact_year = 0
    exact_window_country = 0
    for country, ids in candidate_ids.items():
        for id_ in ids:
            if id_ in unique:
                raise SourceError("Candidate event ID appears in multiple countries")
            unique.add(id_)
            exact_year += int(id_ in annual_ids)
            exact_window_country += int(id_ in annual_window_ids.get(country, []))
    return {
        "q3_candidate_eligible_may_event_ids": len(unique),
        "candidate_id_in_annual_target_year_any_type_any_date": exact_year,
        "candidate_id_in_annual_same_country_same_window": exact_window_country,
        "not_matched_by_exact_id_in_annual_target_year": len(unique)-exact_year,
        "warning": "No exact ID match can reflect deletion, split, merge or recoding; do not infer disappearance of an event.",
    }


def candidate_registry_pins(registry):
    if registry.get("status") != "RETROSPECTIVE_REVISIONS_NOT_ASOF_NOT_PROSPECTIVE":
        raise SourceError("Prior institutional Candidate source registry unavailable")
    pins = {}
    for item in registry.get("nine_official_archives", []):
        y, m = item["year"],item["month"]
        if y not in YEARS:
            continue
        key = (y,m)
        if key in pins:
            raise SourceError("Duplicate frozen Candidate archive pin")
        url = archive_url(y, m) if m in (3,9) else url_for(y, 2)
        if item.get("source_url") != url or len(item.get("source_sha256","")) != 64:
            raise SourceError("Frozen Candidate manifest path/SHA mismatch")
        pins[key] = item["source_sha256"]
    if set(pins) != {(y,m) for y in YEARS for m in (3,6,9)}:
        raise SourceError("Missing exactly six prerequisite Candidate vintages")
    return pins


def build_report(candidate_fetcher=get_source, annual_fetcher=fetch_annual_zip,
                 raw_universe=None, candidate_registry=None,
                 prior_stability=None, prior_grid=None, annual_pins=None):
    raw_universe = COUNTRY_SOURCE.read_bytes() if raw_universe is None else raw_universe
    names = dict(universe_from_bytes(raw_universe))
    registry = json.loads(CANDIDATE_REGISTRY.read_text("utf8")) if candidate_registry is None else candidate_registry
    stability = json.loads(PREVIOUS_THRESHOLD_STUDY.read_text("utf8")) if prior_stability is None else prior_stability
    grid = json.loads(PREVIOUS_GRID.read_text("utf8")) if prior_grid is None else prior_grid
    if grid.get("universe_sha256") != hashlib.sha256(raw_universe).hexdigest():
        raise SourceError("Canonical 196-country universe differs from existing research")
    if stability.get("status") != "POST_SELECTION_SOURCE_REVISION_SENSITIVITY_NOT_PROSPECTIVE":
        raise SourceError("Prior May-label stability report has unexpected status")
    pins = candidate_registry_pins(registry)
    fixed_annual = ANNUAL_ZIP_SHA if annual_pins is None else annual_pins
    if set(fixed_annual) != set(YEARS) or any(
            not isinstance(fixed_annual[y],str) or len(fixed_annual[y])!=64 for y in YEARS):
        raise SourceError("Annual GED original ZIP hashes must be fixed before comparing outcomes")

    source_details = []
    all_metrics = {}
    focus_country_changes = []
    country_vectors = []
    id_checks = {}
    for year in YEARS:
        q = {}
        for month in (3,6,9):
            source_url = archive_url(year, month) if month!=6 else url_for(year,2)
            raw = candidate_fetcher(source_url)
            sha = hashlib.sha256(raw).hexdigest()
            if sha != pins[(year,month)]:
                raise SourceError(f"Candidate historical source SHA mismatch: {year}m{month}")
            meta, e = candidate_with_status(raw, year, month, set(names))
            q[month] = e
            source_details.append({"source_family":"Candidate","year":year,"month":month,
                "url":source_url, "sha256":sha, "bytes":len(raw), "metadata":meta})
        ged_raw = annual_fetcher(GED_URL[year])
        ged_sha = hashlib.sha256(ged_raw).hexdigest()
        if ged_sha != fixed_annual[year]:
            raise SourceError(f"Annual GED ZIP SHA does not match fixed source census: {year}")
        meta, annual_events, annual_id_year = read_annual(ged_raw, year, set(names))
        source_details.append({"source_family":"annual_GED","year":year,
            "version":"25.1" if year==2024 else "26.1",
            "url":GED_URL[year],"sha256":ged_sha,"bytes":len(ged_raw),"metadata":meta})
        prior=prior_sums(q[3],year)
        rollups={}
        selected_ids={}
        coding={}
        for source,events in (("q2",q[6]),("q3",q[9]),("annual",annual_events)):
            rollups[source]={}
            selected_ids[source]={}
            coding[source]={}
            for h in (30,90) if source!="q2" else (30,):
                p, ids, status_deaths = rollup(events,year,h)
                rollups[source][h]=p
                selected_ids[source][h]=ids
                coding[source][h]=status_deaths
        compare={}
        for t in THRESHOLDS:
            compare[str(t)]={}
            for h in HORIZONS:
                result={"q3_vs_annual":paired_metrics(
                    prior,rollups["q3"][h],rollups["annual"][h],t,names
                )}
                if h==30:
                    result["q2_vs_annual"]=paired_metrics(
                        prior,rollups["q2"][30],rollups["annual"][30],t,names
                    )
                compare[str(t)][str(h)]=result
                expected_rate = grid["yearly_threshold_rates"][str(t)][str(h)][str(year)]
                observed=paired_metrics(prior,rollups["q3"][h],rollups["annual"][h],t,names)
                if expected_rate["at_risk"]!=observed["n_at_risk"] or expected_rate["positive"]!=observed["candidate_positive"]:
                    raise SourceError(f"Q3 Candidate cohort drift against preregistered threshold grid {year} T={t} H={h}")
        year_stability=next((x for x in stability["may_label_revision_by_year"] if x["year"]==year),None)
        if year_stability is None:
            raise SourceError("Missing prior fixed label report for this year")
        expected=year_stability["thresholds"]["5"]
        for key,col in (("q2","q2"),("q3","q3")):
            got=sorted(c for c in names if prior[c]<5 and rollups[key][30][c]>=5)
            if got != expected[col+"_positive_country_ids"]:
                raise SourceError("Same official Candidate May five-death labels changed from prior audit")
        all_metrics[str(year)]=compare
        id_checks[str(year)]=matching_event_ids(
            selected_ids["q3"][30],annual_id_year,selected_ids["annual"][30],names
        )
        for country,name in names.items():
            details={
                "year":year, "country_id":country,"country":name,
                "candidate_q1_prior_best":prior[country],
                "candidate_q2_may30_best":rollups["q2"][30][country],
                "candidate_q3_may30_best":rollups["q3"][30][country],
                "candidate_q3_90_best":rollups["q3"][90][country],
                "ged_annual_may30_best":rollups["annual"][30][country],
                "ged_annual_90_best":rollups["annual"][90][country],
            }
            country_vectors.append(details)
            if prior[country]<5 and (
                rollups["q2"][30][country]>=5 or rollups["q3"][30][country]>=5
                or rollups["annual"][30][country]>=5
            ):
                focus_country_changes.append({**details,
                    "q3_candidate_may30_code_status_best":dict(
                        sorted(coding["q3"][30][country].items())),
                    "q3_candidate_may30_event_count":len(selected_ids["q3"][30][country]),
                    "candidate_q3_may30_exact_id_present_in_ged_any":sum(
                        id_ in annual_id_year for id_ in selected_ids["q3"][30][country]
                    ),
                    "candidate_q3_may30_exact_id_present_in_ged_window":sum(
                        id_ in selected_ids["annual"][30][country] for id_ in selected_ids["q3"][30][country]
                    ),
                })
    return {
        "schema":"idealab.psico.candidate_to_annual_ged_resolution.v1",
        "status":"RETROSPECTIVE_FINAL_VINTAGE_COMPARISON_NOT_PROSPECTIVE",
        "fixed_design_date":"2026-11-20",
        "annual_version_by_year":{"2024":"GED 25.1","2025":"GED 26.1"},
        "country_universe_sha256":hashlib.sha256(raw_universe).hexdigest(),
        "n_countries":len(names),"years":list(YEARS),
        "thresholds":list(THRESHOLDS),"horizons":list(HORIZONS),
        "window_30":"May 1-30","window_90":"May 1-Jul 29",
        "source_details":source_details,
        "by_year_threshold_and_horizon":all_metrics,
        "candidate_q3_may_exact_id_overlap_with_annual":id_checks,
        "may30_t5_countries_positive_in_any_source":sorted(focus_country_changes,key=lambda x:(x["year"],x["country_id"])),
        "country_vectors":sorted(country_vectors,key=lambda x:(x["year"],x["country_id"])),
        "annual_original_archive_sha_pinned_before_scoring":True,
        "original_candidate_release_dates_verified":False,
        "prospective_issued_probabilities":0,
        "cohorts_modified":0,
        "interpretation":(
            "GED 25.1 and GED 26.1 annual releases are different target vintages "
            "from Candidate and may apply different inclusion rules. Candidate may include "
            "subthreshold dyads. Country-level label retention, not exact event confirmation; "
            "a missing matching event ID can reflect recoding/splitting/merging. "
            "No real as-of or prospective skill claim; 2026 annual GED not yet available."
        ),
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--source-census",action="store_true")
    mode.add_argument("--print-report",action="store_true")
    mode.add_argument("--check-report",action="store_true")
    args=parser.parse_args(argv)
    try:
        if args.source_census:
            print(json.dumps(annual_census(),indent=2,sort_keys=True,ensure_ascii=False))
            return 0
        report=build_report()
        if args.print_report:
            print(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False))
        else:
            frozen=json.loads(REPORT.read_text("utf8"))
            if frozen!=report:
                raise SourceError("Frozen Candidate→GED annual report disagrees with source replay")
            print("OK: six Candidate SHA and two GED ZIP SHA, 2024/25 threshold labels reproduced")
    except (SourceError,OSError,ValueError,TypeError,KeyError,TimeoutError) as exc:
        print(f"BLOCKED: {exc}",file=sys.stderr)
        return 2
    return 0


if __name__=="__main__":
    sys.exit(main())
