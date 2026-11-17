#!/usr/bin/env python3
"""Official archived UCDP GED -> OrganizedViolenceCY crosswalk feasibility.

UCDP GED rows are *events*, not OrganizedViolenceCY country-years. The only
identification check that can support equivalence is GED 23.1 against the
SAME RELEASE OrganizedViolenceCY 23.1. Earlier GED 19.1 and 22.1 remain
separate historical event-data sources, never quietly relabelled as CY.
SHA-pin official archives; reject missing/corrupt data; no future forecast.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from zipfile import ZipFile

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit as audit_issued,
)
from backtest_archived_country_vintages import SOURCES
from experiment_geo2027_intensity_markov_cross_release import (
    EXPECTED_ROWS, parse_counts,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data/geo-ged-old-vintage-countryyear-feasibility.json"
ARCHIVE = "https://ucdp.uu.se/downloads/olddw.html"
MAX_ZIP = 95_000_000
VERSIONS = ("17.1", "18.1", "19.1", "20.1", "21.1", "22.1", "23.1")
SELECTED = ("19.1", "22.1", "23.1")
GED_URLS = {
    version: "https://ucdp.uu.se/downloads/ged/ged" +
             version.replace(".", "") + "-csv.zip"
    for version in SELECTED
}
GED_221_CODEBOOK = "https://ucdp.uu.se/downloads/ged/ged221.pdf"
CY_VERSION = "23.1"
THRESHOLD = 25
MIN_YEAR = 1989
COMPARISON_YEARS = tuple(range(2011, 2023))


class ArchivedGEDLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.heading_tag = None
        self.heading_parts = []
        self.in_ged = False
        self.version = None
        self.links = []
        self.href = None
        self.label = []
    def handle_starttag(self, tag, attrs):
        if tag in ("h2", "h3"):
            self.heading_tag=tag
            self.heading_parts=[]
        elif tag=="a" and self.in_ged:
            self.href=dict(attrs).get("href")
            self.label=[]
    def handle_endtag(self, tag):
        if tag==self.heading_tag:
            title=" ".join(" ".join(self.heading_parts).split()).lower()
            self.in_ged="georeferenced event dataset" in title
            self.version=None
            self.heading_tag=None
        elif tag=="a" and self.href is not None:
            label=" ".join(" ".join(self.label).split()).upper()
            if self.in_ged and label in ("CSV", "CODEBOOK") and self.version:
                uri=urljoin(ARCHIVE,self.href)
                self.links.append({
                    "version":self.version,"format":label,"url":uri})
            self.href=None
    def handle_data(self, content):
        if self.heading_tag is not None:
            self.heading_parts.append(content)
        elif self.in_ged:
            match=re.search(r"\bGED\s+(\d{1,2}\.\d)\s*:", content,re.I)
            if match:
                self.version=match.group(1)
            elif re.search(r"\bGED\s+[^\d\s]", content, re.I):
                # UCDP lists special GED Syria (652...) directly after 19.1.
                # Never attribute its CSV to the preceding general GED edition.
                self.version=None
        if self.href is not None:
            self.label.append(content)


def discover_ged(raw):
    parser=ArchivedGEDLinks()
    parser.feed(raw.decode("utf-8-sig"))
    observed={}
    for item in parser.links:
        p=urlsplit(item["url"])
        valid=(p.scheme=="https" and p.netloc=="ucdp.uu.se" and
               p.path.startswith("/downloads/ged/") and
               not p.query and not p.fragment)
        version=item["version"]
        if not valid:
            # Some historical entries link outside the GED folder and are
            # irrelevant to the three exact official downloads. Never ingest
            # them; selected releases must remain strictly allowlisted.
            if (version in SELECTED and item["format"]=="CSV") or (
                version=="22.1" and item["format"]=="CODEBOOK"):
                raise ValueError("Selected official GED link left allowlisted "
                                 "UCDP host/path: "+repr(item))
            continue
        observed.setdefault(version, {})
        if item["format"] in observed[version]:
            raise ValueError("Ambiguous multiple archived GED links for one version/format")
        observed[version][item["format"]]=item["url"]
    return observed


def _int(field, what):
    if isinstance(field,str):
        field=field.strip()
    if not isinstance(field,str) or not re.fullmatch(r"\d+",field):
        raise ValueError("Noninteger official GED " + what + ": " + str(field)[:30])
    return int(field)


def parse_ged(raw, version, *, expected_sha256=None):
    """Only one CSV member; inspect & aggregate event best by location/yr/type."""
    actual=hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and actual!=expected_sha256:
        raise ValueError("Original official GED ZIP SHA-256 mismatch")
    if not raw.startswith(b"PK"):
        raise ValueError("GED official archive not a ZIP")
    with ZipFile(io.BytesIO(raw)) as z:
        members=[x for x in z.namelist()
                 if x.lower().endswith(".csv") and not x.endswith("/")]
        required={"id","year","country_id","type_of_violence","best"}
        eligible=[]
        encodings={}
        for member in members:
            with z.open(member) as reader:
                prefix=reader.read(32768)
            try:
                prefix.decode("utf-8-sig")
                enc="utf-8-sig"
            except UnicodeDecodeError:
                # Some pre-2020 source ZIP members use a legacy 8-bit encoding.
                # Use byte-total latin-1 for numeric-header inspection only,
                # and must be explicitly recorded instead of silently ignored.
                enc="latin-1"
            encodings[member]=enc
            with io.TextIOWrapper(z.open(member),encoding=enc,
                                  newline="") as probe:
                header=next(csv.reader(probe), [])
            if required.issubset(header):
                eligible.append(member)
        if len(eligible)!=1:
            raise ValueError("Expected exactly one GED event-table CSV member with "
                             "id/year/country/type/best, discovered " +
                             repr({"all_csv":members[:12], "matched":eligible[:12],
                                   "first_zip_members":z.namelist()[:8]}))
        selected_member=eligible[0]
        counts=defaultdict(int)
        deaths_by_type={1:0,2:0,3:0}
        events_by_type={1:0,2:0,3:0}
        years=set()
        seen_ids=set()
        bad_estimate_order=0
        omitted_country=0
        with io.TextIOWrapper(z.open(selected_member),encoding=encodings[selected_member],
                              newline="") as source:
            reader=csv.DictReader(source)
            fields=set(reader.fieldnames or ())
            if not required.issubset(fields):
                raise ValueError("GED event schema lacks immutable required fields: "+
                                 repr(sorted(required-fields)))
            for r in reader:
                eid=_int(r["id"],"event id")
                if eid in seen_ids:
                    raise ValueError("Duplicate official GED event id")
                seen_ids.add(eid)
                y=_int(r["year"],"year")
                typ=_int(r["type_of_violence"],"violence type")
                if not (MIN_YEAR<=y<=2025) or typ not in (1,2,3):
                    raise ValueError("GED out-of-range year or violence type")
                if r["country_id"].strip() in ("", "NA"):
                    omitted_country+=1
                    continue
                cid=_int(r["country_id"],"GWNO country")
                fatalities=_int(r["best"],"best deaths")
                if not 1<=cid<=2000:
                    raise ValueError("GED country ID outside GWNO range")
                if "low" in fields and "high" in fields:
                    lo=_int(r["low"],"low deaths")
                    hi=_int(r["high"],"high deaths")
                    if not lo<=fatalities<=hi:
                        bad_estimate_order+=1
                years.add(y)
                events_by_type[typ]+=1
                deaths_by_type[typ]+=fatalities
                if typ==1:
                    counts[(cid,y)]+=fatalities
        if len(seen_ids)<1000 or not years or not counts:
            raise ValueError("Insufficient official GED archive event coverage")
        return {
            "version":version,
            "sha256":actual,
            "zip_bytes":len(raw),
            "csv_member":selected_member,
            "csv_detected_encoding":encodings[selected_member],
            "header":list(reader.fieldnames or []),
            "event_ids_unique":True,
            "event_count":len(seen_ids),
            "events_without_country_GWNO":omitted_country,
            "first_recorded_event_year":min(years),
            "last_recorded_event_year":max(years),
            "events_by_violence_type":events_by_type,
            "total_best_deaths_by_violence_type":deaths_by_type,
            "nonmonotonic_low_best_high_event_n":bad_estimate_order,
            "distinct_state_based_country_year_n":len(counts),
        }, dict(counts)


def compare_state_based(ged, target, ids, years):
    """Uniform fixed GWNO-year domain, *including* the zero-event country-years."""
    if len(ids)!=196 or len(set(ids))!=196 or not years:
        raise ValueError("Fixed issued riskset and comparison years required")
    extra=[]
    annual=[]
    exact=0
    binary_match=0
    total_abs=0
    signed=0
    positives_ged=positives_target=0
    rows=0
    for year in years:
        changed=[]
        absolute=0
        threshold_disagree=0
        for cid in ids:
            x=ged.get((cid,year),0)
            y=target.get((cid,year),0)
            if not (type(x) is int and type(y) is int and x>=0 and y>=0):
                raise ValueError("Invalid nonnegative GED/CY deaths")
            rows+=1
            dx=x-y
            signed+=dx
            absolute+=abs(dx)
            total_abs+=abs(dx)
            exact+=int(x==y)
            s=int(x>=THRESHOLD)
            t=int(y>=THRESHOLD)
            positives_ged+=s
            positives_target+=t
            binary_match+=int(s==t)
            threshold_disagree+=int(s!=t)
            if x!=y:
                changed.append({
                    "year":year,"GWNO":cid,"ged_deaths":x,
                    "comparison_deaths":y,
                    "absolute_difference":abs(dx),
                    "ged_active":bool(s),"comparison_active":bool(t),
                })
        annual.append({
            "year":year,"total_absolute_death_difference":absolute,
            "mismatched_GWNO_n":len(changed),
            "activity_binary_disagreement_n":threshold_disagree,
        })
        extra.extend(changed)
    if rows!=196*len(years) or not 0<=exact<=rows:
        raise AssertionError("Unexpected fixed cohort comparison size")
    return {
        "country_years":rows,
        "country_n":196,
        "years":list(years),
        "exact_death_count_match_n":exact,
        "exact_death_count_match_rate":exact/rows,
        "binary_state_match_n":binary_match,
        "binary_state_match_rate":binary_match/rows,
        "threshold_disagreement_n":rows-binary_match,
        "total_absolute_death_difference":total_abs,
        "signed_ged_minus_comparison_death_difference":signed,
        "ged_active_country_year_n":positives_ged,
        "comparison_active_country_year_n":positives_target,
        "annual":annual,
        "largest_ten_discrepancies":sorted(
            extra,key=lambda r:(-r["absolute_difference"],r["year"],r["GWNO"]))[:10],
    }


def replay(sources, originals, fixed_ids, catalogue):
    if (set(sources)!=set(SELECTED) or
        sorted(fixed_ids)!=sorted(set(fixed_ids)) or len(fixed_ids)!=196 or
        set(VERSIONS)-set(catalogue) or
        any(catalogue[v].get("CSV")!=GED_URLS[v] for v in SELECTED) or
        catalogue["22.1"].get("CODEBOOK")!=GED_221_CODEBOOK):
        raise ValueError("Official GED version listing, country cohort or exact download path invalid")
    if not (len(originals)==EXPECTED_ROWS[CY_VERSION] and
            all((cid,year) in originals for cid in fixed_ids
                for year in COMPARISON_YEARS)):
        raise ValueError("Official OrganizedViolenceCY target risk set incomplete")
    metadata={}
    sums={}
    for v in SELECTED:
        metadata[v],sums[v]=parse_ged(sources[v],v)
    if (metadata["19.1"]["last_recorded_event_year"]!=2018 or
        metadata["22.1"]["last_recorded_event_year"]!=2021 or
        metadata["23.1"]["last_recorded_event_year"]!=2022):
        raise ValueError("GED old official edition temporal coverage changed")
    same=compare_state_based(sums["23.1"], originals, fixed_ids, COMPARISON_YEARS)
    compare_old={}
    for old,year_stop in (("19.1",2018),("22.1",2021)):
        years=tuple(range(2011,year_stop+1))
        compare_old[old]={
            "same_years_vs_GED23_1":compare_state_based(
                sums[old],sums["23.1"],fixed_ids,years),
            "same_years_vs_OrganizedViolenceCY23_1_not_same_vintage":
                compare_state_based(sums[old],originals,fixed_ids,years),
            "source_last_recorded_year":year_stop,
            "not_same_release_as_CY23_1":True,
        }
    is_compatible=(same["threshold_disagreement_n"]==0 and
                   same["total_absolute_death_difference"]==0)
    return {
        "schema":"idealab.psico.legacy_ged_to_countryyear_equivalence_feasibility.v1",
        "status":"OFFICIAL_SHA_PINNED_EVENT_AGGREGATION_DIAGNOSTIC_NOT_BACKTEST",
        "official_archive_url":ARCHIVE,
        "source_formats":{"GED":"event CSV inside ZIP",
                          "OrganizedViolenceCY":"country-year XLSX"},
        "original_forecast_2027_sha256":SOURCE_SHA256,
        "reference_organizedviolencecy23_1_sha256":SOURCES[CY_VERSION]["sha256"],
        "GED_metadata":metadata,
        "official_ged_archive_17_1_through_23_1_listed":True,
        "documented_ged221_extraction_day_from_official_codebook":
            "2022-04-27",
        "ged221_documented_extraction_is_not_file_download_release_date":True,
        "official_GED23_1_vs_OrganizedViolenceCY23_1_same_version":
            same,
        "historic_GED_against_later_23_1_revised_records":compare_old,
        "state_based_filter":"type_of_violence == 1",
        "raw_aggregation":"sum GED event best within country_id × year; absent event coded 0 for comparison only",
        "raw_aggregation_exactly_reproduces_same_vintage_CY23_1":is_compatible,
        "historical_GED_for_original_GEO_CY_predictions_authorized":False,
        "new_historical_issued_predictions":0,
        "GEO2027_or_GEO2028_original_issued_probabilities_modified":False,
        "no_2027_outcomes_scored":True,
        "no_2027_predictions_changed":True,
        "scope":"Evaluate measurement compatibility BEFORE considering any historical backtest",
        "limitations":(
            "GED is an event dataset, not country-year estimation. A raw best "
            "sum can diverge from OrganizedViolenceCY's built-in aggregation, "
            "zero-filling, geography and 25-death dyad inclusion rules. Old "
            "GED 19.1/22.1 versus CY 23.1 also differs by subsequent source "
            "revision, not just aggregation algorithm. Absence of an event in "
            "one edition is not evidence of absence of violence. GED releases "
            "were not cryptographically timestamp-notarized at each simulated "
            "forecast origin. No model has been fitted or scored on GED here."
        ),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report",action="store_true")
    parser.add_argument("--print-report",action="store_true")
    args=parser.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Original issued GEO 2027 probabilities changed")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),
                 ORIGINAL.read_bytes(),OLD_SHADOW.read_bytes(),
                 OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    catalogue=discover_ged(request(ARCHIVE))
    raw={}
    for v in SELECTED:
        raw[v]=request(GED_URLS[v],MAX_ZIP)
    cy_raw=request(SOURCES[CY_VERSION]["url"],8_000_000)
    cy_counts=parse_counts(cy_raw,CY_VERSION)
    cy={(cid,year):d for cid,h in cy_counts.items() for year,d in h.items()}
    frozen=json.loads(ISSUE.read_text(encoding="utf8"))
    report=replay(raw,cy,[r["country_id"] for r in frozen["countries"]],
                  catalogue)
    codebook=request(GED_221_CODEBOOK,8_000_000)
    if not codebook.startswith(b"%PDF-"):
        raise ValueError("GED 22.1 official codebook not PDF")
    report["ged221_codebook_current_sha256"]=hashlib.sha256(codebook).hexdigest()
    payload=json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if args.check_report and REPORT.read_bytes()!=payload.encode("utf-8"):
        raise ValueError("Official SHA-verified GED-to-CY bridge report changed")
    print("GEO_GED_LEGACY_BRIDGE_BEGIN")
    if args.print_report:
        print(payload,end="")
    else:
        print(json.dumps({
            "same_vintage":report[
                "official_GED23_1_vs_OrganizedViolenceCY23_1_same_version"],
            "old_years":{v:{
                "event_n":report["GED_metadata"][v]["event_count"],
                "state_year":report["GED_metadata"][v]["last_recorded_event_year"],
                "binary_disagreement_vs_revised23_1":
                    report["historic_GED_against_later_23_1_revised_records"][v][
                        "same_years_vs_OrganizedViolenceCY23_1_not_same_vintage"][
                            "threshold_disagreement_n"],
            } for v in ("19.1","22.1")},
            "bridge_authorized":report[
                "historical_GED_for_original_GEO_CY_predictions_authorized"],
        },indent=2,sort_keys=True))
    print("GEO_GED_LEGACY_BRIDGE_END")


if __name__=="__main__":
    main()
