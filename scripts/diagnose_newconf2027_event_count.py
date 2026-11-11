#!/usr/bin/env python3
"""Pre-outcome, model-implied NEWCONF-2027 event-count distribution.

This is a conditional Poisson-binomial calculation, NOT an empirical
validation, predictive interval with guaranteed coverage, or outcome resolver.
The 196 issued probabilities are read without alteration. Conditional
independence across countries is assumed only for this illustrative scenario.
"""
import argparse
import json
from pathlib import Path


def poisson_binomial(probabilities):
    pmf = [1.0]
    for p in probabilities:
        if not isinstance(p, (int, float)) or isinstance(p, bool) or not 0 <= p <= 1:
            raise ValueError("Expected finite probability in [0,1]")
        next_pmf = [0.0] * (len(pmf) + 1)
        for k, mass in enumerate(pmf):
            next_pmf[k] += mass * (1.0 - p)
            next_pmf[k + 1] += mass * p
        pmf = next_pmf
    return pmf


def quantile(pmf, level):
    running = 0.0
    for k, mass in enumerate(pmf):
        running += mass
        if running >= level - 1e-14:
            return k
    return len(pmf) - 1


def diagnose(path):
    issued = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = issued["countries"]
    ids = [str(row["country_id"]) for row in rows]
    if len(rows) != 196 or len(set(ids)) != 196 or issued.get("forecast_id") != "PSICO-QGEO01-NEWCONF2027-ORIGIN2025-V1":
        raise ValueError("Refusing noncanonical NEWCONF-2027 cohort")
    ps = [row["p_model"] for row in rows]
    pmf = poisson_binomial(ps)
    return {
        "status": "PRE_OUTCOME_MODEL_IMPLIED_ONLY",
        "forecast_id": issued["forecast_id"],
        "countries": len(rows),
        "2027_outcomes_observed": 0,
        "assumption": "conditional independence across country event indicators; shared shocks not modeled",
        "expected_events": sum(ps),
        "variance_events": sum(p * (1 - p) for p in ps),
        "p_zero": pmf[0],
        "p_at_most_one": sum(pmf[:2]),
        "p_at_most_two": sum(pmf[:3]),
        "p_six_or_more": sum(pmf[6:]),
        "model_implied_central_95_count_range": [quantile(pmf, 0.025), quantile(pmf, 0.975)],
        "distinct_probabilities": len(set(ps)),
        "top20_expected_events": sum(sorted(ps, reverse=True)[:20]),
        "note": "Not observed performance or a calibrated uncertainty interval; this cannot prove model skill.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--forecast", default="data/forecast-2027-newconf.json")
    args = parser.parse_args()
    print(json.dumps(diagnose(args.forecast), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
