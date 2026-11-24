#!/usr/bin/env python3
"""Synthetic-only adversarial tests. No real people or events in these fixtures."""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import audit_candidate_ged_retention_strata as audit


def raw(obj):
    return json.dumps(obj,sort_keys=True,ensure_ascii=False).encode("utf8")


def make_fixtures():
    years=(2021,2022,2024,2025)
    risk={2021:160,2022:161,2024:161,2025:160}
    # Country IDs 1..196 are synthetic; positives below are intentionally fabricated.
    cases={
        2021:[(1,12,12,{"clear":12},1),
              (2,18,18,{"clear":16,"check":2},2),
              (3,100,104,{"clear":100},3)],
        2022:[(1,8,19,{"check deaths":8},1)],
        2024:[(1,5,0,{"clear":5},0),
              (2,7,0,{"check dyad":7},0)],
        2025:[(1,5,0,{"check":5},0),
              (2,7,0,{"check dyad":7},0),
              (3,12,0,{"check":12},0),
              (4,38,14,{"clear":4,"check deaths":34},2)],
    }
    early_vec,late_vec,early_case,late_case=[],[],[],[]
    early_metrics={str(y):{"5":{"30":{"candidate_q3_vs_annual":{
        "n_at_risk":risk[y],"candidate_positive":len(cases[y]),
        "both_positive":sum(g>=5 for _,_,g,_,_ in cases[y]),
        "ged_positive":sum(g>=5 for _,_,g,_,_ in cases[y])
    }}}} for y in (2021,2022)}
    late_metrics={str(y):{"5":{"30":{"q3_vs_annual":{
        "n_at_risk":risk[y],"candidate_positive":len(cases[y]),
        "both_positive":sum(g>=5 for _,_,g,_,_ in cases[y]),
        "ged_positive":sum(g>=5 for _,_,g,_,_ in cases[y])
    }}}} for y in (2024,2025)}
    for y in years:
        lookup={x[0]:x for x in cases[y]}
        for cid in range(1,197):
            active=cid<=risk[y]
            q1=0 if active else 7
            positive=lookup.get(cid)
            c=positive[1] if positive else 0
            g=positive[2] if positive else 0
            name=f"Synthetic {cid}"
            if y in (2021,2022):
                early_vec.append({"year":y,"country_id":cid,"country":name,
                    "q1_candidate_best":q1,"q3_candidate_may30_best":c,
                    "annual_ged_may30_best":g})
            else:
                late_vec.append({"year":y,"country_id":cid,"country":name,
                    "candidate_q1_prior_best":q1,"candidate_q3_may30_best":c,
                    "ged_annual_may30_best":g})
            if positive:
                _,cand,ged,codes,match=positive
                if y in (2021,2022):
                    early_case.append({"year":y,"country_id":cid,"country":name,
                        "q1_candidate_best":q1,"q3_candidate_may30_best":cand,
                        "annual_ged_may30_best":ged,
                        "candidate_q3_may30_code_status_best":codes,
                        "candidate_q3_may30_events":max(1,match),
                        "candidate_exact_id_in_annual_same_country_window":match})
                else:
                    late_case.append({"year":y,"country_id":cid,"country":name,
                        "candidate_q1_prior_best":q1,"candidate_q3_may30_best":cand,
                        "ged_annual_may30_best":ged,
                        "q3_candidate_may30_code_status_best":codes,
                        "q3_candidate_may30_event_count":max(1,match),
                        "candidate_q3_may30_exact_id_present_in_ged_window":match})
    later={"status":"RETROSPECTIVE_FINAL_VINTAGE_COMPARISON_NOT_PROSPECTIVE",
           "country_universe_sha256":"synthetic-global-country-universe",
           "country_vectors":late_vec,
           "may30_t5_countries_positive_in_any_source":late_case,
           "by_year_threshold_and_horizon":late_metrics,
           "prospective_issued_probabilities":0}
    later_bytes=raw(later)
    early={"status":"ARCHIVED_FIRST_ANNUAL_GED_LABEL_RESOLUTION_NOT_ASOF",
           "source_universe_sha256":"synthetic-global-country-universe",
           "source_prev_2024_25_sha256":hashlib.sha256(later_bytes).hexdigest(),
           "country_vectors_new":early_vec,
           "primary_t5_may30_2021_22_changed_cases":early_case,
           "years_new_by_threshold_horizon":early_metrics,
           "years_pooled":[2021,2022,2024,2025],
           "new_prospective_issues":0,
           "pooled_2021_22_24_25_results":{"5":{"30":{
               "candidate_positive":10,"both_positive":5,
               "ged_positive":5,"n_at_risk":642,
           }}}}
    drift={"status":"RETROSPECTIVE_ANNUAL_VINTAGE_DRIFT_NOT_PROSPECTIVE",
           "country_universe_sha256":"synthetic-global-country-universe",
           "prospective_issued_probabilities":0,
           "by_threshold_and_horizon":{"5":{"30":{
               "first_annual_vs_later_annual":{"n_at_risk":161,"disagreements":0}
           }}}}
    return raw(early),later_bytes,raw(drift)


class CandidateGEDStrataTests(unittest.TestCase):
    def test_exact_interval_monotonic_and_extreme_cases(self):
        self.assertEqual(audit.exact_binomial_interval(0,5)[0],0)
        self.assertEqual(audit.exact_binomial_interval(4,4)[1],1)
        self.assertAlmostEqual(audit.exact_binomial_interval(4,4)[0],0.39763536,places=7)
        self.assertGreater(audit.exact_binomial_interval(1,6)[1],0.60)
        self.assertLess(audit.exact_binomial_interval(1,6)[0],0.01)
        self.assertEqual(audit.exact_binomial_interval(5,10),
                         [round(audit.exact_binomial_interval(5,10)[0],8),
                          round(audit.exact_binomial_interval(5,10)[1],8)])
        with self.assertRaises(audit.AuditError):
            audit.exact_binomial_interval(6,5)

    def test_fisher_exact_and_empty_groups(self):
        self.assertAlmostEqual(audit.fisher_two_sided(4,0,1,5),0.04761905,places=8)
        self.assertAlmostEqual(audit.fisher_two_sided(2,0,0,2),1/3,places=7)
        self.assertIsNone(audit.fisher_two_sided(0,0,1,2))
        self.assertIsNone(audit.subset_summary([])["retention_clopper_pearson_95"])

    def test_complete_4year_postselection_audit_no_model_training(self):
        a,b,c=make_fixtures()
        result=audit.build_report(a,b,c)
        self.assertEqual(result["n_country_years_at_risk"],642)
        self.assertEqual(result["n_candidate_positive_country_years"],10)
        self.assertEqual(result["overall_retention"]["n_retain_ged_label"],5)
        self.assertEqual(result["annual"]["2024"]["n_lose_ged_label"],2)
        self.assertEqual(result["annual"]["2025"]["n_retain_ged_label"],1)
        self.assertEqual(len(result["candidate_positive_cases"]),10)
        self.assertTrue(result["after_outcome_event_id_match_must_never_be_used_for_prediction"])
        self.assertFalse(result["preregistered_before_seeing_categorization_outcomes"])
        era=result["exploratory_postselection_contrasts"]["era_2021_22_vs_2024_25"]
        self.assertEqual(era["yes"]["n_retain_ged_label"],4)
        self.assertEqual(era["no"]["n_retain_ged_label"],1)
        self.assertEqual(result["new_forecasts_issued"],0)

    def test_modified_status_deaths_and_source_tampering_rejected(self):
        early,late,drift=make_fixtures()
        changed=json.loads(late)
        changed["may30_t5_countries_positive_in_any_source"][0][
            "q3_candidate_may30_code_status_best"]={"clear":999}
        with self.assertRaises(audit.AuditError):
            audit.build_report(early,raw(changed),drift)
        changed2=json.loads(early)
        changed2["source_prev_2024_25_sha256"]="f"*64
        with self.assertRaises(audit.AuditError):
            audit.build_report(raw(changed2),late,drift)
        changed3=json.loads(drift)
        changed3["by_threshold_and_horizon"]["5"]["30"][
            "first_annual_vs_later_annual"]["disagreements"]=1
        with self.assertRaises(audit.AuditError):
            audit.build_report(early,late,raw(changed3))
        changed4=json.loads(early)
        changed4["primary_t5_may30_2021_22_changed_cases"].append(
            copy.deepcopy(changed4["primary_t5_may30_2021_22_changed_cases"][0]))
        with self.assertRaises(audit.AuditError):
            audit.build_report(raw(changed4),late,drift)


if __name__=="__main__":
    unittest.main()
