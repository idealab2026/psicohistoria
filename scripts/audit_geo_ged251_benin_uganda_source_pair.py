#!/usr/bin/env python3
"""GED25.1 event-provenance audit of two prespecified threshold-sensitive pairs.

Read official SHA-verified ZIP. Diagnose dated vs fuzzy events and dependence of
UCDP's underlying bibliographic references without declaring duplicate victims.
No original forecast or historical event data is edited.
"""
import argparse
import csv
from datetime import date
from hashlib import sha256
from io import BytesIO,TextIOWrapper
import json
from pathlib import Path
from urllib.parse import urlsplit
from zipfile import ZipFile

from audit_geo_ged251_stratified_linkage import (
    GED_SHA, read_frame, audit_existing_forecasts, get_official_bytes,
    haversine, gap_days,
)
from audit_geo_burundi_2022_neighbor_event_linkage import check_frozen_chain

ROOT=Path(__file__).resolve().parents[1]
UPSTREAM=ROOT/"data/geo-ged251-near25-2021-22-countryyear-census.json"
REPORT=ROOT/"data/geo-ged251-benin-uganda-2022-source-pair-audit.json"
PUBLIC_REVIEW=ROOT/"data/geo-ged251-benin-uganda-public-firstparty-review.json"
REVIEW_URL_HOSTS={
    "www.africanparks.org","whc.unesco.org",
    "crisisgroup-staging.sbx.so","upf.go.ug","nilepost.co.ug",
}
CASES={
    "benin_2022": {"GWNO":434,"year":2022,"pair":(431254,431259),
                   "total":30,"best":(8,1)},
    "uganda_2022":{"GWNO":500,"year":2022,"pair":(444764,444765),
                   "total":25,"best":(1,1)},
}
FIELDS={"id","country_id","year","type_of_violence","best","low","high",
        "date_start","date_end","date_prec","where_prec","where_coordinates",
        "where_description","latitude","longitude","dyad_new_id","dyad_name",
        "event_clarity","source_article","source_original","source_date",
        "source_office","source_headline","number_of_sources",
        "adm_1","adm_2","side_a","side_b"}
MAX_CITATION_PREVIEW=350
MAX_FRAGMENT_LEN=1000


def citation_fragments(raw):
    """These are UCDP bibliographic metadata, not primary event testimonies."""
    if not isinstance(raw,str):
        raise ValueError("Unexpected source_article type")
    # GED25.1 CSV serializes each bibliographic reference as a quoted
    # semicolon-delimited cell; the /// separator is used in other UCDP
    # formats (not this official 25.1 ZIP). Splitting on /// would turn
    # multiple distinct citations into ONE and underestimate source overlap.
    parts=next(csv.reader([raw],delimiter=";",quotechar='"',
                          skipinitialspace=True))
    pieces=[" ".join(s.split()) for s in parts
            if s.strip() and s.strip().lower() not in ("na","n/a","unknown")]
    if len(pieces)>100:
        raise ValueError("Implausibly many GED citation fragments")
    return pieces


def extract_target_rows(raw):
    if sha256(raw).hexdigest()!=GED_SHA:
        raise ValueError("GED25.1 ZIP SHA mismatch")
    targets={eventid for x in CASES.values() for eventid in x["pair"]}
    events={}
    with ZipFile(BytesIO(raw)) as z:
        candidates=[x for x in z.infolist() if x.filename.lower().endswith(".csv")
                    and not x.is_dir()]
        if len(candidates)!=1 or candidates[0].file_size>900_000_000:
            raise ValueError("Official GED ZIP changed")
        with TextIOWrapper(z.open(candidates[0]),encoding="utf-8-sig",
                              newline="") as stream:
            reader=csv.DictReader(stream)
            if not FIELDS.issubset(reader.fieldnames or []):
                raise ValueError("GED25.1 lacks mandatory event/source metadata")
            for row in reader:
                try:
                    eid=int(row["id"])
                except (ValueError,TypeError):
                    continue
                if eid in targets:
                    if eid in events:
                        raise ValueError("Duplicate original GED event ID")
                    events[eid]=row
    if set(events)!=targets:
        raise ValueError("At least one targeted GED ID is missing")
    return events


def parse_source_row(r):
    eid=int(r["id"])
    start=date.fromisoformat(r["date_start"][:10])
    end=date.fromisoformat(r["date_end"][:10])
    if start>end:
        raise ValueError("GED event date range reversed")
    try:
        best,low,high=(int(r[k]) for k in ("best","low","high"))
        lat,lon=(float(r[k]) for k in ("latitude","longitude"))
        temporal,spatial=(int(r[k]) for k in ("date_prec","where_prec"))
        clarity=int(r["event_clarity"])
        num_sources=int(r["number_of_sources"])
    except (TypeError,ValueError):
        raise ValueError("Unparseable official GED metadata")
    if not(0<=low<=high and 0<=best<=100_000 and 1<=temporal<=5
           and 1<=spatial<=7 and clarity in (1,2)
           and -90<=lat<=90 and -180<=lon<=180):
        raise ValueError("Unexpected official GED precision/estimate metadata")
    refs=citation_fragments(r["source_article"])
    if num_sources>=0 and num_sources!=len(refs):
        raise ValueError("GED number_of_sources differs from citation list")
    return {
        "GED_event_id":eid,
        "GWNO":int(r["country_id"]),
        "year":int(r["year"]),
        "type_of_violence":int(r["type_of_violence"]),
        "best":best,"low":low,"high":high,
        "start":start,"end":end,"date_prec":temporal,
        "where_prec":spatial,"event_clarity":clarity,
        "lat":lat,"lon":lon,
        "dyad_id":str(r["dyad_new_id"]).strip(),
        "dyad_name":str(r["dyad_name"]).strip(),
        "side_a":str(r["side_a"]).strip(),
        "side_b":str(r["side_b"]).strip(),
        "where_coordinates":str(r["where_coordinates"]).strip(),
        "where_description":str(r["where_description"]).strip(),
        "adm_1":str(r["adm_1"]).strip(),
        "adm_2":str(r["adm_2"]).strip(),
        "source_original":str(r["source_original"]).strip(),
        "number_of_sources":num_sources,
        "source_article_count":len(refs),
        "citation_fingerprints":[sha256(x.lower().encode("utf-8")).hexdigest()
                                 for x in refs],
        "citation_preview":refs,
        "source_date":str(r["source_date"]).strip(),
        "source_office":str(r["source_office"]).strip(),
        "source_headline":str(r["source_headline"]).strip(),
    }


def check_existing_case_contract():
    prior=json.loads(UPSTREAM.read_text(encoding="utf-8"))
    if (prior.get("schema")!="idealab.psico.geo_ged251_near25_countryyear_census.v1"
        or prior.get("official_GED25_1_zip_SHA256")!=GED_SHA
        or prior.get("marginal_candidate_pairs_with_one_row_pivot_n")!=2
        or prior.get("total_frame_country_year_cells_n")!=392):
        raise ValueError("Upstream preregistered near-25 census contract changed")
    seen=[]
    for name,spec in CASES.items():
        candidate=[x for x in prior["marginal_country_years"]
                   if x["GWNO"]==spec["GWNO"] and x["year"]==spec["year"]]
        if len(candidate)!=1 or candidate[0]["GED25_1_type1_annual_best"]!=spec["total"]:
            raise ValueError("Wrong frozen GWNO-year death total")
        pairs=[x for x in candidate[0]["candidate_pairs"]
               if x["pair_ids"]==list(spec["pair"])
               and x["either_single_row_removal_flips_label"] is True]
        if len(pairs)!=1 or pairs[0]["best_pair"]!=list(spec["best"]):
            raise ValueError("Frozen risk-sensitive pair identities changed")
        seen.append((name,pairs[0]))
    return prior,seen


def summarize_case(spec,src):
    a,b=(parse_source_row(src[x]) for x in spec["pair"])
    for ev,expected_best in zip((a,b),spec["best"]):
        if (ev["GWNO"]!=spec["GWNO"] or ev["year"]!=2022
            or ev["type_of_violence"]!=1 or ev["best"]!=expected_best):
            raise ValueError("Official GED event does not match frozen case")
    def public_event(ev):
        excluded={"lat","lon","start","end","citation_preview",
                  "citation_fingerprints"}
        data={k:v for k,v in ev.items() if k not in excluded}
        data["date_start"]=ev["start"].isoformat()
        data["date_end"]=ev["end"].isoformat()
        data["latitude"]=ev["lat"]
        data["longitude"]=ev["lon"]
        data["citation_fingerprint_sha256"]=ev["citation_fingerprints"]
        # Catalog metadata is limited to short previews and its hash. The
        # original articles and associated quoted texts are NOT republished.
        data["bibliographic_ref_previews"]=[
            s[:MAX_CITATION_PREVIEW] for s in ev["citation_preview"][:12]]
        data["citation_fragments_truncated"]=len(ev["citation_preview"])>12 or any(
            len(s)>MAX_CITATION_PREVIEW for s in ev["citation_preview"])
        return data
    refsa=set(a["citation_fingerprints"])
    refsb=set(b["citation_fingerprints"])
    gap=gap_days(a,b)
    km=haversine(a,b)
    return {
        "GWNO":spec["GWNO"],"year":spec["year"],
        "official_type1_best_total":spec["total"],
        "pair_ged_ids":list(spec["pair"]),
        "same_dyad_id":a["dyad_id"]==b["dyad_id"],
        "common_identical_normalized_UCDP_bibliographic_citations_n":len(refsa&refsb),
        "separate_UCDP_citation_fragments_n":len(refsa|refsb),
        "date_interval_gap_days":gap,
        "distance_km":round(km,3),
        "exact_same_assigned_coordinates":round(km,6)==0,
        "observed_different_event_ids":True,
        "independent_publisher_primary_witness_verified":False,
        "identical_victims_verified":False,
        "duplicate_event_proven":False,
        "events":[public_event(a),public_event(b)],
        "scientific_status":"UNADJUDICATED_BIBLIOGRAPHIC_RECONCILIATION",
    }


def build(raw):
    prior,cases=check_existing_case_contract()
    source=extract_target_rows(raw)
    result={}
    for name,spec in CASES.items():
        result[name]=summarize_case(spec,source)
    return {
        "schema":"idealab.psico.geo_ged251_benin_uganda_source_pair_audit.v1",
        "research_date":"2026-11-19",
        "phase":"SOURCE_METADATA_NOT_INDEPENDENT_DOCUMENTARY_ADJUDICATION",
        "official_GED25_1_zip_sha256":GED_SHA,
        "prior_392_country_year_census_sha256":sha256(UPSTREAM.read_bytes()).hexdigest(),
        "target_pair_count":2,
        "selected_because_pivotal_counterfactual_not_verified_error":True,
        "identified_true_duplicate_pairs_n":0,
        "external_primary_source_independence_certified_n":0,
        "cases":result,
        "fatality_label_corrected":False,
        "issued_GEO_forecast_modified":False,
        "limitations":"UCDP published bibliographic citations document their coding inputs, not independent witness examination. Same coordinates, overlapping source titles, actor dyad, relative reporting dates or casualty magnitudes alone cannot establish duplicate incident identity. Date/where precision and event clarity are UCDP metadata and must be assessed together. Removing an event is purely hypothetical; no GED or GEO label is altered.",
    }


def check_public_review(report):
    """Validate first-party editorial review against SAME official GED event IDs.

    The remote web pages were manually read, not fetched or hash-verified here.
    This check protects metadata links and case boundaries, not factual truth.
    """
    review=json.loads(PUBLIC_REVIEW.read_text(encoding="utf-8"))
    if (review.get("schema")!="idealab.psico.ged251_benin_uganda_public_first_party_review.v1"
        or review.get("independent_third_party_victim_rosters_verified") is not False
        or review.get("coded_GED_records_corrected") is not False
        or review.get("original_GEO_issued_forecasts_modified") is not False):
        raise ValueError("Public first-party source review contract violated")
    cases=review["cases"]
    if len(cases)!=len(CASES) or {x["case_id"] for x in cases}!=set(CASES):
        raise ValueError("Public review cases or evidence scope changed")
    expected_overlap={"benin_2022":4,"uganda_2022":2}
    for record in cases:
        key=record["case_id"]
        official=report["cases"][key]
        spec=CASES[key]
        if (record["GED_event_ids"]!=list(spec["pair"])
            or official["pair_ged_ids"]!=list(spec["pair"])
            or record["GED_event_days"]!=[x["date_start"] for x in official["events"]]
            or record["verdict_for_duplicate_detection"].split("__")[0]!="NO_DUPLICATE_SUPPORTED"
            or official["duplicate_event_proven"] is not False
            or official["common_identical_normalized_UCDP_bibliographic_citations_n"]!=expected_overlap[key]):
            raise ValueError("Public review mismatches official GED metadata")
        urls=set()
        for evidence in record["original_source_evidence"]:
            u=urlsplit(evidence["url"])
            if (u.scheme!="https" or u.hostname not in REVIEW_URL_HOSTS
                or not u.path or u.query or evidence["url"] in urls):
                raise ValueError("Unreviewed or repeated public source URL")
            urls.add(evidence["url"])
            if date.fromisoformat(evidence["published"])<min(date.fromisoformat(d)
                                                            for d in record["GED_event_days"]):
                raise ValueError("Retrospective page purportedly predates event")
        if key=="benin_2022":
            if (record["participant_death_total_reported_for_both_dates"]!=8
                or record["competing_reported_aggregate"]!=9
                or record["competing_reported_aggregate_is_verified"] is not False
                or len(urls)<3
                or record["full_fatality_roster_independently_matched"] is not False):
                raise ValueError("Benin competing-count source claim changed")
        if key=="uganda_2022":
            if (record["separate_reported_victims_in_same_primary_statement"] is not True
                or record["independent_person_identity_or_combatant_status_verified"] is not False
                or len(urls)<2 or official["events"][0]["where_description"]==
                                            official["events"][1]["where_description"]):
                raise ValueError("Uganda distinct reported locations not preserved")
    return review


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--emit-report",action="store_true")
    ap.add_argument("--check-report",action="store_true")
    args=ap.parse_args()
    frame,original=read_frame()
    audit_existing_forecasts()
    check_frozen_chain()
    report=build(get_official_bytes())
    check_public_review(report)
    for key,case in report["cases"].items():
        if case["GWNO"] not in frame:
            raise ValueError("Case outside original prospectively issued country frame")
    if args.check_report:
        if report!=json.loads(REPORT.read_text(encoding="utf-8")):
            raise ValueError("Frozen source genealogy changed")
    if args.emit_report:
        print("GED251_BENIN_UGANDA_PAIR_BEGIN",flush=True)
        print(json.dumps(report,ensure_ascii=False,separators=(",",":"),
                         sort_keys=True),flush=True)
        print("GED251_BENIN_UGANDA_PAIR_END",flush=True)
    else:
        print(json.dumps({k:{
            "same_dyad_id":v["same_dyad_id"],
            "shared_bibliographic_refs":v["common_identical_normalized_UCDP_bibliographic_citations_n"],
            "date_gap_days":v["date_interval_gap_days"],
        } for k,v in report["cases"].items()},sort_keys=True))


if __name__=="__main__":
    main()
