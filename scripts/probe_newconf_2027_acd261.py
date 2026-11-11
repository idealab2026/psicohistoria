#!/usr/bin/env python3
"""Audit UCDP/PRIO 26.1 as only the 2025 origin conflict-activity source.

No newconf outcomes for 2025/2026/2027 are inferred from this data.
The 25.1 Multiple Onset country universe is frozen separately (196).
Provenance tool: the SHA printed here must be pinned before any issuance.
"""
from __future__ import annotations
import hashlib
import json
from collections import Counter
from inspect_ucdp_archives import fetch
from probe_ucdp_prio_incidence import source_zip,parse_country_code,ALLOWED_TYPES
from probe_multiple_onset_vintages import PINNED as MULTIPLE_PINNED
from experiment_multiple_newconf import load_multiple
URL="https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-261-csv.zip"
LIMIT=8_000_000
PINNED_SHA="5f951743222964674a446e32a5a871077b29bd13349588d85fc59953d89c878a"

def audit(fetcher=fetch,multiple_loader=load_multiple):
    raw=fetcher(URL,LIMIT)
    if hashlib.sha256(raw).hexdigest()!=PINNED_SHA:
        raise ValueError("Official UCDP PRIO 26.1 source digest changed")
    rows,cols=source_zip(raw)
    origin,meta=multiple_loader("25.1")
    cohort={cid for cid,h in origin.items() if 2024 in h}
    if len(cohort)!=196:raise ValueError("Not the original 196-country multiple-onset cohort")
    activity=set()
    type_counts=Counter()
    extra=0
    missing=0
    codes_with_2025=set()
    for row in rows:
        year=int(row["year"])
        typ=row["type_of_conflict"].strip()
        type_counts[typ]+=1
        if typ not in ALLOWED_TYPES:continue
        cid=parse_country_code(row["gwno_a"])
        loc=parse_country_code(row["gwno_loc"])
        if cid is None or loc!=cid:
            raise ValueError("Ambiguous government location or non-country code in 26.1 intrastate ACD")
        if year>2025 or year<1946:
            raise ValueError("Invalid chronology in ACD 26.1 original")
        if year==2025:
            codes_with_2025.add(cid)
            if cid not in cohort:extra+=1
            activity.add(cid)
    if len(rows)<2700 or len(activity)<20 or len(activity)>100 or not codes_with_2025:
        raise ValueError("UCDP/PRIO source coverage suspicious")
    if extra:raise ValueError("New 2025 activity country absent from 2024 196-country origin population")
    return {
        "schema":"idealab.psico.newconf_2027_acd261_origin_audit.v1",
        "source_url":URL,
        "source_sha256":hashlib.sha256(raw).hexdigest(),
        "source_bytes":len(raw),
        "source_original_conflict_year_rows":len(rows),
        "source_fields":cols,
        "conflict_type_row_counts":dict(sorted(type_counts.items())),
        "last_activity_year":2025,
        "origin_multiple_onset_version":"25.1",
        "origin_multiple_onset_sha256":MULTIPLE_PINNED["25.1"]["sha256"],
        "origin_cohort":len(cohort),
        "active_intrastate_in_2025":len(activity),
        "inactive_intrastate_in_2025":len(cohort)-len(activity),
        "country_level_forecasts_or_identifiers_emitted":False,
        "2025_newconf_labels_observed":False,
        "2026_2027_labels_observed":False,
        "2027_prospective_forecast_issued":False
    }

def activity_2025(fetcher=fetch):
    raw=fetcher(URL,LIMIT)
    if hashlib.sha256(raw).hexdigest()!=PINNED_SHA:
        raise ValueError("Official UCDP PRIO 26.1 source hash changed")
    rows,fields=source_zip(raw)
    found=set()
    for row in rows:
        if row["type_of_conflict"].strip() not in ALLOWED_TYPES:
            continue
        cid=parse_country_code(row["gwno_a"])
        loc=parse_country_code(row["gwno_loc"])
        if cid is None or cid!=loc:
            raise ValueError("2025 UCDP government GW country ID ambiguous")
        if int(row["year"])==2025:
            found.add(cid)
        if int(row["year"])>2025:
            raise ValueError("Future official activity in 26.1 source")
    if len(found)!=32:
        raise ValueError("2025 origin armed-conflict country count changed")
    return found


if __name__=="__main__":
    d=audit()
    print("NEWCONF_2027_ACD261_SOURCE_PROBE_BEGIN")
    print(json.dumps(d,sort_keys=True,ensure_ascii=False,indent=2))
    print("NEWCONF_2027_ACD261_SOURCE_PROBE_END")
