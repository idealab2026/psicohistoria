#!/usr/bin/env python3
"""Audit zero-coded UCDP state-based deaths and 196-GWNO source coverage.

The UCDP OrganizedViolenceCY 26.1 official codebook explicitly states that
a 0 fatalities value may occur when there was fatal organized violence but
its dyad never qualified for the 25/year inclusion threshold. Thus:
  coded sb_total_deaths_best == 0 != proof of real absence of violence.
Likewise sb_exist flags GED recorded events, not UCDP conflict activeness.

No forecast, alert, country ranking, or 2027 outcome is emitted by this audit.
Four official ZIP/XLSX sources are SHA-verified by existing parse_counts,
and EVERY field used for the additional sb_exist semantic audit is joined
exactly to those checked original source counts.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import io
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    FROZEN_SHA256, audit as audit_issued,
)
from audit_geo2027_log1p_shadow_issue import FROZEN_ISSUE_SHA256
from audit_geo2027_log1p_issued_death_stress import ALERT_SHA
from backtest_archived_country_vintages import SOURCES, XLSX_NS
from build_official_countries import read_zip
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD, VERSION_ORDER, EXPECTED_ROWS, parse_counts,
)
from prepare_geo2027_transition_alerts import SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo2027-ucdp-zero-coding-riskset-audit.json"
CODEBOOK="https://ucdp.uu.se/downloads/organizedviolencecy/UCDP_OrganizedViolenceCY_Codebook_261.pdf"
KEYS={
    "23.1":("country_id_cy","year_cy","sb_total_deaths_best_cy","sb_exist_cy"),
    "24.1":("country_id_cy","year_cy","sb_total_deaths_best_cy","sb_exist_cy"),
    "25.1":("country_id_cy","year_cy","sb_total_deaths_best_cy","sb_exist_cy"),
    "26.1":("country_id","year","sb_total_deaths_best","sb_exist"),
}
RECENT_YEARS=(2022,2023,2024,2025)
HISTORY_BEGIN=1989
HISTORY_END=2025
FIXED_COUNTRY_N=196


def strict_int(v,field):
    if type(v) is int:
        n=v
    elif type(v) is str and re.fullmatch(r"(?:0|[1-9][0-9]*)",v.strip()):
        n=int(v.strip())
    else:
        raise ValueError("Official "+field+" is not a strict nonnegative integer")
    return n


def bool_flag(v):
    if type(v) is int and v in (0,1):
        return v
    if type(v) is str:
        z=v.strip().lower()
        if z in ("0","false"):
            return 0
        if z in ("1","true"):
            return 1
    raise ValueError("UCDP sb_exist must be explicitly 0 or 1")


def _xlsx_named_rows(raw,fields):
    """Stream first worksheet with stdlib; no installed spreadsheet package."""
    with ZipFile(io.BytesIO(raw)) as z:
        if "xl/worksheets/sheet1.xml" not in z.namelist():
            raise ValueError("Original 23.1 XLSX first sheet missing")
        strings=[]
        if "xl/sharedStrings.xml" in z.namelist():
            with z.open("xl/sharedStrings.xml") as f:
                for _,node in ET.iterparse(f,events=("end",)):
                    if node.tag==XLSX_NS+"si":
                        strings.append("".join(node.itertext()))
                        node.clear()
        def value(cell):
            el=cell.find(XLSX_NS+"v")
            if el is not None and el.text is not None:
                if cell.get("t")=="s":
                    i=int(el.text)
                    if i<0 or i>=len(strings):
                        raise ValueError("Malformed UCDP XLSX string table")
                    return strings[i]
                return el.text
            if cell.get("t")=="inlineStr":
                return "".join(cell.itertext())
            return ""
        with z.open("xl/worksheets/sheet1.xml") as f:
            indexes=None
            for _,node in ET.iterparse(f,events=("end",)):
                if node.tag!=XLSX_NS+"row":
                    continue
                cols={}
                for cell in node.findall(XLSX_NS+"c"):
                    m=re.match(r"([A-Z]+)",cell.attrib.get("r",""))
                    if not m:
                        raise ValueError("No XLSX cell coordinate")
                    col=0
                    for letter in m.group(1):
                        col=col*26+(ord(letter)-ord("A")+1)
                    cols[col-1]=value(cell)
                if indexes is None:
                    header=[cols.get(i,"") for i in range(max(cols,default=-1)+1)]
                    if not set(fields).issubset(header):
                        raise ValueError("UCDP 23.1 country-year sb_exist schema changed")
                    indexes=[header.index(x) for x in fields]
                elif any(str(v).strip() for v in cols.values()):
                    yield tuple(cols.get(i,"") for i in indexes)
                node.clear()


def _csv_named_rows(raw,version,fields):
    if version=="26.1":
        content=read_zip(raw)
    else:
        with ZipFile(io.BytesIO(raw)) as z:
            members=[x for x in z.infolist()
                     if not x.is_dir() and x.filename.lower().endswith(".csv")]
            if (len(members)!=1 or members[0].file_size>12_000_000 or
                members[0].file_size<100_000):
                raise ValueError("Expected one bounded official CSV file")
            content=z.read(members[0]).decode("utf-8-sig")
    reader=csv.DictReader(io.StringIO(content))
    if not set(fields).issubset(set(reader.fieldnames or [])):
        raise ValueError("Official UCDP sb_exist/country/year schema missing")
    for row in reader:
        if row.get(None):
            raise ValueError("Malformed UCDP CSV row")
        yield tuple(row.get(field) for field in fields)


def annotated_rows(raw,version,verified_counts):
    """Return strictly joined existence annotations for verified source rows."""
    if version not in VERSION_ORDER:
        raise ValueError("Unknown official source version")
    fields=KEYS[version]
    iterator=(_xlsx_named_rows(raw,fields) if version=="23.1"
              else _csv_named_rows(raw,version,fields))
    out={}
    n=0
    for country,year,deaths,exist in iterator:
        cid=strict_int(country,"GWNO")
        y=strict_int(year,"year")
        d=strict_int(deaths,"state-based best deaths")
        ex=bool_flag(exist)
        if (cid not in verified_counts or
            y not in verified_counts[cid] or
            d!=verified_counts[cid][y]):
            raise AssertionError("Existence annotation cannot be reconciled with SHA-verified source counts")
        key=(cid,y)
        if key in out:
            raise ValueError("Duplicate original UCDP country-year")
        out[key]={"deaths":d,"sb_exist":ex}
        n+=1
    if (n!=EXPECTED_ROWS[version] or
        n!=sum(len(h) for h in verified_counts.values())):
        raise ValueError("Incomplete UCDP sb_exist annotation extraction")
    return out


def yearly_coverage(annotated,ids,year):
    rows={cid:annotated[(cid,year)] for cid in ids
          if (cid,year) in annotated}
    present=set(rows)
    zeros={cid for cid,r in rows.items() if r["deaths"]==0}
    positive={cid for cid,r in rows.items() if r["deaths"]>0}
    sub={cid for cid,r in rows.items() if 1<=r["deaths"]<=24}
    active={cid for cid,r in rows.items() if r["deaths"]>=25}
    exist={cid for cid,r in rows.items() if r["sb_exist"]==1}
    result={
        "year":year,
        "first_issued_country_universe_n":len(ids),
        "explicit_rows_n":len(rows),
        "first_issued_GWNO_missing_ids":sorted(set(ids)-present),
        "literal_zero_best_fatalities_n":len(zeros),
        "positive_best_fatalities_n":len(positive),
        "best_deaths_1_to_24_n":len(sub),
        "best_deaths_25_plus_n":len(active),
        "state_based_existence_flag_1_n":len(exist),
        "zero_best_but_existence_flag_1_n":len(zeros&exist),
        "zero_best_and_existence_flag_0_n":len(zeros-exist),
        "best_positive_but_existence_flag_0_n":len(positive-exist),
        "zero_best_does_not_prove_no_fatal_organized_violence":True,
        "state_based_existence_flag_does_not_prove_UCDP_threshold_activeness":True,
        "explicit_country_year_missing_is_not_implicit_zero":True,
    }
    if (sum(result[k] for k in (
        "literal_zero_best_fatalities_n","best_deaths_1_to_24_n",
        "best_deaths_25_plus_n"))!=len(rows)):
        raise AssertionError("Disjoint coded fatality bins incomplete")
    return result


def study(sources,issued):
    if not sources or set(sources)!=set(VERSION_ORDER):
        raise ValueError("Require all four original official UCDP archives")
    ids=sorted(row["country_id"] for row in issued["countries"])
    if (len(ids)!=196 or len(set(ids))!=196 or
        issued.get("official_2027_outcomes_resolved")!=0):
        raise ValueError("First-issued prospectively frozen risk universe changed")
    per_version={}
    annotated_by_version={}
    for version in VERSION_ORDER:
        raw=sources[version]
        verified=parse_counts(raw,version) # SHA, row count, cutoff + 196 year riskset
        ann=annotated_rows(raw,version,verified)
        cutoff=SOURCES[version]["last_year"]
        years=[year for year in RECENT_YEARS if year<=cutoff]
        snapshots=[yearly_coverage(ann,ids,year) for year in years]
        if (snapshots[-1]["explicit_rows_n"]!=196 or
            snapshots[-1]["first_issued_GWNO_missing_ids"]):
            raise ValueError("Latest edition does not cover all first-issued countries")
        older=[{
            "year":year,
            "all_GWNO_source_rows":sum(
                (cid,year) in ann for cid in {country for country,_ in ann}),
            "fixed_196_GWNO_rows":sum(
                (cid,year) in ann for cid in ids),
        } for year in range(1989,cutoff+1)]
        per_version[version]={
            "source_archive_sha256":SOURCES[version]["sha256"],
            "source_last_year":cutoff,
            "total_verified_country_year_rows":len(ann),
            "total_annotated_flags":len(ann),
            "first_issued_cohort_2022_through_edition_cutoff":snapshots,
            "historical_country_coverage_by_year":older,
            "earliest_year_complete_fixed_196_cohort":next(
                (x["year"] for x in older
                 if x["fixed_196_GWNO_rows"]==196),None),
            "source_years_with_incomplete_original_196":sum(
                x["fixed_196_GWNO_rows"]<196 for x in older),
        }
        annotated_by_version[version]=ann
    if (per_version["26.1"]["first_issued_cohort_2022_through_edition_cutoff"][-1]
        ["explicit_rows_n"]!=196):
        raise AssertionError("Original 2025 first-issued cohort incomplete")
    for version in VERSION_ORDER:
        if (per_version[version]["total_verified_country_year_rows"]!=
            EXPECTED_ROWS[version]):
            raise AssertionError("UCDP source row count changed")
    comparisons=[]
    for version in ("23.1","24.1","25.1"):
        older=annotated_by_version[version]
        newest=annotated_by_version["26.1"]
        cutoff=SOURCES[version]["last_year"]
        for year in (2022,2023,2024):
            if year>cutoff:
                continue
            fixed={cid for cid in ids
                   if (cid,year) in older and (cid,year) in newest}
            if len(fixed)!=196:
                raise ValueError("Historical source edition cannot reconcile fixed cohort")
            n_zeros_recode=sum(
                (older[(cid,year)]["deaths"]==0)!=(newest[(cid,year)]["deaths"]==0)
                for cid in fixed)
            n_sb_existence_recode=sum(
                older[(cid,year)]["sb_exist"]!=newest[(cid,year)]["sb_exist"]
                for cid in fixed)
            comparisons.append({
                "origin_year":year,
                "older_edition":version,
                "later_edition":"26.1",
                "country_n":196,
                "countries_changed_zero_fatality_indicator":n_zeros_recode,
                "countries_changed_sb_exist_indicator":n_sb_existence_recode,
                "not_independent_edition_comparisons":True,
            })
    yearly26=per_version["26.1"]["first_issued_cohort_2022_through_edition_cutoff"]
    zero2025=next(x for x in yearly26 if x["year"]==2025)
    return {
        "schema":"idealab.psico.geo2027_ucdp_zero_coding_country_coverage_v1",
        "status":"OFFICIAL_SOURCE_SEMANTICS_AND_FIRST_ISSUED_COUNTRY_COVERAGE_NOT_2027_OUTCOME",
        "codebook_official_version":"26.1",
        "codebook_official_url":CODEBOOK,
        "official_codebook_zero_semantics":"A literal zero is an official coded zero of included event fatalities, not proof of absence of all fatal violence, because UCDP GED inclusion depends on a dyad/actor qualifying 25 deaths within a year.",
        "official_codebook_existence_semantics":"sb_exist is a recorded state-based event flag, not a UCDP active-state indicator, and is a different measurement from best deaths >= 25.",
        "country_zero_coding_is_not_missing_row_imputation":True,
        "UCDP_source_versions":list(VERSION_ORDER),
        "original_issued_GEO2027_sha256":SOURCE_SHA256,
        "original_issued_LOG1P_sha256":FROZEN_ISSUE_SHA256,
        "new_global_only_issued_sha256":FROZEN_SHA256,
        "original_15_alerts_sha256":ALERT_SHA,
        "original_196_GWNO_cohort_immutable":True,
        "official_2027_labels_observed":0,
        "2027_source_release_not_yet_available":True,
        "no_2027_forecasts_or_alerts_reissued":True,
        "not_a_history_release_available_asof_original_year":True,
        "archived_edition_comparisons_correlated":True,
        "year_2025_coded_zero_country_n":zero2025["literal_zero_best_fatalities_n"],
        "year_2025_coded_zero_with_sb_exist_1_n":
            zero2025["zero_best_but_existence_flag_1_n"],
        "year_2025_explicit_country_year_rows_n":zero2025["explicit_rows_n"],
        "recent_year_coverage_and_flag_by_edition":per_version,
        "historical_cross_edition_semantic_indicator_revisions":comparisons,
        "limitations":"An actual coded zero can coincide with omitted below-eligibility violence and/or zero documented included state-based deaths. sb_exist is an event existence variable, not a threshold event. Exact probability outcome remains UCDP OrganizedViolenceCY state-based best >=25 as coded, not a claim of no real-world violence. Annual 196-country cohort can only be resolved when actual future edition supplies 196 explicit target rows, and the first-complete edition must be independently authenticated. Cross-edition comparisons share GWNO country-years and are not independent."
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    args=ap.parse_args()
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),
                 ORIGINAL.read_bytes(),OLD_SHADOW.read_bytes(),
                 OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    sources={v:request(SOURCES[v]["url"],MAX_DOWNLOAD)
             for v in VERSION_ORDER}
    issued=json.loads(ISSUE.read_text(encoding="utf8"))
    obj=study(sources,issued)
    content=json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False)+"\n"
    print("GEO2027_UCDP_ZERO_CODING_BEGIN")
    print(content,end="")
    print("GEO2027_UCDP_ZERO_CODING_END",flush=True)
    if args.check_report and REPORT.read_bytes()!=content.encode():
        raise ValueError("Published UCDP zero-semantics and country-year coverage report is not source identical")


if __name__=="__main__":
    main()
