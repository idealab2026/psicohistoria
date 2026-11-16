#!/usr/bin/env python3
"""Explain the historical Indonesian GEO H2 vintage-ranking revision exactly.

Decompose the 2022-origin UCDP 23.1->24.1/25.1/26.1 two-step Markov
probability change into Indonesian transition-count revisions and all other
country transition-count revisions with a two-factor Shapley identity.
These are algebraic source-replay effects, NOT causal or prospective effects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from backtest_archived_country_vintages import SOURCES, fetch_archives
from decompose_geo2028_origin2026_update import nstep
from diagnose_geo2028_historical_forecast_vintage_drift import (
    _fit_at_origin, _verify_records,
)
from prepare_geo2027_transition_alerts import SOURCE_SHA256, FORECAST_PATH

ROOT = Path(__file__).resolve().parents[1]
VINTAGE = ROOT / "data/geo2028-historical-forecast-vintage-drift.json"
ALERT_STUDY = ROOT / "data/geo2027-historical-alert-vintage-overlap.json"
ALERTS = ROOT / "data/forecast-2027-transition-alerts.json"
REPORT = ROOT / "data/geo2027-indonesia-vintage-revision-attribution.json"
ALERT_SHA256 = "309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb"
COUNTRIES = {850: "Indonesia", 703: "Kyrgyzstan"}
ORIGIN = 2022
COMPARISONS = ("24.1", "25.1", "26.1")
LAPLACE = 1
PRIOR = 20
TOL = 2e-10


def sha(data):
    return hashlib.sha256(data).hexdigest()


def counts(history, cutoff):
    """Count observed consecutive Markov transitions, <= cutoff only."""
    clipped = {year: value for year, value in history.items() if year <= cutoff}
    if any(type(year) is not int or type(value) is not int or
           value not in (0, 1) for year, value in clipped.items()):
        raise ValueError("Invalid historical state")
    matrix = [[0, 0], [0, 0]]
    for year in sorted(clipped):
        if year > 1989 and year - 1 in clipped:
            matrix[clipped[year - 1]][clipped[year]] += 1
    return matrix


def subtract(all_counts, local):
    other = [[all_counts[i][j] - local[i][j] for j in range(2)]
             for i in range(2)]
    if any(value < 0 for row in other for value in row):
        raise ValueError("Country transition exceeds global transitions")
    return other


def model_probability(origin_state, local, other):
    """The originally preregistered country-shrinkage Markov H2 equation."""
    if origin_state not in (0, 1):
        raise ValueError("Invalid origin state")
    if any(type(x) is not int or x < 0 for matrix in (local, other)
           for row in matrix for x in row):
        raise ValueError("Negative/non-integer transitions")
    total = [[local[i][j] + other[i][j] for j in range(2)]
             for i in range(2)]
    global_q = [(total[i][1] + LAPLACE) /
                (sum(total[i]) + 2 * LAPLACE) for i in range(2)]
    local_q = [(local[i][1] + PRIOR * global_q[i]) /
               (sum(local[i]) + PRIOR) for i in range(2)]
    probability = nstep(origin_state, local_q, 2)
    if not 0 < probability < 1 or not math.isfinite(probability):
        raise ValueError("Invalid Markov probability")
    return probability, global_q, local_q


def shapley_revision(state, old_local, revised_local, old_other, revised_other):
    """Exact 2-factor split. Local factor includes its own global-rate effect."""
    p00, g00, q00 = model_probability(state, old_local, old_other)
    p10, _, _ = model_probability(state, revised_local, old_other)
    p01, _, _ = model_probability(state, old_local, revised_other)
    p11, g11, q11 = model_probability(state, revised_local, revised_other)
    own = ((p10 - p00) + (p11 - p01)) / 2
    rest = ((p01 - p00) + (p11 - p10)) / 2
    interaction = p11 - p10 - p01 + p00
    if abs((own + rest) - (p11 - p00)) > TOL:
        raise AssertionError("Shapley attribution does not telescope")
    return {
        "original_probability": round(p00, 12),
        "later_probability": round(p11, 12),
        "probability_change_pp": round((p11 - p00) * 100, 9),
        "own_historical_transitions_shapley_pp": round(own * 100, 9),
        "all_other_countries_transitions_shapley_pp": round(rest * 100, 9),
        "interaction_before_equal_shapley_split_pp": round(interaction * 100, 9),
        "global_q_original": [round(v, 12) for v in g00],
        "global_q_later": [round(v, 12) for v in g11],
        "country_q_original": [round(v, 12) for v in q00],
        "country_q_later": [round(v, 12) for v in q11],
        "counterfactual_p_local_revised_only": round(p10, 12),
        "counterfactual_p_other_countries_revised_only": round(p01, 12),
    }


def compare(old_records, new_records, old_metadata, new_metadata, cid,
            old_fit, revised_fit, origin=ORIGIN):
    old_hist = old_records[cid]
    later_hist = new_records[cid]
    if origin not in old_hist or origin not in later_hist:
        raise ValueError("Country lacks source origin label")
    if old_hist[origin] != later_hist[origin]:
        raise ValueError("Source origin classification changed; isolate separately")
    old_local, new_local = counts(old_hist, origin), counts(later_hist, origin)
    old_global = old_metadata["global_transition_counts"]
    new_global = new_metadata["global_transition_counts"]
    old_other = subtract(old_global, old_local)
    new_other = subtract(new_global, new_local)
    result = shapley_revision(old_hist[origin], old_local, new_local,
                              old_other, new_other)
    if (abs(result["original_probability"] -
            old_fit[cid]["p_model_h2"]) > TOL or
        abs(result["later_probability"] -
            revised_fit[cid]["p_model_h2"]) > TOL):
        raise AssertionError("Attribution fails source-model original/revision match")
    changed = []
    missing = []
    for year in sorted(set(old_hist) | set(later_hist)):
        if year > origin:
            continue
        a, b = old_hist.get(year), later_hist.get(year)
        if a is None or b is None:
            missing.append(year)
        elif a != b:
            changed.append({"year": year, "original_state": a, "revised_state": b})
    result.update({
        "country_id": cid, "country": COUNTRIES[cid],
        "origin_year": origin, "origin_state": old_hist[origin],
        "changed_historical_binary_years": changed,
        "historical_missing_years_between_vintages": missing,
        "old_country_transition_counts": old_local,
        "revised_country_transition_counts": new_local,
        "old_other_countries_transition_counts": old_other,
        "revised_other_countries_transition_counts": new_other,
        "no_post_origin_training_labels_used": True,
        "two_factor_split_is_algebraic_not_causal": True,
    })
    return result


def study(vintages, metadata, issued_revisions, historical_alerts):
    _verify_records(vintages, metadata)
    if issued_revisions.get("schema") != (
        "idealab.psico.geo_historical_fixed_origin_vintage_probability_drift.v1"
    ) or issued_revisions.get("prospective_2027_2028_skill_demonstrated") is not False:
        raise ValueError("Referenced historical vintage report changed")
    if historical_alerts.get("schema") != (
        "idealab.psico.geo2027_historical_topk_vintage_overlap.v1"
    ) or historical_alerts.get("n_2027_outcomes_resolved") != 0:
        raise ValueError("Referenced original alert comparison changed")
    old, oldmeta = _fit_at_origin(vintages["23.1"], ORIGIN)
    pairs = []
    for version in COMPARISONS:
        revised, newmeta = _fit_at_origin(vintages[version], ORIGIN,
                                         fixed_cohort=list(old))
        rows = {str(cid): compare(
            vintages["23.1"], vintages[version], oldmeta, newmeta,
            cid, old, revised) for cid in COUNTRIES}
        history_row = next(x for x in issued_revisions["historical_comparisons"]
                           if x["origin_year_fixed"] == ORIGIN
                           and x["original_edition"] == "23.1"
                           and x["later_revision_edition"] == version)
        hist_h2 = next(x for x in history_row["horizons"]
                       if x["horizon_years"] == 2)
        for cid in COUNTRIES:
            known = next((v for v in hist_h2["largest_ten_named_probability_revisions"]
                          if v["country_id"] == cid), None)
            if known:
                if (abs(rows[str(cid)]["original_probability"] -
                        known["original_p"]) > TOL or
                    abs(rows[str(cid)]["later_probability"] -
                        known["revised_p"]) > TOL):
                    raise AssertionError("Previous frozen report contradicted")
        prior = next(x for x in historical_alerts["paired_comparisons"]
                     if x["fixed_origin_year"] == ORIGIN
                     and x["original_UCDP_version"] == "23.1"
                     and x["revised_UCDP_version"] == version)
        exits = prior["groups"]["1"]["deterministic_exited"]
        enters = prior["groups"]["1"]["deterministic_entered"]
        pairs.append({
            "comparison": f"23.1->{version}",
            "origin_year": ORIGIN,
            "global_transition_original": oldmeta["global_transition_counts"],
            "global_transition_revised": newmeta["global_transition_counts"],
            "indonesia_exits_historical_resolution_top5":
                any(x["country_id"] == 850 for x in exits),
            "kyrgyzstan_enters_historical_resolution_top5":
                any(x["country_id"] == 703 for x in enters),
            "countries": rows,
        })
    return {
        "schema": "idealab.psico.geo2027_indonesia_vintage_source_attribution.v1",
        "status": "EX_POST_FIXED_ORIGIN_REPLAY_NOT_ISSUED_FORECAST",
        "source_shas": {v: SOURCES[v]["sha256"] for v in ("23.1", *COMPARISONS)},
        "original_2027_forecast_sha256": SOURCE_SHA256,
        "original_2027_transition_alerts_sha256": ALERT_SHA256,
        "origin_year_fixed": ORIGIN,
        "horizon_years": 2,
        "shapley_factors": [
            "Indonesia_or_Kyrgyzstan_country_historical_transition_counts",
            "all_other_countries_historical_transition_counts",
        ],
        "same_2022_origin_state_in_all_comparisons": True,
        "counterfactual_sources_are_hypothetical_hybrids_not_UCDP_releases": True,
        "comparisons": pairs,
        "historical_forecasts_actually_issued": False,
        "outcomes_2027_resolved": 0,
        "prospective_prediction_skill_demonstrated": False,
        "no_frozen_forecast_or_alert_modified": True,
        "country_history_and_global_history_components_are_not_causal": True,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-report", action="store_true")
    args = ap.parse_args()
    if (sha(FORECAST_PATH.read_bytes()) != SOURCE_SHA256 or
            sha(ALERTS.read_bytes()) != ALERT_SHA256):
        raise ValueError("Frozen issued GEO2027 forecast or alert SHA mismatch")
    vintage = json.loads(VINTAGE.read_text(encoding="utf8"))
    original_alert = json.loads(ALERT_STUDY.read_text(encoding="utf8"))
    vintages, metadata = fetch_archives()
    report = study(vintages, metadata, vintage, original_alert)
    payload = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    print("GEO2027_INDONESIA_SOURCE_ATTRIBUTION_BEGIN")
    print(payload, end="")
    print("GEO2027_INDONESIA_SOURCE_ATTRIBUTION_END")
    if args.check_report:
        if REPORT.read_bytes() != payload.encode("utf8"):
            raise ValueError("Source-backed Indonesia attribution differs from committed report")


if __name__ == "__main__":
    main()
