#!/usr/bin/env python3
"""Issue candidate for a SEPARATE, prospective shadow of issued GEO-2027.

The original 196 forecast probabilities and 15 issued alert positions remain
untouched. The two pre-existing 2012-19 fitted log-odds intercepts are applied
to the 2027 probabilities from the SHA-pinned original public issue.
The model-choice was inspired by already-inspected later historical labels:
future-target prospective, but NO independent confirmatory model selection.
No observation from 2026 or 2027 is loaded.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from experiment_geo2027_temporal_calibration import logistic_shift
from prepare_geo2027_transition_alerts import (
    FORECAST_PATH, MANIFEST_PATH, SOURCE_SHA256, verify_source, sha,
)

REPORT_PATH = Path("data/geo2027-temporal-calibration-ablation.json")
ALERT_PATH = Path("data/forecast-2027-transition-alerts.json")
SHADOW_PATH = Path("data/forecast-2027-geo-shadow.json")
SHADOW_ID = "PSICO-GEO2027-STATEBASED25-CALIBRATED-SHADOW-V1"
SHADOW_SCHEMA = "idealab.psico.geo2027_calibrated_shadow_issued_candidate.v1"
ORIGINAL_FIRST_COMMIT = "3bb3561c8d6182c30624591276c705fb76ce99dc"
ORIGINAL_ALERT_FIRST_COMMIT = "5938db3c93661ce04ed35902b2bdaa68abfb8daa"
TRAIN_YEARS = list(range(2012, 2020))
VALIDATION_YEARS = list(range(2020, 2024))
CROSS_YEARS = [2024, 2025]
EXPECTED_ALPHA = {0: -0.2921540997775962, 1: -0.7367471232834963}
EXPECTED_TRANSITIONS = {0: 51, 1: 34}
EXPECTED_COUNTS = {0: 162, 1: 34}
COUNTRY_COUNT = 196


def authenticated_inputs(original_raw, original_manifest, calibration_raw,
                         alerts_raw):
    original, rows = verify_source(original_raw, original_manifest)
    if original_manifest["first_public_forecast_commit"] != ORIGINAL_FIRST_COMMIT:
        raise ValueError("Original forecast first public commit changed")
    report = json.loads(calibration_raw)
    if (report.get("schema") != "idealab.psico.geo2027_posthoc_intercept_calibration_split.v1"
        or report.get("status") != "EXPLORATORY_POSTHOC_TEMPORAL_SPLIT_NOT_ASOF"
        or report.get("train_years_revised_26_1") != TRAIN_YEARS
        or report.get("validation_years_revised_26_1") != VALIDATION_YEARS
        or report.get("external_label_years_source_separated") != CROSS_YEARS
        or report.get("prospective_2027_results_observed") != 0
        or report.get("prospective_2027_forecast_modified") is not False
        or report.get("external_holdout_confirmatory") is not False):
        raise ValueError("Previously published calibration provenance changed")
    alphas = {}
    for state in (0, 1):
        rec = report["per_known_origin_state"][str(state)]
        alpha = rec["alpha_log_odds_shift_estimated_from_2012_2019_only"]
        train = rec["train_revised_2012_2019"]
        if (rec["origin_state"] != state or type(alpha) is not float
            or not math.isfinite(alpha) or abs(alpha-EXPECTED_ALPHA[state]) > 1e-13
            or train["observed_transitions"] != EXPECTED_TRANSITIONS[state]
            or abs(train["odds_intercept_calibrated"]["expected_events"] -
                   EXPECTED_TRANSITIONS[state]) > 1e-7):
            raise ValueError("Frozen training-only intercept is different")
        alphas[state] = alpha
    alerts = json.loads(alerts_raw)
    if (alerts.get("cohort_id") != "PSICO-GEO2027-TRANSITION-ALERTS-V1"
        or alerts.get("2027_outcomes_resolved") != 0
        or alerts.get("target_year") != 2027
        or alerts.get("source_forecast_sha256") != SOURCE_SHA256
        or alerts["risk_groups"]["0"]["budget"] != 10
        or alerts["risk_groups"]["1"]["budget"] != 5):
        raise ValueError("Issued original top-15 alert cohort changed")
    ids = [a["country_id"] for state in (0, 1) for a in
           alerts["risk_groups"][str(state)]["selected_countries"]]
    if len(ids) != 15 or len(set(ids)) != 15 or any(
        cid not in {row["country_id"] for row in rows} for cid in ids
    ):
        raise ValueError("Original alerts not safely present in full cohort")
    if len(rows) != COUNTRY_COUNT:
        raise ValueError("Canonical country cohort incomplete")
    return original, rows, alphas, alerts


def construct(original_raw, original_manifest, calibration_raw, alerts_raw,
              generator_raw):
    original, rows, alphas, alerts = authenticated_inputs(
        original_raw, original_manifest, calibration_raw, alerts_raw)
    result = []
    for row in rows:
        state = row["last_observed_state_2025"]
        p0 = row["p_model"]
        old_transition = p0 if state == 0 else 1-p0
        q = logistic_shift(old_transition, alphas[state])
        pshadow = q if state == 0 else 1-q
        q_rounded = round(q, 12)
        p_rounded = round(pshadow, 12)
        if not (0 < q_rounded < 1 and 0 < p_rounded < 1):
            raise ValueError("Shadow probability not strictly between 0 and 1")
        result.append({
            "country_id": row["country_id"],
            "country": row["country"],
            "origin_state_2025": state,
            "original_issued_p_active_2027": p0,
            "shadow_p_active_2027": p_rounded,
            "shadow_p_transition_2027": q_rounded,
        })
    if len(result) != COUNTRY_COUNT or len({r["country_id"] for r in result}) != COUNTRY_COUNT:
        raise ValueError("Shadow output omitted or duplicated country ID")
    # Strict monotone map in each original risk set. No reordering is claimed.
    for state in (0, 1):
        group = [x for x in result if x["origin_state_2025"] == state]
        if len(group) != EXPECTED_COUNTS[state]:
            raise ValueError("Wrong number of country-risk entries")
        original_order = sorted(group, key=lambda x: (
            -(x["original_issued_p_active_2027"] if state == 0 else
              1-x["original_issued_p_active_2027"]), x["country_id"]
        ))
        new_order = sorted(group, key=lambda x: (
            -x["shadow_p_transition_2027"], x["country_id"]
        ))
        if [x["country_id"] for x in original_order] != [x["country_id"] for x in new_order]:
            raise ValueError("Monotone intercept unexpectedly changed ranking")
    selected = {state: alerts["risk_groups"][str(state)]["selected_countries"]
                for state in (0, 1)}
    shadow_by_id = {r["country_id"]: r for r in result}
    alert_totals = {str(state): {
        "fixed_issued_alert_budget": len(selected[state]),
        "expected_hits_shadow": sum(shadow_by_id[a["country_id"]][
            "shadow_p_transition_2027"] for a in selected[state]),
        "expected_hits_original": alerts["risk_groups"][str(state)][
            "model_expected_hits_in_selected_alerts"],
        "alert_selection_changed": False,
    } for state in (0, 1)}
    return {
        "schema": SHADOW_SCHEMA,
        "forecast_id": SHADOW_ID,
        "status": "PREPARED_FOR_FIRST_PUBLIC_SHADOW_COMMIT",
        "original_forecast_id": original["forecast_id"],
        "original_issued_forecast_sha256": SOURCE_SHA256,
        "original_forecast_first_public_commit": ORIGINAL_FIRST_COMMIT,
        "original_15_alerts_first_public_commit": ORIGINAL_ALERT_FIRST_COMMIT,
        "original_15_alerts_sha256": sha(alerts_raw),
        "calibration_report_sha256": sha(calibration_raw),
        "generator_sha256": sha(generator_raw),
        "observed_source_last_year": 2025,
        "target_year": 2027,
        "horizon_years": 2,
        "n_countries": COUNTRY_COUNT,
        "n_initially_inactive": EXPECTED_COUNTS[0],
        "n_initially_active": EXPECTED_COUNTS[1],
        "target_rule": "UCDP OrganizedViolenceCY statebased deaths >=25 in 2027",
        "training_only_calibration_intercepts_log_odds": {
            str(k): alphas[k] for k in (0, 1)
        },
        "calibration_train_years_revised_26_1": TRAIN_YEARS,
        "posthoc_development_and_evaluation_labels_already_seen":
            VALIDATION_YEARS + CROSS_YEARS,
        "design_posthoc_not_independently_confirmatory": True,
        "original_forecast_altered": False,
        "original_alerts_altered": False,
        "2027_outcomes_resolved": 0,
        "prospective_predictive_skill_demonstrated": False,
        "future_evaluation_rule": {
            "eligible_country_ids": "identical 196 original issued country IDs",
            "resolution_source": "first official complete UCDP OrganizedViolenceCY country-year release for 2027",
            "missing_policy": "ANY missing original country-year blocks score publication until full 196-country labels resolved",
            "primary_endpoint": "paired Brier difference shadow minus ORIGINAL issued country Markov across all original 196",
            "secondary_endpoint": "paired log-loss difference shadow minus ORIGINAL issued model",
            "origin_state_diagnostics": "paired Brier/log-loss separately for 2025 state 0 and 1, no hypothesis substitution",
            "other_comparator": "original issued global Markov, secondary only",
            "model_swap_allowed": False,
            "retrospective_score_can_substitute_for_2027": False,
        },
        "original_alert_ranks_unchanged": True,
        "original_15_alert_expected_hits": alert_totals,
        "countries": result,
        "limits": "Secondary future-target shadow selected AFTER inspecting historical validation errors. Its future results can be scored against frozen original but model selection is not confirmatory, and historical dates not independently timestamp-notarized. Not a declaration of new conflicts or peace.",
    }


def canonical(doc):
    return (json.dumps(doc,sort_keys=True,ensure_ascii=False,separators=(",",":"))+"\n").encode("utf8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--print-canonical",action="store_true")
    args = ap.parse_args()
    doc = construct(
        FORECAST_PATH.read_bytes(),
        json.loads(MANIFEST_PATH.read_text(encoding="utf8")),
        REPORT_PATH.read_bytes(),
        ALERT_PATH.read_bytes(),
        Path(__file__).read_bytes(),
    )
    out = canonical(doc)
    Path(args.output).write_bytes(out)
    print("GEO2027_SHADOW_CANDIDATE",
          sha(out), "countries", doc["n_countries"],
          "2027_outcomes", doc["2027_outcomes_resolved"],
          "source_unchanged", not doc["original_forecast_altered"])
    if args.print_canonical:
        print("GEO2027_SHADOW_CANONICAL_BEGIN")
        print(out.decode("utf8"), end="")
        print("GEO2027_SHADOW_CANONICAL_END")


if __name__=="__main__":
    main()
