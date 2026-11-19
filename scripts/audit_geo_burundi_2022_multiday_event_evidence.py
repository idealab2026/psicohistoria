#!/usr/bin/env python3
"""Exploratory, follow-on June 2022 Burundi multi-day GED/GDELT evidence audit.

Independent scientific artifact following the already-frozen THREE CASE audit.
It must NOT rewrite, extend, or rescore that primary analysis.

Official GED 25.1 type-1 event 442626: Burundi (516), 2022-06-19..21,
best=10, (lat, lon)=(-2.708333,29.243056).
GDELT daily 1.0 archival exports 2022-06-19..22 are separate *media-coded*
events, NOT independent adjudicated fatality counts. Event-date window and
publication-day window are tracked separately; country centroids excluded.
A primary contemporaneous journalistic report and an ICG SECONDARY summary
are assessed as potentially dependent and are not two independent witnesses.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from zipfile import ZipFile

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit as audit_issued,
)
from audit_geo_ged_gdelt_independent_media_events import (
    EXPECTED_GED_SHA256, GED_URL, MAX_GED_BYTES, MAX_GDELT_BYTES,
    geo_km, gdelt_day_url, fetch,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256

ROOT=Path(__file__).resolve().parents[1]
PRIOR=ROOT/"data/geo-ged-gdelt-external-event-footprint-3case.json"
REPORT=ROOT/"data/geo-burundi-2022-multiday-independent-event-evidence.json"
GED_ID=442626
GWNO=516
FIPS="BY"
YEAR=2022
BEST=10
START=date(2022,6,19)
END=date(2022,6,21)
REPORT_THROUGH=END+timedelta(days=1)
LAT=-2.708333
LON=29.243056
WINDOW=[START+timedelta(days=i) for i in range((REPORT_THROUGH-START).days+1)]
VIOLENT={"18","19","20"}
EXPECTED_DAILY_SHA256={
    "20220619":"42c087d1091b188761bcf50b7066feb534714cdd61bf92ae161fae08da50da9b",
    "20220620":"f4f73ca505b6eb133a2350c09e64292132618e11e4f5eebbddf434ca32cbba87",
    "20220621":"dd9aa095b48b58c8adceb559737728d68e300495b947e166fc74e8ca11a3c08b",
    "20220622":"14b82c4475e1df059326926ae408271df9a7e7557f71c8709e48dda03dc82881",
}  # Four official GDELT 1.0 daily ZIPs, frozen after first SHA replay.
DOCUMENTS=(
    {"id":"sosmediasburundi-2022-06-21",
     "publication_date":"2022-06-21",
     "url":"https://www.sosmediasburundi.org/2022/06/21/cibitoke-une-dizaine-de-morts-et-plusieurs-blesses-decouverts-a-la-kibira/",
     "publisher":"SOS Médias Burundi",
     "reporting_type":"contemporaneous_local_reporting_with_anonymous_sources",
     "reported_fatalities":10,"reported_injured":8,
     "event_location":"Kibira forest, Mabayi commune, Cibitoke, Burundi",
     "time_claim":"Combat over the three days preceding 2022-06-21",
     "uncertainty":"Armed group identity and alleged Rwandan military involvement not independently established"},
    {"id":"icg-crisiswatch-june-2022",
     "publication_date":"2022-07",
     "url":"https://crisisgroup-staging-3.sbx.so/crisiswatch/july-alerts-and-june-trends-2022",
     "publisher":"International Crisis Group / CrisisWatch",
     "reporting_type":"secondary_monthly_conflict_digest",
     "reported_fatalities":10,"reported_injured":8,
     "event_location":"Mabayi commune, Cibitoke, Burundi",
     "time_claim":"2022-06-19 through 2022-06-21",
     "uncertainty":"Likely overlapping upstream reporting; no separate witness established"},
)
MAX_ARTICLE_DOMAINS=20
MAX_NEAR_CANDIDATES=15


def parse_official_ged_event(raw):
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_GED_SHA256:
        raise ValueError("Official GED 25.1 archive source SHA mismatch")
    with ZipFile(io.BytesIO(raw)) as z:
        files=[x for x in z.infolist() if x.filename.lower().endswith(".csv")
               and not x.is_dir()]
        if len(files)!=1 or files[0].file_size>900_000_000:
            raise ValueError("Unexpected official GED archive member")
        with io.TextIOWrapper(z.open(files[0]),encoding="utf-8-sig",newline="") as stream:
            reader=csv.DictReader(stream)
            required={"id","country_id","year","best","type_of_violence",
                      "date_start","date_end","latitude","longitude"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError("GED25.1 schema missing mandatory event facts")
            selected=None
            count=0
            for r in reader:
                if r["id"].strip()==str(GED_ID):
                    count+=1
                    selected=r
    if count!=1:
        raise ValueError("Expected exactly one official GED event 442626")
    r=selected
    try:
        facts={
            "GED_event_id":int(r["id"]),
            "GWNO":int(r["country_id"]),
            "event_year":int(r["year"]),
            "GED_type_of_violence":int(r["type_of_violence"]),
            "best_fatalities_estimate":int(r["best"]),
            "event_start":r["date_start"][:10],
            "event_end":r["date_end"][:10],
            "latitude":float(r["latitude"]),
            "longitude":float(r["longitude"]),
        }
    except (ValueError,TypeError,OverflowError) as e:
        raise ValueError("Bad original GED event fields") from e
    if (facts["GED_event_id"]!=GED_ID or facts["GWNO"]!=GWNO
        or facts["event_year"]!=YEAR or facts["GED_type_of_violence"]!=1
        or facts["best_fatalities_estimate"]!=BEST
        or facts["event_start"]!=START.isoformat()
        or facts["event_end"]!=END.isoformat()
        or abs(facts["latitude"]-LAT)>1e-6
        or abs(facts["longitude"]-LON)>1e-6):
        raise ValueError("Official event no longer reproduces prespecified case")
    # Neither alleged participants nor counts of injuries are guaranteed by
    # these GED fields. Document them only as source-specific assertions.
    return facts


def parse_gdelt_day(raw,day):
    tag=day.strftime("%Y%m%d")
    digest=hashlib.sha256(raw).hexdigest()
    if tag in EXPECTED_DAILY_SHA256 and EXPECTED_DAILY_SHA256[tag]!=digest:
        raise ValueError("GDELT original daily ZIP SHA changed")
    total=0
    fips_violent=0
    event_date_violent=0
    geocoded=[]
    with ZipFile(io.BytesIO(raw)) as z:
        csv_members=[x for x in z.infolist() if x.filename.endswith(".CSV")
                     and not x.is_dir()]
        if len(csv_members)!=1 or csv_members[0].file_size>190_000_000:
            raise ValueError("Unexpected GDELT daily archive CSV")
        with io.TextIOWrapper(z.open(csv_members[0]),encoding="latin-1",newline="") as stream:
            for row in csv.reader(stream,delimiter="\t"):
                total+=1
                if len(row)<58:
                    raise ValueError("Short GDELT 1.0 event row")
                if row[51].strip()!=FIPS or row[28].strip() not in VIOLENT:
                    continue
                fips_violent+=1
                sql_day=row[1].strip()
                if sql_day not in {d.strftime("%Y%m%d") for d in WINDOW}:
                    continue
                event_date_violent+=1
                try:
                    lon=float(row[54]);lat=float(row[53])
                    event_id=int(row[0])
                    geo_type=int(row[49])
                except (ValueError,OverflowError):
                    continue
                if not (-90<=lat<=90 and -180<=lon<=180 and 0<=geo_type<=5):
                    continue
                article=row[57].strip()
                url=urlsplit(article)
                domain=(url.hostname or "").lower() if url.scheme in ("http","https") else None
                try:
                    added=row[56].strip()
                except IndexError:
                    added=""
                dist=geo_km(LAT,LON,lat,lon)
                geocoded.append({
                    "GDELT_event_id":event_id,
                    "archive_day":day.isoformat(),
                    "inferred_event_date":sql_day,
                    "DATEADDED":added,
                    "geo_type":geo_type,
                    "CAMEO_root":row[28].strip(),
                    "CAMEO_event_code":row[26].strip(),
                    "ActionGeo_name":row[50].strip()[:130],
                    "distance_km":round(dist,3),
                    "source_host":domain,
                    "source_url_sha256":hashlib.sha256(article.encode("latin-1")).hexdigest()
                       if article else None,
                })
    if total<500 or total>600_000:
        raise ValueError("Unplausible GDELT archive event count")
    return {
        "date_of_gdelt_daily_archive":day.isoformat(),
        "source_archive_sha256":digest,
        "source_archive_bytes":len(raw),
        "all_gdelt_event_rows_n":total,
        "all_burundi_violent_root_rows_n":fips_violent,
        "burundi_violent_root_rows_sql_date_in_window_n":event_date_violent,
        "geocoded_violent_rows":geocoded,
    }


def evaluate_window(daily):
    expected={d.strftime("%Y%m%d") for d in WINDOW}
    if set(daily)!=expected:
        raise ValueError("Four preregistered days, including report lag, required")
    all_rows=[x for d in sorted(daily) for x in daily[d]["geocoded_violent_rows"]]
    events={}
    for row in all_rows:
        gid=row["GDELT_event_id"]
        if gid in events and events[gid]!=row:
            raise ValueError("Ambiguous duplicate GDELT event id across daily archives")
        events[gid]=row
    rows=list(events.values())
    eligible_event_days={d.strftime("%Y%m%d") for d in
                         [START,START+timedelta(days=1),END]}
    def summarize(group):
        return {
            "coded_events_n":len(group),
            "within_25km_n":sum(r["distance_km"]<=25 for r in group),
            "within_100km_n":sum(r["distance_km"]<=100 for r in group),
            "within_250km_n":sum(r["distance_km"]<=250 for r in group),
            "city_precision_type4_near100km_n":sum(
                r["geo_type"]==4 and r["distance_km"]<=100 for r in group),
            "country_centroid_type1_near100km_n":sum(
                r["geo_type"]==1 and r["distance_km"]<=100 for r in group),
            "distinct_source_hosts_near100km_n":len(set(
                r["source_host"] for r in group
                if r["distance_km"]<=100 and r["source_host"])),
            "sources_near100km":sorted(set(r["source_host"] for r in group
                if r["distance_km"]<=100 and r["source_host"]))[:MAX_ARTICLE_DOMAINS],
            "closest_coded_events":sorted(group,key=lambda x:
                (x["distance_km"],x["GDELT_event_id"]))[:MAX_NEAR_CANDIDATES],
        }
    event_window=[r for r in rows
                  if r["inferred_event_date"] in eligible_event_days]
    report_lag=[r for r in rows
                if r["inferred_event_date"]==REPORT_THROUGH.strftime("%Y%m%d")]
    # FIPS-only or 250 km matches do not amount to confirmation at Mabayi.
    return {
        "all_observed_GDELT_event_ids_n":len(events),
        "same_2022_06_19_to_21_event_date":summarize(event_window),
        "post_interval_2022_06_22_inferred_event_date_not_a_direct_match":
            summarize(report_lag),
        "all_inferred_dates_including_22":summarize(rows),
        "by_daily_archive":[{
            "archive_day":day,
            **{k:v for k,v in daily[day].items()
               if k!="geocoded_violent_rows"},
        } for day in sorted(daily)],
    }


def verify_prior(prior):
    if (prior.get("schema")!="idealab.psico.geo_ged_gdelt_independent_media_event_footprint_v1"
        or prior.get("GEO2027_original_SHA256")!=SOURCE_SHA256
        or prior.get("GEO2027_or_GEO2028_original_issues_modified") is not False
        or prior.get("source_UCDP_GED_25_1_sha256")!=EXPECTED_GED_SHA256):
        raise ValueError("Primary state-based GED/GDELT scientific issue changed")
    cases={x["GWNO"]:x for x in prior["selected_country_years"]}
    b=cases.get(GWNO)
    if (b is None or b["year"]!=YEAR
        or not b["GED_case_no_eligible_point_date"]
        or b["GED_case_raw_events_n"]!=42
        or b["GED_case_excluded_non_statebased_events_n"]!=41
        or not any(str(x.get("id"))==str(GED_ID)
            and str(x.get("best"))==str(BEST)
            for x in b["GED_case_ineligible_statebased_event_examples"])):
        raise ValueError("Original primary frozen Burundi non-point event mismatch")


def build_report(prior,ged,daily):
    verify_prior(prior)
    if (ged["GED_event_id"]!=GED_ID or
        set(daily)!={d.strftime("%Y%m%d") for d in WINDOW}):
        raise ValueError("Not the anchored Burundi multi-day observation")
    window=evaluate_window(daily)
    return {
        "schema":"idealab.psico.geo_burundi_2022_statebased_multiday_external_evidence.v1",
        "status":"POST_HOC_EXPLORATORY_HISTORICAL_MULTI_DAY_EVIDENCE_NOT_PROSPECTIVE",
        "prior_frozen_primary_report_path":str(PRIOR.relative_to(ROOT)),
        "original_GEO2027_SHA256":SOURCE_SHA256,
        "GED_official_release":"25.1",
        "GED_official_ZIP_url":GED_URL,
        "GED_official_ZIP_sha256":EXPECTED_GED_SHA256,
        "GED_record":ged,
        "GED_event_type_one_only":True,
        "event_date_interval_inclusive":[START.isoformat(),END.isoformat()],
        "extra_reporting_lag_archive_day":REPORT_THROUGH.isoformat(),
        "exact_date_source_selection_posthoc_extension":True,
        "same_source_individual_fatality_confirmation":False,
        "news_media_coded_events_are_a_fatality_ground_truth":False,
        "documentary_source_independence_verified":False,
        "source_documents":[{**x,"same_underlying_reporting_possible":True}
                            for x in DOCUMENTS],
        "GDELT_source":"GDELT 1.0 daily historical events (not fatalities)",
        "GDELT_coded_violence_CAMEO_roots":sorted(VIOLENT),
        "GDELT_FIPS_action_country":FIPS,
        "GDELT_news_events":window,
        "GDELT_news_article_hosts_are_independent_witnesses":False,
        "event_identity_verified_with_primary_source":False,
        "two_original_GEO2027_GEO2028_issues_unchanged":True,
        "limitations":"A posthoc exploratory exception for GED interval 2022-06-19..21; never merged into original point-date sample or denominator. Institutional documents may recycle SOS Médias Burundi; matching killed/injured totals is not independent forensic verification. GDELT 1.0 news event extraction may duplicate articles, use broad or centroid geocodes and have inconsistent event dates. SOURCEURL hosts are neither proof of separate news reporting nor verified event identity. No claim that recorded fatality estimate, identity of alleged Rwandan forces, or state-based threshold is independently proven.",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--print-report",action="store_true")
    parser.add_argument("--check-report",action="store_true")
    args=parser.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("GEO2027 original issued source vector changed")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    prior=json.loads(PRIOR.read_text(encoding="utf-8"))
    verify_prior(prior)
    ged=parse_official_ged_event(fetch(GED_URL,MAX_GED_BYTES))
    daily={}
    for d in WINDOW:
        key=d.strftime("%Y%m%d")
        daily[key]=parse_gdelt_day(fetch(gdelt_day_url(d),MAX_GDELT_BYTES),d)
    report=build_report(prior,ged,daily)
    if args.check_report and json.loads(REPORT.read_text(encoding="utf-8"))!=report:
        raise ValueError("Frozen source SHA or result no longer replays")
    if args.print_report:
        print("BURUNDI_2022_MULTIDAY_BEGIN",flush=True)
        print(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False))
        print("BURUNDI_2022_MULTIDAY_END",flush=True)
    else:
        a=report["GDELT_news_events"]
        print(json.dumps({"GED":GED_ID,
                          "event_window":a["same_2022_06_19_to_21_event_date"],
                          "lag_window":a["post_interval_2022_06_22_inferred_event_date_not_a_direct_match"]},sort_keys=True))


if __name__=="__main__":
    main()
