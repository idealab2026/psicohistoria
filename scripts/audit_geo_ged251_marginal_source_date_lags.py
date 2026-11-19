#!/usr/bin/env python3
"""GED25.1 source-publication lag census in 14 PRESELECTED marginal country-years.

Crucial: source_date = PUBLICATION date, NOT event date. A +1-day lag is
normal reporting, not an erroneous UCDP-coded date. 1753-01-01 is UCDP's
missing date sentinel. Explicit source-text day discordances are separate
manual evidence (only two Uganda Dec events were previously audited).
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter, defaultdict
from datetime import date
from hashlib import sha256
from io import BytesIO, TextIOWrapper
import json
from pathlib import Path
from zipfile import ZipFile

from audit_geo_ged251_stratified_linkage import (
    GED_SHA, read_frame, audit_existing_forecasts, get_official_bytes,
)
from audit_geo_burundi_2022_neighbor_event_linkage import check_frozen_chain

ROOT=Path(__file__).resolve().parents[1]
COHORT=ROOT/"data/geo-ged251-near25-2021-22-countryyear-census.json"
UGANDA_REVIEW=ROOT/"data/geo-ged251-uganda-2022-december-public-source-review.json"
OUTPUT=ROOT/"data/geo-ged251-marginal-source-publication-lags-2021-22.json"
THRESHOLD=25
DATE_SENTINEL=date(1753,1,1)
MAX_EVENTS=1000
REQUIRED={"id","country_id","year","type_of_violence","best","date_start",
          "date_end","date_prec","source_date","number_of_sources"}


def publication_dates(text):
    """Parse GED25.1 semicolon-delimited PUBLICATION dates.

    Never convert missing/placeholder into a measured publication lag.
    If malformed dates occur, retain counts instead of imputing.
    """
    tokens=next(csv.reader([text or ""],delimiter=";",quotechar='"',
                           skipinitialspace=True))
    good,missing,invalid=[],0,0
    for t in tokens:
        token=t.strip()
        if not token or token.lower() in ("na","n/a","none","unknown","null"):
            missing+=1
            continue
        try:
            published=date.fromisoformat(token[:10])
            if len(token)<10 or (len(token)>10 and token[10] not in ("T"," ")):
                raise ValueError("Non ISO publication date")
        except ValueError:
            invalid+=1
            continue
        if published==DATE_SENTINEL:
            missing+=1
        else:
            good.append(published)
    return good,missing,invalid


def lag_classification(first_pub,start,end,prec):
    if start>end:
        raise ValueError("Reversed event window")
    if first_pub is None:
        return "no_valid_publication_date"
    if first_pub<start:
        return "publication_before_event_window_not_a_proven_date_error"
    if first_pub<=end:
        return "publication_within_event_window"
    lag=(first_pub-end).days
    if lag==1:
        return "publication_one_day_after_event_end"
    if lag<=7:
        return "publication_2_to_7_days_after_event_end"
    if lag<=30:
        return "publication_8_to_30_days_after_event_end"
    return "publication_over_30_days_after_event_end"


def read_source_cohort():
    frozen=json.loads(COHORT.read_text(encoding="utf-8"))
    if (frozen.get("schema")!="idealab.psico.geo_ged251_near25_countryyear_census.v1"
        or frozen.get("total_frame_country_year_cells_n")!=392
        or frozen.get("official_GED25_1_zip_SHA256")!=GED_SHA
        or frozen.get("prespecified_band_inclusive")!=[15,35]
        or frozen.get("marginal_country_years_n")!=14):
        raise ValueError("Prior 14-country-year marginal cohort has changed")
    pairs={(r["GWNO"],r["year"]):r for r in frozen["marginal_country_years"]}
    if len(pairs)!=14:
        raise ValueError("Marginal cohort repeated country-year")
    return frozen,pairs


def scan_official_source_dates(raw,selected):
    if sha256(raw).hexdigest()!=GED_SHA:
        raise ValueError("Official GED25.1 archive SHA256 mismatch")
    records=defaultdict(list)
    with ZipFile(BytesIO(raw)) as z:
        members=[x for x in z.infolist()
                 if x.filename.lower().endswith(".csv") and not x.is_dir()]
        if len(members)!=1 or members[0].file_size>900_000_000:
            raise ValueError("Expected exactly one bounded UCDP GED CSV")
        with TextIOWrapper(z.open(members[0]),encoding="utf-8-sig",newline="") as f:
            reader=csv.DictReader(f)
            if not REQUIRED.issubset(reader.fieldnames or []):
                raise ValueError("Missing required GED dates or precision metadata")
            ids=set()
            for row in reader:
                try:
                    gwno,year=int(row["country_id"]),int(row["year"])
                except (ValueError,TypeError):
                    continue
                key=(gwno,year)
                if key not in selected or row["type_of_violence"].strip()!="1":
                    continue
                try:
                    eid,best,prec=(int(row[x]) for x in
                                  ("id","best","date_prec"))
                    start=date.fromisoformat(row["date_start"][:10])
                    end=date.fromisoformat(row["date_end"][:10])
                except (TypeError,ValueError) as err:
                    raise ValueError("Malformed marginal GED event/date") from err
                if (eid<=0 or eid in ids or best<0 or not 1<=prec<=5
                    or end<start or start.year!=year or end.year!=year):
                    raise ValueError("Invalid marginal GED source event")
                ids.add(eid)
                pub_dates,missing,invalid=publication_dates(row["source_date"])
                first=min(pub_dates) if pub_dates else None
                last=max(pub_dates) if pub_dates else None
                daylag=((first-end).days if first else None)
                exact=prec==1 and start==end
                record={
                    "GED_event_id":eid,"GWNO":gwno,"year":year,"best":best,
                    "date_start":start.isoformat(),
                    "date_end":end.isoformat(),"date_prec":prec,
                    "exact_day_coded":exact,
                    "source_date_tokens_valid_n":len(pub_dates),
                    "source_date_tokens_missing_or_1753_n":missing,
                    "source_date_tokens_unparseable_n":invalid,
                    "earliest_publication_date":first.isoformat() if first else None,
                    "latest_publication_date":last.isoformat() if last else None,
                    "earliest_publication_minus_event_end_days":daylag,
                    "publication_lag_category":lag_classification(
                        first,start,end,prec),
                    "one_day_publication_lag_is_error":False,
                }
                records[key].append(record)
    if sum(len(rows) for rows in records.values())>MAX_EVENTS:
        raise ValueError("Unexpectedly large near-threshold cohort")
    for key,upstream in selected.items():
        rows=records[key]
        if (len(rows)!=upstream["GED_type1_event_rows_including_zero_best_n"]
            or sum(x["best"] for x in rows)!=
                        upstream["GED25_1_type1_annual_best"]):
            raise ValueError("Source-date cohort fails frozen annual totals/rows")
    return records


def manual_text_discordances(records):
    """Two previously source-reviewed Ukraine? No: Uganda exact-day controls.

    They are not discovered from source_date; use contemporaneous explicit
    event-day claims in the frozen PR140 review, not publication lags.
    """
    reviewed=json.loads(UGANDA_REVIEW.read_text(encoding="utf-8"))
    if (reviewed.get("schema")!="idealab.psico.uganda_december2022_public_source_reconciliation.v1"
        or reviewed.get("event_fatality_labels_modified") is not False
        or reviewed.get("duplicate_events_confirmed_by_external_sources_n")!=0):
        raise ValueError("Prior manual date-source review changed")
    byid={x["GED_event_id"]:x for rows in records.values() for x in rows}
    flagged=[]
    for original in reviewed["episode_claims"]:
        eid=original["GED_id"]
        if eid not in (460859,462156):
            continue
        if eid not in byid:
            raise ValueError("Prior Uganda event missing in marginal source cohort")
        ev=byid[eid]
        if (ev["date_prec"]!=1
            or original["GED_date_start"]!=ev["date_start"]
            or original["GED_date_end"]!=ev["date_end"]
            or original["GED_best"]!=ev["best"]):
            raise ValueError("Manually reviewed event diverges from official")
        explicit=original["reported_event_dates"]
        if len(explicit)!=1:
            raise ValueError("Previously quoted day not individually discerned")
        source_day=date.fromisoformat(explicit[0])
        ged_day=date.fromisoformat(ev["date_start"])
        shift=(ged_day-source_day).days
        if shift!=1:
            raise ValueError("Previously reviewed one-day mismatch changed")
        flagged.append({
            "GED_event_id":eid,"GWNO":ev["GWNO"],"year":ev["year"],
            "GED_exact_date":ev["date_start"],
            "contemporaneous_source_text_event_day":source_day.isoformat(),
            "coded_minus_reported_event_day_days":shift,
            "earliest_UCDP_source_publication":ev["earliest_publication_date"],
            "UCDP_official_event_date_changed":False,
            "coding_error_adjudicated":False,
        })
    if len(flagged)!=2:
        raise ValueError("Source-reviewed time offsets must be precisely two")
    return sorted(flagged,key=lambda x:x["GED_event_id"])


def build(raw):
    cohort,selected=read_source_cohort()
    all_records=scan_official_source_dates(raw,selected)
    marginal_rows=[]
    all_events=[]
    for (gwno,year),upstream in sorted(selected.items()):
        events=sorted(all_records[(gwno,year)],key=lambda x:x["GED_event_id"])
        total=upstream["GED25_1_type1_annual_best"]
        for e in events:
            e["single_event_deletion_would_cross_25"]=(
                total>=THRESHOLD and total-e["best"]<THRESHOLD)
        exact=[x for x in events if x["exact_day_coded"]]
        marginal_rows.append({
            "GWNO":gwno,"year":year,"GED_statebased_best_total":total,
            "statebased_GED_events_n":len(events),
            "exact_day_coded_events_n":len(exact),
            "any_valid_source_publication_date_events_n":sum(
                x["earliest_publication_date"] is not None for x in events),
            "publication_first_after_event_end_one_day_events_n":sum(
                x["publication_lag_category"]==
                "publication_one_day_after_event_end" for x in events),
            "earliest_publication_before_event_window_events_n":sum(
                x["publication_lag_category"]==
                "publication_before_event_window_not_a_proven_date_error"
                for x in events),
            "individually_pivotal_GED_rows_n":sum(
                x["single_event_deletion_would_cross_25"] for x in events),
            "GED_event_ids":[x["GED_event_id"] for x in events],
        })
        all_events.extend(events)
    manual=manual_text_discordances(all_records)
    categories=Counter(e["publication_lag_category"] for e in all_events)
    precise=[x for x in all_events if x["exact_day_coded"]]
    pivot=[x for x in all_events if x["single_event_deletion_would_cross_25"]]
    if (len(marginal_rows)!=14 or len(pivot)!=13
        or len(manual)!=2):
        raise ValueError("Previously fixed near25 row/hand-checked anchors changed")
    return {
        "schema":"idealab.psico.ged251_near25_source_publication_date_lag_census.v1",
        "research_date":"2026-11-19",
        "phase":"MEASURED_PUBLICATION_LAGS_ONLY__TWO_PREVIOUS_TEXT_DAY_ALERTS_NOT_ADJUDICATED",
        "official_GED25_1_zip_SHA256":GED_SHA,
        "original_marginal_countryyear_study_SHA256":sha256(
            COHORT.read_bytes()).hexdigest(),
        "original_Uganda_december_public_review_SHA256":sha256(
            UGANDA_REVIEW.read_bytes()).hexdigest(),
        "frozen_GWNO_years_n":14,
        "total_all_type1_GED_event_rows_n":len(all_events),
        "exact_day_coded_events_n":len(precise),
        "events_without_valid_publication_date_n":categories[
            "no_valid_publication_date"],
        "all_event_publication_lag_category_counts":dict(sorted(categories.items())),
        "exact_day_publication_lag_category_counts":dict(sorted(
            Counter(x["publication_lag_category"] for x in precise).items())),
        "pivotal_event_rows_n":len(pivot),
        "pivotal_event_publication_categories":dict(sorted(
            Counter(x["publication_lag_category"] for x in pivot).items())),
        "source_date_1753_or_missing_token_count":sum(
            x["source_date_tokens_missing_or_1753_n"] for x in all_events),
        "source_date_unparseable_token_count":sum(
            x["source_date_tokens_unparseable_n"] for x in all_events),
        "manual_source_text_claims_of_distinct_event_day_n":len(manual),
        "manual_exact_event_date_discordances_from_PR140":manual,
        "countryyear_summaries":marginal_rows,
        "event_publication_metadata":sorted(all_events,key=lambda x:x["GED_event_id"]),
        "actual_event_date_corrections_made":0,
        "actual_annual_target_labels_changed":0,
        "issued_GEO2027_GEO2028_probabilities_modified":False,
        "model_skill_or_Brier_improvement_claimed":False,
        "this_is_not_population_error_prevalence_estimate":True,
        "limitations":"UCDP GED25.1 source_date is PUBLICATION date, not date of observed event. Earliest publication may precede a multi-day event's end or even predate an event as contextual reporting; that is a review trigger, not a proven source-coding error. 1753-01-01 is UCDP default missing-source date and never assigned a lag. Date_prec 1 means exact coded event day, but a +1 day after event publication is a NORMAL publishing lag. Two specific Uganda events were already verified as text-day claims in separate historical public documents; they are not a new data-mined incidence estimate. Near25 selection by UCDP best total gives a conditional sample of 14 country-years, not an all-country random prevalence survey. UCDP historical GED25.1 source vintage (2025 extraction) must never be treated as a 2021-22 real-time signal. No source independent victim identities or event-day updates are certified.",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--emit-report",action="store_true")
    parser.add_argument("--check-report",action="store_true")
    args=parser.parse_args()
    frame,original_sha=read_frame()
    audit_existing_forecasts()
    check_frozen_chain()
    frozen,selected=read_source_cohort()
    if not set(c for c,_ in selected).issubset(frame):
        raise ValueError("Marginal cohort left original GEO2027 frame")
    report=build(get_official_bytes())
    if args.check_report:
        if json.loads(OUTPUT.read_text(encoding="utf-8"))!=report:
            raise ValueError("Official UCDP 25.1 source-publication lag report changed")
    if args.emit_report:
        print("GED251_MARGINAL_PUBLICATION_LAGS_BEGIN",flush=True)
        print(json.dumps(report,ensure_ascii=False,separators=(",",":"),
                         sort_keys=True),flush=True)
        print("GED251_MARGINAL_PUBLICATION_LAGS_END",flush=True)
    else:
        print(json.dumps({
            "events":report["total_all_type1_GED_event_rows_n"],
            "countryyears":report["frozen_GWNO_years_n"],
            "lag_categories":report["all_event_publication_lag_category_counts"],
            "documented_source_text_day_mismatches":report[
                "manual_source_text_claims_of_distinct_event_day_n"]
        },sort_keys=True))


if __name__=="__main__":
    main()
