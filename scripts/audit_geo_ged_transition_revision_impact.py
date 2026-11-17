#!/usr/bin/env python3
"""Derive exact four-state *transition-label revision counts* from official GED comparison summaries.

Does not rebuild source GED event archives. Source authenticity belongs to
audit_geo_ged20_21_coverage_revisions.py, whose source-pinned report is input.
A binary flip at year y necessarily changes every adjacent 2-state pair
(y-1,y) and (y,y+1), whenever those years are eligible. Count the UNION,
not twice the number of flips. This is a retrospective measurement study,
not model skill and not a genuine as-of backtest.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/geo-ged-20-21-coverage-revisions.json"
REPORT = ROOT / "data/geo-ged-transition-revision-impact.json"


def summarize(report: dict) -> dict:
    if report.get("historical_model_fitting_authorized") is not False:
        raise ValueError("Historical GED report is not authorized as a forecast backtest")
    if report.get("GEO2027_GEO2028_forecasts_modified") is not False:
        raise ValueError("Frozen issues changed")
    rows = []
    for item in report["pairs"]:
        c = item["comparison"]
        years = c["target_years"]
        if (not years or years != list(range(years[0], years[-1] + 1))
                or len(years) < 2):
            raise ValueError("Noncontiguous years cannot be treated as adjacent transitions")
        n = c["eligible_countries_per_year"]
        if (not isinstance(n, int) or n < 1
                or c["observed_country_years"] != n * len(years)
                or sum(a["binary_best_ge25_label_flips"] for a in c["annual"])
                != c["best_ge25_binary_label_change_n"]):
            raise ValueError("Inconsistent source comparison exposures")
        flips = c["binary_flip_details"]
        if len(flips) != c["best_ge25_binary_label_change_n"]:
            raise ValueError("Missing country-year identity of a binary revision")
        excluded = set(c["excluded_GWNO_due_official_GED_coverage"])
        revised = set()
        touched = set()
        for f in flips:
            key = (f["GWNO"], f["target_year"])
            if (key in revised or f["GWNO"] in excluded
                    or f["target_year"] not in years
                    or bool(f["old_active"]) == bool(f["new_active"])):
                raise ValueError("Invalid, repeated or out-of-coverage source flip")
            revised.add(key)
            for start in (f["target_year"] - 1, f["target_year"]):
                if start in years and start + 1 in years:
                    touched.add((f["GWNO"], start))
        denominator = n * (len(years) - 1)
        if len(touched) > denominator:
            raise ValueError("Transition count exceeds eligible exposures")
        rows.append({
            "old_version": item["old_version"],
            "new_version": item["new_version"],
            "consecutive_release": item["is_consecutive_release"],
            "years_compared": years,
            "cohort_country_n": n,
            "revised_single_year_binary_labels": len(revised),
            "revised_two_year_transition_labels": len(touched),
            "eligible_country_transitions": denominator,
            "transition_revision_fraction": len(touched) / denominator,
            "revised_transition_country_start_year": [
                {"GWNO": country, "start_year": year}
                for country, year in sorted(touched)
            ],
            "source_coverage_exclusions": sorted(excluded),
        })
    return {
        "schema": "idealab.psico.ged_transition_revision_impact.v1",
        "status": "RETROSPECTIVE_OFFICIAL_SOURCE_SUMMARY_DERIVED_NOT_FORECAST_VALIDATION",
        "method": "Union of adjacent transition pairs touched by country-year binary source flips",
        "source_input": "data/geo-ged-20-21-coverage-revisions.json",
        "source_hashes": report["source_zip_sha256"],
        "independence_warning": "Overlapping edition pairs and country-years are not independent experiments",
        "prospective_skill_claimed": False,
        "new_predictions_issued": 0,
        "pairs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-report", action="store_true")
    parser.add_argument("--print-report", action="store_true")
    args = parser.parse_args()
    result = summarize(json.loads(SOURCE.read_text(encoding="utf-8")))
    data = (json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    if args.check_report and REPORT.read_bytes() != data:
        raise ValueError("Frozen GED transition revision impact report differs")
    if args.print_report:
        print(data.decode(), end="")
    else:
        print(json.dumps([{
            "pair": p["old_version"] + "→" + p["new_version"],
            "revised_transition_labels": p["revised_two_year_transition_labels"],
            "eligible": p["eligible_country_transitions"],
        } for p in result["pairs"]], ensure_ascii=False))


if __name__ == "__main__":
    main()
