#!/usr/bin/env python3
"""Prespecified GED25.1 low/best/high threshold audit of 14 marginal country-years.

The band and the 118 type1 historical event IDs are frozen by prior #137/#141.
No country-year is selected by its low or high values. Summing UCDP published
event low/high supplies an arithmetic sensitivity envelope, NOT independent
confidence bounds, jointly credible configurations, actual errors, or Brier.
Second goal: inspect the original source genealogy for Azerbaijan GED 427299,
whose one cited publication predates the GED exact event day by 11 days.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import csv
from datetime import date
from hashlib import sha256
from io import BytesIO,TextIOWrapper
import json
from pathlib import Path
from zipfile import ZipFile

from audit_geo_ged251_stratified_linkage import (
    GED_SHA, read_frame, audit_existing_forecasts, get_official_bytes,
)
from audit_geo_burundi_2022_neighbor_event_linkage import check_frozen_chain
from audit_geo_ged251_marginal_source_date_lags import (
    read_source_cohort, OUTPUT as SOURCE_COHORT,
)
from audit_geo_ged251_benin_uganda_source_pair import citation_fragments

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"data/geo-ged251-marginal-low-best-high-2021-22.json"
AZER_ID=427299
AZER_GWNO,AZER_YEAR=373,2021
THRESHOLD=25
MAX_REFS=25
REQUIRED={"id","country_id","year","type_of_violence","best","low","high",
    "date_start","date_end","date_prec","source_date","source_article",
    "source_office","source_original","number_of_sources","where_description",
    "where_coordinates","where_prec","dyad_name","dyad_new_id","side_a","side_b",
    "deaths_a","deaths_b","deaths_civilians","deaths_unknown","event_clarity"}


def label_class(lo,be,hi,threshold=THRESHOLD):
    if any(type(n) is not int or n<0 for n in (lo,be,hi)):
        raise ValueError("Invalid signed GED fatality estimate")
    if not lo<=be<=hi:
        raise ValueError("GED component bounds contradict best")
    if hi<threshold:
        return "negative_for_all_three_estimates"
    if lo>=threshold:
        return "positive_for_all_three_estimates"
    return "low_high_straddle_binary_threshold"


def sum_envelope(rows):
    # UCDP GED25.1 codebook §5.5 explicitly warns that event_clarity=2
    # aggregate rows can have high < low or best after subtracting already
    # disaggregated clarity=1 events. Preserve literal scenario totals AND
    # separately calculate min/max of the three estimates of EACH row.
    counts={k:sum(r[k] for r in rows) for k in ("low","best","high")}
    counts["per_row_min_total"]=sum(min(r[k] for k in ("low","best","high"))
                                    for r in rows)
    counts["per_row_max_total"]=sum(max(r[k] for k in ("low","best","high"))
                                    for r in rows)
    counts["class"]=label_class(counts["per_row_min_total"],counts["best"],
                                 counts["per_row_max_total"])
    counts["best_label_ge25"]=counts["best"]>=THRESHOLD
    counts["low_label_ge25"]=counts["low"]>=THRESHOLD
    counts["high_label_ge25"]=counts["high"]>=THRESHOLD
    counts["best_vs_low_label_disagrees"]=counts["best_label_ge25"]!=counts["low_label_ge25"]
    counts["best_vs_high_label_disagrees"]=counts["best_label_ge25"]!=counts["high_label_ge25"]
    counts["raw_scenario_totals_monotone"]=counts["low"]<=counts["best"]<=counts["high"]
    counts["uncertainty_range_total"]=counts["per_row_max_total"]-counts["per_row_min_total"]
    return counts


def source_extract(raw,selection):
    if sha256(raw).hexdigest()!=GED_SHA:
        raise ValueError("Official UCDP GED25.1 ZIP SHA mismatch")
    selected=set(selection)
    output=defaultdict(list)
    ids=set()
    original_azer=None
    with ZipFile(BytesIO(raw)) as z:
        members=[x for x in z.infolist()
                 if x.filename.lower().endswith(".csv") and not x.is_dir()]
        if len(members)!=1 or members[0].file_size>900_000_000:
            raise ValueError("Unexpected GED25.1 official archive")
        with TextIOWrapper(z.open(members[0]),encoding="utf-8-sig",
                           newline="") as f:
            reader=csv.DictReader(f)
            if not REQUIRED.issubset(reader.fieldnames or []):
                raise ValueError("UCDP GED source or casualty columns missing")
            for r in reader:
                try:
                    k=(int(r["country_id"]),int(r["year"]))
                except (TypeError,ValueError):
                    continue
                if k not in selected or str(r["type_of_violence"]).strip()!="1":
                    continue
                try:
                    eid=int(r["id"])
                    low,best,high=(int(r[n]) for n in ("low","best","high"))
                    p=int(r["date_prec"])
                    clarity=int(r["event_clarity"])
                except (TypeError,ValueError) as e:
                    raise ValueError("Malformed GED marginal annual casualty row") from e
                if (eid in ids or eid<=0 or not 1<=p<=5 or clarity not in (1,2)
                    or min(low,best,high)<0):
                    raise ValueError("Duplicate GED ID or invalid official fatality/precision")
                ids.add(eid)
                is_nonmonotone=not(low<=best<=high)
                output[k].append({"GED_event_id":eid,"low":low,
                                  "best":best,"high":high,
                                  "event_clarity":clarity,
                                  "source_fatality_order_nonmonotone":is_nonmonotone,
                                  "date_start":r["date_start"][:10],
                                  "date_end":r["date_end"][:10],
                                  "date_prec":p})
                if eid==AZER_ID:
                    if original_azer is not None:
                        raise ValueError("Duplicate Azerbaijan source event")
                    original_azer=r
    if original_azer is None:
        raise ValueError("Frozen Azerbaijan source event absent")
    return output,original_azer


def azerbaijan_original_source(original,source_registry):
    metadata=source_registry["event_publication_metadata"]
    found=[r for r in metadata if r["GED_event_id"]==AZER_ID]
    if len(found)!=1:
        raise ValueError("Azerbaijan pre-event metadata missing")
    earlier=found[0]
    if (earlier["GWNO"]!=AZER_GWNO or earlier["year"]!=AZER_YEAR
        or earlier["date_start"]!="2021-06-17"
        or earlier["earliest_publication_date"]!="2021-06-06"
        or earlier["best"]!=1 or earlier["date_prec"]!=1):
        raise ValueError("Frozen Azerbaijan date/source alert changed")
    citations=citation_fragments(original["source_article"])
    pubdate=next(csv.reader([original["source_date"]],delimiter=";",
                             quotechar='"',skipinitialspace=True))
    office=next(csv.reader([original["source_office"]],delimiter=";",
                            quotechar='"',skipinitialspace=True))
    n=int(original["number_of_sources"])
    if (n!=1 or len(citations)!=n or len(pubdate)!=n or len(office)!=n):
        raise ValueError("Azerbaijan original bibliographic relationship changed")
    sources=[]
    for i,(cit,day,publisher) in enumerate(zip(citations,pubdate,office)):
        day=day.strip()[:10]
        if date.fromisoformat(day).isoformat()!="2021-06-06":
            raise ValueError("Azerbaijan UCDP original source publication changed")
        sources.append({"publisher_as_GED":publisher.strip(),
                        "publication_date_as_GED":day,
                        "bibliographic_reference_excerpt":cit[:350],
                        "bibliographic_sha256":sha256(cit.lower().encode()).hexdigest(),
                        "independent_full_text_checked":False})
    components={name:int(original[name]) for name in (
        "deaths_a","deaths_b","deaths_civilians","deaths_unknown")}
    if sum(components.values())!=1:
        raise ValueError("Azerbaijan 1 fatality by side does not match")
    return {"GED_event_id":AZER_ID,"GWNO":AZER_GWNO,"year":AZER_YEAR,
        "UCDP_date_start":original["date_start"][:10],
        "UCDP_date_end":original["date_end"][:10],
        "date_prec":int(original["date_prec"]),
        "fatality_low":int(original["low"]),
        "fatality_best":int(original["best"]),
        "fatality_high":int(original["high"]),
        "fatality_components":components,
        "dyad_name":original["dyad_name"],
        "dyad_new_id":str(original["dyad_new_id"]),
        "side_a":original["side_a"],"side_b":original["side_b"],
        "location_as_GED":original["where_description"],
        "where_coordinates":original["where_coordinates"],
        "where_prec":int(original["where_prec"]),
        "source_original_as_GED":original["source_original"],
        "bibliographic_count":n,"bibliography":sources,
        "source_day_minus_coded_event_day":-11,
        "date_error_proven":False,
        "independent_person_specific_fatality_verified":False,
        "notes":"A single GED citation dated 6 June precedes the precise 17 June event. It could be a previously described incident, issue-date convention, contextual background, or coding mismatch. Bibliographic metadata alone is NOT independent evidence of an incorrectly dated fatality."}


def build(raw):
    prior,selected=read_source_cohort()
    source_registry=json.loads(SOURCE_COHORT.read_text(encoding="utf-8"))
    if (source_registry.get("schema")!="idealab.psico.ged251_near25_source_publication_date_lag_census.v1"
        or source_registry.get("official_GED25_1_zip_SHA256")!=GED_SHA
        or source_registry.get("total_all_type1_GED_event_rows_n")!=118
        or source_registry.get("frozen_GWNO_years_n")!=14):
        raise ValueError("Original fixed 118-event temporal universe drifted")
    rows,azer=source_extract(raw,selected)
    source_ids={e["GED_event_id"] for e in source_registry["event_publication_metadata"]}
    report=[]
    allids=set()
    for key,upstream in sorted(selected.items()):
        group=sorted(rows[key],key=lambda r:r["GED_event_id"])
        originalids={e["GED_event_id"] for e in source_registry["event_publication_metadata"]
                     if (e["GWNO"],e["year"])==key}
        if (len(group)!=upstream["GED_type1_event_rows_including_zero_best_n"]
            or {x["GED_event_id"] for x in group}!=originalids
            or {x["GED_event_id"] for x in group}&allids):
            raise ValueError("Source/casualty cohorts differ by original event ID")
        allids.update(originalids)
        envelope=sum_envelope(group)
        if envelope["best"]!=upstream["GED25_1_type1_annual_best"]:
            raise ValueError("Original annual best changed")
        variable=[r for r in group if len({r["low"],r["best"],r["high"]})>1]
        anomalous=[r for r in group if r["source_fatality_order_nonmonotone"]]
        report.append({"GWNO":key[0],"year":key[1],
            "GED_type1_rows_n":len(group),
            **envelope,
            "rows_with_nonpoint_fatality_estimate_n":len(variable),
            "rows_with_nonpoint_fatality_estimate_ids":[r["GED_event_id"] for r in variable],
            "source_row_nonmonotone_fatality_estimates_n":len(anomalous),
            "source_row_nonmonotone_fatality_estimates":[
                {"GED_event_id":r["GED_event_id"],"event_clarity":r["event_clarity"],
                 "source_low":r["low"],"source_best":r["best"],"source_high":r["high"]}
                for r in anomalous],
            "single_row_low_replacement_flips_best_label_n":sum(
                (envelope["best"]>=THRESHOLD)!=(
                envelope["best"]-r["best"]+r["low"]>=THRESHOLD) for r in group),
            "single_row_high_replacement_flips_best_label_n":sum(
                (envelope["best"]>=THRESHOLD)!=(
                envelope["best"]-r["best"]+r["high"]>=THRESHOLD) for r in group),
        })
    if allids!=source_ids or len(allids)!=118 or len(report)!=14:
        raise ValueError("Loss of source/casualty marginal original frame")
    classes=Counter(r["class"] for r in report)
    azer_metadata=azerbaijan_original_source(azer,source_registry)
    if not any(x["GWNO"]==461 and x["year"]==2022 for x in report):
        raise ValueError("Missing prior pivotal Togo 2022 cohort")
    return {"schema":"idealab.psico.geo_ged251_near25_fatality_interval_v1",
        "research_date":"2026-11-19",
        "method":"componentwise_GED_event_low_best_high_arithmetic_envelopes_NOT_probabilistic_joint_bands",
        "official_GED25_1_zip_sha256":GED_SHA,
        "source_cohort_14_countryyear_sha256":sha256(
            Path(ROOT/"data/geo-ged251-near25-2021-22-countryyear-census.json").read_bytes()).hexdigest(),
        "source_date_118_event_sha256":sha256(SOURCE_COHORT.read_bytes()).hexdigest(),
        "selection_by_only_best_15_35_before_inspection_of_low_high":True,
        "preselected_country_years_n":len(report),
        "replayed_statebased_event_rows_n":len(allids),
        "binary_threshold":THRESHOLD,
        "countryyear_class_counts":dict(sorted(classes.items())),
        "countryyears_best_ge25_n":sum(r["best_label_ge25"] for r in report),
        "nonmonotone_official_event_rows_n":sum(
            r["source_row_nonmonotone_fatality_estimates_n"] for r in report),
        "nonmonotone_official_event_details":[
            {"GWNO":r["GWNO"],"year":r["year"],**e}
            for r in report for e in r["source_row_nonmonotone_fatality_estimates"]],
        "countryyears_low_ge25_n":sum(r["low_label_ge25"] for r in report),
        "countryyears_high_ge25_n":sum(r["high_label_ge25"] for r in report),
        "countryyears_best_vs_low_label_disagreement_n":sum(
            r["best_vs_low_label_disagrees"] for r in report),
        "countryyears_best_vs_high_label_disagreement_n":sum(
            r["best_vs_high_label_disagrees"] for r in report),
        "countryyears_with_single_row_low_label_flip_n":sum(
            r["single_row_low_replacement_flips_best_label_n"]>0 for r in report),
        "countryyears_with_single_row_high_label_flip_n":sum(
            r["single_row_high_replacement_flips_best_label_n"]>0 for r in report),
        "countries":report,"azerbaijan_event427299":azer_metadata,
        "actual_GED_label_corrections_n":0,
        "issued_GEO2027_or_GEO2028_probabilities_modified":False,
        "model_skill_or_Brier_gain_demonstrated":False,
        "limitations":"UCDP GED25.1 official codebook §5.5 permits event_clarity=2 rows with high below best or low after subtraction of more precise subevents. The ORIGINAL preregistration erroneously assumed rowwise low<=best<=high and was amended transparently after initial CI failure and review of the codebook. We report verbatim low/best/high scenario totals, and separate per-row min/max arithmetic envelopes that always contain best but are NOT jointly credible confidence bands. Combinations may have correlated or mutually incompatible casualty estimates. The 14 country-years are conditioned on 2025 GED25.1 best in [15,35], NOT global future uncertainty rates. UCDP source_date is source publication date, not death date. Azerbaijan June6 bibliography precedes June17 exact GED event but proves no miscoding. No GED corrections or prospective GEO skill changes are inferred."}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--emit-report",action="store_true")
    parser.add_argument("--check-report",action="store_true")
    args=parser.parse_args()
    frame,origsha=read_frame()
    audit_existing_forecasts()
    check_frozen_chain()
    report=build(get_official_bytes())
    if args.check_report and report!=json.loads(OUTPUT.read_text(encoding="utf-8")):
        raise ValueError("Official 14 country-year low-best-high sensitivity replay drifted")
    if args.emit_report:
        print("GED251_MARGINAL_INTERVAL_AZER_BEGIN",flush=True)
        print(json.dumps(report,ensure_ascii=False,
                         separators=(",",":"),sort_keys=True),flush=True)
        print("GED251_MARGINAL_INTERVAL_AZER_END",flush=True)
    else:
        print(json.dumps({"n":report["preselected_country_years_n"],
                          "classes":report["countryyear_class_counts"],
                          "Azerbaijan":report["azerbaijan_event427299"]},sort_keys=True))

if __name__=="__main__":
    main()
