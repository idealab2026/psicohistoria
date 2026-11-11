#!/usr/bin/env python3
"""Historical GEO country transition COUNT dispersion, with strict vintage labels.

Reference: 12 rolling target years 2012..2023 from SHA-pinned, revised UCDP
26.1. No origin-year as-of attestation. Two *separate-source* target years
2024/25 use 23.1->25.1 and 24.1->26.1, respectively, with immutable hashes
and no future training leakage. Neither sample identifies structural country
correlation or 2027 prospective performance; they diagnose how fragile the
independent-Bernoulli aggregate assumption would be IF marginals were calibrated.

No individual country outcomes or individual probabilities are printed.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from backtest_archived_country_vintages import (
    SOURCES, fetch_archives,
)
from backtest_statebased_2027_spec import _annual_frame, from_zip
from diagnose_geo2027_transition_skill import make_holdout_rows
from forecast_2027_statebased import download_official
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256, sha

REVISED_TARGET_YEARS = tuple(range(2012, 2024))
SEPARATED_TARGET_YEARS = (2024, 2025)
EXPECTED_SEPARATED_COUNTRY_YEARS = 392
EXPECTED_SEPARATED_EVENTS = 69
MIN_N = 15


def group_year(rows, year, state, probability_field="p_model"):
    """Observed count vs *conditional independent model* expectation/variance.

    This is a COUNT-RESIDUAL diagnostic, NOT a correlation estimate.
    """
    if state not in (0, 1) or not (2012 <= year <= 2025):
        raise ValueError("Unexpected historical target year or origin state")
    if probability_field not in ("p_model", "p_global_markov"):
        raise ValueError("Unknown frozen model comparator")
    subset = [r for r in rows if r["target_year"] == year and
              r["origin_state"] == state]
    if len(subset) < MIN_N or len({r["country_id"] for r in subset}) != len(subset):
        raise ValueError("Too few or duplicated historical country-year outcomes")
    expected = var = 0.0
    observed = 0
    for row in subset:
        outcome = row["outcome"]
        if type(outcome) is not int or outcome not in (0, 1):
            raise ValueError("Unresolved outcome cannot become a negative")
        if row["origin_state"] != state:
            raise ValueError("Mixed origin strata")
        p = row[probability_field]
        if type(p) not in (int, float) or not math.isfinite(p) or not 0 < p < 1:
            raise ValueError("Invalid origin-only prediction")
        q = p if state == 0 else 1-p
        observed += int(outcome != state)
        expected += q
        var += q*(1-q)
    if var <= 0:
        raise ValueError("Independent-count model has zero variance")
    delta = observed-expected
    return {
        "target_year": year,
        "origin_state": state,
        "n": len(subset),
        "observed_transitions": observed,
        "expected_transitions_given_original_model": expected,
        "variance_under_country_independence": var,
        "count_residual": delta,
        "normalized_count_residual": delta / math.sqrt(var),
        "count_pearson_contribution": delta*delta/var,
        "observed_transition_rate": observed/len(subset),
        "mean_forecast_transition_probability": expected/len(subset),
    }


def panel(rows, years):
    years = tuple(years)
    if (not years or len(set(years)) != len(years)
        or any(y not in (*REVISED_TARGET_YEARS, *SEPARATED_TARGET_YEARS)
               for y in years)):
        raise ValueError("Invalid time panel")
    result = {}
    for s in (0, 1):
        annual = [group_year(rows, y, s) for y in years]
        reference = [group_year(rows, y, s, "p_global_markov") for y in years]
        n = sum(x["n"] for x in annual)
        observed = sum(x["observed_transitions"] for x in annual)
        expected = sum(x["expected_transitions_given_original_model"] for x in annual)
        variance = sum(x["variance_under_country_independence"] for x in annual)
        pearson = sum(x["count_pearson_contribution"] for x in annual)
        ref_pearson = sum(x["count_pearson_contribution"] for x in reference)
        if any(a["n"] != b["n"] or a["observed_transitions"] != b["observed_transitions"]
               for a,b in zip(annual,reference)):
            raise ValueError("Comparators must evaluate IDENTICAL cohorts")
        result[str(s)] = {
            "n_country_years": n,
            "number_of_target_years": len(years),
            "observed_transitions": observed,
            "expected_model_transitions": expected,
            "expected_global_markov_transitions": sum(
                x["expected_transitions_given_original_model"] for x in reference
            ),
            "observed_minus_expected": observed-expected,
            "independence_variance_sum_by_year": variance,
            "pearson_dispersion_ratio_model": pearson/len(years),
            "pearson_dispersion_ratio_global_markov": ref_pearson/len(years),
            "yearly_aggregate_count_residuals": annual,
            "reference_yearly_aggregate_count_residuals": reference,
        }
    return result


def revised_reference(records):
    if not records or max(max(h) for h in records.values()) != 2025:
        raise ValueError("Historical 26.1 source has unexpected final year")
    predictions=[]
    for target in REVISED_TARGET_YEARS:
        origin=target-2
        frame,info=_annual_frame(records,origin)
        if (info["target_year"] != target or info["origin_cutoff"] != origin or
            len(frame)<175):
            raise ValueError("Rolling-origin fixed 2-year specification changed")
        for r in frame:
            cid=r["country_id"]
            if records.get(cid,{}).get(origin) not in (0,1) or (
                records[cid].get(target) != r["outcome"]
            ):
                raise ValueError("Origin/target state missing in revised source")
            predictions.append({**r,"origin_state":records[cid][origin]})
    if sorted({r["target_year"] for r in predictions}) != list(REVISED_TARGET_YEARS):
        raise ValueError("Incomplete rolling retrospective years")
    return predictions


def diagnose(revised_rows, historical_rows, source_hashes):
    if (len(historical_rows) != EXPECTED_SEPARATED_COUNTRY_YEARS
        or sum(r["outcome"] for r in historical_rows) != EXPECTED_SEPARATED_EVENTS
        or sorted({r["target_year"] for r in historical_rows}) !=
           list(SEPARATED_TARGET_YEARS)):
        raise ValueError("Source separated 2024/25 holdout changed")
    if (set(source_hashes) != set(SOURCES)
        or any(source_hashes[v] != SOURCES[v]["sha256"] for v in SOURCES)):
        raise ValueError("Historical UCDP official source SHA-256 mismatch")
    if sorted({r["target_year"] for r in revised_rows}) != list(REVISED_TARGET_YEARS):
        raise ValueError("Rolling origin years changed")
    if any(len({r["country_id"] for r in revised_rows if r["target_year"]==year})
           <175 for year in REVISED_TARGET_YEARS):
        raise ValueError("Not enough rolling-country exposure")
    train=panel(revised_rows,REVISED_TARGET_YEARS)
    external=panel(historical_rows,SEPARATED_TARGET_YEARS)
    return {
        "schema":"idealab.psico.geo2027_historical_count_dispersion.v1",
        "status":"EX_POST_DESCRIPTIVE_NON_IDENTIFYING_NOT_PROSPECTIVE",
        "definition":"Change of binary state-based violence threshold >=25 annual deaths from origin t-2 to target year t, NOT newconf/onset2 or peace",
        "rolling_origin_reference_years":list(REVISED_TARGET_YEARS),
        "separate_release_target_years":list(SEPARATED_TARGET_YEARS),
        "source_rolling_revised_version":"26.1 (historical labels revised through 2025, available in 2026; NOT original as-of editions)",
        "source_rolling_sha256":SOURCES["26.1"]["sha256"],
        "cross_release_source_sha256":{v:source_hashes[v] for v in sorted(source_hashes)},
        "rolling_origin_12_year_count_diagnostics":train,
        "cross_release_2_year_count_diagnostics":external,
        "source_release_dates_independently_notarized":False,
        "model_parameters_changed":False,
        "2027_forecast_and_alerts_changed":False,
        "2027_outcomes_observed":0,
        "structural_cross_country_correlation_identified":False,
        "independent_forecast_skill_demonstrated":False,
        "limitations":(
            "Dispersion ratio = sum over years of (observed_count-expected_count)^2/"
            "independent-Bernoulli count variance, divided by number of years. "
            "A value above 1 can arise from wrong marginals, temporal trends, "
            "country dependence, revisions, or common geopolitical shocks. "
            "It cannot identify pairwise correlation. Twelve years of REVISED "
            "labels are not independently issued forecast vintages; only two "
            "later years use separate UCDP outcome editions. Overlapping two-year "
            "horizons and shared countries preclude iid significance tests."
        ),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report")
    args=parser.parse_args()
    original=FORECAST_PATH.read_bytes()
    if sha(original) != SOURCE_SHA256:
        raise ValueError("Original publicly issued GEO2027 source was changed")
    from build_official_countries import PINNED_SOURCE_SHA256
    raw=download_official()
    if sha(raw) != PINNED_SOURCE_SHA256:
        raise ValueError("UCDP 26.1 input source hash changed")
    records,_=from_zip(raw)
    archives,metadata=fetch_archives()
    report=diagnose(revised_reference(records),make_holdout_rows(archives),
                    {v:meta["sha256"] for v,meta in metadata.items()})
    body=json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    print("GEO2027_HISTORICAL_COUNT_DISPERSION_BEGIN")
    print(body,end="")
    print("GEO2027_HISTORICAL_COUNT_DISPERSION_END")
    if args.check_report and Path(args.check_report).read_bytes()!=body.encode("utf8"):
        raise ValueError("Pinned-source historical count dispersion report mismatch")


if __name__=="__main__":
    main()
