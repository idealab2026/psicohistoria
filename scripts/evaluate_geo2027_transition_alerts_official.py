#!/usr/bin/env python3
"""GEO-2027: future-only OFFICIAL state-transition alert scoring CONTRACT.

Never reads target-year outcomes unless an operator explicitly supplies a ZIP,
source URL, exact byte hash and post-2027 claimed release date. None of those
operator claims proves that the file is the FIRST COMPLETE official release.
No report is ever marked independently certified or prospective skill proven.

The 196 probabilities, 2025 states, 15 issued alerts and first public commit
are authenticated against their existing SHA-256 fingerprints before scoring.
Missing 2027 country-year labels force all alert/skill scores to remain null.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
from pathlib import Path
from urllib.parse import urlsplit

from audit_issued_geo2027_transition_alerts import audit as audit_issue
from build_official_countries import read_zip
from diagnose_geo2027_exact_alert_null import hypergeom_pmf
from evaluate_2027_official import load_frozen_issue, validate_future_source
from evaluate_geo2027_transition_alerts import (
    auc_with_midrank_ties, tie_group_average_precision,
)
from prepare_geo2027_transition_alerts import (
    FORECAST_PATH, MANIFEST_PATH, BUDGETS, SOURCE_SHA256, sha,
)

ISSUE_PATH = Path("data/forecast-2027-transition-alerts.json")
ISSUE_MANIFEST = Path("data/forecast-2027-transition-alerts-manifest.json")
ISSUE_AUDIT = Path("data/forecast-2027-transition-alerts-audit.json")
GENERATOR = Path("scripts/prepare_geo2027_transition_alerts.py")
ISSUE_SHA = "309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb"
FIRST_ISSUE_COMMIT = "5938db3c93661ce04ed35902b2bdaa68abfb8daa"
YEAR = 2027
N_COUNTRIES = 196
COUNTS = {0: 162, 1: 34}
COLUMNS = ("p_model", "p_global_markov")


def load_authenticated():
    """Fail closed if ANY original source, alert or provenance byte changes."""
    forecast, original_manifest = load_frozen_issue(FORECAST_PATH, MANIFEST_PATH)
    original_raw = FORECAST_PATH.read_bytes()
    issue_raw = ISSUE_PATH.read_bytes()
    issued_manifest = json.loads(ISSUE_MANIFEST.read_text(encoding="utf8"))
    actual_audit = audit_issue(
        issue_raw, issued_manifest, GENERATOR.read_bytes(),
        original_raw, original_manifest,
    )
    if (sha(original_raw) != SOURCE_SHA256 or sha(issue_raw) != ISSUE_SHA
        or issued_manifest.get("first_public_issue_commit") != FIRST_ISSUE_COMMIT
        or actual_audit != json.loads(ISSUE_AUDIT.read_text(encoding="utf8"))
        or actual_audit.get("outcomes_2027_resolved") != 0):
        raise ValueError("Original GEO-2027 alert issue fingerprint/audit changed")
    alerts = json.loads(issue_raw)
    return forecast, alerts, issued_manifest


def validate_candidate_source(url, claimed_sha, claimed_date):
    """Shape and timing checks, NOT independent UCDP provenance certification."""
    validate_future_source(url, claimed_sha, claimed_date)
    parts = urlsplit(url)
    if (parts.hostname != "ucdp.uu.se" or parts.port is not None
        or parts.username or parts.password or not re.fullmatch(
            r"/downloads/organizedviolencecy/organizedviolencecy-(\d{3})-csv\.zip",
            parts.path,
        )):
        raise ValueError("Only direct official UCDP OrganizedViolenceCY releases")
    release = int(re.search(r"-(\d{3})-csv\.zip$", parts.path).group(1))
    if release < 281:
        raise ValueError("A UCDP vintage from before 2028 cannot resolve 2027")
    return True


def parse_future_csv(text):
    """Parse country-year, flag blank deaths as UNRESOLVED, reject duplicates."""
    if isinstance(text, bytes):
        text = text.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    headers = reader.fieldnames or []
    if len(set(headers)) != len(headers):
        raise ValueError("Duplicate official CSV columns")
    def pick(primary, alt):
        available = [x for x in (primary, alt) if x in headers]
        if not available:
            raise ValueError("Missing official " + primary + " column")
        if len(available) != 1:
            raise ValueError("Ambiguous duplicate official field aliases")
        return available[0]
    id_key = pick("country_id", "country_id_cy")
    year_key = pick("year", "year_cy")
    deaths_key = pick("sb_total_deaths_best", "sb_total_deaths_best_cy")
    labels = {}
    unlabelled = set()
    seen = set()
    target_rows = 0
    for row in reader:
        if None in row or row.get(None) is not None:
            raise ValueError("Malformed official country-year CSV row")
        raw_year = (row.get(year_key) or "").strip()
        if not re.fullmatch(r"\d{4}", raw_year):
            raise ValueError("Invalid annual official source year")
        if int(raw_year) != YEAR:
            continue
        target_rows += 1
        raw_id = (row.get(id_key) or "").strip()
        if not re.fullmatch(r"[0-9]{1,5}", raw_id):
            raise ValueError("Missing/invalid official country ID")
        country = int(raw_id)
        if not 1 <= country <= 2000:
            raise ValueError("Official country ID out of range")
        if country in seen:
            raise ValueError("Duplicated 2027 country-year, cannot aggregate")
        seen.add(country)
        raw_deaths = (row.get(deaths_key) or "").strip()
        if raw_deaths == "":
            unlabelled.add(country)
            continue
        if not re.fullmatch(r"\d{1,8}", raw_deaths):
            raise ValueError("Official deaths is not an integer or marked missing")
        deaths = int(raw_deaths)
        if deaths > 10_000_000:
            raise ValueError("Official deaths outside supported range")
        labels[country] = int(deaths >= 25)
    if target_rows == 0:
        raise ValueError("No official 2027 country-year records")
    return labels, {
        "source_2027_rows": target_rows,
        "source_2027_complete_labels": len(labels),
        "source_2027_blank_labels": len(unlabelled),
        "source_2027_unique_ids": len(seen),
        "blank_labels_never_imputed_negative": True,
    }


def holm_pair(p):
    """Pre-registered two-sided FAMILY of TWO one-sided upper-tail endpoints."""
    if set(p) != {"entry", "resolution"} or any(
        isinstance(v, bool) or not isinstance(v, (int, float))
        or not math.isfinite(v) or not 0 <= v <= 1 for v in p.values()
    ):
        raise ValueError("Exactly two valid original endpoint upper tails required")
    ranked = sorted(p, key=lambda x: (p[x], x))
    adjusted = {}
    previous = 0.0
    for i, key in enumerate(ranked):
        value = min(1.0, (len(ranked) - i) * p[key])
        adjusted[key] = max(previous, value)
        previous = adjusted[key]
    return adjusted


def scoring_group(rows, issued, state, outcomes):
    if state not in (0, 1):
        raise ValueError("Unknown origin state")
    group = [r for r in rows if r["last_observed_state_2025"] == state]
    if len(group) != COUNTS[state]:
        raise ValueError("Source-defined 2025 risk set changed")
    alerts = issued["risk_groups"][str(state)]["selected_countries"]
    if (len(alerts) != BUDGETS[state]
        or {a["country_id"] for a in alerts} -
           {r["country_id"] for r in group}):
        raise ValueError("Original alert list not part of frozen risk set")
    if any(r["country_id"] not in outcomes for r in group):
        raise ValueError("No skill/alert score allowed on unresolved full risk set")
    scores = {}
    for key in COLUMNS:
        comparisons = []
        for r in group:
            p = r[key] if state == 0 else 1-r[key]
            event = int(outcomes[r["country_id"]] != state)
            if not 0 < p < 1 or type(event) is not int:
                raise ValueError("Invalid frozen forecast probability")
            comparisons.append((p, event))
        brier = sum((p - y)**2 for p, y in comparisons) / len(comparisons)
        scores[key] = {
            "brier": brier,
            "mean_probability": sum(p for p, _ in comparisons) / len(comparisons),
            "auc_roc_midrank": auc_with_midrank_ties(comparisons),
            "pr_area_tie_group": tie_group_average_precision(comparisons),
        }
    events = sum(int(outcomes[r["country_id"]] != state) for r in group)
    hits = sum(int(outcomes[a["country_id"]] != state) for a in alerts)
    budget = BUDGETS[state]
    pmf = hypergeom_pmf(len(group), events, budget)
    exact_tail = min(1.0, sum(prob for k, prob in pmf.items() if k >= hits))
    return {
        "status": "SELF_REPORTED_SOURCE_COMPLETE_CANDIDATE_UNCERTIFIED",
        "origin_state": state,
        "question": "entry_0_to_1" if state == 0 else "resolution_1_to_0",
        "eligible": len(group),
        "target_transitions": events,
        "target_prevalence": events / len(group),
        "issued_alert_budget": budget,
        "alert_hits": hits,
        "alert_false_positives": budget-hits,
        "alert_precision": hits / budget,
        "alert_recall": hits / events if events else None,
        "model_expected_hits_at_issue": issued["risk_groups"][str(state)][
            "model_expected_hits_in_selected_alerts"],
        "model_expected_transition_count_at_issue": issued["risk_groups"][str(state)][
            "model_expected_transitions_in_all_eligible_countries"],
        "models": scores,
        "delta_brier_country_minus_global_markov": (
            scores["p_model"]["brier"] - scores["p_global_markov"]["brier"]
        ),
        "deterministic_no_transition_brier": events / len(group),
        "random_expected_alert_hits": budget * events / len(group),
        "exact_upper_tail_given_observed_transitions": exact_tail,
        "hypergeometric_null": "Exchangeable labels conditional on the number of transitions inside this known 2025 risk set; not a causal/null test of geopolitical independence",
    }


def evaluate(forecast, alerts, outcomes, source_claim, parse_audit):
    if (forecast.get("forecast_id") != "PSICO-GEO2027-STATEBASED25-V1"
        or alerts.get("cohort_id") != "PSICO-GEO2027-TRANSITION-ALERTS-V1"
        or len(forecast.get("countries", [])) != N_COUNTRIES
        or alerts.get("2027_outcomes_resolved") != 0):
        raise ValueError("Unexpected 2027 original forecast/issued alert identity")
    rows = forecast["countries"]
    frozen_ids = {r["country_id"] for r in rows}
    if len(frozen_ids) != N_COUNTRIES or any(
        type(v) is not int or v not in (0, 1) for v in outcomes.values()
    ):
        raise ValueError("Future labels must be binary and original cohort unique")
    available = set(outcomes) & frozen_ids
    missing = sorted(frozen_ids - set(outcomes))
    base = {
        "schema": "idealab.psico.geo2027_official_transition_alert_candidate.v1",
        "status": "CANDIDATE_NOT_INDEPENDENTLY_ATTESTED",
        "source_claim": source_claim,
        "source_2027_schema_audit": parse_audit,
        "source_first_complete_release_independently_attested": False,
        "github_issue_first_public_commit": FIRST_ISSUE_COMMIT,
        "original_issue_sha256": ISSUE_SHA,
        "original_forecast_sha256": SOURCE_SHA256,
        "issued_alerts": 15,
        "issued_eligible_country_years": N_COUNTRIES,
        "resolved": len(available),
        "unresolved": len(missing),
        "unresolved_country_ids": missing,
        "extra_unissued_2027_source_ids_ignored": len(set(outcomes)-frozen_ids),
        "2027_outcomes_already_present_at_issue": False,
        "prospective_skill_independently_certified": False,
        "model_retrained_or_probabilities_modified": False,
        "endpoints": None,
        "holm_adjusted_upper_tails": None,
        "interpretation": "Candidate scores require independent verification of FIRST COMPLETE official UCDP 2027 source release, full 196-country denominator and any later revisions; source URL/hash/date are operator claims, NOT notarized provenance.",
    }
    if missing:
        base["status"] = "CANDIDATE_PARTIAL_COVERAGE_NO_SCORES"
        return base
    groups = {
        "entry": scoring_group(rows, alerts, 0, outcomes),
        "resolution": scoring_group(rows, alerts, 1, outcomes),
    }
    base["endpoints"] = groups
    base["holm_adjusted_upper_tails"] = holm_pair({
        k: v["exact_upper_tail_given_observed_transitions"]
        for k, v in groups.items()
    })
    base["status"] = "CANDIDATE_FULL_COVERAGE_STILL_UNCERTIFIED"
    return base


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-zip", required=True)
    parser.add_argument("--official-url", required=True)
    parser.add_argument("--official-sha256", required=True)
    parser.add_argument("--claimed-release-date", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    validate_candidate_source(
        args.official_url, args.official_sha256, args.claimed_release_date
    )
    raw = Path(args.official_zip).read_bytes()
    if sha(raw) != args.official_sha256:
        raise ValueError("Candidate official ZIP does not match declared SHA-256")
    forecast, alerts, manifest = load_authenticated()
    outcomes, parse_audit = parse_future_csv(read_zip(raw))
    report = evaluate(forecast, alerts, outcomes, {
        "url_self_reported": args.official_url,
        "zip_sha256_verified_against_operator_claim": args.official_sha256,
        "claimed_release_date": args.claimed_release_date,
        "release_is_first_complete_independently_verified": False,
    }, parse_audit)
    output = Path(args.output)
    output.write_text(
        json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf8",
    )
    print("GEO2027_ALERT_RESOLUTION_CANDIDATE",
          report["status"], "resolved", report["resolved"],
          "unresolved", report["unresolved"],
          "independently_certified", False)


if __name__ == "__main__":
    main()
