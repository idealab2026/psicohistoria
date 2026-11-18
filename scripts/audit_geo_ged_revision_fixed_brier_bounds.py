#!/usr/bin/env python3
"""Finite-cohort Brier sensitivity ceilings for GED-vintage label revisions.

Algebra only: holds prediction vectors fixed, makes no assertion that historic
predictions existed. For y' != y, [(p-y')²-(p-y)²] = (y'-y)(1-2p).
With p in [0,1], absolute change <= 1 per revised label.
For two fixed models, paired Brier difference can move by <= 2 per revised
label. These ceilings are worst-case mathematical guarantees, NOT measured
model score changes, confidence intervals, or claims of prospective skill.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ANNUAL=ROOT/"data/geo-ged-20-21-coverage-revisions.json"
TRANSITIONS=ROOT/"data/geo-ged-transition-revision-impact.json"
OUTPUT=ROOT/"data/geo-ged-revision-fixed-brier-bounds.json"


def derive(annual: dict, transitions: dict) -> dict:
    if (annual.get("historical_model_fitting_authorized") is not False
        or annual.get("GEO2027_GEO2028_forecasts_modified") is not False
        or transitions.get("prospective_skill_claimed") is not False
        or transitions.get("new_predictions_issued") != 0
        or annual.get("source_zip_sha256") != transitions.get("source_hashes")):
        raise ValueError("Historical source provenance or frozen forecast guard failed")
    amap={(a["old_version"],a["new_version"]): a for a in annual["pairs"]}
    tmap={(t["old_version"],t["new_version"]): t for t in transitions["pairs"]}
    if len(amap)!=len(annual["pairs"]) or len(tmap)!=len(transitions["pairs"]) or set(amap)!=set(tmap):
        raise ValueError("Pair mapping differs or has duplicates")
    outputs=[]
    for key in sorted(amap):
        a=amap[key]["comparison"]
        t=tmap[key]
        if (len(t["years_compared"])<2 or a["target_years"]!=t["years_compared"]
            or a["eligible_countries_per_year"]!=t["cohort_country_n"]):
            raise ValueError("Country-year cohort mismatch")
        label_flips=a["best_ge25_binary_label_change_n"]
        label_n=a["observed_country_years"]
        transition_flips=t["revised_two_year_transition_labels"]
        transition_n=t["eligible_country_transitions"]
        if (not isinstance(label_flips,int) or not isinstance(transition_flips,int)
            or not (0<=label_flips<=label_n) or not (0<=transition_flips<=transition_n)
            or label_n!=len(t["years_compared"])*t["cohort_country_n"]
            or transition_n!=(len(t["years_compared"])-1)*t["cohort_country_n"]
            or len(t["revised_transition_country_start_year"])!=transition_flips):
            raise ValueError("Invalid or incomplete denominator")
        outputs.append({
            "old_version":key[0],
            "new_version":key[1],
            "is_consecutive_release":amap[key]["is_consecutive_release"],
            "annual": {
                "country_years":label_n,
                "revised_binary_labels":label_flips,
                "max_absolute_single_fixed_model_brier_shift":label_flips/label_n,
                "max_absolute_two_fixed_model_delta_brier_shift":min(1.0,2*label_flips/label_n),
            },
            "transition_fourstate": {
                "country_year_transitions":transition_n,
                "revised_fourstate_labels":transition_flips,
                "max_absolute_single_fixed_binary_event_brier_shift":transition_flips/transition_n,
                "max_absolute_two_fixed_binary_event_delta_brier_shift":min(1.0,2*transition_flips/transition_n),
                "event_specific_caution":"Individual transition event indicators may change on a subset of the changed four-state labels",
            },
        })
    return {
        "schema":"idealab.psico.ged_fixed_forecasts_brier_revision_ceiling.v1",
        "status":"EX_POST_SOURCE_REVISION_ALGEBRA_NOT_MEASURED_BRIER",
        "source_annual":"data/geo-ged-20-21-coverage-revisions.json",
        "source_transition":"data/geo-ged-transition-revision-impact.json",
        "official_ged_sha256":annual["source_zip_sha256"],
        "bounds":"finite sample, fixed probabilities in [0,1], no independence assumption",
        "same_model_probability_vector_assumed_across_vintages":True,
        "actual_historical_predictions_available_or_certified":False,
        "prospective_skill_demonstrated":False,
        "new_forecasts_emitted":0,
        "overlapping_pairs_cannot_be_pooled_as_independent":True,
        "pairs":outputs,
    }


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    ap.add_argument("--print-report",action="store_true")
    args=ap.parse_args()
    result=derive(json.loads(ANNUAL.read_text(encoding="utf-8")),
                  json.loads(TRANSITIONS.read_text(encoding="utf-8")))
    payload=json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    if args.check_report and json.loads(OUTPUT.read_text(encoding="utf-8"))!=result:
        raise ValueError("Stored GED Brier revision ceiling differs")
    if args.print_report:
        print(payload,end="")
    else:
        print(json.dumps([{"pair":p["old_version"]+"→"+p["new_version"],
                           "annual_single_max":p["annual"]["max_absolute_single_fixed_model_brier_shift"],
                           "transition_single_max":p["transition_fourstate"]["max_absolute_single_fixed_binary_event_brier_shift"]}
                          for p in result["pairs"]],ensure_ascii=False))


if __name__=="__main__":
    main()
