#!/usr/bin/env python3
"""Retrospective UCDP Candidate 30/90-day benchmarks, NOT prospective forecasts.

Preregistered design: March cumulative input, hypothetical Apr30 origin, May1
forward exactly 30/90 days. Train 2024-25; test 2026, without tuning on test.
The original archive publication dates have NOT been independently verified.
"""
import argparse
from collections import defaultdict
from datetime import date, timedelta
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import sys

from check_ucdp_candidate_asof import SourceError, ged_day
from audit_candidate_q2_q3_vintages import get_source

ROOT = Path(__file__).resolve().parents[1]
YEARS = (2024, 2025, 2026)
SOURCE_FORECAST = ROOT / "data/forecast-2027-ucdp261.json"
REPORT = ROOT / "data/candidate-30-90-baseline-holdout.json"
Q3_PINNED_SHA = {
    2024: "3f9f7acea9690cd8c5150981ae85b5a9365b2ca233f2b351b680de95cd4af390",
    2025: "086362d535c61d1237f0824bee8afb6459bac71ca8d02026946b715264c910be",
    2026: "134da9b3df08b65266802c4b662e572f396c70c92ab62297319be657540bcede",
}


def archive_url(year, month):
    if year not in YEARS or month not in (3, 9):
        raise SourceError("Out-of-protocol archive year or month")
    yy = year % 100
    return f"https://ucdp.uu.se/downloads/candidateged/GEDEvent_v{yy:02d}_01_{yy:02d}_{month:02d}.csv"


def universe_from_bytes(raw):
    try:
        obj = json.loads(raw.decode("utf8"))
        countries = obj["countries"]
        out = [(int(c["country_id"]), str(c["country"])) for c in countries]
    except (UnicodeError, KeyError, TypeError, ValueError) as exc:
        raise SourceError("Canonical 196-country archive invalid") from exc
    if len(out) != 196 or len({x[0] for x in out}) != 196:
        raise SourceError("Universe does not exactly contain 196 unique countries")
    return out


def extract_state_based(raw, year, purpose, universe_ids):
    """Filter date and precision before country summation; archive unmodified."""
    if purpose not in ("origin", "outcome") or year not in YEARS:
        raise SourceError("Invalid extraction purpose/year")
    try:
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        necessary = {
            "id", "country_id", "type_of_violence", "date_prec",
            "date_start", "date_end", "best",
        }
        if not reader.fieldnames or not necessary.issubset(reader.fieldnames):
            raise SourceError("UCDP GED required fields missing")
        ids = set()
        source_n, excluded_boundary, excluded_date_precision = 0, 0, 0
        outside_universe, retained = 0, 0
        accepted = []
        minimum = date(year, 1, 1)
        limit = date(year, 3, 31) if purpose == "origin" else date(year, 7, 29)
        for row in reader:
            source_n += 1
            event_id = (row.get("id") or "").strip()
            if not event_id or event_id in ids:
                raise SourceError("GED duplicate/missing source event ID")
            ids.add(event_id)
            try:
                country = int(row["country_id"])
                kind = int(row["type_of_violence"])
                best = int(row["best"])
                precision = int(row["date_prec"])
            except (ValueError, TypeError) as exc:
                raise SourceError("Unparseable required GED event field") from exc
            if country <= 0 or kind not in (1, 2, 3) or best < 0 or precision not in (1, 2, 3, 4, 5):
                raise SourceError(f"Invalid GED category/death/precision in {year} {purpose}: id={event_id} country={country} type={kind} best={best} date_prec={precision}")
            start = ged_day(row["date_start"], "date_start")
            end = ged_day(row["date_end"], "date_end")
            if start > end:
                raise SourceError("Reversed GED event chronology")
            if kind != 1:
                continue
            if precision > 2:
                excluded_date_precision += 1
                continue
            if country not in universe_ids:
                outside_universe += 1
                continue
            if start < minimum or end > limit:
                excluded_boundary += 1
                continue
            retained += 1
            accepted.append((event_id, country, start, end, best))
        if source_n == 0:
            raise SourceError("Empty GED source")
        return {
            "source_rows": source_n,
            "retained_statebased_high_precision_within_outer_window": retained,
            "excluded_type1_high_precision_outside_date_window": excluded_boundary,
            "excluded_type1_low_date_precision": excluded_date_precision,
            "excluded_type1_high_precision_outside_196": outside_universe,
        }, accepted
    except UnicodeError as exc:
        raise SourceError("Unparseable UCDP CSV UTF-8") from exc


def bin_of(deaths):
    if deaths == 0:
        return "zero"
    if deaths < 25:
        return "one_to_24"
    if deaths < 100:
        return "25_to_99"
    return "100_plus"


def estimates(train, target_key):
    # Fit with 392 country-year observations (not independent IID samples).
    n = len(train)
    if n != 392:
        raise SourceError("Training must contain exactly 2024+2025 x 196")
    positive = sum(r[target_key] for r in train)
    global_probability = (positive + 1) / (n + 2)
    if not 0 < global_probability < 1:
        raise SourceError("Invalid climatology")
    grouping = {"persistence": defaultdict(list), "recent_volume": defaultdict(list)}
    for r in train:
        grouping["persistence"][str(r["prior_best"] >= 25)].append(r[target_key])
        grouping["recent_volume"][bin_of(r["prior_best"])].append(r[target_key])
    groups = {}
    for name, candidate_groups in grouping.items():
        keys = ("False", "True") if name == "persistence" else ("zero", "one_to_24", "25_to_99", "100_plus")
        groups[name] = {}
        for key in keys:
            outcomes = candidate_groups[key]
            p = (sum(outcomes) + 10 * global_probability) / (len(outcomes) + 10)
            groups[name][key] = {
                "train_n": len(outcomes),
                "train_positive": sum(outcomes),
                "p": p,
            }
    return {"global": global_probability, "train_positive": positive, "train_n": n, "groups": groups}


def predict(prior_best, trained):
    key = str(prior_best >= 25)
    volume = bin_of(prior_best)
    return {
        "global": trained["global"],
        "persistence": trained["groups"]["persistence"][key]["p"],
        "recent_volume": trained["groups"]["recent_volume"][volume]["p"],
    }


def measure(rows, probabilities, subset=None):
    selected = [r for r in rows if subset is None or subset(r)]
    if not selected:
        raise SourceError("Cannot score an empty subset")
    y = [int(r["target"]) for r in selected]
    ps = [float(probabilities[r["country_id"]]) for r in selected]
    if any(not 0 < p < 1 for p in ps):
        raise SourceError("Smoothed probabilities must be strictly inside (0,1)")
    n = len(y)
    score = {
        "n": n,
        "positives": sum(y),
        "positive_rate": round(sum(y) / n, 8),
        "p_mean": round(sum(ps) / n, 8),
        "brier": round(sum((p - true) ** 2 for p, true in zip(ps, y)) / n, 8),
        "log_loss": round(-sum(
            true * math.log(p) + (1 - true) * math.log1p(-p) for p, true in zip(ps, y)
        ) / n, 8),
    }
    ranked = sorted(selected, key=lambda r: (-probabilities[r["country_id"]], r["country_id"]))
    top = ranked[:10]
    score["true_positives_top_10"] = sum(r["target"] for r in top)
    score["precision_top_10"] = round(score["true_positives_top_10"] / len(top), 8)
    return score


def build_report(fetcher=get_source, universe_raw=None, q3_sha=Q3_PINNED_SHA):
    frozen_universe = SOURCE_FORECAST.read_bytes() if universe_raw is None else universe_raw
    canonical = universe_from_bytes(frozen_universe)
    countries = {id_ for id_, _ in canonical}
    years = {}
    sources = []
    for year in YEARS:
        quarterly = {}
        for month, purpose in ((3, "origin"), (9, "outcome")):
            url = archive_url(year, month)
            data = fetcher(url)
            sha = hashlib.sha256(data).hexdigest()
            if month == 9 and sha != q3_sha[year]:
                raise SourceError(f"Q3 source SHA changed from frozen prior audit for {year}")
            scan, events = extract_state_based(data, year, purpose, countries)
            sources.append({"year": year, "month": month, "source_url": url,
                            "source_sha256": sha, "source_bytes": len(data),
                            "audit": scan})
            quarterly[purpose] = events
        prior = defaultdict(int)
        for _, country, start, end, best in quarterly["origin"]:
            prior[country] += best
        horizons = {30: defaultdict(int), 90: defaultdict(int)}
        beginning = date(year, 5, 1)
        for _, country, start, end, best in quarterly["outcome"]:
            for days in (30, 90):
                if start >= beginning and end <= beginning + timedelta(days=days - 1):
                    horizons[days][country] += best
        years[year] = [
            {"country_id": country_id, "country": name,
             "prior_best": prior[country_id],
             "target_best_30": horizons[30][country_id],
             "target_best_90": horizons[90][country_id],
             "y30": int(horizons[30][country_id] >= 25),
             "y90": int(horizons[90][country_id] >= 25)}
            for country_id, name in canonical
        ]
    train = years[2024] + years[2025]
    holdout = years[2026]
    forecast = {}
    model_fits = {}
    scored = {}
    for horizon in (30, 90):
        key = "y" + str(horizon)
        trained = estimates(train, key)
        model_fits[str(horizon)] = trained
        preds = {m: {} for m in ("global", "persistence", "recent_volume")}
        obs = []
        for row in holdout:
            pred = predict(row["prior_best"], trained)
            obs.append({"country_id": row["country_id"], "prior_best": row["prior_best"],
                        "target": row[key]})
            for model in preds:
                preds[model][row["country_id"]] = pred[model]
            if row["country_id"] not in forecast:
                forecast[row["country_id"]] = {
                    "country_id": row["country_id"], "country": row["country"],
                    "prior_best_q1_2026": row["prior_best"],
                }
            forecast[row["country_id"]]["h" + str(horizon)] = {
                "target_best_q3_2026": row["target_best_" + str(horizon)],
                "target": row[key],
                "predicted_probabilities": {k: round(v, 10) for k, v in pred.items()},
            }
        overall = {model: measure(obs, preds[model]) for model in preds}
        emerging = {model: measure(obs, preds[model],
                     subset=lambda r: r["prior_best"] < 25) for model in preds}
        zero_score = round(sum(r["target"] for r in obs) / len(obs), 8)
        scored[str(horizon)] = {
            "holdout_2026": overall,
            "subthreshold_origin_2026": emerging,
            "always_zero_reference_brier": zero_score,
            "holdout_positive_count": sum(r["target"] for r in obs),
        }
    return {
        "schema": "idealab.psico.candidate.q1q3_30_90_holdout.v1",
        "status": "RETROSPECTIVE_ONLY_NOT_ISSUED",
        "protocol_fixed_date": "2026-11-19",
        "training_years": [2024, 2025],
        "holdout_year": 2026,
        "hypothetical_issue_date": "2026-04-30",
        "target_windows_2026": {
            "30": {"start": "2026-05-01", "end": "2026-05-30"},
            "90": {"start": "2026-05-01", "end": "2026-07-29"},
        },
        "historical_issue_dates_independently_verified": False,
        "universe_sha256": hashlib.sha256(frozen_universe).hexdigest(),
        "n_countries": len(canonical),
        "sources": sources,
        "fit_2024_2025": model_fits,
        "retrospective_2026_metrics": scored,
        "retrospective_2026_country_vector": list(forecast.values()),
        "prospective_issued_probabilities": 0,
        "prospective_outcomes_resolved": 0,
        "interpretation": (
            "This is a reconstructed historical check of Candidate >=25 registered "
            "state-based fatalities, restricted to well-dated events. Source vintages "
            "are real but availability by Apr30 was not certified; countries without "
            "registered records are not asserted violence-free. One 2026 holdout year, "
            "strong country dependence, previously studied project, no blind skill claim."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--print-report", action="store_true")
    mode.add_argument("--check-report", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = build_report()
        if args.print_report:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            frozen = json.loads(REPORT.read_text(encoding="utf8"))
            if report != frozen:
                raise SourceError("Published historical holdout differs from official byte replay")
            print("OK: UCDP Candidate 2024-26 March/Sep original-byte 30/90-day holdout replay")
    except (SourceError, ValueError, OSError, TimeoutError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
