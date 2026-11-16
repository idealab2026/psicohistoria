#!/usr/bin/env python3
"""Read real official state-based annual fatality COUNTS underlying 2019/2020 label revisions.

Ex-post source-vintage comparison only: 23.1 XLSX and 24.1/25.1/26.1
CSV ZIP are independently SHA-pinned. Never use an updated vintage as an
alleged prospectively published historical prediction.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zipfile import ZipFile

from backtest_archived_country_vintages import SOURCES, read_xlsx_rows
from build_official_countries import read_zip
from probe_ucdp_organized_vintages import request

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data/geo2027-indonesia-raw-death-revisions.json"
ATTRIBUTION = ROOT / "data/geo2027-indonesia-vintage-revision-attribution.json"
IDS = {850: "Indonesia", 703: "Kyrgyzstan"}
YEARS = tuple(range(2017, 2023))
VERSIONS = ("23.1", "24.1", "25.1", "26.1")
MAX_BYTES = 8_000_000


def exact_nonnegative_int(raw, field):
    try:
        val = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid official {field} field") from exc
    if not val.is_finite() or val != val.to_integral_value():
        raise ValueError(f"Noninteger official {field} field")
    number = int(val)
    if number < 0 or number > 10_000_000:
        raise ValueError(f"Implausible official {field} field")
    return number


def parse_selected_rows(raw: bytes, version: str):
    """Original best-estimate death counts for two GW countries, 2017..2022."""
    if version not in VERSIONS:
        raise ValueError("Unsupported UCDP source edition")
    if version == "23.1":
        rows = read_xlsx_rows(raw)
    else:
        if version == "26.1":
            csv_text = read_zip(raw)
            country_col, year_col, deaths_col = (
                "country_id", "year", "sb_total_deaths_best")
        else:
            with ZipFile(io.BytesIO(raw)) as archive:
                members = [n for n in archive.namelist() if n.endswith(".csv")]
                if len(members) != 1 or archive.getinfo(members[0]).file_size > 12_000_000:
                    raise ValueError("Unexpected historical UCDP source ZIP")
                csv_text = archive.read(members[0]).decode("utf-8-sig")
            country_col, year_col, deaths_col = (
                "country_id_cy", "year_cy", "sb_total_deaths_best_cy")
        reader = csv.DictReader(io.StringIO(csv_text))
        if not {country_col, year_col, deaths_col}.issubset(reader.fieldnames or []):
            raise ValueError("Required official source columns absent")
        rows = ((r[country_col], r[year_col], r[deaths_col]) for r in reader)
    selected = {cid: {} for cid in IDS}
    for cid_raw, year_raw, death_raw in rows:
        cid = exact_nonnegative_int(cid_raw, "country_id")
        if cid not in selected:
            continue
        year = exact_nonnegative_int(year_raw, "year")
        if year not in YEARS:
            continue
        deaths = exact_nonnegative_int(death_raw, "sb_total_deaths_best")
        if year in selected[cid]:
            raise ValueError("Duplicate official country-year row")
        selected[cid][year] = deaths
    if any(set(years) != set(YEARS) for years in selected.values()):
        raise ValueError("Country-year gap: never treat missing record as zero")
    return selected


def revision_rows(sources, prior):
    if prior.get("schema") != (
        "idealab.psico.geo2027_indonesia_vintage_source_attribution.v1"
    ) or prior.get("outcomes_2027_resolved") != 0:
        raise ValueError("Expected SHA-pinned prior source-attribution report")
    orig = sources["23.1"]
    editions = {}
    for version in VERSIONS:
        epochs = {}
        for cid, name in IDS.items():
            epochs[str(cid)] = [
                {"year": year, "sb_total_deaths_best": sources[version][cid][year],
                 "binary_state_at_25": int(sources[version][cid][year] >= 25)}
                for year in YEARS
            ]
        editions[version] = epochs

    cases = []
    for pair in prior["comparisons"]:
        version = pair["comparison"].split("->")[1]
        if version not in VERSIONS[1:]:
            raise ValueError("Unknown revision pair")
        changes = []
        for cid in IDS:
            for year in YEARS:
                old_value, new_value = orig[cid][year], sources[version][cid][year]
                if (old_value >= 25) != (new_value >= 25):
                    changes.append({
                        "country": IDS[cid], "country_id": cid, "year": year,
                        "old_deaths": old_value, "revised_deaths": new_value,
                        "old_state": int(old_value >= 25),
                        "revised_state": int(new_value >= 25)
                    })
        idn_prior = pair["countries"]["850"]["changed_historical_binary_years"]
        observed_idn = [{"year": r["year"], "original_state": r["old_state"],
                         "revised_state": r["revised_state"]}
                        for r in changes if r["country_id"] == 850]
        if sorted(idn_prior, key=lambda x:x["year"]) != sorted(observed_idn, key=lambda x:x["year"]):
            raise ValueError("Underlying official death-count thresholds contradict prior binary revisions")
        cases.append({"comparison": pair["comparison"], "binary_threshold_changes": changes})
    return {
        "schema": "idealab.psico.geo2027_indonesia_annual_deaths_vintage_audit.v1",
        "status": "OFFICIAL_SOURCE_SHA_PINNED_HISTORICAL_REVISION_NOT_PREDICTION",
        "sources_sha256": {v:SOURCES[v]["sha256"] for v in VERSIONS},
        "countries": IDS,
        "years": list(YEARS),
        "death_metric": "UCDP OrganizedViolenceCY sb_total_deaths_best country-year",
        "threshold_state_1": ">=25 state-based deaths; NOT violence against civilians or all-organized-violence deaths",
        "source_original_annual_deaths": editions,
        "compared_to_23_1": cases,
        "2027_outcomes_observed": 0,
        "not_a_causal_analysis_or_historical_issue": True,
        "no_issued_forecast_replaced": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-report", action="store_true")
    args = parser.parse_args()
    prior = json.loads(ATTRIBUTION.read_text(encoding="utf8"))
    sources = {}
    for version in VERSIONS:
        raw = request(SOURCES[version]["url"], MAX_BYTES)
        digest = hashlib.sha256(raw).hexdigest()
        if digest != SOURCES[version]["sha256"]:
            raise ValueError("Official original UCDP source hash mismatch: "+version)
        sources[version] = parse_selected_rows(raw, version)
    report = revision_rows(sources, prior)
    payload = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    print("GEO2027_INDONESIA_ORIGINAL_FATALITIES_BEGIN")
    print(payload, end="")
    print("GEO2027_INDONESIA_ORIGINAL_FATALITIES_END")
    if args.check_report and REPORT.read_bytes() != payload.encode("utf8"):
        raise ValueError("Published original death-count revision report differs from source")


if __name__ == "__main__":
    main()
