#!/usr/bin/env python3
"""Event-ID and dyad fate decomposition of ten already-observed Candidate cases.

Retrospective/postselected research only. Never infer absence of violence from
absence of a record ID. Never create/refit a forecast or expose individual IDs.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile

from check_ucdp_candidate_asof import SourceError, ged_day
from audit_candidate_q2_q3_vintages import get_source
from audit_candidate_to_annual_ged import examine_zip, fetch_annual_zip
from audit_candidate_ged_2021_22 import get_annual_zip

ROOT = Path(__file__).resolve().parents[1]
RETENTION_FILE = ROOT / "data/candidate-ged-retention-strata.json"
EARLY_FILE = ROOT / "data/candidate-ged-2021-22-resolution.json"
LATE_FILE = ROOT / "data/candidate-to-annual-ged-resolution.json"
REPORT_FILE = ROOT / "data/candidate-ged-event-dyad-fates.json"
YEARS = (2021, 2022, 2024, 2025)
THRESHOLD = 5
EDITION = {2021: "22", 2022: "23", 2024: "25", 2025: "26"}
GED_ZIP_URL = {
    2021: "https://ucdp.uu.se/downloads/ged/ged221-csv.zip",
    2022: "https://ucdp.uu.se/downloads/ged/ged231-csv.zip",
    2024: "https://ucdp.uu.se/downloads/ged/ged251-csv.zip",
    2025: "https://ucdp.uu.se/downloads/ged/ged261-csv.zip",
}
SOURCE_BASE = "https://ucdp.uu.se/downloads/candidateged/"
DYAD_FIELDS = ("dyad_new_id", "side_a_new_id", "side_b_new_id")
REQUIRED = {"id","country_id","type_of_violence","date_prec","date_start",
            "date_end","best"}


def default_candidate_fetch(url):
    return get_source(url)


def default_annual_fetch(url, year):
    return get_annual_zip(url) if year <= 2022 else fetch_annual_zip(url)


def source_pins(early, late):
    sources = {}
    for row in early["source_provenance"]:
        y=row["year"]
        if y not in (2021,2022):
            continue
        key=(y, "candidate" if row["family"]=="candidate" else "annual")
        if key[1]=="candidate" and row.get("month")!=9:
            continue
        if key in sources:
            raise SourceError("Repeated fixed early source entry")
        sources[key]={"url":row["url"],"sha256":row["sha256"],
                      "bytes":row["bytes"]}
    for row in late["source_details"]:
        y=row["year"]
        if y not in (2024,2025):
            continue
        key=(y, "candidate" if row["source_family"]=="Candidate" else "annual")
        if key[1]=="candidate" and row.get("month")!=9:
            continue
        if key in sources:
            raise SourceError("Repeated fixed recent source entry")
        sources[key]={"url":row["url"],"sha256":row["sha256"],"bytes":row["bytes"]}
    expected={(y,fam) for y in YEARS for fam in ("candidate","annual")}
    if set(sources)!=expected:
        raise SourceError("Require four Q3 Candidate and four first GED annual sources")
    for y in YEARS:
        target_c=SOURCE_BASE+f"GEDEvent_v{str(y)[2:]}_01_{str(y)[2:]}_09.csv"
        if sources[(y,"candidate")]["url"]!=target_c or sources[(y,"annual")]["url"]!=GED_ZIP_URL[y]:
            raise SourceError("UCDP original URL does not match frozen vintage")
    for p in sources.values():
        if len(p["sha256"])!=64 or p["bytes"]<=0:
            raise SourceError("Invalid original UCDP SHA or byte size")
    return sources


def parse_event(row, year=None):
    eid=(row.get("id") or "").strip()
    if not eid:
        raise SourceError("Blank original event ID")
    try:
        country=int(row["country_id"])
        violence=int(row["type_of_violence"])
        precision=int(row["date_prec"])
        best=int(row["best"])
        source_year=int(row["year"]) if year is None else year
    except (ValueError,TypeError,KeyError) as exc:
        raise SourceError("UCDP original event fields have invalid types") from exc
    if (country<=0 or violence not in (1,2,3)
        or precision not in (0,1,2,3,4,5) or best<0):
        raise SourceError("UCDP source has invalid coding or negative deaths")
    start,end=ged_day(row["date_start"],"date_start"),ged_day(row["date_end"],"date_end")
    if start>end:
        raise SourceError("Source event has date_start later than date_end")
    return {
        "id":eid, "year":source_year, "country":country, "violence":violence,
        "precision":precision,"start":start,"end":end,"best":best,
        "status":(row.get("code_status") or "").strip().casefold() or "(blank)",
        "dyad":(row.get("dyad_new_id") or "").strip(),
        "side_a":(row.get("side_a_new_id") or "").strip(),
        "side_b":(row.get("side_b_new_id") or "").strip(),
    }


def eligible(event, year, country):
    return (event["year"]==year and event["country"]==country
            and event["violence"]==1 and event["precision"] in (1,2)
            and date(year,5,1)<=event["start"] and event["end"]<=date(year,5,30))


def candidate_focus(raw, year, focus):
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    if not reader.fieldnames or not REQUIRED.union({"code_status"}).issubset(reader.fieldnames):
        raise SourceError("Original Candidate Q3 missing required event/quality columns")
    seen=set()
    selections=defaultdict(list)
    n=0
    for row in reader:
        n+=1
        event=parse_event(row,year=year)
        if event["id"] in seen:
            raise SourceError("Duplicate original Candidate event ID")
        seen.add(event["id"])
        if event["country"] in focus and eligible(event,year,event["country"]):
            selections[event["country"]].append(event)
    if n==0:
        raise SourceError("Empty Candidate Q3 CSV")
    return {
        "rows":n,"has_dyad_new_id":"dyad_new_id" in reader.fieldnames,
        "has_side_a_new_id":"side_a_new_id" in reader.fieldnames,
        "has_side_b_new_id":"side_b_new_id" in reader.fieldnames,
        "eligible_focus_events":sum(map(len,selections.values()))
    },dict(selections)


def annual_focus(raw, year, focus, candidate_ids):
    examine_zip(raw)
    expected=f"GEDEvent_v{EDITION[year]}_1.csv"
    target_ids=set(candidate_ids)
    indexed={}  # candidate IDs found anywhere in archive, even different year
    selections=defaultdict(list)
    dyads_state_year=set()
    rows=0
    target_rows=0
    seen=set()
    with zipfile.ZipFile(io.BytesIO(raw)) as source:
        matches=[item for item in source.infolist()
                 if PurePosixPath(item.filename).name.casefold()==expected.casefold()]
        if len(matches)!=1:
            raise SourceError("No unique original annual GED CSV member")
        member=matches[0]
        with source.open(member) as zipped:
            reader=csv.DictReader(io.TextIOWrapper(zipped,encoding="utf-8-sig",newline=""))
            if not reader.fieldnames or not REQUIRED.union({"year"}).issubset(reader.fieldnames):
                raise SourceError("Annual GED CSV has wrong mandatory schema")
            has_dyad="dyad_new_id" in reader.fieldnames
            has_side_a="side_a_new_id" in reader.fieldnames
            has_side_b="side_b_new_id" in reader.fieldnames
            for row in reader:
                rows+=1
                eid=(row.get("id") or "").strip()
                if not eid or eid in seen:
                    raise SourceError("Empty/reused original annual GED event ID")
                seen.add(eid)
                try:
                    event_year=int(row["year"])
                except (ValueError,TypeError) as exc:
                    raise SourceError("Invalid year in annual GED ZIP") from exc
                if event_year!=year and eid not in target_ids:
                    continue
                event=parse_event(row)
                if eid in target_ids:
                    indexed[eid]=event
                if event_year!=year:
                    continue
                target_rows+=1
                if event["violence"]==1 and event["dyad"]:
                    dyads_state_year.add(event["dyad"])
                if event["country"] in focus and eligible(event,year,event["country"]):
                    selections[event["country"]].append(event)
    if target_rows==0:
        raise SourceError("Annual GED ZIP contains no relevant event-year records")
    return {
        "annual_zip_member":member.filename,"all_zip_rows":rows,
        "target_year_rows":target_rows,"has_dyad_new_id":has_dyad,
        "has_side_a_new_id":has_side_a,"has_side_b_new_id":has_side_b,
        "indexed_candidate_id_matches_any_year":len(indexed),
        "annual_statebased_unique_dyads":len(dyads_state_year),
        "eligible_focus_events":sum(map(len,selections.values())),
    },dict(selections),indexed,dyads_state_year


def fate(candidate,annual,year,country):
    if annual is None:
        return "id_absent_from_annual_all_years",["id_absent"]
    flags=[]
    if annual["year"]!=year:
        flags.append("event_year_changed")
    if annual["country"]!=country:
        flags.append("country_changed")
    if annual["violence"]!=1:
        flags.append("violence_type_changed")
    if annual["precision"] not in (1,2):
        flags.append("precision_outside_1_2")
    if not (date(year,5,1)<=annual["start"] and annual["end"]<=date(year,5,30)):
        flags.append("moved_outside_may1_30")
    if eligible(annual,year,country):
        return "shared_eligible_same_id",flags
    # Priority is explicitly defined before source replay. Simultaneous flags
    # are retained separately rather than inventing one causal explanation.
    mapping=[
        ("event_year_changed","id_found_in_different_event_year"),
        ("country_changed","id_reassigned_country"),
        ("violence_type_changed","id_retyped_nonstate_or_unilateral"),
        ("precision_outside_1_2","id_changed_temporal_precision"),
        ("moved_outside_may1_30","id_moved_outside_window"),
    ]
    for key,result in mapping:
        if key in flags:
            return result,flags
    raise SourceError("Same ID ceased to be eligible without an observable coding difference")


def analyze_case(year,country,candidates,annuals,annual_id_index,annual_dyads,
                 expected,source_fields):
    candidate_ids={x["id"]:x for x in candidates}
    annual_ids={x["id"]:x for x in annuals}
    if len(candidate_ids)!=len(candidates) or len(annual_ids)!=len(annuals):
        raise SourceError("Repeated ID in focus events")
    if (not candidates or len(candidates)!=expected["candidate_state_events"]
        or sum(ev["best"] for ev in candidates)!=expected["candidate_q3_may30_best"]
        or sum(ev["best"] for ev in annuals)!=expected["ged_first_annual_may30_best"]):
        raise SourceError("Reconstructed case does not match frozen country-level totals")
    statuses=defaultdict(int)
    for ev in candidates:
        statuses[ev["status"]]+=ev["best"]
    if dict(sorted(statuses.items()))!=expected["candidate_code_status_best"]:
        raise SourceError("Recomputed event code_status deaths differ from original frozen report")
    categories=Counter()
    category_best=Counter()
    all_flags=Counter()
    statuses_by_fate=defaultdict(lambda:defaultdict(int))
    shared_cand=shared_annual=only_cand=only_annual=0
    shared_n=0
    dyad_change=0
    dyad_comparable=0
    unmatched_dyad_present=unmatched_dyad_absent=unmatched_dyad_unavailable=0
    example_counts=Counter()
    for eid,event in candidate_ids.items():
        annual=annual_id_index.get(eid)
        category,flags=fate(event,annual,year,country)
        categories[category]+=1
        category_best[category]+=event["best"]
        statuses_by_fate[category][event["status"]]+=event["best"]
        all_flags.update(flags)
        example_counts["candidate_event_ids"]+=1
        if category=="shared_eligible_same_id":
            if eid not in annual_ids:
                raise SourceError("GED exact ID eligible not found in annual target-country set")
            shared_n+=1
            shared_cand+=event["best"]
            shared_annual+=annual_ids[eid]["best"]
            if event["dyad"] and annual_ids[eid]["dyad"]:
                dyad_comparable+=1
                dyad_change+=int(event["dyad"]!=annual_ids[eid]["dyad"])
        else:
            only_cand+=event["best"]
            if not source_fields["candidate_dyad"] or not source_fields["annual_dyad"] or not event["dyad"]:
                unmatched_dyad_unavailable+=1
            elif event["dyad"] in annual_dyads:
                unmatched_dyad_present+=1
            else:
                unmatched_dyad_absent+=1
    for eid,ev in annual_ids.items():
        if eid not in candidate_ids:
            only_annual+=ev["best"]
    actual_ged=sum(v["best"] for v in annuals)
    actual_cand=sum(v["best"] for v in candidates)
    if (actual_cand!=shared_cand+only_cand
        or actual_ged!=shared_annual+only_annual
        or actual_ged-actual_cand!=(shared_annual-shared_cand)+only_annual-only_cand):
        raise SourceError("Conservation of deaths across matched/unmatched original event IDs failed")
    if shared_n!=expected["candidate_same_country_window_exact_id_match_count"]:
        raise SourceError("Same-ID eligible overlap differs from frozen #154 observations")
    return {
        "year":year,"country_id":country,"country":expected["country"],
        "retained_ged_threshold_5":expected["retained_ged"],
        "candidate_q3_best":actual_cand,"ged_first_annual_best":actual_ged,
        "candidate_n_eligible_events":len(candidates),
        "ged_n_eligible_events":len(annuals),
        "candidate_code_status_best":dict(sorted(statuses.items())),
        "shared_eligible_same_id_events":shared_n,
        "shared_candidate_best":shared_cand,
        "shared_ged_best":shared_annual,
        "candidate_only_best":only_cand,
        "annual_only_best":only_annual,
        "delta_best_ged_minus_candidate":actual_ged-actual_cand,
        "delta_best_shared_event_reestimation":shared_annual-shared_cand,
        "decomposition_reconciles":True,
        "candidate_event_id_fates":dict(sorted(categories.items())),
        "candidate_deaths_by_fate":dict(sorted(category_best.items())),
        "all_record_changes_for_matched_ids":dict(sorted(all_flags.items())),
        "candidate_status_best_by_fate":{
            key:dict(sorted(v.items())) for key,v in sorted(statuses_by_fate.items())
        },
        "shared_id_dyad_comparable":dyad_comparable,
        "shared_id_dyad_changed":dyad_change,
        "candidate_nonshared_ids_with_dyad_still_present_in_annual_state_year":unmatched_dyad_present,
        "candidate_nonshared_ids_with_dyad_absent_from_annual_state_year":unmatched_dyad_absent,
        "candidate_nonshared_ids_dyad_unavailable":unmatched_dyad_unavailable,
        "candidate_minus_ged_cannot_be_interpreted_as_unreal_violence":True,
    }


def build_report(candidate_fetch=default_candidate_fetch,
                 annual_fetch=default_annual_fetch,
                 retention_raw=None,early_raw=None,late_raw=None):
    rbytes=RETENTION_FILE.read_bytes() if retention_raw is None else retention_raw
    ebytes=EARLY_FILE.read_bytes() if early_raw is None else early_raw
    lbytes=LATE_FILE.read_bytes() if late_raw is None else late_raw
    retention=json.loads(rbytes)
    early=json.loads(ebytes)
    late=json.loads(lbytes)
    if retention.get("status")!="POST_SELECTED_EXPLORATORY_NON_CAUSAL_NO_FORECASTS":
        raise SourceError("Upstream case retention report is not frozen/exploratory")
    if early.get("status")!="ARCHIVED_FIRST_ANNUAL_GED_LABEL_RESOLUTION_NOT_ASOF" or late.get("status")!="RETROSPECTIVE_FINAL_VINTAGE_COMPARISON_NOT_PROSPECTIVE":
        raise SourceError("Upstream annual report status differs")
    if (retention["source_reports"]["candidate_2021_22_and_4year_pool_sha256"]!=hashlib.sha256(ebytes).hexdigest()
        or retention["source_reports"]["candidate_2024_25_sha256"]!=hashlib.sha256(lbytes).hexdigest()):
        raise SourceError("Frozen case report references different source report bytes")
    if retention["n_country_years_at_risk"]!=642 or retention["n_candidate_positive_country_years"]!=10:
        raise SourceError("Not the declared T=5/30d Candidate-positive cohort")
    cases=retention["candidate_positive_cases"]
    if len(cases)!=10 or len({(c["year"],c["country_id"]) for c in cases})!=10:
        raise SourceError("Ten already-selected country-year cases expected")
    if any(c["year"] not in YEARS or c["candidate_q3_may30_best"]<THRESHOLD for c in cases):
        raise SourceError("Unregistered year or nonpositive Candidate threshold case")
    pins=source_pins(early,late)
    all_cases=[]
    manifest=[]
    for year in YEARS:
        focus={c["country_id"]:c for c in cases if c["year"]==year}
        if not focus:
            raise SourceError("A registered year contains no cases")
        cpin=pins[(year,"candidate")]
        apin=pins[(year,"annual")]
        raw_c=candidate_fetch(cpin["url"])
        if hashlib.sha256(raw_c).hexdigest()!=cpin["sha256"] or len(raw_c)!=cpin["bytes"]:
            raise SourceError("Original Q3 Candidate archive changed byte content")
        cmeta, events=candidate_focus(raw_c,year,focus)
        ids={x["id"] for values in events.values() for x in values}
        raw_a=annual_fetch(apin["url"],year)
        if hashlib.sha256(raw_a).hexdigest()!=apin["sha256"] or len(raw_a)!=apin["bytes"]:
            raise SourceError("Original GED annual ZIP changed byte content")
        ameta,annuals,lookup,annual_dyads=annual_focus(raw_a,year,focus,ids)
        manifest.append({"year":year,"candidate_q3":{"url":cpin["url"],"sha256":cpin["sha256"],"bytes":cpin["bytes"],"audit":cmeta},
                         "first_annual_ged":{"url":apin["url"],"sha256":apin["sha256"],"bytes":apin["bytes"],"audit":ameta}})
        for cid,case in focus.items():
            all_cases.append(analyze_case(
                year,cid,events.get(cid,[]),annuals.get(cid,[]),lookup,annual_dyads,
                case,{"candidate_dyad":cmeta["has_dyad_new_id"],"annual_dyad":ameta["has_dyad_new_id"]}
            ))
    all_cases.sort(key=lambda x:(x["year"],x["country_id"]))
    if len(all_cases)!=10 or sum(x["retained_ged_threshold_5"] for x in all_cases)!=5:
        raise SourceError("Historical 10-case label retention changed")
    categories=Counter()
    by_group={}
    for era,selected in (("2021-2022",[v for v in all_cases if v["year"]<=2022]),
                         ("2024-2025",[v for v in all_cases if v["year"]>=2024]),
                         ("four_years",all_cases)):
        by_cat=Counter()
        by_best=Counter()
        for x in selected:
            by_cat.update(x["candidate_event_id_fates"])
            by_best.update(x["candidate_deaths_by_fate"])
        by_group[era]={
            "n_candidate_positive_country_years":len(selected),
            "n_retained_ged_label":sum(x["retained_ged_threshold_5"] for x in selected),
            "n_candidate_events":sum(x["candidate_n_eligible_events"] for x in selected),
            "n_ged_events":sum(x["ged_n_eligible_events"] for x in selected),
            "candidate_best":sum(x["candidate_q3_best"] for x in selected),
            "annual_best":sum(x["ged_first_annual_best"] for x in selected),
            "shared_candidate_best":sum(x["shared_candidate_best"] for x in selected),
            "shared_annual_best":sum(x["shared_ged_best"] for x in selected),
            "candidate_only_best":sum(x["candidate_only_best"] for x in selected),
            "annual_only_best":sum(x["annual_only_best"] for x in selected),
            "candidate_event_id_fates":dict(sorted(by_cat.items())),
            "candidate_deaths_by_fate":dict(sorted(by_best.items())),
            "candidate_nonshared_dyad_absent":sum(x["candidate_nonshared_ids_with_dyad_absent_from_annual_state_year"] for x in selected),
            "candidate_nonshared_dyad_present":sum(x["candidate_nonshared_ids_with_dyad_still_present_in_annual_state_year"] for x in selected),
        }
    return {
        "schema":"idealab.psico.candidate_ged_event_dyad_fates.v1",
        "status":"RETROSPECTIVE_POSTSELECTED_EVENT_ID_DIAGNOSTICS_NO_FORECAST",
        "design_date":"2026-11-24",
        "years":list(YEARS),"threshold_best":THRESHOLD,
        "target_window":"May 1-30", "n_cases":len(all_cases),
        "n_population_at_risk":642,
        "n_cases_retained_in_ged":5,
        "source_report_sha256":{
            "retention_10cases":hashlib.sha256(rbytes).hexdigest(),
            "2021_22":hashlib.sha256(ebytes).hexdigest(),
            "2024_25":hashlib.sha256(lbytes).hexdigest(),
        },
        "original_archive_provenance":manifest,
        "case_level_aggregates":all_cases,
        "pooled_era_and_all":by_group,
        "raw_event_ids_or_event_descriptions_published":False,
        "cross_dataset_record_id_not_event_ontology":True,
        "later_ged_features_never_usable_for_asof_prediction":True,
        "prospective_issues":0,"frozen_forecasts_modified":0,
        "limitations":(
            "Only ten postselected Candidate-positive country-years, 4 dependent years. "
            "Absence of exact ID or dyad in first annual GED is compatible with "
            "recoding, split/merge and annual inclusion differences, not proof "
            "that the original act of violence did not occur. Country label "
            "thresholds are database-version outcomes, not independently as-of "
            "verified conflict onset; individual event identities not published."
        ),
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--print-report",action="store_true")
    modes.add_argument("--check-report",action="store_true")
    args=p.parse_args(argv)
    try:
        result=build_report()
        if args.print_report:
            print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
        else:
            stored=json.loads(REPORT_FILE.read_text("utf8"))
            if result!=stored:
                raise SourceError("Original UCDP event and dyad fate decomposition changed")
            print("OK: eight source hashes, ten Candidate-to-GED case decompositions, 642 risk set")
    except (SourceError,OSError,KeyError,ValueError,TypeError,TimeoutError,UnicodeError,zipfile.BadZipFile) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 2
    return 0


if __name__=="__main__":
    sys.exit(main())
