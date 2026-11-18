#!/usr/bin/env python3
"""Rwanda 2023 historical H2 probability edit: local vs rest-of-world Shapley.

Exact two-group *mechanical* counterfactual source intervention, not causal
interpretation. Original 23.1 vs 24.1 UCDP OrganizedViolenceCY country-year
best-death archives, clipped at pseudo-origin 2021, same four-state Markov
estimator. Groups: Rwanda's own 1989..2021 rows vs all other official source-country rows (including any not in GWNO evaluation cohort).
For each 2x2 combination reconstruct global transition Dirichlet prior and
Rwanda local shrinkage. Exact averaging of both intervention orders.
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
    VERSION_ORDER, EXPECTED_ROWS, MAX_DOWNLOAD, parse_counts,
    four_state_forecast, intensity_state,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
REFERENCE=ROOT/"data/geo-h2-2023-country-origin-vintage-rank-influence.json"
OUTPUT=ROOT/"data/geo-h2-rwanda-2021-23-24-source-shapley.json"
RWANDA=517
ORIGIN=2021
TARGET=2023
N=196
EPS=1e-11


def _clipped(records,cohort):
    if not cohort.issubset(set(records)):
        raise ValueError("Original GWNO risk cohort incomplete in source")
    panel={cid:{yr:deaths for yr,deaths in h.items() if yr<=ORIGIN}
           for cid,h in records.items()}
    if any(not panel[cid] or ORIGIN not in panel[cid] or ORIGIN-1 not in panel[cid] for cid in cohort):
        raise ValueError("Missing state transitions in fixed 196-country source")
    return panel


def evaluate(old_source,new_source,reference):
    if (reference.get("schema") !=
        "idealab.psico.geo_h2_2023_country_origin_vintage_rank_attribution.v1"
        or reference.get("country_n")!=N
        or reference.get("target_year")!=TARGET
        or reference.get("origin_year")!=ORIGIN
        or reference.get("common_official_outcome_release")!="26.1"
        or reference.get("prospective_skill_claimed") is not False
        or reference.get("original_GEO2027_issued_sha256")!=SOURCE_SHA256
        or reference.get("source_ZIP_sha256") !=
             {v:SOURCES[v]["sha256"] for v in VERSION_ORDER}):
        raise ValueError("Frozen previous country-replayed original issue mismatch")
    ids={x["country_id"] for x in json.loads(ISSUE.read_text(encoding="utf-8"))["countries"]}
    if len(ids)!=N or RWANDA not in ids:
        raise ValueError("Frozen GWNO origin country IDs invalid")
    old=_clipped(old_source,ids)
    new=_clipped(new_source,ids)
    if set(old)!=set(new):
        raise ValueError("Source countries differ: source coverage must be comparable")
    own_old=old[RWANDA]
    own_new=new[RWANDA]
    edits=[]
    annual_diff_n=0
    state_diff_n=0
    for cid in sorted(old):
        if set(old[cid])!=set(new[cid]):
            raise ValueError("Country-year coverage changed: no common panel")
        for year in sorted(old[cid]):
            x=old[cid][year]
            y=new[cid][year]
            if x!=y:
                annual_diff_n+=1
                state_diff_n+=int(intensity_state(x)!=intensity_state(y))
                edits.append({"GWNO":cid,"year":year,"old_best_deaths":x,
                              "new_best_deaths":y,
                              "old_four_state":intensity_state(x),
                              "new_four_state":intensity_state(y)})
    own_changes=[x for x in edits if x["GWNO"]==RWANDA]
    # Four 2x2 combinations, no training algorithm modifications.
    predicted={}
    source_provenance={}
    for use_own in (0,1):
        for use_other in (0,1):
            mix={cid:(new[cid] if (use_own if cid==RWANDA else use_other)
                      else old[cid])
                 for cid in sorted(old)}
            f,meta=four_state_forecast(
                mix,ORIGIN,historical_rolling_diagnostic=True)
            if (meta["cutoff_max"]!=ORIGIN or meta["eligible_countries"]!=N
                or set(f)!=ids):
                raise AssertionError("Time or risk-set mismatch")
            p=f[RWANDA]["p_intensity_markov"]
            predicted[f"{use_own}{use_other}"]=p
            source_provenance[f"{use_own}{use_other}"]={
                "rwanda_source":("24.1" if use_own else "23.1"),
                "other_source_countries":("24.1" if use_other else "23.1"),
                "origin_four_state":f[RWANDA]["origin_intensity_state"],
                "rwanda_H2_probability":p,
                "global_4x4_transition_counts":meta["global_4x4_transitions"],
            }
    rec=next((x for x in reference["country_observations"]
              if x["GWNO"]==RWANDA),None)
    if not rec or rec["label_best_26_1"]!=0:
        raise ValueError("Rwanda original observed country-level label missing")
    if (not math.isclose(predicted["00"],rec["p_fourstate_origin23_1"],abs_tol=EPS,rel_tol=0)
        or not math.isclose(predicted["11"],rec["p_fourstate_origin24_1"],abs_tol=EPS,rel_tol=0)):
        raise AssertionError("Exact Rwanda historical H2 probabilities not reproduced")
    total=predicted["11"]-predicted["00"]
    own=0.5*((predicted["10"]-predicted["00"])+(predicted["11"]-predicted["01"]))
    others=0.5*((predicted["01"]-predicted["00"])+(predicted["11"]-predicted["10"]))
    interaction=predicted["11"]-predicted["10"]-predicted["01"]+predicted["00"]
    if not math.isclose(total,own+others,abs_tol=1e-12,rel_tol=0):
        raise AssertionError("Shapley effect does not sum to original H2 revision")
    # All other rows may move global prior even if Rwanda local rows never change.
    return {
        "schema":"idealab.psico.geo_h2_rwanda_origin_vintage_twofactor_shapley.v1",
        "status":"SHA_REPLAYED_RETROSPECTIVE_SOURCE_EDIT_NOT_PROSPECTIVE",
        "source_versions":["23.1","24.1"],
        "source_SHA256":{"23.1":SOURCES["23.1"]["sha256"],
                         "24.1":SOURCES["24.1"]["sha256"]},
        "original_GEO2027_issue_sha256":SOURCE_SHA256,
        "GWNO":RWANDA,"origin_year":ORIGIN,"target_year":TARGET,
        "countries":N,
        "source_training_countries":len(old),
        "rest_of_source_training_countries":len(old)-1,
        "historical_source_country_year_death_count_edit_n":annual_diff_n,
        "historical_source_four_state_label_edit_n":state_diff_n,
        "rwanda_annual_fatality_revisions":own_changes,
        "rwanda_revised_count_n":len(own_changes),
        "source_revised_country_years":edits,
        "counterfactual_source_combinations":source_provenance,
        "p_fourstate_original":predicted["00"],
        "p_fourstate_revised":predicted["11"],
        "observed_probability_shift":total,
        "rwanda_local_source_shapley":own,
        "other_source_countries_shapley":others,
        "local_other_interaction":interaction,
        "no_historical_probabilities_actually_issued_in_2021":True,
        "new_prospective_forecasts_emitted":0,
        "caveat":"Exact algebraic two-block source intervention under fixed estimator and 2021 clipping. Other countries' revisions can change the global transition prior; this does not causally attribute historical violence or isolate any single global row. Model reconstructed with archives not available at simulated origin.",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    ap.add_argument("--print-report",action="store_true")
    args=ap.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("GEO2027 source issued vector changed")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),
                 ORIGINAL.read_bytes(),OLD_SHADOW.read_bytes(),
                 OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    raw={v:request(SOURCES[v]["url"],MAX_DOWNLOAD) for v in ("23.1","24.1")}
    counts={v:parse_counts(raw[v],v) for v in raw}
    if any(sum(map(len,counts[v].values()))!=EXPECTED_ROWS[v] for v in raw):
        raise ValueError("Incorrect source country-year count")
    result=evaluate(counts["23.1"],counts["24.1"],
                    json.loads(REFERENCE.read_text(encoding="utf-8")))
    payload=json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    if args.check_report and json.loads(OUTPUT.read_text(encoding="utf-8"))!=result:
        raise ValueError("Stored Rwanda vintage attribution differs from original replay")
    if args.print_report:
        print("GEO_RWANDA_SHAPLEY_BEGIN",flush=True)
        print(payload,end="")
        print("GEO_RWANDA_SHAPLEY_END",flush=True)
    else:
        print(json.dumps({k:result[k] for k in (
            "rwanda_revised_count_n","historical_source_four_state_label_edit_n",
            "observed_probability_shift","rwanda_local_source_shapley",
            "other_source_countries_shapley")},sort_keys=True))


if __name__=="__main__":
    main()
