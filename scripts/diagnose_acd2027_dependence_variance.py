#!/usr/bin/env python3
"""Exact dependence sensitivity for FIRST-ISSUED ACD2027 Brier model gaps.

For each HYPOTHETICAL probability-marginal world r=p_primary or r=q_secondary:
  - compute paired Brier mean and variance assuming independent countries;
  - compute the SHARP MAXIMUM variance across ALL joint Bernoulli laws with
    those exact fixed marginal probabilities, using signed comonotonicity;
  - derive an attainable max-variance rank probability, NOT a forecast;
  - for lag1's original 31+1 profile, derive the independent rank-probability
    from its exact Binomial(31,r_other) + Bernoulli(r_pivot) law.
NO actual 2027 labels, NO estimates of real dependence or years, no model change.
"""
from __future__ import annotations

import argparse
import json
import math

import build_2027_prospective_registry as issued
import diagnose_acd2027_exact_count_evidence as frontiers

PRIMARY=frontiers.PRIMARY
SECONDARIES=frontiers.SECONDARIES
EPS=1e-12


def pair_coefficients(rows,secondary):
    """D = Brier(secondary)-Brier(primary) = c + sum(a_i*Y_i)."""
    if secondary not in SECONDARIES or not rows:
        raise ValueError("Unregistered ACD comparator or empty risk cohort")
    ids=[r.get("country_id") for r in rows]
    if (len(set(ids))!=len(ids)
        or any(type(cid) is not int or cid<=0 for cid in ids)):
        raise ValueError("Duplicate or malformed ACD GWNO")
    n=len(rows)
    coeff={}
    c=0.
    for r in rows:
        p=frontiers.probability(r[PRIMARY])
        q=frontiers.probability(r[secondary])
        c+=(q*q-p*p)/n
        coeff[r["country_id"]]=-2*(q-p)/n
    return c,coeff


def rank(d):
    """Interpret a realized secondary-minus-primary Brier difference."""
    if d < -EPS:
        return "secondary_wins"
    if d > EPS:
        return "primary_wins"
    return "tie"


def signed_comonotonic_distribution(coeff,marginals,constant):
    """Attain maximal variance of c+sum a_i Y_i given Bernoulli marginals.

    Use U~Uniform(0,1). For a_i>=0 let Y_i=1[U<r_i], for a_i<0
    let Y_i=1[U>1-r_i]. The signed terms a_i Y_i are all co-monotone:
    every pair attains its Fréchet maximum covariance simultaneously.
    Thus this construction is the exact global maximum variance coupling,
    NOT an estimate of actual country correlation.
    """
    if set(coeff)!=set(marginals) or not coeff:
        raise ValueError("Incompatible hypothetical marginal risk population")
    breaks={0.,1.}
    for cid,a in coeff.items():
        r=frontiers.probability(marginals[cid])
        if type(a) not in (float,int) or not math.isfinite(a):
            raise ValueError("Invalid signed score coefficient")
        breaks.add(r if a>=0 else 1-r)
    points=sorted(breaks)
    atoms=[]
    for lo,hi in zip(points,points[1:]):
        probability=hi-lo
        if probability<=0:
            raise ValueError("Degenerate comonotonic probability interval")
        u=(lo+hi)/2
        present={
            cid for cid,a in coeff.items()
            if (u < marginals[cid] if a>=0 else u > 1-marginals[cid])
        }
        delta=constant+sum(coeff[cid] for cid in present)
        atoms.append({
            "probability_mass":probability,
            "hypothetical_recorded_country_ids":sorted(present),
            "n_hypothetical_2027_acd_presences":len(present),
            "paired_brier_secondary_minus_primary":delta,
            "winner":rank(delta),
        })
    if abs(sum(x["probability_mass"] for x in atoms)-1)>EPS:
        raise ValueError("Constructed dependence probabilities do not sum to one")
    return atoms


def moment_report(rows,secondary,marginal_model):
    """Variance under independence vs sharp maximum, holding marginals fixed.

    A 'true marginal' scenario does NOT imply that original forecasts are
    calibrated or correct; both worlds are explicit counterfactuals.
    """
    if marginal_model not in (PRIMARY,secondary):
        raise ValueError("Hypothetical marginals must be one issued model")
    constant,coeff=pair_coefficients(rows,secondary)
    marginals={r["country_id"]:frontiers.probability(r[marginal_model])
               for r in rows}
    mu=constant+sum(coeff[cid]*r for cid,r in marginals.items())
    variance_indep=sum(a*a*marginals[cid]*(1-marginals[cid])
                       for cid,a in coeff.items())
    atoms=signed_comonotonic_distribution(coeff,marginals,constant)
    mean_aligned=sum(a["probability_mass"]*
                     a["paired_brier_secondary_minus_primary"] for a in atoms)
    variance_max=sum(a["probability_mass"]*
                     (a["paired_brier_secondary_minus_primary"]-mu)**2
                     for a in atoms)
    if (abs(mu-mean_aligned)>EPS
        or variance_indep<0 or variance_max<variance_indep-EPS):
        raise ValueError("Dependence scenario violates paired-score moment identities")
    expected_gap=sum(
        (frontiers.probability(r[secondary])-
         frontiers.probability(r[PRIMARY]))**2 for r in rows
    )/len(rows)
    expected=expected_gap if marginal_model==PRIMARY else -expected_gap
    if abs(mu-expected)>EPS:
        raise ValueError("Hypothetical correct-marginal expected Brier identity broken")
    aligned_probs={
        w:sum(a["probability_mass"] for a in atoms if a["winner"]==w)
        for w in ("primary_wins","secondary_wins","tie")
    }
    return {
        "hypothetical_true_marginal_model":marginal_model,
        "expected_paired_brier_secondary_minus_primary":mu,
        "standard_deviation_if_independent_countries":math.sqrt(variance_indep),
        "standard_deviation_maximum_over_all_dependence_structures":
            math.sqrt(variance_max),
        "variance_if_independent_countries":variance_indep,
        "sharp_maximum_variance_given_exact_marginals":variance_max,
        "variance_amplification_vs_independence":(
            variance_max/variance_indep if variance_indep>EPS*EPS else None
        ),
        "max_variance_coupling_is_attainable":True,
        "max_variance_coupling_probability_primary_wins":
            aligned_probs["primary_wins"],
        "max_variance_coupling_probability_secondary_wins":
            aligned_probs["secondary_wins"],
        "max_variance_coupling_probability_tie":aligned_probs["tie"],
        "max_variance_coupling_atoms":atoms,
        "counterfactual_not_estimated_joint_probabilities":True,
        "observed_2027_labels_used":0,
    }


def independent_lag1_rank(rows,marginal_model):
    """Exact 31+1 Bernoulli-independent *hypothetical* ranking probability.

    Original lag1 2027 vector differs for 1 country only; 31 identical
    (p, q, true marginal r) exposures allow Binomial(31, r) conditioning.
    This avoids Monte Carlo, false IID-inference or huge enumeration.
    """
    if len(rows)!=32 or marginal_model not in (PRIMARY,"p_lag1_group"):
        raise ValueError("Only original 31+1 ACD2027 lag1 scenario is supported")
    changed=[r for r in rows if r.get("also_active_in_2024") is False]
    common=[r for r in rows if r.get("also_active_in_2024") is True]
    if (len(changed)!=1 or len(common)!=31
        or changed[0]["country_id"]!=626
        or any((r[PRIMARY],r["p_lag1_group"],r[marginal_model])!=
               (common[0][PRIMARY],common[0]["p_lag1_group"],
                common[0][marginal_model]) for r in common)):
        raise ValueError("Issued ACD lag1 31+1 country strata changed")
    other_r=frontiers.probability(common[0][marginal_model])
    pivot_r=frontiers.probability(changed[0][marginal_model])
    constant,co=pair_coefficients(rows,"p_lag1_group")
    counts={w:0. for w in ("primary_wins","secondary_wins","tie")}
    witness=[]
    for pivot_presence in (0,1):
        for other_presences in range(32):
            mass=(pivot_r if pivot_presence else 1-pivot_r)*(
                math.comb(31,other_presences)*
                other_r**other_presences*(1-other_r)**(31-other_presences))
            delta=constant + pivot_presence*co[626]+other_presences*co[
                common[0]["country_id"]]
            winner=rank(delta)
            counts[winner]+=mass
            witness.append({
                "pivotal_south_sudan_acd_2027_hypothetical":bool(pivot_presence),
                "other_31_acd2027_presences_hypothetical":other_presences,
                "probability_if_countries_independent":mass,
                "paired_brier_secondary_minus_primary":delta,
                "winner":winner,
            })
    if abs(sum(counts.values())-1)>EPS:
        raise ValueError("Exact independent binary law probabilities do not sum to 1")
    return {
        "assumption":"COUNTRIES_INDEPENDENT_BERNOULLI_HYPOTHETICAL_NOT_VALIDATED",
        "n_exact_independent_binomial_plus_pivot_cells":64,
        "probability_primary_wins_if_independent":counts["primary_wins"],
        "probability_secondary_wins_if_independent":counts["secondary_wins"],
        "probability_tie_if_independent":counts["tie"],
        "all_64_independent_hypothetical_cells":witness,
    }


def diagnose(docs,manifests):
    register=issued.make_registry(docs,manifests)
    acd=docs["acd"]
    if (register["n_unique_country_endpoint_rows"]!=424
        or register["n_verified_future_2027_outcomes"]!=0
        or acd["2027_outcomes_resolved"]!=0
        or acd["target_year"]!=2027
        or acd["primary_model"]!=PRIMARY
        or len(acd["countries"])!=32
        or set(acd["secondary_models"])!=set(SECONDARIES)):
        raise ValueError("Original prospective 2027 issue integrity changed")
    names={r["country_id"]:r["country"] for r in docs["geo"]["countries"]}
    models={}
    for secondary in SECONDARIES:
        scenarios={}
        for marginal_model in (PRIMARY,secondary):
            v=moment_report(acd["countries"],secondary,marginal_model)
            if secondary=="p_lag1_group":
                v["exact_independent_rank_probability"]=independent_lag1_rank(
                    acd["countries"],marginal_model
                )
            scenarios[marginal_model]=v
        models[secondary]={
            "scenarios_by_hypothetically_true_marginals":scenarios,
            "issued_probability_vector_sha256":issued.EXPECTED["acd"][1],
            "first_public_commit":issued.EXPECTED["acd"][2],
            "do_not_interpret_scenario_probabilities_as_empirical_forecast":True,
        }
    return {
        "schema":"idealab.psico.acd2027_extreme_dependence_paired_brier_sensitivity.v1",
        "status":"EX_ANTE_COUNTERFACTUAL_DEPENDENCE_MOMENTS_ZERO_2027_LABELS",
        "source_five_issued_files_and_manifests_sha_checked":True,
        "n_frozen_ACD_issued_country_questions":32,
        "n_frozen_unique_country_endpoint_questions_all_2027":424,
        "year_target":2027,
        "2027_outcomes_used":0,
        "original_primary_model":PRIMARY,
        "models":models,
        "country_names_for_original_cohort":{
            str(r["country_id"]):names[r["country_id"]] for r in acd["countries"]},
        "decision_contract":{
            "max_variance_is_sharp_given_assumed_marginals":True,
            "actual_country_dependence_estimated":False,
            "actual_temporal_dependence_estimated":False,
            "no_2027_empirical_scores_or_event_count_distribution":True,
            "no_iid_country_p_values":True,
            "no_model_reissue_or_automatic_switch":True,
            "a_single_year_2027_is_only_one_joint_country_panel":True,
            "historical_2021_to_2024_target_years_not_independent_validation":
                True,
            "future_dependence_study_requires_multiple_preissued_disjoint_target_year_panels":
                True,
        },
        "limitations":(
            "Both marginal truth worlds are hypothetical and unverified. "
            "The independence scenario and signed-comonotone maximum-variance "
            "coupling are mathematically coherent but do not estimate real "
            "country joint probabilities. Variance maximum is SHARP only "
            "conditional on those given Bernoulli marginal probabilities; "
            "independence is NOT guaranteed to be the minimum variance. "
            "Maximal-variance scenario's winner probability is not a predictive "
            "probability. The 2027 ACD vector is ONE annual joint country panel, "
            "not 32 independent retrospective years. Four adjacent past ACD "
            "target years with recurring countries do not identify a 2027 "
            "copula or time-varying cross-country dependence. No empirical "
            "confidence interval, sample-size claim, IID significance, new "
            "2027 event likelihood, forecast refit, or observational skill."
        ),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--summary",action="store_true")
    parser.add_argument("--check-report")
    args=parser.parse_args()
    docs,manifests=issued.read_issued()
    result=diagnose(docs,manifests)
    if args.summary:
        for model in result["models"].values():
            for scenario in model[
                "scenarios_by_hypothetically_true_marginals"].values():
                scenario.pop("max_variance_coupling_atoms")
                if "exact_independent_rank_probability" in scenario:
                    scenario["exact_independent_rank_probability"].pop(
                        "all_64_independent_hypothetical_cells"
                    )
    body=issued.canonical(result)
    if args.check_report and open(args.check_report,"rb").read()!=body:
        raise ValueError("Published hypothetical dependence sensitivity changed")
    print("ACD2027_DEPENDENCE_SENSITIVITY_BEGIN")
    print(body.decode("utf8"),end="")
    print("ACD2027_DEPENDENCE_SENSITIVITY_END")


if __name__=="__main__":
    main()
