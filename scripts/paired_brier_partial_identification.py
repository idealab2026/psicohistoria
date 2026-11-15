#!/usr/bin/env python3
"""Exact, distribution-free bounds on paired Brier difference with missing labels.

For a fixed, FIRST-ISSUED cohort of N countries and two frozen vectors p,q,
the unknown labels y_i in {0,1} imply a SHARP algebraic identification region
for D = N^{-1} sum [(p_i-y_i)^2 - (q_i-y_i)^2].

Each unresolved i has exactly two possible contributions: d_i(0) and d_i(1).
Thus min/max are the sum of individual min/max contributions, divided by the
ORIGINAL N. No exchangeability, independence, sampling model, confidence
level, p-value, imputation or belief about unobserved outcomes is involved.

At full coverage the region collapses to the observed paired Brier difference.
Do not call these bounds 'confidence intervals', 'prediction intervals',
'bootstrap uncertainty' or 'probabilistic rankings'.
"""
from __future__ import annotations

import math


def sharp_partial_paired_brier(rows, outcomes, primary, reference, *,
                               cohort_size=196):
    """Return sharp full-original-cohort algebraic interval for y_i missing.

    This function accepts ONLY country-issued rows; each row must preserve
    the original country ID and strictly interior first-issued probabilities.
    Actual source provenance authentication belongs to the calling evaluator.
    """
    if (type(cohort_size) is not int or cohort_size<1 or
        not isinstance(rows,list) or len(rows)!=cohort_size or
        not isinstance(outcomes,dict) or
        type(primary) is not str or type(reference) is not str or
        not primary or not reference or primary==reference):
        raise ValueError("Invalid fixed issued cohort or comparison fields")
    ids=set()
    known_sum=0.0
    low=0.0
    high=0.0
    missing=[]
    observed=0
    for row in rows:
        if not isinstance(row,dict):
            raise ValueError("Invalid original issued country record")
        cid=row.get("country_id")
        if (type(cid) not in (int,str) or type(cid) is str and
            (not cid.isdigit() or not 1<=int(cid)<=2000) or
            type(cid) is int and not 1<=cid<=2000 or cid in ids):
            raise ValueError("Invalid or repeated first-issued country identifier")
        ids.add(cid)
        p=row.get(primary)
        q=row.get(reference)
        if (type(p) not in (int,float) or type(q) not in (int,float)
            or not math.isfinite(p) or not math.isfinite(q) or
            not 0<p<1 or not 0<q<1):
            raise ValueError("Invalid original first-issued probability")
        d0=p*p-q*q
        d1=(1-p)*(1-p)-(1-q)*(1-q)
        if cid in outcomes:
            y=outcomes[cid]
            if type(y) is not int or y not in (0,1):
                raise ValueError("Future outcome must be explicitly binary")
            d=d1 if y==1 else d0
            known_sum+=d
            low+=d
            high+=d
            observed+=1
        else:
            missing.append(cid)
            low+=min(d0,d1)
            high+=max(d0,d1)
    # Extra country labels cannot enter the original fixed N denominator.
    for cid,y in outcomes.items():
        if type(cid) not in (int,str) or type(y) is not int or y not in (0,1):
            raise ValueError("Malformed future country outcome record")
    # Avoid implying a zero-width confidence interval on full coverage.
    return {
        "interpretation":"SHARP_FINITE_COHORT_IDENTIFICATION_SET_NOT_CONFIDENCE_INTERVAL",
        "fixed_issued_cohort_n":cohort_size,
        "resolved_country_outcomes":observed,
        "unresolved_country_outcomes":len(missing),
        "unresolved_country_ids":missing,
        "primary_field":primary,
        "reference_field":reference,
        "lower_full_cohort_delta_brier":low/cohort_size,
        "upper_full_cohort_delta_brier":high/cohort_size,
        "observed_full_cohort_delta_brier_if_complete":(
            known_sum/cohort_size if not missing else None),
        "all_unknown_binary_completions_considered":True,
        "sharp_for_each_missing_country_label_free_0_or_1":True,
        "iid_country_assumption":False,
        "bootstrap_resampling_used":False,
        "confidence_level":None,
        "p_value":None,
        "independent_source_attestation_supplied_by_this_calculation":False,
        "prospective_skill_established":False,
        "limitations":(
            "Algebraic extrema across every 0/1 assignment to missing issued "
            "countries. No probability or coverage statement and no skill "
            "validation. Results are conditional on observed labels supplied "
            "by another component, whose official provenance must still be "
            "independently authenticated."
        ),
    }
