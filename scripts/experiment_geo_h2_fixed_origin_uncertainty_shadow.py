#!/usr/bin/env python3
"""GEO H2 fixed 10% origin-state uncertainty shadow and historical diagnostics.

Predefined mechanical stress: for each origin state 0 or 1, place 90% mass
on its recorded state and 10% on the adjacent 1 or 0; states 2/3 unchanged.
Do NOT calibrate weight on historical outcome or cross-edition revisions.
Same frozen 4-state H2 Markov transitions, evaluated at unchanged cutoff.

Retrospective 2012..2022 pseudo-origins across UCDP 23.1/24.1 and fixed
26.1 target labels 2014..2024; not genuine historical issue-date validation.
A NEW prospective shadow is first produced with UCDP26.1 <=2025, target
2027, compared against a newly calculated hard-state four-state comparator,
and never replaces any original GEO2027 issue.
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
    MAX_DOWNLOAD, EXPECTED_ROWS, STATES, ACTIVE, LAPLACE, SHRINK,
    VERSION_ORDER, intensity_state, parse_counts, four_state_forecast,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
ANCHOR=ROOT/"data/geo-h2-origin-vintage-only-brier-rank.json"
REPORT=ROOT/"data/geo-h2-origin-state-10pct-uncertainty-shadow.json"
ORIGINS=tuple(range(2012,2023))
SOURCE_OLD="23.1"
SOURCE_NEW="24.1"
TARGET_RELEASE="26.1"
PROSPECTIVE_ORIGIN=2025
PROSPECTIVE_TARGET=2027
LAMBDA=0.10
N=196
TRAIN=199
EPS=1e-10


def compute_probabilities(records,origin,issue_ids):
    """Exactly reconstruct published original 4-state transition math.

    Return BOTH categorical conditional P(active at H2 | initial state=s)
    and hard-state P; conditional rows are reused unchanged by the shadow.
    """
    histories={cid:{yr:intensity_state(deaths) for yr,deaths in h.items()
                    if yr<=origin} for cid,h in records.items()}
    if (set(histories)!=set(records) or len(histories)!=TRAIN
        or len(issue_ids)!=N or not set(issue_ids).issubset(histories)
        or any(origin not in histories[c] or origin-1 not in histories[c]
               for c in issue_ids)):
        raise ValueError("Original 199-country source and 196-country risk set invalid")
    global_counts=[[0]*STATES for _ in range(STATES)]
    local={}
    for cid,h in histories.items():
        c=[[0]*STATES for _ in range(STATES)]
        for year in sorted(h):
            if year-1 in h:
                s,t=h[year-1],h[year]
                c[s][t]+=1
                global_counts[s][t]+=1
        local[cid]=c
    if any(sum(row)<10 for row in global_counts):
        raise ValueError("Untrained global intensity state")
    g=[[(global_counts[s][t]+LAPLACE)/
        (sum(global_counts[s])+STATES*LAPLACE)
        for t in range(STATES)] for s in range(STATES)]
    result={}
    for cid in sorted(issue_ids):
        c=local[cid]
        q=[[(c[s][t]+SHRINK*g[s][t])/
            (sum(c[s])+SHRINK) for t in range(STATES)]
           for s in range(STATES)]
        conditional=[sum(q[s][j]*sum(q[j][a] for a in ACTIVE)
                         for j in range(STATES))
                     for s in range(STATES)]
        st=histories[cid][origin]
        hard=round(conditional[st],12)
        shadow=round((1-LAMBDA)*conditional[st]+
                     LAMBDA*conditional[1-st],12) if st in (0,1) else hard
        if any(not math.isfinite(x) or not 0<x<1 for x in (hard,shadow)):
            raise AssertionError("Forecast outside open probability interval")
        result[cid]={
            "origin_intensity_state":st,
            "origin_year":origin,
            "p_original_four_state":hard,
            "p_uncertain_origin_shadow":shadow,
            "difference_shadow_minus_original":shadow-hard,
        }
    return result


def analyze(sources,issue_ids,reference):
    if (reference.get("schema")!="idealab.psico.geo_h2_origin_vintage_only_brier_rank.v1"
        or reference.get("historical_issued_asof_evidence") is not False
        or reference.get("held_fixed_outcome_release")!=TARGET_RELEASE
        or reference.get("original_GEO2027_issue_SHA256")!=SOURCE_SHA256
        or reference.get("country_n")!=N
        or reference.get("official_UCDP_ZIP_sha256")!=
            {v:SOURCES[v]["sha256"] for v in VERSION_ORDER}
        or reference.get("historical_targets")!=list(range(2014,2025))
        or len(issue_ids)!=N or len(set(issue_ids))!=N):
        raise ValueError("Frozen archival Brier experiment and original issue mismatch")
    annual={}
    for origin in ORIGINS:
        target=origin+2
        src={}
        for version in (SOURCE_OLD,SOURCE_NEW):
            vec=compute_probabilities(sources[version],origin,issue_ids)
            # Independent original implementation must agree to 12 decimals.
            original,meta=four_state_forecast(
                sources[version],origin,historical_rolling_diagnostic=True)
            if (meta["cutoff_max"]!=origin or set(original)!=set(issue_ids)
                or any(original[c]["p_intensity_markov"]!=
                       vec[c]["p_original_four_state"] for c in issue_ids)):
                raise AssertionError("Original Markov 4-state reference not reproduced")
            source_rows=[]
            for cid in sorted(issue_ids):
                if target not in sources[TARGET_RELEASE].get(cid,{}):
                    raise ValueError("Missing outcome cannot be imputed zero")
                y=int(sources[TARGET_RELEASE][cid][target]>=25)
                row=vec[cid]
                source_rows.append({
                    "GWNO":cid,"target_26_1_binary":y,
                    "origin_intensity_state":row["origin_intensity_state"],
                    "p_original_four_state":row["p_original_four_state"],
                    "p_uncertain_origin_shadow":row["p_uncertain_origin_shadow"],
                    "brier_original":(row["p_original_four_state"]-y)**2,
                    "brier_shadow":(row["p_uncertain_origin_shadow"]-y)**2,
                })
            src[version]=source_rows
        by_version={v:{r["GWNO"]:r for r in rows} for v,rows in src.items()}
        rold,rnew=by_version[SOURCE_OLD],by_version[SOURCE_NEW]
        fold=next(x for x in reference["annual"] if x["target_year"]==target)
        per={}
        for version,rows in src.items():
            hard=sum(x["brier_original"] for x in rows)/N
            soft=sum(x["brier_shadow"] for x in rows)/N
            ref_key=("old_origin_fixed_target_26_1_brier"
                     if version==SOURCE_OLD else
                     "new_origin_fixed_target_26_1_brier")
            if not math.isclose(
                hard,fold[ref_key]["four_state_intensity"],abs_tol=EPS,rel_tol=0):
                raise AssertionError("Historical Brier hard model does not reproduce prior audit")
            per[version]={
                "mean_brier_hard":hard,
                "mean_brier_uncertain_shadow":soft,
                "shadow_minus_hard_brier":soft-hard,
                "changed_prediction_n":sum(
                    r["p_original_four_state"]!=r["p_uncertain_origin_shadow"]
                    for r in rows),
            }
        p_hard=[rnew[c]["p_original_four_state"]-rold[c]["p_original_four_state"]
                for c in sorted(issue_ids)]
        p_soft=[rnew[c]["p_uncertain_origin_shadow"]-rold[c]["p_uncertain_origin_shadow"]
                for c in sorted(issue_ids)]
        per["source_vintage_probability_stability"]={
            "mean_absolute_hard":sum(map(abs,p_hard))/N,
            "mean_absolute_uncertain_shadow":sum(map(abs,p_soft))/N,
            "max_absolute_hard":max(map(abs,p_hard)),
            "max_absolute_uncertain_shadow":max(map(abs,p_soft)),
            "country_cases_with_smaller_absolute_shadow_drift":sum(
                abs(s)<abs(h) for s,h in zip(p_soft,p_hard)),
            "country_cases_with_larger_absolute_shadow_drift":sum(
                abs(s)>abs(h) for s,h in zip(p_soft,p_hard)),
            "source_revision_origin_state_disagreement_zero_low_GWNO":sorted(
                cid for cid in issue_ids
                if {rold[cid]["origin_intensity_state"],
                    rnew[cid]["origin_intensity_state"]}=={0,1}),
        }
        annual[target]=per
    # New prospective issue only, never overwriting original issued forecast.
    future=compute_probabilities(sources[TARGET_RELEASE],
                                 PROSPECTIVE_ORIGIN,issue_ids)
    prospective=[{"GWNO":cid,**future[cid]} for cid in sorted(issue_ids)]
    pooled={}
    for version in (SOURCE_OLD,SOURCE_NEW):
        pooled[version]={
            "mean_hard_brier":sum(annual[y][version]["mean_brier_hard"]
                                   for y in annual)/len(annual),
            "mean_shadow_brier":sum(annual[y][version]["mean_brier_uncertain_shadow"]
                                     for y in annual)/len(annual),
            "mean_delta_shadow_minus_hard":sum(
                annual[y][version]["shadow_minus_hard_brier"] for y in annual)/len(annual),
        }
    pooled["cross_source_drift"]={
        k:sum(annual[y]["source_vintage_probability_stability"][k]
              for y in annual)/len(annual)
        for k in ("mean_absolute_hard","mean_absolute_uncertain_shadow")}
    return {
        "schema":"idealab.psico.geo_h2_fixed10pct_origin_state_uncertainty.v1",
        "status":"RETROSPECTIVE_STRESS_PLUS_NEW_PROSPECTIVE_UNSCORED_SHADOW",
        "method":"For initial state 0 or 1 only: 90% recorded four-state H2 probability and 10% counterfactual adjacent-state probability under identical transition matrix. States 2/3 unchanged.",
        "lambda_assumed_a_priori_not_fitted":LAMBDA,
        "lambda_not_empirically_calibrated":True,
        "source_sha256":{v:SOURCES[v]["sha256"] for v in VERSION_ORDER},
        "original_GEO2027_source_sha256":SOURCE_SHA256,
        "historical_origins":list(ORIGINS),
        "historical_targets":sorted(annual),
        "historical_outcome_fixed_source":TARGET_RELEASE,
        "historical_annual":{str(y):annual[y] for y in sorted(annual)},
        "historical_pooled":pooled,
        "retrospective_not_genuine_origin_date_issue":True,
        "new_prospective_shadow":{
            "pseudo_issue_class":"NEW_DISTINCT_FOURSTATE_10PCT_2027_SHADOW",
            "origin_year":PROSPECTIVE_ORIGIN,
            "target_year":PROSPECTIVE_TARGET,
            "origin_source":"26.1",
            "country_n":N,
            "probabilities":prospective,
            "outcomes_2027_available":False,
            "prospective_skill_evaluated":False,
            "may_replace_original_GEO2027_or_GEO2028":False,
        },
        "original_issued_GEO2027_or_GEO2028_modified":False,
        "limitations":"Fixed 10% categorical-state uncertainty is a declared sensitivity assumption, not a calibrated posterior. Historical 23.1/24.1 editions postdate many pseudo-origins; only cutoff masking is strict, not historical publication as-of. Unscored new 2027 shadow must be independently timestamped before 2027 outcome labels become available.",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    ap.add_argument("--print-report",action="store_true")
    args=ap.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Original GEO2027 issue altered")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    raw={v:request(SOURCES[v]["url"],MAX_DOWNLOAD) for v in VERSION_ORDER}
    sources={v:parse_counts(raw[v],v) for v in VERSION_ORDER}
    if any(sum(map(len,sources[v].values()))!=EXPECTED_ROWS[v]
           for v in VERSION_ORDER):
        raise ValueError("UCDP original official archives changed")
    ids=[c["country_id"] for c in json.loads(ISSUE.read_text())["countries"]]
    result=analyze(sources,ids,json.loads(ANCHOR.read_text(encoding="utf-8")))
    payload=json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    if args.check_report and json.loads(REPORT.read_text(encoding="utf-8"))!=result:
        raise ValueError("The historical and prospective 10% uncertainty report changed")
    if args.print_report:
        print("GEO_H2_ORIGIN_MIX_BEGIN",flush=True)
        print(payload,end="")
        print("GEO_H2_ORIGIN_MIX_END",flush=True)
    else:
        print(json.dumps({"retrospective":result["historical_pooled"],
                          "shadow_n":result["new_prospective_shadow"]["country_n"]},
                         sort_keys=True))


if __name__=="__main__":
    main()
