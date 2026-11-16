#!/usr/bin/env python3
"""GEO2027: Markov own-history partial-pooling and vintage stability study.

Mechanistic source-verified analysis, NOT a 2027 forecast issue and NOT a
retrained LOG1P comparison. Exactly the original 196 GWNO reference countries.
Never uses outcomes after the origin of a replay, even in later-edition UCDP.

For all four SHA-pinned official archive vintages, replay origins 2022 and
2023 where available. For 2025 only edition 26.1 has a complete origin.
Scale national transition counts by a FIXED non-selected weight grid:
  q_s(w) = (w * own[s][1] + 20 * g_s[without country])
           / (w * sum(own[s]) + 20)
  p(H2 | origin_state) = (1-q_origin)*q0 + q_origin*q1.

w=0 suppresses local history; w=1 approximates issued country-aware Markov,
with a small intentional difference because the global prior now holds that
country out. The original first-issued Markov is reproduced exactly as
a separate integrity check, not refitted/modified. No 2027 outcome is scored.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from audit_geo2027_global_only_matched_issue import (
    ISSUE as GLOBAL_ONLY_ISSUE, MANIFEST as GLOBAL_ONLY_MANIFEST,
    audit as audit_new_issue,
    FROZEN_SHA256 as NEW_SHA256,
)
from audit_geo2027_log1p_shadow_issue import (
    ISSUE as OLD_LOG1P, MANIFEST as OLD_LOG1P_MANIFEST,
    ORIGINAL, FROZEN_ISSUE_SHA256,
)
from audit_geo2027_log1p_issued_death_stress import ALERTS, ALERT_SHA
from backtest_archived_country_vintages import SOURCES
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD, VERSION_ORDER, counts_to_binary, parse_counts,
)
from prepare_geo2027_transition_alerts import SOURCE_SHA256
from probe_ucdp_organized_vintages import request
from experiment_geo2027_log1p_markov_country_history_ablation import (
    _nstep_two,
)

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo2027-markov-partial-pooling-vintage-stability.json"
ORIGINS=(2022,2023,2025)
WEIGHTS=(0.0,0.25,0.5,1.0)
PRIOR_STRENGTH=20
LAPLACE=1
EPS=2e-11


def _percentile(nums,p):
    if not nums or not 0<=p<=1:
        raise ValueError("Invalid percentile input")
    v=sorted(nums); t=(len(v)-1)*p; k=int(t)
    return v[k]+(v[min(k+1,len(v)-1)]-v[k])*(t-k)


def summary(values):
    if not values or any(type(x) not in (int,float) or
                         not math.isfinite(x) for x in values):
        raise ValueError("Nonfinite or empty scientific comparison")
    n=len(values);m=sum(values)/n
    return {
        "n":n,
        "mean":round(m,12),
        "std_population":round(math.sqrt(
            sum((x-m)**2 for x in values)/n),12),
        "min":round(min(values),12),
        "p10":round(_percentile(values,.1),12),
        "median":round(_percentile(values,.5),12),
        "p90":round(_percentile(values,.9),12),
        "p95":round(_percentile(values,.95),12),
        "max":round(max(values),12),
        "range":round(max(values)-min(values),12),
    }


def build_counts(binary,origin):
    """Only consecutive annual transitions where both years are observed."""
    if origin not in ORIGINS or not isinstance(binary,dict):
        raise ValueError("Invalid original historical origin")
    glob=[[0,0],[0,0]]
    locals={}
    seen=[]
    for cid,h in binary.items():
        if type(cid) is not int or not isinstance(h,dict):
            raise ValueError("Country history schema changed")
        own=[[0,0],[0,0]]
        for year in sorted(h):
            if year>origin or year-1 not in h:
                continue
            a,b=h[year-1],h[year]
            if a not in (0,1) or b not in (0,1):
                raise ValueError("Invalid threshold state")
            own[a][b]+=1
            glob[a][b]+=1
            seen.append(year)
        locals[cid]=own
    if min(sum(row) for row in glob)<100:
        raise ValueError("Too few state transitions in UCDP edition")
    if not seen or max(seen)!=origin:
        raise ValueError("Missing official origin-year transition")
    return glob,locals


def raw_markov(global_counts,local_counts,state,weight,omit_own_global=True):
    """Original 2-step Markov kernel with separately weighted local counts."""
    if (state not in (0,1) or
        type(weight) not in (int,float) or
        not math.isfinite(weight) or weight<0 or
        len(global_counts)!=2 or len(local_counts)!=2):
        raise ValueError("Malformed national transition probability")
    for matrix in (global_counts,local_counts):
        if any(len(row)!=2 or
               any(type(x) is not int or x<0 for x in row)
               for row in matrix):
            raise ValueError("Negative/fractional transition count")
    pooled=[[global_counts[s][t]-
             (local_counts[s][t] if omit_own_global else 0)
             for t in (0,1)] for s in (0,1)]
    if any(x<0 for row in pooled for x in row) or min(
        sum(row) for row in pooled)<100:
        raise ValueError("Country withheld prior unavailable")
    g=[(row[1]+LAPLACE)/(sum(row)+2*LAPLACE) for row in pooled]
    q=[(weight*local_counts[s][1]+PRIOR_STRENGTH*g[s])/
       (weight*sum(local_counts[s])+PRIOR_STRENGTH)
       for s in (0,1)]
    p=round(_nstep_two(state,q),12)
    if not 0<p<1:
        raise ValueError("Invalid two-step risk")
    return p


def replay_snapshot(source,origin,ids,issued_original=None):
    """Source edition may postdate origin; cutoff transition inputs at origin."""
    binary=counts_to_binary(source)
    global_counts,locals=build_counts(binary,origin)
    cases={}
    for cid in sorted(ids):
        if (cid not in source or cid not in binary or
            not {origin-1,origin}.issubset(source[cid]) or
            cid not in locals):
            raise ValueError("Unobserved origin country is NOT a negative")
        deaths=source[cid][origin]
        state=int(deaths>=25)
        counts=locals[cid]
        ps={str(w):raw_markov(global_counts,counts,state,w)
            for w in WEIGHTS}
        reference=raw_markov(global_counts,counts,state,1.,False)
        if issued_original is not None:
            original=issued_original[cid]
            if (int(original["last_observed_state_2025"])!=state or
                abs(original["p_model"]-reference)>EPS):
                raise AssertionError("Original first-issued 2027 Markov kernel not reproduced")
        cases[cid]={
            "country_id":cid,
            "country_deaths_at_origin":deaths,
            "country_origin_state":state,
            "origin_deaths_group":("zero" if deaths==0 else
                "subthreshold_1_to_24" if deaths<25 else "active_25_plus"),
            "local_transition_exposures_state0":sum(counts[0]),
            "local_transition_exposures_state1":sum(counts[1]),
            "local_activation_transitions_n":counts[0][1],
            "local_persistence_transitions_n":counts[1][1],
            "national_fraction_state0":sum(counts[0])/(sum(counts[0])+20),
            "national_fraction_state1":sum(counts[1])/(sum(counts[1])+20),
            "p_original_with_country_in_global":reference,
            "p_partial_pool_grid":ps,
        }
    if len(cases)!=196:
        raise AssertionError("Changed 196-country fixed reference universe")
    return cases,{"origin":origin,"global_transition_counts":global_counts,
                  "source_country_transition_count":len(locals),
                  "maximum_observed_transition_year":origin}


def _by_group(cases):
    by_group={}
    for name in ("zero","subthreshold_1_to_24","active_25_plus"):
        group=[r for r in cases.values() if r["origin_deaths_group"]==name]
        if not group:
            raise ValueError("Missing risk classification")
        by_group[name]={
            "n":len(group),
            "n_ever_visited_state1":sum(
                r["local_transition_exposures_state1"]>0 for r in group),
            "n_no_local_active_transitions":sum(
                r["local_transition_exposures_state1"]==0 for r in group),
            "n_no_local_inactive_transitions":sum(
                r["local_transition_exposures_state0"]==0 for r in group),
            "national_fraction_state0":summary([
                r["national_fraction_state0"] for r in group]),
            "national_fraction_state1":summary([
                r["national_fraction_state1"] for r in group]),
            "local_transition_exposures_state0":summary([
                r["local_transition_exposures_state0"] for r in group]),
            "local_transition_exposures_state1":summary([
                r["local_transition_exposures_state1"] for r in group]),
            "original_markov_from_frozen_law":summary([
                r["p_original_with_country_in_global"] for r in group]),
            "Markov_partial_pooling":{
                key:summary([r["p_partial_pool_grid"][key] for r in group])
                for key in (str(w) for w in WEIGHTS)
            },
        }
    return by_group


def vintage_pair(old,new,older,later,origin):
    if set(old)!=set(new) or len(old)!=196:
        raise ValueError("Country-vintage pair mismatch")
    per_weight={}
    for w in WEIGHTS:
        key=str(w)
        change_pp=[
            100*(new[cid]["p_partial_pool_grid"][key]-
                 old[cid]["p_partial_pool_grid"][key])
            for cid in sorted(old)]
        abs_pp=[abs(x) for x in change_pp]
        per_weight[key]={
            "absolute_risk_revision_pp":summary(abs_pp),
            "signed_risk_revision_pp":summary(change_pp),
            "countries_revision_at_least_1_pp":sum(x>=1-1e-9 for x in abs_pp),
            "countries_revision_at_least_5_pp":sum(x>=5-1e-9 for x in abs_pp),
        }
    deaths_revision=sum(
        old[cid]["country_deaths_at_origin"]!=
        new[cid]["country_deaths_at_origin"] for cid in old)
    state_revision=sum(
        old[cid]["country_origin_state"]!=
        new[cid]["country_origin_state"] for cid in old)
    return {
        "origin":origin,"older_edition":older,"later_edition":later,
        "n_fixed_country_ids":196,
        "countries_with_revised_origin_best_deaths":deaths_revision,
        "countries_with_revised_origin_binary_state":state_revision,
        "risk_revision_by_prespecified_local_history_weight":per_weight,
        "edition_pairs_share_histories_and_are_not_independent":True,
    }


def study(sources,original,oldshadow,newshadow):
    if (set(sources)!=set(VERSION_ORDER) or
        original.get("forecast_id")!="PSICO-GEO2027-STATEBASED25-V1" or
        len(original.get("countries",[]))!=196 or
        len(oldshadow.get("countries",[]))!=196 or
        len(newshadow.get("countries",[]))!=196 or
        newshadow.get("official_2027_outcomes_resolved")!=0):
        raise ValueError("Frozen source and 2027 issued cohort changed")
    ids={r["country_id"] for r in original["countries"]}
    official={r["country_id"]:r for r in original["countries"]}
    if (len(ids)!=196 or ids!={r["country_id"] for r in oldshadow["countries"]}
        or ids!={r["country_id"] for r in newshadow["countries"]}):
        raise ValueError("First issued GWNO country universe differs")
    snapshots={}
    summaries=[]
    vintages=[]
    for origin in ORIGINS:
        versions=[v for v in VERSION_ORDER if
                  SOURCES[v]["last_year"]>=origin]
        for version in versions:
            local,provenance=replay_snapshot(
                sources[version],origin,ids,
                official if origin==2025 else None)
            snapshots[(origin,version)]=local
            summaries.append({
                "source_edition":version,
                "edition_last_year":SOURCES[version]["last_year"],
                "origin":origin,"n_country":196,
                "cutoff_provenance":provenance,
                "by_origin_deaths_group":_by_group(local),
                "post_origin_information_used_for_Markov_transition_fit":False,
                "edition_published_after_origin_and_revised_retrospectively":
                    SOURCES[version]["last_year"]>origin,
            })
        first=versions[0]
        for later in versions[1:]:
            vintages.append(vintage_pair(
                snapshots[(origin,first)],snapshots[(origin,later)],
                first,later,origin))
    if len(summaries)!=8 or len(vintages)!=5:
        raise AssertionError("Expected four historical 2022, three 2023 and one 2025 snapshots")
    current=snapshots[(2025,"26.1")]
    g=_by_group(current)
    if ([g[k]["n"] for k in ("zero","subthreshold_1_to_24",
                             "active_25_plus")]!=[154,8,34]):
        raise AssertionError("Original 2025 state/death strata changed")
    # Aggregated only (not another published alternative country forecast).
    largest=sorted(current.values(),key=lambda r:(
        -abs(r["p_partial_pool_grid"]["1.0"]-
             r["p_partial_pool_grid"]["0.0"]),r["country_id"]))[:12]
    top=[{
        "country_id":r["country_id"],
        "country":official[r["country_id"]]["country"],
        "origin_deaths_bucket":r["origin_deaths_group"],
        "local_history_exposures_state0":
            r["local_transition_exposures_state0"],
        "local_history_exposures_state1":
            r["local_transition_exposures_state1"],
        "national_weight_given_state0":round(
            r["national_fraction_state0"],6),
        "national_weight_given_state1":round(
            r["national_fraction_state1"],6),
        "absolute_local_Markov_H2_sensitivity_pp":round(
            100*abs(r["p_partial_pool_grid"]["1.0"]-
                    r["p_partial_pool_grid"]["0.0"]),9),
    } for r in largest]
    return {
        "schema":"idealab.psico.geo2027_markov_local_partial_pooling_vintage_stability.v1",
        "status":"EX_ANTE_2025_SOURCE_ONLY_MARKOV_COMPONENT_DIAGNOSTIC_NOT_NEW_FORECAST",
        "source_sha256":{v:SOURCES[v]["sha256"] for v in VERSION_ORDER},
        "original_GEO2027_sha256":SOURCE_SHA256,
        "original_LOG1P2027_shadow_sha256":FROZEN_ISSUE_SHA256,
        "new_global_only_matched_2027_sha256":NEW_SHA256,
        "original_15_transition_alerts_sha256":ALERT_SHA,
        "frozen_2027_country_universe":196,
        "target_year":2027,
        "origin_year_for_issued_model":2025,
        "official_2027_outcomes_resolved":0,
        "no_new_forecasts_or_alerts_issued":True,
        "issued_GEO_and_LOG1P_and_globalonly_all_frozen_unchanged":True,
        "weights_are_fixed_mechanistic_stress_not_candidate_selection":
            list(WEIGHTS),
        "prior_strength_original":20,
        "global_laplace_one":True,
        "new_grid_uses_global_leave_target_country_out_in_every_weight":True,
        "w_equal_1_differs_slightly_from_original_which_includes_target_country_in_global":True,
        "original_frozen_GEO_markov_reproduced_on_all_196":True,
        "not_using_LOG1P_or_intercept_recalibration_for_weight_comparisons":True,
        "not_a_multimodel_prospective_2027_forecast":True,
        "revised_edition_not_available_asof_older_historical_origin":True,
        "archive_snapshot_n":len(summaries),
        "historical_edition_comparison_n":len(vintages),
        "origins_studied":list(ORIGINS),
        "2025_risk_by_origin_deaths":g,
        "2025_top12_most_history_sensitive_countries_without_new_country_forecast_probabilities":top,
        "archive_snapshots_aggregate_only":summaries,
        "five_overlapping_source_revision_pairs":vintages,
        "limitations":"Only a mechanistic Markov two-state H2 sensitivity audit, not a refit of country-blocked LOG1P. w grid fixed but considered after examining historical data; using its results to select a w would remain exploratory. Revisions are overlapping releases, so five comparisons are not independent. Later editions can retroactively revise historical origin transitions, though every replay clips all transitions to that origin. History-sensitive risk is not necessarily more accurate. No 2027 labels; the 196 originally issued probabilities of three distinct models and original 15 alerts remain SHA-frozen. No new per-country candidate forecast list is published."
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--check-report",action="store_true")
    args=p.parse_args()
    raw_sources={v:request(SOURCES[v]["url"],MAX_DOWNLOAD)
                 for v in VERSION_ORDER}
    sources={v:parse_counts(raw_sources[v],v) for v in VERSION_ORDER}
    audit_new_issue(
        GLOBAL_ONLY_ISSUE.read_bytes(),GLOBAL_ONLY_MANIFEST.read_bytes(),
        ORIGINAL.read_bytes(),OLD_LOG1P.read_bytes(),
        OLD_LOG1P_MANIFEST.read_bytes(),ALERTS.read_bytes())
    original=json.loads(ORIGINAL.read_text(encoding="utf8"))
    old=json.loads(OLD_LOG1P.read_text(encoding="utf8"))
    new=json.loads(GLOBAL_ONLY_ISSUE.read_text(encoding="utf8"))
    report=study(sources,original,old,new)
    content=json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    print("GEO2027_MARKOV_PARTIAL_POOLING_BEGIN")
    print(content,end="")
    print("GEO2027_MARKOV_PARTIAL_POOLING_END",flush=True)
    if args.check_report and REPORT.read_bytes()!=content.encode():
        raise ValueError("Pinned UCDP Markov partial pooling source-vintage report differs")


if __name__=="__main__":
    main()
