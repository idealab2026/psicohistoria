#!/usr/bin/env python3
"""Independent official UCDP Dyadic dyad-year vs Candidate Q3 event reconciliation.

Historical/postselected only. --source-census inventories ZIP SHA/headers first.
After pinning originals, --print-report or --check-report replays exact data.
Never publicly emit raw dyad or event IDs.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
import urllib.request
import zipfile

from check_ucdp_candidate_asof import SourceError
from audit_candidate_q2_q3_vintages import get_source
from audit_candidate_to_annual_ged import examine_zip
from audit_candidate_ged_event_dyad_fates import (
    candidate_focus, parse_event, eligible
)

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / "data/candidate-ged-event-dyad-fates.json"
REPORT = ROOT / "data/ucdp-official-dyadyear-case-resolution.json"
YEARS = (2021, 2022, 2024, 2025)
EDITIONS = {2021:"221",2022:"231",2024:"251",2025:"261"}
ORIGINAL_URLS = {
    y:f"https://ucdp.uu.se/downloads/dyadic/ucdp-dyadic-{EDITIONS[y]}-csv.zip"
    for y in YEARS
}
ZIP_SHA = {2021:None,2022:None,2024:None,2025:None}  # pin AFTER census only
MAX_BYTES = 50_000_000
MAX_UNCOMPRESSED = 300_000_000


def fetch_dyadic_zip(url):
    if url not in ORIGINAL_URLS.values():
        raise SourceError("Unregistered UCDP Dyadic ZIP original")
    request=urllib.request.Request(
        url,headers={"User-Agent":"IDEA-LAB-institutional-science-audit/1.0"})
    chunks=[]
    n=0
    with urllib.request.urlopen(request,timeout=90) as response:
        if response.url != url:
            raise SourceError("Official dyad ZIP unexpected redirect")
        while True:
            buf=response.read(1024*1024)
            if not buf:
                break
            n+=len(buf)
            if n>MAX_BYTES:
                raise SourceError("Dyadic original ZIP exceeds size cap")
            chunks.append(buf)
    data=b"".join(chunks)
    examine_zip(data)
    return data


def identify_csv_member(raw):
    examine_zip(raw)
    if len(raw)>MAX_BYTES:
        raise SourceError("Dyadic ZIP exceeds study limit")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        csv_files=[m for m in z.infolist()
            if PurePosixPath(m.filename).suffix.casefold()==".csv"
            and not m.is_dir()]
        if len(csv_files)!=1 or csv_files[0].file_size>MAX_UNCOMPRESSED:
            raise SourceError("Expected exactly one Dyadic original CSV in ZIP")
        file=csv_files[0]
        with z.open(file) as inner:
            reader=csv.reader(io.TextIOWrapper(inner,encoding="utf-8-sig",newline=""))
            fields=next(reader,None)
        if not fields or "year" not in fields or "dyad_id" not in fields:
            raise SourceError("Dyadic ZIP original CSV lacks expected dyad_id/year header")
        return {"member":file.filename,"csv_bytes":file.file_size,"columns":fields}


def source_census(fetcher=fetch_dyadic_zip):
    out=[]
    for year in YEARS:
        blob=fetcher(ORIGINAL_URLS[year])
        info=identify_csv_member(blob)
        out.append({"year":year,"edition":EDITIONS[year],
            "url":ORIGINAL_URLS[year],"zip_sha256":hashlib.sha256(blob).hexdigest(),
            "zip_bytes":len(blob),"csv_header_only":info})
    return {"schema":"idealab.psico.ucdp_dyadic_source_census.v1",
        "status":"SOURCE_ONLY_CENSUS_NO_DYADYEAR_OUTCOMES_READ",
        "source_count":4,"sources":out}


def parse_dyadic_year(raw,event_year):
    info=identify_csv_member(raw)
    seen=set()
    all_dyads=set()
    active=set()
    available=Counter()
    values_for_year=0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        with z.open(info["member"]) as inner:
            reader=csv.DictReader(io.TextIOWrapper(inner,encoding="utf-8-sig",newline=""))
            for row in reader:
                try:
                    dyad=int((row.get("dyad_id") or "").strip())
                    y=int((row.get("year") or "").strip())
                except (TypeError,ValueError) as exc:
                    raise SourceError("Official Dyadic ZIP contains invalid dyad_id/year") from exc
                if dyad<=0 or y<=0:
                    raise SourceError("Nonpositive Dyadic record identifier/year")
                pair=(dyad,y)
                if pair in seen:
                    raise SourceError("Dyadic ZIP has duplicated dyad-year")
                seen.add(pair)
                all_dyads.add(dyad)
                if y==event_year:
                    values_for_year+=1
                    active.add(dyad)
                    for col in ("conflict_id","side_a_id","side_b_id"):
                        if col in row and (row[col] or "").strip():
                            available[col]+=1
    if not values_for_year:
        raise SourceError("Historical Dyadic original edition lacks target year")
    return {"edition":EDITIONS[event_year],"year":event_year,
        "source_rows":len(seen),"target_year_rows":values_for_year,
        "n_unique_dyads_in_archive":len(all_dyads),
        "fields_nonblank_target_year":dict(sorted(available.items())),
        "csv_member":info["member"]},active,all_dyads


def numeric_dyad(value):
    raw=(value or "").strip()
    if not raw:
        return None
    try:
        result=int(raw)
    except (ValueError,TypeError):
        return None
    return result if result>0 else None


def candidate_q3_year_by_dyad(raw,year,allow_dyads):
    """Q3 Jan-Sep sum for only case-dyads; never substitute for annual BRD."""
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    if not reader.fieldnames or not {
        "id","country_id","type_of_violence","date_prec","date_start",
        "date_end","best","dyad_new_id"
    }.issubset(reader.fieldnames):
        raise SourceError("Candidate Q3 lacks essential original dyad/coding fields")
    candidates=defaultdict(int)
    candidate_events=Counter()
    for row in reader:
        e=parse_event(row,year=year)
        dyad=numeric_dyad(e["dyad"])
        if (dyad in allow_dyads and e["violence"]==1 and e["precision"] in (1,2)
            and date(year,1,1)<=e["start"] and e["end"]<=date(year,9,30)):
            candidates[dyad]+=e["best"]
            candidate_events[dyad]+=1
    return candidates,candidate_events


def analyze_case(case,events,active,ever,jan_sep):
    year,country=case["year"],case["country_id"]
    if (len(events)!=case["candidate_n_eligible_events"]
        or sum(v["best"] for v in events)!=case["candidate_q3_best"]
        or case["retained_ged_threshold_5"]!=(case["ged_first_annual_best"]>=5)):
        raise SourceError("Candidate May case does not match frozen #155")
    status=Counter()
    by_dyad=defaultdict(lambda:{"best":0,"events":0,"statuses":Counter()})
    missing=0
    for ev in events:
        status[ev["status"]]+=ev["best"]
        dyad=numeric_dyad(ev["dyad"])
        if dyad is None:
            missing+=1
        else:
            d=by_dyad[dyad]
            d["best"]+=ev["best"]
            d["events"]+=1
            d["statuses"][ev["status"]]+=ev["best"]
    if dict(sorted(status.items()))!=case["candidate_code_status_best"]:
        raise SourceError("Candidate code-status mismatch against SHA-frozen #155")
    n_active=n_absent=n_ever_outside=0
    events_active=events_absent=0
    best_active=best_absent=0
    status_activity=defaultdict(lambda:Counter())
    jan_sep_active=jan_sep_absent=0
    dyad_with_candidate_jansep_ge25=0
    for dyad,agg in by_dyad.items():
        eligible_year=dyad in active
        if eligible_year:
            n_active+=1
            events_active+=agg["events"]
            best_active+=agg["best"]
            jan_sep_active+=jan_sep.get(dyad,0)
            status_activity["dyadic_annual_active"].update(agg["statuses"])
        else:
            n_absent+=1
            n_ever_outside+=int(dyad in ever)
            events_absent+=agg["events"]
            best_absent+=agg["best"]
            jan_sep_absent+=jan_sep.get(dyad,0)
            status_activity["not_active_same_year"].update(agg["statuses"])
        dyad_with_candidate_jansep_ge25+=int(jan_sep.get(dyad,0)>=25)
    if (best_active+best_absent+sum(e["best"] for e in events if numeric_dyad(e["dyad"]) is None)
        !=case["candidate_q3_best"]):
        raise SourceError("Dyadic-year May death attribution not exactly reconciled")
    if len(by_dyad)!=n_active+n_absent or missing+events_active+events_absent!=len(events):
        raise SourceError("Dyadic-year May event partition did not reconcile")
    return {
        "year":year,"country_id":country,"country":case["country"],
        "retained_ged_threshold_5":case["retained_ged_threshold_5"],
        "candidate_q3_best":case["candidate_q3_best"],
        "ged_first_annual_best":case["ged_first_annual_best"],
        "n_candidate_may_events":len(events),
        "n_candidate_may_events_unavailable_dyad":missing,
        "n_distinct_candidate_may_dyads_with_valid_ids":len(by_dyad),
        "n_distinct_candidate_may_dyads_active_in_original_dyadic_year":n_active,
        "n_distinct_candidate_may_dyads_not_active_in_original_dyadic_year":n_absent,
        "n_distinct_candidate_may_dyads_not_active_that_appear_in_dyadic_other_year":n_ever_outside,
        "candidate_may_events_active_dyads":events_active,
        "candidate_may_events_inactive_dyads":events_absent,
        "candidate_may_best_active_dyads":best_active,
        "candidate_may_best_inactive_dyads":best_absent,
        "candidate_q3_jan_sep_best_active_dyads":jan_sep_active,
        "candidate_q3_jan_sep_best_inactive_dyads":jan_sep_absent,
        "n_candidate_q3_jan_sep_dyads_ge25_best":dyad_with_candidate_jansep_ge25,
        "candidate_may_code_status_best_by_dyadic_activity":{
            k:dict(sorted(v.items())) for k,v in sorted(status_activity.items())
        },
        "no_identifiers_published":True
    }


def build_report(candidate_fetch=get_source,dyadic_fetch=fetch_dyadic_zip,
                 prior_raw=None,pins=None):
    prior_raw=PREVIOUS.read_bytes() if prior_raw is None else prior_raw
    prior=json.loads(prior_raw)
    if (prior.get("status")!="RETROSPECTIVE_POSTSELECTED_EVENT_ID_DIAGNOSTICS_NO_FORECAST"
        or prior.get("n_cases")!=10 or prior.get("n_cases_retained_in_ged")!=5
        or prior.get("n_population_at_risk")!=642):
        raise SourceError("Prior ten-case research has not been verified")
    fixed=ZIP_SHA if pins is None else pins
    if set(fixed)!=set(YEARS) or any(
        not isinstance(fixed[y],str) or len(fixed[y])!=64 for y in YEARS):
        raise SourceError("Original Dyadic ZIP source SHA not fixed after census")
    cases=prior["case_level_aggregates"]
    if len(cases)!=10 or len({(x["year"],x["country_id"]) for x in cases})!=10:
        raise SourceError("Missing/duplicated ten cases")
    cohort=[]
    manifest=[]
    for year in YEARS:
        focus={c["country_id"]:c for c in cases if c["year"]==year}
        if not focus:
            raise SourceError("No previously registered Candidate case for year")
        original=next((x["candidate_q3"] for x in prior["original_archive_provenance"] if x["year"]==year),None)
        if original is None:
            raise SourceError("Missing previous original Candidate source manifest")
        raw=candidate_fetch(original["url"])
        if len(raw)!=original["bytes"] or hashlib.sha256(raw).hexdigest()!=original["sha256"]:
            raise SourceError("Frozen original Candidate Q3 URL/bytes/SHA drifted")
        cmeta,countries=candidate_focus(raw,year,focus)
        if not cmeta["has_dyad_new_id"]:
            raise SourceError("UCDP Candidate Q3 lacks dyad_new_id")
        blob=dyadic_fetch(ORIGINAL_URLS[year])
        sha=hashlib.sha256(blob).hexdigest()
        if sha!=fixed[year]:
            raise SourceError("Official UCDP Dyadic archive original SHA drifted")
        info,active,ever=parse_dyadic_year(blob,year)
        dyads=set()
        for values in countries.values():
            dyads.update(dyad for e in values if (dyad:=numeric_dyad(e["dyad"])) is not None)
        jan_sep,_=candidate_q3_year_by_dyad(raw,year,dyads)
        for country,case in focus.items():
            cohort.append(analyze_case(case,countries.get(country,[]),active,ever,jan_sep))
        manifest.append({"year":year,"candidate_q3_sha256":original["sha256"],
            "dyadic_original_zip_sha256":sha,"dyadic_original_url":ORIGINAL_URLS[year],
            "dyadic_zip_bytes":len(blob),"dyadic_audit":info,
            "candidate_events_in_all_focus_countries":cmeta["eligible_focus_events"]})
    cohort.sort(key=lambda x:(x["year"],x["country_id"]))
    if len(cohort)!=10 or sum(x["retained_ged_threshold_5"] for x in cohort)!=5:
        raise SourceError("Previously fixed country labels did not reproduce")
    strata={}
    for name,subset in (("retained",[x for x in cohort if x["retained_ged_threshold_5"]]),
                        ("lost",[x for x in cohort if not x["retained_ged_threshold_5"]]),
                        ("all",cohort)):
        strata[name]={
            "n_country_years":len(subset),
            "n_country_years_with_any_original_dyad_active":sum(
                x["n_distinct_candidate_may_dyads_active_in_original_dyadic_year"]>0 for x in subset),
            "n_country_years_with_no_original_dyad_active":sum(
                x["n_distinct_candidate_may_dyads_active_in_original_dyadic_year"]==0 for x in subset),
            "n_distinct_original_candidate_dyads_active":sum(
                x["n_distinct_candidate_may_dyads_active_in_original_dyadic_year"] for x in subset),
            "n_distinct_original_candidate_dyads_inactive":sum(
                x["n_distinct_candidate_may_dyads_not_active_in_original_dyadic_year"] for x in subset),
            "candidate_may_best_on_active_dyads":sum(x["candidate_may_best_active_dyads"] for x in subset),
            "candidate_may_best_on_inactive_dyads":sum(x["candidate_may_best_inactive_dyads"] for x in subset),
            "n_candidate_events_without_numeric_dyad":sum(
                x["n_candidate_may_events_unavailable_dyad"] for x in subset),
        }
    return {
        "schema":"idealab.psico.ucdp_dyadic_year_inclusion_v1",
        "status":"POSTSELECTED_OFFICIAL_DYADYEAR_LABEL_CHECK_NOT_FORECAST",
        "design_date":"2026-11-24",
        "source_previous_event_fate_sha256":hashlib.sha256(prior_raw).hexdigest(),
        "n_original_csv_sources":4,"n_original_dyadic_zip_sources":4,
        "source_provenance":manifest,
        "case_level_country_aggregates":cohort,
        "retention_strata":strata,
        "annual_dyadic_activity_definition":"25 battle-related deaths per dyad per calendar year (official first annual edition)",
        "candidate_q3_partial_jan_sep_best_not_annual_brd":True,
        "dyad_missing_or_unmatched_is_not_proof_of_absence_of_real_violence":True,
        "new_forecasts_issued":0,"existing_620_forecasts_modified":0,
        "interpretation":(
            "Only ten already-selected Candidate-positive country-years. "
            "Exact dyad_id-year membership in UCDP Dyadic is a hindsight "
            "annual product, not an as-of predictive feature; an absent ID "
            "may mean inclusion failure, actor recoding or coalition/split "
            "rather than absence of violence. Numeric Candidate best Jan-Sep "
            "is not equivalent to Dyadic annual battle deaths; no causal "
            "conclusion or confirmed short-horizon forecast."
        )
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    opts=p.add_mutually_exclusive_group(required=True)
    opts.add_argument("--source-census",action="store_true")
    opts.add_argument("--print-report",action="store_true")
    opts.add_argument("--check-report",action="store_true")
    args=p.parse_args(argv)
    try:
        if args.source_census:
            print(json.dumps(source_census(),indent=2,sort_keys=True,ensure_ascii=False))
        else:
            result=build_report()
            if args.print_report:
                print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
            else:
                existing=json.loads(REPORT.read_text("utf8"))
                if existing!=result:
                    raise SourceError("Pinned official dyadic-year source / case results disagree")
                print("OK: 4 original official UCDP Dyadic SHA and 4 Candidate SHA, 10 annual case labels reproduced")
    except (OSError,SourceError,ValueError,TypeError,KeyError,TimeoutError,UnicodeError,zipfile.BadZipFile) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 2
    return 0


if __name__=="__main__":
    sys.exit(main())
