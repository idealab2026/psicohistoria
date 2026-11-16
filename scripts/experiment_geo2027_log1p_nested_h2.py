#!/usr/bin/env python3
"""Nested chronological, retrospective GEO H2 log1p-fatality residual model.

The ORIGINAL two-state Markov H2 issue is unmodified. A low-dimensional
logistic offset augments its probabilities using two continuous origin-year
intensity features. Penalties are selected ONLY using target years 2018-2020
in the ORIGIN edition, trained on 2012-2017 targets, then refitted using
target years 2012..origin. Evaluates the already-examined 2024/2025 targets:
therefore EXPLORATORY, NOT INDEPENDENT HOLDOUT OR PROSPECTIVE SKILL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

from backtest_archived_country_vintages import FOLDS, SOURCES
from diagnose_geo2028_historical_forecast_vintage_drift import _fit_at_origin
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD, VERSION_ORDER, counts_to_binary, intensity_state,
    parse_counts, scores,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo2027-log1p-nested-h2.json"
BINARY_REFERENCE=ROOT/"data/forecast-2027-archival-cross-release.json"
FOUR_STATE_REFERENCE=ROOT/"data/geo2027-intensity-markov-cross-release.json"
LAMBDAS=(5.0,20.0,80.0)
TRAIN_TARGET_YEARS=tuple(range(2012,2018))
TUNE_TARGET_YEARS=(2018,2019,2020)
FIRST_INNER_TARGET=2012
MODEL_DIM=3
SOURCE_BOUND=2023
INTENSITY_NORMALIZER_INACTIVE=math.log(26)
INTENSITY_NORMALIZER_ACTIVE=math.log(101)
MIN_OBSERVATIONS=500


def logistic(z):
    if z>=0:
        return 1/(1+math.exp(-z))
    e=math.exp(z)
    return e/(1+e)


def logit(p):
    if not 0<p<1 or not math.isfinite(p):
        raise ValueError("Invalid original Markov probability for offset")
    return math.log(p)-math.log1p(-p)


def features(deaths):
    if type(deaths) is not int or deaths<0:
        raise ValueError("Invalid historical state-based death count")
    if deaths<25:
        return (1.0,math.log1p(deaths)/INTENSITY_NORMALIZER_INACTIVE,0.0)
    return (1.0,0.0,
            (math.log1p(deaths)-math.log(26))/INTENSITY_NORMALIZER_ACTIVE)


def solve(matrix, rhs):
    """Deterministic pivoted Gauss elimination; ≤3 ridge variables."""
    n=len(rhs)
    if n not in (1,3) or len(matrix)!=n or any(len(r)!=n for r in matrix):
        raise ValueError("Unexpected ridge Hessian shape")
    a=[list(matrix[i])+[rhs[i]] for i in range(n)]
    for col in range(n):
        pivot=max(range(col,n),key=lambda i:abs(a[i][col]))
        if abs(a[pivot][col])<1e-12:
            raise ValueError("Ridge Hessian singular")
        a[col],a[pivot]=a[pivot],a[col]
        scale=a[col][col]
        for j in range(col,n+1):
            a[col][j]/=scale
        for i in range(n):
            if i==col:
                continue
            factor=a[i][col]
            for j in range(col,n+1):
                a[i][j]-=factor*a[col][j]
    result=[r[-1] for r in a]
    if not all(math.isfinite(x) for x in result):
        raise ValueError("Nonfinite logistic update")
    return result


def predict(row,beta):
    if len(beta)!=MODEL_DIM:
        raise ValueError("Bad coefficient shape")
    return logistic(logit(row["p_original_binary"])+
                    sum(a*b for a,b in zip(features(row["origin_deaths"]),beta)))


def fit(rows,lam,*,intercept_only=False):
    """Penalised logistic with original model log-odds as fixed offset."""
    if (type(lam) is not float or lam not in LAMBDAS
        or len(rows)<MIN_OBSERVATIONS):
        raise ValueError("Invalid lambda or short historical learning sample")
    n=1 if intercept_only else MODEL_DIM
    beta=[0.0]*n
    for _ in range(40):
        grad=[lam*b for b in beta]
        hess=[[lam if i==j else 0.0 for j in range(n)]
              for i in range(n)]
        for row in rows:
            original=logit(row["p_original_binary"])
            xx=features(row["origin_deaths"])[:n]
            p=logistic(original+sum(a*b for a,b in zip(xx,beta)))
            w=p*(1-p)
            for i in range(n):
                grad[i]+=(p-row["outcome"])*xx[i]
                for j in range(n):
                    hess[i][j]+=w*xx[i]*xx[j]
        direction=solve(hess,grad)
        if max(abs(d) for d in direction)<1e-10:
            break
        beta=[b-d for b,d in zip(beta,direction)]
        if any(not math.isfinite(b) or abs(b)>20 for b in beta):
            raise ValueError("Logistic optimisation divergent")
    else:
        raise ValueError("Ridge logistic fit did not converge")
    if intercept_only:
        return (beta[0],0.0,0.0)
    return tuple(beta)


def binary_h2_until(binary,cutoff):
    """Original GEO equations for historical nested training at any cutoff."""
    if not isinstance(binary,dict) or not 2010<=cutoff<=2023:
        raise ValueError("Invalid historical nested cutoff")
    local={}
    global_counts=[[0,0],[0,0]]
    for cid,h in binary.items():
        if type(cid) is not int or not isinstance(h,dict):
            raise ValueError("Invalid country risk history")
        own=[[0,0],[0,0]]
        for year in sorted(h):
            if year>cutoff or year-1 not in h:
                continue
            a,b=h[year-1],h[year]
            if a not in (0,1) or b not in (0,1):
                raise ValueError("Invalid state-based threshold")
            own[a][b]+=1
            global_counts[a][b]+=1
        local[cid]=own
    if min(sum(row) for row in global_counts)<100:
        raise ValueError("Insufficient global source transitions")
    g=[(global_counts[s][1]+1)/(sum(global_counts[s])+2)
       for s in (0,1)]
    result={}
    for cid,h in binary.items():
        if cutoff not in h or cutoff-1 not in h:
            continue
        own=local[cid]
        q=[(own[s][1]+20*g[s])/(sum(own[s])+20) for s in (0,1)]
        a=q[h[cutoff]]
        result[cid]=round((1-a)*q[0]+a*q[1],12)
    return result


def inner_rows(source,origin):
    """Outcomes used for learning are within one original edition <=origin."""
    if origin not in (2022,2023):
        raise ValueError("Expected original release cutoff")
    binary=counts_to_binary(source)
    rows=[]
    summary=[]
    for target in range(FIRST_INNER_TARGET,origin+1):
        cutoff=target-2
        preds=binary_h2_until(binary,cutoff)
        byyear=[]
        for cid,p in preds.items():
            source_history=source[cid]
            if target not in source_history:
                continue   # not missing==0
            origin_deaths=source_history[cutoff]
            byyear.append({
                "country_id":cid,"target_year":target,
                "origin_year":cutoff,"origin_deaths":origin_deaths,
                "origin_binary":int(origin_deaths>=25),
                "p_original_binary":p,
                "outcome":int(source_history[target]>=25),
            })
        if len(byyear)<175:
            raise ValueError("Nested historical year has too few outcomes")
        summary.append({"target_year":target,"n":len(byyear),
                        "positives":sum(r["outcome"] for r in byyear),
                        "max_training_cutoff":cutoff})
        rows+=byyear
    return rows,summary


def select_and_fit(rows,origin):
    fitrows=[r for r in rows if r["target_year"] in TRAIN_TARGET_YEARS]
    valrows=[r for r in rows if r["target_year"] in TUNE_TARGET_YEARS]
    finalrows=[r for r in rows if r["target_year"]<=origin]
    if (min(r["target_year"] for r in fitrows)!=2012 or
        max(r["target_year"] for r in fitrows)!=2017 or
        min(r["target_year"] for r in valrows)!=2018 or
        max(r["target_year"] for r in valrows)!=2020 or
        len(fitrows)<MIN_OBSERVATIONS or len(valrows)<MIN_OBSERVATIONS or
        max(r["target_year"] for r in finalrows)!=origin):
        raise ValueError("Nested rolling split violated")
    selection=[]
    for lam in LAMBDAS:
        beta=fit(fitrows,lam)
        pred=[{**r,"p_offset_log1p":predict(r,beta)} for r in valrows]
        s=scores(pred,"p_offset_log1p")
        selection.append({"lambda":lam,"validation_brier":s["brier"],
                          "validation_logloss":s["logloss"],
                          "development_beta":[round(x,12) for x in beta]})
    chosen=min(selection,key=lambda r:(r["validation_brier"],r["lambda"]))["lambda"]
    beta=fit(finalrows,chosen)
    intercept=fit(finalrows,chosen,intercept_only=True)
    return beta,intercept,{
        "inner_fit_targets":[min(TRAIN_TARGET_YEARS),max(TRAIN_TARGET_YEARS)],
        "inner_select_targets":[min(TUNE_TARGET_YEARS),max(TUNE_TARGET_YEARS)],
        "final_train_targets":[2012,origin],
        "inner_fit_n":len(fitrows),"inner_validation_n":len(valrows),
        "final_train_n":len(finalrows),
        "final_train_positives":sum(r["outcome"] for r in finalrows),
        "selected_ridge_lambda":chosen,
        "candidate_lambda_validation_scores":selection,
        "final_beta_log1p":[round(x,12) for x in beta],
        "final_beta_intercept_only":[round(x,12) for x in intercept],
        "no_post_origin_supervised_label_used":True
    }


def compare(rows):
    if not rows:
        raise ValueError("Empty evaluation stratum")
    score_fields=("p_original_binary","p_calibrated_intercept","p_offset_log1p")
    ss={k:scores(rows,k) for k in score_fields}
    base=ss["p_original_binary"]["brier"]
    return {
        "n":len(rows),"positives":sum(r["outcome"] for r in rows),
        "scores":ss,
        "log1p_minus_binary_delta_brier":ss["p_offset_log1p"]["brier"]-base,
        "log1p_minus_intercept_delta_brier":
            ss["p_offset_log1p"]["brier"]-ss["p_calibrated_intercept"]["brier"],
        "log1p_minus_binary_delta_logloss":
            ss["p_offset_log1p"]["logloss"]-ss["p_original_binary"]["logloss"],
        "log1p_minus_intercept_delta_logloss":
            ss["p_offset_log1p"]["logloss"]-ss["p_calibrated_intercept"]["logloss"],
    }


def replay(sources,prior_binary,prior_four_state):
    if (prior_binary.get("schema")!="idealab.psico.statebased_archival_cross_release_v1"
        or prior_binary.get("historical_forecasts_actually_issued") is not False
        or prior_four_state.get("schema")!="idealab.psico.geo2027_four_state_intensity_cross_release.v1"
        or prior_four_state.get("outcomes_2027_resolved")!=0):
        raise ValueError("Historical comparator provenance not verified")
    foldreports=[]
    allrows=[]
    for spec in FOLDS:
        old_v,new_v=spec["origin_release"],spec["target_release"]
        origin,target=spec["origin_year"],spec["target_year"]
        if SOURCES[old_v]["last_year"]!=origin or SOURCES[new_v]["last_year"]!=target:
            raise ValueError("Origin/target source year mismatch")
        origin_source=sources[old_v]
        outcome_source=sources[new_v]
        nested,summary=inner_rows(origin_source,origin)
        beta,intercept,selection=select_and_fit(nested,origin)
        binary=counts_to_binary(origin_source)
        original,origmeta=_fit_at_origin(binary,origin)
        own_pred=binary_h2_until(binary,origin)
        if set(original)!=set(own_pred) or len(original)!=196:
            raise ValueError("Original 196-country GEO cohort changed")
        if any(abs(own_pred[cid]-original[cid]["p_model_h2"])>1e-11
               for cid in original):
            raise AssertionError("Nested baseline not faithful to original GEO")
        rows=[]
        for cid in sorted(original):
            deaths=origin_source[cid][origin]
            if target not in outcome_source.get(cid,{}):
                raise ValueError("No official later-edition target row: no imputation")
            original_p=original[cid]["p_model_h2"]
            rr={"country_id":cid,"target_year":target,"origin_deaths":deaths,
                "origin_binary":int(deaths>=25),"intensity_stratum":intensity_state(deaths),
                "outcome":int(outcome_source[cid][target]>=25),
                "p_original_binary":original_p}
            rr["p_offset_log1p"]=round(predict(rr,beta),12)
            rr["p_calibrated_intercept"]=round(predict(rr,intercept),12)
            rows.append(rr)
        previous=next(x for x in prior_binary["folds"]
                      if x["origin_cutoff"]==origin and
                      x["origin_version"]==old_v and
                      x["outcome_version"]==new_v)
        now=compare(rows)
        for k in ("brier","logloss"):
            if abs(now["scores"]["p_original_binary"][k]-
                   previous["scores"]["p_model"][k])>2e-10:
                raise AssertionError("Original historical Brier/log-loss not reproduced")
        if sum(r["outcome"] for r in rows)!=previous["positives"]:
            raise AssertionError("Original source-separated outcome positives changed")
        foldreports.append({
            "origin_vintage":old_v,"outcome_vintage":new_v,
            "origin_cutoff":origin,"outcome_year":target,
            "inner_years":summary,
            "nested_training_and_selection":selection,
            "metrics":now,
            "by_binary_origin_state":{
                str(st):compare([r for r in rows if r["origin_binary"]==st])
                for st in (0,1)},
            "by_origin_intensity":{
                str(st):compare([r for r in rows if r["intensity_stratum"]==st])
                for st in range(4)
                if any(r["intensity_stratum"]==st for r in rows)
            }
        })
        allrows+=rows
    result=compare(allrows)
    if len(allrows)!=392 or result["positives"]!=69:
        raise ValueError("Historical source-separated evaluation cohort changed")
    if abs(result["scores"]["p_original_binary"]["brier"]-
           prior_binary["metrics"]["p_model"]["brier"])>1e-10:
        raise AssertionError("Pooled original binary anchor mismatch")
    if abs(result["scores"]["p_original_binary"]["brier"]-
           prior_four_state["pooled"]["original_binary"]["brier"])>1e-10:
        raise AssertionError("Four-state study uses different original reference")
    per_country=[]
    for cid in sorted(set(r["country_id"] for r in allrows)):
        rs=[r for r in allrows if r["country_id"]==cid]
        if len(rs)!=2:
            raise ValueError("Incomplete 2-year country pair")
        mean_delta=sum((r["p_offset_log1p"]-r["outcome"])**2-
                       (r["p_original_binary"]-r["outcome"])**2
                       for r in rs)/2
        per_country.append({"country_id":cid,"delta_brier_mean":round(mean_delta,12),
                            "origin_2022_deaths":rs[0]["origin_deaths"],
                            "origin_2023_deaths":rs[1]["origin_deaths"],
                            "outcomes":[r["outcome"] for r in rs]})
    ranked=sorted(per_country,key=lambda r:(r["delta_brier_mean"],r["country_id"]))
    return {
        "schema":"idealab.psico.geo2027_log1p_nested_h2_research.v1",
        "status":"EX_POST_AFTER_SEEING_2024_2025_RESULTS_NOT_FRESH_HOLDOUT",
        "original_forecast_sha256":SOURCE_SHA256,
        "original_2027_2028_issue_changed":False,
        "target_definition":"UCDP state-based annual deaths best >=25 at horizon H2",
        "source_sha256":{v:SOURCES[v]["sha256"] for v in VERSION_ORDER},
        "continuous_features":["log1p(origin_deaths) inactive / log(26)",
            "(log1p(origin_deaths)-log(26)) active / log(101)"],
        "original_binary_p_as_fixed_logit_offset":True,
        "baseline_intercept_only_calibration_control":True,
        "ridge_candidates":list(LAMBDAS),
        "inner_training_target_years":[2012,2017],
        "inner_validation_target_years":[2018,2020],
        "inner_lambda_selected_only_on_pre_2021_labels":True,
        "evaluation_target_years":[2024,2025],
        "evaluation_target_years_previously_inspected_in_prior_research":True,
        "inner_temporal_validation_not_independent_source_vintage":True,
        "outcome_release_only_used_after_fitting":True,
        "report_original_markov_binary_comparator":
            prior_binary["metrics"]["p_model"],
        "report_previously_explored_four_state_brier":
            prior_four_state["pooled"]["intensity_four_state"]["brier"],
        "folds":foldreports,"pooled":result,
        "n_country_pairs_lower_brier_log1p_than_original":
            sum(r["delta_brier_mean"]<0 for r in per_country),
        "n_country_pairs_higher_brier_log1p_than_original":
            sum(r["delta_brier_mean"]>0 for r in per_country),
        "largest_country_brier_improvements":ranked[:10],
        "largest_country_brier_deteriorations":list(reversed(ranked[-10:])),
        "no_external_2026_2027_outcome_available":True,
        "historical_predictions_actually_issued":False,
        "prospective_predictive_skill_demonstrated":False,
        "n_2027_outcomes_resolved":0,
        "limitations":"Strict inner chronological fitting and tuning within each ORIGINAL archived edition; 2018-2020 tuning labels and 2012..origin final fit never use later origin-release target years. BUT all 2024/25 holdouts were already examined by prior project iterations; choosing to explore log1p now makes them reused exploratory data, not untouched confirmatory validation. Archives release timestamps not independently notarized. Two outcome years with repeated countries and common shocks. No independent 2026+ official outcome; no causal estimates or IID uncertainty intervals."
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    args=ap.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Original issued GEO2027 SHA mismatch")
    source={}
    for ver in VERSION_ORDER:
        raw=request(SOURCES[ver]["url"],MAX_DOWNLOAD)
        source[ver]=parse_counts(raw,ver)
    prior=json.loads(BINARY_REFERENCE.read_text(encoding="utf8"))
    four=json.loads(FOUR_STATE_REFERENCE.read_text(encoding="utf8"))
    result=replay(source,prior,four)
    payload=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    print("GEO2027_LOG1P_NESTED_RESULT_BEGIN")
    print(payload,end="")
    print("GEO2027_LOG1P_NESTED_RESULT_END")
    if args.check_report and REPORT.read_bytes()!=payload.encode():
        raise ValueError("Official-source-replayed nested log1p report differs from committed report")


if __name__=="__main__":
    main()
