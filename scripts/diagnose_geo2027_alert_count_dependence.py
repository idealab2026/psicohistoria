#!/usr/bin/env python3
"""Pre-outcome joint-count scenarios for the 15 publicly issued GEO-2027 alerts.

Never re-fits, edits or predicts country risk. EXACT marginal 2027 event
probabilities from the already publicly issued 10 entry + 5 resolution alerts.
All dependency models are ILLUSTRATIVE couplings, NOT fitted correlation,
credible intervals or outcome evidence. No country records in output.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from audit_issued_geo2027_transition_alerts import audit as audit_issue
from diagnose_newconf2027_event_count import (
    poisson_binomial, comonotonic_pmf, quantile,
)
from prepare_geo2027_transition_alerts import (
    FORECAST_PATH, MANIFEST_PATH, sha,
)

ALERT_PATH = Path("data/forecast-2027-transition-alerts.json")
ALERT_MANIFEST = Path("data/forecast-2027-transition-alerts-manifest.json")
ALERT_AUDIT = Path("data/forecast-2027-transition-alerts-audit.json")
GENERATOR = Path("scripts/prepare_geo2027_transition_alerts.py")

EXPECTED_ALERT_SHA256 = "309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb"
EXPECTED_FIRST_PUBLIC_COMMIT = "5938db3c93661ce04ed35902b2bdaa68abfb8daa"
WEIGHTS = (0.0, 0.1, 0.25, 1.0)
TARGET_YEAR = 2027


def verify_issued():
    original = FORECAST_PATH.read_bytes()
    source_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf8"))
    alert_raw = ALERT_PATH.read_bytes()
    alert_manifest = json.loads(ALERT_MANIFEST.read_text(encoding="utf8"))
    audit = audit_issue(
        alert_raw, alert_manifest, GENERATOR.read_bytes(),
        original, source_manifest,
    )
    if (sha(alert_raw) != EXPECTED_ALERT_SHA256
        or alert_manifest.get("first_public_issue_commit") !=
           EXPECTED_FIRST_PUBLIC_COMMIT
        or audit != json.loads(ALERT_AUDIT.read_text(encoding="utf8"))
        or audit["outcomes_2027_resolved"] != 0):
        raise ValueError("Frozen first-public 2027 alert issuance invalid")
    issue = json.loads(alert_raw)
    if issue["target_year"] != TARGET_YEAR or issue["2027_outcomes_resolved"] != 0:
        raise ValueError("No future outcomes may be present")
    groups = issue["risk_groups"]
    if groups["0"]["budget"] != 10 or groups["1"]["budget"] != 5:
        raise ValueError("Published 2027 alert budgets changed")
    entries = groups["0"]["selected_countries"]
    resolutions = groups["1"]["selected_countries"]
    if (len(entries), len(resolutions)) != (10, 5):
        raise ValueError("Not the canonical 15 already-issued forecasts")
    p0 = [r["transition_probability_model"] for r in entries]
    p1 = [r["transition_probability_model"] for r in resolutions]
    if any(type(x) not in (int, float) or not math.isfinite(x) or not 0 < x < 1
           for x in p0 + p1):
        raise ValueError("Invalid issued Bernoulli marginal")
    if (abs(sum(p0)-groups["0"]["model_expected_hits_in_selected_alerts"]) > 1e-10
        or abs(sum(p1)-groups["1"]["model_expected_hits_in_selected_alerts"]) > 1e-10):
        raise ValueError("Expected count disagrees with pre-2027 issue")
    return p0, p1


def convolve(left, right):
    if not left or not right:
        raise ValueError("Cannot convolve empty count distributions")
    out = [0.0] * (len(left)+len(right)-1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            out[i+j] += a*b
    return out


def frechet_zero_bounds(probabilities):
    """Sharp unconditional P(no events) bounds with fixed Bernoulli marginals."""
    if not probabilities or any(
        type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1
        for p in probabilities
    ):
        raise ValueError("Nonempty finite Bernoulli marginals required")
    return [
        max(0.0, 1.0 - sum(probabilities)),
        1.0 - max(probabilities),
    ]


def mixture(independent, comonotonic, weight):
    if (len(independent) != len(comonotonic) or type(weight) not in (int, float)
        or not math.isfinite(weight) or not 0 <= weight <= 1):
        raise ValueError("Ill-formed scenario mixture")
    return [(1-weight)*a + weight*b for a, b in zip(independent, comonotonic)]


def describe(pmf):
    total = sum(pmf)
    if (not pmf or abs(total-1) > 1e-10
        or any(not math.isfinite(p) or p < -1e-12 for p in pmf)):
        raise ValueError("Scenario probability mass must normalize")
    mean = sum(k*p for k,p in enumerate(pmf))
    second = sum(k*k*p for k,p in enumerate(pmf))
    return {
        "expected_transitions": mean,
        "variance_transition_count": max(0.0, second-mean*mean),
        "p_zero": pmf[0],
        "p_one_or_more": 1.0 - pmf[0],
        "p_three_or_more": sum(pmf[3:]),
        "central_95pct_model_implied_range": [
            quantile(pmf,.025), quantile(pmf,.975)
        ],
        "full_probability_mass_by_count": pmf,
    }


def diagnose(entry, resolution):
    if len(entry) != 10 or len(resolution) != 5:
        raise ValueError("Must use exactly 10 + 5 first-public 2027 alerts")
    groups = {"entry": entry, "resolution": resolution}
    all_p = entry + resolution
    independent_all = poisson_binomial(all_p)
    common_all = comonotonic_pmf(all_p)
    independent_by_group = {
        k: poisson_binomial(p) for k,p in groups.items()
    }
    common_by_group = {k: comonotonic_pmf(p) for k,p in groups.items()}
    group_common_independent_between_groups = convolve(
        common_by_group["entry"], common_by_group["resolution"]
    )
    if abs(sum(all_p)-sum(k*d for k,d in enumerate(independent_all))) > 1e-10:
        raise ValueError("Independence scenario must preserve original expectation")
    return {
        "schema": "idealab.psico.geo2027_alert_count_dependence_sensitivity.v1",
        "status": "PRE_OUTCOME_UNFITTED_MARGINAL_PRESERVING_SCENARIOS_ONLY",
        "issued_alert_file_sha256": EXPECTED_ALERT_SHA256,
        "first_public_alert_commit": EXPECTED_FIRST_PUBLIC_COMMIT,
        "target_year": TARGET_YEAR,
        "original_2027_alert_count": 15,
        "outcomes_2027_observed": 0,
        "forecast_probabilities_modified": False,
        "assumptions": {
            "independent": "All Bernoulli alert events are mutually independent, an UNTESTED assumption",
            "comonotonic": "All event indicators use a single U~Uniform(0,1) and Yi=1[U<p_i]; exact original marginals, extreme positive dependence",
            "scenario_weight": "Probability that ALL 15 alerts share the common-U regime, otherwise all are independent; mixture weight is NOT estimated correlation",
            "within_group_common": "Entry alerts share U_entry, resolution alerts share independent U_resolution; all original marginals unchanged",
            "frechet": "Sharp marginal-only P(K=0) lower/upper for arbitrary joint dependence, not a fitted interval",
        },
        "risk_groups": {
            k: {
                "n_alerts": len(p),
                "expected_transitions_under_any_coupling": sum(p),
                "frechet_p_zero_bounds": frechet_zero_bounds(p),
                "independent": describe(independent_by_group[k]),
                "comonotonic_common_uniform": describe(common_by_group[k]),
                "dependence_mixture_scenarios": [
                    {"common_regime_weight": w,
                     **describe(mixture(independent_by_group[k],
                                        common_by_group[k],w))}
                    for w in WEIGHTS
                ],
            }
            for k,p in groups.items()
        },
        "joint_15_alerts": {
            "expected_transitions_under_any_coupling": sum(all_p),
            "frechet_p_zero_bounds": frechet_zero_bounds(all_p),
            "all_independent": describe(independent_all),
            "two_group_common_with_independent_group_shocks":
                describe(group_common_independent_between_groups),
            "single_common_uniform_all_15": describe(common_all),
            "global_regime_mixtures": [
                {"common_regime_weight":w,
                 **describe(mixture(independent_all,common_all,w))}
                for w in WEIGHTS
            ],
        },
        "limitations": (
            "These are algebraic distributions CONDITIONAL on 15 frozen marginal "
            "probabilities. No estimation of dependence, predictive interval "
            "coverage, calibration or prospective skill. Common shocks in "
            "real conflicts may be positive, negative, region-specific and "
            "time varying; marginal Frechet bounds are not a joint model. "
            "Entry/resolution mean state-based >=25 deaths threshold, "
            "NOT new conflict onset or end of a war."
        ),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report")
    args=parser.parse_args()
    entry,resolution=verify_issued()
    output=json.dumps(diagnose(entry,resolution),indent=2,
                      ensure_ascii=False,sort_keys=True)+"\n"
    print("GEO2027_ALERT_COUNT_DEPENDENCE_BEGIN")
    print(output,end="")
    print("GEO2027_ALERT_COUNT_DEPENDENCE_END")
    if args.check_report and Path(args.check_report).read_bytes() != output.encode("utf8"):
        raise ValueError("Public alert dependence scenario report changed")


if __name__=="__main__":
    main()
