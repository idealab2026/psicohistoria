#!/usr/bin/env python3
"""Uganda 2022: GED25.1 dyad threshold and qualitative source-independence audit.

Research question: Are two distinct police shootings automatically state-based
battle deaths in a Government-Uganda vs IS dyad? NO mechanical inference.
External notes are human-authored summaries; UCDP ZIP checked by SHA256.
Never recode GED or an issued GEO forecast.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
from hashlib import sha256
from io import BytesIO,TextIOWrapper
import json
from pathlib import Path
from urllib.parse import urlsplit
from zipfile import ZipFile

from audit_geo_ged251_stratified_linkage import (
    GED_SHA, get_official_bytes, read_frame, audit_existing_forecasts)
from audit_geo_burundi_2022_neighbor_event_linkage import check_frozen_chain

ROOT=Path(__file__).resolve().parents[1]
PAIR_PATH=ROOT/"data/geo-ged251-benin-uganda-2022-source-pair-audit.json"
REVIEW_PATH=ROOT/"data/geo-ged251-uganda-2022-eligibility-source-genealogy.json"
OUTPUT=ROOT/"data/geo-ged251-uganda-2022-eligibility-dyad-stress.json"
GWNO,YEAR=500,2022
DYAD="16938"
GED_IDS=(444764,444765)
THRESHOLD=25
HOSTS={"upf.go.ug","www.independent.co.ug","softpower.ug","dailyexpress.co.ug",
       "www.ugandaradionetwork.net","ugandaradionetwork.net",
       "observer.ug","www.uu.se","journals.sagepub.com"}
REQUIRED={"id","country_id","year","type_of_violence",
          "dyad_new_id","best","low","high","date_start","date_end"}


def scan_official_uganda_2022(raw:bytes):
    if sha256(raw).hexdigest()!=GED_SHA:
        raise ValueError("Official GED25.1 source ZIP SHA changed")
    by_dyad=defaultdict(list)
    with ZipFile(BytesIO(raw)) as archive:
        files=[x for x in archive.infolist()
               if x.filename.lower().endswith(".csv") and not x.is_dir()]
        if len(files)!=1 or files[0].file_size>900_000_000:
            raise ValueError("Unexpected official GED CSV container")
        with TextIOWrapper(archive.open(files[0]),encoding="utf-8-sig",
                           newline="") as f:
            reader=csv.DictReader(f)
            if not REQUIRED.issubset(reader.fieldnames or []):
                raise ValueError("Missing official UCDP dyad/fatality columns")
            seen=set()
            for r in reader:
                try:
                    country,year=int(r["country_id"]),int(r["year"])
                except (ValueError,TypeError):
                    continue
                if country!=GWNO or year!=YEAR or r["type_of_violence"].strip()!="1":
                    continue
                try:
                    eid,best,low,high=(int(r[k]) for k in ("id","best","low","high"))
                except (ValueError,TypeError) as err:
                    raise ValueError("Uganda type-1 event has unparseable fatality") from err
                dyad=str(r["dyad_new_id"]).strip()
                if not dyad or eid<=0 or min(best,low,high)<0 or low>high:
                    raise ValueError("Uganda type-1 event missing dyad or valid deaths")
                if eid in seen:
                    raise ValueError("Repeated 2022 Uganda state-based event id")
                seen.add(eid)
                by_dyad[dyad].append({
                    "GED_event_id":eid,"best":best,"low":low,"high":high,
                    "date_start":r["date_start"][:10],
                    "date_end":r["date_end"][:10],
                })
    if not by_dyad:
        raise ValueError("Uganda 2022 state-based event group unexpectedly absent")
    grouped={}
    for dyad,items in sorted(by_dyad.items()):
        rows=sorted(items,key=lambda x:x["GED_event_id"])
        grouped[dyad]={
            "dyad_new_id":dyad,
            "rows_n":len(rows),
            "best_total":sum(r["best"] for r in rows),
            "low_sum_diagnostic":sum(r["low"] for r in rows),
            "high_sum_diagnostic":sum(r["high"] for r in rows),
            "event_rows":[{"GED_event_id":r["GED_event_id"],"best":r["best"],
                           "date_start":r["date_start"],"date_end":r["date_end"]}
                          for r in rows],
        }
    return grouped


def verify_manual_evidence(data:dict,pair:dict):
    if (data.get("schema")!="idealab.psico.uganda_2022_eligibility_source_genealogy.v1"
        or data.get("research_date")!="2026-11-19"
        or data.get("manual_review_is_not_fatality_verification") is not True
        or data.get("independently_verified_combatant_or_conflict_dyad") is not False
        or data.get("revision_of_UCDP_or_GEO_labels") is not False):
        raise ValueError("Editorial qualification of UCDP events changed")
    sources=data["sources"]
    ids=[r["id"] for r in sources]
    if len(ids)!=len(set(ids)) or len(ids)<6:
        raise ValueError("Source genealogy lacks unique multiple witnesses/publications")
    src={r["id"]:r for r in sources}
    for r in sources:
        uri=urlsplit(r["url"])
        if uri.scheme!="https" or uri.hostname not in HOSTS or not uri.path or uri.query:
            raise ValueError("Unreviewed source host or ambiguous link")
        if r["source_role"] not in ("involved_actor_press_release",
                                  "press_report_same_briefing",
                                  "interview_with_other_state_actor",
                                  "republished_original_interview",
                                  "institutional_codebook"):
            raise ValueError("Unsupported claimed witness provenance")
        if r["source_role"]=="institutional_codebook":
            if r["origin_group"]!="UCDP_METHODOLOGY":
                raise ValueError("UCDP codebook origin must not be independent victim witness")
        elif not r["origin_group"].startswith("UGANDA_STATE_"):
            raise ValueError("Source claims a nonstate independent victim witness")
    edges=data["dependencies"]
    observed=set()
    for edge in edges:
        a,b=edge["publication"],edge["origin_publication"]
        if a==b or a not in src or b not in src or (a,b) in observed:
            raise ValueError("Circular/unknown/duplicate source dependency")
        observed.add((a,b))
        if src[a]["origin_group"]!=src[b]["origin_group"]:
            raise ValueError("Dependent publications disagree on original witness group")
    if any(x["GED_event_id"] not in GED_IDS for x in data["event_claims"]):
        raise ValueError("Unapproved GED source matching")
    claims={r["GED_event_id"]:r for r in data["event_claims"]}
    if set(claims)!=set(GED_IDS):
        raise ValueError("Original two case identifiers changed")
    for eid,claim in claims.items():
        if claim["date"]!={
            444764:"2022-06-05",444765:"2022-06-02"}[eid]:
            raise ValueError("Contemporaneous event date misattributed")
        if (claim["independent_nonstate_witness_verified"] is not False
            or claim["battle_related_classification"]!="UNRESOLVED"
            or claim["victim_separate_from_other_event"] is not True
            or claim["source_ids"][0]!="upf_june"):
            raise ValueError("Qualitative eligibility adjudication not evidence supported")
        if not set(claim["source_ids"]).issubset(src):
            raise ValueError("Event cites an unknown public source")
    if (pair["pair_ged_ids"]!=list(GED_IDS)
        or pair["official_type1_best_total"]!=THRESHOLD
        or pair["same_dyad_id"] is not True
        or pair["common_identical_normalized_UCDP_bibliographic_citations_n"]!=2
        or pair["duplicate_event_proven"] is not False):
        raise ValueError("Official Uganda two-event metadata is inconsistent")
    if data["required_missing_evidence"]!=[
        "independent_person_specific_conflict_dyad_membership_or_warring_party_status",
        "independent_event_specific_armed_exchange_between_dyad_parties",
        "event_specific_link_to_government_or_territory_incompatibility"
    ]:
        raise ValueError("The prespecified conflict-eligibility gap changed")
    return {"total_publications_reviewed":len(sources),
            "publication_origin_groups":sorted(set(
                s["origin_group"] for s in sources
                if s["source_role"]!="institutional_codebook")),
            "nonstate_original_witness_groups_verified":0,
            "dependency_edges_n":len(edges),
            "separate_reported_persons_n":2,
            "independently_verified_warring_party_member_events_n":0,
            "independently_verified_statebased_battle_events_n":0}


def annual_counterfactual(total:int,excluded_ids,records):
    """Sensitivity scenarios, not an inferred correction or UCDP finding."""
    selection=set(excluded_ids)
    if len(selection)!=len(excluded_ids):
        raise ValueError("Duplicate excluded event selection")
    known={r["GED_event_id"]:r for r in records}
    if not selection.issubset(known):
        raise ValueError("Hypothetical exclusion references unknown event")
    if total<0:
        raise ValueError("Negative annual baseline")
    remaining=total-sum(known[eid]["best"] for eid in selection)
    if remaining<0:
        raise ValueError("Event deaths exceed annual total")
    return {"excluded_ged_ids":sorted(selection),"hypothetical_best":remaining,
            "hypothetical_ge25":remaining>=THRESHOLD,
            "crosses_observed_label":(total>=THRESHOLD)!=(remaining>=THRESHOLD)}


def build(raw:bytes):
    earlier=json.loads(PAIR_PATH.read_text(encoding="utf-8"))
    if (earlier.get("schema")!="idealab.psico.geo_ged251_benin_uganda_source_pair_audit.v1"
        or earlier.get("official_GED25_1_zip_sha256")!=GED_SHA):
        raise ValueError("Frozen GED source-pair predecessor moved")
    pair=earlier["cases"]["uganda_2022"]
    notes=json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    source_audit=verify_manual_evidence(notes,pair)
    grouped=scan_official_uganda_2022(raw)
    if DYAD not in grouped:
        raise ValueError("Original state-based IS dyad not present")
    flat=[r for x in grouped.values() for r in x["event_rows"]]
    expected_rows={r["GED_event_id"]:r for r in flat}
    if any(eid not in expected_rows or expected_rows[eid]["best"]!=1
           for eid in GED_IDS):
        raise ValueError("Frozen June Uganda events no longer match official GED")
    country_best=sum(x["best_total"] for x in grouped.values())
    if country_best!=25:
        raise ValueError("Uganda country-year sum differs from prior GED25.1 census")
    # A country-year threshold is the GEO MODEL target. UCDP's 25-death
    # active-dyad rule is distinct; also historical GED dyads can contain
    # episodes from years below 25 after a previous threshold crossing.
    variants=[
        annual_counterfactual(country_best, [],flat),
        annual_counterfactual(country_best,[GED_IDS[0]],flat),
        annual_counterfactual(country_best,[GED_IDS[1]],flat),
        annual_counterfactual(country_best,list(GED_IDS),flat)
    ]
    return {
        "schema":"idealab.psico.uganda_2022_ged251_dyad_eligibility_audit.v1",
        "research_date":"2026-11-19",
        "phase":"INSTITUTIONAL_SOURCE_GENEALOGY_NOT_ELIGIBILITY_ADJUDICATION",
        "official_UCDP_GED25_1_sha256":GED_SHA,
        "frozen_prior_pair_report_sha256":sha256(PAIR_PATH.read_bytes()).hexdigest(),
        "manual_evidence_review_sha256":sha256(REVIEW_PATH.read_bytes()).hexdigest(),
        "country_GWNO":GWNO,"year":YEAR,
        "UCDP25_1_annual_country_type1_best":country_best,
        "UCDP25_1_annual_country_type1_ge25":country_best>=THRESHOLD,
        "dyads":grouped,
        "statebased_dyad_n":len(grouped),
        "source_dependency_audit":source_audit,
        "hypothetical_event_exclusion_scenarios":variants,
        "independent_victim_rosters_or_membership_verified":False,
        "recode_or_deleted_GED_events_n":0,
        "GEO2027_or_GEO2028_prediction_vectors_modified":False,
        "Brier_improvement_demonstrated":False,
        "methodology":"UCDP defines a state-based battle death by direct use of armed force between warring parties in a political incompatibility over government/territory. A report that someone financed an insurgency and was shot by police during a robbery or an arrest does NOT establish the required facts automatically. Existing armed conflict context alone does not settle the individual event; a dyad-year cutoff is not interchangeable with the GEO country-year cutoff. Published news repeating a police communique is institutionally dependent. The later police-officer interview belongs to the SAME state institution and does not provide an independent nonstate eyewitness. No source page HTML bytes are archived or SHA-hashed. None of the hypothetical exclusions is an observation or justified label correction.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--emit-report",action="store_true")
    p.add_argument("--check-report",action="store_true")
    args=p.parse_args()
    frame,original=read_frame()
    if GWNO not in frame:
        raise ValueError("Uganda not in original GEO2027 196-country frame")
    audit_existing_forecasts()
    check_frozen_chain()
    report=build(get_official_bytes())
    if args.check_report:
        if json.loads(OUTPUT.read_text(encoding="utf-8"))!=report:
            raise ValueError("Published Uganda eligible-dyad audit not reproducible")
    if args.emit_report:
        print("UGANDA_GED251_ELIGIBILITY_BEGIN",flush=True)
        print(json.dumps(report,ensure_ascii=False,sort_keys=True,
                         separators=(",",":")),flush=True)
        print("UGANDA_GED251_ELIGIBILITY_END",flush=True)
    else:
        print(json.dumps({
            "country_best":report["UCDP25_1_annual_country_type1_best"],
            "dyads_n":report["statebased_dyad_n"],
            "source_groups":report["source_dependency_audit"]["publication_origin_groups"],
            "status":report["phase"]
        },sort_keys=True))


if __name__=="__main__":
    main()
