#!/usr/bin/env python3
"""GEO-2027: temporal origin-state intercept calibration ablation.

Fit ONLY on revised historical target years 2012-19, evaluate on unseen-in-fit
revised 2020-23 and source-separated 2024-25. Model architecture is frozen;
the proposed one-intercept-per-origin-state odds shift is post-hoc exploratory,
NOT independently prospective, and NEVER applied to issued 2027 forecasts.
No individual country data or probabilities are written.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from backtest_archived_country_vintages import SOURCES,fetch_archives
from backtest_statebased_2027_spec import from_zip
from diagnose_geo2027_transition_skill import make_holdout_rows
from diagnose_geo2027_historical_count_dispersion import (
    diagnose as original_count_diagnostic, revised_reference,
)
from forecast_2027_statebased import download_official
from prepare_geo2027_transition_alerts import FORECAST_PATH,SOURCE_SHA256,sha

TRAIN_YEARS=tuple(range(2012,2020))
REVISED_VALIDATION_YEARS=tuple(range(2020,2024))
SEPARATE_VALIDATION_YEARS=(2024,2025)
EXPECTED_CROSS_N=392
EXPECTED_CROSS_STATE_POSITIVES=69
COUNT_ARCHIVE=Path("data/geo2027-historical-count-dispersion-archival.json")
CALIBRATOR="additive_log_odds_intercept_per_origin_state_from_train_only"


def transition_pair(row,field="p_model"):
    s=row.get("origin_state")
    if s not in (0,1) or type(s) is not int:
        raise ValueError("Origin state missing")
    y=row.get("outcome")
    if type(y) is not int or y not in (0,1):
        raise ValueError("Missing future historical label")
    p=row.get(field)
    if type(p) not in (int,float) or not math.isfinite(p) or not 0<p<1:
        raise ValueError("Invalid frozen model probability")
    return (p if s==0 else 1-p),int(y!=s)


def logistic_shift(p,alpha):
    if not 0<p<1 or not math.isfinite(p) or not math.isfinite(alpha):
        raise ValueError("Invalid intercept calibration input")
    logit=math.log(p)-math.log1p(-p)+alpha
    # Stable logistic for extreme logit, no spurious 0/1
    if logit>=0:
        q=1/(1+math.exp(-logit))
    else:
        e=math.exp(logit)
        q=e/(1+e)
    return min(1-1e-12,max(1e-12,q))


def fit_intercept(pairs):
    """Unique intercept matching aggregate observed transitions in training."""
    if len(pairs)<100:
        raise ValueError("Too few exposure observations to calibrate")
    observed=0
    ps=[]
    for p,y in pairs:
        if type(p) not in (int,float) or not math.isfinite(p) or not 0<p<1:
            raise ValueError("Bad training probability")
        if type(y) is not int or y not in (0,1):
            raise ValueError("Missing or nonbinary training label")
        observed+=y
        ps.append(p)
    if observed<=0 or observed>=len(pairs):
        raise ValueError("Cannot estimate finite intercept for single-class data")
    lo,hi=-20.,20.
    if sum(logistic_shift(p,lo) for p in ps)>=observed or sum(
        logistic_shift(p,hi) for p in ps
    )<=observed:
        raise ValueError("Intercept root not bracketed")
    for _ in range(75):
        middle=(lo+hi)/2
        expected=sum(logistic_shift(p,middle) for p in ps)
        if expected<observed:
            lo=middle
        else:
            hi=middle
    alpha=(lo+hi)/2
    if abs(sum(logistic_shift(p,alpha) for p in ps)-observed)>1e-7:
        raise ValueError("Training intercept failed its root constraint")
    return alpha


def score(rows,alpha):
    if len(rows)==0:
        raise ValueError("Empty scoring panel")
    s=rows[0]["origin_state"]
    if any(row["origin_state"]!=s for row in rows):
        raise ValueError("Mixed ex-ante risk sets")
    pmod=[transition_pair(row,"p_model") for row in rows]
    pglo=[transition_pair(row,"p_global_markov") for row in rows]
    if any(a[1]!=b[1] for a,b in zip(pmod,pglo)):
        raise ValueError("Comparator and candidate labels disagree")
    calibrated=[(logistic_shift(p,alpha),y) for p,y in pmod]
    def metrics(pairs):
        n=len(pairs)
        return {
            "expected_events":sum(p for p,_ in pairs),
            "mean_probability":sum(p for p,_ in pairs)/n,
            "brier":sum((p-y)**2 for p,y in pairs)/n,
            "log_loss":-sum(y*math.log(p)+(1-y)*math.log1p(-p)
                            for p,y in pairs)/n,
        }
    a,b,c=metrics(pmod),metrics(calibrated),metrics(pglo)
    return {
        "country_years":len(rows),
        "observed_transitions":sum(y for p,y in pmod),
        "original_country_markov":a,
        "odds_intercept_calibrated":b,
        "original_global_markov":c,
        "delta_brier_calibrated_minus_original":b["brier"]-a["brier"],
        "delta_logloss_calibrated_minus_original":b["log_loss"]-a["log_loss"],
        "delta_brier_calibrated_minus_global":b["brier"]-c["brier"],
    }


def evaluate(revised,external,source_hashes,previous_report):
    if (len(external)!=EXPECTED_CROSS_N or
        sum(r["outcome"] for r in external)!=EXPECTED_CROSS_STATE_POSITIVES):
        raise ValueError("Official source-separated 392/69 comparator changed")
    if set(source_hashes)!=set(SOURCES) or any(
        source_hashes[k]!=SOURCES[k]["sha256"] for k in SOURCES
    ):
        raise ValueError("Official historical source SHA mismatch")
    if (sorted({r["target_year"] for r in revised})!=list(
        TRAIN_YEARS+REVISED_VALIDATION_YEARS
    ) or sorted({r["target_year"] for r in external})!=list(
        SEPARATE_VALIDATION_YEARS
    )):
        raise ValueError("Unexpected training/development/external target years")
    if original_count_diagnostic(revised,external,source_hashes)!=previous_report:
        raise ValueError("Original committed count-dispersion report did not reproduce")
    state_reports={}
    for s in (0,1):
        train=[r for r in revised if r["origin_state"]==s and
               r["target_year"] in TRAIN_YEARS]
        dev=[r for r in revised if r["origin_state"]==s and
             r["target_year"] in REVISED_VALIDATION_YEARS]
        holdout=[r for r in external if r["origin_state"]==s and
                 r["target_year"] in SEPARATE_VALIDATION_YEARS]
        if (len(train)<100 or len(dev)<50 or len(holdout)<30
            or len({r["target_year"] for r in train})!=len(TRAIN_YEARS)
            or len({r["target_year"] for r in dev})!=len(REVISED_VALIDATION_YEARS)
            or len({r["target_year"] for r in holdout})!=len(
                SEPARATE_VALIDATION_YEARS)
        ):
            raise ValueError("Missing year/state country exposure")
        alpha=fit_intercept([transition_pair(r) for r in train])
        train_result=score(train,alpha)
        dev_result=score(dev,alpha)
        holdout_result=score(holdout,alpha)
        state_reports[str(s)]={
            "origin_state":s,
            "alpha_log_odds_shift_estimated_from_2012_2019_only":alpha,
            "odds_multiplier":math.exp(alpha),
            "train_revised_2012_2019":train_result,
            "validation_revised_2020_2023":dev_result,
            "evaluation_separate_source_2024_2025":holdout_result,
            "cross_vintage_by_year":{
                str(y):score([r for r in holdout if r["target_year"]==y],alpha)
                for y in SEPARATE_VALIDATION_YEARS
            },
        }
    return {
        "schema":"idealab.psico.geo2027_posthoc_intercept_calibration_split.v1",
        "status":"EXPLORATORY_POSTHOC_TEMPORAL_SPLIT_NOT_ASOF",
        "original_probabilities_retrained_or_modified":False,
        "prospective_2027_forecast_modified":False,
        "prospective_2027_results_observed":0,
        "model":CALIBRATOR,
        "hyperparameters":"Two scalar intercepts (entry vs resolution), fit by training-only Bernoulli likelihood, no tuning on validation labels",
        "train_years_revised_26_1":list(TRAIN_YEARS),
        "validation_years_revised_26_1":list(REVISED_VALIDATION_YEARS),
        "external_label_years_source_separated":list(SEPARATE_VALIDATION_YEARS),
        "historical_source_sha256":{k:source_hashes[k] for k in sorted(source_hashes)},
        "revised_source_sha256":SOURCES["26.1"]["sha256"],
        "historical_question_selected_after_historical_outcomes_seen":True,
        "historical_26_1_revisions_not_contemporaneous":True,
        "external_holdout_confirmatory":False,
        "per_known_origin_state":state_reports,
        "limitations":("Calibration was designed AFTER inspecting aggregate historical "
            "overprediction from both study periods, so even held-out external "
            "years DO NOT constitute untouched confirmatory evidence. "
            "Training/validation labels are from a single 2026 revised source, "
            "not signed contemporaneous origin releases. Tiny counts, shared "
            "country-years and geopolitical shocks. An intercept improves "
            "marginal mean fit if stable but cannot establish dependence "
            "structure or prospective predictive skill. 2027 remains frozen."),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report")
    args=parser.parse_args()
    original=FORECAST_PATH.read_bytes()
    if sha(original)!=SOURCE_SHA256:
        raise ValueError("Issued GEO-2027 bytes changed")
    from build_official_countries import PINNED_SOURCE_SHA256
    raw=download_official()
    if sha(raw)!=PINNED_SOURCE_SHA256:
        raise ValueError("Official 26.1 source has changed")
    records,_=from_zip(raw)
    editions,meta=fetch_archives()
    expected=json.loads(COUNT_ARCHIVE.read_text(encoding="utf8"))
    report=evaluate(revised_reference(records),make_holdout_rows(editions),
                    {k:v["sha256"] for k,v in meta.items()},expected)
    content=json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    print("GEO2027_TEMPORAL_CALIBRATION_BEGIN")
    print(content,end="")
    print("GEO2027_TEMPORAL_CALIBRATION_END")
    if args.check_report and Path(args.check_report).read_bytes()!=content.encode("utf8"):
        raise ValueError("Frozen temporal calibration report mismatch")


if __name__=="__main__":
    main()
