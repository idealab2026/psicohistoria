import unittest

from experiment_multiple_newconf import (
    evaluate,fold,_history,load_multiple,summarize,CANDIDATES,
    EXTERNAL_ORIGIN,ROLLING_ORIGINS,HORIZONS
)

def fixture():
    prior={}
    later={}
    for i in range(1,197):
        cid=str(i)
        prior[cid]={}
        later[cid]={}
        for year in range(1946,2025):
            value=int(i%19==0 and year%5==0)
            v={"newconf":value,"onset2":int(i%37==0 and year%11==0),
               "newconf_episodes":value,"onset2_episodes":0,
               "multiple_episode_rows":1}
            if year<=2022:prior[cid][year]=v.copy()
            later[cid][year]=v.copy()
    for cid in later:
        later[cid][2023]["newconf"]=0
        later[cid][2024]["newconf"]=0
        later[cid][2023]["newconf_episodes"]=0
        later[cid][2024]["newconf_episodes"]=0
    for cid in ("3","5"):
        later[cid][2023]["newconf"]=1
        later[cid][2023]["newconf_episodes"]=1
    later["8"][2024]["newconf"]=1
    later["8"][2024]["newconf_episodes"]=1
    # The observed alternative target onset2 intentionally DOES NOT equal newconf.
    old_active={(str(i),year) for i in range(1,197)
                for year in range(1946,2023)
                if i%7==0 or i%13==0 and year%2==0}
    return prior,later,old_active

class MultipleNewConflictTests(unittest.TestCase):
    def test_source_vintage_schema_binds_to_official_hash(self):
        with self.assertRaisesRegex(ValueError,"SHA-256 changed"):
            load_multiple("23.1",lambda url,lim:b"tampered")
        with self.assertRaisesRegex(ValueError,"Unapproved"):
            load_multiple("19.1")

    def test_source_sep_and_all_candidate_models_are_reported(self):
        old,later,active=fixture()
        study=evaluate(old,later,active)
        self.assertEqual(study["external"]["forecast_evaluations"],392)
        self.assertEqual(study["external"]["positive_forecast_evaluations"],3)
        self.assertEqual(len(study["external"]["folds"]),2)
        self.assertEqual([x["positive_country_years"] for x in study["external"]["folds"]],[2,1])
        self.assertEqual(study["internal"]["forecast_evaluations"],2744)
        self.assertEqual(study["internal"]["unique_country_years"],1568)
        self.assertEqual(study["internal"]["overlapping_forecasts"],1176)
        self.assertEqual(set(study["external"]["scores"]),set(CANDIDATES))
        self.assertEqual(study["active_countries_eligible_for_newconf"],True)
        self.assertFalse(study["predictive_skill_demonstrated"])
        self.assertFalse(study["original_2027_prospective_country_risk_probabilities_changed"])
        self.assertEqual(study["2027_outcomes_evaluated"],0)
        self.assertTrue(study["hypothesis_defined_after_external_outcomes_seen"])

    def test_future_labels_only_change_outcomes_not_predictions(self):
        old,later,activity=fixture()
        before,folds=fold(old,later,activity,2022,2)
        later["21"][2023]["newconf"]=1
        later["21"][2024]["newconf"]=1
        later["21"][2024]["newconf_episodes"]=1
        after,newfold=fold(old,later,activity,2022,2)
        self.assertEqual(
            [{k:v for k,v in row.items() if k not in
              ("outcome","onset2_other_target","episode_events")} for row in before],
            [{k:v for k,v in row.items() if k not in
              ("outcome","onset2_other_target","episode_events")} for row in after]
        )
        self.assertEqual(folds["fit"]["latest_training_year"],2022)
        self.assertFalse(folds["fit"]["later_release_labels_used_in_fit"])
        self.assertFalse(folds["fit"]["later_release_activity_used"])
        self.assertEqual(newfold["positive_country_years"],2)

    def test_year_2023_is_unknown_for_horizon2_even_if_seen_in_truth(self):
        old,later,active=fixture()
        f0,m0=fold(old,later,active,2022,2)
        for country in later:
            later[country][2023]["newconf"]=1
        f1,m1=fold(old,later,active,2022,2)
        self.assertEqual(f0,f1)
        self.assertEqual(m0["scores"],m1["scores"])

    def test_aggregate_ongoing_activity_does_not_disqualify_newconf(self):
        old,later,activity=fixture()
        cohort=set(old)
        basic,info=_history(old,activity,2022,1,cohort)
        cid=next(c for c in sorted(cohort) if (c,2022) not in activity)
        active=activity|{(cid,2022)}
        other,info2=_history(old,active,2022,1,cohort)
        self.assertEqual(basic[cid]["country_eb"],other[cid]["country_eb"])
        self.assertNotEqual(basic[cid]["activity_global"],other[cid]["activity_global"])
        self.assertTrue(other[cid]["activity_country"]>0)

    def test_missing_countries_not_silently_zero(self):
        old,later,activity=fixture()
        del later["5"][2024]
        rows,info=fold(old,later,activity,2022,2)
        self.assertEqual(len(rows),195)
        self.assertEqual(info["positive_country_years"],1)
        for cid in list(later)[:9]:
            later[cid].pop(2024,None)
        with self.assertRaisesRegex(ValueError,"Missing target countries"):
            fold(old,later,activity,2022,2)

if __name__=="__main__":
    unittest.main()
