#!/usr/bin/env python3
"""Official UCDP/PRIO conflict-year vintage provenance and join feasibility.

This is a pre-model audit: it must NOT imply that the releases were
independently timestamped, or that conflict-year rows are country-year rows.
Only aggregate metadata is logged; no country names, IDs or country scores.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
from pathlib import Path
import argparse
import re
from collections import Counter,defaultdict
from zipfile import ZipFile

from inspect_ucdp_archives import fetch
from experiment_onset2_lagged_signals import load_panel

SOURCES={
 "23.1":"https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-231-csv.zip",
 "25.1":"https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-251-csv.zip",
}
MAX_ZIP=8_000_000
PINNED_SHA={
 "23.1":"8fe95d8a5780cba1d312f9673ffd9e93b90c91bb26e348393a583853a892b718",
 "25.1":"b49f7e80510d8a5779a52d872aef5b26456b3f5cbdd3ec32031339488e81813f"
}
ALLOWED_TYPES={"3","4"}
NEEDED={"year","type_of_conflict","gwno_a","gwno_loc","conflict_id"}

def source_zip(data):
    if not data.startswith(b"PK"):
        raise ValueError("Source is not a ZIP archive")
    with ZipFile(io.BytesIO(data)) as archive:
        files=[f for f in archive.infolist() if not f.is_dir() and f.filename.lower().endswith(".csv")]
        if len(files)!=1:
            raise ValueError("Expected exactly one UCDP conflict-year CSV inside ZIP")
        f=files[0]
        if f.file_size>30_000_000 or f.compress_size>MAX_ZIP:
            raise ValueError("Archive exceeds approved original data limits")
        raw=archive.read(f).decode("utf-8-sig")
    reader=csv.DictReader(io.StringIO(raw))
    fieldnames=reader.fieldnames or []
    if not NEEDED.issubset(fieldnames):
        raise ValueError("UCDP/PRIO original conflict-year schema is incompatible: "+repr(fieldnames[:25]))
    return list(reader),fieldnames

def parse_country_code(value):
    """Only singleton official GW identifiers are mapped; never guess multi-code actors."""
    s=(value or "").strip()
    return s if s.isdigit() else None

def audit(fetcher=fetch,panel_loader=load_panel,require_pinned=True):
    report={
      "schema":"idealab.psico.acd_vintage_provenance_probe.v1",
      "source_family":"UCDP/PRIO Armed Conflict Dataset (conflict-year)",
      "intrastate_type_codes":[3,4],
      "country_link":"gwno_a singleton, government primary party, same GW identifier as country-onset",
      "vintage_downloaded_today_not_notarized":True,
      "historical_release_dates_independently_authenticated":False,
      "country_year_labels_or_predictions_published":False,
      "versions":{}
    }
    for version,url in SOURCES.items():
        data=fetcher(url,MAX_ZIP)
        checksum=hashlib.sha256(data).hexdigest()
        if require_pinned and checksum!=PINNED_SHA[version]:
            raise ValueError("Source not pinned to authentic UCDP/PRIO edition: "+version)
        records,fields=source_zip(data)
        code_counts=Counter()
        included={}
        years=defaultdict(set)
        allcodes=set()
        nonmatch=0;missing=0
        for row in records:
            typ=row["type_of_conflict"].strip()
            code_counts[typ]+=1
            if typ not in ALLOWED_TYPES:continue
            cid=parse_country_code(row["gwno_a"])
            if cid is None:
                missing+=1
                continue
            other=parse_country_code(row["gwno_loc"])
            if other is not None and other!=cid:
                nonmatch+=1
            y=int(row["year"])
            if y<1946 or y>2024:
                raise ValueError("Invalid original conflict-year coverage")
            key=(cid,y)
            included.setdefault(key,set()).add(row["conflict_id"])
            years[y].add(cid)
            allcodes.add(cid)
        onset,oinfo=panel_loader(version)
        onset_universe={cid for cid,h in onset.items() if oinfo["max_year"] in h}
        missing_links={cid for cid in allcodes if cid not in onset}
        if not records or max(years,default=0)!=oinfo["max_year"]:
            raise ValueError("UCDP/PRIO version does not cover the requested cutoff year")
        report["versions"][version]={
          "url":url,
          "sha256":checksum,
          "bytes":len(data),
          "raw_conflict_year_rows":len(records),
          "fields":fields,
          "row_counts_by_conflict_type":dict(sorted(code_counts.items())),
          "missing_or_multiple_government_codes":missing,
          "different_singleton_gwno_a_and_gwno_loc":nonmatch,
          "unique_intrastate_country_years":len(included),
          "countries_with_intrastate_conflict":len(allcodes),
          "intrastate_codes_without_any_onset_country_mapping":len(missing_links),
          "latest_year":max(years),
          "latest_year_countries_active":len(years[max(years)]),
          "latest_year_onset_universe":len(onset_universe),
          "active_in_latest_onset_universe":len(years[max(years)] & onset_universe),
          "onset_vintage_sha256":oinfo["sha256"],
          "original_csv_row_unit":"conflict-year; collapsed only for country-year incidence"
        }
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--check-report")
    args=p.parse_args()
    d=audit()
    content=json.dumps(d,sort_keys=True,indent=2)+"\n"
    print("UCDPPRIO_INCIDENCE_AUDIT_BEGIN")
    print(content,end="")
    print("UCDPPRIO_INCIDENCE_AUDIT_END")
    if args.check_report and Path(args.check_report).read_text(encoding="utf-8")!=content:
        raise ValueError("Official source incidence audit differs from published metadata")
