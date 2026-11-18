#!/usr/bin/env python3
"""GEO H2: full four-state editorial-observation kernel and latent-state bounds.

The official UCDP country-year editorial transition A(version v)->B(v+1)
is observable; the latent real conflict state is *not* identified by
sequential revisions of the same underlying data source. We therefore:
 - train a four-state source-revision kernel on 23.1->24.1 and 24.1->25.1,
   only country-years <=2021, with fixed Dirichlet(0.5) per origin row;
 - evaluate prediction of the *later recorded category*, not truth,
   on reserved 25.1->26.1 (plus calendar strata);
 - document a fully unrestricted partial-identification interval and a
   separately assumed 0..10% mass on adjacent 0/1 initial state;
 - issue a distinct UNSCORED 2027 shadow using the frozen editorial kernel
   and unchanged original H2 4-state transition dynamics.
No 2027/2028 original issued probability vector is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit as audit_issued,
)
from backtest_archived_country_vintages import SOURCES
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD, EXPECTED_ROWS, VERSION_ORDER, intensity_state, parse_counts,
)
from experiment_geo_h2_empirical_revision_rate_shadow import conditional_h2
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
ANCHOR_EDITORIAL=ROOT/"data/geo-h2-empirical-origin-revision-rate-2027-shadow.json"
ANCHOR_FIXED10=ROOT/"data/geo-h2-origin-state-10pct-uncertainty-shadow.json"
OUTPUT=ROOT/"data/geo-h2-fourstate-observation-kernel-latent-bounds-2027.json"
TRAIN_PAIRS=(("23.1","24.1"),("24.1","25.1"))
HOLDOUT_PAIR=("25.1","26.1")
STATE_COUNT=4
TRAIN_CUTOFF=2021
N_COUNTRIES=196
N_TRAIN=199
DIRICHLET=.5
MAX_ADJACENT_LATENT_MASS=.10
FORECAST_ORIGIN=2025
TARGET_YEAR=2027
EPS=1e-11


def pair_confusion(old,new,cutoff=TRAIN_CUTOFF,year_min=None):
    """Compare equal source-country-year panels; zero is NOT imputed."""
    if set(old)!=set(new) or len(old)!=N_TRAIN:
        raise ValueError("Source country-universe mismatch")
    matrix=[[0]*STATE_COUNT for _ in range(STATE_COUNT)]
    edited=[]
    for cid in sorted(old):
        first={yr:d for yr,d in old[cid].items()
               if yr<=cutoff and (year_min is None or yr>=year_min)}
        last={yr:d for yr,d in new[cid].items()
              if yr<=cutoff and (year_min is None or yr>=year_min)}
        if set(first)!=set(last):
            raise ValueError("Cannot compare missing source country-year as zero")
        for year,a in sorted(first.items()):
            b=last[year]
            s,t=intensity_state(a),intensity_state(b)
            matrix[s][t]+=1
            if s!=t:
                edited.append({"GWNO":cid,"year":year,
                    "state_earlier":s,"state_later":t,
                    "fatalities_earlier":a,"fatalities_later":b})
    return matrix,edited


def aggregate_matrices(matrices):
    if not matrices or any(len(x)!=STATE_COUNT or
                           any(len(r)!=STATE_COUNT for r in x) for x in matrices):
        raise ValueError("Expected square four-state source matrices")
    return [[sum(m[i][j] for m in matrices) for j in range(STATE_COUNT)]
            for i in range(STATE_COUNT)]


def posterior_kernel(counts):
    """Smoothing fixed before holdout, not calibrated to H2 outcomes."""
    if (len(counts)!=STATE_COUNT or
        any(len(r)!=STATE_COUNT or
            any(type(v) is not int or v<0 for v in r) for r in counts)):
        raise ValueError("Invalid recorded category confusion")
    if any(sum(row)<10 for row in counts):
        raise ValueError("Insufficient exposure in a recorded intensity class")
    out=[[(c+DIRICHLET)/(sum(row)+DIRICHLET*STATE_COUNT)
          for c in row] for row in counts]
    if any(not math.isclose(sum(row),1.,abs_tol=1e-13,rel_tol=0)
           for row in out):
        raise AssertionError("Editorial kernel is not stochastic")
    return out


def evaluate_holdout(counts,kernel):
    """Proper scores for later *recorded* labels; not latent truth."""
    n=sum(sum(row) for row in counts)
    if n<=0:
        raise ValueError("No reserved source transitions")
    raw_logloss=0.
    raw_brier=0.
    state_detail=[]
    for s,row in enumerate(counts):
        nr=sum(row)
        pred=kernel[s]
        if nr==0:
            raise ValueError("Reserved source has no exposure for class")
        row_logloss=-sum(row[t]*math.log(pred[t]) for t in range(STATE_COUNT))/nr
        row_brier=(sum(v*v for v in pred)+
                   sum(row[t]*(1-2*pred[t]) for t in range(STATE_COUNT))/nr)
        raw_logloss+=nr*row_logloss
        raw_brier+=nr*row_brier
        state_detail.append({
            "recorded_state":s,
            "holdout_exposures":nr,
            "holdout_unchanged":row[s],
            "holdout_category_changes":nr-row[s],
            "heldout_change_rate":(nr-row[s])/nr,
            "estimated_change_rate":1-pred[s],
            "recorded_next_edition_logloss":row_logloss,
            "recorded_next_edition_multiclass_brier":row_brier,
        })
    return {
        "country_year_exposures":n,
        "heldout_category_changes":n-sum(counts[s][s] for s in range(STATE_COUNT)),
        "heldout_category_change_rate":
            (n-sum(counts[s][s] for s in range(STATE_COUNT)))/n,
        "mean_multiclass_logloss_next_recording":raw_logloss/n,
        "mean_multiclass_brier_next_recording":raw_brier/n,
        "by_recorded_state":state_detail,
    }


def latent_bounds(conditional,recorded,max_mass=MAX_ADJACENT_LATENT_MASS):
    """Partial identification: T unobserved; bounds require assumptions.

    Unrestricted true initial state can be ANY of 4 states, giving
    [min f(s),max f(s)]; 0..10% on adjacent state for recorded 0/1
    gives a smaller *assumption-conditional* interval, not data-derived.
    """
    if (len(conditional)!=STATE_COUNT or
        not all(0<=p<=1 and math.isfinite(p) for p in conditional) or
        recorded not in range(STATE_COUNT)
        or not 0<=max_mass<=1):
        raise ValueError("Invalid conditional H2 latent-state scenario")
    hard=conditional[recorded]
    noassumption=[min(conditional),max(conditional)]
    if recorded in (0,1):
        edge=(1-max_mass)*hard+max_mass*conditional[1-recorded]
        bounded=[min(hard,edge),max(hard,edge)]
    else:
        bounded=[hard,hard]  # this narrower scenario assumes no errors for 2/3
    if not (noassumption[0]<=bounded[0]+1e-12 and
            bounded[1]<=noassumption[1]+1e-12):
        raise AssertionError("Conditional bound not within unrestricted bounds")
    return noassumption,bounded


def vintage_sequence_diagnostics(data,cutoff=TRAIN_CUTOFF):
    """Four successive observations of same country-year; no ground truth."""
    if any(set(data[v])!=set(data["23.1"]) for v in VERSION_ORDER):
        raise ValueError("Official country roster changed")
    counts={"observed_country_year_n":0,"ever_changed_four_state_n":0,
            "first_and_last_disagree_n":0,
            "consecutive_reversal_events_n":0,
            "middle_different_then_returned_to_first_n":0,
            "stable_across_all_four_n":0}
    for cid in sorted(data["23.1"]):
        years={y for y in data["23.1"][cid] if y<=cutoff}
        if any({y for y in data[v][cid] if y<=cutoff}!=years
               for v in VERSION_ORDER):
            raise ValueError("Four editions have incompatible matched year panels")
        for y in sorted(years):
            states=[intensity_state(data[v][cid][y]) for v in VERSION_ORDER]
            counts["observed_country_year_n"]+=1
            changed=len(set(states))>1
            counts["ever_changed_four_state_n"]+=int(changed)
            counts["stable_across_all_four_n"]+=int(not changed)
            counts["first_and_last_disagree_n"]+=int(states[0]!=states[-1])
            counts["middle_different_then_returned_to_first_n"]+=int(
                states[0]!=states[1] and states[0]==states[2])
            counts["consecutive_reversal_events_n"]+=sum(
                states[i]==states[i+2] and states[i]!=states[i+1]
                for i in (0,1))
    return counts


def analyze(sources,cohort,anchor_editorial,anchor_10pct):
    expected_sha={v:SOURCES[v]["sha256"] for v in VERSION_ORDER}
    if (anchor_editorial.get("schema")!=
        "idealab.psico.geo_h2_empirical_editorial_revision_rate_shadow.v1"
        or anchor_editorial.get("input_source_SHA256")!=expected_sha
        or anchor_editorial.get("not_estimated_latent_state_truth_probabilities") is not True
        or anchor_editorial.get("original_GEO2027_or_GEO2028_issued_vectors_modified") is not False
        or anchor_10pct.get("schema")!=
        "idealab.psico.geo_h2_fixed10pct_origin_state_uncertainty.v1"
        or anchor_10pct.get("lambda_assumed_a_priori_not_fitted")!=MAX_ADJACENT_LATENT_MASS
        or anchor_10pct.get("original_GEO2027_source_sha256")!=SOURCE_SHA256
        or len(cohort)!=N_COUNTRIES or len(set(cohort))!=N_COUNTRIES
        or any(len(sources[v])!=N_TRAIN for v in VERSION_ORDER)):
        raise ValueError("Published 2027 shadows/source roster/archives not verified")
    bypair={}
    fits=[]
    for old,new in TRAIN_PAIRS:
        matrix,changes=pair_confusion(sources[old],sources[new])
        bypair[f"{old}->{new}"]={
            "confusion_counts":matrix,
            "changed_four_state_records":changes,
            "total_exposures":sum(map(sum,matrix)),
        }
        fits.append(matrix)
    pool=aggregate_matrices(fits)
    kernel=posterior_kernel(pool)
    heldout_counts,heldout_changes=pair_confusion(
        sources[HOLDOUT_PAIR[0]],sources[HOLDOUT_PAIR[1]])
    heldout=evaluate_holdout(heldout_counts,kernel)
    historical_strata=[]
    for start,end in ((1989,2010),(2011,2021)):
        c,_=pair_confusion(
            sources[HOLDOUT_PAIR[0]],sources[HOLDOUT_PAIR[1]],
            cutoff=end,year_min=start)
        historical_strata.append({
            "country_year_start":start,"country_year_end":end,
            **evaluate_holdout(c,kernel),
        })
    # Preserve independently published asymmetric 0<->1 adjacent counts;
    # the 4-state kernel uses 4-way instead of 2-way smoothing.
    previous=anchor_editorial["pooled_training_exposure_counts"]
    for state in (0,1):
        row=pool[state]
        n=sum(row)
        count=row[1-state]
        if (previous[str(state)]["n"]!=n or
            previous[str(state)]["cross_to_adjacent"]!=count):
            raise AssertionError("Prior editorial source study reproduced incorrectly")
    if heldout_counts[0][1]!=4 or heldout_counts[1][0]!=2:
        raise AssertionError("Reserved editorial source disagreement no longer matches")
    future=conditional_h2(sources["26.1"],FORECAST_ORIGIN,cohort)
    previous_fixed={
        r["GWNO"]:r
        for r in anchor_10pct["new_prospective_shadow"]["probabilities"]}
    previous_emp={
        r["GWNO"]:r
        for r in anchor_editorial["prospective_unscored_2027_shadow"]["probabilities"]}
    if set(previous_fixed)!=set(cohort) or set(previous_emp)!=set(cohort):
        raise ValueError("Original 2027 shadow cohort changed")
    predictions=[]
    for cid in sorted(cohort):
        r=future[cid]
        state=r["origin_state"]
        f=r["conditional_H2"]
        hard=r["hard_p"]
        editorial=round(sum(kernel[state][j]*f[j] for j in range(STATE_COUNT)),12)
        unrestricted,assumed=latent_bounds(f,state)
        fixed_edge=(round(.9*f[state]+.1*f[1-state],12)
                    if state in (0,1) else hard)
        if (hard!=previous_fixed[cid]["p_original_four_state"]
            or hard!=previous_emp[cid]["p_hard_four_state"]
            or fixed_edge!=previous_fixed[cid]["p_uncertain_origin_shadow"]):
            raise AssertionError("Immutable original or 10% shadow reference mismatch")
        if not 0<editorial<1:
            raise AssertionError("Editorial shadow out of [0,1]")
        predictions.append({
            "GWNO":cid,"origin_year":FORECAST_ORIGIN,"target_year":TARGET_YEAR,
            "recorded_origin_state":state,"hard_four_state_p":hard,
            "next_edition_editorial_kernel_p":editorial,
            "editorial_minus_hard_p":editorial-hard,
            "conditional_H2_by_unobserved_initial_state":[round(x,12) for x in f],
            "unrestricted_latent_state_envelope":[round(x,12) for x in unrestricted],
            "adjacent_0_1_at_most_10pct_assumption_envelope":
                [round(x,12) for x in assumed],
            "earlier_published_10pct_shadow_p":fixed_edge,
            "earlier_published_two_state_editorial_shadow_p":
                previous_emp[cid]["p_revision_rate_shadow"],
        })
    seq=vintage_sequence_diagnostics(sources)
    return {
        "schema":"idealab.psico.geo_h2_fourstate_editorial_kernel_latent_partial_id.v1",
        "status":"SOURCE_OBSERVATION_MODEL_HELDOUT_VALIDATION_PLUS_UNSCORED_2027_SHADOW",
        "official_sources_SHA256":expected_sha,
        "original_issued_GEO2027_SHA256":SOURCE_SHA256,
        "fixed_source_training_country_year_cutoff":TRAIN_CUTOFF,
        "training_source_pairs":[list(x) for x in TRAIN_PAIRS],
        "reserved_editorial_source_pair":list(HOLDOUT_PAIR),
        "dirichlet_pseudocount_per_four_state_cell":DIRICHLET,
        "training_pair_results":bypair,
        "pooled_four_state_source_revision_confusion_counts":pool,
        "frozen_editorial_next_edition_state_kernel":kernel,
        "heldout_25_1_to_26_1_confusion_counts":heldout_counts,
        "heldout_25_1_to_26_1_four_state_revision_events":heldout_changes,
        "heldout_later_recorded_state_scores":heldout,
        "heldout_by_year_stratum":historical_strata,
        "source_four_vintage_sequence":seq,
        "latent_true_state_identified_by_revisions_alone":False,
        "latent_error_rate_estimated":False,
        "latent_error_partial_identification":{
            "no_assumption":"Any mixture on four initial states, so risk lies in convex hull of the four H2 conditional probabilities. No tighter latent interval is supported without assumptions.",
            "assumed_0_1_10pct":"When recorded state is 0 or 1, assume latent mass 0..10% may lie on adjacent 1 or 0; for recorded 2/3, assume exact. Bound conditional on this assumption only. Not estimated by editorial revision frequencies.",
            "max_adjacent_mass_assumed":MAX_ADJACENT_LATENT_MASS,
        },
        "prospective_unscored_2027_shadow":{
            "origin_year":FORECAST_ORIGIN,"target_year":TARGET_YEAR,
            "source":"26.1","countries_n":N_COUNTRIES,
            "predictions":predictions,
            "actual_2027_labels_observed":False,
            "prospective_skill_claimed":False,
            "original_GEO2027_issued_vector_replaced":False,
        },
        "prospective_GEO2027_or_GEO2028_original_issues_modified":False,
        "limitations":"Sequential editions are not independent measurements of a latent true state, so latent misclassification probabilities are non-identifiable. The editorial kernel predicts next-edition recorded states, not latent truth; averaging H2 conditionals with this kernel is a declared sensitivity heuristic. Training year panels overlap between pairs and holdout, source vintages postdate pseudo-origin years. A no-assumption interval is necessarily broad and the 10% adjacent envelope is assumption conditional. 2027 outcomes unavailable.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--check-report",action="store_true")
    p.add_argument("--print-report",action="store_true")
    args=p.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Original institutional GEO2027 issue hash changed")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    raw={v:request(SOURCES[v]["url"],MAX_DOWNLOAD) for v in VERSION_ORDER}
    records={v:parse_counts(raw[v],v) for v in VERSION_ORDER}
    if any(sum(map(len,records[v].values()))!=EXPECTED_ROWS[v] for v in VERSION_ORDER):
        raise ValueError("Official source archive rows changed")
    cohort=[r["country_id"] for r in json.loads(ISSUE.read_text())["countries"]]
    report=analyze(records,cohort,
        json.loads(ANCHOR_EDITORIAL.read_text(encoding="utf-8")),
        json.loads(ANCHOR_FIXED10.read_text(encoding="utf-8")))
    payload=json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n"
    if args.check_report and json.loads(OUTPUT.read_text(encoding="utf-8"))!=report:
        raise ValueError("Published four-state editorial observation report mismatch")
    if args.print_report:
        print("GEO_FOUR_STATE_OBSERVATION_BEGIN",flush=True)
        print(payload,end="")
        print("GEO_FOUR_STATE_OBSERVATION_END",flush=True)
    else:
        print(json.dumps({
            "heldout":report["heldout_later_recorded_state_scores"],
            "sequence":report["source_four_vintage_sequence"],
            "unscored_2027_n":report["prospective_unscored_2027_shadow"]["countries_n"],
        },sort_keys=True))


if __name__=="__main__":
    main()
