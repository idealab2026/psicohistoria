#!/usr/bin/env python3
"""Source-only historical roster drift; no coup data, model or forecast."""
import json, sys
from audit_coup_reconciliation import ROOT, pinned, rows, memberships
from audit_coup_membership import get, URLS, census_zip

def cohort(sets, key, year):
    return {c for c, y in sets[key] if y == year}

def compare(sets, year, lag):
    fixed = cohort(sets, "dec31", year-lag)
    actual = cohort(sets, "jan1", year)
    full = cohort(sets, "full_year", year)
    any_day = cohort(sets, "any_day", year)
    if not fixed or not actual or not full <= actual <= any_day:
        raise ValueError("Invalid source cohort")
    return {"year": year, "lag": lag, "fixed_n": len(fixed),
            "actual_n": len(actual), "intersection_n": len(fixed & actual),
            "missing_from_fixed": len(actual-fixed),
            "stale_in_fixed": len(fixed-actual),
            "fixed_no_membership_during_year": len(fixed-any_day),
            "fixed_not_full_year": len(fixed-full),
            "exact_match": fixed == actual}

def summarize(sets):
    folds = [compare(sets, year, lag) for lag in (1, 3) for year in range(1980, 2025)]
    out = {}
    for lag in (1, 3):
        f = [x for x in folds if x["lag"] == lag]
        n = sum(x["actual_n"] for x in f)
        out[str(lag)] = {"years": len(f), "exact_match_years": sum(x["exact_match"] for x in f),
          "actual_country_years": n, "fixed_country_years": sum(x["fixed_n"] for x in f),
          "missing_country_years": sum(x["missing_from_fixed"] for x in f),
          "stale_country_years": sum(x["stale_in_fixed"] for x in f),
          "max_missing_one_year": max(x["missing_from_fixed"] for x in f),
          "max_stale_one_year": max(x["stale_in_fixed"] for x in f),
          "no_membership_during_year": sum(x["fixed_no_membership_during_year"] for x in f),
          "not_full_year": sum(x["fixed_not_full_year"] for x in f),
          "missing_fraction_of_actual": round(sum(x["missing_from_fixed"] for x in f)/n,9)}
    roster = cohort(sets, "dec31", 2024)
    if not roster:
        raise ValueError("Missing source snapshot")
    return {"status": "HISTORICAL_MEMBERSHIP_DRIFT_ONLY_NO_OUTCOMES",
            "source_snapshot_date": "2024-12-31", "frozen_roster_n": len(roster),
            "future_origin_membership_verified": False, "summary": out,
            "folds": folds, "outcomes_read": 0, "new_forecasts": 0, "modified_forecasts": 0}

def run():
    manifest = json.loads((ROOT/"data/coup-membership-census.json").read_text())
    frozen = json.loads((ROOT/"data/coup-membership-reconciliation.json").read_text())
    inputs = {}
    for m in manifest["sources"]:
        raw = pinned(get(URLS[m["kind"]]), m)
        if census_zip(raw, m["kind"])["csv_member"] != m["csv_member"]:
            raise ValueError("Unexpected archive member")
        inputs[m["kind"]] = list(rows(raw, m["csv_member"]))
    spans, keys, sets, diag = memberships(inputs["States2024"], inputs["System2024"])
    if diag != frozen["membership"] or sets["any_day"] != keys:
        raise ValueError("Frozen membership reconciliation differs")
    report = summarize(sets)
    report["source_sha256"] = [m["sha256"] for m in manifest["sources"]]
    return report

if __name__ == "__main__":
    print("COUP_ROSTER_BEGIN", flush=True)
    report = run()
    if "--check" in sys.argv and report != json.loads((ROOT/"data/coup-fixed-cohort-audit.json").read_text()):
        raise ValueError("Frozen roster audit differs")
    print(json.dumps(report, sort_keys=True, indent=2))
    print("COUP_ROSTER_END", flush=True)
