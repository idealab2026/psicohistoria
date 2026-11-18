#!/usr/bin/env python3
"""Audit UCDP GED event dates against independent GDELT 1.0 news-event files.

Three PRESELECTED country-year revision cases: Rwanda 2021, Burundi 2022,
Venezuela 2021. Select at most two highest-'best deaths', distinct-date,
single-day geolocated GED events, using official GED25.1 (no outcome-driven
sample tuning). For each date read GDELT daily news-coded event zip and next
day (coverage of news reported late), and compare violent CAMEO roots
18/19/20, country and <=100km. Report near misses, no matches, and archive
SHA. This is ONLY media-footprint feasibility, not event identity or
independent verification of deaths. No forecasts reissued.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
from datetime import date,timedelta
from pathlib import Path
from urllib.request import Request,urlopen
from zipfile import ZipFile

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit as audit_issued,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH,SOURCE_SHA256

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"data/geo-ged-gdelt-external-event-footprint-3case.json"
ANCHOR=ROOT/"data/geo-h2-three-adjacent-vintage-zero-low-11-origin.json"
GED_URL="https://ucdp.uu.se/downloads/ged/ged251-csv.zip"
# Historical daily GDELT 1.0 *media-coded event*, NOT death database.
GDELT_BASE="https://data.gdeltproject.org/events/"
# GWNO, year, GDELT FIPS ActionGeo code, source vintage crossing.
CASES=((517,2021,"RW","23.1->24.1"),
       (516,2022,"BY","23.1->24.1"),
       (101,2021,"VE","24.1->25.1"))
EVENTS_PER_CASE=2
NEAR_KM=100.
STRICT_NEAR_KM=25.
MAX_GED_BYTES=90_000_000
MAX_GDELT_BYTES=15_000_000
MIN_GDELT_ROWS=500
VIOLENT_CAMEO_ROOTS=("18","19","20")
EXPECTED_GED_SHA256=None
EXPECTED_GDELT_SHA256={} # Official first observations frozen by report check.


def fetch(url,cap):
    if (not url.startswith(("https://ucdp.uu.se/downloads/ged/",
                            "https://data.gdeltproject.org/events/"))
        or not url.endswith((".zip",))):
        raise ValueError("Non-allowlisted official UCDP/GDELT ZIP URL")
    with urlopen(Request(url,headers={"User-Agent":
        "IDEA-LAB-GEO-GED-GDELT-EVENT-COMPARABILITY/1.0"}),timeout=80) as resp:
        data=resp.read(cap+1)
    if len(data)>cap or len(data)<1000 or not data.startswith(b"PK"):
        raise ValueError("Official ZIP missing or outside controlled byte limits")
    return data


def eligible_ged_event(row):
    """Exact dated, point-geolocated historical event with best>=1."""
    if not all(k in row for k in
               ("id","year","country_id","best","date_start",
                "date_end","latitude","longitude","type_of_violence")):
        raise ValueError("Official GED25.1 event row missing mandatory column")
    try:
        cid=int(row["country_id"])
        year=int(row["year"])
        best=int(row["best"])
        typ=int(row["type_of_violence"])
        eid=int(row["id"])
        start=date.fromisoformat(row["date_start"][:10])
        end=date.fromisoformat(row["date_end"][:10])
        lat=float(row["latitude"])
        lon=float(row["longitude"])
    except (ValueError,TypeError,OverflowError):
        return None
    if (start!=end or start.year!=year or
        not 1<=best<=1_000_000 or typ not in (1,2,3)
        or not -90<=lat<=90 or not -180<=lon<=180
        or eid<=0 or cid<=0):
        return None
    return {"GED_event_id":eid,"GWNO":cid,"year":year,
            "event_date":start.isoformat(),
            "GED_best_deaths":best,
            "GED_type_of_violence":typ,
            "lat":lat,"lon":lon}


def parse_ged_source(raw):
    """Scan full trusted ZIP stream, retain only preregistered case years."""
    actual=hashlib.sha256(raw).hexdigest()
    if EXPECTED_GED_SHA256 and actual!=EXPECTED_GED_SHA256:
        raise ValueError("Official GED25.1 SHA changed")
    target={(cid,year) for cid,year,_,_ in CASES}
    bycase={key:[] for key in target}
    raw_case_rows={key:0 for key in target}
    rejected={key:0 for key in target}
    with ZipFile(io.BytesIO(raw)) as z:
        candidates=[x for x in z.infolist()
                    if x.filename.lower().endswith(".csv")
                    and not x.is_dir()]
        if len(candidates)!=1 or candidates[0].file_size>900_000_000:
            raise ValueError("Ambiguous or oversized GED event CSV within ZIP")
        member=candidates[0]
        with io.TextIOWrapper(z.open(member),encoding="utf-8-sig",
                              errors="strict",newline="") as stream:
            reader=csv.DictReader(stream)
            needed={"id","year","country_id","best","date_start",
                    "date_end","latitude","longitude","type_of_violence"}
            if not needed.issubset(reader.fieldnames or []):
                raise ValueError("GED event CSV missing mandatory fields")
            total=0
            for row in reader:
                total+=1
                try:
                    cid=int(row["country_id"])
                    year=int(row["year"])
                except (ValueError,TypeError):
                    continue
                key=(cid,year)
                if key not in bycase:
                    continue
                raw_case_rows[key]+=1
                event=eligible_ged_event(row)
                if event is None:
                    rejected[key]+=1
                    continue
                bycase[key].append(event)
    if total<100_000:
        raise ValueError("GED official archive event coverage unexpectedly low")
    selection={}
    for key in sorted(target):
        ranked=sorted(bycase[key],key=lambda e:
                      (-e["GED_best_deaths"],e["event_date"],e["GED_event_id"]))
        chosen=[]
        seen_dates=set()
        for ev in ranked:
            if ev["event_date"] in seen_dates:
                continue
            chosen.append(ev)
            seen_dates.add(ev["event_date"])
            if len(chosen)==EVENTS_PER_CASE:
                break
        selection[key]={
            "all_case_ged_events_n":raw_case_rows[key],
            "single_day_point_eligible_n":len(bycase[key]),
            "ineligible_case_ged_events_n":rejected[key],
            "selected":chosen,
        }
    return {"sha256":actual,"zip_bytes":len(raw),
            "csv_member":member.filename,
            "total_ged_events_scanned":total,
            "case_selection":selection}


def gdelt_day_url(day):
    if not isinstance(day,date) or not 2015<=day.year<=2025:
        raise ValueError("GDELT daily date outside preregistered event period")
    return GDELT_BASE+day.strftime("%Y%m%d")+".export.CSV.zip"


def geo_km(lat1,lon1,lat2,lon2):
    if not all(math.isfinite(x) for x in (lat1,lon1,lat2,lon2)):
        raise ValueError("Non-finite geolocation")
    dlat=math.radians(lat2-lat1)
    dlon=math.radians(lon2-lon1)
    a=math.sin(dlat/2)**2+math.cos(math.radians(lat1))*math.cos(
        math.radians(lat2))*math.sin(dlon/2)**2
    return 6371.0088*2*math.asin(min(1.,math.sqrt(a)))


def parse_gdelt_day(raw,day,needed_fips):
    actual=hashlib.sha256(raw).hexdigest()
    tag=day.strftime("%Y%m%d")
    if tag in EXPECTED_GDELT_SHA256 and actual!=EXPECTED_GDELT_SHA256[tag]:
        raise ValueError("GDELT day archive SHA changed")
    retained=[]
    n=0
    malformed=0
    matching_fips_rows=0
    with ZipFile(io.BytesIO(raw)) as z:
        members=[x for x in z.infolist()
                 if x.filename.endswith(".CSV") and not x.is_dir()]
        if len(members)!=1 or members[0].file_size>190_000_000:
            raise ValueError("GDELT historical daily archive shape changed")
        with io.TextIOWrapper(z.open(members[0]),encoding="latin-1",
                              newline="") as stream:
            reader=csv.reader(stream,delimiter="\t")
            for row in reader:
                n+=1
                if len(row)<57:
                    malformed+=1
                    continue
                fips=row[51].strip()
                if fips not in needed_fips:
                    continue
                matching_fips_rows+=1
                sql_date=row[1]
                if not re.fullmatch(r"20[0-9]{6}",sql_date):
                    malformed+=1
                    continue
                try:
                    lat=float(row[53])
                    lon=float(row[54])
                    gid=int(row[0])
                except (ValueError,OverflowError):
                    continue
                if not (-90<=lat<=90 and -180<=lon<=180):
                    continue
                root=row[28].strip()
                retained.append({"GDELT_event_id":gid,
                    "SQLDATE":sql_date,
                    "CAMEO_root":root,
                    "violent_root":root in VIOLENT_CAMEO_ROOTS,
                    "FIPS":fips,"lat":lat,"lon":lon})
    if n<MIN_GDELT_ROWS or malformed>n*.1:
        raise ValueError("GDELT historical day archive missing or structurally corrupt")
    return {"date":day.isoformat(),"sha256":actual,
            "zip_bytes":len(raw),"total_news_coded_events":n,
            "malformed_rows":malformed,
            "selected_country_rows":matching_fips_rows,
            "geocoded_selected_country_rows":len(retained),
            "events":retained}


def match_event(event,observations,fips):
    """GDELT media footprint, not one-to-one event identity."""
    day=date.fromisoformat(event["event_date"])
    allowed={day.strftime("%Y%m%d")}
    nearby=[]
    others=0
    violent_country=0
    for row in observations:
        if row["FIPS"]!=fips:
            continue
        if row["SQLDATE"] not in allowed:
            continue
        if row["violent_root"]:
            violent_country+=1
        dist=geo_km(event["lat"],event["lon"],row["lat"],row["lon"])
        if dist>NEAR_KM:
            continue
        if row["violent_root"]:
            nearby.append({"GDELT_event_id":row["GDELT_event_id"],
                           "distance_km":round(dist,3),
                           "CAMEO_root":row["CAMEO_root"]})
        else:
            others+=1
    seen={}
    for item in nearby:
        gid=item["GDELT_event_id"]
        if gid not in seen or item["distance_km"]<seen[gid]["distance_km"]:
            seen[gid]=item
    sorted_near=sorted(seen.values(),key=lambda x:
                       (x["distance_km"],x["GDELT_event_id"]))
    return {"same_SQLDATE_same_FIPS_violent_root_events_n":violent_country,
            "same_date_country_nonviolent_near100km_n":others,
            "violent_same_date_near100km_n":len(sorted_near),
            "violent_same_date_near25km_n":sum(
                x["distance_km"]<=STRICT_NEAR_KM for x in sorted_near),
            "closest_five_GDELT_violent_news_events":sorted_near[:5],
            "fatality_confirmation_from_GDELT":False,
            "one_to_one_event_match_verified":False}


def anchored_cases(anchor):
    if (anchor.get("schema")!=
        "idealab.psico.geo_h2_three_adjacent_vintage_zero_low_11_origin.v1"
        or anchor.get("original_GEO2027_SHA256")!=SOURCE_SHA256
        or anchor.get("historical_asof_issues_genuinely_timestamped") is not False):
        raise ValueError("Original 33-fold country-year revision provenance changed")
    bypair={(f["source_pair"],f["origin_year"]):f for f in anchor["folds"]}
    out={}
    for cid,year,fips,pair in CASES:
        fold=bypair[pair,year]
        edits=[r for r in fold["training_zero_low_events"]
               if r["GWNO"]==cid and r["year"]==year]
        if len(edits)!=1 or not edits[0]["old"]==0 or not 1<=edits[0]["new"]<=24:
            raise ValueError("Preselected 0-to-low observed revision anchor changed")
        out[(cid,year)]={"source_pair":pair,"revision":edits[0],
                         "GDELT_FIPS":fips}
    return out


def analyze(ged,gdelt_daily,anchor):
    anchors=anchored_cases(anchor)
    selected=ged["case_selection"]
    rows=[]
    for (cid,year),source in sorted(anchors.items()):
        info=selected[cid,year]
        outcomes=[]
        for event in info["selected"]:
            d=date.fromisoformat(event["event_date"])
            expected=(d,d+timedelta(days=1))
            days=[x.strftime("%Y%m%d") for x in expected]
            if not all(x in gdelt_daily for x in days):
                raise ValueError("Missing preregistered event-date + day-after archive")
            observations=[row for tag in days for row in gdelt_daily[tag]["events"]]
            outcomes.append({**event,
                "GDELT_days_queried":[x.isoformat() for x in expected],
                **match_event(event,observations,source["GDELT_FIPS"])})
        rows.append({"GWNO":cid,"year":year,
                     **source,
                     "GED_case_raw_events_n":info["all_case_ged_events_n"],
                     "GED_case_point_dated_eligible_n":
                         info["single_day_point_eligible_n"],
                     "GED_case_no_eligible_point_date":
                         len(info["selected"])==0,
                     "sample_rule":"top best deaths, at most 2 distinct single-day geocoded GED25.1 events",
                     "sampled_events":outcomes,
                     "has_any_geographic_media_footprint":any(
                         x["violent_same_date_near100km_n"]>0 for x in outcomes)})
    by_day={key:{k:v for k,v in obj.items() if k!="events"}
            for key,obj in sorted(gdelt_daily.items())}
    return {
        "schema":"idealab.psico.geo_ged_gdelt_independent_media_event_footprint_v1",
        "status":"EVENT_LEVEL_EXTERNAL_MEDIA_FEASIBILITY_NOT_FATALITY_GROUND_TRUTH",
        "target_case_revision_release_source":
            "data/geo-h2-three-adjacent-vintage-zero-low-11-origin.json",
        "GEO2027_original_SHA256":SOURCE_SHA256,
        "source_UCDP_GED_25_1_url":GED_URL,
        "source_UCDP_GED_25_1_sha256":ged["sha256"],
        "source_UCDP_GED_25_1_total_events":ged["total_ged_events_scanned"],
        "source_UCDP_GED_25_1_member":ged["csv_member"],
        "source_GDELT_daily_zip_sha256_and_row_counts":by_day,
        "selected_country_years":rows,
        "selected_0_to_low_revision_cases_n":len(rows),
        "case_with_eligible_GED_event_n":sum(bool(x["sampled_events"]) for x in rows),
        "sampled_UCDP_GED_events_n":sum(len(x["sampled_events"]) for x in rows),
        "sampled_events_with_nearby_violent_GDELT_news_footprint_n":sum(
            x["violent_same_date_near100km_n"]>0 for r in rows
            for x in r["sampled_events"]),
        "GDELT_is_a_fatality_ground_truth":False,
        "UCDP_GED_and_OrganizedViolenceCY_are_independent_institutions":False,
        "GDELT_and_UCDP_underlying_news_sources_may_overlap":True,
        "event_identity_certified":False,
        "historical_origin_date_asof_prospectivity_claimed":False,
        "GEO2027_or_GEO2028_original_issues_modified":False,
        "limitations":"Only top two dated point-geolocated GED25.1 events per prespecified revision case, not exhaustive annual matching. GDELT daily 1.0 media coding may miss events, report with lag, geolocate inaccurately, and count news about nonfatal violence. Violent CAMEO 18/19/20 + same date + <=100km is candidate co-occurrence, not independently verified event identity or fatalities; no match does NOT show no violence. UCDP GED and CY are one institution. Date of later GED edition postdates event year.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--check-report",action="store_true")
    p.add_argument("--print-report",action="store_true")
    args=p.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Original GEO2027 issue changed")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    anchor=json.loads(ANCHOR.read_text(encoding="utf-8"))
    anchored_cases(anchor)
    ged=parse_ged_source(fetch(GED_URL,MAX_GED_BYTES))
    required={}
    for (cid,year),obj in ged["case_selection"].items():
        fips=next(f for c,y,f,p in CASES if (c,y)==(cid,year))
        for ev in obj["selected"]:
            day=date.fromisoformat(ev["event_date"])
            for d in (day,day+timedelta(days=1)):
                required[d.strftime("%Y%m%d")]=d
    if len(required)>2*EVENTS_PER_CASE*len(CASES):
        raise AssertionError("Unexpected GDELT external source download fanout")
    gdelt={}
    for tag,day in sorted(required.items()):
        gdelt[tag]=parse_gdelt_day(fetch(gdelt_day_url(day),MAX_GDELT_BYTES),
                                  day,{x[2] for x in CASES})
    report=analyze(ged,gdelt,anchor)
    payload=json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n"
    if args.check_report:
        if json.loads(OUTPUT.read_text(encoding="utf-8"))!=report:
            raise ValueError("Published event evidence report fails external SHA replay")
    if args.print_report:
        print("GED_GDELT_EVENT_BEGIN",flush=True)
        print(payload,end="")
        print("GED_GDELT_EVENT_END",flush=True)
    else:
        print(json.dumps({
            "cases":report["selected_0_to_low_revision_cases_n"],
            "GED_events":report["sampled_UCDP_GED_events_n"],
            "GDELT_archives":len(gdelt),
            "media_footprints":
                report["sampled_events_with_nearby_violent_GDELT_news_footprint_n"],
        },sort_keys=True))


if __name__=="__main__":
    main()
