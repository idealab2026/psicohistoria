#!/usr/bin/env python3
"""Exploratory 2023-24 NEWCONF ablation: origin-frozen 3-year ACD persistence.

Only original UCDP 23.1 Multiple Onset + 23.1 ACD are permitted for training
and feature creation. Outcomes come separately from 25.1. Hypothesis is post-hoc
to already-inspected 2023/24 outcomes, NOT independent prospective evidence.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from experiment_multiple_newconf import EXTERNAL_ORIGIN, HORIZONS, PRIOR, TRAIN_START
from experiment_multiple_newconf import ci, fold, load_multiple, metrics
from experiment_onset2_conflict_incidence import load_activity
from probe_multiple_onset_vintages import PINNED as ONSET_PINNED
from probe_ucdp_prio_incidence import PINNED_SHA as ACD_PINNED


def persistence_group(activity, country, origin):
    """Count active years in origin-2..origin, grouped 0 / 1 / 2+."""
    return min(2, sum((country, y) in activity for y in range(origin - 2, origin + 1)))


def estimate(old, activity, origin, horizon):
    if origin != EXTERNAL_ORIGIN or horizon not in HORIZONS:
        raise ValueError("Only frozen 2022 origin and horizons 1,2 are permitted")
    if not activity or max(y for _, y in activity) != 2022:
        raise ValueError("Activity must be from original ACD 23.1 through 2022")
    if not old or max(max(hist) for hist in old.values()) != 2022:
        raise ValueError("Training NEWCONF labels must end in 2022")
    cohort = {cid for cid, hist in old.items() if origin in hist}
    if len(cohort) != 196:
        raise ValueError("Incomplete source-frozen 196-country origin cohort")
    histories = {}
    for cid in cohort:
        observations = [row["newconf"] for year, row in old[cid].items()
                        if TRAIN_START <= year <= origin]
        if not observations or any(v not in (0, 1) for v in observations):
            raise ValueError("Missing or invalid historic country labels")
        histories[cid] = (sum(observations), len(observations))
    full_n = sum(n for _, n in histories.values())
    full_pos = sum(pos for pos, _ in histories.values())
    if full_n < 4000:
        raise ValueError("Insufficient source-frozen training history")
    global_prior = (full_pos + 1) / (full_n + 2)
    strata = {0: [0, 0], 1: [0, 0], 2: [0, 0]}
    for cid in sorted(cohort):
        hist = old[cid]
        for t in range(TRAIN_START, origin - horizon + 1):
            if t not in hist or t + horizon not in hist:
                continue
            target = hist[t + horizon]["newconf"]
            if target not in (0, 1):
                raise ValueError("Invalid 2-year NEWCONF target")
            g = persistence_group(activity, cid, t)
            strata[g][0] += target
            strata[g][1] += 1
    if min(n for pos, n in strata.values()) < 50:
        raise ValueError("Persistence stratum too sparse: no post-hoc pooling permitted")
    priors = {g: (pos + PRIOR * global_prior) / (n + PRIOR)
              for g, (pos, n) in strata.items()}
    candidates = {}
    for cid in sorted(cohort):
        positives, n = histories[cid]
        p = (positives + PRIOR * priors[persistence_group(activity, cid, origin)]) / (n + PRIOR)
        if not 0 < p < 1:
            raise ValueError("Invalid fitted persistence probability")
        candidates[cid] = p
    info = {
        "origin": origin, "horizon": horizon, "max_fitted_newconf_year": origin,
        "max_activity_source_year": 2022, "prior_strength": PRIOR,
        "group_definition": "0 / 1 / 2+ active years among t-2,t-1,t",
        "stratum_exposure": {str(k): n for k, (pos, n) in strata.items()},
        "stratum_events": {str(k): pos for k, (pos, n) in strata.items()},
    }
    return candidates, info


def evaluate(old, later, activity, *, with_ci=True):
    if not later or max(max(hist) for hist in later.values()) != 2024:
        raise ValueError("External labels must be Multiple Onset 25.1 through 2024")
    all_rows = []
    folds = []
    for horizon in HORIZONS:
        candidate, info = estimate(old, activity, EXTERNAL_ORIGIN, horizon)
        rows, _ = fold(old, later, activity, EXTERNAL_ORIGIN, horizon)
        for row in rows:
            row["persistence_country"] = candidate[row["country"]]
        all_rows.extend(rows)
        folds.append({
            "horizon": horizon,
            "target_year": EXTERNAL_ORIGIN + horizon,
            "n": len(rows),
            "positive_country_years": sum(row["outcome"] for row in rows),
            "brier_persistence": metrics(rows, "persistence_country")["brier"],
            "brier_binary_activity": metrics(rows, "activity_country")["brier"],
            "brier_recent5_global": metrics(rows, "global_last5")["brier"],
            "fit": info,
        })
    if len(all_rows) != 392 or sum(row["outcome"] for row in all_rows) != 3:
        raise ValueError("Original external country-year labels changed; fail closed")
    p = metrics(all_rows, "persistence_country")
    a = metrics(all_rows, "activity_country")
    g = metrics(all_rows, "global_last5")
    return {
        "schema": "idealab.psico.newconf_persistence_2023_24_exploratory.v1",
        "status": "POST_HOC_NOT_CONFIRMATORY_OR_PROSPECTIVE_SKILL",
        "source_multiple_onset_23_1_sha256": ONSET_PINNED["23.1"]["sha256"],
        "source_multiple_onset_25_1_sha256": ONSET_PINNED["25.1"]["sha256"],
        "source_activity_acd_23_1_sha256": ACD_PINNED["23.1"],
        "target": "ANY(newconf=1) UCDP Multiple Onset per GW country-year",
        "origin_year": EXTERNAL_ORIGIN,
        "cohort_n": 196,
        "evaluations": len(all_rows),
        "positive_evaluations": sum(row["outcome"] for row in all_rows),
        "candidate": "country EB shrink20 toward 0/1/2+ origin-activity-year strata",
        "benchmark": "country EB shrink20 toward binary current-activity strata",
        "brier_persistence": p["brier"],
        "brier_binary_activity": a["brier"],
        "brier_recent5_global": g["brier"],
        "logloss_persistence": p["logloss"],
        "logloss_binary_activity": a["logloss"],
        "delta_brier_persistence_minus_binary": p["brier"] - a["brier"],
        "delta_brier_persistence_minus_recent5": p["brier"] - g["brier"],
        "bootstrap_country_delta_persistence_minus_binary_95": (
            ci(all_rows, competitor="activity_country",
               candidate="persistence_country", n=1000) if with_ci else None),
        "by_horizon": folds,
        "posthoc_model_design_after_2023_2024_seen": True,
        "forecast_2027_modified": False,
        "2027_outcomes_observed": 0,
        "limitations": ("2023/24 external outcomes had already been inspected; "
            "three positives only; no claim of prospective skill; bootstrap "
            "by country misses shared shocks; vintage releases not "
            "independently notarized. No geographic region inferred."),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-report")
    args = parser.parse_args()
    old, _ = load_multiple("23.1")
    later, _ = load_multiple("25.1")
    activity, _ = load_activity("23.1")
    result = evaluate(old, later, activity)
    content = json.dumps(result, sort_keys=True, indent=2) + "\n"
    print("NEWCONF_PERSISTENCE_EXPLORATORY_BEGIN")
    print(content, end="")
    print("NEWCONF_PERSISTENCE_EXPLORATORY_END")
    if args.check_report and Path(args.check_report).read_text(encoding="utf8") != content:
        raise ValueError("Official pinned-source persistence study changed")


if __name__ == "__main__":
    main()
