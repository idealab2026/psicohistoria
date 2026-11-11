#!/usr/bin/env python3
"""Prepare a SECONDARY, future-only 2027 alert cohort from already issued GEO.

Selects ten 2025-inactive countries ranked by frozen 2027 >=25-deaths
probability and five 2025-active countries ranked by its complement. Does not
fit/recalibrate any model or read outcomes beyond 2025. The output becomes an
issued alert cohort ONLY at the first public commit with its entire content,
with a separate SHA-256 manifest and public GitHub metadata.

This is NOT a claim of geopolitical expertise, war onset or negotiated peace.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

FORECAST_PATH = Path("data/forecast-2027-ucdp261.json")
MANIFEST_PATH = Path("data/forecast-2027-manifest.json")
SOURCE_SHA256 = "5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5"
EXPECTED_MODEL_ID = "PSICO-GEO2027-STATEBASED25-V1"
ISSUE_ID = "PSICO-GEO2027-TRANSITION-ALERTS-V1"
SCHEMA = "idealab.psico.prospective_geo2027_transition_alerts.v1"
COUNTRIES = 196
ORIGIN_ACTIVE = 34
ORIGIN_INACTIVE = 162
TARGET_YEAR = 2027
BUDGETS = {0: 10, 1: 5}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_source(raw, manifest):
    if sha(raw) != SOURCE_SHA256:
        raise ValueError("Refuse modified already issued GEO2027 forecast bytes")
    if manifest.get("forecast_sha256") != SOURCE_SHA256 or (
        manifest.get("forecast_id") != EXPECTED_MODEL_ID
    ) or manifest.get("status") != "ISSUED_PROSPECTIVE_UNRESOLVED" or (
        manifest.get("outcomes_resolved") != 0
    ) or not manifest.get("first_public_forecast_commit"):
        raise ValueError("Original public forecast issuance not verified")
    data = json.loads(raw)
    if data.get("forecast_id") != EXPECTED_MODEL_ID or (
        data.get("source", {}).get("data_last_year") != 2025
    ) or data.get("target", {}).get("year") != TARGET_YEAR or (
        data.get("protocol", {}).get("horizon_years") != 2
    ):
        raise ValueError("2027 frozen original prediction protocol mismatch")
    rows = data.get("countries", [])
    if len(rows) != COUNTRIES or len({r["country_id"] for r in rows}) != COUNTRIES:
        raise ValueError("Original full 196-country future cohort changed")
    if [r["country_id"] for r in rows] != sorted(r["country_id"] for r in rows):
        raise ValueError("Original country order changed")
    for row in rows:
        if (row.get("last_observed_state_2025") not in (0, 1) or
            not isinstance(row.get("country"), str) or
            not row["country"].strip()):
            raise ValueError("Missing original 2025 state or official country name")
        for key in ("p_model", "p_global_markov", "p_baseline_global_5y"):
            p = row.get(key)
            if isinstance(p, bool) or not isinstance(p, (int, float)) or (
                not math.isfinite(p) or not 0 < p < 1):
                raise ValueError("Invalid probability in already issued forecast")
    if (sum(r["last_observed_state_2025"] for r in rows) != ORIGIN_ACTIVE or
        sum(r["last_observed_state_2025"] == 0 for r in rows) != ORIGIN_INACTIVE):
        raise ValueError("Original 2025 known-at-origin risk-set counts changed")
    return data, rows


def transition_score(row, state, key):
    p = row[key]
    return p if state == 0 else round(1.0 - p, 12)


def selection(rows, state):
    if state not in BUDGETS:
        raise ValueError("Unknown ex ante state")
    members = [r for r in rows if r["last_observed_state_2025"] == state]
    count = ORIGIN_INACTIVE if state == 0 else ORIGIN_ACTIVE
    if len(members) != count:
        raise ValueError("Incomplete fixed 2025 risk set")
    ordered = sorted(members, key=lambda r: (
        -transition_score(r, state, "p_model"), r["country_id"]
    ))
    k = BUDGETS[state]
    cutoff = transition_score(ordered[k-1], state, "p_model")
    next_score = transition_score(ordered[k], state, "p_model")
    if cutoff == next_score or any(
        transition_score(ordered[i], state, "p_model") ==
        transition_score(ordered[i+1], state, "p_model")
        for i in range(k-1)
    ):
        raise ValueError("Tied alert rank or cutoff: no arbitrary country choice")
    if cutoff < next_score:
        raise ValueError("Alert probability order inconsistent")
    alerts = []
    for rank, item in enumerate(ordered[:k], start=1):
        alerts.append({
            "rank": rank,
            "country_id": item["country_id"],
            "country": item["country"],
            "state_2025": state,
            "transition_probability_model": transition_score(item, state, "p_model"),
            "transition_probability_global_markov": transition_score(
                item, state, "p_global_markov"),
            "frozen_p_statebased_active_2027": item["p_model"],
        })
    return {
        "origin_state": state,
        "question": "entry_0_to_1" if state == 0 else "resolution_1_to_0",
        "eligible_country_count": count,
        "budget": k,
        "selected_countries": alerts,
        "selection_is_unique_no_boundary_tie": True,
        "model_expected_transitions_in_all_eligible_countries": round(
            sum(transition_score(r, state, "p_model") for r in members), 12),
        "model_expected_hits_in_selected_alerts": round(
            sum(x["transition_probability_model"] for x in alerts), 12),
        "alert_cutoff_score": cutoff,
        "next_not_selected_score": next_score,
    }


def build(raw, manifest, generator):
    original, rows = verify_source(raw, manifest)
    groups = {str(s): selection(rows, s) for s in (0, 1)}
    return {
        "schema": SCHEMA,
        "cohort_id": ISSUE_ID,
        "state": "PREPARED_FOR_FIRST_PUBLIC_COMMIT",
        "original_issued_forecast_id": EXPECTED_MODEL_ID,
        "source_forecast_sha256": SOURCE_SHA256,
        "source_first_public_forecast_commit": manifest[
            "first_public_forecast_commit"],
        "generator_sha256": sha(generator),
        "source_original_zip_sha256": original["source"]["sha256"],
        "horizon_years": 2,
        "origin_year": 2025,
        "target_year": TARGET_YEAR,
        "target_field": "UCDP OrganizedViolenceCY sb_total_deaths_best",
        "target_state_rule": "active iff official statebased deaths >=25 in target 2027",
        "scope": "GW country-year, statebased conflict threshold, not newconf/onset2 or total deaths",
        "protocol": {
            "primary_ranking": "frozen original 2027 p_model, descending for entry, ascending for resolution",
            "fixed_budget_entry": 10,
            "fixed_budget_resolution": 5,
            "tie_policy": "refuse issue if any tie within selected ranks or crossing boundary",
            "evaluation": "first complete official UCDP OrganizedViolenceCY release covering target 2027",
            "missing": "Any missing country-year remains unresolved, never assumed no transition",
            "primary_future_alert_counts": "hits among 10 entry / 5 resolution alerts, one target year",
            "conditional_random_reference": "hypergeometric exact upper tail with observed future positives in each frozen eligible group; descriptive under exchangeability",
            "multiplicity": "report both original upper tails and Holm-adjusted values across two predefined direction endpoints",
            "additional_metrics": "conditional Brier vs frozen global Markov, within-risk ROC AUC and ranking tie audit; no threshold tuning",
            "target_outcomes_observed_before_issue": 0,
            "models_retrained_or_forecast_changed": False,
        },
        "risk_groups": groups,
        "retrospective_2024_2025_outcomes_used_to_choose_alert_budget": True,
        "pre_2027_forecast_originals_unchanged": True,
        "2027_outcomes_resolved": 0,
        "demonstrated_prospective_skill": False,
        "first_public_alert_commit": "must be certified separately in issue manifest",
    }


def validate(issue):
    if (issue.get("schema") != SCHEMA or issue.get("cohort_id") != ISSUE_ID or
        issue.get("2027_outcomes_resolved") != 0 or
        issue.get("demonstrated_prospective_skill") is not False):
        raise ValueError("Invalid future-only alert cohort protocol")
    if {k: issue["risk_groups"][str(k)]["budget"] for k in (0, 1)} != BUDGETS:
        raise ValueError("Alert budget changed")
    selected = [r["country_id"] for s in (0, 1)
                for r in issue["risk_groups"][str(s)]["selected_countries"]]
    if len(selected) != sum(BUDGETS.values()) or len(set(selected)) != len(selected):
        raise ValueError("Missing/duplicated prospective alert countries")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()
    raw = FORECAST_PATH.read_bytes()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf8"))
    result = build(raw, manifest, Path(__file__).read_bytes())
    validate(result)
    body = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    Path(args.output).write_text(body, encoding="utf8")
    print("GEO2027_ALERTS_PREPARED", sha(body.encode("utf8")),
          "entry", len(result["risk_groups"]["0"]["selected_countries"]),
          "resolution", len(result["risk_groups"]["1"]["selected_countries"]),
          "outcomes_resolved", 0)
    if args.print_summary:
        print("GEO2027_ALERTS_CANDIDATE_BEGIN")
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
        print("GEO2027_ALERTS_CANDIDATE_END")


if __name__ == "__main__":
    main()
