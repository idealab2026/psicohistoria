#!/usr/bin/env python3
"""Full-GWNO near-threshold GED25.1 country-year screen (years 2021, 2022).

Selection is pre-specified by observable annual state-based fatalities (15..35)
rather than by any event-pair match, source reference or GEO forecast value.
One-row removal is a HYPOTHETICAL mathematical perturbation, not an alleged
coding mistake or a genuine updated forecast outcome.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
from hashlib import sha256
from io import BytesIO, TextIOWrapper
import json
from pathlib import Path
from zipfile import ZipFile

from audit_geo_ged251_stratified_linkage import (
    GED_SHA, parse_ged, read_frame, audit_existing_forecasts,
    get_official_bytes, gap_days, haversine,
)
from audit_geo_ged251_candidate_source_threshold import TARGET_THRESHOLD

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"data/geo-ged251-near25-2021-22-countryyear-census.json"
PRIOR=ROOT/"data/geo-ged251-candidate-provenance-threshold-triage.json"
YEARS=(2021,2022)
BAND_MIN=15
BAND_MAX=35
NEAR_KM=25.0
NEAR_GAP_DAYS=3


def annual_all_statebased(raw,frame):
    """All GED25.1 type1 best, not only geocodable + point-date records.

    A country-year without GED rows has an observed-database total of zero,
    not proven zero deaths in the underlying historical world.
    """
    if sha256(raw).hexdigest()!=GED_SHA:
        raise ValueError("Official GED25.1 SHA mismatch")
    sums=Counter()
    records=defaultdict(list)
    with ZipFile(BytesIO(raw)) as z:
        members=[x for x in z.infolist() if x.filename.lower().endswith(".csv")
                 and not x.is_dir()]
        if len(members)!=1 or members[0].file_size>900_000_000:
            raise ValueError("Expected one official GED table")
        with TextIOWrapper(z.open(members[0]),encoding="utf-8-sig",newline="") as f:
            reader=csv.DictReader(f)
            required={"id","year","country_id","type_of_violence","best"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError("Missing official GED numeric fields")
            for row in reader:
                try:
                    c=int(row["country_id"])
                    yr=int(row["year"])
                except (ValueError,TypeError):
                    continue
                if c not in frame or yr not in YEARS or row["type_of_violence"].strip()!="1":
                    continue
                try:
                    eid=int(row["id"])
                    best=int(row["best"])
                except (ValueError,TypeError):
                    raise ValueError("Malformed GED type1 deaths/id in target cohort")
                if eid<=0 or best<0:
                    raise ValueError("Invalid state-based deaths/id")
                k=(c,yr)
                sums[k]+=best
                records[k].append((eid,best))
    if len(frame)!=196:
        raise ValueError("Original GWNO frame unexpectedly changed")
    keys={(c,y) for c in frame for y in YEARS}
    # Force all 392 country-year cells, including years without recorded events.
    return {k:sums[k] for k in keys},{k:records[k] for k in keys}


def bands_partition(total):
    if total<0:
        raise ValueError("Negative death total")
    if total==0:
        return "no_recorded_type1_deaths"
    if total<BAND_MIN:
        return "positive_below_band"
    if total<TARGET_THRESHOLD:
        return "below25_in_band"
    if total<=BAND_MAX:
        return "at_or_above25_in_band"
    return "above_band"


def pivotal_under_one_record_removal(total,best):
    """One-row deletion sensitivity; no claim that row is erroneous."""
    if total<0 or best<0 or best>total:
        raise ValueError("Impossible GED one-row counterfactual")
    return total>=TARGET_THRESHOLD and total-best<TARGET_THRESHOLD


def candidates_in_country_year(events):
    ordered=sorted(events,key=lambda x:x["id"])
    candidates=[]
    for i,a in enumerate(ordered):
        for b in ordered[i+1:]:
            days=gap_days(a,b)
            if days>NEAR_GAP_DAYS:
                continue
            distance=haversine(a,b)
            if distance>NEAR_KM:
                continue
            candidates.append({
                "pair_ids":[a["id"],b["id"]],
                "gap_days":days,
                "distance_km":round(distance,3),
                "where_prec_pair":[a["where_prec"],b["where_prec"]],
                "best_pair":[a["best"],b["best"]],
                "both_where_prec_1_or_2":(
                    a["where_prec"]<=2 and b["where_prec"]<=2),
            })
    return candidates


def build_report(raw,frame,forecast_sha):
    prev=json.loads(PRIOR.read_text(encoding="utf-8"))
    if (prev.get("schema")!="idealab.psico.geo_ged251_candidate_source_threshold_triage.v1"
        or prev.get("ged25_1_official_zip_sha256")!=GED_SHA
        or prev.get("unique_unordered_candidate_pairs_n")!=81
        or prev.get("candidate_pairs_pivotal_under_either_one_row_deletion_n")!=0):
        raise ValueError("Previous frozen source-threshold research changed")
    totals,rows=annual_all_statebased(raw,frame)
    scanned,events=parse_ged(raw,frame)
    by_country=defaultdict(list)
    for e in events:
        by_country[(e["GWNO"],e["year"])].append(e)
    categories=Counter(bands_partition(v) for v in totals.values())
    marginal_keys=sorted(k for k,v in totals.items() if BAND_MIN<=v<=BAND_MAX)
    data=[]
    for country,year in marginal_keys:
        k=(country,year)
        total=totals[k]
        all_events=rows[k]
        eligible=by_country[k]
        neighbors=candidates_in_country_year(eligible)
        id_set={eid for eid,_ in all_events}
        if len(id_set)!=len(all_events):
            raise ValueError("Reused event id in a near-threshold country-year")
        pivotal=[eid for eid,best in all_events
                 if pivotal_under_one_record_removal(total,best)]
        for n in neighbors:
            a,b=n["best_pair"]
            n["either_single_row_removal_flips_label"]=(
                pivotal_under_one_record_removal(total,a)
                or pivotal_under_one_record_removal(total,b))
            n["both_single_row_removal_options_flip_label"]=(
                pivotal_under_one_record_removal(total,a)
                and pivotal_under_one_record_removal(total,b))
            n["duplicate_identity_proven"]=False
        data.append({
            "GWNO":country,
            "year":year,
            "GED25_1_type1_annual_best":total,
            "observed_annual_label_ge25":total>=TARGET_THRESHOLD,
            "GED_type1_event_rows_including_zero_best_n":len(all_events),
            "geocoded_positive_best_events_within_year_n":len(eligible),
            "pivotal_event_rows_under_hypothetical_one_row_removal_n":len(pivotal),
            "candidate_25km_gap3d_pairs_n":len(neighbors),
            "candidate_pairs_with_either_one_row_threshold_flip_n":sum(
                x["either_single_row_removal_flips_label"] for x in neighbors),
            "candidate_pairs":neighbors,
            "independent_documentary_review_complete":False,
        })
    return {
        "schema":"idealab.psico.geo_ged251_near25_countryyear_census.v1",
        "research_design_date":"2026-11-19",
        "phase":"RETROSPECTIVE_THRESHOLD_STRESS_NOT_ERROR_ESTIMATE",
        "official_GED25_1_zip_SHA256":GED_SHA,
        "frozen_original_GEO2027_SHA256":forecast_sha,
        "frozen_prior_triage_path":str(PRIOR.relative_to(ROOT)),
        "frozen_prior_triage_sha256":sha256(PRIOR.read_bytes()).hexdigest(),
        "GWNO_n":len(frame),
        "years":list(YEARS),
        "total_frame_country_year_cells_n":len(totals),
        "target_variable":"GED25.1 type1 state-based annual sum(best) >=25",
        "prespecified_band_inclusive":[BAND_MIN,BAND_MAX],
        "marginal_country_years_n":len(data),
        "marginal_active_country_years_n":sum(x["observed_annual_label_ge25"] for x in data),
        "marginal_inactive_country_years_n":sum(
            not x["observed_annual_label_ge25"] for x in data),
        "frame_category_counts":dict(sorted(categories.items())),
        "marginal_with_any_pivotal_event_row_n":sum(
            x["pivotal_event_rows_under_hypothetical_one_row_removal_n"]>0 for x in data),
        "marginal_pivotal_event_rows_n":sum(
            x["pivotal_event_rows_under_hypothetical_one_row_removal_n"] for x in data),
        "marginal_candidate_near_event_pairs_n":sum(
            x["candidate_25km_gap3d_pairs_n"] for x in data),
        "marginal_candidate_pairs_with_one_row_pivot_n":sum(
            x["candidate_pairs_with_either_one_row_threshold_flip_n"] for x in data),
        "marginal_country_years":data,
        "total_GED25_1_events_scanned":scanned,
        "eligible_geocoded_positive_events_n":len(events),
        "no_actual_duplicate_corrections_performed":True,
        "no_independent_victim_verification":True,
        "issued_GEO2027_or_GEO2028_modified":False,
        "forecast_skill_or_Brier_change_claimed":False,
        "notes":"Census of 196 issued GWNO x 2 years (392 cells) with all type1 GED25.1 event best totals; band 15..35 chosen from the model target before querying these conditional results. This retrospective band-conditioned analysis cannot estimate GED data error rates, true casualties, documentary identity or model skill. Rows with no GED events have sum 0 as database output, not evidence of true absence of violence. Date/coordinate eligibility applies ONLY to candidate-pair screening, not annual death aggregation. Deleting one recorded event is a hypothetical counterfactual, not a suggested edit. Historical source vintage 25.1 cannot be treated as 2021/22 real-time information.",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--print-report",action="store_true")
    ap.add_argument("--check-report",action="store_true")
    args=ap.parse_args()
    frame,sha=read_frame()
    audit_existing_forecasts()
    from audit_geo_burundi_2022_neighbor_event_linkage import check_frozen_chain
    check_frozen_chain()
    report=build_report(get_official_bytes(),frame,sha)
    if args.check_report:
        if report!=json.loads(OUTPUT.read_text(encoding="utf-8")):
            raise ValueError("Official near-threshold GWNO-year census changed")
    if args.print_report:
        print("GED251_NEAR25_CENSUS_BEGIN",flush=True)
        print(json.dumps(report,ensure_ascii=False,
                         separators=(",",":"),sort_keys=True),flush=True)
        print("GED251_NEAR25_CENSUS_END",flush=True)
    else:
        print(json.dumps({x:report[x] for x in (
            "marginal_country_years_n","marginal_active_country_years_n",
            "marginal_pivotal_event_rows_n","marginal_candidate_near_event_pairs_n",
            "marginal_candidate_pairs_with_one_row_pivot_n")},sort_keys=True))


if __name__=="__main__":
    main()
