#!/usr/bin/env python3
"""Audit separate historical UCDP/PRIO ACD conflict-incidence vintages.

Never splice ACD intrastate conflict incidence into GEO2027's separate
OrganizedViolenceCY 25-death country-year labels. Historical ACD rows are
CONFLICT-YEAR, not COUNTRY-YEAR and there is no listed non-conflict universe.
Versions 20.1/21.1/22.1 are strictly historical, not prospective issues.

All public official ZIP bytes are SHA-pinned after first source audit. Earlier
source versions do not make the older predictions independently timestamped.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter,defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from inspect_ucdp_archives import fetch
from probe_ucdp_prio_incidence import (
    MAX_ZIP,source_zip,parse_country_code,ALLOWED_TYPES,
    PINNED_SHA as CURRENT_PINS,SOURCES as CURRENT_SOURCES,
)

HISTORICAL={
    "20.1":{"last_year":2019,"url":"https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-201-csv.zip","sha256":"f4f924c1c7ce4ca5c8451512afced6182350b2ea849dd271617febc224218c93"},
    "21.1":{"last_year":2020,"url":"https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-211-csv.zip","sha256":"4bebac361a42a9db813da58bf6244f7ec04b780dc24a8c236993672e32460dc4"},
    "22.1":{"last_year":2021,"url":"https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-221-csv.zip","sha256":"82e8326c2de196f1acf3538e6bd8efd818fdde175c399b43282b4d9ee15b954d"},
    "23.1":{"last_year":2022,"url":CURRENT_SOURCES["23.1"],"sha256":CURRENT_PINS["23.1"]},
    "25.1":{"last_year":2024,"url":CURRENT_SOURCES["25.1"],"sha256":CURRENT_PINS["25.1"]},
}
PAIRS=(("20.1","21.1"),("21.1","22.1"),("22.1","23.1"),("23.1","25.1"))
MIN_ACTIVE=1200
MIN_COUNTRIES=90


def official_download_url(url):
    parsed=urlsplit(url)
    if (parsed.scheme!="https" or parsed.netloc!="ucdp.uu.se"
        or not parsed.path.startswith("/downloads/ucdpprio/")
        or not parsed.path.endswith("-csv.zip") or parsed.query or parsed.fragment):
        raise ValueError("Non-institutional or unfixed historical official ZIP URL")
    return url


def parse_version(raw,version,*,allow_probe=False):
    if version not in HISTORICAL:
        raise ValueError("Unapproved historic conflict-incidence edition")
    spec=HISTORICAL[version]
    digest=hashlib.sha256(raw).hexdigest()
    if spec["sha256"] is None:
        if not allow_probe:
            raise ValueError("Unpinned historical source cannot be certified or published")
    elif digest!=spec["sha256"]:
        raise ValueError("Official UCDP/PRIO ACD source SHA-256 differs from frozen edition")
    records,fields=source_zip(raw)
    count_by_type=Counter()
    active=set()
    unique_conflicts=set()
    first_active_year=None
    late_count=0
    for row in records:
        conflict_type=row["type_of_conflict"].strip()
        count_by_type[conflict_type]+=1
        year_string=row["year"].strip()
        if not year_string.isdigit():
            raise ValueError("Invalid original historical ACD conflict year")
        year=int(year_string)
        if not 1946<=year<=spec["last_year"]:
            raise ValueError("ACD edition contains forbidden future or pre-1946 observations")
        if conflict_type not in ALLOWED_TYPES:
            continue
        cid=parse_country_code(row["gwno_a"])
        loc=parse_country_code(row["gwno_loc"])
        if cid is None or loc!=cid:
            raise ValueError("Cannot resolve intrastate government location to one country")
        if not 1<=int(cid)<=2000:
            raise ValueError("Historical ACD country code out of range")
        conflict_id=row["conflict_id"].strip()
        if not conflict_id.isdigit():
            raise ValueError("Non-numeric original conflict identifier")
        unique=(cid,year,conflict_id)
        if unique in unique_conflicts:
            raise ValueError("Repeated conflict-year in one annual edition")
        unique_conflicts.add(unique)
        active.add((cid,year))
        if first_active_year is None or year<first_active_year:
            first_active_year=year
        if year==spec["last_year"]:
            late_count+=1
    if (len(active)<MIN_ACTIVE or len({cid for cid,_ in active})<MIN_COUNTRIES
        or not any(year==spec["last_year"] for cid,year in active)
        or len(records)<2000):
        raise ValueError("Official historical conflict-incidence coverage unexpectedly sparse")
    meta={
        "official_url":official_download_url(spec["url"]),
        "original_zip_sha256":digest,
        "sha256_pinned_before_run":spec["sha256"] is not None,
        "n_bytes":len(raw),
        "raw_conflict_year_records":len(records),
        "parsed_column_names":fields,
        "conflict_year_records_by_type":dict(sorted(count_by_type.items())),
        "unique_intrastate_conflict_year_records":len(unique_conflicts),
        "unique_active_intrastate_country_years":len(active),
        "distinct_countries_with_recorded_intrastate_conflict":len({cid for cid,_ in active}),
        "country_years_with_recorded_intrastate_conflict_in_last_year":
            sum(year==spec["last_year"] for _,year in active),
        "last_year":spec["last_year"],
        "first_observed_intrastate_year":first_active_year,
        "repeated_government_multicode_entries_accepted":False,
        "all_implicit_country_year_non_events_recovered":False,
    }
    return active,meta


def compare(old,new,earlier_cutoff):
    if (not isinstance(earlier_cutoff,int)
        or earlier_cutoff<1946 or earlier_cutoff>2023):
        raise ValueError("Unsafe early source cutoff")
    shared_old={key for key in old if key[1]<=earlier_cutoff}
    shared_new={key for key in new if key[1]<=earlier_cutoff}
    added=shared_new-shared_old
    removed=shared_old-shared_new
    overlap=shared_new & shared_old
    return {
        "overlap_year_cutoff":earlier_cutoff,
        "earlier_intrastate_active_country_years":len(shared_old),
        "later_intrastate_active_country_years_for_same_period":len(shared_new),
        "both_edition_active_country_years":len(overlap),
        "newly_coded_active_country_years":len(added),
        "no_longer_coded_active_country_years":len(removed),
        "net_change_in_active_incidence_count":len(added)-len(removed),
        "sum_absolute_label_changes_in_recorded_active_set":len(added)+len(removed),
        "possible_missing_country_universe_not_interpreted_as_non_conflict":True,
        "implies_statebased_25death_label_revision":False,
    }


def diagnose(fetcher=fetch,*,allow_probe=False):
    if set(HISTORICAL)!={"20.1","21.1","22.1","23.1","25.1"}:
        raise ValueError("Unapproved historical source registry")
    sources={};meta={}
    for version,spec in HISTORICAL.items():
        if not official_download_url(spec["url"]):
            raise ValueError("Unsupported historical source")
        raw=fetcher(spec["url"],MAX_ZIP)
        sources[version],meta[version]=parse_version(
            raw,version,allow_probe=allow_probe)
    pairs=[]
    for first,last in PAIRS:
        pairs.append({
            "earlier_edition":first,
            "later_edition":last,
            "same_historical_years_comparison":compare(
                sources[first],sources[last],HISTORICAL[first]["last_year"]
            ),
        })
    provisional=any(not m["sha256_pinned_before_run"] for m in meta.values())
    if provisional and not allow_probe:
        raise ValueError("Cannot certify historical source archives before SHA pinning")
    return {
        "schema":"idealab.psico.ucdp_prio_2020_2022_source_vintage_extension.v1",
        "status":"SOURCE_DISCOVERY_PROVISIONAL_NOT_FOR_MODEL_EVALUATION"
            if provisional else "SHA_PINNED_SOURCE_METADATA_REPRODUCIBLE",
        "subject":"Intrastate UCDP/PRIO Armed Conflict Dataset (ACD) presence by conflict-year, collapsed to country-year for presence ONLY",
        "explicitly_not_original_geo2027_statebased_25_deaths":True,
        "different_target_family_requires_separate_model_and_evaluation":True,
        "target_2027_observations":0,
        "original_geo2027_or_newconf2027_or_shadow_modified":False,
        "source_metadata":meta,
        "revision_of_historical_intrastate_country_year_incidence":pairs,
        "archived_source_release_dates_independently_notarized":False,
        "historical_forecasts_independently_issued_at_origin":False,
        "country_wide_inactive_labels_derivable_from_ACD_alone":False,
        "structural_geopolitical_dependence_identified":False,
        "source_metadata_provisional":provisional,
        "note":(
            "Old ACD conflict-year editions are different from the UCDP "
            "OrganizedViolenceCY country-year statebased 25-death indicator. "
            "Their historical presence rows do not give a full 196-country "
            "non-conflict denominator; no probability or calibration of GEO2027 "
            "can be inferred from this probe. Changes in past editions are "
            "editorial incidence revisions, not true transitions. Even after "
            "SHA pinning, edition names do not independently notarize first "
            "release dates. This is a source inventory and drift audit, "
            "not independent forecast validation."
        ),
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--probe",action="store_true",
                   help="Allow unpinned sources for first hash discovery only; never certify")
    p.add_argument("--check-report")
    args=p.parse_args()
    if args.check_report and args.probe:
        raise ValueError("Cannot publish an unpinned discovery as certified report")
    report=diagnose(allow_probe=args.probe)
    content=json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    print("UCDP_PRIO_OLD_VINTAGES_BEGIN")
    print(content,end="")
    print("UCDP_PRIO_OLD_VINTAGES_END")
    if args.check_report and Path(args.check_report).read_bytes()!=content.encode():
        raise ValueError("Pinned UCDP PRIO old-vintage report changed")


if __name__=="__main__":
    main()
