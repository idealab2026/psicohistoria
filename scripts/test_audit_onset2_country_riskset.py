import unittest

from audit_onset2_country_riskset import (
    audit_year,origin_risk_status,after_outcome_eligibility,
    run,ONSET_CODEBOOK,COUNTRY_LEVEL_CODE,MULTIPLE_CODE
)

def panels():
    prior={}
    late={}
    for cid in range(1,197):
        code=str(cid)
        prior[code]={year:(0,0) for year in range(1946,2023)}
        late[code]={year:(0,0) for year in range(1946,2025)}
    late["4"][2023]=(1,1)
    late["5"][2024]=(1,1)
    old_activity={("20",2021),("21",2022),("22",2021)}
    later_activity=old_activity|{("6",2023),("4",2023),("5",2024)}
    return prior,late,old_activity,later_activity

class CountryLevelOnsetRiskSetTests(unittest.TestCase):
    def test_one_year_eligible_requires_two_inactive_years_known(self):
        activity={("20",2021),("21",2022)}
        self.assertEqual(origin_risk_status("20",2023,2022,activity),
                         "certain_ineligible")
        self.assertEqual(origin_risk_status("21",2023,2022,activity),
                         "certain_ineligible")
        self.assertEqual(origin_risk_status("22",2023,2022,activity),
                         "eligible_known_origin")
        self.assertTrue(after_outcome_eligibility("22",2023,activity))
        self.assertFalse(after_outcome_eligibility("20",2023,activity))

    def test_two_year_target_year_intermediate_is_UNKNOWN_not_absent(self):
        activity={("20",2021),("21",2022),("22",2023)}
        self.assertEqual(origin_risk_status("21",2024,2022,activity),
                         "certain_ineligible")
        self.assertEqual(origin_risk_status("20",2024,2022,activity),
                         "possible_pending_intermediate_year")
        self.assertEqual(origin_risk_status("22",2024,2022,activity),
                         "possible_pending_intermediate_year")
        self.assertFalse(after_outcome_eligibility("22",2024,activity))
        self.assertNotEqual(origin_risk_status("22",2024,2022,activity),
                            "eligible_known_origin")

    def test_cross_release_diagnostics_do_not_use_future_as_features(self):
        old,late,acf,newacf=panels()
        a=audit_year(old,late,acf,newacf,2022,2023)
        b=audit_year(old,late,acf,newacf,2022,2024)
        self.assertEqual(a["origin_population"],196)
        self.assertEqual(a["observed_outcomes"],196)
        self.assertEqual(a["positive_onset2"],1)
        self.assertEqual(a["asof_origin_status_counts"]["certain_ineligible"],3)
        self.assertEqual(a["asof_origin_status_counts"]["eligible_known_origin"],193)
        self.assertEqual(a["asof_origin_status_counts"]["possible_pending_intermediate_year"],0)
        self.assertFalse(a["future_target_year_eligibility_cannot_be_fully_known_at_origin"])
        self.assertEqual(b["asof_origin_status_counts"]["certain_ineligible"],1)
        self.assertEqual(b["asof_origin_status_counts"]["possible_pending_intermediate_year"],195)
        self.assertEqual(b["asof_origin_status_counts"]["eligible_known_origin"],0)
        self.assertTrue(b["future_target_year_eligibility_cannot_be_fully_known_at_origin"])
        self.assertEqual(b["positive_outcomes_by_asof_status"]["possible_pending_intermediate_year"],1)
        self.assertFalse(b["future_vintage_used_to_select_fitted_or_issued_forecast_cohort"])
        # A future change to 2023 incidence can change retrospective realized
        # eligibility but NOT any status known at 2022 cutoff.
        future=newacf|{("7",2023)}
        changed=audit_year(old,late,acf,future,2022,2024)
        self.assertEqual(b["asof_origin_status_counts"],changed["asof_origin_status_counts"])
        self.assertEqual(b["positive_outcomes_by_asof_status"],changed["positive_outcomes_by_asof_status"])
        self.assertEqual(
           changed["later_vintage_realized_eligible_country_years_DESCRIPTIVE_ONLY"],
           b["later_vintage_realized_eligible_country_years_DESCRIPTIVE_ONLY"]-1)

    def test_do_not_mistake_multiple_onset_for_country_level_onset(self):
        self.assertIn("ucdp-codebook-onset-251.pdf",ONSET_CODEBOOK)
        self.assertIn("COUNTRY_LEVEL_ONSET_VERSION_2",COUNTRY_LEVEL_CODE)
        self.assertIn("MULTIPLE_ONSET_VERSION_3",MULTIPLE_CODE)
        a,late,acf,newacf=panels()
        with self.assertRaisesRegex(ValueError,"Only one-/two"):
            origin_risk_status("10",2025,2022,acf)
        del a["1"][2022]
        with self.assertRaisesRegex(ValueError,"Origin country population"):
            audit_year(a,late,acf,newacf,2022,2023)

if __name__=="__main__":
    unittest.main()
