#!/usr/bin/env python3
"""GEO H2 long rolling historical diagnostics, not ex-ante forecast validation.

Twelve H2 target years 2014..2025, same 196 original GWNO countries.
Model training masks >origin observations. These source editions 23.1/24.1
WERE PUBLISHED YEARS AFTER MANY SIMULATED ORIGINS/OUTCOMES; masking does NOT
undo later backfill and measurement revision in earlier observations.
Therefore this is ex-post rolling *diagnostics*, not prospective out-of-sample
evidence. Both model hyperparameters remain identical to the prior H2 study.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit as audit_issued,
)
from audit_geo2027_ucdp_fatality_vintages import (
    classify, read_verified_intervals,
)
from backtest_archived_country_vintages import SOURCES
from diagnose_geo2028_historical_forecast_vintage_drift import _fit_at_origin
from experiment_geo_h2_fatality_estimate_brier_sensitivity import summarize
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD, VERSION_ORDER, EXPECTED_ROWS, counts_to_binary,
    four_state_forecast, parse_counts,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data/geo-h2-rolling-historical-2014-2025.json"
REFERENCE_2FOLD = ROOT / "data/geo2027-h2-fatality-estimate-brier-sensitivity.json"
ORIGINAL_BACKTEST = ROOT / "data/geo2027-intensity-markov-cross-release.json"
SOURCE_AUDIT = ROOT / "data/geo2027-ucdp-fatality-vintage-intervals.json"
ISSUE_N = 196
HORIZON = 2
ORIGINS = tuple(range(2012, 2024))
TARGETS = tuple(range(2014, 2026))
N = len(ORIGINS) * ISSUE_N
YEARS_EARLY = tuple(range(2014, 2020))
YEARS_LATE = tuple(range(2020, 2026))
EPS = 1e-10


def fold_specs(track):
    """Select each outcome calendar year once, never pool overlapping vintages."""
    if track == "fixed_first_vintage_then_latest":
        return [
            {
                "origin_year": origin,
                "target_year": origin + HORIZON,
                "origin_release": "23.1" if origin <= 2022 else "24.1",
                "outcome_release": "25.1" if origin <= 2022 else "26.1",
            }
            for origin in ORIGINS
        ]
    if track == "later_vintage_stress":
        return [{
            "origin_year": origin, "target_year": origin + HORIZON,
            "origin_release": "24.1", "outcome_release": "26.1",
        } for origin in ORIGINS]
    raise ValueError("Historical audit track is not predeclared")


def _proper_score(p, y):
    if not (type(p) in (float, int) and math.isfinite(p) and 0 < p < 1
            and y in (0, 1) and type(y) is int):
        raise ValueError("Invalid probability or label for proper score")
    return (p-y)**2, -(y*math.log(p)+(1-y)*math.log1p(-p))


def _baseline_scores(rows):
    result = {}
    for estimator, position in (("low", 0), ("best", 1), ("high", 2)):
        for key, field in (
            ("global_markov_h2", "p_global_markov"),
            ("global_prevalence_5y", "p_baseline_global_5y"),
        ):
            vals = [_proper_score(r[field], classify(r["official_fatalities_estimates"])[position])
                    for r in rows]
            result.setdefault(estimator, {})[key] = {
                "brier": sum(x[0] for x in vals)/len(vals),
                "logloss": sum(x[1] for x in vals)/len(vals),
            }
    return result


def _build_fold(spec, counts, panels, ids):
    origin = spec["origin_year"]
    year = spec["target_year"]
    src = spec["origin_release"]
    target = spec["outcome_release"]
    if (year != origin + HORIZON or
        origin not in ORIGINS or
        SOURCES[src]["last_year"] < origin or
        SOURCES[target]["last_year"] < year or
        src == target):
        raise ValueError("Invalid archived origin/outcome cutoffs")
    binary, bmeta = _fit_at_origin(counts_to_binary(counts[src]), origin,
                                   fixed_cohort=ids)
    four, fmeta = four_state_forecast(
        counts[src], origin, historical_rolling_diagnostic=True)
    if (bmeta["last_training_year"] != origin or
        fmeta["cutoff_max"] != origin or
        set(binary) != set(ids) or set(four) != set(ids)):
        raise ValueError("Model contains post-origin training or changed GWNO cohort")
    rows = []
    for cid in ids:
        triple = panels[target].get((cid, year))
        if triple is None:
            raise ValueError("Missing target UCDP row cannot be imputed 0")
        if triple[1] != counts[target].get(cid, {}).get(year):
            raise ValueError("Target best deaths disagree with official SHA-pinned source")
        if four[cid]["origin_state"] != binary[cid]["origin_state"]:
            raise AssertionError("Four-state and binary origin label differ")
        rows.append({
            "country_id": cid,
            "target_year": year,
            "official_fatalities_estimates": triple,
            "p_original_binary": binary[cid]["p_model_h2"],
            "p_intensity_markov": four[cid]["p_intensity_markov"],
            "p_global_markov": binary[cid]["p_global_markov_h2"],
            "p_baseline_global_5y": binary[cid]["p_baseline_global_5y"],
            "origin_active": binary[cid]["origin_state"],
        })
    return rows, {
        "origin_year": origin, "target_year": year,
        "origin_release": src, "outcome_release": target,
        "last_training_year": bmeta["last_training_year"],
        "four_state_last_training_year": fmeta["cutoff_max"],
        "country_n": ISSUE_N,
        "forecast_probabilities_unchanged_across_three_outcome_definitions": True,
        "archive_at_origin_was_not_actually_published_at_historical_origin": True,
    }


def _summarize_track(specs, counts, panels, ids, anchor, source_audit):
    all_rows = []
    folds = []
    for spec in specs:
        rows, meta = _build_fold(spec, counts, panels, ids)
        target = spec["outcome_release"]
        year = spec["target_year"]
        snap = next(item for item in source_audit[
            "all_historical_year_edition_snapshots"][target]
            if item["year"] == year)
        result = summarize(rows)
        for name in ("low", "best", "high"):
            if result["scenarios"][name]["positives"] != snap["active_" + name + "_n"]:
                raise AssertionError("Official source vintage threshold counts disagree")
        if result["ambiguous_country_year_n"] != snap["ambiguous_threshold_n"]:
            raise AssertionError("Official source ambiguity count differs from source audit")
        if (spec["origin_year"] == 2022 and target == "25.1" and
            spec["origin_release"] == "23.1") or (
            spec["origin_year"] == 2023 and target == "26.1" and
            spec["origin_release"] == "24.1"):
            frozen = next(x for x in anchor["folds"]
                          if x["origin_year"] == spec["origin_year"])
            if (frozen["origin_edition"] != spec["origin_release"] or
                frozen["target_edition"] != target):
                raise AssertionError("Registered 2024/2025 historical fold changed")
            for name in ("low", "best", "high"):
                for model in ("original_binary", "four_state_intensity"):
                    for metric in ("brier", "logloss"):
                        now = result["scenarios"][name][model][metric]
                        previously = frozen["evaluation"]["scenarios"][name][model][metric]
                        if abs(now - previously) > EPS:
                            raise AssertionError("Frozen two-fold historical forecast replay differs")
        meta.update({
            "comparison": result,
            "baseline_scores": _baseline_scores(rows),
        })
        folds.append(meta)
        all_rows.extend(rows)
    if sorted(x["target_year"] for x in folds) != list(TARGETS):
        raise ValueError("Missing or duplicated historical target years")
    if len(all_rows) != N or len(set((r["target_year"],r["country_id"])
                                     for r in all_rows)) != N:
        raise ValueError("Historical balanced 196x12 panel has missing or duplicate rows")
    summary = summarize(all_rows)
    baselines = _baseline_scores(all_rows)
    eras = []
    for era, years in (("2014_2019", YEARS_EARLY), ("2020_2025", YEARS_LATE)):
        selected = [r for r in all_rows if r["target_year"] in years]
        eras.append({
            "era": era, "year_n": len(years), "country_year_n": len(selected),
            "model_comparison": summarize(selected),
            "baseline_scores": _baseline_scores(selected),
        })
    return {
        "year_n": len(specs), "observations": N,
        "mean_of_twelve_annual_scores_not_IID": True,
        "folds": folds, "pooled": summary,
        "pooled_baseline_scores": baselines,
        "predefined_noncausal_year_groups": eras,
    }, all_rows


def _compare_tracks(primary_rows, later_rows):
    before = {(r["target_year"], r["country_id"]): r for r in primary_rows}
    after = {(r["target_year"], r["country_id"]): r for r in later_rows}
    if set(before) != set(after) or len(before) != N:
        raise ValueError("Vintage comparison has mismatched country/year cohort")
    differences = []
    counts = {"origin_binary_changed":0,"outcome_best_label_changed":0,
              "either_markov_probability_changed":0}
    annual = {}
    for year, cid in sorted(before):
        a, b = before[(year, cid)], after[(year, cid)]
        old_label = classify(a["official_fatalities_estimates"])[1]
        new_label = classify(b["official_fatalities_estimates"])[1]
        p_change = abs(a["p_original_binary"] - b["p_original_binary"])
        q_change = abs(a["p_intensity_markov"] - b["p_intensity_markov"])
        changed = (
            a["origin_active"] != b["origin_active"],
            old_label != new_label, p_change > 1e-12 or q_change > 1e-12,
        )
        for key, flag in zip(counts, changed):
            counts[key] += int(flag)
        if any(changed):
            differences.append({
                "target_year": year, "GWNO": cid,
                "origin_binary_changed": changed[0],
                "outcome_best_label_changed": changed[1],
                "abs_binary_forecast_change": p_change,
                "abs_four_state_forecast_change": q_change,
            })
        current = annual.setdefault(year, {
            "year": year, "origin_binary_changed_n":0,
            "outcome_best_label_changed_n":0,
            "either_markov_probability_changed_n":0})
        for k, flag in zip(("origin_binary_changed_n",
                            "outcome_best_label_changed_n",
                            "either_markov_probability_changed_n"), changed):
            current[k] += int(flag)
    return {
        "two_tracks_same_country_years_not_independent": True,
        "same_outcome_years_and_GWNOs": True,
        "overlapping_vintages_are_measurement_stress_not_an_extra_sample": True,
        "counts": counts,
        "annual_changed_label_and_forecast_counts": list(annual.values()),
        "largest_ten_vintage_differences": sorted(
            differences,
            key=lambda x:(-max(x["abs_binary_forecast_change"],
                                x["abs_four_state_forecast_change"]),
                          x["target_year"],x["GWNO"]))[:10],
    }


def replay(counts, panels, issue, anchor, original, source_audit):
    if (set(counts) != set(VERSION_ORDER) or
        set(panels) != set(VERSION_ORDER) or
        len(issue.get("countries",[])) != ISSUE_N or
        issue.get("official_2027_outcomes_resolved") != 0 or
        anchor.get("schema") !=
          "idealab.psico.geo_h2_crossrelease_fatality_label_sensitivity.v1" or
        anchor.get("historical_origin_target_pairs_n") != 2 or
        original.get("schema") !=
          "idealab.psico.geo2027_four_state_intensity_cross_release.v1" or
        source_audit.get("schema") !=
          "idealab.psico.geo2027_ucdp_fatality_interval_historical_vintages.v1" or
        source_audit.get("official_UCDP_source_sha256") !=
          {v:SOURCES[v]["sha256"] for v in VERSION_ORDER}):
        raise ValueError("Four official archives and exact previous reports required")
    ids = sorted(r["country_id"] for r in issue["countries"])
    if len(set(ids)) != ISSUE_N:
        raise ValueError("Duplicated frozen GWNO in original GEO forecast")
    for version in VERSION_ORDER:
        if sum(len(hist) for hist in counts[version].values()) != EXPECTED_ROWS[version]:
            raise ValueError("Source row total changed")
    primary_specs = fold_specs("fixed_first_vintage_then_latest")
    later_specs = fold_specs("later_vintage_stress")
    primary, rows_first = _summarize_track(
        primary_specs, counts, panels, ids, anchor, source_audit)
    later, rows_later = _summarize_track(
        later_specs, counts, panels, ids, anchor, source_audit)
    variance = _compare_tracks(rows_first, rows_later)
    return {
        "schema":"idealab.psico.geo_h2_rolling_historical_2014_2025.v1",
        "status":"EX_POST_ROLLING_DIAGNOSTIC_SOURCE_BACKFILLED_NOT_CONTEMPORANEOUS_PROSPECTIVE_TEST",
        "original_GEO2027_SHA256":SOURCE_SHA256,
        "source_archives_sha256":{v:SOURCES[v]["sha256"] for v in VERSION_ORDER},
        "target_years":list(TARGETS),
        "horizon_years":HORIZON,
        "fixed_original_GWNO_n":ISSUE_N,
        "unique_country_years_primary_n":N,
        "source_versions_postdate_many_simulated_forecast_origins":True,
        "historical_backfilled_training_features_can_reflect_later_editorial_revisions":True,
        "chronological_training_clip_does_not_make_the_archive_contemporaneous":True,
        "not_prospective_or_independently_timestamped_skill":True,
        "distinct_origin_target_editions_but_not_contemporaneous":True,
        "primary_frozen_2027_probabilities_changed":False,
        "outcome_2027_labels_resolved":0,
        "new_prospective_probabilities_issued":0,
        "predefined_parameters_only_not_tuned_to_outcomes":True,
        "year_blocks_and_countries_are_correlated_no_IID_claim":True,
        "primary_unique_year_series":primary,
        "later_vintage_same_year_sensitivity_NOT_second_sample":later,
        "primary_vs_later_vintage_historical_revisions":variance,
        "limitations": (
            "Rolling annual holdout by chronological cutoff uses revised source "
            "editions that were published years after several simulated origins "
            "and historical outcomes; training feature revisions can leak later "
            "knowledge even if the target year itself is removed before fitting. "
            "These are historical model diagnostics, not real ex-ante forecasts, "
            "not 12 independent year shocks or 2352 IID countries. "
            "The overlap-vintage track duplicates the same country-years and is "
            "only a sensitivity control, never an increased test sample. "
            "No statistical significance, confidence intervals, causal claims, "
            "or 2027 outcomes can be asserted."
        ),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report",action="store_true")
    parser.add_argument("--print-report",action="store_true")
    args=parser.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Frozen original 2027 forecast vector modified")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    sources={v:request(SOURCES[v]["url"],MAX_DOWNLOAD) for v in VERSION_ORDER}
    counts={v:parse_counts(sources[v],v) for v in VERSION_ORDER}
    panels={v:read_verified_intervals(sources[v],v) for v in VERSION_ORDER}
    refs=[json.loads(p.read_text(encoding="utf-8")) for p in (
        ISSUE,REFERENCE_2FOLD,ORIGINAL_BACKTEST,SOURCE_AUDIT)]
    report=replay(counts,panels,*refs)
    payload=json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    if args.check_report and REPORT.read_bytes()!=payload.encode("utf-8"):
        raise ValueError("SHA-verified 12-year rolling historical report is not byte-identical")
    if args.print_report:
        print("GEO_H2_ROLLING_2014_2025_BEGIN",flush=True)
        print(payload,end="")
        print("GEO_H2_ROLLING_2014_2025_END",flush=True)
    else:
        print(json.dumps({
            "status":report["status"],
            "primary_pooled":report["primary_unique_year_series"]["pooled"]["scenarios"]["best"],
            "vintage_stress_pooled":report["later_vintage_same_year_sensitivity_NOT_second_sample"]["pooled"]["scenarios"]["best"],
            "yearly_best_deltas":[
                [f["target_year"],
                 f["comparison"]["scenarios"]["best"]["four_state_minus_original_delta_brier"]]
                for f in report["primary_unique_year_series"]["folds"]],
            "primary_observations":N,"years":len(TARGETS),
        },indent=2,sort_keys=True))


if __name__=="__main__":
    main()
