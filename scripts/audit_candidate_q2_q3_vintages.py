#!/usr/bin/env python3
"""Deterministic UCDP Candidate quarterly archived-vintage revision audit.

This is research on record revisions, NOT a forecast or genuine as-of backtest.
No article text or person-level source material is emitted; only aggregates.
"""
import argparse
from collections import defaultdict
import csv
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.request

from check_ucdp_candidate_asof import ged_day, SourceError

YEARS = (2024, 2025, 2026)
BASE = "https://ucdp.uu.se/downloads/candidateged/"
Q3_2026_SHA = "134da9b3df08b65266802c4b662e572f396c70c92ab62297319be657540bcede"
REPORT_PATH = Path(__file__).resolve().parents[1] / "data/candidate-q2-q3-vintage-revisions.json"
MAX_SOURCE_BYTES = 25_000_000


def url_for(year, quarter):
    if year not in YEARS or quarter not in (2, 3):
        raise SourceError("Out-of-protocol year/quarter")
    yy = str(year)[2:]
    return BASE + f"GEDEvent_v{yy}_01_{yy}_{quarter * 3:02d}.csv"


def get_source(url):
    if not url.startswith(BASE) or not url.endswith(".csv"):
        raise SourceError("Unexpected official source URL")
    request = urllib.request.Request(url, headers={"User-Agent": "IDEA-LAB-institutional-science-audit/1.0"})
    with urllib.request.urlopen(request, timeout=65) as response:
        if response.url != url:
            raise SourceError("Unexpected redirect for official Candidate source")
        raw = response.read(MAX_SOURCE_BYTES + 1)
    if len(raw) > MAX_SOURCE_BYTES or not raw:
        raise SourceError("Source exceeds cap or is empty")
    return raw


def extract(raw, year):
    """Keep ONLY same first-half event window in each original source."""
    if not isinstance(raw, bytes):
        raise SourceError("Expected original source bytes")
    try:
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        mandatory = {"id", "country_id", "type_of_violence", "date_start", "date_end", "best"}
        if not reader.fieldnames or not mandatory.issubset(reader.fieldnames):
            raise SourceError("GED essential schema mismatch")
        ids, selected = set(), {}
        excluded = {"outside_first_half": 0}
        count = 0
        lo, hi = date(year, 1, 1), date(year, 6, 30)
        for row in reader:
            count += 1
            identifier = (row.get("id") or "").strip()
            if not identifier or identifier in ids:
                raise SourceError("Duplicate or missing ID within a release")
            ids.add(identifier)
            try:
                country = int(row["country_id"])
                kind = int(row["type_of_violence"])
                best = int(row["best"])
            except (TypeError, ValueError) as exc:
                raise SourceError("Unparseable fatality, country or type") from exc
            if country <= 0 or kind not in (1, 2, 3) or best < 0:
                raise SourceError("Invalid GED event coding")
            start = ged_day(row["date_start"], "date_start")
            end = ged_day(row["date_end"], "date_end")
            if start > end:
                raise SourceError("Event start is later than end")
            if start < lo or end > hi:
                excluded["outside_first_half"] += 1
                continue
            selected[identifier] = (country, kind, best, start.isoformat(), end.isoformat())
        if not count or not selected:
            raise SourceError("Empty original archive or ineligible first-half coverage")
        return {"total_rows": count, "eligible_rows": len(selected), "excluded": excluded}, selected
    except UnicodeError as exc:
        raise SourceError("Official CSV is not UTF-8") from exc


def statebased_by_country(records):
    totals = defaultdict(int)
    for country, kind, best, _, _ in records.values():
        if kind == 1:
            totals[country] += best
    return totals


def contrast(left, right):
    a, b = set(left), set(right)
    shared = a & b
    deaths_changed = type_changed = country_changed = dates_changed = 0
    abs_death_revision = 0
    for identifier in shared:
        l, r = left[identifier], right[identifier]
        if l[2] != r[2]:
            deaths_changed += 1
            abs_death_revision += abs(l[2] - r[2])
        country_changed += int(l[0] != r[0])
        type_changed += int(l[1] != r[1])
        dates_changed += int(l[3:] != r[3:])
    a_country, b_country = statebased_by_country(left), statebased_by_country(right)
    countries = set(a_country) | set(b_country)
    a_active = {x for x in countries if a_country.get(x, 0) >= 25}
    b_active = {x for x in countries if b_country.get(x, 0) >= 25}
    return {
        "same_id_events": len(shared),
        "only_q2_ids": len(a - b),
        "only_q3_ids": len(b - a),
        "matched_best_changed_ids": deaths_changed,
        "matched_sum_absolute_best_change": abs_death_revision,
        "matched_type_changed_ids": type_changed,
        "matched_country_changed_ids": country_changed,
        "matched_date_changed_ids": dates_changed,
        "statebased": {
            "q2_fatalities_best": sum(a_country.values()),
            "q3_fatalities_best": sum(b_country.values()),
            "q2_countries_with_25_or_more_best": len(a_active),
            "q3_countries_with_25_or_more_best": len(b_active),
            "country_crosses_up_25": len(b_active - a_active),
            "country_crosses_down_25": len(a_active - b_active),
            "countries_with_changed_recorded_best": sum(
                a_country.get(c, 0) != b_country.get(c, 0) for c in countries
            ),
        },
    }


def build_report(fetcher=get_source):
    years = []
    for year in YEARS:
        archives = []
        selected = []
        for quarter in (2, 3):
            url = url_for(year, quarter)
            raw = fetcher(url)
            digest = hashlib.sha256(raw).hexdigest()
            if (year, quarter) == (2026, 3) and digest != Q3_2026_SHA:
                raise SourceError("Previously SHA-pinned 2026 Q3 official archive changed")
            metadata, eligible = extract(raw, year)
            archives.append({
                "url": url, "sha256": digest, "bytes": len(raw), **metadata
            })
            selected.append(eligible)
        years.append({
            "year": year,
            "q2": archives[0],
            "q3": archives[1],
            "revisions": contrast(*selected),
        })
    fields = ("only_q2_ids", "only_q3_ids", "same_id_events",
              "matched_best_changed_ids", "matched_sum_absolute_best_change",
              "matched_type_changed_ids", "matched_country_changed_ids",
              "matched_date_changed_ids")
    overall = {key: sum(v["revisions"][key] for v in years) for key in fields}
    return {
        "schema": "idealab.psico.candidate.quarterly_vintage_revisions.v1",
        "study_design_date": "2026-11-19",
        "status": "ARCHIVED_SOURCE_REVISIONS_NOT_PREDICTIVE_VALIDATION",
        "comparison": "first-half Jan-Jun identical calendar dates from 2 archival UCDP Candidate editions",
        "year_count": len(YEARS),
        "years": years,
        "pooled_event_accounting_descriptive_only": overall,
        "independent_vintage_publication_dates_verified": False,
        "prospective_issued_probabilities": 0,
        "outcomes_resolved": 0,
        "limitations": (
            "Later Candidate editions are not ground truth; release timestamps are "
            "not certified by archived URLs; event IDs may be recoded; country-year "
            "absence is not proof of zero violence. No as-of prediction or skill claims."
        ),
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--print-report", action="store_true")
    group.add_argument("--check-report", action="store_true")
    args = p.parse_args(argv)
    try:
        report = build_report()
        if args.print_report:
            print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            original = json.loads(REPORT_PATH.read_text(encoding="utf8"))
            if original != report:
                raise SourceError("Frozen report differs from source-byte reconstruction")
            print("OK: exact 2024-2026 UCDP Candidate quarterly source-vintage revision replay")
    except (SourceError, OSError, ValueError, TimeoutError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
