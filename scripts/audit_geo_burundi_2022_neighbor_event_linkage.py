#!/usr/bin/env python3
"""Conservative, reproducible hard negatives for Mabayi GED 442626 entity linkage.

Never equate a place/FLN keyword match with a June 2022 casualty witness.
This audit scores the REPORT'S EPISODE; death-date and person identities may
remain unresolved. The external pages are manually summarized, NOT hashed.
"""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/geo-burundi-2022-neighbor-event-linkage.json"
TARGET_START = date(2022, 6, 18)
TARGET_END = date(2022, 6, 21)
HOSTS = {"www.sosmediasburundi.org", "www.iwacu-burundi.org"}
ALLOWED_TYPES = {"armed_clash", "mining_accident"}


def classify(source, tolerance_days=3):
    if set(("id", "publisher", "published", "source_url", "incident_type",
            "event_window", "expected_relation")) - set(source):
        raise ValueError("Missing structured comparison fields")
    published = date.fromisoformat(source["published"])
    host = urlsplit(source["source_url"]).hostname
    if host not in HOSTS:
        raise ValueError("Unreviewed event-comparison publication host")
    kind = source["incident_type"]
    if kind not in ALLOWED_TYPES:
        raise ValueError("Unknown incident class")
    if not isinstance(tolerance_days, int) or not 0 <= tolerance_days <= 14:
        raise ValueError("Unsupported date tolerance")
    if source.get("local_primary_june_2022_fatality_verification") is not False:
        raise ValueError("Unverified June casualty corroboration")
    obs = source.get("observation_day")
    if obs is not None and date.fromisoformat(obs) > published:
        raise ValueError("Observation cannot postdate source publication")
    window = source["event_window"]
    if window is not None:
        if len(window) != 2:
            raise ValueError("Invalid event window")
        first, last = (date.fromisoformat(t) for t in window)
        if first > last or last > published:
            raise ValueError("Invalid event-window order or future interval")
    if kind != "armed_clash":
        return "EXCLUDE_INCOMPATIBLE_CAUSE"
    # A May 9 article cannot directly witness a later June 18-21 event.
    if published < TARGET_START:
        return "EXCLUDE_PUBLICATION_PREDATES_JUNE"
    if window is None:
        # Discovery dates are NOT automatically death dates. This is an
        # unresolved person linkage, but is not fresh June corroboration.
        return "UNRESOLVED_DEATH_DATES_NOT_JUNE_CORROBORATION"
    if first > TARGET_END:
        gap = (first - TARGET_END).days
    elif last < TARGET_START:
        gap = (TARGET_START - last).days
    else:
        gap = 0
    if gap > tolerance_days:
        return "EXCLUDE_SEPARATE_REPORTED_BATTLE_WINDOW"
    return "MANUAL_SAME_EPISODE_REVIEW_REQUIRED"


def build(data):
    if data["schema"] != "idealab.psico.geo_burundi_2022_neighbor_event_linkage.v1":
        raise ValueError("Wrong comparison protocol version")
    if data["target"]["ged_event_id"] != 442626:
        raise ValueError("Reference event changed")
    if data["target"]["fatalities_in_GED_best"] != 10:
        raise ValueError("Prior GED best estimate changed")
    if data["target"]["uncertain_event_window"] != ["2022-06-18", "2022-06-21"]:
        raise ValueError("June 18-21 uncertainty envelope changed")
    tol = data["temporal_tolerance_days"]
    cases = data["case_records"]
    if len(cases) != 5 or len({x["id"] for x in cases}) != 5:
        raise ValueError("Expected five unique public comparator reports")
    relations = [{"case_id": x["id"], "relation": classify(x, tol)} for x in cases]
    if any(x["expected_relation"] != rel["relation"] for x, rel in zip(cases, relations)):
        raise ValueError("Editorial and algorithmic relation do not agree")
    counts = {
        "records_n": len(cases),
        # Location-only retrieval cannot identify episodes; count all rows.
        "potential_location_only_false_matches_n": len(cases),
        "excluded_as_direct_june_episode_n": sum(
            x["relation"].startswith("EXCLUDE_") for x in relations),
        "ambiguous_later_discovery_n": sum(
            x["relation"] == "UNRESOLVED_DEATH_DATES_NOT_JUNE_CORROBORATION"
            for x in relations),
        "additional_independent_june_fatality_verifications_n": 0,
        "confirmed_disjoint_person_rosters_n": 0,
        "results": relations,
    }
    if counts != data["expected_results"]:
        raise ValueError("Frozen comparison decisions or counts changed")
    return counts


def check_frozen_chain():
    import audit_geo_burundi_2022_institutional_dependency as base
    from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Original GEO2027 vector changed")
    previous = json.loads(base.ANCHOR.read_text(encoding="utf-8"))
    if base.build_report(previous) != json.loads(base.OUTPUT.read_text(encoding="utf-8")):
        raise ValueError("Previously published institutional source chain changed")
    from audit_geo2027_global_only_matched_issue import (
        ISSUE, MANIFEST, ORIGINAL, OLD_SHADOW, OLD_MANIFEST, ALERTS,
        audit as audit_issued)
    audit_issued(ISSUE.read_bytes(), MANIFEST.read_bytes(), ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(), OLD_MANIFEST.read_bytes(), ALERTS.read_bytes())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--check-report", action="store_true")
    p.add_argument("--print-report", action="store_true")
    a = p.parse_args()
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    results = build(data)
    if a.check_report:
        check_frozen_chain()
    print(json.dumps(results, indent=2 if a.print_report else None,
                     sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
