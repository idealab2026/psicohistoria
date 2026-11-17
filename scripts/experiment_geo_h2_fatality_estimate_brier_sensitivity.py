#!/usr/bin/env python3
"""Ex-post GEO H2 Brier sensitivity to three UCDP fatality estimates.

Recompute (not issue) the exact original binary H2 and fixed four-state H2
historical predictions from origin-only archived releases. Evaluate 2024/2025
target labels from distinct official target releases using low/best/high with
zero tuning. UCDP named estimates may be nonmonotonic. Sharp extrema describe
finite-cohort label sensitivity, not confidence intervals or prospective skill.
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
from backtest_archived_country_vintages import FOLDS, SOURCES
from diagnose_geo2028_historical_forecast_vintage_drift import _fit_at_origin
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD, VERSION_ORDER, counts_to_binary,
    four_state_forecast, parse_counts,
)
from prepare_geo2027_transition_alerts import (
    FORECAST_PATH, SOURCE_SHA256,
)
from probe_ucdp_organized_vintages import request

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data/geo2027-h2-fatality-estimate-brier-sensitivity.json"
INTENSITY_REFERENCE = ROOT / "data/geo2027-intensity-markov-cross-release.json"
ORIGINAL_REFERENCE = ROOT / "data/forecast-2027-archival-cross-release.json"
VINTAGE_REFERENCE = ROOT / "data/geo2027-ucdp-fatality-vintage-intervals.json"
FORECAST_FIELDS = ("p_original_binary", "p_intensity_markov")
SCENARIOS = ("low", "best", "high")
N = 196
EPS = 1e-12


def _delta(p_alt, p_original, y):
    return (p_alt - y) ** 2 - (p_original - y) ** 2


def _sign(value):
    return "four_state_lower_brier" if value < -EPS else (
        "original_binary_lower_brier" if value > EPS else "numerically_tied"
    )


def summarize(rows):
    """Preserve the 3 global scenarios and sharp independent-label envelope.

    The sharp envelope allows only a binary state realized by at least one
    of the three explicitly coded UCDP estimates for each country-year.
    It makes NO claim that these independent extremes form a realizable
    conflict scenario or 95% interval. Clustered/correlated data are not IID.
    """
    if not rows:
        raise ValueError("No country-year cases to evaluate")
    ids = [(r["target_year"], r["country_id"]) for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Repeated target year/GWNO evaluation row")
    accum = {
        tag: {name: {"brier": 0.0, "logloss": 0.0}
              for name in FORECAST_FIELDS}
        for tag in SCENARIOS
    }
    positives = {tag: 0 for tag in SCENARIOS}
    lower = upper = 0.0
    changed = {tag: [] for tag in ("low", "high")}
    ambiguous = []
    nonmonotonic = []
    by_case = []
    for r in rows:
        triple = r["official_fatalities_estimates"]
        label = classify(triple)
        p, q = (r["p_original_binary"], r["p_intensity_markov"])
        if any(type(x) not in (int, float) or not math.isfinite(x)
               or not 0 < x < 1 for x in (p, q)):
            raise ValueError("Non-finite or invalid frozen historical probability")
        if not triple[0] <= triple[1] <= triple[2]:
            nonmonotonic.append([r["target_year"], r["country_id"]])
        if min(label) != max(label):
            ambiguous.append([r["target_year"], r["country_id"]])
        for name, index in (("low", 0), ("high", 2)):
            if label[index] != label[1]:
                changed[name].append([r["target_year"], r["country_id"]])
        d0, d1 = _delta(q, p, 0), _delta(q, p, 1)
        lo, hi = (min(d0, d1), max(d0, d1)) if min(label) != max(label) else (
            (d0, d0) if label[0] == 0 else (d1, d1))
        lower += lo
        upper += hi
        by_case.append({
            "target_year": r["target_year"],
            "country_id": r["country_id"],
            "deaths_low_best_high": list(triple),
            "active_low_best_high": list(label),
            "p_original_binary": p,
            "p_intensity_four_state": q,
            "delta_brier_low": d1 if label[0] else d0,
            "delta_brier_best": d1 if label[1] else d0,
            "delta_brier_high": d1 if label[2] else d0,
            "sharp_case_min_delta": lo,
            "sharp_case_max_delta": hi,
        })
        for tag, y in zip(SCENARIOS, label):
            positives[tag] += y
            for field in FORECAST_FIELDS:
                probability = r[field]
                accum[tag][field]["brier"] += (probability - y) ** 2
                accum[tag][field]["logloss"] -= (
                    y * math.log(probability) + (1-y) * math.log1p(-probability))
    n = len(rows)
    results = {}
    for tag in SCENARIOS:
        original = {metric: accum[tag]["p_original_binary"][metric] / n
                    for metric in ("brier", "logloss")}
        alt = {metric: accum[tag]["p_intensity_markov"][metric] / n
               for metric in ("brier", "logloss")}
        d_brier = alt["brier"] - original["brier"]
        d_logloss = alt["logloss"] - original["logloss"]
        results[tag] = {
            "positives": positives[tag],
            "original_binary": original,
            "four_state_intensity": alt,
            "four_state_minus_original_delta_brier": d_brier,
            "four_state_minus_original_delta_logloss": d_logloss,
            "lower_brier_in_this_scenario": _sign(d_brier),
        }
    band = {
        "sharp_finite_cohort_lower_delta_brier": lower/n,
        "sharp_finite_cohort_upper_delta_brier": upper/n,
        "zero_excluded_by_algebraic_envelope":
            lower/n > EPS or upper/n < -EPS,
        "same_model_lower_brier_for_every_consistent_binary_label_assignment":
            _sign(lower/n) if lower/n > EPS else (
                _sign(upper/n) if upper/n < -EPS else "not_identified"),
        "not_a_statistical_confidence_or_prediction_interval": True,
        "country_year_label_independence_not_assumed": True,
        "country_year_envelope_extremes_not_asserted_jointly_feasible": True,
    }
    for scenario in results.values():
        d = scenario["four_state_minus_original_delta_brier"]
        if not lower/n - 1e-11 <= d <= upper/n + 1e-11:
            raise AssertionError("A named-label scenario escaped algebraic envelope")
    return {
        "n": n,
        "scenarios": results,
        "sharp_label_ambiguity_envelope": band,
        "ambiguous_country_years": sorted(ambiguous),
        "ambiguous_country_year_n": len(ambiguous),
        "low_vs_best_changed_country_years": sorted(changed["low"]),
        "high_vs_best_changed_country_years": sorted(changed["high"]),
        "nonmonotonic_named_death_estimate_country_years": sorted(nonmonotonic),
        "ambiguous_country_year_contributions": sorted(
            (r for r in by_case
             if min(r["active_low_best_high"]) != max(r["active_low_best_high"])),
            key=lambda x: (x["target_year"], x["country_id"])),
        "top_ten_absolute_best_brier_difference_contributions": sorted(
            by_case, key=lambda x: (-abs(x["delta_brier_best"]),
                                    x["target_year"], x["country_id"]))[:10],
    }


def _assert_scores_frozen(rows, fold, intensity_ref, original_ref):
    """Require best-based replay to equal both independently pinned reports."""
    got = summarize(rows)["scenarios"]["best"]
    historical = next(item for item in intensity_ref["cohorts"]
                      if item["origin_year"] == fold["origin_year"]
                      and item["target_year"] == fold["target_year"])
    baseline = next(item for item in original_ref["folds"]
                    if item["origin_cutoff"] == fold["origin_year"]
                    and item["origin_version"] == fold["origin_release"]
                    and item["outcome_version"] == fold["target_release"])
    if got["positives"] != historical["metrics"]["positives"] or (
        got["positives"] != baseline["positives"]
    ):
        raise AssertionError("Best outcome count differs from frozen historical reports")
    for model, ref in (("original_binary", historical["metrics"]["original_binary"]),
                       ("four_state_intensity", historical["metrics"]["intensity_four_state"])):
        for metric in ("brier", "logloss"):
            if abs(got[model][metric] - ref[metric]) > 1e-10:
                raise AssertionError("Best-label replay diverged from frozen " + model)
    for metric in ("brier", "logloss"):
        if abs(got["original_binary"][metric] - baseline["scores"]["p_model"][metric]) > 1e-10:
            raise AssertionError("Original frozen binary Markov baseline mismatch")
    return True


def replay(counts, panels, issue, intensity_ref, original_ref, vintage_ref):
    """Train exclusively in origin archive, score only separate target archive."""
    if (set(counts) != set(VERSION_ORDER) or
        set(panels) != set(VERSION_ORDER) or
        issue.get("official_2027_outcomes_resolved") != 0 or
        intensity_ref.get("schema") !=
            "idealab.psico.geo2027_four_state_intensity_cross_release.v1" or
        intensity_ref.get("prospective_skill_demonstrated") is not False or
        original_ref.get("schema") !=
            "idealab.psico.statebased_archival_cross_release_v1" or
        original_ref.get("historical_forecasts_actually_issued") is not False or
        vintage_ref.get("schema") !=
            "idealab.psico.geo2027_ucdp_fatality_interval_historical_vintages.v1" or
        vintage_ref.get("2027_official_outcomes_observed") != 0):
        raise ValueError("Exactly four archived sources and all immutable reports required")
    ids = sorted(x["country_id"] for x in issue["countries"])
    if len(ids) != N or len(set(ids)) != N:
        raise ValueError("Frozen GEO2027 riskset is no longer 196 GWNOs")
    if vintage_ref["official_UCDP_source_sha256"] != {
        v: SOURCES[v]["sha256"] for v in VERSION_ORDER
    }:
        raise ValueError("Historical UCDP source SHA reference changed")
    for v in VERSION_ORDER:
        if sum(len(h) for h in counts[v].values()) != {
            "23.1":6544, "24.1":6740, "25.1":6936, "26.1":7132
        }[v]:
            raise ValueError("Original UCDP source row counts changed")
    folds = []
    pooled_rows = []
    for fold in FOLDS:
        src, target = fold["origin_release"], fold["target_release"]
        origin, year = fold["origin_year"], fold["target_year"]
        if (SOURCES[src]["last_year"] != origin or
            SOURCES[target]["last_year"] != year or year - origin != 2):
            raise ValueError("Origin/target edition year mixup")
        binary, meta = _fit_at_origin(counts_to_binary(counts[src]), origin)
        intensity, intensity_meta = four_state_forecast(counts[src], origin)
        if (meta["last_training_year"] != origin or
            intensity_meta["cutoff_max"] != origin or
            set(binary) != set(ids) or set(intensity) != set(ids)):
            raise ValueError("Forecast training leakage or fixed country riskset mismatch")
        rows = []
        target_snapshot = next(
            item for item in vintage_ref["recent_2022_2025_countrywise_snapshots"][target]
            if item["year"] == year)
        for cid in ids:
            if (cid, year) not in panels[target]:
                raise ValueError("Absent official target country-year; cannot impute zero")
            triple = panels[target][(cid, year)]
            if triple[1] != counts[target].get(cid, {}).get(year):
                raise ValueError("Reconstructed UCDP best label and official source disagree")
            rows.append({
                "country_id": cid, "target_year": year,
                "official_fatalities_estimates": triple,
                "p_original_binary": binary[cid]["p_model_h2"],
                "p_intensity_markov": intensity[cid]["p_intensity_markov"],
            })
        aggregate = summarize(rows)
        _assert_scores_frozen(rows, fold, intensity_ref, original_ref)
        for k in SCENARIOS:
            if aggregate["scenarios"][k]["positives"] != target_snapshot["active_"+k+"_n"]:
                raise AssertionError("Target labels disagree with separately pinned historical audit")
        if (aggregate["ambiguous_country_year_n"] !=
            target_snapshot["ambiguous_threshold_n"] or
            [cid for y,cid in aggregate["ambiguous_country_years"]] !=
            target_snapshot["ambiguous_GWNO"]):
            raise AssertionError("Target ambiguous GWNOs differ from prior official audit")
        folds.append({
            "origin_year": origin,
            "origin_edition": src,
            "target_year": year,
            "target_edition": target,
            "n": N,
            "forecast_origin_training_data_only": True,
            "origin_binary_last_training_year": meta["last_training_year"],
            "origin_intensity_last_training_year": intensity_meta["cutoff_max"],
            "prior_best_brier_scores_reproduced_exactly": True,
            "evaluation": aggregate,
        })
        pooled_rows.extend(rows)
    if len(pooled_rows) != 392:
        raise AssertionError("Two distinct full 196-GWNO year blocks expected")
    pooled = summarize(pooled_rows)
    original_metric = intensity_ref["pooled"]
    for model, ref in (("original_binary", original_metric["original_binary"]),
                       ("four_state_intensity", original_metric["intensity_four_state"])):
        for metric in ("brier", "logloss"):
            if abs(pooled["scenarios"]["best"][model][metric] - ref[metric]) > 1e-10:
                raise AssertionError("Pooled frozen baseline score not reproduced")
    if pooled["scenarios"]["best"]["positives"] != 69:
        raise AssertionError("Original exact 69/392 best labels not reproduced")
    return {
        "schema": "idealab.psico.geo_h2_crossrelease_fatality_label_sensitivity.v1",
        "status": "EX_POST_SOURCE_SEPARATED_REPLAY_MEASUREMENT_ONLY_NOT_ISSUED_PREDICTIONS",
        "original_GEO2027_issued_sha256": SOURCE_SHA256,
        "source_archives_sha256": {
            version: SOURCES[version]["sha256"] for version in VERSION_ORDER},
        "frozen_fourstate_reference": "data/geo2027-intensity-markov-cross-release.json",
        "frozen_historical_reference": "data/forecast-2027-archival-cross-release.json",
        "previous_54_panel_source_audit": "data/geo2027-ucdp-fatality-vintage-intervals.json",
        "historical_origin_target_pairs_n": 2,
        "horizon_years": 2,
        "original_frozen_196_GWNO": True,
        "same_origin_issued_model_replayed_for_all_outcome_estimates": True,
        "two_target_years_not_independent": True,
        "shared_countries_not_independent": True,
        "no_outcome_based_hyperparameter_selection": True,
        "best_is_the_only_preregistered_primary_label": True,
        "low_best_high_are_named_estimates_not_confidence_limits": True,
        "no_2027_outcomes_observed": True,
        "no_2027_probabilities_or_alerts_reissued": True,
        "historical_predictions_issued_at_origin": False,
        "prospective_skill_demonstrated": False,
        "folds": folds,
        "pooled": pooled,
        "limitations": (
            "Ex-post four-source backtest; 2022/2023 forecast origins were not "
            "independently timestamp-notarized before their 2024/2025 outcomes. "
            "Only two overlapping annual blocks, not an IID confidence "
            "sample. Best is the preregistered GEO target; low/high are "
            "measurement perturbations. Algebraic extrema across ambiguous "
            "GWNOs are not confidence intervals, feasible simultaneous "
            "political configurations, or proof of prospective predictive skill."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-report", action="store_true")
    parser.add_argument("--print-report", action="store_true")
    args = parser.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Frozen 2027 original probability vector changed")
    audit_issued(ISSUE.read_bytes(), MANIFEST.read_bytes(), ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(), OLD_MANIFEST.read_bytes(),
                 ALERTS.read_bytes())
    raw = {v: request(SOURCES[v]["url"], MAX_DOWNLOAD) for v in VERSION_ORDER}
    counts = {v: parse_counts(raw[v], v) for v in VERSION_ORDER}
    panels = {v: read_verified_intervals(raw[v], v) for v in VERSION_ORDER}
    refs = [json.loads(p.read_text(encoding="utf-8"))
            for p in (ISSUE, INTENSITY_REFERENCE, ORIGINAL_REFERENCE,
                      VINTAGE_REFERENCE)]
    report = replay(counts, panels, *refs)
    encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    print("GEO_H2_FATALITY_BRIER_SENSITIVITY_BEGIN")
    print(encoded if args.print_report else
          json.dumps({
              "schema": report["schema"],
              "pooled": report["pooled"]["scenarios"],
              "pooled_ambiguity": report["pooled"]["ambiguous_country_years"],
              "folds": [{
                  "origin": f["origin_year"],
                  "target": f["target_year"],
                  "scenarios": f["evaluation"]["scenarios"],
                  "ambiguous": f["evaluation"]["ambiguous_country_years"],
              } for f in report["folds"]],
          }, indent=2, sort_keys=True))
    print("GEO_H2_FATALITY_BRIER_SENSITIVITY_END")
    if args.check_report and REPORT.read_bytes() != encoded.encode("utf-8"):
        raise ValueError("Four-archive measurement Brier report is not byte identical")


if __name__ == "__main__":
    main()
