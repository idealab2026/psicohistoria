#!/usr/bin/env python3
"""Fail-closed as-of eligibility audit for UCDP Candidate monthly vintages.

This is NOT a forecasting model. A source passing this gate is not a certified
historical release or an issued prediction. Python standard library only.
"""
import argparse
import calendar
import csv
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


class SourceError(ValueError):
    pass


def iso_day(value, field):
    try:
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError()
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SourceError(f"Invalid ISO date in {field}") from exc


def expected_vintage(url):
    """Derive FULL calendar coverage from an official source filename, not user claims."""
    u = urlsplit(url)
    if (u.scheme, u.netloc) != ("https", "ucdp.uu.se") or u.query or u.fragment:
        raise SourceError("Source must be an unparameterized official UCDP HTTPS URL")
    if not u.path.startswith("/downloads/candidateged/"):
        raise SourceError("Source path is outside official Candidate download directory")
    basename = u.path.rsplit("/", 1)[-1]
    single = re.fullmatch(r"GEDEvent_v(\d{2})_0_(\d{1,2})\.csv", basename)
    cumulative = re.fullmatch(r"GEDEvent_v(\d{2})_01_(\d{2})_(\d{2})\.csv", basename)
    if single:
        yy, mm = map(int, single.groups())
        kind = "monthly"
        first_month = mm
    elif cumulative:
        yy, duplicate_year, mm = map(int, cumulative.groups())
        if yy != duplicate_year or mm not in (3, 6, 9, 12):
            raise SourceError("Invalid official cumulative quarter identifier")
        kind = "cumulative_quarter"
        first_month = 1
    else:
        raise SourceError("Unexpected Candidate filename/version format")
    if not 1 <= mm <= 12:
        raise SourceError("Invalid Candidate release month")
    year = 2000 + yy
    return {
        "kind": kind,
        "version": f"{yy}.0.{mm}" if kind == "monthly" else f"{yy}.01.{yy}.{mm:02d}",
        "coverage_start": date(year, first_month, 1),
        "coverage_end": date(year, mm, calendar.monthrange(year, mm)[1]),
    }


def validate(source_path, manifest, issued_on, horizon_days):
    if horizon_days not in (30, 90):
        raise SourceError("Only predeclared horizons 30 and 90 are allowed")
    issued = iso_day(issued_on, "issued_on")
    if not isinstance(manifest, dict):
        raise SourceError("Manifest must be an object")
    vintage = expected_vintage(manifest.get("source_url", ""))
    if manifest.get("source_version") != vintage["version"]:
        raise SourceError("Source version does not match official filename")
    for field in ("coverage_start", "coverage_end"):
        if iso_day(manifest.get(field), field) != vintage[field]:
            raise SourceError("Declared coverage differs from official filename calendar")
    released = iso_day(manifest.get("released_on"), "released_on")
    if released <= vintage["coverage_end"] or released >= issued:
        raise SourceError("Release must postdate coverage and precede issuance")
    if (issued - vintage["coverage_end"]).days > 45:
        raise SourceError("Source is too stale for a short-horizon issue (>45 days)")
    if (vintage["coverage_end"] - vintage["coverage_start"]).days < 90:
        raise SourceError("Archive lacks the predeclared 90-day source-history window")
    evidence = manifest.get("release_evidence_url", "")
    e = urlsplit(evidence)
    if e.scheme != "https" or e.netloc != "ucdp.uu.se" or not e.path.startswith("/"):
        raise SourceError("Release-date claim requires a reviewable UCDP source URL")
    if manifest.get("review_status") != "operator_attested":
        raise SourceError("Explicit operator review of publication chronology is required")
    expected_sha = manifest.get("source_sha256", "")
    if not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise SourceError("Missing full lowercase SHA-256 of archived original source")
    raw = Path(source_path).read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != expected_sha:
        raise SourceError("Official source bytes do not match declared SHA-256")
    try:
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(text.splitlines())
        required = {"id", "country_id", "type_of_violence", "date_start", "date_end", "best"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise SourceError("Candidate CSV schema missing essential GED columns")
        observed_ids = set()
        counts = {"total": 0, "state_based": 0, "other": 0, "multiday": 0}
        countries = set()
        for row in reader:
            counts["total"] += 1
            identifier = (row["id"] or "").strip()
            if not identifier or identifier in observed_ids:
                raise SourceError("Blank or duplicated GED event id")
            observed_ids.add(identifier)
            try:
                country = int(row["country_id"])
                violence = int(row["type_of_violence"])
                deaths = int(row["best"])
            except (TypeError, ValueError) as exc:
                raise SourceError("Invalid country, type or best death count") from exc
            if country <= 0 or violence not in (1, 2, 3) or deaths < 0:
                raise SourceError("Invalid GED country, violence type or fatalities")
            start = iso_day(row["date_start"], "date_start")
            end = iso_day(row["date_end"], "date_end")
            if start > end or end > vintage["coverage_end"] or end < vintage["coverage_start"]:
                raise SourceError("GED event falls outside declared source window")
            countries.add(country)
            counts["multiday"] += int(start != end)
            counts["state_based" if violence == 1 else "other"] += 1
        if counts["total"] == 0:
            raise SourceError("Empty candidate source: zero events cannot be assumed")
    except UnicodeError as exc:
        raise SourceError("CSV cannot be decoded as UTF-8") from exc
    return {
        "status": "SOURCE_ELIGIBLE_NO_FORECAST",
        "source_version": vintage["version"],
        "source_kind": vintage["kind"],
        "source_sha256": actual_sha,
        "issued_on": issued.isoformat(),
        "target_start": (issued + timedelta(days=1)).isoformat(),
        "target_end": (issued + timedelta(days=horizon_days)).isoformat(),
        "horizon_days": horizon_days,
        "last_observation": vintage["coverage_end"].isoformat(),
        "observation_lag_days": (issued - vintage["coverage_end"]).days,
        "event_counts": counts,
        "distinct_countries_with_events": len(countries),
        "outcomes_resolved": 0,
        "issued_probabilities": 0,
        "release_date_is_independently_verified": False,
        "note": "Operator attestation and SHA ensure traceability, not independent proof of publication date or completeness.",
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--issued-on", required=True)
    p.add_argument("--horizon-days", type=int, choices=(30, 90), required=True)
    args = p.parse_args(argv)
    try:
        meta = json.loads(args.manifest.read_text(encoding="utf8"))
        report = validate(args.source, meta, args.issued_on, args.horizon_days)
    except (SourceError, ValueError, OSError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(report, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
