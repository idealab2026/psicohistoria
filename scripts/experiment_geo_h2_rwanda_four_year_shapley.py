#!/usr/bin/env python3
"""Rwanda 2023 H2: exact five-factor Shapley of four local year edits and rest.

Historical source vintages UCDP 23.1/24.1 are SHA-verified; all four
fatality-count edits are original and named. The fifth factor switches the
other 198 source-country histories, preserving the original 199-country
global Markov prior. Four-state estimator and 2021 cutoff never change.
All 32 source combinations are evaluated, with equal-order exact Shapley.
Retrospective sensitivity only, not a genuinely 2021-issued forecast.
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
    MAX_DOWNLOAD, EXPECTED_ROWS, VERSION_ORDER, intensity_state,
    parse_counts, four_state_forecast,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
REFERENCE=ROOT/"data/geo-h2-rwanda-2021-23-24-source-shapley.json"
OUTPUT=ROOT/"data/geo-h2-rwanda-1996-2021-four-year-shapley.json"
RWANDA=517
YEARS=(1996,1997,2018,2021)
FACTOR_NAMES=tuple(f"rwanda_{yr}" for yr in YEARS)+("other_198_source_countries",)
NFACTORS=len(FACTOR_NAMES)
ALL_MASK=(1<<NFACTORS)-1
ORIGIN=2021
EPS=1e-11


def exact_shapley(values):
    """Average each factor's difference over all 5! intervention orders."""
    if set(values)!=set(range(1<<NFACTORS)):
        raise ValueError("The full, unique 2^5 factorial is required")
    factorial=[math.factorial(x) for x in range(NFACTORS+1)]
    result={}
    for i,name in enumerate(FACTOR_NAMES):
        total=0.
        for mask in range(1<<NFACTORS):
            if mask&(1<<i):
                continue
            k=mask.bit_count()
            weight=factorial[k]*factorial[NFACTORS-k-1]/factorial[NFACTORS]
            total+=weight*(values[mask|(1<<i)]-values[mask])
        result[name]=total
    if not math.isclose(sum(result.values()),values[ALL_MASK]-values[0],
                        abs_tol=1e-12,rel_tol=0):
        raise AssertionError("Five-factor Shapley attribution incomplete")
    return result


def derive(old_source,new_source,reference,issued_ids):
    if (reference.get("schema")!="idealab.psico.geo_h2_rwanda_origin_vintage_twofactor_shapley.v1"
        or reference.get("no_historical_probabilities_actually_issued_in_2021") is not True
        or reference.get("new_prospective_forecasts_emitted")!=0
        or reference.get("source_SHA256")!={v:SOURCES[v]["sha256"] for v in ("23.1","24.1")}
        or reference.get("original_GEO2027_issue_sha256")!=SOURCE_SHA256
        or reference.get("GWNO")!=RWANDA
        or reference.get("origin_year")!=ORIGIN
        or reference.get("target_year")!=2023
        or reference.get("source_training_countries")!=199
        or reference.get("countries")!=196
        or len(issued_ids)!=196 or RWANDA not in issued_ids):
        raise ValueError("Cannot reuse unverified source-revision experiment")
    old={cid:{y:d for y,d in hist.items() if y<=ORIGIN}
         for cid,hist in old_source.items()}
    new={cid:{y:d for y,d in hist.items() if y<=ORIGIN}
         for cid,hist in new_source.items()}
    if (set(old)!=set(new) or len(old)!=199 or not issued_ids.issubset(old)
        or any(set(old[c])!=set(new[c]) for c in old)
        or any(not old[c] or ORIGIN not in old[c] or ORIGIN-1 not in old[c]
               for c in issued_ids)):
        raise ValueError("UCDP original source-country/coverage mismatch")
    edits=[]
    for i,year in enumerate(YEARS):
        a,b=old[RWANDA][year],new[RWANDA][year]
        edits.append({
            "year":year,"old_best_deaths":a,"new_best_deaths":b,
            "old_state":intensity_state(a),"new_state":intensity_state(b),
            "crosses_four_state_boundary":intensity_state(a)!=intensity_state(b),
        })
    if (len(reference["rwanda_annual_fatality_revisions"])!=4 or
        any((e["year"],e["old_best_deaths"],e["new_best_deaths"])!=
            (r["year"],r["old_best_deaths"],r["new_best_deaths"])
            for e,r in zip(edits,reference["rwanda_annual_fatality_revisions"]))):
        raise ValueError("Rwanda four exact original revisions mismatch")
    # Other source-country histories switch as a single fifth factor.
    values={}
    states={}
    for mask in range(1<<NFACTORS):
        other_revised=bool(mask & (1<<len(YEARS)))
        mixed={
            cid:dict(new[cid] if other_revised else old[cid])
            for cid in sorted(old)
        }
        mixed[RWANDA]=dict(old[RWANDA])
        for i,year in enumerate(YEARS):
            if mask&(1<<i):
                mixed[RWANDA][year]=new[RWANDA][year]
        predictions,metadata=four_state_forecast(
            mixed,ORIGIN,historical_rolling_diagnostic=True)
        if (metadata["eligible_countries"]!=196 or
            metadata["training_countries"]!=199 or
            metadata["cutoff_max"]!=ORIGIN or
            set(predictions)!=issued_ids):
            raise AssertionError("H2 training cohort, cutoff or model changed")
        values[mask]=predictions[RWANDA]["p_intensity_markov"]
        states[mask]=predictions[RWANDA]["origin_intensity_state"]
    points=reference["counterfactual_source_combinations"]
    checks=((0,"00"),(1<<len(YEARS),"01"),
            ((1<<len(YEARS))-1,"10"),(ALL_MASK,"11"))
    for mask,key in checks:
        if not math.isclose(values[mask],points[key]["rwanda_H2_probability"],
                            abs_tol=EPS,rel_tol=0):
            raise AssertionError("Earlier 2-block experiment endpoint differs")
    factors=exact_shapley(values)
    if not all(math.isclose(factors[f"rwanda_{yr}"],0,abs_tol=1e-14,rel_tol=0)
               for yr in (1997,2018)):
        raise AssertionError("A within-bin count change affected categorical model")
    for mask in range(1<<NFACTORS):
        for i,year in enumerate(YEARS):
            if year in (1997,2018) and not mask&(1<<i):
                if values[mask]!=values[mask|(1<<i)]:
                    raise AssertionError("Within-bin historical source change not neutral")
    p_old,p_new=values[0],values[ALL_MASK]
    return {
        "schema":"idealab.psico.geo_h2_rwanda_year_specific_fivefactor_shapley.v1",
        "status":"SHA_REPLAYED_RETROSPECTIVE_32_INTERVENTIONS_NOT_PROSPECTIVE",
        "source_SHA256":reference["source_SHA256"],
        "frozen_original_GEO2027_sha256":SOURCE_SHA256,
        "GWNO":RWANDA,"origin_year":ORIGIN,"target_year":2023,
        "source_training_countries":199,"original_evaluation_GWNO_n":196,
        "factor_order":list(FACTOR_NAMES),
        "rwanda_source_fatality_edits":edits,
        "counterfactuals":[{
            "mask":mask,"revised_factors":[FACTOR_NAMES[i] for i in range(NFACTORS)
                                           if mask&(1<<i)],
            "p_four_state_H2":values[mask],
            "rwanda_origin_four_state":states[mask],
        } for mask in range(1<<NFACTORS)],
        "old_probability":p_old,"new_probability":p_new,
        "full_revision_probability_shift":p_new-p_old,
        "fivefactor_shapley":factors,
        "within_bin_count_edits_neutral":True,
        "two_group_reference_local_shapley":reference["rwanda_local_source_shapley"],
        "two_group_reference_other_shapley":reference["other_source_countries_shapley"],
        "difference_between_grouped_and_ungrouped_shapley_is_interaction_dependent":True,
        "original_forecasts_2027_2028_unchanged":True,
        "not_actual_2021_issued_probabilities":True,
        "limitations":"Exact mechanical attribution across 4 Rwanda yearly edits and all other source countries, with 32 source combinations and fixed estimator. Not historical causal attribution, not IID skill, and official source vintages were released after simulated 2021 origin. Four within-1997/2018 counts did not change categorical states.",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report",action="store_true")
    parser.add_argument("--print-report",action="store_true")
    args=parser.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("GEO2027 original forecasts changed")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    raw={v:request(SOURCES[v]["url"],MAX_DOWNLOAD) for v in ("23.1","24.1")}
    counts={v:parse_counts(raw[v],v) for v in raw}
    if any(sum(map(len,counts[v].values()))!=EXPECTED_ROWS[v] for v in counts):
        raise ValueError("Source vintage archives have wrong total row counts")
    ids={r["country_id"] for r in json.loads(ISSUE.read_text())["countries"]}
    result=derive(counts["23.1"],counts["24.1"],
                  json.loads(REFERENCE.read_text(encoding="utf-8")),ids)
    payload=json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    if args.check_report and json.loads(OUTPUT.read_text(encoding="utf-8"))!=result:
        raise ValueError("Published Rwanda year-specific factor attribution not reproduced")
    if args.print_report:
        print("GEO_RWANDA_YEAR_SHAPLEY_BEGIN",flush=True)
        print(payload,end="")
        print("GEO_RWANDA_YEAR_SHAPLEY_END",flush=True)
    else:
        print(json.dumps({"shift":result["full_revision_probability_shift"],
                          "per_factor":result["fivefactor_shapley"]},sort_keys=True))


if __name__=="__main__":
    main()
