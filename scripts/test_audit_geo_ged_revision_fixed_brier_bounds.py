#!/usr/bin/env python3
"""Pure synthetic tests: Brier-label revision inequalities and source guards."""
import copy
import unittest
from audit_geo_ged_revision_fixed_brier_bounds import derive


def case(flips=1, touched=2):
    years=[2013,2014,2015,2016]
    return (
        {"historical_model_fitting_authorized":False,
         "GEO2027_GEO2028_forecasts_modified":False,
         "source_zip_sha256":{"synthetic":"placeholder"},
         "pairs":[{"old_version":"A","new_version":"B","is_consecutive_release":True,
                   "comparison":{"target_years":years,"eligible_countries_per_year":2,
                                 "observed_country_years":8,
                                 "best_ge25_binary_label_change_n":flips}}]},
        {"prospective_skill_claimed":False,"new_predictions_issued":0,
         "source_hashes":{"synthetic":"placeholder"},
         "pairs":[{"old_version":"A","new_version":"B","years_compared":years,
                   "cohort_country_n":2,"eligible_country_transitions":6,
                   "revised_two_year_transition_labels":touched,
                   "revised_transition_country_start_year":[{"GWNO":1,"start_year":i}
                                                             for i in range(touched)]}]}
    )


class TestFiniteBrierSensitivity(unittest.TestCase):
    def test_one_change_two_transitions(self):
        a,b=case()
        p=derive(a,b)["pairs"][0]
        self.assertEqual(p["annual"]["max_absolute_single_fixed_model_brier_shift"],1/8)
        self.assertEqual(p["transition_fourstate"]["max_absolute_single_fixed_binary_event_brier_shift"],2/6)

    def test_zero_flips_means_zero_ceiling(self):
        a,b=case(0,0)
        p=derive(a,b)["pairs"][0]
        self.assertEqual(p["annual"]["max_absolute_two_fixed_model_delta_brier_shift"],0)
        self.assertEqual(p["transition_fourstate"]["max_absolute_two_fixed_binary_event_delta_brier_shift"],0)

    def test_algebra_one_case_extremes(self):
        for y,yp in ((0,1),(1,0)):
            for p in (0,0.1,0.5,0.9,1):
                score_shift=(p-yp)**2-(p-y)**2
                self.assertLessEqual(abs(score_shift),1+1e-12)
                for q in (0,0.3,1):
                    diff=((q-yp)**2-(p-yp)**2)-((q-y)**2-(p-y)**2)
                    self.assertLessEqual(abs(diff),2+1e-12)

    def test_bad_provenance_refused(self):
        a,b=case()
        a["historical_model_fitting_authorized"]=True
        with self.assertRaises(ValueError):
            derive(a,b)

    def test_bad_sha_refused(self):
        a,b=case()
        b["source_hashes"]={"different":"placeholder"}
        with self.assertRaises(ValueError):
            derive(a,b)

    def test_bad_denominator_refused(self):
        a,b=case()
        b["pairs"][0]["eligible_country_transitions"]=7
        with self.assertRaises(ValueError):
            derive(a,b)

    def test_duplicate_pairs_refused(self):
        a,b=case()
        a["pairs"].append(copy.deepcopy(a["pairs"][0]))
        with self.assertRaises(ValueError):
            derive(a,b)


if __name__=="__main__":
    unittest.main()
