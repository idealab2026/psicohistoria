#!/usr/bin/env python3
"""Reactivation indicator sensitivity, 2021-2026 Candidate, RETROSPECTIVE ONLY.

This does not issue forecasts. Train 2021/22/24/25, score 2026 once,
never infer that a country with no Candidate event experienced no violence.
"""
import argparse
from collections import defaultdict
import csv
from datetime import date, timedelta
import hashlib
import io
import json
import math
from pathlib import Path
import sys

from check_ucdp_candidate_asof import SourceError, ged_day
from audit_candidate_q2_q3_vintages import get_source
from audit_candidate_onset_label_stability import tie_aware_k
from experiment_candidate_30_90_holdout import universe_from_bytes

ROOT = Path(__file__).resolve().parents[1]
YEARS = (2021, 2022, 2024, 2025, 2026)
TRAIN = (2021, 2022, 2024, 2025)
HOLDOUT = 2026
THRESHOLDS = (1, 5, 10, 25)
HORIZONS = (30, 90)
UNIVERSE = ROOT / "data/forecast-2027-ucdp261.json"
FROZEN_2026 = ROOT / "data/candidate-30-90-baseline-holdout.json"
REPORT_PATH = ROOT / "data/candidate-reactivation-threshold-grid.json"
SOURCE_BASE = "https://ucdp.uu.se/downloads/candidateged/"
# These source hashes were independently frozen in earlier institutional studies.
PREVIOUS_PINS = {
    (2024, 3): "ae794cc614a56a7445cdb72be95df7681431245c6ffda4ed6f3d56d36db29b6f",
    (2024, 9): "3f9f7acea9690cd8c5150981ae85b5a9365b2ca233f2b351b680de95cd4af390",
    (2025, 3): "42465f8c081bd70e67221e216d2c0b3fae59586f1ca45561f48052a26a2910e8",
    (2025, 9): "086362d535c61d1237f0824bee8afb6459bac71ca8d02026946b715264c910be",
    (2026, 3): "a3cae550d6b806b3872aa4a12d0d47e2634ca2fc30dae385463230c659865346",
    (2026, 9): "134da9b3df08b65266802c4b662e572f396c70c92ab62297319be657540bcede",
}
MODELS = ("climatology", "state_recency", "other_violence", "combined")


def source_url(year, month):
    if year not in YEARS or month not in (3, 9):
        raise SourceError("Out-of-design Candidate source year or month")
    yy = year % 100
    return SOURCE_BASE + f"GEDEvent_v{yy:02d}_01_{yy:02d}_{month:02d}.csv"


def state_bin(deaths):
    if deaths == 0:
        return "zero"
    if deaths < 5:
        return "1-4"
    if deaths < 10:
        return "5-9"
    return "10+"


def parse_original(raw, year, month, population):
    if year not in YEARS or month not in (3, 9):
        raise SourceError("Archive incompatible with study")
    if not isinstance(raw, bytes) or not raw:
        raise SourceError("Candidate archive unavailable")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
        columns = {"id", "country_id", "type_of_violence", "date_prec",
                   "date_start", "date_end", "best"}
        if not reader.fieldnames or not columns.issubset(reader.fieldnames):
            raise SourceError("Required Candidate schema not available")
        identifiers = set()
        record_count = 0
        included = 0
        skipped = defaultdict(int)
        prior_state, prior_other = defaultdict(int), defaultdict(int)
        future30, future90 = defaultdict(int), defaultdict(int)
        q1_start, q1_end = date(year, 1, 1), date(year, 3, 31)
        target_start = date(year, 5, 1)
        end30 = target_start + timedelta(days=29)
        end90 = target_start + timedelta(days=89)
        for row in reader:
            record_count += 1
            identifier = (row.get("id") or "").strip()
            if not identifier or identifier in identifiers:
                raise SourceError("Source has duplicate or empty event ID")
            identifiers.add(identifier)
            try:
                country = int(row["country_id"])
                violence = int(row["type_of_violence"])
                date_prec = int(row["date_prec"])
                best = int(row["best"])
            except (TypeError, ValueError) as exc:
                raise SourceError("Missing or nonnumeric mandatory GED coding") from exc
            if country <= 0 or violence not in (1, 2, 3) or date_prec not in (0, 1, 2, 3, 4, 5) or best < 0:
                raise SourceError("Invalid Candidate event category or fatality")
            start = ged_day(row["date_start"], "date_start")
            end = ged_day(row["date_end"], "date_end")
            if start > end:
                raise SourceError("Event dates reversed")
            if date_prec not in (1, 2):
                skipped["low_or_unknown_date_precision"] += 1
                skipped["unknown_precision_zero"] += int(date_prec == 0)
                continue
            if country not in population:
                skipped["outside_196_countries"] += 1
                continue
            if month == 3:
                if start < q1_start or end > q1_end:
                    skipped["outside_q1_window"] += 1
                    continue
                if violence == 1:
                    prior_state[country] += best
                else:
                    prior_other[country] += best
            else:
                if violence != 1:
                    skipped["not_state_based_outcome"] += 1
                    continue
                if start < target_start or end > end90:
                    skipped["outside_target_90_window"] += 1
                    continue
                future90[country] += best
                if end <= end30:
                    future30[country] += best
            included += 1
        if record_count == 0 or included == 0:
            raise SourceError("No eligible events in Candidate original")
        meta = {
            "source_rows": record_count, "eligible_events": included,
            "exclusions": dict(sorted(skipped.items())),
            "distinct_countries_with_eligible_events":
                len({*prior_state, *prior_other, *future90}),
        }
        return meta, {"prior_state": prior_state, "prior_other": prior_other,
                      "30": future30, "90": future90}
    except UnicodeError as exc:
        raise SourceError("Candidate archive CSV cannot decode") from exc


def assemble(year, q1, q3, names):
    return [
        {"country_id": country, "country": label,
         "q1_state_best": q1["prior_state"][country],
         "q1_other_best": q1["prior_other"][country],
         "future_best_30": q3["30"][country],
         "future_best_90": q3["90"][country]}
        for country, label in names
    ]


def fits(train_rows, threshold, horizon):
    key = f"future_best_{horizon}"
    eligible = [r for r in train_rows if r["q1_state_best"] < threshold]
    if not eligible:
        raise SourceError("Empty training risk set")
    y = lambda r: int(r[key] >= threshold)
    positives = sum(y(row) for row in eligible)
    global_p = (positives + 1) / (len(eligible) + 2)
    bucket_keys = {
        "state_recency": ("zero", "1-4", "5-9", "10+"),
        "other_violence": ("False", "True"),
        "combined": tuple(f"{a}|{b}" for a in ("zero", "1-4", "5-9", "10+") for b in ("False", "True")),
    }
    groups = {kind: {v: [0, 0] for v in keys} for kind, keys in bucket_keys.items()}
    for row in eligible:
        keys = group_keys(row)
        label = y(row)
        for model, key2 in keys.items():
            groups[model][key2][0] += 1
            groups[model][key2][1] += label
    return {
        "train_n_at_risk": len(eligible), "train_positive": positives,
        "p_global": global_p, "shrinkage_k": 20,
        "groups": {
            model: {k: {"n": v[0], "positives": v[1],
                         "p": (v[1] + 20 * global_p) / (v[0] + 20)}
                    for k, v in items.items()}
            for model, items in groups.items()
        },
    }


def group_keys(row):
    state = state_bin(row["q1_state_best"])
    other = str(row["q1_other_best"] >= 1)
    return {"state_recency": state, "other_violence": other,
            "combined": state + "|" + other}


def predict(row, fitted):
    keys = group_keys(row)
    return {
        "climatology": fitted["p_global"],
        **{name: fitted["groups"][name][bucket]["p"]
           for name, bucket in keys.items()},
    }


def score(rows, model, threshold, horizon, fitted):
    eligible = [r for r in rows if r["q1_state_best"] < threshold]
    if len(eligible) < 50:
        raise SourceError("2026 risk-set size unexpectedly small")
    key = f"future_best_{horizon}"
    preds = []
    for r in eligible:
        p = predict(r, fitted)[model]
        if not 0 < p < 1:
            raise SourceError("Invalid probability after smoothing")
        preds.append({"country_id": r["country_id"],
                      "p": p, "target": int(r[key] >= threshold)})
    brier = sum((r["p"] - r["target"]) ** 2 for r in preds) / len(preds)
    log_loss = -sum(r["target"] * math.log(r["p"]) +
                    (1 - r["target"]) * math.log1p(-r["p"]) for r in preds) / len(preds)
    return {
        "n": len(preds), "positive": sum(v["target"] for v in preds),
        "brier": round(brier, 8),
        "log_loss": round(log_loss, 8),
        "mean_probability": round(sum(v["p"] for v in preds) / len(preds), 8),
        "top10_with_tie_bounds": tie_aware_k(preds, "p", 10),
    }


def build_report(fetcher=get_source, universe_raw=None, frozen=None, source_pins=None):
    raw_universe = UNIVERSE.read_bytes() if universe_raw is None else universe_raw
    names = universe_from_bytes(raw_universe)
    population = {x for x, _ in names}
    archived = json.loads(FROZEN_2026.read_text("utf8")) if frozen is None else frozen
    if archived.get("status") != "RETROSPECTIVE_ONLY_NOT_ISSUED":
        raise SourceError("Prior 2026 archive status incorrect")
    if archived.get("universe_sha256") != hashlib.sha256(raw_universe).hexdigest():
        raise SourceError("Canonical 196-country universe hash not identical to earlier study")
    pins = PREVIOUS_PINS if source_pins is None else source_pins
    sources = []
    annual = {}
    for year in YEARS:
        archive = {}
        for month in (3, 9):
            url = source_url(year, month)
            raw = fetcher(url)
            sha = hashlib.sha256(raw).hexdigest()
            if (year, month) in pins and pins[(year, month)] != sha:
                raise SourceError("Changed previously frozen UCDP Candidate original bytes")
            metadata, values = parse_original(raw, year, month, population)
            archive[month] = values
            sources.append({"year": year, "month": month,
                            "source_url": url, "sha256": sha,
                            "source_bytes": len(raw), **metadata})
        annual[year] = assemble(year, archive[3], archive[9], names)
    for row, old in zip(annual[2026], archived["retrospective_2026_country_vector"]):
        if row["country_id"] != old["country_id"] or row["q1_state_best"] != old["prior_best_q1_2026"]:
            raise SourceError("2026 Q1 prior-state data drifted from frozen study")
        for horizon in HORIZONS:
            if row[f"future_best_{horizon}"] != old[f"h{horizon}"]["target_best_q3_2026"]:
                raise SourceError("2026 Q3 outcome drifted from frozen study")
    trained = [r for year in TRAIN for r in annual[year]]
    results = {}
    yearly = {}
    all_fits = {}
    for threshold in THRESHOLDS:
        results[str(threshold)] = {}
        yearly[str(threshold)] = {}
        all_fits[str(threshold)] = {}
        for horizon in HORIZONS:
            key = str(horizon)
            scores = {}
            for year in YEARS:
                risk = [r for r in annual[year] if r["q1_state_best"] < threshold]
                positives = sum(r[f"future_best_{horizon}"] >= threshold for r in risk)
                scores[str(year)] = {
                    "at_risk": len(risk), "positive": positives,
                    "rate": round(positives / len(risk), 8) if risk else None,
                }
            yearly[str(threshold)][key] = scores
            trained_model = fits(trained, threshold, horizon)
            all_fits[str(threshold)][key] = trained_model
            results[str(threshold)][key] = {
                model: score(annual[HOLDOUT], model, threshold, horizon, trained_model)
                for model in MODELS
            }
    return {
        "schema": "idealab.psico.candidate.state_reactivation_threshold_grid.v1",
        "status": "EXPLORATORY_HISTORICAL_NOT_ASOF_NOT_ISSUED",
        "protocol_date": "2026-11-19",
        "years": list(YEARS), "train_years": list(TRAIN), "holdout_year": HOLDOUT,
        "excluded_noncomparable_year": 2023,
        "universe_sha256": hashlib.sha256(raw_universe).hexdigest(),
        "n_countries": len(names),
        "horizons_days": list(HORIZONS),
        "target_best_thresholds": list(THRESHOLDS),
        "source_snapshots": sources,
        "yearly_threshold_rates": yearly,
        "trained_models": all_fits,
        "holdout_2026_model_scores": results,
        "holdout_2026_country_observations": annual[2026],
        "historical_original_release_dates_certified": False,
        "prospective_issued_probabilities": 0,
        "prospective_outcomes_resolved": 0,
        "limitations": (
            "Retrospective source snapshots only; no independent first-publication date; "
            "thresholds fixed for this exploratory sweep after previous 2026 investigations; "
            "low thresholds count provisional coded violence, not new wars; "
            "2023 excluded as Q1 cumulative archive is Jan-Apr not Jan-Mar; "
            "one holdout year with dependent countries. Tie-aware ranking prevents "
            "country-ID order from pretending to be individual discriminatory skill."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--print-report", action="store_true")
    group.add_argument("--check-report", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = build_report()
        if args.print_report:
            print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            old = json.loads(REPORT_PATH.read_text("utf8"))
            if old != report:
                raise SourceError("Frozen report does not match original-source replay")
            print("OK: 10 original Candidate source SHA, 2026 holdout, 8 targets and tie-aware models reproduced")
    except (SourceError, OSError, ValueError, KeyError, TypeError, TimeoutError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
