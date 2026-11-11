#!/usr/bin/env python3
"""Q-GEO-01: first-party UCDP country-level MULTIPLE-onset vintage discovery.

Uses the official historic download index rather than guessed URLs. This is
SOURCE DISCOVERY, NOT A RELEASE OR A PRE-REGISTERED MODEL. Reports aggregates;
never prints GW country identifiers, labels, or country probabilities.
"""
from __future__ import annotations
import argparse
import csv
import io
import json
from collections import Counter
from inspect_ucdp_archives import (
    HISTORY, MAX_HTML, MAX_CSV, fetch, digest, discover, official_url,
    onset_labels
)
from evaluate_homogeneous_onset2 import SOURCES

VERSIONS=("23.1","25.1")
REQUESTED_CAPTION="Intrastate Country Level Multiple Onset CSV"
SCHEMA="idealab.psico.onset2_country_multiple_vintage_probe.v1"
PINNED={
 "23.1":{
   "url":"https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-multiple-onset-231.csv",
   "sha256":"a31abf6c278bd3a14d6c5b64e075cb38cebe63c95e0535454426c09be21d60e3",
   "last_year":2022,
 },
 "25.1":{
   "url":"https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-multiple-onset-251.csv",
   "sha256":"5fe7411942aa7e6a38d6386faa64f4d7f0703482509f121c4136c0e3223d7f05",
   "last_year":2024,
 }
}

def source_urls(html):
    links=discover(html.decode("utf-8-sig"))
    out={}
    for version in VERSIONS:
        matched=[
           x["url"] for x in links if x["version"]==version and
           "intrastate" in x["caption"].lower() and
           "country level multiple onset" in x["caption"].lower()
        ]
        if len(matched)!=1:
            raise ValueError("Unable to uniquely identify original multiple-onset link for "+version+
                             "; official onset links available: "+
                             json.dumps([{"version":q["version"],"caption":q["caption"]}
                                         for q in links if q["version"]==version][:12]))
        url=official_url(matched[0])
        if not url.startswith("https://ucdp.uu.se/downloads/onset/"):
            raise ValueError("Non-official UCDP source")
        out[version]=url
    if out[VERSIONS[0]]==out[VERSIONS[1]]:
        raise ValueError("Different editions cannot share source bytes")
    if any(out[v]!=PINNED[v]["url"] for v in VERSIONS):
        raise ValueError("Official multiple-onset archive changed from source-pinned links")
    return out

def scan(data,last_year):
    """Preserve episode rows; derive country-year ANY flags without miscounting."""
    reader=csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    fields=reader.fieldnames or []
    if not {"gwno_a","year","onset2","newconf"}.issubset(fields):
        raise ValueError("Multiple-onset source requires both onset2 and newconf")
    groups={}
    row_total=0
    for row in reader:
        code=row["gwno_a"].strip()
        year=int(row["year"])
        onset=row["onset2"].strip()
        newconf=row["newconf"].strip()
        if not code.isdecimal() or onset not in ("0","1") or newconf not in ("0","1"):
            raise ValueError("Non-binary country-level multiple-onset row or country")
        key=(year,code)
        # This official variant can contain several conflict episode rows
        # within the same country-year. NEVER deduplicate them silently.
        if key not in groups:
            groups[key]={"rows":0,"onset2_episode_count":0,
                         "new_conflict_episode_count":0}
        v=groups[key]
        v["rows"]+=1
        v["onset2_episode_count"]+=int(onset)
        v["new_conflict_episode_count"]+=int(newconf)
        row_total+=1
    if len(groups)<9000 or max(y for y,_ in groups)!=last_year:
        raise ValueError("Unexpected multiple onset dataset coverage")
    annual={}
    for year in sorted({year for year,_ in groups}):
        cohort=[x for (y,_),x in groups.items() if y==year]
        annual[year]={
           "country_years":len(cohort),
           "country_years_any_new_conflict":sum(v["new_conflict_episode_count"]>0 for v in cohort),
           "country_years_any_onset2":sum(v["onset2_episode_count"]>0 for v in cohort),
           "new_conflict_episode_rows":sum(v["new_conflict_episode_count"] for v in cohort),
           "onset2_episode_rows":sum(v["onset2_episode_count"] for v in cohort),
           "new_conflict_without_onset2_country_years":sum(
             v["new_conflict_episode_count"]>0 and v["onset2_episode_count"]==0
             for v in cohort)
        }
    return groups,{
        "episode_rows":row_total,
        "unique_country_years":len(groups),
        "duplicate_country_year_keys":sum(x["rows"]>1 for x in groups.values()),
        "extra_episode_rows_over_country_years":row_total-len(groups),
        "max_rows_in_a_country_year":max(x["rows"] for x in groups.values()),
        "first_year":min(y for y,_ in groups),
        "last_year":max(y for y,_ in groups),
        "total_country_years_any_newconf":sum(x["new_conflict_episode_count"]>0 for x in groups.values()),
        "total_country_years_any_onset2":sum(x["onset2_episode_count"]>0 for x in groups.values()),
        "total_newconf_episode_rows":sum(x["new_conflict_episode_count"] for x in groups.values()),
        "total_onset2_episode_rows":sum(x["onset2_episode_count"] for x in groups.values()),
        "latest_year":annual[last_year],
        "recent_2023_2024":{str(year):annual[year] for year in (2023,2024) if year in annual},
        "latest_country_count":annual[last_year]["country_years"],
        "unit":"episode rows (possibly several per country-year); ANY flags for country-year; no row treated as independent country",
        "fields":fields
    }

def probe(fetcher=fetch):
    raw_index=fetcher(HISTORY,MAX_HTML)
    urls=source_urls(raw_index)
    result={
        "schema":SCHEMA,
        "status":"SOURCE_INSPECTION_ONLY_NOT_HISTORICALLY_ISSUED",
        "archive_index":HISTORY,
        "archive_index_sha256":digest(raw_index),
        "official_codebook":"https://ucdp.uu.se/downloads/onset/ucdp-codebook-onset-251.pdf",
        "variant_2":"INTRASTATE_COUNTRY_LEVEL_ONSET",
        "variant_3":"INTRASTATE_COUNTRY_LEVEL_MULTIPLE_ONSET",
        "newconf_distinct_from_onset2":True,
        "duplicate_country_year_rows_are_valid_in_variant_3":True,
        "not_a_prospective_comparison":True,
        "versions":{},
        "comparison":{},
        "provenance_asof_release_timestamp_verified":False,
        "forecasts_2027_changed":False,
        "new_prospective_predictions_issued":0
    }
    for version in VERSIONS:
        data=fetcher(urls[version],MAX_CSV)
        if digest(data)!=PINNED[version]["sha256"]:
            raise ValueError("Official multiple onset source SHA-256 changed: "+version)
        labels,summary=scan(data,PINNED[version]["last_year"])
        country_source=SOURCES[version]
        oldbytes=fetcher(country_source["url"],MAX_CSV)
        if digest(oldbytes)!=country_source["sha256"]:
            raise ValueError("Original country-level onset2 reference has been revised")
        oldlabels=onset_labels(oldbytes)
        common=set(labels)&set(oldlabels)
        newpositive=[k for k in common if labels[k]["onset2_episode_count"]>0 and oldlabels[k]==0]
        reverse=[k for k in common if oldlabels[k]==1 and labels[k]["onset2_episode_count"]==0]
        newconf_concurrent=[k for k in common
                            if labels[k]["new_conflict_episode_count"]>0 and oldlabels[k]==0]
        episodes_with_newconf_no_onset2=[k for k in common
                           if labels[k]["new_conflict_episode_count"]>0 and
                              labels[k]["onset2_episode_count"]==0]
        if len(common)<9000:
            raise ValueError("Country-level variants have too few common country-year rows")
        result["versions"][version]={
           "source_url":urls[version],
           "source_sha256":digest(data),
           "source_bytes":len(data),
           **summary,
           "old_country_onset_sha256":country_source["sha256"],
           "common_country_years_with_variant_2":len(common),
           "multiple_onset2_country_years_not_in_standard_onset2":len(newpositive),
           "standard_onset2_country_years_not_in_multiple_onset2":len(reverse),
           "new_conflict_country_years_not_in_standard_onset2":len(newconf_concurrent),
           "newconf_positive_without_onset2_in_multiple_source":len(episodes_with_newconf_no_onset2),
           "recent_2023_2024_differences":{
              str(y):{
                  "multiple_onset2_positive_standard_negative":sum(k[0]==y for k in newpositive),
                  "standard_onset2_positive_multiple_negative":sum(k[0]==y for k in reverse),
                  "multiple_newconf_positive_standard_onset2_negative":sum(k[0]==y for k in newconf_concurrent),
                  "multiple_newconf_positive_multiple_onset2_negative":sum(k[0]==y for k in episodes_with_newconf_no_onset2)
              }
              for y in (2023,2024) if y<=summary["last_year"]
           }
        }
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report")
    args=ap.parse_args()
    study=probe()
    data=json.dumps(study,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    print("UCDP_MULTIPLE_ONSET_PROBE_BEGIN")
    print(data,end="")
    print("UCDP_MULTIPLE_ONSET_PROBE_END")
    if args.check_report:
        from pathlib import Path
        if Path(args.check_report).read_bytes()!=data.encode("utf8"):
            raise ValueError("Frozen official multiple-onset study does not reproduce")

if __name__=="__main__":
    main()
