#!/usr/bin/env python3
"""Audit which GWNO countries drive GEO historical 2023 H2 rank reversal.

Exactly the same 196 GWNO, 2023 UCDP 26.1 outcome labels and fixed H2
model hyperparameters. Change ONLY origin training data release 23.1 to
24.1; calculate country-wise delta [Brier(four state)-Brier(binary)].
Replays SHA-pinned official data. These are retrospective pseudo-origin
reconstructions, never real ex-ante 2021-issued forecasts.
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
from experiment_geo_h2_rolling_2014_2025 import _build_fold
from experiment_geo2027_intensity_markov_cross_release import (
    EXPECTED_ROWS, MAX_DOWNLOAD, VERSION_ORDER, parse_counts,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "data/geo-h2-origin-vintage-only-brier-rank.json"
ROLLING = ROOT / "data/geo-h2-rolling-historical-2014-2025.json"
OUTPUT = ROOT / "data/geo-h2-2023-country-origin-vintage-rank-influence.json"
YEAR = 2023
ORIGIN = 2021
N = 196
EPS = 1e-11


def attribute(early_rows, later_rows, reference, rolling):
    if (reference.get("schema") !=
            "idealab.psico.geo_h2_origin_vintage_only_brier_rank.v1"
        or reference.get("annual_winner_changes_n") != 1
        or reference.get("held_fixed_outcome_release") != "26.1"
        or reference.get("old_origin_release") != "23.1"
        or reference.get("later_origin_release") != "24.1"
        or reference.get("historical_issued_asof_evidence") is not False
        or reference.get("no_2027_2028_forecasts_reissued") is not True
        or rolling.get("schema") !=
            "idealab.psico.geo_h2_rolling_historical_2014_2025.v1"
        or rolling.get("not_prospective_or_independently_timestamped_skill") is not True
        or reference.get("original_GEO2027_issue_SHA256") != SOURCE_SHA256
        or reference.get("official_UCDP_ZIP_sha256") !=
            {v: SOURCES[v]["sha256"] for v in VERSION_ORDER}
        or rolling.get("source_archives_sha256") !=
            reference["official_UCDP_ZIP_sha256"]):
        raise ValueError("Historical SHA/source/preregistration guard failed")
    fold = next((f for f in reference["annual"] if f["target_year"] == YEAR), None)
    if (not fold or fold["origin_year"] != ORIGIN or
        fold["outcome_label_revisions_n"] != 0 or
        fold["winner_origin23_1"] != "four_state_intensity" or
        fold["winner_origin24_1"] != "original_binary"):
        raise ValueError("2023 rank flip and common target label not verified")
    if len(early_rows) != N or len(later_rows) != N:
        raise ValueError("Official 196 GWNO cohort absent")
    early = {r["country_id"]:r for r in early_rows}
    later = {r["country_id"]:r for r in later_rows}
    if (len(early) != N or len(later) != N or set(early) != set(later)
        or set(early) != {r["country_id"] for r in json.loads(ISSUE.read_text())["countries"]}):
        raise ValueError("Original 196-country issue identities changed")
    results = []
    for cid in sorted(early):
        a,b = early[cid],later[cid]
        if (a["target_year"] != YEAR or b["target_year"] != YEAR
            or a["official_fatalities_estimates"] != b["official_fatalities_estimates"]
            or a["origin_active"] != b["origin_active"]):
            raise ValueError("Outcome labels, origin classification or year changed")
        y = classify(a["official_fatalities_estimates"])[1]
        values = [a["p_original_binary"],a["p_intensity_markov"],
                  b["p_original_binary"],b["p_intensity_markov"]]
        if not all(type(p) in (int,float) and math.isfinite(p) and 0<p<1 for p in values):
            raise ValueError("Non-finite original/model probability")
        pba,pfa,pbb,pfb = values
        binary_old = (pba-y)**2
        four_old = (pfa-y)**2
        binary_new = (pbb-y)**2
        four_new = (pfb-y)**2
        old_margin = four_old-binary_old
        new_margin = four_new-binary_new
        contribution = new_margin-old_margin
        results.append({
            "GWNO":cid,"target_year":YEAR,"origin_year":ORIGIN,
            "label_best_26_1":y,
            "best_deaths_26_1":a["official_fatalities_estimates"][1],
            "origin_binary_state":a["origin_active"],
            "p_binary_origin23_1":pba,
            "p_fourstate_origin23_1":pfa,
            "p_binary_origin24_1":pbb,
            "p_fourstate_origin24_1":pfb,
            "four_minus_binary_brier_origin23_1":old_margin,
            "four_minus_binary_brier_origin24_1":new_margin,
            "four_minus_binary_brier_vintage_shift":contribution,
        })
    old_sum = sum(r["four_minus_binary_brier_origin23_1"] for r in results)
    new_sum = sum(r["four_minus_binary_brier_origin24_1"] for r in results)
    shift_sum = sum(r["four_minus_binary_brier_vintage_shift"] for r in results)
    old_global = old_sum/N
    new_global = new_sum/N
    difference = shift_sum/N
    expected_old = (fold["old_origin_fixed_target_26_1_brier"]["four_state_intensity"]
                    -fold["old_origin_fixed_target_26_1_brier"]["original_binary"])
    expected_new = (fold["new_origin_fixed_target_26_1_brier"]["four_state_intensity"]
                    -fold["new_origin_fixed_target_26_1_brier"]["original_binary"])
    if (not math.isclose(old_global,expected_old,abs_tol=EPS,rel_tol=0)
        or not math.isclose(new_global,expected_new,abs_tol=EPS,rel_tol=0)
        or not math.isclose(difference,expected_new-expected_old,abs_tol=EPS,rel_tol=0)
        or not old_global < 0 < new_global):
        raise AssertionError("Exact Brier country decomposition differs from prior published 2023 flip")
    # Full 196-country nonaggregated decomposition is retained; rankings
    # and leave-one-out tests never conflate net and absolute influence.
    biggest = sorted(results,key=lambda r:(-abs(r["four_minus_binary_brier_vintage_shift"]),r["GWNO"]))
    top20 = biggest[:20]
    top20_positive = sum(r["four_minus_binary_brier_vintage_shift"] for r in top20)
    loo=[]
    for r in results:
        cid=r["GWNO"]
        old=(old_sum-r["four_minus_binary_brier_origin23_1"])/(N-1)
        new=(new_sum-r["four_minus_binary_brier_origin24_1"])/(N-1)
        loo.append({
            "GWNO":cid,"margin_origin23_1":old,"margin_origin24_1":new,
            "rank_flip_retained_without_country":old<0<new,
            "new_origin_winner_without_country":
                "four_state_intensity" if new<0 else
                "original_binary" if new>0 else "tie",
        })
    influential = [r for r in loo if not r["rank_flip_retained_without_country"]]
    return {
        "schema":"idealab.psico.geo_h2_2023_country_origin_vintage_rank_attribution.v1",
        "status":"SHA_REPLAYED_RETROSPECTIVE_COUNTRY_INFLUENCE_NOT_PROSPECTIVE",
        "horizon_years":2,"origin_year":ORIGIN,"target_year":YEAR,
        "old_origin_release":"23.1","new_origin_release":"24.1",
        "common_official_outcome_release":"26.1",
        "country_n":N,"frozen_original_GWNO_cohort":True,
        "source_ZIP_sha256":reference["official_UCDP_ZIP_sha256"],
        "original_GEO2027_issued_sha256":SOURCE_SHA256,
        "country_observations":results,
        "sum_unscaled_country_margin_shift":shift_sum,
        "mean_brier_four_minus_binary_origin23_1":old_global,
        "mean_brier_four_minus_binary_origin24_1":new_global,
        "mean_brier_margin_origin_vintage_shift":difference,
        "top20_abs_shift_countries":top20,
        "top20_signed_sum_fraction_of_total_shift":
            top20_positive/shift_sum if shift_sum != 0 else None,
        "country_leave_one_out":loo,
        "leave_one_country_out_flip_retained_n":N-len(influential),
        "leave_one_country_out_flip_lost_n":len(influential),
        "countries_whose_exclusion_loses_original_flip":influential,
        "source_version_change_not_an_individual_country_causal_effect":True,
        "historical_forecasts_issued_at_actual_origin":False,
        "new_2027_or_2028_forecasts_issued":False,
        "prospective_skill_claimed":False,
        "limitations":"Country contribution is an exact algebraic attribution of score differences, not the causal contribution of a country to the globally fitted models: one country's data may change probabilities for all countries. Source editions 23.1/24.1 postdate the hypothetical origin year 2021. No IID assumption, significance testing or prospective success claim.",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--print-report",action="store_true")
    parser.add_argument("--check-report",action="store_true")
    args=parser.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Prospective 2027 issue SHA mutated")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    source_bytes={v:request(SOURCES[v]["url"],MAX_DOWNLOAD) for v in VERSION_ORDER}
    counts={v:parse_counts(source_bytes[v],v) for v in VERSION_ORDER}
    if any(sum(map(len,counts[v].values()))!=EXPECTED_ROWS[v] for v in VERSION_ORDER):
        raise ValueError("Official source archive country-year rows differ")
    # Full original official source SHA and target-best-vs-count consistency
    # are enforced by read_verified_intervals + _build_fold.
    panels={v:read_verified_intervals(source_bytes[v],v) for v in VERSION_ORDER}
    ids=sorted(r["country_id"] for r in json.loads(ISSUE.read_text())["countries"])
    rows={}
    for origin_v in ("23.1","24.1"):
        rows[origin_v],meta=_build_fold({
            "origin_year":ORIGIN,"target_year":YEAR,
            "origin_release":origin_v,"outcome_release":"26.1",
        },counts,panels,ids)
        if (meta["last_training_year"]!=ORIGIN or
            meta["four_state_last_training_year"]!=ORIGIN or
            meta["country_n"]!=N):
            raise ValueError("Model training cutoff / GWNO issue cohort incorrect")
    result=attribute(rows["23.1"],rows["24.1"],
                     json.loads(REFERENCE.read_text(encoding="utf-8")),
                     json.loads(ROLLING.read_text(encoding="utf-8")))
    payload=json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n"
    if args.check_report and json.loads(OUTPUT.read_text(encoding="utf-8"))!=result:
        raise ValueError("Official 2023 country influence report no longer reproducible")
    if args.print_report:
        print("GEO_2023_COUNTRY_INFLUENCE_BEGIN",flush=True)
        print(payload,end="")
        print("GEO_2023_COUNTRY_INFLUENCE_END",flush=True)
    else:
        print(json.dumps({
            "country_n":result["country_n"],
            "old_margin":result["mean_brier_four_minus_binary_origin23_1"],
            "new_margin":result["mean_brier_four_minus_binary_origin24_1"],
            "top_countries":[r["GWNO"] for r in result["top20_abs_shift_countries"][:5]],
            "leave_one_out_lost_n":result["leave_one_country_out_flip_lost_n"],
        },sort_keys=True))


if __name__=="__main__":
    main()
