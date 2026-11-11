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
    return out

def scan(data,last_year):
    reader=csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    fields=reader.fieldnames or []
    if not {"gwno_a","year","onset2"}.issubset(fields):
        raise ValueError("Multiple-onset source lacks country-year onset2")
    counts=Counter()
    annual=Counter()
    labels={}
    for row in reader:
        code=row["gwno_a"].strip()
        year=int(row["year"])
        v=row["onset2"].strip()
        if not code.isdecimal() or v not in ("0","1"):
            raise ValueError("Non-binary country-level multiple-onset row or country")
        key=(year,code)
        if key in labels:
            raise ValueError("Duplicate country-year: multiple-onset dataset may require another unit")
        labels[key]=int(v)
        counts[v]+=1
        annual[year]+=int(v)
    if len(labels)<9000 or max(y for y,_ in labels)!=last_year:
        raise ValueError("Unexpected multiple onset dataset coverage")
    return labels,{
        "rows":len(labels),"first_year":min(y for y,_ in labels),
        "last_year":max(y for y,_ in labels),
        "total_positives":counts["1"],
        "latest_year_positives":annual[last_year],
        "latest_country_count":len({code for y,code in labels if y==last_year}),
        "country_year_unique":True,
        "binary_onset2":True,
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
        "versions":{},
        "comparison":{},
        "provenance_asof_release_timestamp_verified":False,
        "forecasts_2027_changed":False,
        "new_prospective_predictions_issued":0
    }
    for version in VERSIONS:
        data=fetcher(urls[version],MAX_CSV)
        labels,summary=scan(data,2022 if version=="23.1" else 2024)
        country_source=SOURCES[version]
        oldbytes=fetcher(country_source["url"],MAX_CSV)
        if digest(oldbytes)!=country_source["sha256"]:
            raise ValueError("Original country-level onset2 reference has been revised")
        oldlabels=onset_labels(oldbytes)
        common=set(labels)&set(oldlabels)
        newpositive=[k for k in common if labels[k]==1 and oldlabels[k]==0]
        reverse=[k for k in common if oldlabels[k]==1 and labels[k]==0]
        if len(common)<9000:
            raise ValueError("Country-level variants have too few common country-year rows")
        result["versions"][version]={
           "source_url":urls[version],
           "source_sha256":digest(data),
           "source_bytes":len(data),
           **summary,
           "old_country_onset_sha256":country_source["sha256"],
           "common_country_years_with_variant_2":len(common),
           "multiple_positive_country_years_not_in_country_onset":len(newpositive),
           "country_onset_positive_country_years_not_in_multiple":len(reverse),
           "new_positive_2023_2024":{
              str(y):sum(labels[k]==1 and oldlabels[k]==0 and k[0]==y for k in common)
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
