#!/usr/bin/env python3
"""Explain candidate→first-annual-GED label heterogeneity, without training.

Exploratory post-selection descriptive audit, NOT as-of forecasting.
Only reads SHA-audited frozen institutional public reports (#151/#152/#153).
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EARLY = ROOT / "data/candidate-ged-2021-22-resolution.json"
LATE = ROOT / "data/candidate-to-annual-ged-resolution.json"
DRIFT = ROOT / "data/ged2024-annual-vintage-drift.json"
RESULT = ROOT / "data/candidate-ged-retention-strata.json"
YEARS = (2021, 2022, 2024, 2025)
PRIOR_YEARS = (2021, 2022)
RECENT_YEARS = (2024, 2025)
THRESHOLD = 5


class AuditError(ValueError):
    pass


def exact_binomial_interval(successes, n, alpha=0.05):
    """Clopper-Pearson by monotone binomial tail inversion; never Wald CI."""
    if not 0 <= successes <= n or n <= 0:
        raise AuditError("Exact interval requires 0<=successes<=n and n>0")
    def upper_tail(k, p):
        return sum(math.comb(n, i) * p ** i * (1-p) ** (n-i)
                   for i in range(k, n+1))
    def lower_tail(k, p):
        return sum(math.comb(n, i) * p ** i * (1-p) ** (n-i)
                   for i in range(k+1))
    if successes == 0:
        lo = 0.0
    else:
        a,b=0.0,1.0
        for _ in range(70):
            mid=(a+b)/2
            if upper_tail(successes, mid)<alpha/2:
                a=mid
            else:
                b=mid
        lo=(a+b)/2
    if successes == n:
        hi = 1.0
    else:
        a,b=0.0,1.0
        for _ in range(70):
            mid=(a+b)/2
            if lower_tail(successes, mid)>alpha/2:
                a=mid
            else:
                b=mid
        hi=(a+b)/2
    return [round(lo,8),round(hi,8)]


def fisher_two_sided(a,b,c,d):
    """Exact hypergeometric Fisher conditional on margins; exploratory only."""
    if any(not isinstance(x,int) or x<0 for x in (a,b,c,d)):
        raise AuditError("Invalid 2x2 contingency")
    n1,n2=a+b,c+d
    if n1==0 or n2==0:
        return None
    k=a+c
    n=n1+n2
    denom=math.comb(n,n1)
    def p(x):
        return (math.comb(k,x)*math.comb(n-k,n1-x))/denom
    xmin=max(0,n1-(n-k));xmax=min(k,n1)
    p_obs=p(a)
    return round(sum(p(x) for x in range(xmin,xmax+1) if p(x)<=p_obs+1e-12),8)


def subset_summary(rows):
    n=len(rows)
    retained=sum(int(r["retained_ged"]) for r in rows)
    return {
        "n_candidate_positive": n,
        "n_retain_ged_label": retained,
        "n_lose_ged_label": n-retained,
        "retention_share": round(retained/n,8) if n else None,
        "retention_clopper_pearson_95": exact_binomial_interval(retained,n) if n else None,
    }


def split_summary(rows, name, test):
    yes=[r for r in rows if test(r)]
    no=[r for r in rows if not test(r)]
    yes_stats=subset_summary(yes)
    no_stats=subset_summary(no)
    return {
        "comparison": name,
        "yes": yes_stats,
        "no": no_stats,
        "fisher_exact_two_sided_exploratory_postselection": fisher_two_sided(
            yes_stats["n_retain_ged_label"],yes_stats["n_lose_ged_label"],
            no_stats["n_retain_ged_label"],no_stats["n_lose_ged_label"]
        ),
        "not_a_prospective_feature_assessment": name=="same_country_window_exact_id_in_later_ged",
    }


def raw_bytes(earlier=None,later=None,drift=None):
    return (
        EARLY.read_bytes() if earlier is None else earlier,
        LATE.read_bytes() if later is None else later,
        DRIFT.read_bytes() if drift is None else drift,
    )


def build_report(early_raw=None,late_raw=None,drift_raw=None):
    early_bytes,late_bytes,drift_bytes=raw_bytes(early_raw,late_raw,drift_raw)
    early=json.loads(early_bytes)
    late=json.loads(late_bytes)
    drift=json.loads(drift_bytes)
    if early.get("status")!="ARCHIVED_FIRST_ANNUAL_GED_LABEL_RESOLUTION_NOT_ASOF":
        raise AuditError("Early report wrong frozen research status")
    if late.get("status")!="RETROSPECTIVE_FINAL_VINTAGE_COMPARISON_NOT_PROSPECTIVE":
        raise AuditError("Later report wrong frozen research status")
    if drift.get("status")!="RETROSPECTIVE_ANNUAL_VINTAGE_DRIFT_NOT_PROSPECTIVE":
        raise AuditError("Intra-GED historical drift source status mismatch")
    if early["source_prev_2024_25_sha256"]!=hashlib.sha256(late_bytes).hexdigest():
        raise AuditError("2024/25 report SHA mismatch: pinned="+early["source_prev_2024_25_sha256"]+" actual="+hashlib.sha256(late_bytes).hexdigest())
    if early["source_universe_sha256"]!=late["country_universe_sha256"] or early["source_universe_sha256"]!=drift["country_universe_sha256"]:
        raise AuditError("Country universe not the same across frozen studies")
    if (early["years_pooled"]!=list(YEARS)
        or len(early["country_vectors_new"])!=392 or len(late["country_vectors"])!=392
        or early["new_prospective_issues"]!=0 or late["prospective_issued_probabilities"]!=0
        or drift["prospective_issued_probabilities"]!=0):
        raise AuditError("Frozen historical year/risk/forecast conditions invalid")
    if drift["by_threshold_and_horizon"]["5"]["30"]["first_annual_vs_later_annual"]["disagreements"]!=0:
        raise AuditError("2024 first/later annual GED label source unexpectedly differs")
    if drift["by_threshold_and_horizon"]["5"]["30"]["first_annual_vs_later_annual"]["n_at_risk"]!=161:
        raise AuditError("Frozen 2024 GED drift not the 161-risk-country cohort")

    vectors={}
    for row in early["country_vectors_new"]:
        year, cid=row["year"],row["country_id"]
        if year not in PRIOR_YEARS or (year,cid) in vectors:
            raise AuditError("Missing/duplicate or wrong-year early country vector")
        vectors[(year,cid)]={"q1":row["q1_candidate_best"],
            "candidate_q3":row["q3_candidate_may30_best"],
            "annual":row["annual_ged_may30_best"],"country":row["country"]}
    for row in late["country_vectors"]:
        year,cid=row["year"],row["country_id"]
        if year not in RECENT_YEARS or (year,cid) in vectors:
            raise AuditError("Missing/duplicate or wrong-year later country vector")
        vectors[(year,cid)]={"q1":row["candidate_q1_prior_best"],
            "candidate_q3":row["candidate_q3_may30_best"],
            "annual":row["ged_annual_may30_best"],"country":row["country"]}
    if len(vectors)!=784:
        raise AuditError("Expected 196 countries by 4 annual cohorts")

    early_cases=early["primary_t5_may30_2021_22_changed_cases"]
    late_cases=late["may30_t5_countries_positive_in_any_source"]
    candidate_positive=[]
    for source,items in (("early",early_cases),("recent",late_cases)):
        for row in items:
            year,cid=row["year"],row["country_id"]
            if (source=="early" and year not in PRIOR_YEARS
                or source=="recent" and year not in RECENT_YEARS):
                raise AuditError("Historical candidate cases assigned wrong source era")
            cand=(row["q3_candidate_may30_best"] if source=="early"
                  else row["candidate_q3_may30_best"])
            annual=(row["annual_ged_may30_best"] if source=="early"
                    else row["ged_annual_may30_best"])
            prior=(row["q1_candidate_best"] if source=="early"
                   else row["candidate_q1_prior_best"])
            if cand<THRESHOLD:
                # Such Q2-only cases belong in the preexisting study but not
                # in this analysis conditioned on positive Candidate Q3.
                continue
            if (prior>=THRESHOLD or (year,cid) not in vectors or
                vectors[(year,cid)]!={"q1":prior,"candidate_q3":cand,
                    "annual":annual,"country":row["country"]}):
                raise AuditError("Case does not reproduce fixed country-level risk/outcome")
            raw_codes=(row["candidate_q3_may30_code_status_best"] if source=="early"
                       else row["q3_candidate_may30_code_status_best"])
            if (not isinstance(raw_codes,dict) or
                any((not isinstance(n,int) or n<0 or not isinstance(k,str))
                    for k,n in raw_codes.items()) or
                sum(raw_codes.values())!=cand):
                raise AuditError("Candidate status breakdown does not sum to its frozen deaths")
            codes={k.strip().casefold():v for k,v in raw_codes.items()}
            if len(codes)!=len(raw_codes):
                raise AuditError("Overlapping status categories under normalization")
            events=(row["candidate_q3_may30_events"] if source=="early"
                    else row["q3_candidate_may30_event_count"])
            matched=(row["candidate_exact_id_in_annual_same_country_window"]
                     if source=="early" else row["candidate_q3_may30_exact_id_present_in_ged_window"])
            if not 0<=matched<=events or events<=0:
                raise AuditError("Event matching index cannot exceed provisional eligible records")
            candidate_positive.append({
                "year":year,"country_id":cid,"country":row["country"],
                "era":"2021-2022" if year<=2022 else "2024-2025",
                "candidate_q1_best":prior,
                "candidate_q3_may30_best":cand,
                "ged_first_annual_may30_best":annual,
                "candidate_margin_over_threshold":cand-THRESHOLD,
                "candidate_best_5_to_9":5<=cand<10,
                "candidate_clear_best":codes.get("clear",0),
                "clear_only_meets_threshold":codes.get("clear",0)>=THRESHOLD,
                "has_check_dyad":codes.get("check dyad",0)>0,
                "candidate_code_status_best":dict(sorted(codes.items())),
                "candidate_state_events":events,
                "candidate_same_country_window_exact_id_match_count":matched,
                "post_ged_has_exact_id_match":matched>0,
                "retained_ged":annual>=THRESHOLD,
            })
    candidate_positive.sort(key=lambda x:(x["year"],x["country_id"]))
    if len(candidate_positive)!=10 or len({(x["year"],x["country_id"]) for x in candidate_positive})!=10:
        raise AuditError("Exactly ten distinct historical Candidate-positive country-years required")
    by_year={}
    previous_aggregate=early["pooled_2021_22_24_25_results"]["5"]["30"]
    for year in YEARS:
        group=[r for r in candidate_positive if r["year"]==year]
        pair=(early["years_new_by_threshold_horizon"][str(year)]["5"]["30"]["candidate_q3_vs_annual"]
              if year in PRIOR_YEARS else
              late["by_year_threshold_and_horizon"][str(year)]["5"]["30"]["q3_vs_annual"])
        pred=subset_summary(group)
        observed_cases=[v for (y,_),v in vectors.items() if y==year and v["q1"]<THRESHOLD]
        ged_positive=sum(x["annual"]>=THRESHOLD for x in observed_cases)
        if (len(group)!=pair["candidate_positive"] or pred["n_retain_ged_label"]!=pair["both_positive"]
            or len(observed_cases)!=pair["n_at_risk"] or ged_positive!=pair["ged_positive"]):
            raise AuditError("Stratification does not match frozen national confusion matrices")
        by_year[str(year)]={"n_at_risk":len(observed_cases),"ged_annual_positive":ged_positive,**pred}
    summary=subset_summary(candidate_positive)
    if (summary["n_candidate_positive"]!=previous_aggregate["candidate_positive"]
        or summary["n_retain_ged_label"]!=previous_aggregate["both_positive"]
        or sum(by_year[str(y)]["n_at_risk"] for y in YEARS)!=previous_aggregate["n_at_risk"]):
        raise AuditError("Combined study fails to reconstruct previously frozen pooled T=5 30d")
    distinctions={
        "era_2021_22_vs_2024_25":split_summary(
            candidate_positive,"early_era_2021_2022",lambda r:r["year"]<=2022),
        "candidate_best_at_least_10":split_summary(
            candidate_positive,"candidate_best_at_least_10",lambda r:r["candidate_q3_may30_best"]>=10),
        "candidate_clear_only_at_least_5":split_summary(
            candidate_positive,"candidate_clear_only_at_least_5",lambda r:r["clear_only_meets_threshold"]),
        "candidate_has_check_dyad":split_summary(
            candidate_positive,"candidate_has_check_dyad",lambda r:r["has_check_dyad"]),
        "same_country_window_exact_id_in_later_ged":split_summary(
            candidate_positive,"same_country_window_exact_id_in_later_ged",
            lambda r:r["post_ged_has_exact_id_match"]),
    }
    strata_by_era={
        era:{
            "margin_5_to_9":subset_summary([r for r in candidate_positive if r["era"]==era and r["candidate_best_5_to_9"]]),
            "margin_at_least_10":subset_summary([r for r in candidate_positive if r["era"]==era and not r["candidate_best_5_to_9"]]),
            "clear_only_at_least_5":subset_summary([r for r in candidate_positive if r["era"]==era and r["clear_only_meets_threshold"]]),
        }
        for era in ("2021-2022","2024-2025")
    }
    return {
        "schema":"idealab.psico.candidate_ged_retention_strata.v1",
        "status":"POST_SELECTED_EXPLORATORY_NON_CAUSAL_NO_FORECASTS",
        "analysis_date":"2026-11-24",
        "source_reports":{
            "candidate_2021_22_and_4year_pool_sha256":hashlib.sha256(early_bytes).hexdigest(),
            "candidate_2024_25_sha256":hashlib.sha256(late_bytes).hexdigest(),
            "ged2024_two_annual_vintages_sha256":hashlib.sha256(drift_bytes).hexdigest(),
        },
        "criterion":"Candidate Q1 state-based best <5, Candidate Q3 May1-30 best >=5; retain if first annual GED same period best >=5",
        "n_country_years_at_risk":previous_aggregate["n_at_risk"],
        "n_candidate_positive_country_years":summary["n_candidate_positive"],
        "n_ged_annual_positive_country_years":previous_aggregate["ged_positive"],
        "overall_retention":summary,
        "annual":by_year,
        "candidate_positive_cases":candidate_positive,
        "exploratory_postselection_contrasts":distinctions,
        "conditioned_by_era":strata_by_era,
        "ged2024_25_1_to_26_1_t5_30d_label_disagreements":0,
        "after_outcome_event_id_match_must_never_be_used_for_prediction":True,
        "preregistered_before_seeing_categorization_outcomes":False,
        "candidate_first_release_dates_certified":False,
        "new_forecasts_issued":0,
        "prospective_cohorts_modified":0,
        "interpretation":(
            "The year split was noticed before this audit, and code-status/margin "
            "subgroups were chosen after seeing the ten events. All Fisher tests and "
            "binomial confidence intervals describe a tiny dependent postselected "
            "sample; do not use them as evidence for causal change, external prediction "
            "skill or an alerting rule. GED exact event ID match is post-outcome leakage. "
            "The mapping between Candidate and first annual GED is temporally heterogeneous "
            "and provisional coding status Clear is neither necessary nor sufficient."
        ),
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--print-report",action="store_true")
    modes.add_argument("--check-report",action="store_true")
    args=parser.parse_args(argv)
    try:
        result=build_report()
        if args.print_report:
            print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
        else:
            frozen=json.loads(RESULT.read_text("utf8"))
            if frozen!=result:
                raise AuditError("Frozen four-year Candidate-to-GED explanatory strata diverged")
            print("OK: frozen annual labels, case strata, event-ID leakage separation and privacy-safe report")
    except (AuditError,KeyError,TypeError,OSError,ValueError) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 2
    return 0


if __name__=="__main__":
    sys.exit(main())
