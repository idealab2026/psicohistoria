#!/usr/bin/env python3
"""Fail-closed temporal-provenance gate for GEO H2 2014–2025 retrospective.

Source codebook year is *not* an attested release date. It can exclude a
purported contemporaneous source when later than its simulated origin or
target, but cannot on its own certify past availability or exact downloaded
bytes. No 2014-2025 retrospective score becomes a historical issued forecast.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit as audit_issued,
)
from backtest_archived_country_vintages import SOURCES
from probe_ucdp_organized_vintages import ARCHIVE, discover, request
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256

ROOT = Path(__file__).resolve().parents[1]
ROLLING = ROOT / "data/geo-h2-rolling-historical-2014-2025.json"
TWO_FOLD = ROOT / "data/geo2027-h2-fatality-estimate-brier-sensitivity.json"
REPORT = ROOT / "data/geo-h2-2014-2025-temporal-source-eligibility.json"
N = 196
YEARS = tuple(range(2014, 2026))
AUDIT_DATE = "2026-11-17"
# Explicitly dated OFFICIAL codebooks, not unverified assumed artifact release
# timestamps. Their present-day PDF bytes will be checksum-pinned in REPORT.
CODEBOOKS = {
    "23.1": {
        "codebook_compiled_year": 2023,
        "url": "https://ucdp.uu.se/downloads/organizedviolencecy/UCDP_OrganizedViolenceCY_Codebook_231.pdf",
        "last_data_year": 2022,
    },
    "24.1": {
        "codebook_compiled_year": 2024,
        "url": "https://ucdp.uu.se/downloads/organizedviolencecy/UCDP_OrganizedViolenceCY_Codebook_241.pdf",
        "last_data_year": 2023,
    },
}


def _delta(fold, label="best"):
    return fold["comparison"]["scenarios"][label][
        "four_state_minus_original_delta_brier"]


def classify(origin, target, edition, codebooks=CODEBOOKS):
    """Three-way calendar-year plausibility only, NEVER availability proof."""
    if (type(origin) is not int or type(target) is not int or
        target != origin + 2 or edition not in codebooks or
        codebooks[edition]["last_data_year"] != SOURCES[edition]["last_year"] or
        SOURCES[edition]["last_year"] < origin):
        raise ValueError("Invalid fixed historical origin, target or documented codebook")
    doc_year = codebooks[edition]["codebook_compiled_year"]
    if type(doc_year) is not int or doc_year < 2000:
        raise ValueError("Codebook compiled year not verified")
    if doc_year > target:
        label = "CODEBOOK_YEAR_AFTER_TARGET"
    elif doc_year == target:
        label = "CODEBOOK_YEAR_EQUALS_TARGET_EXACT_DATE_UNKNOWN"
    else:
        label = "CODEBOOK_YEAR_BEFORE_TARGET_NOT_BYTE_NOTARIZED"
    return {
        "origin_year": origin,
        "target_year": target,
        "origin_edition": edition,
        "codebook_compiled_year": doc_year,
        "source_last_observation_year": SOURCES[edition]["last_year"],
        "source_year_after_simulated_origin": doc_year > origin,
        "codebook_year_relative_to_target": label,
        "origin_year_contemporaneous_file_proven": False,
        "actual_origin_issue_timestamp_notarized": False,
        "exact_original_file_bytes_notarized_before_target": False,
        "codebook_year_cannot_certify_actual_release_date": True,
        "reason": (
            "Official codebook compilation-year evidence only: no original "
            "file checksum independently notarized before simulation date; "
            "past historical values in the modern archive may have been revised."
        ),
    }


def _avg_folds(folds, scenario):
    """Balanced annual country cohorts: equal year weights, NOT IID inference."""
    if not folds or len(set(f["target_year"] for f in folds)) != len(folds):
        raise ValueError("Empty/duplicated historical target year set")
    n=len(folds)
    scores={}
    for k in ("original_binary","four_state_intensity"):
        scores[k]={
            field:sum(f["comparison"]["scenarios"][scenario][k][field]
                      for f in folds)/n
            for field in ("brier","logloss")}
    delta=scores["four_state_intensity"]["brier"]-scores["original_binary"]["brier"]
    sum_positives=sum(f["comparison"]["scenarios"][scenario]["positives"]
                      for f in folds)
    if abs(delta - sum(_delta(f,scenario) for f in folds)/n) > 5e-11:
        raise AssertionError("Balanced-country-years score decomposition fails")
    return {
        "year_n":n,
        "country_year_n":n*N,
        "positives":sum_positives,
        "original_binary":scores["original_binary"],
        "four_state_intensity":scores["four_state_intensity"],
        "four_state_minus_original_delta_brier":delta,
        "lower_brier_in_this_retro_sample":
            "four_state" if delta < -1e-12 else
            "binary_original" if delta > 1e-12 else "tie",
    }


def audit(rolling, twofold, issue, codebook_sha, listed_archive_links):
    if (rolling.get("schema") != "idealab.psico.geo_h2_rolling_historical_2014_2025.v1" or
        rolling.get("not_prospective_or_independently_timestamped_skill") is not True or
        rolling.get("unique_country_years_primary_n") != 2352 or
        twofold.get("schema") !=
            "idealab.psico.geo_h2_crossrelease_fatality_label_sensitivity.v1" or
        twofold.get("prospective_skill_demonstrated") is not False or
        rolling.get("source_archives_sha256") != {
            version: spec["sha256"] for version, spec in SOURCES.items()
        } or
        len(issue.get("countries",[])) != N or
        issue.get("official_2027_outcomes_resolved") != 0 or
        set(codebook_sha) != set(CODEBOOKS) or
        set(listed_archive_links) != {"23.1","24.1","25.1"}):
        raise ValueError("Prior published source audit, frozen issue or original sources changed")
    for version, digest in codebook_sha.items():
        if not isinstance(digest,str) or not re.fullmatch(r"[0-9a-f]{64}",digest):
            raise ValueError("Official codebook PDF not verified by SHA-256")
    for version in ("23.1","24.1","25.1"):
        if SOURCES[version]["url"] not in listed_archive_links[version]:
            raise ValueError("Original pinned source is not listed in official archive")
    unique = rolling["primary_unique_year_series"]
    later = rolling["later_vintage_same_year_sensitivity_NOT_second_sample"]
    if (unique.get("year_n") != 12 or unique.get("observations") != 2352 or
        later.get("observations") != 2352):
        raise ValueError("Source-vintage stress is not the exact 12x196 fixed cohort")
    folds=unique["folds"]
    if ([f["target_year"] for f in folds] != list(YEARS) or
        len(set((f["target_year"],f["origin_year"]) for f in folds)) != 12 or
        any(f["country_n"] != N or f["last_training_year"] !=
            f["origin_year"] or f["target_year"] != f["origin_year"] + 2
            for f in folds)):
        raise ValueError("Retrospective rolling folds are changed or leaked")
    report_rows=[]
    for fold in folds:
        label=classify(fold["origin_year"],fold["target_year"],
                       fold["origin_release"])
        label["n_GWNO"]=N
        label["original_fold_brier"]=fold["comparison"]["scenarios"]["best"]["original_binary"]["brier"]
        label["four_state_fold_brier"]=fold["comparison"]["scenarios"]["best"]["four_state_intensity"]["brier"]
        label["delta_four_state_minus_original"]= _delta(fold)
        report_rows.append(label)
    groups={
        "after_target":[f for f,r in zip(folds,report_rows)
                        if r["codebook_year_relative_to_target"] ==
                        "CODEBOOK_YEAR_AFTER_TARGET"],
        "same_target_year_unknown_date":[f for f,r in zip(folds,report_rows)
                        if r["codebook_year_relative_to_target"] ==
                        "CODEBOOK_YEAR_EQUALS_TARGET_EXACT_DATE_UNKNOWN"],
        "pre_target_year_only_nonnotarized":[f for f,r in zip(folds,report_rows)
                        if r["codebook_year_relative_to_target"] ==
                        "CODEBOOK_YEAR_BEFORE_TARGET_NOT_BYTE_NOTARIZED"],
    }
    if ([len(groups[k]) for k in (
            "after_target","same_target_year_unknown_date",
            "pre_target_year_only_nonnotarized")] != [9,1,2] or
        [f["target_year"] for f in groups["pre_target_year_only_nonnotarized"]] !=
        [2024,2025] or
        any(not r["source_year_after_simulated_origin"] for r in report_rows)):
        raise AssertionError("As-of source-year temporal barrier changed")
    # IMPORTANT: at-year-granularity we cannot certify the archived file itself
    # as having been byte-for-byte available then. These two folds are *only*
    # plausible pre-target retrospective cohorts, NOT prospective issuance.
    pretarget=groups["pre_target_year_only_nonnotarized"]
    if ([f["origin_release"] for f in pretarget]!=["23.1","24.1"] or
        [f["outcome_release"] for f in pretarget]!=["25.1","26.1"]):
        raise AssertionError("Prior two real archive separated target blocks changed")
    for current in pretarget:
        frozen=next(f for f in twofold["folds"]
                    if f["target_year"]==current["target_year"])
        for scenario in ("low","best","high"):
            for model in ("original_binary","four_state_intensity"):
                for metric in ("brier","logloss"):
                    a=current["comparison"]["scenarios"][scenario][model][metric]
                    b=frozen["evaluation"]["scenarios"][scenario][model][metric]
                    if abs(a-b)>1e-10:
                        raise AssertionError("Two recent year source-replay frozen scores changed")
    res={
        key:{
            "target_years":[f["target_year"] for f in group],
            "best_label":_avg_folds(group,"best"),
        } for key,group in groups.items()
    }
    before=[*groups["after_target"],*groups["same_target_year_unknown_date"]]
    res["not_pre_target_year_based"]={
        "target_years":[f["target_year"] for f in before],
        "best_label":_avg_folds(before,"best"),
    }
    res["complete_rolling_retrospective_not_asof"]={
        "target_years":list(YEARS),
        "best_label":_avg_folds(folds,"best"),
    }
    full=unique["pooled"]["scenarios"]["best"]
    for model in ("original_binary","four_state_intensity"):
        for metric in ("brier","logloss"):
            if abs(res["complete_rolling_retrospective_not_asof"][
                "best_label"][model][metric] - full[model][metric]) > 1e-10:
                raise AssertionError("Full rolling reference no longer reproduced")
    if not (res["complete_rolling_retrospective_not_asof"][
        "best_label"]["four_state_minus_original_delta_brier"] < 0 and
        res["not_pre_target_year_based"]["best_label"][
            "four_state_minus_original_delta_brier"] < 0 and
        res["pre_target_year_only_nonnotarized"]["best_label"][
            "four_state_minus_original_delta_brier"] > 0):
        raise AssertionError("Observed historic time-eligibility sign attribution changed")
    return {
        "schema":"idealab.psico.geo_h2_rolling_asof_source_eligibility.v1",
        "audit_design_date":AUDIT_DATE,
        "status":"TEMPORAL_PROVENANCE_EXCLUSION_NO_NEW_PREDICTIONS",
        "original_GEO2027_issue_sha256":SOURCE_SHA256,
        "official_original_archive_data_sha256":rolling["source_archives_sha256"],
        "official_codebooks_compilation_years":{
            version:{
                "url":spec["url"],
                "compiled_year":spec["codebook_compiled_year"],
                "source_last_data_year":spec["last_data_year"],
                "pdf_sha256_as_of_audit":codebook_sha[version],
                "exact_publication_date_verified":False,
                "past_original_dataset_checksum_timestamp_notarized":False,
            } for version,spec in CODEBOOKS.items()},
        "official_archival_catalog":ARCHIVE,
        "official_listed_archive_23_24_25_present":True,
        "no_22_1_organized_violence_cy_version_listed_on_official_archive":True,
        "absence_from_archive_not_proof_no_older_data_ever_existed":True,
        "historical_PDF_year_is_compilation_not_independent_file_release_timestamp":True,
        "all_12_pseudo_origins_precede_edition_codebook_year":True,
        "n_pseudo_origins_with_source_verified_available_at_pseudo_origin":0,
        "n_target_years_with_prior_year_codebook_but_no_file_time_hash":2,
        "n_target_years_after_own_source_codebook_year":9,
        "n_target_years_same_as_source_codebook_year_unresolved":1,
        "n_target_years_with_hash_timestamp_confirmed_source_available_before_target":0,
        "first_issued_2027_and_2028_probabilities_unchanged":True,
        "outcomes_2027_observed":0,
        "genuine_contemporaneously_notarized_historical_issue_count":0,
        "strict_asof_rolling_forecast_skill_estimate":None,
        "year_level_only_eligibility":report_rows,
        "score_decomposition_by_source_timing":res,
        "not_independent_confidence_or_predictive_intervals":True,
        "no_tuning_or_original_model_reissue":True,
        "interpretation":(
            "The 12-year four-state Brier lead originates in years for which "
            "the chosen origin-edition codebook postdates the evaluated outcome "
            "year, or comes from the same year without precise release dates. "
            "The two later 2024/25 years have codebooks dated before their "
            "outcomes, yet the archived data bytes are not contemporaneously "
            "notarized and neither historical forecast was issued then. "
            "Year-level plausibility does not confer actual out-of-sample skill."
        ),
        "limitations":(
            "Archived present-day download SHA authenticates current official "
            "bytes, NOT their historical availability. Codebook compilation "
            "years 2023/2024 are not exact public release dates. The UCDP "
            "archive's lack of earlier OrganizedViolenceCY editions is NOT "
            "evidence that no underlying GED or other UCDP dataset existed. "
            "The main 2014-2025 rolling score is a source-revised ex-post "
            "diagnostic, never a pre-registered real-world prospective test."
        ),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report",action="store_true")
    parser.add_argument("--print-report",action="store_true")
    args=parser.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Frozen original 2027 forecast checksum changed")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    raw=request(ARCHIVE)
    catalog=discover(raw.decode("utf-8"))
    listed={version:[e["url"] for e in entries]
            for version,entries in catalog.items() if version in
            ("23.1","24.1","25.1")}
    digests={}
    for version,spec in CODEBOOKS.items():
        data=request(spec["url"])
        if not data.startswith(b"%PDF-") or len(data) < 1500:
            raise ValueError("Official document is not a substantial PDF")
        digests[version]=hashlib.sha256(data).hexdigest()
    files=[json.loads(p.read_text(encoding="utf-8"))
           for p in (ROLLING,TWO_FOLD,ISSUE)]
    report=audit(*files,digests,listed)
    encoded=json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    if args.check_report and REPORT.read_bytes()!=encoded.encode("utf-8"):
        raise ValueError("Official UCDP release-eligibility report is not byte-identical")
    print("GEO_H2_ASOF_SOURCE_GATE_BEGIN")
    print(encoded if args.print_report else json.dumps({
        "schema":report["schema"],
        "source_timing_categories":{
            k: {"years":v["target_years"],
                "paired_brier_delta":v["best_label"][
                    "four_state_minus_original_delta_brier"]}
            for k,v in report["score_decomposition_by_source_timing"].items()},
        "genuine_asof_issue_count":report[
            "genuine_contemporaneously_notarized_historical_issue_count"],
    },sort_keys=True,indent=2))
    print("GEO_H2_ASOF_SOURCE_GATE_END")


if __name__=="__main__":
    main()
