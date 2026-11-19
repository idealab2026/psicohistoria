#!/usr/bin/env python3
"""Post-screening triage of 81 GED25.1 same-country/time/place candidate links.

Fixed cohort: 14 flagged anchors from SHA-frozen 24-anchor screening (#135).
Computes provenance metadata overlap and the counterfactual annual >=25 label
effect of deleting exactly ONE member of a candidate pair (hypothesis ONLY).

It NEVER declares a GED record duplicate or recodes an issued forecast.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile

import audit_geo_ged251_stratified_linkage as prior
from audit_geo_ged251_stratified_linkage import (
    GED_SHA, N_PER_STRATUM, REPORT as FROZEN, build as rebuild,
    gap_days, haversine, parse_ged, read_frame, audit_existing_forecasts,
    get_official_bytes,
)

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"data/geo-ged251-candidate-provenance-threshold-triage.json"
REQUIRED={"id","year","country_id","type_of_violence","best",
          "dyad_new_id","source_article"}
CANDIDATE_DISTANCE_KM=25.0
CANDIDATE_GAP_DAYS=3
TARGET_THRESHOLD=25


def normalize_source_articles(value):
    """Only exact normalized individual reference fragments are compared.

    A repeated reference string can be recycled reporting; it cannot be
    counted as an independent witness or proof of a duplicate record.
    """
    if not isinstance(value,str) or not value.strip():
        return frozenset()
    return frozenset(hashlib.sha256(" ".join(x.lower().split()).encode(
        "utf-8")).hexdigest() for x in value.split("///")
        if len(" ".join(x.split()))>=25)


def valid_dyad(value):
    v=str(value or "").strip()
    return None if v.lower() in ("","na","n/a","none","null","-1") else v


def candidate_pairs(frozen, events):
    flagged=[x for x in frozen["sampled_anchors"]
             if x["space_time_neighbors_gap3d_25km"]>0]
    if len(flagged)!=14 or frozen["sampled_anchors_n"]!=24:
        raise ValueError("Cannot silently move the previously frozen anchor set")
    by_id={x["id"]:x for x in events}
    by_country_year=defaultdict(list)
    for x in events:
        by_country_year[(x["GWNO"],x["year"])].append(x)
    pairs={}
    count=Counter()
    for a in flagged:
        if a["ged_id"] not in by_id:
            raise ValueError("Frozen anchor absent in official GED25.1")
        anchor=by_id[a["ged_id"]]
        if (anchor["GWNO"]!=a["GWNO"] or anchor["year"]!=a["year"]
            or anchor["where_prec"]!=a["where_prec"]
            or anchor["best"]!=a["best_deaths"]):
            raise ValueError("Frozen anchor attributes changed")
        for other in by_country_year[(anchor["GWNO"],anchor["year"])]:
            if other["id"]==anchor["id"]:
                continue
            km=haversine(anchor,other)
            days=gap_days(anchor,other)
            if km<=CANDIDATE_DISTANCE_KM and days<=CANDIDATE_GAP_DAYS:
                left,right=sorted((anchor["id"],other["id"]))
                key=(left,right)
                # There can be an event pair with both endpoints sampled
                # as anchors. It is only one unique unordered relation.
                count[a["ged_id"]]+=1
                if key not in pairs:
                    pairs[key]={"left":by_id[left],"right":by_id[right],
                                "distance_km":km,"gap_days":days}
    if sum(count.values())!=81 or set(count)!={x["ged_id"] for x in flagged}:
        raise ValueError("Original 81 anchored-neighbor observations changed")
    if any(count[x["ged_id"]]!=x["space_time_neighbors_gap3d_25km"]
           for x in flagged):
        raise ValueError("Frozen per-anchor candidate counts changed")
    return flagged,pairs


def source_annual_totals_and_metadata(archive_bytes, country_years, required_ids):
    if hashlib.sha256(archive_bytes).hexdigest()!=GED_SHA:
        raise ValueError("GED25.1 official ZIP digest changed")
    annual=Counter()
    metadata={}
    with ZipFile(io.BytesIO(archive_bytes)) as z:
        members=[x for x in z.infolist()
                 if x.filename.lower().endswith(".csv") and not x.is_dir()]
        if len(members)!=1 or members[0].file_size>900_000_000:
            raise ValueError("GED official archive CSV member changed")
        with io.TextIOWrapper(z.open(members[0]),encoding="utf-8-sig",
                              newline="") as src:
            rows=csv.DictReader(src)
            if not REQUIRED.issubset(rows.fieldnames or []):
                raise ValueError("Missing GED25.1 source/dyad/annual-total fields")
            for row in rows:
                try:
                    year=int(row["year"])
                    gwno=int(row["country_id"])
                except (TypeError,ValueError):
                    continue
                if (gwno,year) not in country_years:
                    continue
                if row["type_of_violence"].strip()!="1":
                    continue
                try:
                    eid=int(row["id"])
                    best=int(row["best"])
                except (TypeError,ValueError):
                    raise ValueError("Invalid state-based event ID or best deaths")
                if best<0:
                    raise ValueError("Negative GED state-based death estimate")
                annual[(gwno,year)]+=best
                if eid in required_ids:
                    if eid in metadata:
                        raise ValueError("Repeated candidate GED event ID")
                    metadata[eid]={
                        "best":best,
                        "dyad":valid_dyad(row["dyad_new_id"]),
                        "references":normalize_source_articles(
                            row["source_article"]),
                    }
    if set(metadata)!=required_ids or set(annual)!=country_years:
        raise ValueError("Missing candidate event metadata or country totals")
    return annual,metadata


def counterfactual_single_row_removal(total, a, b):
    """Pure sensitivity test, NOT a claim that either row is erroneous."""
    if min(total,a,b)<0 or max(a,b)>total:
        raise ValueError("Inconsistent annual total or GED event deaths")
    original=total>=TARGET_THRESHOLD
    remove_a=(total-a)>=TARGET_THRESHOLD
    remove_b=(total-b)>=TARGET_THRESHOLD
    return {
        "baseline_ge25":original,
        "remove_left_flips_label":original!=remove_a,
        "remove_right_flips_label":original!=remove_b,
        "either_single_removal_flips_label":original!=remove_a or original!=remove_b,
        "both_possible_single_removals_flip_label":(
            original!=remove_a and original!=remove_b),
    }


def build_report(raw, frame, forecast_sha):
    original=json.loads(FROZEN.read_text(encoding="utf-8"))
    if original["official_GED25_1_zip_SHA256"]!=GED_SHA:
        raise ValueError("Frozen study source hash changed")
    count,events=parse_ged(raw,frame)
    if rebuild(events,count,forecast_sha)!=original:
        raise ValueError("Previous 24-anchor report no longer replays")
    flagged,pairs=candidate_pairs(original,events)
    country_years={(x["GWNO"],x["year"]) for x in flagged}
    ids=set(eid for key in pairs for eid in key)
    annual,meta=source_annual_totals_and_metadata(raw,country_years,ids)
    recs=[]
    for (left,right),item in sorted(pairs.items()):
        a,b=item["left"],item["right"]
        p,q=meta[left],meta[right]
        if p["best"]!=a["best"] or q["best"]!=b["best"]:
            raise ValueError("GED eligible event fatality counts changed")
        t=annual[(a["GWNO"],a["year"])]
        sensitivity=counterfactual_single_row_removal(t,a["best"],b["best"])
        same_dyad=None if p["dyad"] is None or q["dyad"] is None else (
            p["dyad"]==q["dyad"])
        shared=len(p["references"] & q["references"])
        recs.append({
            "GED_pair_ids":[left,right],
            "GWNO":a["GWNO"],
            "year":a["year"],
            "distance_km":round(haversine(a,b),3),
            "interval_gap_days":gap_days(a,b),
            "where_prec_pair":[a["where_prec"],b["where_prec"]],
            "pair_best_deaths":[a["best"],b["best"]],
            "where_both_high_precision":(
                a["where_prec"]<=2 and b["where_prec"]<=2),
            "same_UCDP_dyad_id":same_dyad,
            "number_of_identical_normalized_UCDP_source_citations":shared,
            "shared_UCDP_source_reference_present":shared>0,
            "country_year_GED_type1_best_total":t,
            "single_GED_row_removal_counterfactual":sensitivity,
            "adjudicated_duplicate":False,
        })
    piv=[x for x in recs if x["single_GED_row_removal_counterfactual"][
        "either_single_removal_flips_label"]]
    selected=[]
    for key in sorted(country_years):
        v=annual[key]
        selected.append({"GWNO":key[0],"year":key[1],
                         "total_GED25_1_type1_best_deaths":v,
                         "GED_country_year_state_ge25":v>=TARGET_THRESHOLD,
                         "candidate_unordered_pairs_n":sum(
                             (r["GWNO"],r["year"])==key for r in recs),
                         "at_least_one_single_row_removal_flips_label":any(
                             (r["GWNO"],r["year"])==key for r in piv)})
    dyad=Counter(str(x["same_UCDP_dyad_id"]) for x in recs)
    return {
        "schema":"idealab.psico.geo_ged251_candidate_source_threshold_triage.v1",
        "research_date":"2026-11-19",
        "phase":"POST_SCREENING_SENSITIVITY_NO_DOCUMENTARY_ADJUDICATION",
        "frozen_24_anchor_prior":str(FROZEN.relative_to(ROOT)),
        "frozen_24_anchor_sha256":hashlib.sha256(
            FROZEN.read_bytes()).hexdigest(),
        "ged25_1_official_zip_sha256":GED_SHA,
        "issued_geo2027_sha256":forecast_sha,
        "target":"UCDP GED25.1 state-based (type1) sum(best) >=25 per GWNO/year",
        "frozen_screening_24_anchors_n":24,
        "frozen_flagged_anchors_n":len(flagged),
        "frozen_anchor_neighbor_observations_n":81,
        "unique_unordered_candidate_pairs_n":len(recs),
        "audited_distinct_GWNO_year_n":len(country_years),
        "candidate_paired_events_with_same_dyad_n":dyad["True"],
        "candidate_paired_events_with_different_dyad_n":dyad["False"],
        "candidate_paired_events_with_unknown_dyad_n":dyad["None"],
        "candidate_pairs_sharing_at_least_one_exact_UCDP_source_reference_n":sum(
            x["shared_UCDP_source_reference_present"] for x in recs),
        "candidate_pairs_both_where_prec_le2_n":sum(
            x["where_both_high_precision"] for x in recs),
        "candidate_pairs_pivotal_under_either_one_row_deletion_n":len(piv),
        "candidate_pairs_pivotal_under_both_possible_one_row_deletions_n":sum(
            x["single_GED_row_removal_counterfactual"][
                "both_possible_single_removals_flip_label"] for x in recs),
        "country_years_pivotal_under_any_single_candidate_row_deletion_n":sum(
            x["at_least_one_single_row_removal_flips_label"] for x in selected),
        "country_year_summaries":selected,
        "candidate_pairs":recs,
        "independent_victim_identity_or_fatality_verification_completed":False,
        "adjudicated_duplicate_event_pairs_n":0,
        "ged_country_year_labels_recoded":False,
        "issued_GEO2027_or_GEO2028_vectors_changed":False,
        "is_population_duplicate_or_error_rate_estimate":False,
        "limitations":"These are SAME UCDP publisher GED25.1 event rows. No external source was obtained for per-pair identity. Shared bibliographic citation is reporting overlap, not independent corroboration or proof of duplicated event. Different dyad IDs can indicate distinct parties but are not guaranteed distinct persons. Deleting either one event in a pair is an explicitly hypothetical perturbation only, does not assert a source correction, and does not aggregate multiple candidate removals or retune the issued GEO forecast. The 14 flagged anchors were selected after the older source-vintage problem study, and the 24-anchor screen is non-proportional across precision/date strata. No global error-rate or real model Brier change is established.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--print-report",action="store_true")
    p.add_argument("--check-report",action="store_true")
    args=p.parse_args()
    frame,issue_sha=read_frame()
    audit_existing_forecasts()
    # Includes the previously committed documentary chain back to Burundi.
    from audit_geo_burundi_2022_neighbor_event_linkage import check_frozen_chain
    check_frozen_chain()
    report=build_report(get_official_bytes(),frame,issue_sha)
    if args.check_report:
        frozen=json.loads(OUTPUT.read_text(encoding="utf-8"))
        if frozen!=report:
            raise ValueError("Cross-country source/threshold report changed")
    if args.print_report:
        print("GED251_SOURCE_THRESHOLD_BEGIN",flush=True)
        print(json.dumps(report,ensure_ascii=False,
                         separators=(",",":"),sort_keys=True),flush=True)
        print("GED251_SOURCE_THRESHOLD_END",flush=True)
    else:
        print(json.dumps({k:v for k,v in report.items() if k in
                          ("frozen_flagged_anchors_n",
                           "unique_unordered_candidate_pairs_n",
                           "candidate_pairs_pivotal_under_either_one_row_deletion_n",
                           "country_years_pivotal_under_any_single_candidate_row_deletion_n",
                           "candidate_pairs_sharing_at_least_one_exact_UCDP_source_reference_n")},
                         sort_keys=True))


if __name__=="__main__":
    main()
