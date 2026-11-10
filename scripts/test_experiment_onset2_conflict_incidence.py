import unittest
from experiment_onset2_conflict_incidence import (
  CANDIDATES,_group_prior,evaluate_origin,run,load_activity
)

def onset_panel(last):
    out={}
    for n in range(200,396):
        key=str(n)
        values={}
        for year in range(1946,last+1):
            # Future two onset2 events; older observations are not supplied
            # by assessment 25.1 when fitting source 23.1.
            onset2=int(year in (2023,2024) and n==200)
            onset1=int(onset2==1 or n%17==0 and year%7==0)
            values[year]=(onset1,onset2)
        out[key]=values
    return out

def conflict_activity(last):
    # Two distinct annual state-based conflict persistence signatures.
    result=set()
    for year in range(1946,last+1):
        for n in range(200,396):
            if n%12==0 and year%7!=1 or n%31==0 and year%5==0:
                result.add((str(n),year))
    # Force latest-year coverage for the fixed 2022/2024 official vintages.
    result.add(("216",last))
    return result

class Onset2ConflictIncidenceTests(unittest.TestCase):
    def test_future_activity_and_outcomes_do_not_enter_2022_forecast(self):
        old=onset_panel(2022)
        newer=onset_panel(2024)
        active=conflict_activity(2022)
        first,folds=evaluate_origin(old,newer,active,2022)
        del newer["201"][2024]
        newer["200"][2023]=(1,0)
        later,folds_later=evaluate_origin(old,newer,active,2022)
        # Compare predictions by (country,target) on outcomes that still exist.
        baseline={(r["country"],r["target"]):r for r in first}
        for r in later:
            original=baseline[r["country"],r["target"]]
            for model in CANDIDATES:
                self.assertEqual(original[model],r[model])
        self.assertEqual(folds_later[1]["n"],195)
        self.assertEqual(folds_later[1]["fit"]["latest_feature_year"],2022)
        self.assertFalse(folds_later[1]["fit"]["future_incidence_used"])

    def test_incidence_group_feature_respects_only_origin_past(self):
        old=onset_panel(2022)
        current=conflict_activity(2022)
        one,_=_group_prior(old,current,2015,2,sorted(old))
        # New later observations must not change 2015 prediction.
        revised=current | {("205",2018),("205",2020)}
        two,_=_group_prior(old,revised,2015,2,sorted(old))
        self.assertEqual(one,two)
        # But origin contemporaneous incidence should affect the incidence prior.
        # Use a country that has not been active at the cutoff.
        cid=next(c for c in sorted(old) if (c,2015) not in current)
        new=current | {(cid,2015)}
        three,_=_group_prior(old,new,2015,2,sorted(old))
        self.assertEqual(one[cid]["country_eb"],three[cid]["country_eb"])
        self.assertNotEqual(one[cid]["active_global"],three[cid]["active_global"])

    def test_internal_repeated_targets_not_2774_independent_countries(self):
        old=onset_panel(2022)
        future=onset_panel(2024)
        act=conflict_activity(2022)
        new_act=conflict_activity(2024)
        report=run(old,future,act,new_act)
        internal=report["internal"]
        external=report["external"]
        self.assertEqual(internal["n_forecast_evaluations"],2744)
        self.assertEqual(internal["unique_country_year_targets"],1568)
        self.assertEqual(internal["repeated_target_evaluations"],1176)
        self.assertEqual(internal["unique_onset2_positive_targets"],0)
        self.assertEqual(external["n_forecast_evaluations"],392)
        self.assertEqual(external["positive_forecast_evaluations"],2)
        self.assertEqual(set(external["scores"]),set(CANDIDATES))
        self.assertFalse(report["certified_predictive_skill"])
        self.assertFalse(report["real_2027_country_forecast_modified"])
        self.assertEqual(report["actual_2027_outcomes_resolved"],0)
        self.assertTrue(report["model_grid_chosen_after_prior_2023_2024_outcomes_inspected"])
        self.assertFalse(report["original_editions_independently_time_notarized"])

    def test_future_vintage_incidence_revisions_are_descriptive_only(self):
        old=onset_panel(2022)
        future=onset_panel(2024)
        act=conflict_activity(2022)
        newer=conflict_activity(2024)
        original=run(old,future,act,newer)
        newer.add(("201",2022))
        changed=run(old,future,act,newer)
        self.assertEqual(original["external"]["scores"],changed["external"]["scores"])
        self.assertEqual(original["internal"]["scores"],changed["internal"]["scores"])
        self.assertEqual(
            changed["historical_conflict_incidence_revision_diagnostic"]["added_in_later_vintage_through_2022"],
            original["historical_conflict_incidence_revision_diagnostic"]["added_in_later_vintage_through_2022"]+1
        )

    def test_tampered_official_zip_or_unapproved_source_rejected(self):
        with self.assertRaisesRegex(ValueError,"hash changed"):
            load_activity("23.1",fetcher=lambda url,limit:b"untrusted zip")
        with self.assertRaisesRegex(ValueError,"Unapproved"):
            load_activity("19.1")
        old=onset_panel(2022)
        with self.assertRaisesRegex(ValueError,"Only vintage 23.1"):
            _group_prior(old,conflict_activity(2021),2015,1,sorted(old))

if __name__=="__main__":
    unittest.main()
