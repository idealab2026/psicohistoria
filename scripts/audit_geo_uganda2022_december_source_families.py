#!/usr/bin/env python3
"""Reproducible source-genealogy triage of all four Uganda Dec 2022 GED25.1 rows.

Rows fixed BEFORE examining their original UCDP citations using prior PR #139.
The 19,2,0,2 records total 23 best. They are not necessarily 23 independently
verified combatant deaths. UCDP publisher/citation roots can be dependent.
No modification of any issued historical label or forecast.
"""
from __future__ import annotations
import argparse
import json
from datetime import date
from hashlib import sha256
from pathlib import Path
from collections import Counter

from audit_geo_ged251_stratified_linkage import (
    GED_SHA, get_official_bytes, read_frame, audit_existing_forecasts,
    gap_days, haversine,
)
from audit_geo_burundi_2022_neighbor_event_linkage import check_frozen_chain
from audit_geo_ged251_benin_uganda_source_pair import (
    parse_source_row, citation_fragments,
)
from audit_geo_uganda2022_statebased_eligibility import (
    scan_official_uganda_2022, GWNO, YEAR, DYAD, THRESHOLD,
    OUTPUT as PREVIOUS,
)

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"data/geo-ged251-uganda-2022-december-source-families.json"
DECEMBER_IDS=(460796,460859,460862,462156)
EXPECTED_BEST={460796:19,460859:2,460862:0,462156:2}
EXPECTED_DATES={
    460796:("2022-12-12","2022-12-13"),
    460859:("2022-12-21","2022-12-21"),
    460862:("2022-12-13","2022-12-27"),
    462156:("2022-12-19","2022-12-19"),
}
SOURCES_MAX=15
PREVIEW_MAX=260


def fixed_prior_contract():
    previous=json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if (previous.get("schema")!="idealab.psico.uganda_2022_ged251_dyad_eligibility_audit.v1"
        or previous.get("official_UCDP_GED25_1_sha256")!=GED_SHA
        or previous.get("UCDP25_1_annual_country_type1_best")!=THRESHOLD
        or previous.get("statebased_dyad_n")!=1):
        raise ValueError("Frozen six-event Uganda GED dyad integrity failed")
    dyad=previous["dyads"][DYAD]
    events={r["GED_event_id"]:r for r in dyad["event_rows"]}
    if (len(events)!=6 or
        {eid:events[eid]["best"] for eid in DECEMBER_IDS}!=EXPECTED_BEST or
        {eid:(events[eid]["date_start"],events[eid]["date_end"])
         for eid in DECEMBER_IDS}!=EXPECTED_DATES):
        raise ValueError("Frozen December identity/death/date contract drifted")
    if sum(EXPECTED_BEST.values())!=23:
        raise ValueError("December baseline is no longer 23 deaths")
    return previous


def official_december_metadata(raw):
    # Access the GED25.1 rows with original bibliography columns by
    # reusing the robust official CSV extraction but without editing its
    # source. Keep the original body out of research artifacts.
    from io import BytesIO, TextIOWrapper
    import csv
    from zipfile import ZipFile

    if sha256(raw).hexdigest()!=GED_SHA:
        raise ValueError("Wrong official GED25.1 ZIP")
    found={}
    with ZipFile(BytesIO(raw)) as z:
        members=[x for x in z.infolist()
                 if x.filename.lower().endswith(".csv") and not x.is_dir()]
        if len(members)!=1 or members[0].file_size>900_000_000:
            raise ValueError("GED source ZIP format drifted")
        with TextIOWrapper(z.open(members[0]),encoding="utf-8-sig",
                           newline="") as f:
            reader=csv.DictReader(f)
            required={"id","country_id","year","type_of_violence",
                      "dyad_new_id","date_start","date_end","best",
                      "low","high","source_article","source_original",
                      "number_of_sources","where_prec","date_prec",
                      "event_clarity","where_description","where_coordinates",
                      "latitude","longitude","source_office",
                      "source_headline","source_date","dyad_name"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError("GED citation/event schema drifted")
            for row in reader:
                try:
                    eid=int(row["id"])
                except (TypeError,ValueError):
                    continue
                if eid not in DECEMBER_IDS:
                    continue
                if eid in found:
                    raise ValueError("Duplicate December GED row ID in official archive")
                found[eid]=row
    if set(found)!=set(DECEMBER_IDS):
        raise ValueError("Missing fixed December GED event ID")
    return found


def normalize_and_publish(eid,row):
    ev=parse_source_row(row)
    if (ev["GED_event_id"]!=eid or ev["GWNO"]!=GWNO
        or ev["year"]!=YEAR or ev["type_of_violence"]!=1
        or ev["dyad_id"]!=DYAD or ev["best"]!=EXPECTED_BEST[eid]
        or (ev["start"].isoformat(),ev["end"].isoformat())!=EXPECTED_DATES[eid]):
        raise ValueError("December row disagrees with six-event frozen dataset")
    fragments=ev["citation_preview"]
    if len(fragments)!=ev["number_of_sources"]:
        raise ValueError("Official GED December bibliography count differs")
    out={k:ev[k] for k in (
        "GED_event_id","GWNO","year","type_of_violence",
        "best","low","high","date_prec","where_prec","event_clarity",
        "dyad_id","dyad_name","side_a","side_b",
        "where_coordinates","where_description","adm_1","adm_2",
        "source_original","source_office","source_headline","source_date",
        "number_of_sources",
    )}
    out["date_start"]=ev["start"].isoformat()
    out["date_end"]=ev["end"].isoformat()
    out["latitude"]=ev["lat"]
    out["longitude"]=ev["lon"]
    out["GED_source_article_fingerprints"]=ev["citation_fingerprints"]
    out["GED_bibliographic_previews"]=[x[:PREVIEW_MAX] for x in fragments[:SOURCES_MAX]]
    out["GED_bibliography_truncated"]=len(fragments)>SOURCES_MAX or any(
        len(x)>PREVIEW_MAX for x in fragments)
    out["independently_verified_fatality_or_rebel_status"]=False
    out["duplicate_event_verified"]=False
    return out,ev


def build(raw):
    previous=fixed_prior_contract()
    rows=official_december_metadata(raw)
    records,internal={},{}
    for eid in DECEMBER_IDS:
        records[eid],internal[eid]=normalize_and_publish(eid,rows[eid])
    if sum(x["best"] for x in records.values())!=23:
        raise ValueError("Official Uganda December estimate totals changed")
    pairs=[]
    for i,left in enumerate(DECEMBER_IDS):
        for right in DECEMBER_IDS[i+1:]:
            a,b=internal[left],internal[right]
            hashes_a=set(a["citation_fingerprints"])
            hashes_b=set(b["citation_fingerprints"])
            overlap=len(hashes_a & hashes_b)
            pairs.append({
                "GED_pair_ids":[left,right],
                "interval_gap_days":gap_days(a,b),
                "coordinate_distance_km":round(haversine(a,b),3),
                "same_assigned_coordinates":round(haversine(a,b),6)==0,
                "shared_exact_GED_citations_n":overlap,
                "shared_citation_is_not_independent_confirmation":True,
                "same_dyad_new_id":a["dyad_id"]==b["dyad_id"],
                "same_original_source_string":a["source_original"]==b["source_original"],
                "duplicate_episodes_verified":False,
            })
    # Comparing the 19-count row with the remaining December records is
    # hypothesis generation, never a mechanical correction.
    return {
        "schema":"idealab.psico.geo_ged251_uganda_december_source_family_audit.v1",
        "research_date":"2026-11-19",
        "status":"OFFICIAL_CITATION_AND_GEO_METADATA_NOT_EXTERNAL_ADJUDICATION",
        "official_GED25_1_ZIP_SHA256":GED_SHA,
        "previous_six_event_census_SHA256":sha256(PREVIOUS.read_bytes()).hexdigest(),
        "GWNO":GWNO,"year":YEAR,"dyad_new_id":DYAD,
        "December_record_count":len(records),
        "December_type1_best_sum":sum(x["best"] for x in records.values()),
        "December_type1_low_sum":sum(x["low"] for x in records.values()),
        "December_type1_high_sum":sum(x["high"] for x in records.values()),
        "zero_best_event_ids":[i for i in DECEMBER_IDS if records[i]["best"]==0],
        "event_records":[records[i] for i in DECEMBER_IDS],
        "unique_unordered_December_pairs":pairs,
        "pairs_sharing_exact_bibliographic_fragments_n":sum(
            bool(x["shared_exact_GED_citations_n"]) for x in pairs),
        "December_event_identity_verified_independently_n":0,
        "December_fatality_lists_verified_independently_n":0,
        "current_2022_country_statebased_best":25,
        "hypothetical_remove_all_December_best":2,
        "hypothetical_remove_only_19_death_row_best":6,
        "corrections_to_GED_events":0,
        "GEO2027_GEO2028_issue_vectors_changed":False,
        "limitations":"GED25.1 2022 December 19+2+0+2=23 is a publisher estimate, not independently recounted deaths. A zero best row is not an observed zero-death episode. UCDP references can reuse one involved army source even when publisher differs. A coordinate centroid can coincide despite distinct villages/dates. Source article titles and publisher names in GED are bibliographic metadata, not a validated source genealogy; external story verification must be performed separately. Hypothetical row deletion is sensitivity, not a correction. Annual country threshold is not interchangeable with conflict dyad definition.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--emit-report",action="store_true")
    p.add_argument("--check-report",action="store_true")
    args=p.parse_args()
    frame,issued=read_frame()
    if GWNO not in frame:
        raise ValueError("Uganda missing from frozen GEO2027 frame")
    audit_existing_forecasts()
    check_frozen_chain()
    report=build(get_official_bytes())
    if args.check_report:
        saved=json.loads(OUTPUT.read_text(encoding="utf-8"))
        if saved!=report:
            raise ValueError("December source family result fails exact GED25.1 replay")
    if args.emit_report:
        print("UGANDA_DECEMBER_SOURCE_FAMILIES_BEGIN",flush=True)
        print(json.dumps(report,ensure_ascii=False,separators=(",",":"),
                         sort_keys=True),flush=True)
        print("UGANDA_DECEMBER_SOURCE_FAMILIES_END",flush=True)
    else:
        print(json.dumps({
            "December_n":report["December_record_count"],
            "best":report["December_type1_best_sum"],
            "shared_pairs_n":report["pairs_sharing_exact_bibliographic_fragments_n"]
        },sort_keys=True))


if __name__=="__main__":
    main()
