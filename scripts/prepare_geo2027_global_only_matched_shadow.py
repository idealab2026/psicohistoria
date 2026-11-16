#!/usr/bin/env python3
"""Issue DISTINCT genuinely future-facing GEO2027 matched global-only shadow.

First complete 196-country forecast commit must be SHA-pinned and treated
immutable. Reconstruct all 196 holdout-country calibrators *using UCDP 26.1
only through calendar 2025*. 2027 results are not observed. Each country
is removed from all supervised historical learning rows, from Markov global
training priors, and from its own 2025 forecast prior. Every training row
further removes its own country's transitions, matching global-only
features in fit and prediction. Target country origin state/deaths are known.

Both alpha=1 and alpha=0 are fixed BEFORE 2027 outcomes; no new 2027 alerts.
New 2027 issue is a distinct comparator, NEVER a replacement of original.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from audit_geo2027_log1p_shadow_issue import (
    ISSUE as OLD_SHADOW, MANIFEST as OLD_SHADOW_MANIFEST,
    ORIGINAL, FROZEN_ISSUE_SHA256, audit as audit_old_shadow,
)
from audit_geo2027_log1p_issued_death_stress import ALERTS, ALERT_SHA
from backtest_archived_country_vintages import SOURCES
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD, counts_to_binary, parse_counts,
)
from experiment_geo2027_log1p_nested_h2 import fit
from experiment_geo2027_log1p_inactive_attenuation_frontier import p_scaled
from experiment_geo2027_log1p_matched_global_only import (
    markov_global_only_offset, matched_training_rows,
)
from prepare_geo2027_log1p_shadow import origin_internal_rows
from prepare_geo2027_transition_alerts import SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
ISSUE=ROOT/"data/forecast-2027-global-only-matched-shadow.json"
ORIGINAL_MANIFEST=ROOT/"data/forecast-2027-manifest.json"
ID="PSICO-GEO2027-STATEBASED25-GLOBALONLY-COUNTRYBLOCK-LOG1P-SHADOW-V1"
SCHEMA="idealab.psico.geo2027_global_only_country_block_shadow.v1"
PREPARE_DATE="2026-11-16"
SOURCE_YEAR=2025
TARGET_YEAR=2027
LAM=5.0


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def transition_snapshots(binary,training_origin_years):
    """Historical, full-source Markov totals, including extra archived GWNO."""
    years=sorted(set(training_origin_years)|{SOURCE_YEAR})
    if not years or years[0]!=2010 or years[-1]!=SOURCE_YEAR:
        raise ValueError("Original through-2025 H2 training years changed")
    counts={}
    for year in years:
        if not 2010<=year<=SOURCE_YEAR:
            raise ValueError("Transition prior leaked beyond 2025")
        glob=[[0,0],[0,0]]
        locals={}
        for cid,h in binary.items():
            own=[[0,0],[0,0]]
            for y in sorted(h):
                if y>year or y-1 not in h:
                    continue
                s,t=h[y-1],h[y]
                if s not in (0,1) or t not in (0,1):
                    raise ValueError("Invalid state-based origin transition")
                own[s][t]+=1
                glob[s][t]+=1
            locals[cid]=own
        if min(sum(row) for row in glob)<100:
            raise ValueError("Too little Markov source history")
        counts[year]=(glob,locals)
    return counts


def prospective_matched_rows(training_rows,snapshots,excluded_country):
    """Every training row excludes target country AND its own transitions."""
    if type(excluded_country) is not int:
        raise ValueError("Country ID must be institutional GWNO integer")
    if (len(training_rows)<2500 or
        min(r["target_year"] for r in training_rows)!=2012 or
        max(r["target_year"] for r in training_rows)!=SOURCE_YEAR):
        raise ValueError("Insufficient official pre-2027 learning rows")
    origin_count=sum(r["country_id"]==excluded_country
                     for r in training_rows)
    if origin_count<10:
        raise ValueError("Target country missing substantial training history")
    rows=[]
    for r in training_rows:
        if r["country_id"]==excluded_country:
            continue
        if (r["origin_year"]!=r["target_year"]-2
            or r["target_year"]>SOURCE_YEAR
            or r["origin_year"]>SOURCE_YEAR-2):
            raise ValueError("Future label/Markov feature entered ridge fit")
        glob,locals=snapshots[r["origin_year"]]
        state=int(r["origin_deaths"]>=25)
        if r["country_id"]==excluded_country:
            raise AssertionError("Heldout supervision leaked")
        p=markov_global_only_offset(glob,locals,state,
                                    excluded_country,r["country_id"])
        rows.append({**r,"p_original_binary":p})
    if (len(rows)<2400 or
        max(r["target_year"] for r in rows)!=SOURCE_YEAR or
        max(r["origin_year"] for r in rows)!=SOURCE_YEAR-2 or
        len(rows)+origin_count!=len(training_rows) or
        any(r["country_id"]==excluded_country for r in rows)):
        raise ValueError("Incomplete or contaminated country-heldout training")
    return rows,origin_count


def build(source_raw,original_raw,original_manifest_raw,shadow_raw,
          shadow_manifest_raw,alerts_raw):
    if sha(source_raw)!=SOURCES["26.1"]["sha256"]:
        raise ValueError("Official 26.1 source changed")
    if sha(original_raw)!=SOURCE_SHA256 or sha(alerts_raw)!=ALERT_SHA:
        raise ValueError("Frozen original GEO forecast or 15 alert source changed")
    audit_old_shadow(shadow_raw,shadow_manifest_raw,original_raw)
    original=json.loads(original_raw)
    manifest=json.loads(original_manifest_raw)
    oldshadow=json.loads(shadow_raw)
    if (manifest.get("forecast_sha256")!=SOURCE_SHA256 or
        manifest.get("outcomes_resolved")!=0 or
        manifest.get("target_year")!=TARGET_YEAR or
        oldshadow.get("outcomes_2027_resolved")!=0 or
        oldshadow.get("training",{}).get("final_train_targets")!=[2012,2025]):
        raise ValueError("Original GEO or LOG1P prospective source contract changed")
    countries={x["country_id"]:x for x in original["countries"]}
    oldrows={x["country_id"]:x for x in oldshadow["countries"]}
    if (len(countries)!=196 or set(countries)!=set(oldrows)
        or len({x["country_id"] for x in oldshadow["countries"]})!=196):
        raise ValueError("Original full 196-country risk universe changed")

    history=parse_counts(source_raw,"26.1")
    binary=counts_to_binary(history)
    raw_rows=origin_internal_rows(history)
    if (len(raw_rows)<2700 or
        len({r["country_id"] for r in raw_rows})<196):
        raise ValueError("Historical source or inner rows incomplete")
    snapshots=transition_snapshots(binary, (r["origin_year"] for r in raw_rows))
    if (len(snapshots)!=15 or
        sorted(snapshots)!=list(range(2010,2024))+[2025]):
        raise AssertionError("Historical feature snapshot set changed")
    glob_2025,locals_2025=snapshots[SOURCE_YEAR]

    issued=[]
    fitted=[]
    for cid in sorted(countries):
        a=countries[cid];old=oldrows[cid]
        h=history.get(cid,{})
        if SOURCE_YEAR not in h or SOURCE_YEAR not in binary[cid]:
            raise ValueError("2025 country source missing; do not impute zero")
        d=h[SOURCE_YEAR];state=int(d>=25)
        if (a["last_observed_state_2025"]!=state or
            old["origin_binary_state_2025"]!=state or
            a["p_model"]!=old["original_2027_p_active"] or
            a["country"]!=old["country"] or
            old["origin_deaths_best_2025"]!=d):
            raise ValueError("Origin state/deaths or original forecast mismatch")

        matched,removed=prospective_matched_rows(raw_rows,snapshots,cid)
        beta=fit(matched,LAM)
        if len(beta)!=3 or any(not math.isfinite(v) for v in beta):
            raise ValueError("Invalid country-block LOG1P fit")
        off=markov_global_only_offset(glob_2025,locals_2025,state,cid)
        alpha0=round(p_scaled(off,d,beta,0.0),12)
        alpha1=round(p_scaled(off,d,beta,1.0),12)
        if not all(0<p<1 for p in (off,alpha0,alpha1)):
            raise ValueError("Prospective global-only probability invalid")
        if (d==0 or d>=25) and abs(alpha0-alpha1)>1e-11:
            raise AssertionError("Alpha variants should only differ for origin deaths 1-24")
        issued.append({
            "country_id":cid,"country":a["country"],
            "origin_deaths_best_2025":d,
            "origin_binary_state_2025":state,
            "original_GEO2027_p_active_frozen":a["p_model"],
            "original_LOG1P2027_p_active_frozen":
                old["log1p_shadow_p_active_2027"],
            "original_intercept_control_p_active_frozen":
                old["intercept_only_control_p_active_2027"],
            "global_only_markov_H2_p_active":off,
            "global_only_alpha0_p_active_2027":alpha0,
            "global_only_alpha1_p_active_2027":alpha1,
            "country_blocked_logistic_beta":[round(x,12) for x in beta],
            "country_supervised_training_rows_withheld":removed,
            "training_rows_after_country_withheld":len(matched),
        })
        fitted.append(beta)
    if (len(issued)!=196 or
        [r["country_id"] for r in issued]!=sorted(countries) or
        len(set(r["country_id"] for r in issued))!=196):
        raise ValueError("Not a complete fixed prospective country cohort")
    if not any(1<=r["origin_deaths_best_2025"]<=24 for r in issued):
        raise ValueError("No subthreshold countries to distinguish alpha variants")
    return {
        "schema":SCHEMA,
        "forecast_id":ID,
        "status":"ISSUED_PROSPECTIVE_UNRESOLVED",
        "issue_class":"DISTINCT_PROSPECTIVE_2027_FULL196_COUNTRYBLOCKED_GLOBALONLY_RESEARCH_COMPARATOR",
        "preparation_calendar_date":PREPARE_DATE,
        "publication_time_authority":"FIRST_COMPLETE_PUBLIC_GITHUB_COMMIT_ONLY_NOT_INDEPENDENT_NOTARY",
        "source":{"dataset":"UCDP OrganizedViolenceCY",
                  "edition":"26.1",
                  "source_archive_sha256":SOURCES["26.1"]["sha256"],
                  "last_observed_year":SOURCE_YEAR},
        "target":{"year":TARGET_YEAR,"forecast_origin_year":SOURCE_YEAR,
                  "horizon_years":2,
                  "binary_outcome":"UCDP OrganizedViolenceCY country-year sb_total_deaths_best >=25",
                  "all_196_GWNO_fixed_identical_to_original_issue":True,
                  "official_2027_labels_missing_are_not_zero":True,
                  "final_scoring_requires_all_196_2027_labels":True},
        "method":{
            "Markov":"Two-state globally pooled country-LOO transition prior, Laplace 1, two annual steps, no national transition shrinkage",
            "LOG1P":"Logistic logit offset + intercept + inactive and active log1p fatality features",
            "ridge_lambda_fixed_from_prior_exploratory_work":LAM,
            "training_target_years":[2012,2025],
            "training_feature_origin_years":[2010,2023],
            "country_models_fitted":196,
            "each_forecast_country_all_supervised_historical_rows_excluded":True,
            "each_training_row_prior_excludes_forecast_country":True,
            "each_training_row_prior_excludes_its_own_source_country":True,
            "each_evaluation_prior_excludes_its_own_country":True,
            "each_evaluation_uses_2025_country_state_and_deaths":True,
            "no_2026_or_2027_label_or_transition_used":True,
            "two_published_alpha_variants":[0.0,1.0],
            "alpha0_inactive_intensity_slope_multiplier":0.0,
            "alpha1_inactive_intensity_slope_multiplier":1.0,
            "alpha_variants_identical_for_zero_and_active_origin_counts":True,
            "historical_model_and_lambda_selection_already_explored":True,
        },
        "prior_frozen_original_geo_sha256":SOURCE_SHA256,
        "prior_frozen_log1p_shadow_sha256":FROZEN_ISSUE_SHA256,
        "prior_frozen_15_alerts_sha256":ALERT_SHA,
        "training":{"historical_supervised_rows_before_country_exclusion":
                        len(raw_rows),
                    "historical_supervised_positives":sum(
                        r["outcome"] for r in raw_rows),
                    "country_block_models":len(fitted),
                    "min_country_training_rows":min(
                        r["training_rows_after_country_withheld"]
                        for r in issued),
                    "max_country_training_rows":max(
                        r["training_rows_after_country_withheld"]
                        for r in issued),
                    "latest_training_outcome_year":SOURCE_YEAR,
                    "latest_training_feature_origin_year":SOURCE_YEAR-2},
        "expected_active_countries_sum_probabilities":{
            "original_GEO":round(sum(r["original_GEO2027_p_active_frozen"]
                                      for r in issued),10),
            "original_LOG1P":round(sum(
                r["original_LOG1P2027_p_active_frozen"] for r in issued),10),
            "global_only_alpha0":round(sum(
                r["global_only_alpha0_p_active_2027"] for r in issued),10),
            "global_only_alpha1":round(sum(
                r["global_only_alpha1_p_active_2027"] for r in issued),10),
        },
        "prospective_scoring_precommitment":{
            "primary_pair":"full196_Brier_global_only_alpha1_minus_frozen_original_LOG1P_shadow",
            "primary_metric":"mean_squared_error_of_196_country_probabilities",
            "secondary_pairs":[
                "Brier_global_only_alpha0_minus_global_only_alpha1",
                "Brier_global_only_alpha1_minus_original_GEO",
                "Brier_global_only_alpha0_minus_original_GEO",
                "Brier_global_only_alpha0_minus_original_LOG1P",
                "logloss_global_only_alpha1_minus_original_LOG1P",
                "logloss_global_only_alpha0_minus_global_only_alpha1",
            ],
            "primary_2027_official_UCDP_edition":"first_complete_edition_with_2027_country_year_labels_for_all_original_196_ids",
            "do_not_treat_missing_country_label_as_zero":True,
            "revisions_in_later_editions_sensitivity_only":True,
            "fixed_country_universe":196,
            "no_ex_post_threshold_or_model_selection":True,
            "report_all_candidates_and_pairs_even_if_unfavourable":True,
            "multiple_comparisons_exploratory_not_familywise_confirmatory":True,
            "no_IID_country_significance_claims":True,
            "no_2027_retraining_of_issued_probabilities":True,
            "no_new_transition_alert_list":True,
        },
        "n_countries":196,
        "countries":issued,
        "official_2027_outcomes_resolved":0,
        "demonstrated_prospective_predictive_skill":False,
        "original_GEO_or_LOG1P_or_15_alerts_modified":False,
        "new_transition_alerts_issued":False,
        "replaces_any_existing_2027_issue":False,
        "limitations":"The historical model architecture, alpha grid and fixed ridge 5 were already explored on 2017–2025 historical results; retrospective advantage does NOT constitute an untouched confirmation. This is a separate prospective 2027 full-country evaluation candidate whose probabilities are frozen before official outcome labels. Its training excludes each target country's historical labels and transitions for transfer analysis, but retains its observed 2025 state and deaths. Correlated outcomes mean no country-IID p-values. Only first complete official 2027 UCDP coverage resolves primary score, without missing-as-zero."
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report",action="store_true")
    args=parser.parse_args()
    raw=request(SOURCES["26.1"]["url"],MAX_DOWNLOAD)
    obj=build(raw,ORIGINAL.read_bytes(),ORIGINAL_MANIFEST.read_bytes(),
              OLD_SHADOW.read_bytes(),OLD_SHADOW_MANIFEST.read_bytes(),
              ALERTS.read_bytes())
    content=json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False)+"\n"
    print("GEO2027_GLOBAL_ONLY_FULL196_BEGIN")
    print(content,end="")
    print("GEO2027_GLOBAL_ONLY_FULL196_END",flush=True)
    print("GEO2027_GLOBAL_ONLY_FULL196_SHA256 "+sha(content.encode()),flush=True)
    if args.check_report and ISSUE.read_bytes()!=content.encode():
        raise ValueError("Prospective complete 196-country global-only issue diverges from frozen file")


if __name__=="__main__":
    main()
