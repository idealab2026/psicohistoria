#!/usr/bin/env python3
"""Togo 11 May 2022: original GED25.1 source chronology and fatality genealogy.

Preselected: GED event 440185, best 23 of 34 annual type1 Togo deaths,
date_prec1 2022-05-11, with one source published 2022-05-05 (before event).
This does NOT establish an event coding error. Later public claims of about
15 attackers and eight soldiers likewise need independent casualty review.
"""
from __future__ import annotations
import argparse
import csv
import json
from datetime import date
from hashlib import sha256
from io import BytesIO,TextIOWrapper
from pathlib import Path
from zipfile import ZipFile

from audit_geo_ged251_stratified_linkage import (
    GED_SHA, get_official_bytes, read_frame, audit_existing_forecasts,
)
from audit_geo_ged251_marginal_source_date_lags import (
    OUTPUT as FROZEN_LAGS, publication_dates,
)
from audit_geo_ged251_benin_uganda_source_pair import citation_fragments
from audit_geo_burundi_2022_neighbor_event_linkage import check_frozen_chain

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/geo-ged251-togo2022-440185-source-genealogy.json"
GOV_REVIEW=ROOT/"data/geo-ged251-togo2022-440185-public-review.json"
GED_ID=440185
GWNO=461
YEAR=2022
DAY="2022-05-11"
BEST=23
COUNTRY_BEST=34
EXPECTED_SOURCE_FIRST="2022-05-05"
EXPECTED_SOURCE_LAST="2022-05-26"
REQUIRED={"id","year","country_id","type_of_violence","best","low",
          "high","deaths_a","deaths_b","deaths_civilians","deaths_unknown",
          "date_start","date_end","date_prec","where_prec","dyad_new_id",
          "dyad_name","side_a","side_b","source_article","source_date",
          "source_office","source_original","number_of_sources"}


def check_source_preselection():
    p=json.loads(FROZEN_LAGS.read_text(encoding="utf-8"))
    if (p.get("schema")!="idealab.psico.ged251_near25_source_publication_date_lag_census.v1"
        or p.get("official_GED25_1_zip_SHA256")!=GED_SHA
        or p.get("frozen_GWNO_years_n")!=14
        or p.get("total_all_type1_GED_event_rows_n")!=118):
        raise ValueError("Preselected public source-chronology audit drifted")
    rows=[r for r in p["event_publication_metadata"]
          if r["GED_event_id"]==GED_ID]
    if len(rows)!=1:
        raise ValueError("Togo 440185 missing from fixed source-date audit")
    e=rows[0]
    if (e["GWNO"]!=GWNO or e["year"]!=YEAR or e["date_start"]!=DAY
        or e["date_end"]!=DAY or e["date_prec"]!=1 or e["best"]!=BEST
        or e["earliest_publication_date"]!=EXPECTED_SOURCE_FIRST
        or e["latest_publication_date"]!=EXPECTED_SOURCE_LAST
        or e["source_date_tokens_valid_n"]!=8
        or e["single_event_deletion_would_cross_25"] is not True):
        raise ValueError("Original source-before-event anomaly does not replay")
    c=[x for x in p["countryyear_summaries"]
       if x["GWNO"]==GWNO and x["year"]==YEAR]
    if len(c)!=1 or c[0]["GED_statebased_best_total"]!=COUNTRY_BEST:
        raise ValueError("Marginal Togo annual mortality changed")
    return p,e


def original_ged_row(raw):
    if sha256(raw).hexdigest()!=GED_SHA:
        raise ValueError("Official GED25.1 source ZIP SHA mismatch")
    found=[]
    with ZipFile(BytesIO(raw)) as z:
        members=[x for x in z.infolist()
                 if x.filename.lower().endswith(".csv") and not x.is_dir()]
        if len(members)!=1 or members[0].file_size>900_000_000:
            raise ValueError("Expected one bounded official GED25.1 CSV")
        with TextIOWrapper(z.open(members[0]),encoding="utf-8-sig",
                           newline="") as f:
            reader=csv.DictReader(f)
            if not REQUIRED.issubset(reader.fieldnames or []):
                raise ValueError("Original UCDP event, source or fatality columns missing")
            for row in reader:
                try:
                    eid=int(row["id"])
                except (TypeError,ValueError):
                    continue
                if eid==GED_ID:
                    found.append(row)
    if len(found)!=1:
        raise ValueError("GED event selected in prior study not unique")
    return found[0]


def interpret_ged_row(r):
    if (int(r["id"])!=GED_ID or int(r["country_id"])!=GWNO
        or int(r["year"])!=YEAR or int(r["type_of_violence"])!=1
        or int(r["best"])!=BEST or r["date_start"][:10]!=DAY
        or r["date_end"][:10]!=DAY or int(r["date_prec"])!=1):
        raise ValueError("Official Togo conflict-event provenance changed")
    mortality={k:int(r[k]) for k in ("best","low","high","deaths_a",
                                      "deaths_b","deaths_civilians",
                                      "deaths_unknown")}
    if (sum(mortality[k] for k in ("deaths_a","deaths_b",
                                   "deaths_civilians","deaths_unknown"))!=BEST
        or not 0<=mortality["low"]<=mortality["best"]<=mortality["high"]):
        raise ValueError("Inconsistent official side-specific fatality counts")
    articles=citation_fragments(r["source_article"])
    pub,missing,invalid=publication_dates(r["source_date"])
    source_dates=next(csv.reader([r["source_date"]],delimiter=";",
                                 quotechar='"',skipinitialspace=True))
    offices=next(csv.reader([r["source_office"]],delimiter=";",
                              quotechar='"',skipinitialspace=True))
    count=int(r["number_of_sources"])
    if (count!=len(articles) or count!=len(source_dates)
        or missing or invalid or len(pub)!=count
        or min(pub).isoformat()!=EXPECTED_SOURCE_FIRST
        or max(pub).isoformat()!=EXPECTED_SOURCE_LAST):
        raise ValueError("The eight Togo bibliography dates or list lengths changed")
    if len(offices)!=count:
        raise ValueError("UCDP source_office list not in 1:1 correspondence")
    sources=[]
    for i,(item,pub_day,publisher) in enumerate(zip(articles,source_dates,offices),1):
        pday=date.fromisoformat(pub_day.strip()[:10])
        sources.append({
            "sequence":i,
            "published":pday.isoformat(),
            "published_before_exact_event_day":pday<date.fromisoformat(DAY),
            "publisher_as_recorded":publisher.strip(),
            "reference_preview":item[:220],
            "UCDP_reference_sha256":sha256(item.lower().encode()).hexdigest(),
            "independent_original_casualty_witness_verified":False,
        })
    return {
        "GED_id":GED_ID,"GWNO":GWNO,"year":YEAR,
        "UCDP_GED_event_day":DAY,"date_prec":1,
        "UCDP_dyad_new_id":r["dyad_new_id"],
        "UCDP_dyad_name":r["dyad_name"],
        "side_a":r["side_a"],"side_b":r["side_b"],
        "official_GED_fatality_components":mortality,
        "UCDP_source_original":r["source_original"],
        "where_prec":int(r["where_prec"]),
        "bibliographic_references_n":count,
        "exact_distinct_bibliographic_refs_n":len(set(x["UCDP_reference_sha256"] for x in sources)),
        "repeated_exact_bibliographic_ref_entries_n":(
            count-len(set(x["UCDP_reference_sha256"] for x in sources))),
        "bibliographic_pre_event_references_n":sum(
            x["published_before_exact_event_day"] for x in sources),
        "bibliographic_references":sources,
        "earliest_publication_day":EXPECTED_SOURCE_FIRST,
        "latest_publication_day":EXPECTED_SOURCE_LAST,
        "pre_event_bibliography_is_proven_coding_error":False,
        "source_publisher_independence_verified":False,
    }


def validate_public_review(ged,review):
    """Editorial annotations only, no network verification or UCDP correction."""
    if (review.get("schema")!="idealab.psico.togo2022_440185_public_source_genealogy.v1"
        or review.get("GED_event_id")!=GED_ID
        or review.get("GED_labels_corrected") is not False
        or review.get("issued_GEO_probabilities_modified") is not False
        or review.get("independent_all_23_fatalities_verified") is not False):
        raise ValueError("Public source editorial contract overstates evidence")
    refs=review["source_evidence"]
    ids=[s["id"] for s in refs]
    if len(refs)<4 or len(ids)!=len(set(ids)):
        raise ValueError("Not enough distinct public publication records")
    from urllib.parse import urlsplit
    allowed={"securite.gouv.tg","www.republiquetogolaise.tg","au.int",
             "www.africanews.com","unowas.unmissions.org"}
    for s in refs:
        u=urlsplit(s["url"])
        if u.scheme!="https" or u.hostname not in allowed or not u.path:
            raise ValueError("Unreviewed source URL or non-HTTPS link")
        if s["original_reporting_root"] not in (
            "TOGO_STATE_MAY11_COMMUNIQUE",
            "TOGO_STATE_MAY18_MINISTER_PRESS",
            "AFRICAN_UNION_RELAY_OF_MAY11",
            "UNITED_NATIONS_REPORT_DERIVED_MAY11"):
            raise ValueError("Unjustified statement of independent 23-victim witness")
    if review["initial_Togo_state_military_dead"]!=8:
        raise ValueError("Original 11 May soldier toll altered")
    if review["later_Togo_minister_alleged_assailant_dead_approx"]!=15:
        raise ValueError("Later minister 15-assailant estimate altered")
    if 8+15!=ged["official_GED_fatality_components"]["best"]:
        raise ValueError("Source estimates do not arithmetically match GED best")
    if review["claims_15_assailant_fatalities_independently_verified"] is not False:
        raise ValueError("Later assailant toll is not independently documented")
    if review["source_before_11May_explains_event_day_error"] is not False:
        raise ValueError("Pre-event published item is not an event-day error proof")
    if ged["official_GED_fatality_components"]["low"]!=8:
        raise ValueError("The original official lower casualty estimate has changed")
    return {
        "reviewed_public_publications_n":len(refs),
        "original_publisher_roots_n":len(set(s["original_reporting_root"]
                                            for s in refs)),
        "later_additional_assailant_deaths_documentarily_independent":False,
        "exact_11May_event_day_contemporaneously_supported":True,
        "togo_initial_8_plus_later_15_equals_GED_best":True,
        "GED_best_correction_justified":False,
    }


def build(raw):
    prior,evidence=check_source_preselection()
    official=interpret_ged_row(original_ged_row(raw))
    reviewed=json.loads(GOV_REVIEW.read_text(encoding="utf-8"))
    external=validate_public_review(official,reviewed)
    return {
        "schema":"idealab.psico.ged251_togo2022_event440185_source_audit.v1",
        "research_date":"2026-11-19",
        "status":"FIRST_PARTY_TOLL_GENEALOGY_NOT_INDEPENDENT_VICTIM_VALIDATION",
        "official_GED25_1_zip_SHA256":GED_SHA,
        "preselected_118_event_lag_study_SHA256":sha256(
            FROZEN_LAGS.read_bytes()).hexdigest(),
        "public_review_sha256":sha256(GOV_REVIEW.read_bytes()).hexdigest(),
        "original_country_year_best":COUNTRY_BEST,
        "hypothetical_drop_entire_event_total":COUNTRY_BEST-BEST,
        "hypothetical_replace_best_with_official_low_total":(
            COUNTRY_BEST-BEST+official["official_GED_fatality_components"]["low"]),
        "hypothetical_replace_best_with_official_low_crosses_25":(
            COUNTRY_BEST-BEST+official["official_GED_fatality_components"]["low"]<25),
        "low_and_best_are_UCDP_sensitivity_estimates_not_errors":True,
        "hypothetical_drop_entire_event_crosses_25":COUNTRY_BEST-BEST<25,
        "original_ged_event":official,
        "contemporaneous_source_audit":external,
        "fatality_corrections_applied":0,
        "model_issued_predictions_modified":False,
        "Brier_skill_gain_demonstrated":False,
        "limitations":"The minister's later about-15 attacker death count is a single interested-party allegation; no forensic victim list or independent count is in the reviewed records. Initial eight soldier fatalities from 11 May government communique are reported also by AU and UN, but that repetition does not independently verify bodies. The GED best=23 can be arithmetically consistent with later official 8+~15 yet such arithmetic does not prove the true casualty count. Pre-event dated bibliography can be unrelated contextual material; textual citation-by-citation chronology must be considered. No GED date error, event deletion or correction to 2022 country label is justified. Event source extraction is retrospective GED25.1, not as-of 2022 real time data.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--emit-report",action="store_true")
    p.add_argument("--check-report",action="store_true")
    args=p.parse_args()
    frame,sha=read_frame()
    if GWNO not in frame:
        raise ValueError("Togo absent in original 196 GWNO frame")
    audit_existing_forecasts()
    check_frozen_chain()
    report=build(get_official_bytes())
    if args.check_report:
        if report!=json.loads(OUT.read_text(encoding="utf-8")):
            raise ValueError("Frozen Togo event-source report differs from GED25.1")
    if args.emit_report:
        print("TOGO_GED440185_SOURCE_AUDIT_BEGIN",flush=True)
        print(json.dumps(report,ensure_ascii=False,separators=(",",":"),
                         sort_keys=True),flush=True)
        print("TOGO_GED440185_SOURCE_AUDIT_END",flush=True)
    else:
        e=report["original_ged_event"]
        print(json.dumps({"best":e["official_GED_fatality_components"]["best"],
                          "before_event_sources":e["bibliographic_pre_event_references_n"],
                          "source_counts":e["bibliographic_references_n"]},sort_keys=True))


if __name__=="__main__":
    main()
