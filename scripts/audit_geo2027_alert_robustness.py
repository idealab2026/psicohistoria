#!/usr/bin/env python3
"""Audit GEO2027 alert membership robustness without changing frozen forecasts.

Run from repository root:
    python3 scripts/audit_geo2027_alert_robustness.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "forecast-2027-ucdp261.json"
EXPECTED_SHA256 = "5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5"
SCENARIOS_PP = (0.157, 0.312, 0.749, 1.0, 5.75)


def calculate() -> dict:
    raw = SOURCE.read_bytes()
    actual_hash = hashlib.sha256(raw).hexdigest()
    if actual_hash != EXPECTED_SHA256:
        raise ValueError(f"Frozen forecast hash mismatch: {actual_hash}")
    countries = json.loads(raw)["countries"]
    if len(countries) != 196 or len({row["country_id"] for row in countries}) != 196:
        raise ValueError("Forecast cohort must contain exactly 196 unique country IDs")
    if any(row["last_observed_state_2025"] not in (0, 1) or not 0 <= row["p_model"] <= 1 for row in countries):
        raise ValueError("Invalid state or probability")

    result = {"forecast_sha256": actual_hash, "total_countries": len(countries), "lists": {}}
    for label, state, k, descending, expected_count in (
        ("entry", 0, 10, True, 162),
        ("exit", 1, 5, False, 34),
    ):
        eligible = [row for row in countries if row["last_observed_state_2025"] == state]
        if len(eligible) != expected_count:
            raise ValueError(f"{label}: expected {expected_count} eligible countries")
        ranked = sorted(
            eligible,
            key=lambda r: ((-1 if descending else 1) * r["p_model"], r["country_id"]),
        )
        selected, first_excluded = ranked[:k], ranked[k]
        boundary = first_excluded["p_model"]
        margins = [
            (row["p_model"] - boundary if descending else boundary - row["p_model"])
            for row in selected
        ]
        if any(margin < 0 for margin in margins):
            raise AssertionError("Invalid sorted boundary")
        scenario_counts = {
            str(epsilon_pp): sum(margin * 100 > 2 * epsilon_pp for margin in margins)
            for epsilon_pp in SCENARIOS_PP
        }
        result["lists"][label] = {
            "eligible": len(eligible),
            "selection_size": k,
            "first_excluded": {
                "country": first_excluded["country"],
                "p_model": boundary,
            },
            "boundary_gap_pp": 100 * margins[-1],
            "selection": [
                {"country": row["country"], "country_id": row["country_id"],
                 "p_model": row["p_model"], "margin_pp": 100 * margin}
                for row, margin in zip(selected, margins)
            ],
            "guaranteed_members_by_epsilon_pp": scenario_counts,
        }
    expected_entries = [10, 10, 7, 7, 2]
    expected_exits = [5, 5, 5, 3, 1]
    for i, epsilon in enumerate(SCENARIOS_PP):
        key = str(epsilon)
        got = (
            result["lists"]["entry"]["guaranteed_members_by_epsilon_pp"][key],
            result["lists"]["exit"]["guaranteed_members_by_epsilon_pp"][key],
        )
        if got != (expected_entries[i], expected_exits[i]):
            raise AssertionError(f"Unexpected scenario {epsilon}: {got}")
    return result


if __name__ == "__main__":
    print(json.dumps(calculate(), ensure_ascii=False, indent=2))
