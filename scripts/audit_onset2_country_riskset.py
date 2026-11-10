#!/usr/bin/env python3
"""Q-GEO-01: source-frozen country-level onset2 risk-set audit.

The official UCDP Onset 25.1 codebook explicitly states that in
*Intrastate Country Level Onset* (version 2), NO onset is coded while
another intrastate conflict is ongoing in the same country. Do not
confuse with Intrastate Country Level Multiple Onset (version 3).

For onset2 in target year T, conflict activity in T-1 and T-2 makes
the country ineligible. The +1-year risk set is fully observable at
cutoff T-1; the +2-year risk set is NOT fully observable at cutoff T-2,
because T-1 activity is then unknown. Do not use future activity to
filter the forecast cohort. Post-outcome feasibility is diagnostic only.

Official UCDP/PRIO ACD 23.1 and Onset 23.1 from a single origin edition;
25.1 Onset outcomes and 25.1 ACD for post-outcome semantic auditing only.
No country identifiers, ranks or individual probabilities in report.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiment_onset2_conflict_incidence import load_activity
from experiment_onset2_lagged_signals import load_panel, TRAIN_CUTOFFS

BASE_YEAR=2022
ASSESSED=(2023,2024)
ONSET_CODEBOOK="https://ucdp.uu.se/downloads/onset/ucdp-codebook-onset-251.pdf"
COUNTRY_LEVEL_CODE="UCDP_INTRASTATE_COUNTRY_LEVEL_ONSET_VERSION_2"
MULTIPLE_CODE="UCDP_INTRASTATE_COUNTRY_LEVEL_MULTIPLE_ONSET_VERSION_3"

def origin_risk_status(cid,target,cutoff,activity):
    """Country is certainly ineligible if any *observed* prior year active."""
    if target-cutoff not in (1,2):
        raise ValueError("Only one-/two-calendar-step horizons supported")
    first=target-2
    last=target-1
    known=range(first,min(last,cutoff)+1)
    if any((cid,year) in activity for year in known):
        return "certain_ineligible"
    if last>cutoff:
        return "possible_pending_intermediate_year"
    return "eligible_known_origin"

def after_outcome_eligibility(cid,target,activity):
    """Diagnostics only: never use T-1 from evaluation vintage as forecast feature."""
    return not any((cid,year) in activity for year in (target-2,target-1))

def audit_year(origin_onset,evaluation_onset,origin_activity,
               revised_activity,cutoff,target):
    if target-cutoff not in (1,2):
        raise ValueError("Riskset year/cutoff mismatch")
    countries=sorted(cid for cid,h in origin_onset.items() if cutoff in h)
    if len(countries)!=196:
        raise ValueError("Origin country population no longer 196")
    status={"certain_ineligible":0,"eligible_known_origin":0,
            "possible_pending_intermediate_year":0}
    outcomes={"certain_ineligible":0,"eligible_known_origin":0,
              "possible_pending_intermediate_year":0}
    future_truth_available=0
    realized_eligible=0;realized_events=0
    known_status_disagreement=0
    for cid in countries:
        year_status=origin_risk_status(cid,target,cutoff,origin_activity)
        status[year_status]+=1
        if target not in evaluation_onset.get(cid,{}):
            continue
        future_truth_available+=1
        onset2=evaluation_onset[cid][target][1]
        outcomes[year_status]+=onset2
        realized=after_outcome_eligibility(cid,target,revised_activity)
        if realized:
            realized_eligible+=1;realized_events+=onset2
        if year_status=="certain_ineligible" and onset2:
            known_status_disagreement+=1
    if future_truth_available<190:
        raise ValueError("Missing historical label coverage")
    if sum(status.values())!=196:
        raise ValueError("Riskset accounting invalid")
    return {
       "cutoff":cutoff,"target_year":target,
       "calendar_steps":target-cutoff,
       "origin_population":196,
       "observed_outcomes":future_truth_available,
       "positive_onset2":sum(outcomes.values()),
       "asof_origin_status_counts":status,
       "positive_outcomes_by_asof_status":outcomes,
       "future_target_year_eligibility_cannot_be_fully_known_at_origin":target-cutoff==2,
       "later_vintage_realized_eligible_country_years_DESCRIPTIVE_ONLY":realized_eligible,
       "later_vintage_realized_onsets_in_eligible_country_years_DESCRIPTIVE_ONLY":realized_events,
       "known_ineligible_positive_mismatches_between_vintages":known_status_disagreement,
       "future_vintage_used_to_select_fitted_or_issued_forecast_cohort":False
    }

def run(orig_onset,late_onset,orig_activity,late_activity):
    if max(max(h) for h in orig_onset.values())!=2022 or \
       max(max(h) for h in late_onset.values())!=2024 or \
       max(y for _,y in orig_activity)!=2022 or \
       max(y for _,y in late_activity)!=2024:
        raise ValueError("Risk-set audit historical-vintage coverage mismatch")
    result=[audit_year(orig_onset,late_onset,orig_activity,late_activity,2022,y)
            for y in ASSESSED]
    internal=[audit_year(orig_onset,orig_onset,orig_activity,orig_activity,
                         cutoff,cutoff+horizon)
              for cutoff in TRAIN_CUTOFFS for horizon in (1,2)]
    if sum(v["positive_onset2"] for v in result)!=2 or \
       sum(v["positive_onset2"] for v in internal)!=37:
        raise ValueError("Historical onset2 cohort count unexpectedly changed")
    return {
      "schema":"idealab.psico.onset2_country_riskset_codebook_audit.v1",
      "study_id":"EMP-ONSET2-RISKSET-231-251-20261110",
      "classification":"POST_HOC_CODEBOOK_SEMANTIC_RISKSET_AUDIT_NOT_MODEL_SELECTION",
      "official_codebook_url":ONSET_CODEBOOK,
      "country_level_dataset":COUNTRY_LEVEL_CODE,
      "different_multiple_onset_dataset":MULTIPLE_CODE,
      "target_definition":"UCDP Onset country-level onset2, not conflict-level or multiple-onset",
      "risk_definition":"Onset2 of country-level intrastate conflict requires absence of all intrastate conflict in both calendar years immediately before target; ongoing conflict rules out country-level onset, even if a different conflict begins.",
      "horizon_1":"At cutoff T-1, T-1 and T-2 activity are known. Restrict eligibility only using frozen source edition.",
      "horizon_2":"At cutoff T-2, status in T-1 is future/unknown. Activity in T-2 makes onset2 impossible, otherwise eligibility remains contingent; no future-riskset conditioning is allowed.",
      "source_23_1_used_for_origin_features":True,
      "source_25_1_activity_used_only_for_descriptive_audit":True,
      "original_2027_prospective_country_forecast_untouched":True,
      "new_predictive_skill_demonstrated":False,
      "forecast_2027_results_resolved":0,
      "external":result,
      "rolling_same_vintage_non_asof":internal,
      "limitations":"Codebook-based feasibility accounting only; no new predictive ability is claimed. UCDP 23.1 and 25.1 can revise historical incidence and onset2. Later-vintage realized risk set cannot be an ex-ante subset, especially at two-year horizon. Multiple-onset dataset allows new conflict while another persists; current country-level outcome does not. Historical rolling folds overlap; independently time-stamped origin snapshots unavailable.",
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report")
    args=ap.parse_args()
    orig,_=load_panel("23.1")
    late,_=load_panel("25.1")
    acd23,_=load_activity("23.1")
    acd25,_=load_activity("25.1")
    report=run(orig,late,acd23,acd25)
    content=json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    print("ONSET2_RISKSET_CODEBOOK_BEGIN")
    print(content,end="")
    print("ONSET2_RISKSET_CODEBOOK_END")
    if args.check_report and Path(args.check_report).read_bytes()!=content.encode("utf8"):
        raise ValueError("The official country-level riskset audit does not reproduce exactly")
    print("ONSET2_RISKSET_CODEBOOK_OK",sum(x["origin_population"] for x in report["external"]),
         "positive",sum(x["positive_onset2"] for x in report["external"]))

if __name__=="__main__":
    main()
