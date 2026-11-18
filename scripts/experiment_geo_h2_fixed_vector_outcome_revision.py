#!/usr/bin/env python3
"""Measure Brier score changes caused ONLY by revised UCDP labels.

For historical 2014-2024 targets, hold the origin-edition model vector fixed
and resolve identical 196 GWNO against 25.1 and 26.1 target labels.
This is retrospective source sensitivity; source releases arrived too late to
qualify as genuinely historical issued predictions.
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
from audit_geo2027_ucdp_fatality_vintages import classify, read_verified_intervals
from backtest_archived_country_vintages import SOURCES
from experiment_geo_h2_rolling_2014_2025 import _build_fold, fold_specs
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD, VERSION_ORDER, parse_counts,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
REFERENCE=ROOT/"data/geo-h2-rolling-historical-2014-2025.json"
OUTPUT=ROOT/"data/geo-h2-fixed-vector-2526-outcome-revision.json"
YEARS=tuple(range(2014,2025))
FIELDS=("p_original_binary","p_intensity_markov","p_global_markov","p_baseline_global_5y")


def fixed_score_change(old: dict, new: dict, expected_ids: set) -> dict:
    """Each side must contain same country/target and IDENTICAL probability vector."""
    if len(old)!=196 or len(new)!=196 or set(old)!=set(new) or set(old)!=expected_ids:
        raise ValueError("Missing, duplicated or non-original fixed GWNO cohort")
    sums={field:0.0 for field in FIELDS}
    revised=[]
    for cid in sorted(expected_ids):
        a,b=old[cid],new[cid]
        if (a["country_id"]!=cid or b["country_id"]!=cid or
            a["target_year"]!=b["target_year"] or
            a["origin_active"]!=b["origin_active"]):
            raise ValueError("Country origin-year mapping changed")
        old_y=classify(a["official_fatalities_estimates"])[1]
        new_y=classify(b["official_fatalities_estimates"])[1]
        if old_y not in (0,1) or new_y not in (0,1):
            raise ValueError("Invalid official target classification")
        for field in FIELDS:
            p,q=a[field],b[field]
            if not (type(p) in (int,float) and math.isfinite(p)
                    and 0<=p<=1 and p==q):
                raise ValueError("Model probability vector differs across outcomes")
            exact=(p-new_y)**2-(p-old_y)**2
            algebraic=(new_y-old_y)*(1-2*p)
            if not math.isclose(exact,algebraic,abs_tol=1e-12,rel_tol=0):
                raise AssertionError("Incorrect Brier revision identity")
            sums[field]+=exact
        if old_y!=new_y:
            revised.append({
                "country_id":cid,"year":a["target_year"],
                "old_label":old_y,"new_label":new_y,
                "old_best_deaths":a["official_fatalities_estimates"][1],
                "new_best_deaths":b["official_fatalities_estimates"][1],
                "fixed_probabilities":{field:a[field] for field in FIELDS},
                "individual_brier_shifts":{field:(
                    a[field]-new_y)**2-(a[field]-old_y)**2 for field in FIELDS},
            })
    changes={field:sums[field]/len(old) for field in FIELDS}
    return {
        "country_n":len(old),
        "label_revisions_n":len(revised),
        "revised_countries":revised,
        "observed_brier_shift_new_minus_old":changes,
        "observed_fourstate_minus_binary_delta_brier_shift":
            changes["p_intensity_markov"]-changes["p_original_binary"],
        "strict_single_model_ceiling":len(revised)/len(old),
        "strict_two_model_comparison_ceiling":2*len(revised)/len(old),
    }


def analyze(counts,panels,issue,reference):
    if (issue.get("official_2027_outcomes_resolved")!=0 or
        reference.get("schema")!="idealab.psico.geo_h2_rolling_historical_2014_2025.v1" or
        reference.get("fixed_original_GWNO_n")!=196 or
        reference.get("not_prospective_or_independently_timestamped_skill") is not True or
        reference.get("source_archives_sha256")!=
          {v:SOURCES[v]["sha256"] for v in VERSION_ORDER}):
        raise ValueError("Original prediction registry or official-source audit differs")
    ids=sorted(x["country_id"] for x in issue["countries"])
    if len(ids)!=196 or len(set(ids))!=196:
        raise ValueError("Frozen GWNO original cohort invalid")
    annual_expect={
        f["year"]:f["outcome_best_label_changed_n"] for f in
        reference["primary_vs_later_vintage_historical_revisions"][
            "annual_changed_label_and_forecast_counts"]
    }
    if set(YEARS)-set(annual_expect):
        raise ValueError("Historical source-year label controls missing")
    report_rows=[]
    total_sums={field:0.0 for field in FIELDS}
    fixed_cohort=set(ids)
    for spec in fold_specs("fixed_first_vintage_then_latest"):
        year=spec["target_year"]
        if year not in YEARS:
            continue
        # Same origin release & model history in BOTH comparisons. Only labels vary.
        old_spec={**spec,"outcome_release":"25.1"}
        new_spec={**spec,"outcome_release":"26.1"}
        old,old_meta=_build_fold(old_spec,counts,panels,ids)
        new,new_meta=_build_fold(new_spec,counts,panels,ids)
        if (old_meta["origin_release"]!=new_meta["origin_release"] or
            old_meta["last_training_year"]!=new_meta["last_training_year"] or
            old_meta["four_state_last_training_year"]!=new_meta["four_state_last_training_year"]):
            raise ValueError("Historical origin model was not held fixed")
        result=fixed_score_change(
            {row["country_id"]:row for row in old},
            {row["country_id"]:row for row in new},
            fixed_cohort,
        )
        if result["label_revisions_n"]!=annual_expect[year]:
            raise ValueError("Label revisions disagree with prior source-vintage audit")
        for field in FIELDS:
            total_sums[field]+=result["observed_brier_shift_new_minus_old"][field]*196
        report_rows.append({
            "target_year":year,"origin_year":spec["origin_year"],
            "frozen_origin_release":spec["origin_release"],
            "old_target_release":"25.1","new_target_release":"26.1",**result,
        })
    total_n=196*len(YEARS)
    revised=sum(r["label_revisions_n"] for r in report_rows)
    changes={field:total_sums[field]/total_n for field in FIELDS}
    return {
        "schema":"idealab.psico.geo_h2_fixed_origin_outcome_revision_brier.v1",
        "status":"OBSERVED_EX_POST_BRIER_LABEL_REVISION_FIXED_MODEL_NOT_PROSPECTIVE",
        "source_archives_sha256":reference["source_archives_sha256"],
        "original_GEO2027_SHA256":SOURCE_SHA256,
        "original_2027_2028_predictions_modified":False,
        "comparison":"UCDP OrganizedViolenceCY 25.1 to 26.1 target year best >=25",
        "same_source_origin_fixed_in_each_pair":True,
        "historical_model_issued_at_real_origin":False,
        "country_n":196,"years":list(YEARS),
        "unique_country_year_n":total_n,
        "revised_binary_labels_n":revised,
        "observed_brier_shift_new_minus_old":changes,
        "observed_fourstate_minus_binary_delta_brier_shift":
            changes["p_intensity_markov"]-changes["p_original_binary"],
        "single_fixed_model_ceiling":revised/total_n,
        "two_fixed_model_comparison_ceiling":2*revised/total_n,
        "yearly":report_rows,
        "caveat":"Backfilled origin source revisions; same fixed vintage prediction is compared against two later historical outcome vintages. No prospective skill claim, IID claim or new prediction.",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--print-report",action="store_true")
    ap.add_argument("--check-report",action="store_true")
    args=ap.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Frozen 2027 GEO probability vector mutated")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    sources={v:request(SOURCES[v]["url"],MAX_DOWNLOAD) for v in VERSION_ORDER}
    counts={v:parse_counts(sources[v],v) for v in VERSION_ORDER}
    panels={v:read_verified_intervals(sources[v],v) for v in VERSION_ORDER}
    report=analyze(
        counts,panels,json.loads(ISSUE.read_text()),
        json.loads(REFERENCE.read_text()),
    )
    payload=json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    if args.check_report and OUTPUT.read_bytes()!=payload.encode():
        raise ValueError("Official source-replayed fixed Brier report changed")
    if args.print_report:
        print("GEO_FIXED_BRIER_BEGIN",flush=True)
        print(payload,end="")
        print("GEO_FIXED_BRIER_END",flush=True)
    else:
        print(json.dumps({"observed":report["observed_brier_shift_new_minus_old"],
                          "revised":report["revised_binary_labels_n"],
                          "n":report["unique_country_year_n"]},sort_keys=True))


if __name__=="__main__":
    main()
