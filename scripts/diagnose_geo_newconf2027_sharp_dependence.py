#!/usr/bin/env python3
"""Pre-outcome GEO2027 / NEWCONF2027 country-dependence Brier comparisons.

Entirely from FIRST-ISSUED SHA-pinned 2027 probability vectors (0 outcomes).
For each separate endpoint, paired Brier difference is affine in 196
hypothetical Bernoulli labels. Compute exact variance under the illustrative
independent marginal world and the SHARP maximum across arbitrary Bernoulli
couplings preserving those SAME marginals (signed Frechet comonotone). Worlds
where either one of the two issued vectors is "true" are counterfactuals.
NO pooling GEO and NEWCONF Brier, NO inferred real country/endpoint
correlations, NO new forecast, NO real 2027 observed outcomes.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import build_2027_prospective_registry as issued
from diagnose_acd2027_dependence_variance import signed_comonotonic_distribution
from diagnose_acd2027_exact_count_evidence import probability

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo-newconf2027-sharp-dependence.json"
EPS=1e-11
SPEC={
    "GEO2027":{
        "n":196,
        "primary":"p_model",
        "comparators":(
            "p_global_markov",
            "p_shadow_exploratorio",
            "p_baseline_global_5y_archival_diagnostic_only",
        ),
    },
    "NEWCONF2027":{
        "n":196,
        "primary":"p_model",
        "comparators":("p_baseline_global_5y",),
    },
}


def paired_moments(rows: list[dict], marginal_model: str) -> dict:
    """One endpoint; fixed country IDs and p/q. Exact sharp variance.

    rows: {country_id: int,p_primary: float,p_comparator: float}
    marginal_model: 'primary' OR 'comparator', the explicitly assumed true
    Bernoulli marginal vector. These are NOT verified real probabilities.
    """
    if not isinstance(rows,list) or len(rows)<2:
        raise ValueError("Need same-endpoint country question panel")
    if marginal_model not in ("primary","comparator"):
        raise ValueError("Unregistered hypothetical truth-world")
    seen=set(); coeff={}; marginals={}; const=0.; gaps=0.
    n=len(rows)
    for row in rows:
        cid=row.get("country_id")
        if type(cid) is not int or cid<1 or cid in seen:
            raise ValueError("Duplicated or invalid GWNO")
        seen.add(cid)
        p,q=probability(row["p_primary"]),probability(row["p_comparator"])
        const+=(q*q-p*p)/n
        coeff[cid]=-2*(q-p)/n
        marginals[cid]=p if marginal_model=="primary" else q
        gaps+=(q-p)**2/n
    mean=const+sum(coeff[cid]*marginals[cid] for cid in coeff)
    expected=+gaps if marginal_model=="primary" else -gaps
    if abs(mean-expected)>EPS:
        raise ValueError("Marginal mean Brier identity broken")
    var_indep=sum(coeff[cid]**2*r*(1-r) for cid,r in marginals.items())
    atoms=signed_comonotonic_distribution(coeff,marginals,const)
    mu_extreme=sum(a["probability_mass"]*a["paired_brier_secondary_minus_primary"]
                   for a in atoms)
    var_max=sum(a["probability_mass"]*
                (a["paired_brier_secondary_minus_primary"]-mean)**2
                for a in atoms)
    if (abs(mu_extreme-mean)>EPS or var_indep<0 or
        var_max < var_indep-EPS or
        abs(sum(a["probability_mass"] for a in atoms)-1)>EPS):
        raise ValueError("Frechet maximum coupling or mean identity broken")
    # If q==p on every country, both variances are zero and no winner exists.
    sign_rank={
        "primary":sum(a["probability_mass"] for a in atoms
                      if a["paired_brier_secondary_minus_primary"]>EPS),
        "comparator":sum(a["probability_mass"] for a in atoms
                         if a["paired_brier_secondary_minus_primary"]< -EPS),
        "tie":sum(a["probability_mass"] for a in atoms
                  if abs(a["paired_brier_secondary_minus_primary"])<=EPS),
    }
    return {
        "hypothetical_true_marginal_vector":marginal_model,
        "mean_paired_brier_comparator_minus_primary":mean,
        "hypothetical_issued_model_mse_gap":gaps,
        "variance_under_independent_bernoulli_countries":var_indep,
        "sharp_max_variance_under_arbitrary_joint_bernoulli_dependence":var_max,
        "standard_deviation_if_independent":math.sqrt(var_indep),
        "sharp_max_standard_deviation":math.sqrt(var_max),
        "variance_multiplier_over_independence":
            var_max/var_indep if var_indep>EPS*EPS else None,
        "max_variance_coupling_primary_win_probability_conditional_only":
            sign_rank["primary"],
        "max_variance_coupling_comparator_win_probability_conditional_only":
            sign_rank["comparator"],
        "max_variance_coupling_tie_probability_conditional_only":
            sign_rank["tie"],
        "max_variance_coupling_atom_count":len(atoms),
        "cross_country_independence_estimated":False,
        "real_world_joint_distribution_inferred":False,
        "confidence_or_significance_test_performed":False,
        "2027_outcomes_used":0,
    }


def analyze(docs: dict, manifests: dict) -> dict:
    ledger=issued.make_registry(docs,manifests)
    if (ledger["n_unique_country_endpoint_rows"]!=424 or
        ledger["n_verified_future_2027_outcomes"]!=0 or
        ledger["observational_skill_demonstrated"] is not False):
        raise ValueError("Frozen future issue registry altered or resolved")
    registry_by_cohort={name:[] for name in SPEC}
    for record in ledger["rows"]:
        if record["cohort"] in registry_by_cohort:
            if (record["observed_2027"] is not None or
                record["resolved_2027"] is not False or
                record["certified_result"] is not False):
                raise ValueError("2027 actual observation not allowed")
            registry_by_cohort[record["cohort"]].append(record)
    names={r["country_id"]:r["country"] for r in docs["geo"]["countries"]}
    geo_raw={r["country_id"]:r for r in docs["geo"]["countries"]}
    if len(geo_raw)!=196 or set(names)!=set(geo_raw):
        raise ValueError("GEO first-issued crosswalk incomplete")
    results={}
    for cohort,contract in SPEC.items():
        records=registry_by_cohort[cohort]
        if (len(records)!=contract["n"] or
            len({r["country_id"] for r in records})!=contract["n"] or
            any(set(r["p_secondary"])!=
                ({"p_global_markov","p_shadow_exploratorio"} if cohort=="GEO2027"
                 else {"p_baseline_global_5y"}) for r in records)):
            raise ValueError("Issued country/comparator cohort mismatch")
        comparisons={}
        for comparator in contract["comparators"]:
            comparison_rows=[]
            for row in records:
                cid=row["country_id"]
                if comparator=="p_baseline_global_5y_archival_diagnostic_only":
                    if cohort!="GEO2027":
                        raise ValueError("Incorrect archival diagnostic endpoint")
                    q=geo_raw[cid]["p_baseline_global_5y"]
                else:
                    q=row["p_secondary"][comparator]
                comparison_rows.append({
                    "country_id":cid,"p_primary":row["p_primary"],
                    "p_comparator":q,
                })
            gap_sq=sorted([
                ((r["p_primary"]-r["p_comparator"])**2,r["country_id"])
                for r in comparison_rows
            ],key=lambda x:(-x[0],x[1]))
            gtotal=sum(v for v,_ in gap_sq)
            report={
                "comparison_primary":contract["primary"],
                "comparison_secondary":comparator,
                "archival_only_not_issued_as_registered_comparator":
                    comparator.endswith("_archival_diagnostic_only"),
                "n_same_endpoint_issued_country_questions":len(comparison_rows),
                "sum_first_issued_primary_probabilities":
                    sum(x["p_primary"] for x in comparison_rows),
                "sum_first_issued_comparator_probabilities":
                    sum(x["p_comparator"] for x in comparison_rows),
                "largest_single_country_share_of_squared_probability_gap":
                    gap_sq[0][0]/gtotal if gtotal else None,
                "top_three_country_id_discrepancies":[
                    {"gwno":cid,"country":names[cid],
                     "share_of_squared_gap":v/gtotal if gtotal else None}
                    for v,cid in gap_sq[:3]
                ],
                "hypothetical_marginal_worlds":{
                    world:paired_moments(comparison_rows,world)
                    for world in ("primary","comparator")
                },
            }
            comparisons[comparator]=report
        results[cohort]={
            "endpoint":ledger["cohorts"][cohort]["question"],
            "n_original_issued_country_questions":contract["n"],
            "first_issued_forecast_sha256":issued.EXPECTED[
                "geo" if cohort=="GEO2027" else "newconf"][1],
            "first_issued_forecast_commit":issued.EXPECTED[
                "geo" if cohort=="GEO2027" else "newconf"][2],
            "comparisons":comparisons,
        }
    return {
        "schema":"idealab.psico.geo_newconf2027_sharp_dependence_paired_brier.v1",
        "status":"PRE_OUTCOME_COUNTERFACTUAL_DEPENDENCE_BOUNDS_NOT_EMPIRICAL_SKILL",
        "n_distinct_endpoints_analyzed":2,
        "n_original_issued_country_endpoint_questions_all_three_cohorts":424,
        "n_distinct_country_questions_in_each_endpoint":196,
        "original_2027_labels_observed":0,
        "all_five_original_2027_issues_and_manifests_sha_checked":True,
        "origin_year_last_observed":2025,
        "target_year":2027,
        "GEO_and_NEWCONF_scores_not_pooled_or_compared_across_endpoints":True,
        "underlying_country_years_overlap_across_endpoints":True,
        "GEO_alerts_and_shadow_are_not_additional_independent_outcome_questions":True,
        "per_endpoint":results,
        "decision_contract":{
            "primary_issued_probabilities_and_model_choices_unchanged":True,
            "real_joint_country_correlation_estimated":False,
            "real_joint_cross_endpoint_correlation_estimated":False,
            "temporal_dependency_or_skill_inferred":False,
            "sharp_upper_variance_bound_requires_hypothetically_true_marginals":True,
            "independence_is_not_a_lower_variance_bound":True,
            "max_variance_coupling_winner_probabilities_are_not_forecasts":True,
            "never_pool_distinct_endpoints_to_claim_effective_n_424":True,
            "do_not_auto_promote_exploratory_secondary_models":True,
            "first_complete_independently_certified_2027_official_release_required":
                True,
        },
        "limitations":(
            "The Bernoulli world assumes either first-issued primary or first-"
            "issued comparator probabilities are the TRUE marginals, which is "
            "not empirically established. Independence and signed-comonotone "
            "Frechet maximum-variance couplings preserve the chosen marginals "
            "but do not estimate geopolitical dependence. The attained variance "
            "maximum is sharp conditional on a chosen marginal vector, not "
            "an interval or distribution for real 2027 scores. Independent "
            "variance is not generally a sharp minimum. Joint GEO+NEWCONF "
            "dependence is NOT modeled; their endpoints differ, and their "
            "196 overlapping GWNOs are not 392 independent events. No true "
            "2027 outcome, source completeness, significance test, confidence "
            "interval, new forecast or model reissue is asserted."
        ),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--summary",action="store_true")
    parser.add_argument("--check-report")
    args=parser.parse_args()
    docs,manifests=issued.read_issued()
    report=analyze(docs,manifests)
    body=issued.canonical(report)
    if args.check_report and Path(args.check_report).read_bytes()!=body:
        raise ValueError("Pinned GEO+NEWCONF dependence diagnostic changed")
    print("GEO_NEWCONF2027_SHARP_DEPENDENCE_BEGIN")
    print(body.decode(),end="")
    print("GEO_NEWCONF2027_SHARP_DEPENDENCE_END")


if __name__=="__main__":
    main()
