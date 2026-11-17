#!/usr/bin/env python3
"""Tunisia's ORIGINAL disputed 2017 transition (not the 2024 case).

Reconcile the 2014-origin 'first exit' and 2016->2017 1->0 observed state
using seven UCDP GED vintages 17.1..23.1, exact source SHA and official
CY23 country-year support as a retrospective *exposure mask*. This is
a VINTAGE REVISION / EVENT-DEFINITION diagnostic, not a prediction issued
at origin, not a statistical validation and not the older private model.

GED17.1 (through 2016) only released in 2017: no historical prediction
source archive existed at the 2016 cutoff. GED18.1 (2017 outcomes)
released in 2018. The later CY23 support is also an anachronism; it
controls comparisons only, and must not be called true as-of training.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

from audit_geo_legacy_ged_countryyear_bridge import (
    ARCHIVE, PINNED_GED_SHA256, GED_URLS, discover_ged, parse_ged,
)
from audit_geo_ged20_21_coverage_revisions import PINNED_NEW_SHA256, ALL_URLS
from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit as audit_issued,
)
from experiment_geo2027_intensity_markov_cross_release import parse_counts
from backtest_archived_country_vintages import SOURCES
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo-tunisia-original-2017-exit-vintage-diagnostic.json"
GED_VERSIONS=("17.1","18.1","19.1","20.1","21.1","22.1","23.1")
EARLIEST=("17.1","18.1")
GED_PATHS={**ALL_URLS, **{
    v:f"https://ucdp.uu.se/downloads/ged/ged{v.replace('.','')}-csv.zip"
    for v in EARLIEST
}}
PINS={**PINNED_GED_SHA256,**PINNED_NEW_SHA256}
ORIGINAL_ISSUED_COUNTRY_N=196
TUNISIA=616
SYRIA=652
FROZEN_ORIGIN=2016
OBSERVED_TARGET=2017
EARLY_ORIGIN=2014
THRESHOLD=25
SHRINK=20
LAPLACE=1
MAX_ZIP=95_000_000
CY_MAX=8_000_000
# Populate after exact source replay, not from guesswork.
GED_EARLY_SHA256={}


def _frozen_original_ids(issue):
    countries=issue.get("countries")
    if (type(countries) is not list or len(countries)!=196 or
        issue.get("official_2027_outcomes_resolved")!=0):
        raise ValueError("Original 196-country GEO2027 issue not intact")
    ids=[r["country_id"] for r in countries]
    if (ids!=sorted(ids) or len(set(ids))!=196 or
        TUNISIA not in ids or SYRIA not in ids):
        raise ValueError("Tunisia/Syria original GWNO risk set differs")
    return ids


def source_annual_counts(event_sums,year):
    """Return exact event deaths & binary label; require edition year coverage."""
    if type(year) is not int or year not in range(2011,2023):
        raise ValueError("Unsupported historical Tunisian event year")
    best=event_sums.get((TUNISIA,year),0)
    if type(best) is not int or best<0:
        raise ValueError("Invalid GED source mortality")
    return {"best_state_based_deaths":best,
            "active_ge25":int(best>=THRESHOLD)}


def historical_eligible_model(ged,cy_support,cohort,origin):
    """Re-estimate frozen Markov constants with a LATER common support mask.

    Historical CY23 (published 2023!) supplies availability of each
    country-year. Exclude all Syria from both comparison cohort and global
    transition counts because GED17-19 lack Syria territorial coverage.
    Other limits on country-level GED coverage are NOT resolved; all
    probabilities remain ex-post measurement diagnostics.
    """
    if (origin not in (2014,2016) or
        len(cohort)!=195 or SYRIA in cohort or TUNISIA not in cohort or
        len(set(cohort))!=195 or
        not set(cohort).issubset(cy_support)):
        raise ValueError("Invalid fixed-source 195-country diagnostic cohort")
    clipped={}
    for cid,h in cy_support.items():
        if cid==SYRIA:
            continue
        if type(cid) is not int or not 1<=cid<=2000:
            raise ValueError("Malformed UCDP historical GWNO")
        d={y:int(ged.get((cid,y),0)>=THRESHOLD)
           for y in h if y<=origin}
        if d:
            clipped[cid]=d
    if any(origin not in clipped.get(cid,{}) or
           origin-1 not in clipped[cid] for cid in cohort):
        raise ValueError("Country coverage for exact origin years is incomplete")
    global_t=[[0,0],[0,0]]
    tunis_t=[[0,0],[0,0]]
    for cid,h in clipped.items():
        for y in sorted(h):
            if y-1 not in h:
                continue
            a,b=h[y-1],h[y]
            global_t[a][b]+=1
            if cid==TUNISIA:
                tunis_t[a][b]+=1
    if min(sum(r) for r in global_t)<100:
        raise ValueError("Historical global Markov transition exposures insufficient")
    q_global=[(global_t[s][1]+LAPLACE)/(sum(global_t[s])+2*LAPLACE)
              for s in (0,1)]
    q_local=[(tunis_t[s][1]+SHRINK*q_global[s])/
             (sum(tunis_t[s])+SHRINK) for s in (0,1)]
    origin_state=clipped[TUNISIA][origin]
    # Exiting active (10) at the NEXT annual step only applies if
    # original binary state in the training vintage is active.
    p_exit=round(1-q_local[1],12) if origin_state==1 else None
    p_first_exit_in_three=round(q_local[1]**2*(1-q_local[1]),12) if origin_state==1 else None
    p_any_exit_in_three=round(1-q_local[1]**3,12) if origin_state==1 else None
    return {
        "origin":origin,
        "origin_binary_state":origin_state,
        "Tunisia_p_active_next_given_active":round(q_local[1],12),
        "Tunisia_p_exit_next_if_origin_active":p_exit,
        "Tunisia_p_first_exit_exactly_origin_plus_3_if_initially_active":
            p_first_exit_in_three,
        "Tunisia_p_at_least_one_exit_within_3_if_initially_active":
            p_any_exit_in_three,
        "Tunisia_2x2_transition_counts":tunis_t,
        "global_2x2_transition_counts":global_t,
        "global_q_active":q_global,
        "Tunisia_q_active":q_local,
        "training_year_max":max(max(h) for h in clipped.values()),
        "n_global_hist_country_ids":len(clipped),
        "frozen_original_GWNO_minus_Syria_195":True,
        "later_2023_CY_country_year_support_not_historical_asof":True,
        "GED_source_event_zeros_on_CY23_support_are_not_proven_peace":True,
    }


def analyze(original,ged_bytes,archive,cy23,prior):
    ids=_frozen_original_ids(original)
    if (set(ged_bytes)!=set(GED_VERSIONS) or
        any(archive.get(v,{}).get("CSV")!=GED_PATHS[v]
            for v in GED_VERSIONS) or
        prior.get("official_GED23_1_vs_OrganizedViolenceCY23_1_same_version",{}).get(
            "exact_death_count_match_n")!=2352 or
        prior.get("historical_GED_for_original_GEO_CY_predictions_authorized") is not False):
        raise ValueError("Official source vintage catalog, old 23.1 bridge, risk set changed")
    if sorted(set(ids))!=ids or not all(cid in cy23 for cid in ids):
        raise ValueError("Official CY23 historical support or cohort changed")
    source={}
    totals={}
    expected_last=dict(zip(GED_VERSIONS,range(2016,2023)))
    for v in GED_VERSIONS:
        sha=GED_EARLY_SHA256.get(v) or PINS.get(v)
        meta,total=parse_ged(ged_bytes[v],v,expected_sha256=sha)
        if meta["last_recorded_event_year"]!=expected_last[v]:
            raise ValueError("Historical GED official cutoff year differs: "+v)
        source[v]=meta
        totals[v]=total
    # Check original same-release bridge for all 2011-22 years, NOT just one
    if any(totals["23.1"].get((cid,year),0)!=cy23[cid][year]
           for cid in ids for year in range(2011,2023)):
        raise ValueError("Original same-release 2352 GED23 to CY23 bridge failed")
    timeline={}
    for year in range(2013,2019):
        timeline[str(year)]={
            v:source_annual_counts(totals[v],year)
            if year<=expected_last[v] else None
            for v in GED_VERSIONS
        }
    # The actual disputed first EXIT 2016 -> 2017, not H2 2024
    transitions={}
    for v in GED_VERSIONS:
        one=timeline["2016"][v]
        two=timeline["2017"][v]
        transitions[v]={
            "2016":one,
            "2017":two,
            "transition_2016_2017":(
                str(one["active_ge25"])+str(two["active_ge25"])
                if two is not None else None),
            "real_source_has_2017_observed":two is not None,
            "2016_origin_source_available_in_2016":False,
        }
    reference=[transitions[v]["transition_2016_2017"] for v in GED_VERSIONS[1:]]
    if any(t!=reference[0] for t in reference):
        # Keep evidence, not reject. Revision can change the label.
        stable=False
    else:
        stable=True
    cohort=[cid for cid in ids if cid!=SYRIA]
    model2016={v:historical_eligible_model(totals[v],cy23,cohort,FROZEN_ORIGIN)
               for v in GED_VERSIONS}
    model2014={v:historical_eligible_model(totals[v],cy23,cohort,EARLY_ORIGIN)
               for v in GED_VERSIONS}
    # Counterfactual take only 2013..15 Tunisia historic GED21 vs GED22
    # while holding GED22 other countries/years fixed.
    counterfactual=dict(totals["22.1"])
    for y in (2013,2014,2015):
        key=(TUNISIA,y)
        counterfactual[key]=totals["21.1"].get(key,0)
    cf2016=historical_eligible_model(counterfactual,cy23,cohort,FROZEN_ORIGIN)
    cf2014=historical_eligible_model(counterfactual,cy23,cohort,EARLY_ORIGIN)
    def diff(a,b,key):
        if a[key] is None or b[key] is None:
            return None
        return round(a[key]-b[key],12)
    report={
        "schema":"idealab.psico.tunisia_2017_first_exit_GED17_23.v1",
        "status":"RETROSPECTIVE_OFFICIAL_GED_VINTAGE_TRANSITION_DIAGNOSTIC_NOT_AN_ISSUED_PREDICTION",
        "scientific_question":"Did the 2017 Tunisia state-based >=25 1-to-0 exit depend on UCDP source vintage, and how did 2013–15 label revisions affect recreated Markov exit probabilities?",
        "country":"Tunisia",
        "GWNO":TUNISIA,
        "source_edition_GED_zip_sha256":{v:source[v]["sha256"] for v in GED_VERSIONS},
        "source_edition_metadata":source,
        "CY23_original_zip_sha256":SOURCES["23.1"]["sha256"],
        "GED23_equals_CY23_original_2011_to_2022_2352_reconfirmed":True,
        "original_2027_forecast_sha256":SOURCE_SHA256,
        "fixed_195_country_exposure_support_mask_excludes_Syria_GWNO652":True,
        "fixed_195_is_NOT_original_196_issued_cohort":True,
        "origin2016_edition17_1_last_available_data_2016_but_published_2017":True,
        "origin2016_historically_issued_forecast_verified":False,
        "2017_official_event_label_first_release_GED18_1_published_in_2018":True,
        "2013_to_2018_Tunisia_source_fatality_timeline":timeline,
        "2016_to_2017_transition_observations_across_versions":transitions,
        "2017_outcome_state_stable_across_GED18_to_GED23":stable,
        "2016_one_step_exit_model_per_source_edition":model2016,
        "2014_three_step_first_exit_model_per_source_edition":model2014,
        "GED22_model_with_only_Tunisia_2013_2015_reverted_to_GED21": {
            "2016_origin":cf2016,"2014_origin":cf2014,
            "delta_2016_one_step_exit_prob_GED22_minus_counterfactual":
                diff(model2016["22.1"],cf2016,
                     "Tunisia_p_exit_next_if_origin_active"),
            "delta_2014_first_exit_exactly_three_GED22_minus_counterfactual":
                diff(model2014["22.1"],cf2014,
                     "Tunisia_p_first_exit_exactly_origin_plus_3_if_initially_active"),
            "synthetic_hybrid_never_issued_by_UCDP":True,
        },
        "first_exit_from_active_state_requires_active_state_at_origin":True,
        "reconstructed_models_match_original_private_historical_model_asserted":False,
        "current_2027_2028_GEO_issued_predictions_modified":False,
        "new_2027_2028_outcomes_observed":False,
        "new_forecast_probabilities_issued":0,
        "observed_one_transition_cannot_validate_probabilistic_skill":True,
        "precise_historic_source_availability_not_notarized":True,
        "interpretation":(
            "A transition exit 10 means >=25 deaths in 2016 and <25 in 2017. "
            "A probability of exact first exit in 2017 from 2014 is only "
            "defined as active-state first exit if 2014 was itself active "
            "in that source vintage. GED21 vs GED22 reclassifies 2013–15, "
            "including 2014. Any comparison must use the same vintage-defined "
            "event and horizon. This is a source-vintage stress test, not "
            "the original 2016-issued forecast, not calibrated skill and not "
            "an inference of actual causal mechanisms. The 2023 CY support "
            "mask used to align exposure is retrospective and not as-of."
        ),
    }
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--print-report",action="store_true")
    p.add_argument("--check-report",action="store_true")
    args=p.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Original issued 2027 GEO probability vector mutated")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),
                 ORIGINAL.read_bytes(),OLD_SHADOW.read_bytes(),
                 OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    catalog=discover_ged(request(ARCHIVE))
    gedraw={v:request(GED_PATHS[v],MAX_ZIP) for v in GED_VERSIONS}
    cy23=parse_counts(request(SOURCES["23.1"]["url"],8_000_000),"23.1")
    prior=json.loads((ROOT/"data/geo-ged-old-vintage-countryyear-feasibility.json").read_text(encoding="utf8"))
    issue=json.loads(ISSUE.read_text(encoding="utf8"))
    report=analyze(issue,gedraw,catalog,cy23,prior)
    payload=json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    if args.check_report and REPORT.read_bytes()!=payload.encode("utf8"):
        raise ValueError("Exact GED 17–23 Tunisia 2017 transition source replay changed")
    if args.print_report:
        print("GEO_TUNISIA_2017_SOURCE_EXIT_BEGIN",flush=True)
        print(payload,end="")
        print("GEO_TUNISIA_2017_SOURCE_EXIT_END",flush=True)
    else:
        print(json.dumps({
            "GED_versions":GED_VERSIONS,
            "2016_17_source_transition":report[
                "2016_to_2017_transition_observations_across_versions"],
            "2014_first_exit_origin_state":{
                k:v["origin_binary_state"] for k,v in
                report["2014_three_step_first_exit_model_per_source_edition"].items()},
            "not_a_historical_issued_forecast":True,
        },ensure_ascii=False,sort_keys=True,indent=2))


if __name__=="__main__":
    main()
