#!/usr/bin/env python3
"""Country-cluster influence on four historical source-separated ACD persistence folds.

This is an EX-POST diagnostic of the *previously published* (not independently
issued) 2021-2024 historical forecasts, holding every forecast fixed when a
country is excluded. Never interpret deletion as retraining or cross-validation.
Never read 2026/2027 labels; never compare ACD to the GEO/NEWCONF endpoints.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path

import backtest_ucdp_prio_retention_four_vintages as original
import build_2027_prospective_registry as prospective

FROZEN_REPORT = Path(__file__).resolve().parents[1] / "data/ucdp-prio-2021-2024-retention-four-vintage.json"
EPS = 1e-11
MODELS = ("p_lag1_group", "p_country_eb")
PRIMARY_BASELINE = "p_global_recent5"


def difference(p: float, baseline: float, y: int) -> float:
    """Paired Brier(candidate) minus Brier(global baseline), exact for a row."""
    if (type(y) is not int or y not in (0, 1) or
        any(type(x) not in (float, int) or not math.isfinite(x) or not 0 < x < 1
            for x in (p, baseline))):
        raise ValueError("Invalid frozen historical probability or outcome")
    return (p-y)**2-(baseline-y)**2


def analyze_ledger(rows: list[dict]) -> dict:
    """Exhaustive fixed-forecast leave-one-country-GWNO-out influence.

    An entire country cluster is omitted across *all* available target years;
    the 3 original probability vectors are never re-fit.
    """
    if not rows:
        raise ValueError("Empty historical ACD ledger")
    seen = set()
    by_country = defaultdict(list)
    for row in rows:
        country_id, target_year, y = (row["country_id"], row["target_year"],
                                      row["observed_acd"])
        if (type(country_id) is not int or country_id < 1 or
            type(target_year) is not int or
            type(y) is not int or y not in (0, 1)):
            raise ValueError("Invalid historical GWNO/year/label")
        key = (country_id, target_year)
        if key in seen:
            raise ValueError("Repeated historical country-target-year score")
        seen.add(key)
        if set(row["models"]) != set(MODELS + (PRIMARY_BASELINE,)):
            raise ValueError("Original three ACD models must be preserved")
        for name in MODELS:
            difference(row["models"][name], row["models"][PRIMARY_BASELINE], y)
        by_country[country_id].append(row)
    N=len(rows)
    if len(by_country)==1:
        raise ValueError("No independent country cluster can be excluded")
    per_model = {}
    for candidate in MODELS:
        contributions = {
            cid: sum(difference(r["models"][candidate],
                                r["models"][PRIMARY_BASELINE],
                                r["observed_acd"]) for r in country_rows)
            for cid, country_rows in by_country.items()
        }
        total = sum(contributions.values())
        mean = total/N
        deletions = []
        for cid,country_rows in by_country.items():
            n=len(country_rows)
            if N==n:
                raise ValueError("No observations after country deletion")
            omitted = (total - contributions[cid])/(N-n)
            effect = omitted-mean
            deletions.append({
                "country_id":cid,
                "n_original_fold_appearances":n,
                "target_years":[r["target_year"] for r in country_rows],
                "sum_original_paired_loss_contribution":contributions[cid],
                "leave_one_country_out_delta_brier":omitted,
                "delta_change_when_country_excluded":effect,
                "reverses_pooled_sign":((mean < -EPS and omitted > EPS) or
                                         (mean > EPS and omitted < -EPS)),
            })
        deletions.sort(key=lambda r:(
            -abs(r["delta_change_when_country_excluded"]),r["country_id"]
        ))
        ordered_contributions = sorted(
            contributions.items(), key=lambda pair:-abs(pair[1])
        )
        per_model[candidate] = {
            "pooled_delta_brier_candidate_minus_global":mean,
            "pooled_sum_paired_loss":total,
            "n_country_deletions":len(deletions),
            "n_sign_reversals":sum(r["reverses_pooled_sign"] for r in deletions),
            "sign_reversals":sorted(
                [r["country_id"] for r in deletions
                 if r["reverses_pooled_sign"]]
            ),
            "min_leave_one_country_out_delta":min(
                r["leave_one_country_out_delta_brier"] for r in deletions),
            "max_leave_one_country_out_delta":max(
                r["leave_one_country_out_delta_brier"] for r in deletions),
            "top_eight_absolute_influence":deletions[:8],
            "all_leave_one_country_out":sorted(
                deletions,key=lambda r:r["country_id"]),
            "share_abs_total_contributions_top_five":(
                sum(abs(v) for _,v in ordered_contributions[:5])/
                sum(abs(v) for v in contributions.values())
                if any(v != 0 for v in contributions.values()) else None
            ),
        }
    counts=Counter(len(v) for v in by_country.values())
    return {
        "total_country_year_fold_scores":N,
        "unique_country_clusters":len(by_country),
        "country_cluster_appearances_histogram":dict(sorted(counts.items())),
        "repeated_country_clusters":sum(len(v)>1 for v in by_country.values()),
        "fixed_predictions_no_refit":True,
        "no_country_years_outside_original_active_origin_cohorts":True,
        "secondary_not_prospectively_independent":True,
        "per_model":per_model,
    }


def reconstruct_ledger(versions: dict, metadata: dict,
                       frozen: dict) -> list[dict]:
    """Verify all six historical source vintages and reproduce four benchmarks."""
    audited = original.diagnose(versions,metadata)
    if (audited["status"]!="SHA_PINNED_EX_POST_FOUR_ORIGIN_TARGET_VINTAGES" or
        audited["2027_outcomes_observed"]!=0 or
        audited["n_country_year_fold_evaluations"]!=137 or
        audited["n_country_year_persistence_positives"]!=116 or
        frozen["source_sha256_by_version"]!=audited["source_sha256_by_version"] or
        frozen["target_years"]!=audited["target_years"] or
        frozen["n_country_year_fold_evaluations"]!=137 or
        frozen["n_country_year_persistence_positives"]!=116):
        raise ValueError("SHA-pinned published historical cohort changed")
    for name in (PRIMARY_BASELINE,)+MODELS:
        if abs(frozen["pooled_models"][name]["pooled_brier"]-
               audited["pooled_models"][name]["pooled_brier"])>EPS:
            raise ValueError("Published source-separated historical Brier changed")
    result=[]
    for _,_,origin_year,target_year in original.PAIRS:
        origin_version = next(v for v,w,a,b in original.PAIRS
                              if a==origin_year and b==target_year)
        target_version = next(w for v,w,a,b in original.PAIRS
                              if a==origin_year and b==target_year)
        origin_set,target_set=versions[origin_version],versions[target_version]
        predictions,fit=original.predict(origin_set,origin_year)
        if fit["latest_training_target_year"]>origin_year:
            raise ValueError("Forward labels in archived historical predictions")
        target_country_ids={cid for cid,_ in target_set}
        for cid,ps in sorted(predictions.items()):
            if cid not in target_country_ids:
                raise ValueError("Historical target code missing from official source")
            if not isinstance(cid,str) or not cid.isdecimal() or not 1 <= int(cid) <= 2000:
                raise ValueError("Invalid singleton source GWNO string")
            result.append({
                "country_id":int(cid),
                "target_year":target_year,
                "observed_acd":int((cid,target_year) in target_set),
                "models":{name:ps[name] for name in (PRIMARY_BASELINE,)+MODELS},
            })
    if len(result)!=137 or sum(r["observed_acd"] for r in result)!=116:
        raise ValueError("Reconstructed row-level original cohort inconsistent")
    return result


def evaluate(versions: dict, metadata: dict, frozen: dict,
             issued_docs: dict, manifests: dict) -> dict:
    # Rebuild and attest all already issued 2027 documents: future label count = 0.
    reg=prospective.make_registry(issued_docs,manifests)
    if (reg["n_verified_future_2027_outcomes"]!=0 or
        reg["n_unique_country_endpoint_rows"]!=424):
        raise ValueError("Prospective 2027 issue registry modified")
    ledger=reconstruct_ledger(versions,metadata,frozen)
    stats=analyze_ledger(ledger)
    if stats["total_country_year_fold_scores"] != 137:
        raise ValueError("Historical 137-country-year cohort changed")
    names={r["country_id"]:r["country"] for r in issued_docs["geo"]["countries"]}
    # Use names only where GWNO exists in original frozen institutional 196;
    # earlier historical countries need not be in the 2025 country universe.
    for model in MODELS:
        model_report=stats["per_model"][model]
        baseline=frozen["pooled_models"][PRIMARY_BASELINE]["pooled_brier"]
        expected=frozen["pooled_models"][model]["pooled_brier"]-baseline
        if abs(model_report["pooled_delta_brier_candidate_minus_global"]-
               expected)>EPS:
            raise ValueError("Country deletion ledger no longer reproduces pooled Brier")
        for record in model_report["all_leave_one_country_out"]:
            record["country_name_from_2025_gwno_crosswalk"]=names.get(
                record["country_id"])
        for record in model_report["top_eight_absolute_influence"]:
            record["country_name_from_2025_gwno_crosswalk"]=names.get(
                record["country_id"])
    return {
        "schema":"idealab.psico.acd_historical_country_cluster_influence.v1",
        "status":"EX_POST_FIXED_FORECAST_DIAGNOSTIC_NO_PROSPECTIVE_SKILL",
        "endpoint":"ACD type 3/4 recorded at t+2 among historically origin-active countries",
        "not_geo2027_or_newconf2027":True,
        "historical_target_years":[2021,2022,2023,2024],
        "historical_source_sha256_by_version":frozen["source_sha256_by_version"],
        "historical_folds_reproduced":True,
        "original_acd2027_sha256":prospective.EXPECTED["acd"][1],
        "original_acd2027_first_public_commit":prospective.EXPECTED["acd"][2],
        "2027_outcomes_observed":0,
        "original_424_issued_country_endpoint_rows_unchanged":True,
        **stats,
        "limitations":(
            "Exploratory ex-post country influence: all forecast probabilities "
            "are fixed while each country is excluded from all folds; not "
            "leave-one-country-out retraining, independence, external holdout "
            "or population-generalizable significance. All four adjacent years "
            "share geopolitical dependence and countries recur. Source editions "
            "are pinned but contemporaneous historical issue timestamps "
            "are not independently notarized. No 2027 labels or new forecasts."
        )
    }


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--summary",action="store_true")
    parser.add_argument("--check-report",metavar="PATH")
    args=parser.parse_args()
    docs,manifests=prospective.read_issued()
    versions,metadata=original.load_sources()
    frozen=json.loads(FROZEN_REPORT.read_text(encoding="utf8"))
    report=evaluate(versions,metadata,frozen,docs,manifests)
    body=json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    if args.summary:
        view={k:report[k] for k in (
            "schema","2027_outcomes_observed","total_country_year_fold_scores",
            "unique_country_clusters","country_cluster_appearances_histogram",
            "repeated_country_clusters","historical_folds_reproduced","per_model",
            "limitations"
        )}
        # Present the first eight influential countries, not 100+ full records.
        for value in view["per_model"].values():
            value.pop("all_leave_one_country_out",None)
        body=json.dumps(view,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    if args.check_report and Path(args.check_report).read_bytes()!=body.encode("utf8"):
        raise ValueError("ACD historical country-cluster diagnostic changed")
    print("ACD_HISTORICAL_COUNTRY_INFLUENCE_BEGIN")
    print(body,end="")
    print("ACD_HISTORICAL_COUNTRY_INFLUENCE_END")


if __name__=="__main__":
    main()
