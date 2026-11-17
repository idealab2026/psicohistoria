#!/usr/bin/env python3
"""Tunisia GED 2013-2015 historical label revision -> GEO H2 mechanical attribution.

Two separate questions:
(1) At SAME pseudo-origin 2019, GED20.1/21.1/22.1/23.1 clipped to
2019 cause what changes in original binary vs fixed four-state probability?
Exact Shapley of GED21.1 -> GED22.1 across four *mechanical source edits*:
the 2013, 2014, 2015 Tunisia counts and all other retrospective edits.
(2) At the frozen 2022 -> 2024 H2 UCDP23.1 -> UCDP25.1 historical
fold, how much would only the three Tunisian *past* rows affect the
original two model predictions / squared errors in a hypothetical edit?

None of these forecasts was issued at the pseudo-origin. EDGES are mechanical
source-data sensitivity under an unchanged estimator, not causal claims about
historical violence or forecasting skill. Do not replace registered forecasts.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit as audit_issued,
)
from audit_geo_legacy_ged_countryyear_bridge import (
    ARCHIVE, GED_URLS, PINNED_GED_SHA256,
    discover_ged, parse_ged,
)
from audit_geo_ged20_21_coverage_revisions import (
    ALL_URLS, PINNED_NEW_SHA256,
)
from backtest_archived_country_vintages import SOURCES
from diagnose_geo2028_historical_forecast_vintage_drift import _fit_at_origin
from experiment_geo2027_intensity_markov_cross_release import (
    counts_to_binary, four_state_forecast, parse_counts,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo-ged-tunisia-2013-15-h2-attribution.json"
BRIDGE=ROOT/"data/geo-ged-old-vintage-countryyear-feasibility.json"
REVISIONS=ROOT/"data/geo-ged-20-21-coverage-revisions.json"
H2=ROOT/"data/geo2027-h2-fatality-estimate-brier-sensitivity.json"
GED_VINTAGES=("20.1","21.1","22.1","23.1")
TUNISIA=616
CHANGED_YEARS=(2013,2014,2015)
MIN_YEAR=1989
EARLY_ORIGIN=2019
HIST_ORIGIN=2022
HIST_TARGET=2024
MAX_ZIP=95_000_000
MODELS=("binary","four_state")
N=196
EPS=1.01e-10


def _check_issues(issue, bridge, revisions, h2):
    countries=issue.get("countries",[])
    ids=[r["country_id"] for r in countries]
    if (len(ids)!=N or ids!=sorted(ids) or len(set(ids))!=N or
        TUNISIA not in ids or issue.get("official_2027_outcomes_resolved")!=0 or
        bridge.get("schema")!="idealab.psico.legacy_ged_to_countryyear_equivalence_feasibility.v1" or
        bridge.get("official_GED23_1_vs_OrganizedViolenceCY23_1_same_version",{}).get(
            "exact_death_count_match_n")!=2352 or
        bridge.get("GED19_1_syria_exclusion",{}).get(
            "missing_GED19_state_based_25_country_years")!=8 or
        revisions.get("schema")!="idealab.psico.ged_20_21_intervintage_coverage_2011_2022.v1" or
        revisions.get("source_zip_sha256")!={**PINNED_GED_SHA256,**PINNED_NEW_SHA256} or
        revisions.get("historical_model_fitting_authorized") is not False or
        h2.get("schema")!="idealab.psico.geo_h2_crossrelease_fatality_label_sensitivity.v1" or
        h2.get("prospective_skill_demonstrated") is not False):
        raise ValueError("Original research anchors or fixed 196 GWNO changed")
    revisions_pair=next(
        x for x in revisions["pairs"] if
        x["old_version"]=="21.1" and x["new_version"]=="22.1")
    flips=[r for r in revisions_pair["comparison"]["binary_flip_details"]
           if r["GWNO"]==TUNISIA]
    if ([r["target_year"] for r in flips]!=list(CHANGED_YEARS) or
        [(r["old_best_statebased_deaths"],r["new_best_statebased_deaths"])
         for r in flips]!=[(0,29),(0,51),(17,75)]):
        raise ValueError("Tunisia exact GED21-to-22 2013-15 revision anchor changed")
    return ids


def _event_panel(sums, ids, *,max_year):
    """Full numeric panel; zeros mean 'no recorded state-based GED event'.

    GED 20.1 onward explicitly covers Syria. Other territorial missingness
    can persist; hence model is a diagnostic, never a genuine as-of forecast.
    """
    if max_year not in (2019,2022):
        raise ValueError("Unexpected country-year pseudo-origin")
    ids=sorted(ids)
    if len(ids)!=N or len(set(ids))!=N:
        raise ValueError("Risk set changed")
    for (cid,year),deaths in sums.items():
        if type(cid) is not int or type(year) is not int or type(deaths) is not int or deaths<0:
            raise ValueError("Malformed source event panel")
    return {cid:{year:sums.get((cid,year),0)
                 for year in range(MIN_YEAR,max_year+1)} for cid in ids}


def _probabilities(panel, year, ids):
    if sorted(panel)!=sorted(ids) or len(panel)!=N:
        raise ValueError("Fixed 196-country model riskset changed")
    binary, bmeta=_fit_at_origin(
        counts_to_binary(panel),year,fixed_cohort=ids)
    four, fmeta=four_state_forecast(
        panel,year,historical_rolling_diagnostic=(year!=2022))
    if (bmeta["last_training_year"]!=year or
        fmeta["cutoff_max"]!=year or
        set(binary)!=set(ids) or set(four)!=set(ids) or
        binary[TUNISIA]["origin_state"]!=four[TUNISIA]["origin_state"]):
        raise ValueError("Source cutoff, original model or cohort leaked")
    probs={
        "binary":binary[TUNISIA]["p_model_h2"],
        "four_state":four[TUNISIA]["p_intensity_markov"],
    }
    return {
        "p":probs,
        "origin_binary_state":binary[TUNISIA]["origin_state"],
        "origin_intensity_state":four[TUNISIA]["origin_intensity_state"],
        "country_binary_transition_q_local":binary[TUNISIA]["q_local"],
        "global_binary_transition_counts":bmeta["global_transition_counts"],
        "global_four_state_transition_counts":fmeta["global_4x4_transitions"],
        "last_training_year":year,
    }


def _shapley21to22(old, new, ids):
    """Exact 2^4 factorial attribution; feature 0 is every other source edit.

    Shapley computes how predictions change mechanically; does NOT attribute
    a real-world causal effect to the violence or revisions. Rounding at
    twelve digits is carried through and checked within EPS.
    """
    bits={0:"all_other_source_edits",1:"tunisia_2013",2:"tunisia_2014",3:"tunisia_2015"}
    panel_cache={}
    for mask in range(16):
        all_other=bool(mask&1)
        panel=copy.deepcopy(new if all_other else old)
        for j,year in enumerate(CHANGED_YEARS, start=1):
            panel[TUNISIA][year]=new[TUNISIA][year] if mask&(1<<j) else old[TUNISIA][year]
        panel_cache[mask]=_probabilities(panel,EARLY_ORIGIN,ids)
    effects={model:{} for model in MODELS}
    factor=math.factorial(4)
    for model in MODELS:
        for j,name in bits.items():
            total=0.
            for subset in range(16):
                if subset&(1<<j):
                    continue
                n=subset.bit_count()
                weight=math.factorial(n)*math.factorial(3-n)/factor
                total+=weight*(panel_cache[subset|(1<<j)]["p"][model]-
                               panel_cache[subset]["p"][model])
            effects[model][name]=round(total,12)
        actual=panel_cache[15]["p"][model]-panel_cache[0]["p"][model]
        if abs(sum(effects[model].values())-actual)>EPS:
            raise AssertionError("Four-factor Shapley attribution does not telescope")
    return {
        "intervention_bits":bits,
        "coalition_n":16,
        "model_shapley_H2_probability_changes":effects,
        "old_full":panel_cache[0],
        "revised_full":panel_cache[15],
        "old_only_Tunisia_three_year_edits":panel_cache[14],
        "revised_all_except_Tunisia_three_year_edits":panel_cache[1],
        "exact_four_factor_telescope_up_to_1e_10":True,
        "not_world_causal_or_real_asof_issued_predictions":True,
    }


def _revised2022(vintage21, cy23, ids, target2024, frozen_h2):
    """Actual 2022->24 archival fold plus explicit impossible-to-issue edit.

    Counterfactual: replace just Tunisia 2013-15 source deaths in an
    otherwise official UCDP23.1 panel, never retrain/change original issue.
    """
    if (set(cy23)!=set(ids) or not all(
        year in cy23[cid] for cid in ids for year in (2011,2022))
    ):
        raise ValueError("Official CY23 risk cohort missing")
    if not 0<=target2024:
        raise ValueError("Missing official Tunisia 2024 outcome")
    original=_probabilities(cy23,HIST_ORIGIN,ids)
    changed=copy.deepcopy(cy23)
    for y in CHANGED_YEARS:
        changed[TUNISIA][y]=vintage21[TUNISIA][y]
    hypothetical=_probabilities(changed,HIST_ORIGIN,ids)
    exact={
        "2022_original_UCDP23_1":original,
        "2022_counterfactual_CY23_replaced_Tunisia_2013_15_from_GED21_1":
            hypothetical,
        "2024_UCDP25_1_Tunisia_best_state_based_deaths":target2024,
        "2024_UCDP25_1_Tunisia_best_ge25_label":int(target2024>=25),
        "counterfactual_not_a_registered_or_contemporaneously_issued_2022_forecast":
            True,
    }
    y=int(target2024>=25)
    change={}
    for model in MODELS:
        p=original["p"][model]
        q=hypothetical["p"][model]
        change[model]={
            "original_H2_probability":p,
            "hypothetical_H2_probability":q,
            "original_minus_hypothetical_probability":round(p-q,12),
            "original_single_country_squared_error":(p-y)**2,
            "hypothetical_single_country_squared_error":(q-y)**2,
            "squared_error_original_minus_hypothetical":(p-y)**2-(q-y)**2,
        }
    exact["per_model"]=change
    anchor=next(f for f in frozen_h2["folds"] if f["origin_year"]==2022)
    if (anchor["target_year"]!=2024 or anchor["origin_edition"]!="23.1" or
        anchor["target_edition"]!="25.1"):
        raise ValueError("Exact original source release-separated 2024 historical fold changed")
    return exact


def evaluate(sources, cy23, cy25, archive, issue, bridge, revisions, frozen_h2):
    ids=_check_issues(issue,bridge,revisions,frozen_h2)
    if set(sources)!=set(GED_VINTAGES) or (
        any(archive.get(v,{}).get("CSV")!=ALL_URLS[v] for v in GED_VINTAGES)
    ):
        raise ValueError("Official GED source vintage URLs were replaced")
    meta={}
    event_sums={}
    for v in GED_VINTAGES:
        pin=PINNED_NEW_SHA256.get(v) or PINNED_GED_SHA256.get(v)
        meta[v],event_sums[v]=parse_ged(sources[v],v,expected_sha256=pin)
    if [meta[v]["last_recorded_event_year"] for v in GED_VINTAGES] != [
        2019,2020,2021,2022]:
        raise ValueError("Historical source years not the original five-vintage audit")
    if not set(cy23)==set(ids) or cy23[TUNISIA][2022] is None:
        raise ValueError("Official 23.1 country-year original cohort changed")
    if 2024 not in cy25[TUNISIA]:
        raise ValueError("Missing historic 2024 Tunisia outcome from UCDP25.1")
    # GED23 to CY23 exact across the original 2011..2022 fixed cohort.
    if any(event_sums["23.1"].get((cid,year),0)!=cy23[cid][year]
           for cid in ids for year in range(2011,2023)):
        raise ValueError("Previously audited exact GED23-to-CY23 bridge changed")
    panel={v:_event_panel(event_sums[v],ids,max_year=EARLY_ORIGIN)
           for v in GED_VINTAGES}
    observed={v:_probabilities(panel[v],EARLY_ORIGIN,ids)
              for v in GED_VINTAGES}
    years={str(y):{
        v:{
            "GED_recorded_best_deaths":panel[v][TUNISIA][y],
            "GED_recorded_state_ge25":int(panel[v][TUNISIA][y]>=25),
        } for v in GED_VINTAGES
    } for y in CHANGED_YEARS}
    if [(panel["21.1"][TUNISIA][y],panel["22.1"][TUNISIA][y])
        for y in CHANGED_YEARS]!=[(0,29),(0,51),(17,75)]:
        raise ValueError("Prior Tunisia official 2013–2015 revisions changed")
    attribution=_shapley21to22(panel["21.1"],panel["22.1"],ids)
    for name,observed_model in (("21.1","old_full"),("22.1","revised_full")):
        if attribution[observed_model]["p"]!=observed[name]["p"]:
            raise ValueError("Shapley coalition no longer matches actual official edition")
    if any(observed[v]["last_training_year"]!=EARLY_ORIGIN for v in GED_VINTAGES):
        raise ValueError("Post-origin source observations leaked into training")
    # GED23 and CY23 historical 1989..2019 source counts may differ despite
    # exact previous 2011..2022 anchor; audit rather than silently elide.
    full=range(MIN_YEAR,EARLY_ORIGIN+1)
    mismatch=[(cid,y) for cid in ids for y in full if
              event_sums["23.1"].get((cid,y),0)!=cy23[cid][y]]
    cy2022=_revised2022(panel["21.1"],cy23,ids,cy25[TUNISIA][HIST_TARGET],frozen_h2)
    report={
        "schema":"idealab.psico.ged_tunisia_2013_15_h2_source_revision_attribution.v1",
        "status":"SHA_VERIFIED_MECHANICAL_SOURCE_REVISION_COUNTERFACTUAL_NOT_ISSUED_FORECAST",
        "sources_GED_SHA256":{v:meta[v]["sha256"] for v in GED_VINTAGES},
        "source_organizedCY23_1_SHA256":SOURCES["23.1"]["sha256"],
        "source_organizedCY25_1_SHA256":SOURCES["25.1"]["sha256"],
        "original_GEO2027_first_issue_SHA256":SOURCE_SHA256,
        "fixed_GWNO_196":True,
        "focus":{"GWNO":TUNISIA,"country":"Tunisia",
                 "historically_revised_annual_best_deaths_by_GED_vintage":years},
        "all_models_same_predeclared_original_parameters":True,
        "binary_country_markov_laplace1_global_shrink20":True,
        "four_state_dirichlet1_global_shrink20":True,
        "source_clip_at_pseudo_origin_2019_verified":True,
        "GED_sources_released_after_2019_pseudo_origin":True,
        "early_pseudo_origin":EARLY_ORIGIN,
        "early_target_H2":2021,
        "early_origin_source_editions":{
            v:{"last_source_recorded_year":meta[v]["last_recorded_event_year"],
               **observed[v]} for v in GED_VINTAGES},
        "exact_shapley_GED21_1_to_GED22_1_2019_H2":attribution,
        "CY23_GED23_1989_to_2019_source_count_mismatch_n":len(mismatch),
        "CY23_GED23_1989_to_2019_count_mismatches_first_10":[
            {"GWNO":cid,"year":y,
             "ged_best":event_sums["23.1"].get((cid,y),0),
             "cy_best":cy23[cid][y]} for cid,y in mismatch[:10]],
        "CY23_GED23_2011_to_2022_original_2352_exact":True,
        "source_2022_origin_H2_2024_Tunisia_historical_diagnostic":cy2022,
        "historical_forecasts_actually_issued_at_2019_or_2022":False,
        "original_2025_origin_future_2027_2028_forecasts_changed":False,
        "new_prospective_probabilities_issued":0,
        "no_2027_or_2028_realized_outcomes":True,
        "no_probabilistic_inference_one_country_one_target":True,
        "explanation":(
            "The Shapley source-edit factors isolate three Tunisian pre-2019 "
            "historical source rows from all other observed GED21->22 changes. "
            "Their contribution is an exact deterministic counterfactual "
            "under fixed model rules, NOT a causal real-world violence effect. "
            "The 2022->2024 retrospective diagnostic replaces only three rows "
            "in the official 23.1 training panel with archived GED21 values. "
            "That hybrid is a hypothetical dataset never issued by UCDP. "
            "No actual registered historical forecast existed. One Tunisia "
            "squared error is not evidence of general forecasting skill."
        ),
    }
    return report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--print-report",action="store_true")
    ap.add_argument("--check-report",action="store_true")
    args=ap.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Original registered GEO2027 issued probabilities modified")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),
                 ORIGINAL.read_bytes(),OLD_SHADOW.read_bytes(),
                 OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    catalog=discover_ged(request(ARCHIVE))
    sources={v:request(ALL_URLS[v],MAX_ZIP) for v in GED_VINTAGES}
    cyraw={v:parse_counts(request(SOURCES[v]["url"],8_000_000),v)
           for v in ("23.1","25.1")}
    docs=[json.loads(p.read_text(encoding="utf8"))
          for p in (ISSUE,BRIDGE,REVISIONS,H2)]
    report=evaluate(sources,*[cyraw[v] for v in ("23.1","25.1")],
                    catalog,*docs)
    encoded=json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    if args.check_report and REPORT.read_bytes()!=encoded.encode("utf8"):
        raise ValueError("Exact UCDP GED Tunisia 2013-15 Shapley source replay differs")
    if args.print_report:
        print("GEO_GED_TUNISIA_ATTRIBUTION_BEGIN",flush=True)
        print(encoded,end="")
        print("GEO_GED_TUNISIA_ATTRIBUTION_END",flush=True)
    else:
        print(json.dumps({
            "Tunisia_2013_15":report["focus"],
            "early_model_probabilities":{
                v:report["early_origin_source_editions"][v]["p"]
                for v in GED_VINTAGES},
            "shapley":report["exact_shapley_GED21_1_to_GED22_1_2019_H2"][
                "model_shapley_H2_probability_changes"],
            "2022_to_2024":report[
                "source_2022_origin_H2_2024_Tunisia_historical_diagnostic"]["per_model"],
            "historic_prediction_was_issued":False,
        },indent=2,sort_keys=True))


if __name__=="__main__":
    main()
