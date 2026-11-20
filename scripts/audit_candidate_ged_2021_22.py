#!/usr/bin/env python3
"""Candidate-to-GED annual reconciliation 2021/22, then four-year summary.

Prospective forecasts ISSUED=0. First official annual GED version per year.
Two-stage: --source-census (SHA only), then pin SHA, then --print/--check.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, timedelta
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
import urllib.request
import zipfile

from check_ucdp_candidate_asof import SourceError, ged_day
from audit_candidate_q2_q3_vintages import get_source
from audit_candidate_to_annual_ged import (
    examine_zip, rollup, prior_sums, paired_metrics, matching_event_ids,
)
from experiment_candidate_30_90_holdout import universe_from_bytes
from experiment_candidate_reactivation_grid import source_url

ROOT = Path(__file__).resolve().parents[1]
YEARS = (2021, 2022)
THRESHOLDS = (1, 5, 10, 25)
HORIZONS = (30, 90)
ORIGINAL_ZIP_URLS = {
    2021: "https://ucdp.uu.se/downloads/ged/ged221-csv.zip",
    2022: "https://ucdp.uu.se/downloads/ged/ged231-csv.zip",
}
ZIP_VERSIONS = {2021: "22", 2022: "23"}
# To be filled ONLY after source census records original ZIP hash, no outcome scan.
ZIP_SHA = {2021: None, 2022: None}
GRID_FILE = ROOT / "data/candidate-reactivation-threshold-grid.json"
PREVIOUS_ANNUAL = ROOT / "data/candidate-to-annual-ged-resolution.json"
UNIVERSE = ROOT / "data/forecast-2027-ucdp261.json"
REPORT = ROOT / "data/candidate-ged-2021-22-resolution.json"
MAX_ARCHIVE_BYTES = 110_000_000
MAX_CSV_UNCOMPRESSED = 750_000_000


def get_annual_zip(url):
    if url not in ORIGINAL_ZIP_URLS.values():
        raise SourceError("Unregistered GED archive URL")
    request = urllib.request.Request(
        url, headers={"User-Agent":"IDEA-LAB-institutional-science-audit/1.0"}
    )
    content = []
    total = 0
    with urllib.request.urlopen(request, timeout=120) as response:
        if response.url != url:
            raise SourceError("GED archive redirect differs from fixed UCDP URL")
        while True:
            part = response.read(1024 * 1024)
            if not part:
                break
            total += len(part)
            if total > MAX_ARCHIVE_BYTES:
                raise SourceError("Annual ZIP exceeded fixed compressed limit")
            content.append(part)
    raw = b"".join(content)
    examine_zip(raw)
    return raw


def source_census(annual_fetcher=get_annual_zip):
    manifest = []
    for year in YEARS:
        raw = annual_fetcher(ORIGINAL_ZIP_URLS[year])
        members = examine_zip(raw)
        manifest.append({
            "year":year, "url":ORIGINAL_ZIP_URLS[year],
            "sha256":hashlib.sha256(raw).hexdigest(), "zip_bytes":len(raw),
            "members":members,
        })
    return {
        "schema":"idealab.psico.ged_21_22_source_census.v1",
        "status":"SOURCES_ONLY_NO_GED_OUTCOMES_READ",
        "manifest":manifest,
    }


def scan_candidate(raw, year, month, countries):
    if year not in YEARS or month not in (3, 9):
        raise SourceError("Out-of-protocol Candidate vintage")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    required = {"id","country_id","type_of_violence","date_prec",
                "date_start","date_end","best","code_status"}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise SourceError("Candidate Q1/Q3 historical source schema invalid")
    used, counts, result = set(), Counter(), []
    year_start, origin_end = date(year,1,1), date(year,3,31)
    target_start, target_end = date(year,5,1), date(year,7,29)
    for row in reader:
        counts["source_rows"] += 1
        eid = (row.get("id") or "").strip()
        if not eid or eid in used:
            raise SourceError("Candidate event ID empty/duplicate")
        used.add(eid)
        try:
            country = int(row["country_id"])
            typ = int(row["type_of_violence"])
            prec = int(row["date_prec"])
            deaths = int(row["best"])
        except (TypeError,ValueError) as exc:
            raise SourceError("Invalid mandatory Candidate numeric code") from exc
        if country <= 0 or typ not in (1,2,3) or prec not in (0,1,2,3,4,5) or deaths < 0:
            raise SourceError("Bad Candidate violence/date/fatality coding")
        start, end = ged_day(row["date_start"], "start"), ged_day(row["date_end"], "end")
        if start > end:
            raise SourceError("Candidate reversed event dates")
        if typ != 1:
            counts["skip_nonstate"] += 1
            continue
        if prec not in (1,2):
            counts["skip_date_precision"] += 1
            counts["skip_unknown_precision_zero"] += int(prec==0)
            continue
        if country not in countries:
            counts["skip_outside_196"] += 1
            continue
        if month==3 and not (year_start <= start and end <= origin_end):
            counts["skip_outside_q1"] += 1
            continue
        if month==9 and not (target_start <= start and end <= target_end):
            counts["skip_outside_may_july"] += 1
            continue
        result.append((eid,country,start,end,deaths,(row.get("code_status") or "").strip().casefold() or "(blank)"))
        counts["eligible_events"] += 1
    if not counts["source_rows"]:
        raise SourceError("Empty Candidate vintage")
    return dict(sorted(counts.items())), result


def scan_annual_zip(raw, year, countries):
    if year not in YEARS:
        raise SourceError("Unexpected annual year")
    examine_zip(raw)
    years = {2021:22, 2022:23}
    meta = Counter()
    ids = {}
    accepted = []
    with zipfile.ZipFile(io.BytesIO(raw),"r") as zipped:
        members = [x for x in zipped.infolist()
                   if re.fullmatch(f"GEDEvent_v{years[year]}_1\\.csv",
                                   PurePosixPath(x.filename).name,re.IGNORECASE)]
        if len(members) != 1 or members[0].file_size > MAX_CSV_UNCOMPRESSED:
            raise SourceError("Expected single historical GED event CSV in official ZIP")
        member = members[0]
        with zipped.open(member) as stream:
            reader = csv.DictReader(io.TextIOWrapper(stream,encoding="utf-8-sig",newline=""))
            required={"id","year","country_id","type_of_violence","date_prec","date_start","date_end","best"}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise SourceError("GED annual CSV schema missing required fields")
            for row in reader:
                meta["source_rows"] += 1
                try:
                    rowyear=int(row["year"])
                except (ValueError,TypeError) as exc:
                    raise SourceError("GED annual event year unparsable") from exc
                if rowyear != year:
                    continue
                meta["target_year_rows"] += 1
                eid=(row.get("id") or "").strip()
                if not eid or eid in ids:
                    raise SourceError("Duplicate/blank GED target-year event ID")
                try:
                    country=int(row["country_id"])
                    typ=int(row["type_of_violence"])
                    precision=int(row["date_prec"])
                    deaths=int(row["best"])
                except (ValueError,TypeError) as exc:
                    raise SourceError("GED annual event coding unusable") from exc
                if country <= 0 or typ not in (1,2,3) or precision not in (0,1,2,3,4,5) or deaths < 0:
                    raise SourceError("GED annual event invalid code/fatalities")
                beginning=ged_day(row["date_start"], "date_start")
                ending=ged_day(row["date_end"], "date_end")
                if beginning > ending:
                    raise SourceError("GED annual event dates reversed")
                ids[eid]=(country,typ,beginning,ending)
                if typ!=1:
                    meta["skip_nonstate"] += 1
                    continue
                if precision not in (1,2):
                    meta["skip_date_precision"] += 1
                    continue
                if country not in countries:
                    meta["skip_outside_196"] += 1
                    continue
                if beginning < date(year,5,1) or ending > date(year,7,29):
                    meta["skip_outside_may_july"] += 1
                    continue
                accepted.append((eid,country,beginning,ending,deaths,"annual GED"))
                meta["eligible_state_events_may_july"] += 1
    if not meta["target_year_rows"]:
        raise SourceError("No annual target-year GED events found")
    return {
        "zip_member": member.filename,
        "member_bytes": member.file_size,
        **dict(sorted(meta.items())),
    }, accepted, ids


def validate_source_pins(grid):
    if grid.get("status") != "EXPLORATORY_HISTORICAL_NOT_ASOF_NOT_ISSUED":
        raise SourceError("Prerequisite Candidate Q1/Q3 original grid status differs")
    pins={}
    for info in grid["source_snapshots"]:
        if info["year"] not in YEARS:
            continue
        key=(info["year"],info["month"])
        if key in pins or info["source_url"] != source_url(*key) or len(info["sha256"])!=64:
            raise SourceError("Historical Candidate original source not valid")
        pins[key]=info
    if set(pins)!={(year,month) for year in YEARS for month in (3,9)}:
        raise SourceError("Need exactly four frozen 2021/22 Candidate original files")
    return pins


def summary_metrics(year, prior, candidate, annual, names, grid):
    result={}
    for t in THRESHOLDS:
        result[str(t)]={}
        for h in HORIZONS:
            sums_q3,_,_=rollup(candidate,year,h)
            sums_annual,_,_=rollup(annual,year,h)
            paired=paired_metrics(prior,sums_q3,sums_annual,t,names)
            expected=grid["yearly_threshold_rates"][str(t)][str(h)][str(year)]
            if paired["n_at_risk"]!=expected["at_risk"] or paired["candidate_positive"]!=expected["positive"]:
                raise SourceError(f"Preexisting candidate result drift year={year} T={t} H={h}")
            result[str(t)][str(h)]={"candidate_q3_vs_annual":paired}
    return result


def build_report(cand_fetcher=get_source, ged_fetcher=get_annual_zip,
                 grid=None, previous=None, universe=None, annual_pins=None):
    grid=json.loads(GRID_FILE.read_text("utf8")) if grid is None else grid
    previous=json.loads(PREVIOUS_ANNUAL.read_text("utf8")) if previous is None else previous
    universe=UNIVERSE.read_bytes() if universe is None else universe
    if hashlib.sha256(universe).hexdigest()!=grid["universe_sha256"]:
        raise SourceError("Canonical 196-country universe SHA no longer matches grid")
    if previous.get("status")!="RETROSPECTIVE_FINAL_VINTAGE_COMPARISON_NOT_PROSPECTIVE":
        raise SourceError("Previously published 2024/25 GED report status invalid")
    names=dict(universe_from_bytes(universe))
    pins=validate_source_pins(grid)
    annual_pins=ZIP_SHA if annual_pins is None else annual_pins
    if set(annual_pins)!=set(YEARS) or any(not isinstance(annual_pins[y],str) or len(annual_pins[y])!=64 for y in YEARS):
        raise SourceError("Annual GED 2021/22 original ZIP SHA must be frozen after source census")
    source_records=[]
    rates={}
    cases=[]
    vectors=[]
    id_overlap={}
    for year in YEARS:
        cand={}
        for month in (3,9):
            original=pins[(year,month)]
            raw=cand_fetcher(original["source_url"])
            digest=hashlib.sha256(raw).hexdigest()
            if digest!=original["sha256"] or len(raw)!=original["source_bytes"]:
                raise SourceError("Original Candidate source bytes changed from preregistered grid")
            meta, events=scan_candidate(raw,year,month,set(names))
            cand[month]=events
            source_records.append({"family":"candidate","year":year,"month":month,
                    "url":original["source_url"],"sha256":digest,"bytes":len(raw),"audit":meta})
        raw_ged=ged_fetcher(ORIGINAL_ZIP_URLS[year])
        ged_sha=hashlib.sha256(raw_ged).hexdigest()
        if ged_sha!=annual_pins[year]:
            raise SourceError("Official annual GED ZIP original SHA has changed")
        ged_meta,annual,year_index=scan_annual_zip(raw_ged,year,set(names))
        source_records.append({"family":"annual_GED","year":year,
            "version":ZIP_VERSIONS[year]+".1","url":ORIGINAL_ZIP_URLS[year],
            "sha256":ged_sha,"bytes":len(raw_ged),"audit":ged_meta})
        origin=prior_sums(cand[3],year)
        rates[str(year)]=summary_metrics(year,origin,cand[9],annual,names,grid)
        cand30,cand_ids,codes=rollup(cand[9],year,30)
        annual30,annual_ids,_=rollup(annual,year,30)
        cand90,_,_=rollup(cand[9],year,90)
        annual90,_,_=rollup(annual,year,90)
        id_overlap[str(year)]=matching_event_ids(cand_ids,year_index,annual_ids,names)
        for country,name in names.items():
            detail={"year":year,"country_id":country,"country":name,
                "q1_candidate_best":origin[country],
                "q3_candidate_may30_best":cand30[country],
                "annual_ged_may30_best":annual30[country],
                "q3_candidate_may90_best":cand90[country],
                "annual_ged_may90_best":annual90[country]}
            vectors.append(detail)
            if origin[country]<5 and (cand30[country]>=5 or annual30[country]>=5):
                cases.append({
                    **detail,
                    "candidate_q3_may30_code_status_best":dict(sorted(codes[country].items())),
                    "candidate_q3_may30_events":len(cand_ids[country]),
                    "candidate_exact_id_in_annual_any_type_window":sum(i in year_index for i in cand_ids[country]),
                    "candidate_exact_id_in_annual_same_country_window":sum(i in annual_ids[country] for i in cand_ids[country])
                })
    # Extend exactly, without recomputing or replacing 2024/25.
    combined={}
    years=list(YEARS)+[2024,2025]
    for threshold in THRESHOLDS:
        t=str(threshold);combined[t]={}
        for horizon in HORIZONS:
            h=str(horizon)
            table=[(str(year),rates[str(year)][t][h]["candidate_q3_vs_annual"]) for year in YEARS]
            table += [(str(year),previous["by_year_threshold_and_horizon"][str(year)][t][h]["q3_vs_annual"]) for year in (2024,2025)]
            expected_cols=("n_at_risk","candidate_positive","ged_positive","both_positive",
                "candidate_only","ged_only","both_negative","disagreements")
            aggregate={k:sum(row[k] for _,row in table) for k in expected_cols}
            aggregate["candidate_positive_matching_ged_share"]=(
                round(aggregate["both_positive"]/aggregate["candidate_positive"],8)
                if aggregate["candidate_positive"] else None)
            aggregate["candidate_sensitivity_to_ged_label"]=(
                round(aggregate["both_positive"]/aggregate["ged_positive"],8)
                if aggregate["ged_positive"] else None)
            aggregate["annual_breakdown"]={
                yr:{k:row[k] for k in expected_cols} for yr,row in table
            }
            combined[t][h]=aggregate
    return {
        "schema":"idealab.psico.candidate_ged_2021_22_extension.v1",
        "status":"ARCHIVED_FIRST_ANNUAL_GED_LABEL_RESOLUTION_NOT_ASOF",
        "design_date":"2026-11-20",
        "years_new":list(YEARS),"years_pooled":years,
        "ged_annual_versions":{"2021":"22.1","2022":"23.1","2024":"25.1","2025":"26.1"},
        "source_provenance":source_records,
        "source_universe_sha256":hashlib.sha256(universe).hexdigest(),
        "source_prev_2024_25_sha256":hashlib.sha256(
            PREVIOUS_ANNUAL.read_bytes() if previous is None
            else json.dumps(previous,ensure_ascii=False,sort_keys=True).encode("utf8")).hexdigest(),
        "n_countries":len(names),
        "years_new_by_threshold_horizon":rates,
        "country_vectors_new":sorted(vectors,key=lambda x:(x["year"],x["country_id"])),
        "primary_t5_may30_2021_22_changed_cases":sorted(cases,key=lambda x:(x["year"],x["country_id"])),
        "eligible_may_candidate_id_matches_annual":id_overlap,
        "pooled_2021_22_24_25_results":combined,
        "new_prospective_issues":0,"prospective_cohorts_changed":0,
        "candidate_original_release_dates_certified":False,
        "conclusions_scope":(
            "Retrospective country-level Candidate vs first annual GED vintage label "
            "comparison, four highly dependent country-year cohorts. Provisional versus "
            "annual thresholds are different outcomes; IDs can be recoded/split/removed. "
            "Cannot infer new conflict onset or predictive validity; 2026 unresolved."
        )
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--source-census",action="store_true")
    modes.add_argument("--print-report",action="store_true")
    modes.add_argument("--check-report",action="store_true")
    args=parser.parse_args(argv)
    try:
        if args.source_census:
            print(json.dumps(source_census(),indent=2,sort_keys=True,ensure_ascii=False))
        else:
            report=build_report()
            if args.print_report:
                print(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False))
            else:
                frozen=json.loads(REPORT.read_text("utf8"))
                if frozen!=report:
                    raise SourceError("Four-year Candidate-to-GED source replay differs from frozen findings")
                print("OK: four 2021/22 Candidate original CSV and GED22.1/23.1 ZIP SHA, four-year pooled labels reproduced")
    except (SourceError,ValueError,TypeError,KeyError,OSError,TimeoutError,UnicodeError,zipfile.BadZipFile) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 2
    return 0


if __name__=="__main__":
    sys.exit(main())
