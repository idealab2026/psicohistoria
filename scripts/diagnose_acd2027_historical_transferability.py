#!/usr/bin/env python3
"""ACD 2027 cohort transferability audit: archived 2021-24 forecasts vs 2025 risk set.

Reconstruct exactly the source-SHA-verified 137 historical ACD country-year
comparisons; compare their support to the 32 already issued 2025-active ACD2027
country GWNO identifiers. This is descriptive retrospective representativeness,
NOT an independent test, future label, reweighting prescription, or forecast.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path

import build_2027_prospective_registry as prospective
import diagnose_acd_retention_country_influence as history
import backtest_ucdp_prio_retention_four_vintages as vintage

ROOT=Path(__file__).resolve().parents[1]
BASELINE=ROOT/"data/ucdp-prio-2021-2024-retention-four-vintage.json"
REPORT=ROOT/"data/acd2027-historical-transferability.json"
MODELS=(history.PRIMARY_BASELINE,)+history.MODELS
YEARS=(2021,2022,2023,2024)
EARLY=(2021,2022)
LATE=(2023,2024)
EPS=1e-11


def score(rows: list[dict]) -> dict:
    """Published model losses plus paired losses, with no IID assumption."""
    if not rows:
        return {
            "n_country_years":0,"n_unique_countries":0,
            "n_recorded_acd_persistence":0,"brier_by_model":None,
            "paired_delta_brier_candidate_minus_global":None,
            "country_equally_weighted_paired_delta":None,
        }
    by_cid=defaultdict(list)
    for row in rows:
        if (type(row["country_id"]) is not int or row["country_id"]<1
            or type(row["target_year"]) is not int or row["target_year"] not in YEARS
            or type(row["observed_acd"]) is not int
            or row["observed_acd"] not in (0,1)
            or set(row["models"])!=set(MODELS)):
            raise ValueError("Invalid historical risk-set row")
        y=row["observed_acd"]
        for m in MODELS:
            p=row["models"][m]
            if type(p) not in (float,int) or not math.isfinite(p) or not 0<p<1:
                raise ValueError("Invalid historical model probability")
        by_cid[row["country_id"]].append(row)
    n=len(rows)
    brier={
        model:sum((r["models"][model]-r["observed_acd"])**2
                  for r in rows)/n
        for model in MODELS
    }
    paired={}
    balanced={}
    for candidate in history.MODELS:
        paired[candidate]=sum(
            history.difference(r["models"][candidate],
                               r["models"][history.PRIMARY_BASELINE],
                               r["observed_acd"]) for r in rows)/n
        country_means=[
            sum(history.difference(r["models"][candidate],
                                   r["models"][history.PRIMARY_BASELINE],
                                   r["observed_acd"]) for r in country_rows)/
            len(country_rows)
            for country_rows in by_cid.values()
        ]
        balanced[candidate]=sum(country_means)/len(country_means)
        if abs(paired[candidate]-(brier[candidate]-brier[history.PRIMARY_BASELINE]))>EPS:
            raise ValueError("Brier paired-metric identity broken")
    return {
        "n_country_years":n,
        "n_unique_countries":len(by_cid),
        "n_recorded_acd_persistence":sum(r["observed_acd"] for r in rows),
        "brier_by_model":brier,
        "paired_delta_brier_candidate_minus_global":paired,
        "country_equally_weighted_paired_delta":balanced,
    }


def assess(rows: list[dict], issued_ids: set[int]) -> dict:
    """Use 2025 issued GWNO membership only, never future 2027 outcomes.

    Temporal halves contain nonoverlapping *rows*, not independent countries.
    2025 status partitions 2021-24 retrospectively; 2025 was not an available
    prospective inclusion criterion at their historical origin dates.
    """
    if (not isinstance(issued_ids,set) or len(issued_ids)!=32 or
        any(type(cid) is not int or cid<1 for cid in issued_ids)):
        raise ValueError("Require original 32 distinct 2025-active country GWNO IDs")
    keys=[(r["country_id"],r["target_year"]) for r in rows]
    if len(keys)!=137 or len(set(keys))!=137 or set(y for _,y in keys)!=set(YEARS):
        raise ValueError("Expected exactly 137 unique original four-vintage rows")
    all_score=score(rows)
    if (all_score["n_recorded_acd_persistence"]!=116 or
        all_score["n_unique_countries"]!=42):
        raise ValueError("Historic source-verified benchmark cohort changed")
    by_cid=defaultdict(list)
    for r in rows:
        by_cid[r["country_id"]].append(r)
    overlap=issued_ids & set(by_cid)
    no_history=issued_ids - set(by_cid)
    history_only=set(by_cid) - issued_ids
    distribution=Counter(len(by_cid[cid]) for cid in issued_ids)
    if sum(k*v for k,v in distribution.items()) != sum(
        r["country_id"] in issued_ids for r in rows
    ):
        raise ValueError("2025 overlap country-year distribution changed")
    subsets={
        "full_historical":rows,
        "early_2021_2022":[r for r in rows if r["target_year"] in EARLY],
        "late_2023_2024":[r for r in rows if r["target_year"] in LATE],
        "issued_2025_cohort_historical":[r for r in rows if r["country_id"] in issued_ids],
        "historical_not_issued_2025":[r for r in rows if r["country_id"] not in issued_ids],
        "issued_2025_early":[r for r in rows
                             if r["country_id"] in issued_ids and r["target_year"] in EARLY],
        "issued_2025_late":[r for r in rows
                            if r["country_id"] in issued_ids and r["target_year"] in LATE],
        "other_historical_early":[r for r in rows
                                  if r["country_id"] not in issued_ids and r["target_year"] in EARLY],
        "other_historical_late":[r for r in rows
                                 if r["country_id"] not in issued_ids and r["target_year"] in LATE],
    }
    by_year={str(y):score([r for r in rows if r["target_year"]==y])
             for y in YEARS}
    block_scores={name:score(part) for name,part in subsets.items()}
    if (sum(block_scores[k]["n_country_years"]
            for k in ("early_2021_2022","late_2023_2024"))!=137
        or sum(block_scores[k]["n_country_years"]
            for k in ("issued_2025_cohort_historical","historical_not_issued_2025"))!=137
        or sum(by_year[str(y)]["n_country_years"] for y in YEARS)!=137):
        raise ValueError("Historical cohort not partitioned exactly")
    # Both groups should be represented in this specific dataset, otherwise
    # no comparison can be interpreted; 2025-only countries are counted but
    # have no historical labels to score.
    if not overlap or not history_only:
        raise ValueError("Expected both in-support and out-of-support 2025 strata")
    return {
        "schema":"idealab.psico.acd2027_historical_cohort_transferability.v1",
        "status":"RETROSPECTIVE_SUPPORT_SHIFT_NO_INDEPENDENT_FORECAST_SKILL",
        "historical_targets":list(YEARS),
        "historical_137_country_year_evaluations":137,
        "historical_116_acd_persistence_positive":116,
        "historical_unique_countries":42,
        "issued_acd2027_2025_origin_active_countries":32,
        "issued_2025_countries_also_scored_historically":len(overlap),
        "issued_2025_countries_without_any_historical_test_row":len(no_history),
        "historical_scored_countries_not_in_issued_2025_cohort":len(history_only),
        "issued_2025_country_ids_without_historical_test_row":sorted(no_history),
        "historical_country_ids_absent_from_issued_2025_cohort":sorted(history_only),
        "issued_2025_country_hist_score_counts":{
            str(n):distribution[n] for n in range(5)
        },
        "fraction_of_issued_2025_countries_with_historical_test_support":
            len(overlap)/len(issued_ids),
        "individual_historical_target_years":by_year,
        "temporal_and_2025_cohort_subsets":block_scores,
        "temporal_halves_share_country_ids":bool(
            {r["country_id"] for r in subsets["early_2021_2022"]} &
            {r["country_id"] for r in subsets["late_2023_2024"]}
        ),
        "2025_membership_used_only_as_posthoc_stratifier":True,
        "no_2027_outcomes_or_probabilities_changed":True,
        "country_balancing_is_diagnostic_not_a_new_2027_scoring_weight":True,
        "limitations":(
            "Historical prediction vectors reconstructed ex post from six "
            "SHA-pinned UCDP/PRIO ACD source editions, not separately issued "
            "at historical origin dates. 2025 origin-active membership is "
            "known only later and creates retrospective survivorship/selection "
            "bias if interpreted as contemporaneous historical evaluation. "
            "Only source-defined active-origin country risk sets are used. "
            "Country-balanced historical differences change the estimand; "
            "neither country weights nor chronological halves are external "
            "validation, independent replication or a 2027 performance "
            "prediction. Country/year geopolitical dependence unmodeled. "
            "No new future labels, no 2027 forecast modification."
        ),
    }


def evaluate() -> dict:
    docs,manifests=prospective.read_issued()
    issued=prospective.make_registry(docs,manifests)
    if (issued["n_unique_country_endpoint_rows"]!=424 or
        issued["n_verified_future_2027_outcomes"]!=0 or
        docs["acd"]["2027_outcomes_resolved"]!=0 or
        docs["acd"]["primary_model"]!=history.PRIMARY_BASELINE):
        raise ValueError("Original issued future cohort not authenticated")
    ids={r["country_id"] for r in docs["acd"]["countries"]}
    if len(ids)!=32 or any(r["conflict_present_in_origin_2025"] is not True
                           for r in docs["acd"]["countries"]):
        raise ValueError("Original issued ACD 2025 cohort changed")
    versions,metadata=vintage.load_sources()
    frozen=json.loads(BASELINE.read_text(encoding="utf8"))
    ledger=history.reconstruct_ledger(versions,metadata,frozen)
    report=assess(ledger,ids)
    for candidate in history.MODELS:
        actual=report["temporal_and_2025_cohort_subsets"]["full_historical"][
            "paired_delta_brier_candidate_minus_global"][candidate]
        expected=frozen["pooled_models"][candidate]["pooled_brier"]-(
            frozen["pooled_models"][history.PRIMARY_BASELINE]["pooled_brier"]
        )
        if abs(actual-expected)>EPS:
            raise ValueError("Historical candidate Brier no longer matches frozen report")
    report["frozen_official_historical_source_sha256_by_version"]=frozen[
        "source_sha256_by_version"]
    report["first_issued_acd2027_sha256"]=prospective.EXPECTED["acd"][1]
    report["first_issued_acd2027_public_commit"]=prospective.EXPECTED["acd"][2]
    report["zero_observed_2027_outcomes_attested"]=True
    return report


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report",metavar="PATH")
    args=parser.parse_args()
    body=json.dumps(evaluate(),indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    if args.check_report and Path(args.check_report).read_bytes()!=body.encode("utf8"):
        raise ValueError("Immutable ACD historical transferability report changed")
    print("ACD2027_HISTORICAL_TRANSFERABILITY_BEGIN")
    print(body,end="")
    print("ACD2027_HISTORICAL_TRANSFERABILITY_END")


if __name__=="__main__":
    main()
