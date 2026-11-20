#!/usr/bin/env python3
"""UCDP Candidate uncertainty + coding sensitivity: NOT a new forecast.

9 original quarter archives; original SHA checked against frozen PR #149.
Fully enclosed events, UCDP date_prec 1/2, fixed 196-country set.
The attractive 2026 five-death result was already known: POST SELECTION.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, timedelta
import hashlib
import io
import json
from pathlib import Path
import sys

from check_ucdp_candidate_asof import SourceError, ged_day
from audit_candidate_q2_q3_vintages import get_source, url_for
from experiment_candidate_30_90_holdout import archive_url, universe_from_bytes
from audit_candidate_onset_label_stability import tie_aware_k

ROOT = Path(__file__).resolve().parents[1]
REVISIONS = ROOT / "data/candidate-may-threshold-vintage-stability.json"
GRID = ROOT / "data/candidate-reactivation-threshold-grid.json"
UNIVERSE = ROOT / "data/forecast-2027-ucdp261.json"
REPORT = ROOT / "data/candidate-fatality-uncertainty-code-status.json"
YEARS = (2024, 2025, 2026)
MONTHS = (3, 6, 9)
FOCUS = (501, 620)  # Kenya and Libya; fixed before running
THRESHOLD = 5
FIELDS = ("low", "best", "high", "clear_best")


def official_pins(registry):
    if registry.get("status") != "POST_SELECTION_SOURCE_REVISION_SENSITIVITY_NOT_PROSPECTIVE":
        raise SourceError("Original source provenance registry status is unexpected")
    result = {}
    for item in registry.get("nine_original_sha_pinned_sources", []):
        y, m = item["year"], item["month"]
        if (y, m) in result:
            raise SourceError("Repeated source in frozen registry")
        url = archive_url(y, m) if m != 6 else url_for(y, 2)
        if item.get("source_url") != url or len(item.get("source_sha256", "")) != 64:
            raise SourceError("Cannot authenticate original UCDP source path / SHA")
        result[(y, m)] = item
    if set(result) != {(y, m) for y in YEARS for m in MONTHS}:
        raise SourceError("Source registry is not exactly 9 fixed archives")
    return result


def blank_country_sums():
    return {"low": 0, "best": 0, "high": 0, "clear_best": 0,
            "n_state_events": 0, "code_status_counts": {}}


def audit_csv(raw, year, month, universe):
    """Parse every event; only type1 date-prec 1/2 fully enclosed in fixed windows."""
    if month not in MONTHS or year not in YEARS:
        raise SourceError("Out-of-protocol source")
    required = {"id", "country_id", "type_of_violence", "date_prec",
                "date_start", "date_end", "best", "low", "high", "code_status"}
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise SourceError("Original Candidate source lacks essential low/high/code_status columns")
    ids = set()
    counts = Counter()
    data = defaultdict(lambda: defaultdict(lambda: {
        "low": 0, "best": 0, "high": 0, "clear_best": 0,
        "n_state_events": 0, "statuses": Counter()
    }))
    first = date(year, 1, 1)
    q1_end = date(year, 3, 31)
    may_start = date(year, 5, 1)
    may_end = date(year, 5, 30)
    long_end = may_start + timedelta(days=89)
    for row in reader:
        counts["source_rows"] += 1
        event_id = (row["id"] or "").strip()
        if not event_id or event_id in ids:
            raise SourceError("Missing/duplicated GED event ID")
        ids.add(event_id)
        try:
            country = int(row["country_id"])
            violence = int(row["type_of_violence"])
            precision = int(row["date_prec"])
            death = {key: int(row[key]) for key in ("low", "best", "high")}
        except (ValueError, TypeError) as exc:
            raise SourceError(f"Invalid GED fields in {year} quarter{month} event id={event_id}") from exc
        if country <= 0 or violence not in (1, 2, 3) or precision not in (0, 1, 2, 3, 4, 5):
            raise SourceError("Invalid country/type/date precision")
        if any(value < 0 for value in death.values()) or not (
            death["low"] <= death["best"] <= death["high"]
        ):
            raise SourceError(f"Candidate {year}-{month} invalid deaths at id={event_id}, country={country}, type={violence}, date_prec={precision}, dates={row.get('date_start')}/{row.get('date_end')}, deaths={death}")
        start = ged_day(row["date_start"], "date_start")
        end = ged_day(row["date_end"], "date_end")
        if start > end:
            raise SourceError("GED event date_start > date_end")
        if violence != 1:
            counts["skip_non_state_based"] += 1
            continue
        if precision not in (1, 2):
            counts["skip_low_or_unknown_date_precision"] += 1
            counts["skip_date_prec_zero"] += int(precision == 0)
            continue
        if country not in universe:
            counts["skip_outside_country_universe"] += 1
            continue
        targets = []
        if month == 3:
            if start >= first and end <= q1_end:
                targets.append("q1")
        else:
            if start >= may_start and end <= may_end:
                targets.append("may30")
            if month == 9 and start >= may_start and end <= long_end:
                targets.append("may90")
        if not targets:
            counts["skip_outside_fixed_windows"] += 1
            continue
        status = (row["code_status"] or "").strip()
        normalized = status.casefold() if status else "(blank)"
        if not status:
            counts["blank_code_status_included"] += 1
        for target in targets:
            record = data[target][country]
            record["n_state_events"] += 1
            record["statuses"][normalized] += 1
            for field in ("low", "best", "high"):
                record[field] += death[field]
            if normalized == "clear":
                record["clear_best"] += death["best"]
            counts["included_" + target] += 1
    if not counts["source_rows"]:
        raise SourceError("Empty source")
    out = {}
    for window, countries in data.items():
        out[window] = {}
        for country, r in countries.items():
            out[window][country] = {
                **{k: r[k] for k in ("low", "best", "high", "clear_best", "n_state_events")},
                "code_status_counts": dict(sorted(r["statuses"].items()))
            }
    return {"source_rows": counts["source_rows"],
            "checks": dict(sorted(counts.items()))}, out


def get_record(data, window, country):
    return data.get(window, {}).get(country, blank_country_sums())


def aggregate_window(data, window, risk_set, focus=FOCUS):
    records = {country: get_record(data, window, country) for country in risk_set}
    classifications = {
        field: sorted(country for country, row in records.items() if row[field] >= THRESHOLD)
        for field in FIELDS
    }
    best_positive = set(classifications["best"])
    low_positive = set(classifications["low"])
    clear_positive = set(classifications["clear_best"])
    all_status = Counter()
    for row in records.values():
        all_status.update(row["code_status_counts"])
    return {
        "n_risk": len(risk_set),
        "threshold": THRESHOLD,
        "positive_counts": {field: len(ids) for field, ids in classifications.items()},
        "best_positive_ids": classifications["best"],
        "low_positive_ids": classifications["low"],
        "high_positive_ids": classifications["high"],
        "clear_best_positive_ids": classifications["clear_best"],
        "best_not_low_ids": sorted(best_positive - low_positive),
        "best_not_clear_ids": sorted(best_positive - clear_positive),
        "all_risk_state_event_code_status_counts": dict(sorted(all_status.items())),
        "focus": {
            str(country): get_record(data, window, country)
            for country in focus
        },
    }


def refit_free_top10(grid, origin, outcomes):
    fit = grid["trained_models"]["5"]["30"]
    vector = grid["holdout_2026_country_observations"]
    alerts = {field: [] for field in FIELDS}
    for row in vector:
        country = row["country_id"]
        if origin[country]["best"] >= THRESHOLD:
            continue
        prior = row["q1_state_best"]
        prior_bin = "zero" if prior == 0 else "1-4" if prior < 5 else "5-9" if prior < 10 else "10+"
        other = "True" if row["q1_other_best"] >= 1 else "False"
        probability = fit["groups"]["combined"][prior_bin + "|" + other]["p"]
        event = outcomes.get(country, blank_country_sums())
        for field in FIELDS:
            alerts[field].append({"country_id": country, "p": probability,
                                  "target": int(event[field] >= THRESHOLD)})
    return {
        field: tie_aware_k(rows, "p", 10)
        for field, rows in alerts.items()
    }


def build_report(fetcher=get_source, registry=None, grid=None, universe_raw=None):
    registry = json.loads(REVISIONS.read_text("utf8")) if registry is None else registry
    grid = json.loads(GRID.read_text("utf8")) if grid is None else grid
    universe_raw = UNIVERSE.read_bytes() if universe_raw is None else universe_raw
    if grid.get("status") != "EXPLORATORY_HISTORICAL_NOT_ASOF_NOT_ISSUED":
        raise SourceError("Prior 2026 grid must be frozen and historical")
    if hashlib.sha256(universe_raw).hexdigest() != grid.get("universe_sha256"):
        raise SourceError("Canonical country universe has changed")
    names = dict(universe_from_bytes(universe_raw))
    for c in FOCUS:
        if c not in names:
            raise SourceError("Focus country missing from universe")
    pins = official_pins(registry)
    historical = []
    provenance = []
    detailed_2026 = None
    for year in YEARS:
        sources = {}
        for month in MONTHS:
            manifest = pins[(year, month)]
            raw = fetcher(manifest["source_url"])
            digest = hashlib.sha256(raw).hexdigest()
            if digest != manifest["source_sha256"]:
                raise SourceError("Official UCDP Candidate original SHA mismatch")
            meta, datasets = audit_csv(raw, year, month, set(names))
            if meta["source_rows"] != manifest["source_rows"]:
                raise SourceError("Source rows drifted despite frozen SHA")
            sources[month] = datasets
            provenance.append({
                "year": year, "month": month, "sha256": digest,
                "source_url": manifest["source_url"], "bytes": len(raw),
                "audit": meta
            })
        risk = sorted(c for c in names if get_record(sources[3], "q1", c)["best"] < THRESHOLD)
        edition_summary = {}
        for month in (6, 9):
            edition_summary[str(month)] = aggregate_window(sources[month], "may30", risk)
        earlier = registry["may_label_revision_by_year"]
        item = next((x for x in earlier if x["year"] == year), None)
        if item is None:
            raise SourceError("Frozen Q2→Q3 comparison missing year")
        for month, col in ((6, "q2"), (9, "q3")):
            expected = item["thresholds"]["5"][col + "_positive_country_ids"]
            if edition_summary[str(month)]["best_positive_ids"] != expected:
                raise SourceError(f"Best May threshold revision mismatch year {year} month {month}")
        if len(risk) != item["thresholds"]["5"]["risk_set"]:
            raise SourceError("Original source risk-set membership changed")
        historical.append({
            "year": year, "risk_q1_best_less_than_5": len(risk),
            "may30_from_q2": edition_summary["6"],
            "may30_from_q3": edition_summary["9"],
        })
        if year == 2026:
            vector = grid["holdout_2026_country_observations"]
            if len(vector) != 196:
                raise SourceError("Frozen 2026 grid missing countries")
            for row in vector:
                cid = row["country_id"]
                if get_record(sources[3], "q1", cid)["best"] != row["q1_state_best"]:
                    raise SourceError("Q1 source differs from frozen model's input")
                if get_record(sources[9], "may30", cid)["best"] != row["future_best_30"]:
                    raise SourceError("Q3 May target differs from frozen holdout")
                if get_record(sources[9], "may90", cid)["best"] != row["future_best_90"]:
                    raise SourceError("Q3 90d target differs from frozen holdout")
            long = aggregate_window(sources[9], "may90", risk)
            detailed_2026 = {
                "risk_members_count": len(risk),
                "origin_q1_focus": {
                    str(cid): get_record(sources[3], "q1", cid) for cid in FOCUS
                },
                "may30_q2_top10_original_model": refit_free_top10(
                    grid, {c: get_record(sources[3], "q1", c) for c in names},
                    sources[6].get("may30", {})
                ),
                "may30_q3_top10_original_model": refit_free_top10(
                    grid, {c: get_record(sources[3], "q1", c) for c in names},
                    sources[9].get("may30", {})
                ),
                "may90_q3": long
            }
    if detailed_2026 is None:
        raise SourceError("2026 holdout missing")
    return {
        "schema": "idealab.psico.candidate.fatality_uncertainty_code_status_v1",
        "status": "POST_SELECTION_HISTORICAL_SENSITIVITY_NOT_ISSUED",
        "design_date": "2026-11-20",
        "years": list(YEARS),
        "threshold": THRESHOLD,
        "n_universe_countries": len(names),
        "focus_country_codes": list(FOCUS),
        "original_source_provenance": provenance,
        "may30_vintage_sensitivity": historical,
        "holdout_2026": detailed_2026,
        "source_first_release_dates_certified": False,
        "forecast_issued": False,
        "historical_model_refit": False,
        "limitations": (
            "UCDP Candidate early-coded events can be recoded, removed or added in annual GED. "
            "low/high are NOT statistical confidence intervals. clear-only is a descriptive "
            "coding filter, NOT final validity. This audit follows an already-inspected "
            "favorable May 2026 result, and source first-publication dates are not proved."
        )
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--print-report", action="store_true")
    g.add_argument("--check-report", action="store_true")
    args = p.parse_args(argv)
    try:
        report = build_report()
        if args.print_report:
            print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
        else:
            frozen = json.loads(REPORT.read_text("utf8"))
            if frozen != report:
                raise SourceError("Official source sensitivity does not match frozen result")
            print("OK: nine UCDP original SHA and fatality/code-status sensitivity reproduced")
    except (SourceError, ValueError, TypeError, KeyError, OSError, TimeoutError) as err:
        print("BLOCKED: " + str(err), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
