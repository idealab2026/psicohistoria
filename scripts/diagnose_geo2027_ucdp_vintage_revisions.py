#!/usr/bin/env python3
"""GEO2027 UCDP threshold-label vintage drift: official editions 23.1..26.1.

Identify what is empirically observed: whether the SAME historical country-year
moves across the >=25 state-based deaths threshold in successive archived
UCDP data releases. Never confuse revised historical labels, geopolitical
2025->2027 transitions, or true cross-country dependence.

The source-separated 2024 holdout (23.1 origin -> 25.1 target) is rescored
only against a 26.1 later LABEL revision with IDENTICAL frozen predictions.
2025 has no later archive in this study, so no 2025 revision score is invented.
A rank ceiling records why 2 annual blocks cannot estimate an unrestricted
196-country covariance structure.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from backtest_archived_country_vintages import SOURCES, fetch_archives
from diagnose_geo2027_transition_skill import make_holdout_rows
from prepare_geo2027_transition_alerts import (
    FORECAST_PATH, SOURCE_SHA256, sha,
)

VERSIONS = ("23.1", "24.1", "25.1", "26.1")
PAIR_RELEASES = (
    ("23.1", "24.1"), ("24.1", "25.1"), ("25.1", "26.1"),
    ("23.1", "25.1"), ("24.1", "26.1"),
)
FOCUS_YEARS = tuple(range(2018, 2025))
HOLDOUT_N = 196
HOLDOUT_TARGET = 2024
ORIGIN_YEAR = 2022


def validate_records(records, *, label="edition"):
    if not isinstance(records, dict) or not records:
        raise ValueError(f"Empty {label} country-year source")
    for cid, years in records.items():
        if type(cid) is not int or not 1 <= cid <= 2000 or not years:
            raise ValueError(f"Invalid {label} country ID/history")
        for year, state in years.items():
            if (type(year) is not int or year < 1989 or year > 2025
                or type(state) is not int or state not in (0,1)):
                raise ValueError(f"Invalid {label} annual binary label")


def drift(old, new, *, year=None, cohort=None):
    """Changes in label for the same ID/year; missing labels NEVER become 0."""
    validate_records(old, label="old edition")
    validate_records(new, label="new edition")
    if year is not None and (type(year) is not int or not 1989<=year<=2025):
        raise ValueError("Unexpected vintage comparison target year")
    if cohort is not None and (
        not cohort or any(type(cid) is not int for cid in cohort) or
        len(cohort)!=len(set(cohort))
    ):
        raise ValueError("Non-unique, empty or noninteger fixed cohort")
    ids = sorted(cohort if cohort is not None else old)
    shared=missing_old=missing_later=stable_inactive=stable_active=up=down=0
    for cid in ids:
        old_hist=old.get(cid,{})
        new_hist=new.get(cid,{})
        if cohort is not None and not old_hist:
            missing_old+=1
        selected_years = (year,) if year is not None else tuple(sorted(old_hist))
        for y in selected_years:
            p=old_hist.get(y)
            q=new_hist.get(y)
            if p is None:
                missing_old+=1 if not (cohort is not None and not old_hist) else 0
                continue
            if q is None:
                missing_later+=1
                continue
            shared+=1
            if p==q==0:stable_inactive+=1
            elif p==q==1:stable_active+=1
            elif p==0 and q==1:up+=1
            elif p==1 and q==0:down+=1
            else:raise ValueError("Missing binary classification")
    # Only when a single year is specified can we assess additions in
    # the same cohort; additions across releases may be whole *new* years.
    n_explicit=len(ids) if cohort is not None and year is not None else None
    return {
        "specified_year": year,
        "fixed_cohort_n": n_explicit,
        "common_country_years":shared,
        "missing_in_earlier":missing_old,
        "missing_in_later":missing_later,
        "same_inactive":stable_inactive,
        "same_active":stable_active,
        "changed_inactive_to_active":up,
        "changed_active_to_inactive":down,
        "revised_binary_threshold_labels":up+down,
        "revision_fraction_of_common":(up+down)/shared if shared else None,
        "later_minus_earlier_active_count_on_common_pairs":up-down,
        "abs_label_churn_not_necessarily_change_in_n_active":up+down,
        "unresolved_later_labels_never_imputed_inactive":True,
    }


def threshold_scores(rows, label_map):
    """Brier/logloss on fixed 196 forecasts with only later-year labels replaced."""
    if len(rows)!=HOLDOUT_N or len({r["country_id"] for r in rows})!=HOLDOUT_N:
        raise ValueError("Original frozen 2024 holdout is not 196 unique countries")
    if any(cid not in label_map for cid in (r["country_id"] for r in rows)):
        raise ValueError("Later official country-year label missing from holdout")
    output={}
    for state in (0,1):
        subset=[r for r in rows if r["origin_state"]==state]
        if len(subset)<20:
            raise ValueError("Unexpected cohort origin risk set")
        changed=sum(r["outcome"] != label_map[r["country_id"]] for r in subset)
        p_old=sum(r["outcome"] for r in subset)
        p_new=sum(label_map[r["country_id"]] for r in subset)
        old_trans=sum(int(r["outcome"]!=state) for r in subset)
        new_trans=sum(int(label_map[r["country_id"]]!=state) for r in subset)
        summaries={}
        for name in ("p_model","p_global_markov"):
            ps=[r[name] for r in subset]
            if any(type(p) not in (int,float) or not math.isfinite(p) or not 0<p<1
                   for p in ps):
                raise ValueError("Invalid pre-target frozen historical probability")
            def scores(outcomes):
                n=len(outcomes)
                return {
                    "brier":sum((p-y)**2 for p,y in zip(ps,outcomes))/n,
                    "logloss":-sum(y*math.log(p)+(1-y)*math.log1p(-p)
                                   for p,y in zip(ps,outcomes))/n,
                }
            old_scores=scores([r["outcome"] for r in subset])
            new_scores=scores([label_map[r["country_id"]] for r in subset])
            summaries[name]={
                "first_target_release_25_1":old_scores,
                "later_revised_release_26_1":new_scores,
                "delta_brier_revised_minus_first":new_scores["brier"]-old_scores["brier"],
                "delta_logloss_revised_minus_first":
                    new_scores["logloss"]-old_scores["logloss"],
            }
        output[str(state)]={
            "n":len(subset),
            "country_year_label_changes_first_to_revised":changed,
            "active_first_25_1":p_old,
            "active_revised_26_1":p_new,
            "transitions_from_2022_origin_first_25_1":old_trans,
            "transitions_from_2022_origin_revised_26_1":new_trans,
            "scoring_identical_frozen_country_probabilities":summaries,
        }
    if sum(x["n"] for x in output.values())!=HOLDOUT_N:
        raise ValueError("Origin groups must partition exactly 196 countries")
    return output


def diagnose(vintages, metadata, holdout):
    if set(vintages)!=set(VERSIONS) or set(metadata)!=set(VERSIONS):
        raise ValueError("The 4 pinned UCDP editions are mandatory")
    for version in VERSIONS:
        spec=SOURCES[version]
        if metadata[version].get("sha256")!=spec["sha256"]:
            raise ValueError("UCDP source SHA-256 provenance changed")
        records=vintages[version]
        validate_records(records, label=version)
        if max(max(y) for y in records.values())!=spec["last_year"]:
            raise ValueError("UCDP edition has unexpected last observed year")
    if len(holdout)!=392 or sum(r["outcome"] for r in holdout)!=69:
        raise ValueError("Original published 2024/25 separated holdout was modified")
    current=[r for r in holdout if r["target_year"]==HOLDOUT_TARGET]
    later={cid:years[HOLDOUT_TARGET] for cid,years in vintages["26.1"].items()
           if HOLDOUT_TARGET in years}
    first={cid:years[HOLDOUT_TARGET] for cid,years in vintages["25.1"].items()
           if HOLDOUT_TARGET in years}
    if (len(current)!=HOLDOUT_N or
        any(r["outcome"]!=first.get(r["country_id"]) for r in current)):
        raise ValueError("Target-first-release 25.1 2024 label mismatch")
    holdout_ids=[r["country_id"] for r in current]
    revision=drift(vintages["25.1"],vintages["26.1"],
                   year=HOLDOUT_TARGET,cohort=holdout_ids)
    if revision["missing_in_earlier"] or revision["missing_in_later"]:
        raise ValueError("Later complete 2024 source has missing original holdout labels")
    if revision["common_country_years"]!=HOLDOUT_N:
        raise ValueError("All 196 original country labels needed for revision scoring")
    scores=threshold_scores(current,later)
    if (sum(x["country_year_label_changes_first_to_revised"] for x in scores.values())
        !=revision["revised_binary_threshold_labels"]):
        raise ValueError("Revision panel and fixed-cohort score drift differ")
    pairs=[]
    for old_version,new_version in PAIR_RELEASES:
        old=vintages[old_version]
        new=vintages[new_version]
        annual=[]
        for year in FOCUS_YEARS:
            if year<=SOURCES[old_version]["last_year"]:
                x=drift(old,new,year=year)
                annual.append(x)
        pairs.append({
            "origin_ed":old_version,
            "later_ed":new_version,
            "all_common_years":drift(old,new),
            "fixed_recent_country_year_drift_by_year":annual,
        })
    # Matrix rank is bound by independent YEAR blocks, not country count.
    # Unrestricted 196x196 covariance has 19110 off-diagonal entries.
    return {
        "schema":"idealab.psico.geo2027_ucdp_revision_and_dependence_identification.v1",
        "status":"EX_POST_PINNED_OFFICIAL_VINTAGE_REVISION_DIAGNOSTIC_NO_2027_OUTCOMES",
        "study_date":"2026-11-12",
        "target_rule":"binary state-based organized violence >=25 country-year deaths",
        "source_versions_and_sha256": {
            version:SOURCES[version]["sha256"] for version in VERSIONS
        },
        "source_release_dating_independently_notarized":False,
        "archived_source_coverage_last_years": {
            k:SOURCES[k]["last_year"] for k in VERSIONS
        },
        "pairwise_revisions_all_years_and_recent_years":pairs,
        "2024_196_country_original_holdout_later_label_revision":revision,
        "2024_196_country_original_holdout_score_sensitivity":scores,
        "2025_later_revision_diagnostic":None,
        "2025_later_revision_why_unavailable":
            "The source series ends at 26.1 (2025): no 27.1 or later release is pinned here.",
        "cross_country_dependence_identification": {
            "genuinely_source_separated_target_year_blocks":[2024,2025],
            "n_independent_year_blocks_not_established":True,
            "maximum_empirical_centered_covariance_rank_with_two_annual_blocks":1,
            "n_country_coordinates":196,
            "unrestricted_pairwise_cross_country_covariances":19110,
            "minimal_year_blocks_for_full_empirical_covariance_rank_if_all_identical_coordinates_observed":197,
            "revised_historical_12_year_blocks_upper_rank":11,
            "actual_rank_or_correlations_estimated":False,
            "sample_covariance_cannot_separate_marginal_miscalibration_from_shared_shocks":True,
        },
        "original_forecast_modified":False,
        "original_shadow_modified":False,
        "original_15_alerts_modified":False,
        "prospective_2027_outcomes_observed":0,
        "prospective_skill_or_independent_dependence_estimated":False,
        "limitations":(
            "Compares same country/year threshold under four official archives, "
            "not geopolitical state changes over time. Full-year pairwise drift "
            "is year-composition weighted; revisions near 25-death threshold "
            "may change labels but source availability does not independently "
            "notarize source issuance time. Outcomes of 2024 were already "
            "examined before this study, so score sensitivity is descriptive. "
            "2025 revision is not available yet. Two source-separated annual "
            "outcome blocks cannot identify a high-dimensional covariance; "
            "with two observations a centered 196x196 empirical covariance "
            "has rank<=1 even if each coordinate were observed. No covariance "
            "or p-value estimated and no issued 2027 probability altered."
        ),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report")
    args=parser.parse_args()
    if sha(FORECAST_PATH.read_bytes()) != SOURCE_SHA256:
        raise ValueError("Original prospective GEO2027 forecast must remain fixed")
    vintages,metadata=fetch_archives()
    holdout=make_holdout_rows(vintages)
    doc=diagnose(vintages,metadata,holdout)
    body=json.dumps(doc,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    print("GEO2027_UCDP_VINTAGE_REVISIONS_BEGIN")
    print(body,end="")
    print("GEO2027_UCDP_VINTAGE_REVISIONS_END")
    if args.check_report and Path(args.check_report).read_bytes()!=body.encode("utf8"):
        raise ValueError("Frozen UCDP vintage revision audit changed")


if __name__=="__main__":
    main()
