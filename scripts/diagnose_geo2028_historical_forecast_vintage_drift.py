#!/usr/bin/env python3
"""Ex-post historical UCDP vintage sensitivity of FROZEN-origin GEO probabilities.

Official SHA-pinned 23.1,24.1,25.1,26.1, fixed origins 2022..2024,
horizons 2 and 3. Model is exactly the preregistered Markov country shrink20 /
Laplace1 GEO2027/28 specification, reproduced against the actual original
2025-origin H2+H3 issued probabilities using the same 26.1 archive.

A LATER vintage may contain later years: all observations above the FIXED
origin are stripped BEFORE transition training, initial state or baseline.
No target labels are used in this analysis; it cannot measure forecasting skill.
The changes are editorial-historical sensitivity, not additional year shocks,
IID uncertainty, real 2027/28 results or a causal decomposition.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from backtest_archived_country_vintages import SOURCES, fetch_archives
from decompose_geo2028_origin2026_update import nstep
from evaluate_geo2028_first_complete_official import load_immutable_issue
from forecast_2027_statebased import LAPLACE, TRANSITION_PRIOR, PROTOCOL_ID
from diagnose_geo2027_ucdp_vintage_revisions import drift

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo2028-historical-forecast-vintage-drift.json"
PAIRS=((2022,"23.1","24.1"),
       (2022,"23.1","25.1"),
       (2022,"23.1","26.1"),
       (2023,"24.1","25.1"),
       (2023,"24.1","26.1"),
       (2024,"25.1","26.1"))
VERSION_ORDER=("23.1","24.1","25.1","26.1")
HORIZONS=(2,3)
EPS=3e-11
PRIMARY="p_model"


def _verify_records(vintages,metadata):
    if set(vintages)!=set(VERSION_ORDER) or set(metadata)!=set(VERSION_ORDER):
        raise ValueError("All four original UCDP editions are required")
    for version in VERSION_ORDER:
        spec=SOURCES[version]
        if metadata[version].get("sha256")!=spec["sha256"] or (
            metadata[version].get("last_year")!=spec["last_year"]):
            raise ValueError("Historical official UCDP source SHA or cutoff changed")
        history=vintages[version]
        if not isinstance(history,dict) or not history:
            raise ValueError("Empty official UCDP source")
        if max(max(h) for h in history.values())!=spec["last_year"]:
            raise ValueError("Unexpected maximum source annual observation")
        for cid,h in history.items():
            if type(cid) is not int or not 1<=cid<=2000 or not h:
                raise ValueError("Bad official GWNO country")
            if any(type(yr) is not int or yr<1989 or yr>spec["last_year"] or
                   type(y) is not int or y not in (0,1) for yr,y in h.items()):
                raise ValueError("Invalid source historical binary state")


def _fit_at_origin(history,year,*,fixed_cohort=None):
    """One exact frozen-origin model with training data <=year ONLY.

    All countries with history through origin enter GLOBAL transition counts;
    baseline is for the original fixed-cohort GWNOs with year and year-1.
    """
    if (type(year) is not int or not 1989+5<=year<=2025 or
        not isinstance(history,dict) or not history or
        TRANSITION_PRIOR!=20 or LAPLACE!=1):
        raise ValueError("Origin, source or issued estimator has changed")
    training={}
    for cid,h in history.items():
        if type(cid) is not int or not 1<=cid<=2000 or not isinstance(h,dict):
            raise ValueError("Invalid archived country identity")
        clipped={y:s for y,s in h.items() if y<=year}
        if clipped:
            if any(type(y) is not int or y<1989 or
                   type(s) is not int or s not in (0,1)
                   for y,s in clipped.items()):
                raise ValueError("Invalid clipped annual binary state")
            training[cid]=clipped
    available=sorted(cid for cid,h in training.items()
                     if year in h and year-1 in h)
    cohort=available if fixed_cohort is None else sorted(fixed_cohort)
    if (len(cohort)!=196 or len(set(cohort))!=196 or
        any(cid not in available for cid in cohort)):
        raise ValueError("Fixed old-vintage original country cohort not fully observed")
    g=[[0,0],[0,0]]
    local={}
    for cid,h in training.items():
        cnt=[[0,0],[0,0]]
        for y in sorted(h):
            if y>1989 and y-1 in h:
                a,b=h[y-1],h[y]
                cnt[a][b]+=1
                g[a][b]+=1
        local[cid]=cnt
    if min(sum(row) for row in g)<100:
        raise ValueError("Official history lacks original Markov training exposures")
    q_global=[(g[s][1]+LAPLACE)/(sum(g[s])+2*LAPLACE)
              for s in (0,1)]
    recent=range(year-4,year+1)
    values=[training[cid][y] for cid in cohort for y in recent
            if y in training[cid]]
    if len(values)<.95*5*len(cohort):
        raise ValueError("Five-year prevalence reference missing histories")
    baseline=(sum(values)+LAPLACE)/(len(values)+2*LAPLACE)
    rows={}
    for cid in cohort:
        h=training[cid]
        q=[(local[cid][s][1]+TRANSITION_PRIOR*q_global[s])/
           (sum(local[cid][s])+TRANSITION_PRIOR) for s in (0,1)]
        s=h[year]
        results={f"p_model_h{horizon}":round(nstep(s,q,horizon),12)
                 for horizon in HORIZONS}
        results.update({f"p_global_markov_h{horizon}":
                        round(nstep(s,q_global,horizon),12)
                        for horizon in HORIZONS})
        results.update({
            "country_id":cid,"origin_state":s,
            "p_baseline_global_5y":round(baseline,12),
            "q_local":q,
        })
        if any(type(v) is not float or not math.isfinite(v) or not 0<v<1
               for k,v in results.items() if k.startswith("p_")):
            raise ValueError("Invalid frozen-model probability")
        rows[cid]=results
    return rows,{
        "origin_year":year,"training_country_ids":len(training),
        "cohort_n":len(cohort),
        "global_transition_counts":g,
        "global_transition_q_active":[round(x,12) for x in q_global],
        "global_baseline_exposures":len(values),
        "global_baseline_active":sum(values),
        "global_baseline_probability":round(baseline,12),
        "last_training_year":max(max(h) for h in training.values()),
    }


def _quantile_ceil(arr,prob):
    if not arr or not 0<prob<1:
        raise ValueError("Empty quantile sample")
    return sorted(arr)[math.ceil(prob*len(arr))-1]


def _changes_for_horizon(initial,later,horizon,*,names):
    ids=sorted(initial)
    n=len(ids)
    if n!=196 or set(ids)!=set(later):
        raise ValueError("Country risk set changed when comparing two UCDP vintages")
    field=f"p_model_h{horizon}"
    one=set(cid for cid in ids if initial[cid][field]>=.5)
    two=set(cid for cid in ids if later[cid][field]>=.5)
    rank_old=sorted(ids,key=lambda cid:(-initial[cid][field],cid))
    rank_new=sorted(ids,key=lambda cid:(-later[cid][field],cid))
    k=20
    old_top=set(rank_old[:k])
    new_top=set(rank_new[:k])
    diagnostics=[]
    states_changed=[]
    for cid in ids:
        old=initial[cid]
        newer=later[cid]
        old_state,new_state=old["origin_state"],newer["origin_state"]
        a=old[field]
        q_new=newer["q_local"]
        b=round(nstep(old_state,q_new,horizon),12)   # new kernel, old state
        c=newer[field]                              # new kernel, revised state
        kernel=b-a
        state=c-b
        delta=c-a
        if abs((kernel+state)-delta)>EPS:
            raise ValueError("Historical revision attribution fails exact telescope")
        if old_state!=new_state:
            states_changed.append(cid)
        diagnostics.append({
            "country_id":cid,
            "country":names.get(cid,str(cid)),
            "original_p":a,"revised_p":c,
            "delta":round(delta,12),
            "abs_delta":abs(delta),
            "kernel_revision_component":round(kernel,12),
            "origin_state_reclassification_component":round(state,12),
            "origin_state_changed":old_state!=new_state,
            "crossed_0_5_decision_threshold":(a>=.5)!=(c>=.5),
        })
    values=[r["abs_delta"] for r in diagnostics]
    total_abs=sum(values)
    by_abs=sorted(diagnostics,key=lambda r:(-r["abs_delta"],r["country_id"]))
    return {
        "target_calendar_year_if_issued_then":initial[ids[0]]["origin_year"]+horizon
            if "origin_year" in initial[ids[0]] else None,
        "horizon_years":horizon,
        "country_count":n,
        "mean_absolute_probability_change":round(total_abs/n,12),
        "median_absolute_probability_change":round(_quantile_ceil(values,.5),12),
        "p95_absolute_probability_change":round(_quantile_ceil(values,.95),12),
        "max_absolute_probability_change":round(max(values),12),
        "n_probability_change_ge_1pp":sum(v>=.01-1e-13 for v in values),
        "n_probability_change_ge_5pp":sum(v>=.05-1e-13 for v in values),
        "n_probability_change_ge_10pp":sum(v>=.1-1e-13 for v in values),
        "n_changed_0_5_binary_decision":len(one.symmetric_difference(two)),
        "n_2025_or_historical_origin_state_reclassified":len(states_changed),
        "origin_state_reclassified_country_ids":states_changed,
        "top20_overlap_with_GWNO_tie_break":len(old_top&new_top),
        "top20_entered_GWNO":sorted(new_top-old_top),
        "top20_exited_GWNO":sorted(old_top-new_top),
        "top20_rank_ties_broken_by_GWNO_numeric_not_statistically_meaningful":True,
        "sum_of_absolute_probability_changes":round(total_abs,12),
        "mean_signed_probability_change":round(sum(r["delta"] for r in diagnostics)/n,12),
        "mean_signed_kernel_revision_component":round(sum(r["kernel_revision_component"] for r in diagnostics)/n,12),
        "mean_signed_origin_state_reclassification_component":round(sum(r["origin_state_reclassification_component"] for r in diagnostics)/n,12),
        "largest_ten_named_probability_revisions":[{
            k:r[k] for k in (
                "country_id","country","original_p","revised_p","delta",
                "kernel_revision_component",
                "origin_state_reclassification_component","origin_state_changed")
            } for r in by_abs[:10]],
        "no_target_labels_observed":True,
        "not_a_confidence_interval_or_skill_estimate":True,
    }


def _compare(vintages,origin_year,old_version,new_version,*,names):
    old=vintages[old_version]
    later=vintages[new_version]
    if (SOURCES[old_version]["last_year"]!=origin_year or
        SOURCES[new_version]["last_year"]<=origin_year):
        raise ValueError("Historical fixed-origin versions not correctly ordered")
    first,firstmeta=_fit_at_origin(old,origin_year)
    revised,revisedmeta=_fit_at_origin(later,origin_year,fixed_cohort=list(first))
    if firstmeta["last_training_year"]!=origin_year or (
        revisedmeta["last_training_year"]!=origin_year):
        raise ValueError("Post-origin UCDP later edition leaked into Markov training")
    # Compare source labels at same year on the original fixed country cohort.
    historical=drift(old,later)
    yearstates=drift(old,later,year=origin_year,cohort=list(first))
    if yearstates["common_country_years"]!=196 or (
        yearstates["missing_in_earlier"] or yearstates["missing_in_later"]):
        raise ValueError("Original country-year origin labels not comparable")
    rows=[]
    for horizon in HORIZONS:
        # Same ID set and same horizon for both snapshots of same origin.
        res=_changes_for_horizon(first,revised,horizon,names=names)
        res["target_calendar_year_if_issued_then"]=origin_year+horizon
        rows.append(res)
    return {
        "origin_year_fixed":origin_year,
        "original_edition":old_version,
        "later_revision_edition":new_version,
        "new_edition_last_year_unused_in_training":SOURCES[new_version]["last_year"],
        "original_risk_set_n":196,
        "revised_risk_set_n":revisedmeta["cohort_n"],
        "old_vintage_training_country_ids":firstmeta["training_country_ids"],
        "later_vintage_training_country_ids":revisedmeta["training_country_ids"],
        "old_vintage_global_transitions":firstmeta["global_transition_counts"],
        "later_vintage_global_transitions":revisedmeta["global_transition_counts"],
        "old_global_5y_baseline_probability":firstmeta["global_baseline_probability"],
        "revised_global_5y_baseline_probability":revisedmeta["global_baseline_probability"],
        "baseline_probability_revision":round(
            revisedmeta["global_baseline_probability"]-
            firstmeta["global_baseline_probability"],12),
        "fixed_origin_binary_reclassification":yearstates,
        "all_common_historical_country_years_including_later_pre_and_post_origin":historical,
        "horizons":rows,
        "training_cutoff_exact":True,
        "first_edition_prediction_retrospectively_reconstructed":True,
        "later_edition_label_revision_not_a_new_2026_origin":True,
    }


def _anchor_first_issued(vintages,first_2027,first_2028):
    """The ORIGINAL 2025 official 26.1 source reproduces H2 and H3 issues."""
    history=vintages["26.1"]
    rows,meta=_fit_at_origin(history,2025)
    old={r["country_id"]:r for r in first_2027["countries"]}
    future={r["country_id"]:r for r in first_2028["countries"]}
    if len(old)!=196 or len(future)!=196 or set(old)!=set(future) or (
        set(rows)!=set(old)):
        raise ValueError("Original 2025-issue risk population not reproduced")
    for cid in rows:
        h=rows[cid]
        if (h["origin_state"]!=old[cid]["last_observed_state_2025"] or
            h["origin_state"]!=future[cid]["last_observed_state_2025"] or
            abs(h["p_model_h2"]-old[cid]["p_model"])>1e-11 or
            abs(h["p_global_markov_h2"]-old[cid]["p_global_markov"])>1e-11 or
            abs(h["p_model_h3"]-future[cid]["p_model"])>1e-11 or
            abs(h["p_global_markov_h3"]-future[cid]["p_global_markov_3step"])>1e-11 or
            abs(h["p_baseline_global_5y"]-old[cid]["p_baseline_global_5y"])>1e-11 or
            abs(h["p_baseline_global_5y"]-future[cid]["p_baseline_global_5y"])>1e-11):
            raise ValueError("2025 original issue is NOT reproduced byte-scale from official archive")
    return {
        "issued_GEO2027_first_original_sha256":
            "5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5",
        "issued_GEO2028_H3_first_original_sha256":
            "fd5832c6896548b053202f2f84bd0f7cd4a75df44462fbd4f259b9d8d4c39bde",
        "2025_origin_H2_original_196_exact_model_and_reference_reproduced":True,
        "2025_origin_H3_original_196_exact_model_and_reference_reproduced":True,
        "2025_source_26_1_global_transition_counts":meta["global_transition_counts"],
        "2025_source_26_1_baseline":meta["global_baseline_probability"],
    }


def study(vintages,metadata,first_2027,first_2028,*,names=None):
    _verify_records(vintages,metadata)
    names=names or {row["country_id"]:row["country"]
                    for row in first_2028["countries"]}
    anchor=_anchor_first_issued(vintages,first_2027,first_2028)
    folds=[_compare(vintages,year,older,newer,names=names)
           for year,older,newer in PAIRS]
    if len(folds)!=6 or any(f["original_risk_set_n"]!=196 for f in folds):
        raise ValueError("Expected six matched old-vs-revised edition comparisons")
    # Six pairs share histories, origins, GWNOs and years: never pool as IID!
    primary=[h for fold in folds for h in fold["horizons"]
             if h["horizon_years"]==3]
    return {
        "schema":"idealab.psico.geo_historical_fixed_origin_vintage_probability_drift.v1",
        "status":"OFFICIAL_SHA_PINNED_RETROSPECTIVE_VINTAGE_SENSITIVITY_NOT_2027_2028_OUTCOME",
        "source_versions_and_sha256":{v:SOURCES[v]["sha256"] for v in VERSION_ORDER},
        "source_last_observation_year":{v:SOURCES[v]["last_year"] for v in VERSION_ORDER},
        "model":"original_country_markov_laplace1_global_shrink20",
        "comparison_policy":"same original year and GWNO cohort, later edition truncated to origin, same target horizon",
        "fixed_origins":[2022,2023,2024],
        "horizons":[2,3],
        "n_comparisons_six_overlapping_source_pairs":6,
        "n_independent_prospective_tests_contributed":0,
        "each_comparison_cohort_n":196,
        "fully_reconstructed_original_2025_H2_H3":anchor,
        "historical_comparisons":folds,
        "horizon3_max_absolute_change_across_overlapping_pairs":
            max(h["max_absolute_probability_change"] for h in primary),
        "horizon3_max_n_change_ge_5pp_in_any_one_pair":
            max(h["n_probability_change_ge_5pp"] for h in primary),
        "first_2025_origin_newer_27_1_available":False,
        "no_historical_2027_or_2028_target_outcomes_used":True,
        "prospective_2027_2028_skill_demonstrated":False,
        "country_probabilities_issued_in_2027_2028_changed":False,
        "country_IID_uncertainty_or_confidence_intervals_estimated":False,
        "notarized_source_release_dates":False,
        "all_six_pairs_statistically_independent":False,
        "limitations":(
            "This is a retrospective replay of the exact preregistered Markov "
            "formula using UCDP 23.1,24.1,25.1,26.1 original source bytes. "
            "Forecasts for historical origins were NOT issued at the time. "
            "Some historical country-year source labels may be revised, "
            "including global transition counts and cohort composition. "
            "The six pairs overlap source editions, historical years and "
            "countries and are NOT six independent trials. No future target "
            "label or first public 2025-origin forecast changes. The source "
            "timestamp is public metadata, not independent notarization. "
            "Deterministic top20 boundary ties are broken by GWNO numeric ID; "
            "these are NOT meaningful confidence differences. No inference "
            "that 27.1 will resemble these revisions or that GEO2028 will "
            "perform at a particular level."
        ),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report")
    args=parser.parse_args()
    original_2028,_=load_immutable_issue()
    # The same institutional source freeze also authenticates GEO2027.
    first_2027=json.loads((ROOT/"data/forecast-2027-ucdp261.json").read_text(encoding="utf8"))
    vintages,metadata=fetch_archives()
    report=study(vintages,metadata,first_2027,original_2028)
    raw=(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode()
    if args.check_report and REPORT.read_bytes()!=raw:
        raise ValueError("Immutable source-backed historical forecast drift report differs from CI")
    print("GEO2028_HISTORICAL_ORIGIN_VINTAGE_DRIFT_BEGIN")
    print(raw.decode(),end="")
    print("GEO2028_HISTORICAL_ORIGIN_VINTAGE_DRIFT_END")


if __name__=="__main__":
    main()
