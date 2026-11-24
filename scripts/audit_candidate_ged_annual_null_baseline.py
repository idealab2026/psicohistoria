#!/usr/bin/env python3
"""Audit retrospective Candidate-versus-annual-GED label agreement against a zero rule.

This is an agreement-of-two-UCDP-products diagnostic, NOT a forecast
evaluation, a model selection, or a certified as-of study.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/candidate-ged-2021-22-resolution.json"
REPORT = ROOT / "data/candidate-ged-annual-null-baseline-audit.json"
SOURCE_SHA256 = "3b2576bae226251aa9a0fc4582cd4b5a185185662a1c04646bb7254d04caa1b0"
YEARS = (2021, 2022, 2024, 2025)
THRESHOLDS = ("1", "5", "10", "25")
HORIZONS = ("30", "90")

class AuditError(ValueError):
    pass

def ratio(numerator, denominator):
    return round(numerator / denominator, 8) if denominator else None

def check_cell(cell):
    keys = ("both_positive", "candidate_only", "ged_only", "both_negative",
            "n_at_risk", "candidate_positive", "ged_positive", "disagreements")
    if any(type(cell.get(k)) is not int or cell[k] < 0 for k in keys):
        raise AuditError("Missing, noninteger or negative confusion-matrix entry")
    tp, fp, fn, tn = (cell[k] for k in keys[:4])
    n = cell["n_at_risk"]
    if n <= 0 or tp + fp + fn + tn != n or (
        cell["candidate_positive"] != tp + fp or
        cell["ged_positive"] != tp + fn or
        cell["disagreements"] != fp + fn
    ):
        raise AuditError("Inconsistent Candidate/GED confusion-matrix marginals")
    return tp, fp, fn, tn, n

def metrics(cell):
    tp, fp, fn, tn, n = check_cell(cell)
    annual_negatives = tn + fp
    candidate_agreement = tp + tn
    always_negative_agreement = annual_negatives
    denom = (tp+fp)*(tp+fn)*(tn+fp)*(tn+fn)
    mcc = round((tp*tn-fp*fn)/math.sqrt(denom), 8) if denom else None
    return {
        "n_at_risk": n, "both_positive": tp, "candidate_only": fp,
        "ged_only": fn, "both_negative": tn,
        "annual_positive": tp + fn, "candidate_positive": tp + fp,
        "candidate_annual_agreement": ratio(candidate_agreement, n),
        "always_negative_annual_agreement": ratio(always_negative_agreement, n),
        "candidate_minus_always_negative_agreement_pp": ratio(
            100*(candidate_agreement-always_negative_agreement), n),
        "candidate_positive_matching_annual_share": ratio(tp, tp+fp),
        "candidate_annual_recall": ratio(tp, tp+fn),
        "specificity_annual": ratio(tn, tn+fp),
        "balanced_annual_agreement": (
            round((tp/(tp+fn)+tn/(tn+fp))/2,8)
            if tp+fn and tn+fp else None
        ),
        "matthews_correlation": mcc,
        "zero_rule_has_no_positive_predictions": True,
    }

def build_report(raw=None):
    raw = SOURCE.read_bytes() if raw is None else raw
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise AuditError("Previously frozen source bytes/SHA-256 changed")
    source = json.loads(raw)
    if (source.get("status") != "ARCHIVED_FIRST_ANNUAL_GED_LABEL_RESOLUTION_NOT_ASOF"
        or source.get("years_pooled") != list(YEARS)
        or source.get("candidate_original_release_dates_certified") is not False
        or source.get("new_prospective_issues") != 0
        or source.get("prospective_cohorts_changed") != 0):
        raise AuditError("Frozen source study fails status, as-of or year controls")
    grid = source["pooled_2021_22_24_25_results"]
    if set(grid) != set(THRESHOLDS):
        raise AuditError("Unexpected or incomplete thresholds")
    rows = []
    for threshold in THRESHOLDS:
        if set(grid[threshold]) != set(HORIZONS):
            raise AuditError("Unexpected or incomplete horizons")
        for horizon in HORIZONS:
            cell = grid[threshold][horizon]
            tp,fp,fn,tn,n=check_cell(cell)
            annual = cell.get("annual_breakdown")
            if not isinstance(annual, dict) or set(annual) != set(map(str,YEARS)):
                raise AuditError("Annual strata are incomplete")
            total = {k: 0 for k in (
                "both_positive","candidate_only","ged_only","both_negative",
                "n_at_risk","candidate_positive","ged_positive","disagreements")}
            yearly = []
            for year in YEARS:
                part = annual[str(year)]
                check_cell(part)
                for k in total:
                    total[k] += part[k]
                yearly.append({"year":year, **metrics(part)})
            if any(total[k]!=cell[k] for k in total):
                raise AuditError("Year-level matrices do not reconcile with pooled counts")
            entry = {"threshold_candidate_and_ged":int(threshold),
                     "horizon_days":int(horizon), **metrics(cell),
                     "annual_breakdown":yearly}
            rows.append(entry)
    by_key = {(r["threshold_candidate_and_ged"],r["horizon_days"]):r for r in rows}
    short = by_key[(5,30)]
    long = by_key[(5,90)]
    if (short["n_at_risk"],short["both_positive"],short["candidate_only"],
        short["ged_only"],short["both_negative"])!=(642,5,5,0,632):
        raise AuditError("Previously frozen primary 5/30 cell changed")
    if (long["n_at_risk"],long["both_positive"],long["candidate_only"],
        long["ged_only"],long["both_negative"])!=(642,10,15,2,615):
        raise AuditError("Previously frozen primary 5/90 cell changed")
    return {
        "schema":"idealab.psico.candidate_ged_annual_null_baseline.v1",
        "status":"RETROSPECTIVE_SOURCE_AGREEMENT_NOT_PREDICTIVE_SKILL",
        "analysis_date":"2026-11-24",
        "source_path":"data/candidate-ged-2021-22-resolution.json",
        "source_sha256":SOURCE_SHA256,
        "years":list(YEARS),
        "thresholds":[int(x) for x in THRESHOLDS],
        "horizons_days":[int(x) for x in HORIZONS],
        "results":rows,
        "not_model_accuracy":True,
        "not_asof_certified":True,
        "baseline":"Always assign the negative GED annual label, within each distinct Candidate Q1 risk set",
        "not_cross_threshold_comparable_risk_sets":True,
        "prospective_cohorts_modified":0,
        "new_forecasts_issued":0,
        "interpretation":("Agreement with a later UCDP GED annual product is not forecasting skill; "
          "a large number of annual negatives inflates raw agreement. Candidate "
          "and annual GED have different inclusion/vintage rules. Exact comparisons "
          "to the zero rule share the same at-risk country-years within a cell, "
          "not across thresholds. Post-outcome, non-blind and dependent observations.")
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    choice=parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--print-report", action="store_true")
    choice.add_argument("--check-report", action="store_true")
    args=parser.parse_args(argv)
    try:
        report=build_report()
        if args.print_report:
            print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            frozen=json.loads(REPORT.read_text(encoding="utf8"))
            if frozen!=report:
                raise AuditError("Frozen public annual agreement report failed exact replay")
            print("OK: 8 frozen Candidate/GED cells, four annual cohorts each, zero-rule comparator")
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 2
    return 0

if __name__=="__main__":
    sys.exit(main())
