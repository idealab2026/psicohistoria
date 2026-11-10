#!/usr/bin/env python3
"""GEO-2027: archive-release-separated two-year state-based violence validation.

Origins and outcomes use DIFFERENT SHA-pinned UCDP OrganizedViolenceCY releases:
23.1 (through 2022) -> 25.1 outcome 2024, and
24.1 (through 2023) -> 26.1 outcome 2025.

This is an ex-post cross-release experiment, NOT a prediction issued in 2023/24.
Archived version numbers suggest contemporaneous editions, but original dates
are not proven by independent timestamp notarization. Never modify 2027 issue.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

from probe_ucdp_organized_vintages import request
from build_official_countries import read_zip,parse_public_source
from backtest_statebased_2027_spec import (
    _annual_frame,_score,_metrics,_pairwise_uncertainty,_reliability,SHRINK,
    LAPLACE,RECENT_WINDOW,MIN_FOLD
)

SOURCES={
    "23.1":{
        "url":"https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy_v23_1.xlsx",
        "sha256":"6c7dc09cc3173b21568a88d70862bee6a9199b2c6b217719698d9298ca8ecaff",
        "last_year":2022,"format":"XLSX"
    },
    "24.1":{
        "url":"https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-241-csv.zip",
        "sha256":"00410bdb65023d1bc8799f47f188677965046bb73447ee33094782db30076260",
        "last_year":2023,"format":"CSV_ZIP"
    },
    "25.1":{
        "url":"https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-251-csv.zip",
        "sha256":"564ce9a33652a5d7adef30f00ce6ac86411dedbcc10ef60ca9bdfbfeb9fea917",
        "last_year":2024,"format":"CSV_ZIP"
    },
    "26.1":{
        "url":"https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-261-csv.zip",
        "sha256":"66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34",
        "last_year":2025,"format":"CSV_ZIP"
    },
}
FOLDS=[
    {"origin_release":"23.1","target_release":"25.1","origin_year":2022,"target_year":2024},
    {"origin_release":"24.1","target_release":"26.1","origin_year":2023,"target_year":2025}
]
XLSX_NS="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

def digest(b):
    return hashlib.sha256(b).hexdigest()

def read_xlsx_rows(raw):
    """Stream official 23.1 XLSX with stdlib; no untrusted formulas or macros."""
    with ZipFile(io.BytesIO(raw)) as archive:
        files=set(archive.namelist())
        if "xl/worksheets/sheet1.xml" not in files:
            raise ValueError("No official XLSX first worksheet")
        strings=[]
        if "xl/sharedStrings.xml" in files:
            with archive.open("xl/sharedStrings.xml") as source:
                for _,node in ET.iterparse(source,events=("end",)):
                    if node.tag==XLSX_NS+"si":
                        strings.append("".join(node.itertext()))
                        node.clear()
        def cell_value(node):
            raw_value=node.find(XLSX_NS+"v")
            if raw_value is not None and raw_value.text is not None:
                return strings[int(raw_value.text)] if node.get("t")=="s" else raw_value.text
            if node.get("t")=="inlineStr":
                return "".join(node.itertext())
            return ""
        with archive.open("xl/worksheets/sheet1.xml") as source:
            header=None
            for _,node in ET.iterparse(source,events=("end",)):
                if node.tag!=XLSX_NS+"row":
                    continue
                columns={}
                for cell in node.findall(XLSX_NS+"c"):
                    address=cell.attrib.get("r","")
                    found=re.match(r"([A-Z]+)",address)
                    if not found:continue
                    index=0
                    for letter in found.group(1):
                        index=index*26+ord(letter)-ord("A")+1
                    columns[index-1]=cell_value(cell)
                if header is None:
                    header=[columns.get(i,"") for i in range(max(columns,default=-1)+1)]
                    if not {"country_id_cy","year_cy","sb_total_deaths_best_cy"}.issubset(header):
                        raise ValueError("Historical 23.1 workbook lacks comparable year/country/deaths fields")
                    keycols=[header.index(k) for k in (
                        "country_id_cy","year_cy","sb_total_deaths_best_cy")]
                elif any(columns.values()):
                    yield tuple(columns.get(i,"") for i in keycols)
                node.clear()

def official_rows(data,version):
    """Returns immutable country-year event labels and source metadata, no country names."""
    spec=SOURCES[version]
    if digest(data)!=spec["sha256"]:
        raise ValueError("Archived UCDP source hash is not pinned: "+version)
    if version=="23.1":
        iterator=read_xlsx_rows(data)
    elif version=="26.1":
        records,names=parse_public_source(read_zip(data))
        if max(max(hist) for hist in records.values())!=spec["last_year"]:
            raise ValueError("Unexpected UCDP 26.1 source max year")
        return records,{"years":spec["last_year"],
                        "rows":sum(len(hist) for hist in records.values()),
                        "country_year_unique":True}
    else:
        with ZipFile(io.BytesIO(data)) as zipped:
            files=[m for m in zipped.namelist() if m.lower().endswith(".csv")]
            if len(files)!=1:
                raise ValueError("Archived CSV ZIP must contain exactly one CSV")
            raw_csv=zipped.read(files[0]).decode("utf-8-sig")
        reader=csv.DictReader(io.StringIO(raw_csv))
        required={"country_id_cy","year_cy","sb_total_deaths_best_cy"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Archived country-level schema incompatible")
        iterator=((row["country_id_cy"],row["year_cy"],row["sb_total_deaths_best_cy"])
                  for row in reader)
    records=defaultdict(dict)
    count=0
    for country,year,deaths in iterator:
        if country=="" or year=="" or deaths=="":
            raise ValueError("Missing archived official country/year/deaths")
        try:
            country_id=int(float(country))
            year=int(float(year))
            fatalities=int(float(deaths))
        except (TypeError,ValueError) as error:
            raise ValueError("Invalid official numeric state-based deaths") from error
        if not (1<=country_id<=2000 and 1989<=year<=spec["last_year"] and
                0<=fatalities<=10_000_000):
            raise ValueError("Archived country-year fields outside declared edition coverage")
        if year in records[country_id]:
            raise ValueError("Duplicated archived country-year cannot be aggregated")
        records[country_id][year]=int(fatalities>=25)
        count+=1
    if count<6000 or max((max(h) for h in records.values()),default=0)!=spec["last_year"]:
        raise ValueError("Unexpected archived UCDP country-year coverage")
    return records,{"years":spec["last_year"],"rows":count,
                    "country_year_unique":True}

def fetch_archives(fetch=request):
    files={}
    metadata={}
    for version,source in SOURCES.items():
        data=fetch(source["url"])
        records,info=official_rows(data,version)
        files[version]=records
        metadata[version]={"url":source["url"],"sha256":source["sha256"],
                           "format":source["format"],"last_year":source["last_year"],
                           **info}
    return files,metadata

def run_folds(files,metadata):
    all_predictions=[]
    fold_reports=[]
    revision_reports=[]
    for fold in FOLDS:
        origin_version=fold["origin_release"]
        target_version=fold["target_release"]
        origin_year=fold["origin_year"]
        target=fold["target_year"]
        origin=files[origin_version]
        outcomes=files[target_version]
        if max(max(h) for h in origin.values())!=origin_year:
            raise ValueError("Origin source contains observation after cutoff")
        if max(max(h) for h in outcomes.values())!=target:
            raise ValueError("Outcome source not actually later than origin")
        combined={cid:dict(h) for cid,h in origin.items()}
        for cid,h in combined.items():
            label=outcomes.get(cid,{}).get(target)
            if label is not None:
                h[target]=label
        # _annual_frame truncates all training transitions at cutoff; only
        # outcome labels for the fixed later year are appended from target release.
        rows,details=_annual_frame(combined,origin_year)
        if details["target_year"]!=target or details["origin_cutoff"]!=origin_year:
            raise ValueError("Unexpected evaluation horizon")
        all_predictions.extend(rows)
        fold_reports.append({
          "origin_version":origin_version,"outcome_version":target_version,
          "origin_max_year":origin_year,"evaluated_year":target,
          **details,"scores":_metrics(rows)
        })
        shared={
            (cid,year) for cid,h in origin.items() for year in h
            if year<=origin_year and year in outcomes.get(cid,{})
        }
        changed=sum(origin[cid][year]!=outcomes[cid][year] for cid,year in shared)
        revision_reports.append({
            "origin_version":origin_version,"outcome_version":target_version,
            "common_historical_country_years":len(shared),
            "revised_binary_labels":changed,
            "revision_fraction":changed/len(shared) if shared else None,
            "scope":"historical data through origin cutoff; measures cross-edition label drift"
        })
    metrics=_metrics(all_predictions)
    skill_full=1-metrics["p_model"]["brier"]/metrics["p_baseline_global_5y"]["brier"]
    skill_markov=1-metrics["p_model"]["brier"]/metrics["p_global_markov"]["brier"]
    return {
        "schema":"idealab.psico.statebased_archival_cross_release_v1",
        "study_type":"EX_POST_ARCHIVED_VINTAGE_SEPARATED_OUTCOMES_NOT_HISTORICALLY_ISSUED",
        "question":"GEO-2027 same frozen 2-year horizon model",
        "target_rule":"UCDP OrganizedViolenceCY sb_total_deaths_best >=25",
        "horizon_years":2,"model_parameters":{"shrinkage":SHRINK,
             "laplace":LAPLACE,"global_baseline_years":RECENT_WINDOW},
        "sources":metadata,
        "folds":fold_reports,
        "historical_revision_diagnostics":revision_reports,
        "country_years":len(all_predictions),
        "positives":sum(row["outcome"] for row in all_predictions),
        "metrics":metrics,
        "brier_skill_vs_global_5y":skill_full,
        "brier_skill_vs_global_markov":skill_markov,
        "country_bootstrap_interval_model_minus_global_5y":_pairwise_uncertainty(all_predictions,"p_baseline_global_5y"),
        "country_bootstrap_interval_model_minus_global_markov":_pairwise_uncertainty(all_predictions,"p_global_markov"),
        "model_reliability":_reliability(all_predictions,"p_model"),
        "original_release_timestamps_independently_notarized":False,
        "historical_forecasts_actually_issued":False,
        "2027_issued_model_or_probabilities_modified":False,
        "prospective_2027_outcomes_resolved":0,
        "prospective_skill_demonstrated":False,
        "limitations":"Origin and outcome editions are distinct official archived UCDP releases, reducing contamination by future label revisions. This is still an ex-post reconstruction in 2026: release provenance is not independently time-notarized and predictions were not issued at the historical origin dates. Only two later years are available; overlapping countries and macro shocks limit inference."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--check-report")
    args=p.parse_args()
    files,info=fetch_archives()
    result=run_folds(files,info)
    content=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if args.check_report and Path(args.check_report).read_bytes()!=content.encode():
        raise ValueError("Source-backed true-vintage report differs from committed aggregate")
    print("GEO2027_TRUE_VINTAGE_BACKTEST_BEGIN")
    print(content,end="")
    print("GEO2027_TRUE_VINTAGE_BACKTEST_END")
    print("GEO2027_TRUE_VINTAGE_COMPLETE",result["country_years"],result["positives"],
          "2027_outcomes",result["prospective_2027_outcomes_resolved"])

if __name__=="__main__":main()
