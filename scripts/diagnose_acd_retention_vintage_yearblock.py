#!/usr/bin/env python3
"""Sensitivity of FOUR historical ACD persistence folds to later SOURCE labels.

Same pinned origin records, exact same 3 preexisting origin-trained models and
origin-active country IDs as the frozen #62 study. Outcome label in target year
is re-extracted from LATER OFFICIAL EDITIONS. This is not recalibration.
Plus leave-one-target-year-out exact deterministic stress (four years only).
No p-values, independent-block inference, claims of prospective skill, or
GEO2027 25-death threshold changes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from backtest_ucdp_prio_retention_four_vintages import (
    PAIRS, compare_pair, diagnose, load_sources, predict,
)
from evaluate_geo2027_calibrated_shadow_official import load_authenticated
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256, sha

BASELINE = Path("data/ucdp-prio-2021-2024-retention-four-vintage.json")
FROZEN_REPORT = Path("data/ucdp-prio-retention-vintage-yearblock-robustness.json")
MODELS = ("p_global_recent5", "p_country_eb", "p_lag1_group")
LAST_YEAR_BY_VERSION = {
    "20.1": 2019, "21.1": 2020, "22.1": 2021,
    "23.1": 2022, "24.1": 2023, "25.1": 2024,
}
TARGETS = (2021, 2022, 2023, 2024)
EPS = 1e-12


def delta(folds, challenger, reference="p_global_recent5"):
    """EXACT country-observation-weighted Brier difference, not year average."""
    if not folds:
        raise ValueError("Cannot compute Brier difference on empty fold set")
    if challenger not in MODELS or reference not in MODELS:
        raise ValueError("Unregistered ACD historical model comparator")
    n = sum(f["n_origin_active_countries"] for f in folds)
    if n <= 0:
        raise ValueError("Empty origin-active country risk sets")
    return sum(
        f["n_origin_active_countries"] *
        (f["models"][challenger]["brier"] -
         f["models"][reference]["brier"])
        for f in folds
    ) / n


def summary(folds):
    if not folds or len({f["target_year"] for f in folds}) != len(folds):
        raise ValueError("Years missing or duplicated")
    n = sum(f["n_origin_active_countries"] for f in folds)
    if not n:
        raise ValueError("Cannot summarize empty origin cohorts")
    brier = {
        model: sum(f["n_origin_active_countries"] * f["models"][model]["brier"]
                   for f in folds) / n
        for model in MODELS
    }
    losses = {
        model: sum(f["n_origin_active_countries"] * f["models"][model]["logloss"]
                   for f in folds) / n
        for model in MODELS
    }
    return {
        "target_years": [f["target_year"] for f in folds],
        "n_country_year_fold_evaluations": n,
        "n_persisted": sum(f["n_target_persistent_country_incidence"] for f in folds),
        "pooled_brier": brier,
        "pooled_logloss": losses,
        "paired_brier_country_eb_minus_global_recent5":
            delta(folds,"p_country_eb"),
        "paired_brier_lag1_minus_global_recent5":
            delta(folds,"p_lag1_group"),
        "paired_brier_lag1_minus_country_eb":
            delta(folds,"p_lag1_group","p_country_eb"),
        "brier_winner_descriptive": min(MODELS,key=lambda model:(brier[model],model)),
        "not_an_independent_test_or_selected_prospective_model": True,
    }


def leave_one_target_year_out(folds):
    if (len(folds) != len(TARGETS) or
        tuple(f["target_year"] for f in folds) != TARGETS):
        raise ValueError("Fixed four-year ACD outcome cohort changed")
    return [
        {
            "withheld_target_year": withheld,
            "three_year_pooled": summary(
                [f for f in folds if f["target_year"] != withheld]),
            "no_model_retraining_or_hyperparameter_tuning": True,
            "not_an_independent_year_test": True,
        }
        for withheld in TARGETS
    ]


def later_editions(year, primary_version):
    if year not in TARGETS or LAST_YEAR_BY_VERSION[primary_version] != year:
        raise ValueError("Original target-year edition no longer matches cutoff")
    return tuple(v for v in LAST_YEAR_BY_VERSION
                 if LAST_YEAR_BY_VERSION[v] > year)


def validate_baseline(versions,meta,frozen):
    if not isinstance(frozen,dict):
        raise ValueError("Missing source-frozen historical ACD baseline")
    authentic = diagnose(versions,meta)
    if authentic != frozen:
        raise ValueError("Original issued #62 historical report changed")
    if (frozen["status"]!="SHA_PINNED_EX_POST_FOUR_ORIGIN_TARGET_VINTAGES"
        or frozen["n_country_year_fold_evaluations"]!=137
        or frozen["n_country_year_persistence_positives"]!=116
        or frozen["target_years"]!=list(TARGETS)
        or not frozen["all_sources_sha_pinned"]
        or frozen["2027_outcomes_observed"]!=0):
        raise ValueError("Wrong original archived ACD retrospective outcome set")
    return authentic


def evaluate(versions,meta,frozen):
    original=validate_baseline(versions,meta,frozen)
    primary = original["folds"]
    revisions=[]
    revised_latest=[]
    for i,(orig_version,primary_version,origin_year,target_year) in enumerate(PAIRS):
        base=primary[i]
        origin_active=versions[orig_version]
        cohort=sorted(cid for cid,y in origin_active if y==origin_year)
        baseline_target=versions[primary_version]
        original_labels={cid:int((cid,target_year) in baseline_target)
                         for cid in cohort}
        if (len(cohort)!=base["n_origin_active_countries"] or
            sum(original_labels.values())!=base["n_target_persistent_country_incidence"]):
            raise ValueError("Country-level original ACD target identity changed")
        checks=[]
        for later_version in later_editions(target_year,primary_version):
            later_active=versions[later_version]
            candidate=compare_pair(
                origin_active,later_active,origin_year,target_year)
            # The SAME origin-only predictions are used by compare_pair:
            # outcomes are solely presence/absence in the later target release.
            later_labels={cid:int((cid,target_year) in later_active)
                          for cid in cohort}
            gained=sum(original_labels[cid]==0 and later_labels[cid]==1
                       for cid in cohort)
            removed=sum(original_labels[cid]==1 and later_labels[cid]==0
                        for cid in cohort)
            if (candidate["n_origin_active_countries"]!=len(cohort)
                or candidate["n_target_persistent_country_incidence"]!=
                    sum(later_labels.values())
                or any(abs(candidate["models"][m]["sum_model_expected_persisted"]-
                           base["models"][m]["sum_model_expected_persisted"])>EPS
                       for m in MODELS)):
                raise ValueError("Historical predictions or origin risk set changed")
            checks.append({
                "revised_label_edition":later_version,
                "n_source_version_reclassified_origin_country_outcomes":
                    gained+removed,
                "newly_recorded_conflicts_in_target_year":gained,
                "no_longer_recorded_conflicts_in_target_year":removed,
                "n_origin_countries_kept_fixed":len(cohort),
                "n_persisted_from_later_ed":sum(later_labels.values()),
                "delta_brier_later_minus_first_by_model":{
                    model:candidate["models"][model]["brier"]-
                          base["models"][model]["brier"]
                    for model in MODELS
                },
                "delta_brier_lag1_minus_global_after_revision":
                    candidate["delta_brier_lag1_group_minus_global_recent5"],
                "first_release_original_probabilities_unchanged":True,
                "later_release_used_for_training":False,
            })
        latest_version=checks[-1]["revised_label_edition"] if checks else None
        latest_fold=(compare_pair(origin_active,versions[latest_version],
                                  origin_year,target_year)
                     if latest_version else base)
        revised_latest.append(latest_fold)
        revisions.append({
            "origin_version":orig_version,
            "first_target_version":primary_version,
            "target_year":target_year,
            "n_origin_countries":len(cohort),
            "n_first_release_persisted":sum(original_labels.values()),
            "later_revisions":checks,
            "latest_known_label_edition":latest_version or primary_version,
            "no_later_release_available":not bool(checks),
            "later_target_outcome_injected_into_origin_fit":False,
        })
    if any(x["no_later_release_available"]!=(x["target_year"]==2024)
           for x in revisions):
        raise ValueError("Misstated extent of available later UCDP editions")
    primary_s=summary(primary)
    latest_s=summary(revised_latest)
    if (primary_s["n_country_year_fold_evaluations"]!=137 or
        latest_s["n_country_year_fold_evaluations"]!=137 or
        primary_s["n_persisted"]!=116):
        raise ValueError("Combined retrospective source episode was modified")
    for name in MODELS:
        if abs(primary_s["pooled_brier"][name]-
               frozen["pooled_models"][name]["pooled_brier"])>EPS:
            raise ValueError("Published original Brier benchmark does not reproduce")
    jackknife_primary=leave_one_target_year_out(primary)
    jackknife_later=leave_one_target_year_out(revised_latest)
    return {
        "schema":"idealab.psico.acd_retention_target_vintage_and_yearblock_sensitivity.v1",
        "status":"EX_POST_ORIGIN_FIXED_TARGET_VINTAGE_SENSITIVITY_NO_NEW_2027_LABELS",
        "2027_outcomes_observed":0,
        "frozen_acd_original_4fold_report_reproduced":True,
        "four_original_2021_2024_target_years":list(TARGETS),
        "n_pooled_origin_active_country_year_evaluations":137,
        "no_full_country_year_inactive_denominator_invented":True,
        "target":(
            "ACD intrastate 3/4 conflict incidence in t+2 among countries "
            "with recorded intrastate conflict in t, NOT GEO >=25 deaths"),
        "not_geo2027_or_newconf_endpoint":True,
        "source_sha256_by_version":frozen["source_sha256_by_version"],
        "revisions_by_target_year_and_later_edition":revisions,
        "primary_first_target_vintage_pooled":primary_s,
        "latest_later_target_vintage_pooled_descriptive_only":latest_s,
        "leave_one_year_out_first_vintage":jackknife_primary,
        "leave_one_year_out_latest_later_vintage":jackknife_later,
        "n_distinct_target_years":4,
        "countries_reappear_across_years":True,
        "historically_independently_issued_probabilities":False,
        "historical_source_release_dates_independently_notarized":False,
        "model_hyperparameters_tuned_against_results":False,
        "selection_after_other_historical_outcomes_previously_seen":True,
        "statistical_significance_or_dependence_estimated":False,
        "original_geo2027_shadow_alerts_newconf_changed":False,
        "limitations":(
            "This is an exploratory ex-post comparison of the same original "
            "origin-only ACD models under increasingly revised target labels, "
            "not independent prospective validation. Four adjacent target "
            "years and recurrent countries do not create independent years "
            "or countries; leave-one-target-year-out stress uses no new "
            "validation data and is NOT a cross-validation estimator. "
            "Later target vintage 25.1 is only available for years <=2024; "
            "2024 has no later source in this experiment. ACD does not "
            "provide an inactive-denominator for all GEO countries. No "
            "probabilities or released 2027 alerts were modified."
        ),
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--check-report")
    args=p.parse_args()
    original,shadow,_=load_authenticated()
    if (len(original["countries"])!=196 or len(shadow["countries"])!=196
        or shadow["2027_outcomes_resolved"]!=0
        or sha(FORECAST_PATH.read_bytes())!=SOURCE_SHA256):
        raise ValueError("Prospective GEO2027 issues must remain untouched")
    versions,meta=load_sources()
    frozen=json.loads(BASELINE.read_text(encoding="utf8"))
    report=evaluate(versions,meta,frozen)
    body=json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    print("ACD_RETENTION_VINTAGE_YEARBLOCK_BEGIN")
    print(body,end="")
    print("ACD_RETENTION_VINTAGE_YEARBLOCK_END")
    if args.check_report and FROZEN_REPORT.read_bytes()!=body.encode("utf8"):
        raise ValueError("Retrospective ACD source-vintage/year-block report changed")


if __name__=="__main__":
    main()
