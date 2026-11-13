#!/usr/bin/env python3
"""2027 ACD forecast discriminability from FIRST-ISSUED probabilities alone.

For every possible number k=0..32 of recorded ACD 2027 country presences,
compute the SHARP MIN and MAX of secondary-minus-primary mean Brier
over all binary label assignments having exactly k ones. This uses sorted
affine score contributions (not 2**32 enumeration and no event independence).
It does NOT predict k, score 2027, authorize a new primary model or infer
the probability of a future model winning.
"""
from __future__ import annotations

import argparse
import json
import math

import build_2027_prospective_registry as registry

PRIMARY="p_global_recent5"
SECONDARIES=("p_lag1_group","p_country_eb")
TOL=1e-14


def probability(p):
    if type(p) not in (int,float) or not math.isfinite(p) or not 0<p<1:
        raise ValueError("Strict interior probability required")
    return float(p)


def compare_labels(rows, challenger, ones):
    """Explicit binary witness score; other labels are zero, no inferred labels."""
    if challenger not in SECONDARIES:
        raise ValueError("Unregistered original ACD2027 comparator")
    ids={x["country_id"] for x in rows}
    if (len(ids)!=len(rows) or not isinstance(ones,set)
        or not ones.issubset(ids)):
        raise ValueError("Invalid binary witness or duplicate GWNO")
    n=len(rows)
    if n==0:
        raise ValueError("Empty issued cohort")
    return sum((probability(r[challenger])-int(r["country_id"] in ones))**2-
               (probability(r[PRIMARY])-int(r["country_id"] in ones))**2
               for r in rows)/n


def sharp_frontier(rows, challenger):
    """Exact finite binary-label assignment range, CONDITIONAL on k successes.

    For each country, secondary-minus-primary Brier equals
      (q² - p²) - 2 (q-p) y.
    Fixing sum(y)=k, the minimum is attained by the k smallest
    increments -2(q-p), and the maximum by the k largest. This is
    exact with arbitrary outcome dependence: no independent labels needed.
    """
    if challenger not in SECONDARIES:
        raise ValueError("Unregistered original ACD2027 comparator")
    if len(rows)!=32:
        raise ValueError("Exactly 32 first-issued ACD risk countries required")
    ids=[r.get("country_id") for r in rows]
    if any(type(cid) is not int or cid<1 for cid in ids) or len(set(ids))!=32:
        raise ValueError("Original ACD country codes invalid/duplicated")
    deltas=[]
    base=0.0
    gap_sq=0.0
    gap_by_country=[]
    for r in rows:
        p,q=probability(r[PRIMARY]),probability(r[challenger])
        base+=q*q-p*p
        inc=-2*(q-p)
        deltas.append((inc,r["country_id"]))
        sq=(q-p)**2
        gap_sq+=sq
        gap_by_country.append((sq,r["country_id"]))
    n=len(rows)
    # Secondary-minus-primary expected Brier if p are the true marginal
    # probabilities: +avg((q-p)^2). If q is the true marginals: negative.
    # These expectations use linearity only, NOT cross-country independence.
    ascending=sorted(deltas,key=lambda x:(x[0],x[1]))
    descending=sorted(deltas,key=lambda x:(-x[0],x[1]))
    count_cases=[]
    for k in range(n+1):
        lower_ids={cid for _,cid in ascending[:k]}
        upper_ids={cid for _,cid in descending[:k]}
        lower=(base+sum(delta for delta,_ in ascending[:k]))/n
        upper=(base+sum(delta for delta,_ in descending[:k]))/n
        if (lower>upper+TOL or
            abs(compare_labels(rows,challenger,lower_ids)-lower)>TOL or
            abs(compare_labels(rows,challenger,upper_ids)-upper)>TOL):
            raise ValueError("ACD exact k-count frontier or witness mismatch")
        winner=(
            "primary_always_better" if lower>TOL else
            "secondary_always_better" if upper<-TOL else
            "tie_or_outcome_assignment_matters"
        )
        count_cases.append({
            "n_2027_countries_with_acd_record_hypothetical":k,
            "sharp_min_secondary_minus_primary_brier":lower,
            "sharp_max_secondary_minus_primary_brier":upper,
            "winner_fixed_by_count_only":winner,
            # These are hypothetical constructions, not scenario forecasts.
            "min_witness_recorded_country_gwno":sorted(lower_ids),
            "max_witness_recorded_country_gwno":sorted(upper_ids),
        })
    weights=sorted(gap_by_country,key=lambda item:(-item[0],item[1]))
    return {
        "secondary_model":challenger,
        "baseline_primary":PRIMARY,
        "conditional_expected_secondary_minus_primary_if_primary_true_marginals":
            gap_sq/n,
        "conditional_expected_secondary_minus_primary_if_secondary_true_marginals":
            -gap_sq/n,
        "mean_squared_issued_probability_gap":gap_sq/n,
        "largest_single_country_share_of_sum_squared_probability_gaps":
            weights[0][0]/gap_sq if gap_sq else None,
        "five_largest_probability_gap_country_gwno":[cid for _,cid in weights[:5]],
        "n_count_values_always_primary":sum(
            v["winner_fixed_by_count_only"]=="primary_always_better"
            for v in count_cases),
        "n_count_values_always_secondary":sum(
            v["winner_fixed_by_count_only"]=="secondary_always_better"
            for v in count_cases),
        "n_count_values_assignment_matters":sum(
            v["winner_fixed_by_count_only"]=="tie_or_outcome_assignment_matters"
            for v in count_cases),
        "n_hypothetical_binary_outcome_assignments":2**n,
        "k_conditioned_sharp_frontier":count_cases,
    }


def diagnose(docs,manifests):
    all_issued=registry.make_registry(docs,manifests)
    acd=docs["acd"]
    if (all_issued["n_unique_country_endpoint_rows"]!=424
        or all_issued["n_verified_future_2027_outcomes"]!=0
        or acd["2027_outcomes_resolved"]!=0
        or acd["target_year"]!=2027
        or acd["origin_year"]!=2025
        or acd["primary_model"]!=PRIMARY
        or set(acd["secondary_models"])!=set(SECONDARIES)
        or any(r.get("conflict_present_in_origin_2025") is not True
               for r in acd["countries"])):
        raise ValueError("Original prospective issued cohort identity changed")
    rows=acd["countries"]
    result={s:sharp_frontier(rows,s) for s in SECONDARIES}
    # Previously published single-country pivotal study is a separately
    # derived same-risk-set metric; verify the exact 31+1 probabilities.
    if (len([r for r in rows if r["also_active_in_2024"] is False])!=1
        or not any(r["country_id"]==626 and
                   r["also_active_in_2024"] is False for r in rows)):
        raise ValueError("Prior pivotal GWNO 626 source shape no longer holds")
    names={r["country_id"]:r["country"] for r in docs["geo"]["countries"]}
    for v in result.values():
        v["five_largest_probability_gap_country_names"]=[
            names.get(cid) for cid in v["five_largest_probability_gap_country_gwno"]]
    return {
        "schema":"idealab.psico.acd2027_exact_count_conditioned_model_discriminability.v1",
        "status":"PRE_OUTCOME_ALGEBRA_ONLY_NO_OBSERVED_2027_LABELS",
        "2027_labels_used":0,
        "issued_endpoint":"ACD2027 any type3/4 intrastate conflict recorded in 2027 among 2025-active countries",
        "n_issued_country_questions":32,
        "n_issued_country_endpoint_questions_all_cohorts_unchanged":424,
        "source_acd_first_issue_sha256":registry.EXPECTED["acd"][1],
        "source_acd_first_issue_git_commit":registry.EXPECTED["acd"][2],
        "source_all_issued_sources_sha_verified_by":"build_2027_prospective_registry.read_issued",
        "primary_model":PRIMARY,
        "exploratory_comparators":list(SECONDARIES),
        "secondary_minus_primary_sign":"negative favors secondary; positive favors primary",
        "sharp_outcome_count_envelopes":result,
        "decision_contract":{
            "k_is_an_unobserved_hypothetical_count_not_a_prediction":True,
            "no_independence_assumption_for_feasible_envelopes":True,
            "conditional_expected_loss_assumes_hypothetically_true_marginals":True,
            "conditional_expected_loss_requires_no_cross_country_independence":True,
            "first_complete_verified_future_official_source_required_for_observed_scoring":True,
            "existing_official_evaluator":"scripts/evaluate_acd2027_retention_official.py",
            "single_2027_calendar_year_cannot_establish_independent_generalizable_skill":True,
            "no_automatic_model_switch_or_reissue_based_on_any_2027_result":True,
            "any_new_year_requires_new_before_outcome_issued_forecast":True,
            "for_any_future_multi_year_comparison":"precommit endpoints and scoring, verify time of each issue precedes outcomes, evaluate complete country risk sets, inspect year-block and country-cluster sensitivity, prohibit IID country p-values; no unvalidated performance inference",
        },
        "limitations":(
            "Exact Brier sign envelopes exhaust feasible BINARY label assignments "
            "conditional on hypothetical k, not actual observed 2027 results or "
            "distributions over future k. Country-level dependence has no effect "
            "on the algebraic sharp bounds or expected loss under explicitly "
            "hypothetical true marginal probabilities, but invalidates naive "
            "sampling-independence tests. No prospective skill, event count "
            "distribution, independent replication, switching decision or "
            "extra issued forecast is inferred. ACD absence is not peace."
        ),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report")
    parser.add_argument("--summary",action="store_true")
    args=parser.parse_args()
    docs,manifests=registry.read_issued()
    report=diagnose(docs,manifests)
    if args.summary:
        view={k:report[k] for k in (
            "schema","status","2027_labels_used","n_issued_country_questions",
            "source_acd_first_issue_sha256","primary_model",
            "decision_contract","limitations"
        )}
        view["sharp_outcome_count_envelopes"]={
            name:{k:v[k] for k in v if k!="k_conditioned_sharp_frontier"}
            for name,v in report["sharp_outcome_count_envelopes"].items()
        }
        body=registry.canonical(view)
    else:
        body=registry.canonical(report)
    if args.check_report and open(args.check_report,"rb").read()!=body:
        raise ValueError("Published ACD count-discrimination report differs")
    print("ACD2027_EXACT_COUNT_EVIDENCE_BEGIN")
    print(body.decode("utf8"),end="")
    print("ACD2027_EXACT_COUNT_EVIDENCE_END")


if __name__=="__main__":
    main()
