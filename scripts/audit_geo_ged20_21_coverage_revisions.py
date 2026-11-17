#!/usr/bin/env python3
"""Audit UCDP GED 20.1/21.1 historical source coverage and label revisions.

Extends the SHA-pinned 19.1/22.1/23.1 original GED event-to-country-year
bridge. Uses *same-GED-release* event definitions on 196 frozen GWNOs,
separates GED19 Syria exclusion from eligible-country label revisions.
No statistical forecast, ex ante issue claim or retrospective model tuning.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from audit_geo_legacy_ged_countryyear_bridge import (
    ARCHIVE, GED_URLS, GED_221_CODEBOOK, PINNED_GED_SHA256,
    GED_221_CODEBOOK, discover_ged, parse_ged,
)
from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit as audit_issued,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data/geo-ged-20-21-coverage-revisions.json"
ANCHOR = ROOT / "data/geo-ged-old-vintage-countryyear-feasibility.json"
VINTAGES = ("19.1", "20.1", "21.1", "22.1", "23.1")
NEW_VINTAGES = ("20.1", "21.1")
ALL_URLS = {**GED_URLS, **{
    v: "https://ucdp.uu.se/downloads/ged/ged" + v.replace(".", "") + "-csv.zip"
    for v in NEW_VINTAGES
}}
CODEBOOKS = {
    "20.1": {
        "url":"https://ucdp.uu.se/downloads/ged/ged201.pdf",
        "compiled_year":2020,
        "data_extracted_on":"2020-04-07",
        "last_event_year":2019,
    },
    "21.1": {
        "url":"https://ucdp.uu.se/downloads/ged/ged211.pdf",
        "compiled_year":2021,
        "data_extracted_on":"2021-04-08",
        "last_event_year":2020,
    },
}
MAX_ZIP=95_000_000
MAX_PDF=8_000_000
MIN_YEAR=2011
SYRIA=652
N=196
# SHA-256 computed from officially retrieved ZIP/PDF bytes on 2026-11-17.
PINNED_NEW_SHA256 = {
    "20.1":"5e35b74f52dc67a18aabfab86f69655c847e87320684662a6112dec46d65111f",
    "21.1":"2cd62e39db0f49b784ecd1d48c364191c78afc9d5fb1bd9f6b6dda55dcd59afd",
}
PINNED_CODEBOOK_SHA256 = {
    "20.1":"964becfa74e56e9217c123d059a6e4156037750dbaadd4b4e5a25de2c990e03a",
    "21.1":"4d1c6ab95462e8bee2c6a4e501fef7b5a5cde6c0e0cd1064bb5c8d3d3c7ab80c",
}


def _valid_ids(ids):
    if (len(ids)!=N or len(set(ids))!=N or
        any(type(x) is not int or x<1 or x>2000 for x in ids) or
        SYRIA not in ids):
        raise ValueError("Original frozen GEO 196-GWNO riskset changed")
    return sorted(ids)


def compare_versions(old, new, ids, years, *, excluded=frozenset()):
    """Compare same target years, excluding documented source coverage gaps.

    Absence of a GED event is zero in the event-sum diagnostic ONLY when
    country is inside known territorial coverage; elsewhere unobserved.
    """
    cohort=_valid_ids(ids)
    years=tuple(years)
    if not years or len(set(years))!=len(years) or (
        any(type(year) is not int or year<MIN_YEAR or year>2022 for year in years)
    ):
        raise ValueError("Invalid or repeated historical calendar years")
    if excluded not in (frozenset(),frozenset({SYRIA})):
        raise ValueError("Only verified GED19 Syria coverage may be excluded")
    eligible=[cid for cid in cohort if cid not in excluded]
    yearly=[]
    mismatch=[]
    exact=0
    changes=0
    signed=0
    absdiff=0
    positives_old=0
    positives_new=0
    for year in years:
        current_mismatch=0
        current_exact=0
        current_label_changes=0
        for cid in eligible:
            a=old.get((cid,year),0)
            b=new.get((cid,year),0)
            if type(a) is not int or type(b) is not int or min(a,b)<0:
                raise ValueError("Malformed GED best-death event count")
            eq=a==b
            flip=(a>=25)!=(b>=25)
            exact+=int(eq)
            current_exact+=int(eq)
            changes+=int(flip)
            current_label_changes+=int(flip)
            signed+=b-a
            absdiff+=abs(b-a)
            positives_old+=int(a>=25)
            positives_new+=int(b>=25)
            current_mismatch+=int(not eq)
            if flip:
                mismatch.append({
                    "target_year":year,"GWNO":cid,
                    "old_best_statebased_deaths":a,
                    "new_best_statebased_deaths":b,
                    "old_active":a>=25,"new_active":b>=25,
                })
        yearly.append({
            "target_year":year,
            "eligible_country_n":len(eligible),
            "numerical_best_death_count_mismatches":current_mismatch,
            "binary_best_ge25_label_flips":current_label_changes,
            "exact_count_matches":current_exact,
        })
    n=len(eligible)*len(years)
    return {
        "target_years":list(years),
        "eligible_countries_per_year":len(eligible),
        "excluded_GWNO_due_official_GED_coverage":sorted(excluded),
        "observed_country_years":n,
        "excluded_unobserved_country_years":len(excluded)*len(years),
        "exact_best_death_count_match_n":exact,
        "exact_best_death_count_match_fraction":exact/n,
        "best_death_count_mismatch_n":n-exact,
        "best_ge25_binary_label_change_n":changes,
        "old_active_country_year_n":positives_old,
        "new_active_country_year_n":positives_new,
        "signed_new_minus_old_best_deaths":signed,
        "absolute_best_death_count_revision_sum":absdiff,
        "annual":yearly,
        "binary_flip_details":mismatch,
        "not_inference_from_iid_samples":True,
    }


def syria_coverage(old, later, ids, yearstop):
    cohort=_valid_ids(ids)
    if SYRIA not in cohort or yearstop not in (2018,2019,2020,2021):
        raise ValueError("Unregistered GED archive country or year")
    years=tuple(range(MIN_YEAR,yearstop+1))
    return {
        "GWNO":SYRIA,
        "years":list(years),
        "old_best_state_based_deaths":[old.get((SYRIA,y),0) for y in years],
        "new_best_state_based_deaths":[later.get((SYRIA,y),0) for y in years],
        "old_best_ge25_year_n":sum(old.get((SYRIA,y),0)>=25 for y in years),
        "new_best_ge25_year_n":sum(later.get((SYRIA,y),0)>=25 for y in years),
        "old_event_record_absence_is_not_proof_of_no_real_violence":True,
    }


def evaluate(source_bytes, pdf_bytes, archive, anchor, issue):
    if (set(source_bytes)!=set(VINTAGES) or set(pdf_bytes)!=set(CODEBOOKS) or
        anchor.get("schema")!="idealab.psico.legacy_ged_to_countryyear_equivalence_feasibility.v1" or
        anchor.get("official_GED23_1_vs_OrganizedViolenceCY23_1_same_version",{}).get(
            "exact_death_count_match_n")!=2352 or
        anchor.get("historical_GED_for_original_GEO_CY_predictions_authorized") is not False or
        issue.get("official_2027_outcomes_resolved")!=0):
        raise ValueError("Original GED-CY bridge, issue status and five archives required")
    ids=_valid_ids([x["country_id"] for x in issue["countries"]])
    if (any(archive.get(v,{}).get("CSV")!=ALL_URLS[v] for v in VINTAGES) or
        any(archive.get(v,{}).get("CODEBOOK")!=CODEBOOKS[v]["url"]
            for v in NEW_VINTAGES)):
        raise ValueError("Historical GED archive URLs are not official or are ambiguous")
    if (anchor.get("pinned_original_GED_zip_SHA256")!=PINNED_GED_SHA256 or
        anchor.get("GED19_1_syria_exclusion",{}).get("GWNO")!=SYRIA):
        raise ValueError("Original official 19/22/23 SHA pins or Syria exclusion changed")
    metadata={}
    deaths={}
    for v in VINTAGES:
        expected=PINNED_GED_SHA256.get(v) or PINNED_NEW_SHA256.get(v)
        meta,rows=parse_ged(source_bytes[v],v,expected_sha256=expected)
        metadata[v]=meta
        deaths[v]=rows
    for v, expected_last in [("19.1",2018),("20.1",2019),("21.1",2020),
                             ("22.1",2021),("23.1",2022)]:
        if metadata[v]["last_recorded_event_year"]!=expected_last:
            raise ValueError("Official GED year coverage changed for "+v)
    doc={}
    for v in NEW_VINTAGES:
        raw=pdf_bytes[v]
        if not raw.startswith(b"%PDF-") or len(raw)<1500:
            raise ValueError("GED "+v+" codebook is not a substantive official PDF")
        digest=hashlib.sha256(raw).hexdigest()
        if PINNED_CODEBOOK_SHA256 and digest!=PINNED_CODEBOOK_SHA256[v]:
            raise ValueError("Historical GED codebook PDF checksum changed")
        doc[v]={**CODEBOOKS[v], "sha256_of_current_official_PDF":digest,
                "notarized_original_release_timestamp":False,
                "dataset_ZIP_digest_not_independently_timestamped_at_origin":True}
    if any(deaths["19.1"].get((SYRIA,year),0)!=0
           for year in range(2011,2019)):
        raise ValueError("GED 19.1 Syria exclusion historical observation changed")
    pairs=[
        ("19.1","20.1",2018, frozenset({SYRIA})),
        ("20.1","21.1",2019, frozenset()),
        ("21.1","22.1",2020, frozenset()),
        ("22.1","23.1",2021, frozenset()),
        ("20.1","23.1",2019, frozenset()),
        ("21.1","23.1",2020, frozenset()),
    ]
    comparison=[]
    for a,b,yearstop,excluded in pairs:
        years=tuple(range(MIN_YEAR,yearstop+1))
        stats=compare_versions(deaths[a],deaths[b],ids,years,excluded=excluded)
        comparison.append({
            "old_version":a,"new_version":b,
            "comparison":stats,
            "is_consecutive_release":(int(b[:2])==int(a[:2])+1),
            "same_country_years_not_independent_across_pairs":True,
            "old_release_last_event_year":metadata[a]["last_recorded_event_year"],
            "new_release_last_event_year":metadata[b]["last_recorded_event_year"],
        })
    # Deliberately separate 19.1 Syria gap from real country-year labels:
    # it is not an inactive country-year and is never in the denominator.
    mask19=comparison[0]["comparison"]
    naive=compare_versions(deaths["19.1"],deaths["20.1"],
                           ids,range(2011,2019))
    if naive["observed_country_years"]!=1568 or mask19["observed_country_years"]!=1560:
        raise AssertionError("GED 19.1 false-zero Syria exposure in 2011–18")
    if mask19["excluded_unobserved_country_years"]!=8 or (
        naive["best_ge25_binary_label_change_n"] <
        mask19["best_ge25_binary_label_change_n"]
    ):
        raise AssertionError("Territorial coverage exclusion did not reduce false negatives")
    syria19to20=syria_coverage(deaths["19.1"],deaths["20.1"],ids,2018)
    syria20to23=syria_coverage(deaths["20.1"],deaths["23.1"],ids,2019)
    if syria19to20["old_best_ge25_year_n"]!=0:
        raise AssertionError("GED19 Syria structural missingness altered")
    return {
        "schema":"idealab.psico.ged_20_21_intervintage_coverage_2011_2022.v1",
        "status":"OFFICIAL_GED_VINTAGE_MEASUREMENT_STRESS_NO_MODEL_FORECASTS",
        "archived_catalog":"https://ucdp.uu.se/downloads/olddw.html",
        "comparison_primary_variable":
            "sum GED event best where type_of_violence=1 by GWNO and event year, >=25",
        "source_zip_sha256":{v:metadata[v]["sha256"] for v in VINTAGES},
        "source_zip_metadata":metadata,
        "official_20_21_codebooks":doc,
        "original_frozen_196_GWNO":True,
        "original_GEO2027_forecast_SHA256":SOURCE_SHA256,
        "original_23_1_same_vintage_GED_CY_bridge_validated_in_prior_report":True,
        "selected_years_in_analysis":list(range(2011,2023)),
        "pairs":comparison,
        "GED19_1_vs_20_1_naive_incorrect_Syria_zero_comparison":
            {
                "naive_total_country_years":naive["observed_country_years"],
                "naive_label_flips":naive["best_ge25_binary_label_change_n"],
                "proper_territorial_coverage_censored_country_years":
                    mask19["observed_country_years"],
                "proper_territorial_coverage_censored_flips":
                    mask19["best_ge25_binary_label_change_n"],
                "unobserved_Syria_country_years":8,
                "false_classification_flips_due_to_structural_missingness":
                    naive["best_ge25_binary_label_change_n"] -
                    mask19["best_ge25_binary_label_change_n"],
                "coverage_status":"GED19.1 excluded Syria, GED20.1 includes Syria",
                "no_real_world_zero_labels_imputed":True,
            },
        "Syria_GWNO652_19_1_to_20_1":syria19to20,
        "Syria_GWNO652_20_1_to_23_1":syria20to23,
        "no_historical_contemporaneous_issue_sha_proof":True,
        "current_official_source_checksums_are_not_historical_timestamp_proofs":True,
        "GED22_1_2022_documented_extraction_not_evidence_of_original_ZIP_bytes":True,
        "older_GED20_21_as_identical_to_OrganizedViolenceCY23_1":False,
        "historical_model_fitting_authorized":False,
        "new_forecast_probabilities_issued":0,
        "GEO2027_GEO2028_forecasts_modified":False,
        "no_2027_outcomes_scored":True,
        "interpretation":(
            "Cohort-paired event-sum label drift measures source revisions and "
            "coverage. GED19 omitted Syria; its zero-event record must never be "
            "coded as observed inactive. GED20.1 and 21.1 codebook extraction "
            "dates document historical source systems, not the cryptographic "
            "availability of today's exact GED ZIP at historical origin. "
            "These comparisons cannot establish prospective skill."
        ),
    }


def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--check-report",action="store_true")
    arg.add_argument("--print-report",action="store_true")
    args=arg.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Original 2027 issued probability vector modified")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),
                 ORIGINAL.read_bytes(),OLD_SHADOW.read_bytes(),
                 OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    raw_archive=request(ARCHIVE)
    catalogue=discover_ged(raw_archive)
    sources={v:request(ALL_URLS[v],MAX_ZIP) for v in VINTAGES}
    books={v:request(CODEBOOKS[v]["url"],MAX_PDF) for v in NEW_VINTAGES}
    anchor=json.loads(ANCHOR.read_text(encoding="utf-8"))
    issue=json.loads(ISSUE.read_text(encoding="utf-8"))
    report=evaluate(sources,books,catalogue,anchor,issue)
    payload=json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if args.check_report and REPORT.read_bytes()!=payload.encode("utf-8"):
        raise ValueError("Five official GED ZIP + two PDF report is not byte-identical")
    if args.print_report:
        print("GED_20_21_COVERAGE_AUDIT_BEGIN",flush=True)
        print(payload,end="")
        print("GED_20_21_COVERAGE_AUDIT_END",flush=True)
    else:
        print(json.dumps({
            "archive_sha256":report["source_zip_sha256"],
            "pairs":[{"old":x["old_version"],"new":x["new_version"],
                      "count":x["comparison"]["observed_country_years"],
                      "flips":x["comparison"]["best_ge25_binary_label_change_n"]}
                     for x in report["pairs"]],
            "syria_gap":report[
                "GED19_1_vs_20_1_naive_incorrect_Syria_zero_comparison"],
            "not_prospective":report["no_historical_contemporaneous_issue_sha_proof"],
        },indent=2,sort_keys=True))


if __name__=="__main__":
    main()
