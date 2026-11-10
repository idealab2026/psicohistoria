import unittest
from experiment_onset2_lagged_signals import (
    load_panel,_fit,evaluate_at_origin,evaluate,score_rows,
    START,TRAIN_CUTOFFS,EXTERNAL_CUTOFF,HORIZONS,MODELS
)

def panel(last_year):
    d={}
    for country in range(200,396):
        name=str(country)
        historical={}
        for year in range(1946,last_year+1):
            onset1=int(country%13==0 and year%7==0 or
                       country%19==0 and year%11==0)
            onset2=int(country%19==0 and year%11==0)
            historical[year]=(onset1,onset2)
        d[name]=historical
    return d

class Onset2LaggedSignalTest(unittest.TestCase):
    def test_horizon_specific_models_evaluate_rolling_origins_and_external(self):
        base=panel(2022)
        later=panel(2024)
        s=evaluate({"23.1":base,"25.1":later})
        self.assertEqual(s["external"]["n"],392)
        self.assertEqual(len(s["external"]["folds"]),2)
        self.assertEqual(len(s["internal"]["folds"]),14)
        self.assertEqual(s["internal"]["n"],len(TRAIN_CUTOFFS)*2*196)
        self.assertEqual(s["internal"]["unique_country_target_years"],8*196)
        self.assertEqual(s["internal"]["repeated_target_evaluations"],6*196)
        self.assertEqual(s["internal"]["unique_positive_country_target_years"],0)  # synthetic timeline has no 2015-22 events
        self.assertEqual(s["internal"]["by_horizon"]["1"]["n"],7*196)
        self.assertEqual(s["internal"]["by_horizon"]["2"]["n"],7*196)
        self.assertEqual(s["internal"]["by_horizon"]["1"]["events"],sum(f["positive_onset2"] for f in s["internal"]["folds"] if f["horizon"]==1))
        self.assertEqual(s["internal"]["by_horizon"]["2"]["events"],sum(f["positive_onset2"] for f in s["internal"]["folds"] if f["horizon"]==2))
        self.assertEqual(s["sample_definitions"]["horizons"],[1,2])
        self.assertEqual(s["sample_definitions"]["rolling_origins"],list(TRAIN_CUTOFFS))
        self.assertEqual(set(s["internal"]["scores"]),set(MODELS))
        self.assertEqual(set(s["external"]["scores"]),set(MODELS))
        self.assertFalse(s["predictive_skill_demonstrated"])
        self.assertFalse(s["historical_predictions_were_issued"])
        self.assertFalse(s["model_selected_or_retrained_on_outcomes"])
        self.assertTrue(s["hypotheses_were_designated_after_previous_holdout_inspection"])
        self.assertFalse(s["prospective_2027_issued_forecast_changed"])
        self.assertEqual(s["actual_2027_results_resolved"],0)
        self.assertFalse(s["country_risks_published"])
        self.assertIn("not the full underlying active-conflict risk-set",s["caution"])
        self.assertIn("not independent cases",s["caution"])

    def test_target_2024_does_not_use_2023_feature_or_label(self):
        original=panel(2022)
        truth=panel(2024)
        before,folds=evaluate_at_origin(original,truth,EXTERNAL_CUTOFF)
        for cid,hist in truth.items():
            hist[2023]=(1,1)
        after,updated=evaluate_at_origin(original,truth,EXTERNAL_CUTOFF)
        b=[r for r in before if r["year"]==2024]
        a=[r for r in after if r["year"]==2024]
        self.assertEqual(b,a)
        self.assertEqual(folds[1]["scores"],updated[1]["scores"])
        self.assertNotEqual(folds[0]["positive_onset2"],updated[0]["positive_onset2"])
        self.assertTrue(folds[1]["fit"]["horizon_2_feature_not_from_intermediate_year"])
        self.assertEqual(folds[1]["fit"]["max_fitted_outcome_year"],2022)

    def test_origin_features_stay_constant_when_outcome_revised(self):
        original=panel(2022)
        target=panel(2024)
        first,detail=evaluate_at_origin(original,target,2022)
        target["200"][2024]=(1,1)
        second,detail2=evaluate_at_origin(original,target,2022)
        self.assertEqual(
            [{k:v for k,v in row.items() if k!="outcome"} for row in first],
            [{k:v for k,v in row.items() if k!="outcome"} for row in second],
        )
        self.assertNotEqual(score_rows(first),score_rows(second))

    def test_wrong_year_schema_or_source_hash_fails(self):
        b=panel(2022);later=panel(2024)
        with self.assertRaisesRegex(ValueError,"Source edition cutoff"):
            evaluate({"23.1":panel(2023),"25.1":later})
        with self.assertRaisesRegex(ValueError,"Unapproved UCDP"):
            load_panel("19.1")
        with self.assertRaisesRegex(ValueError,"changed"):
            load_panel("23.1",fetcher=lambda url,limit:b"tampered")

    def test_own_lag_one_changes_country_conditional_prior_only_with_origin_flag(self):
        b=panel(2022)
        cid="219"
        first,meta=_fit(b,2022,2,sorted(b))
        b[cid][2022]=(1-int(b[cid][2022][0]),b[cid][2022][1])
        # At 2022 the group-specific horizon conditional model must use
        # onset1 from 2022 and not any later year.
        second,meta2=_fit(b,2022,2,sorted(b))
        self.assertNotEqual(first[cid]["lag1_global"],second[cid]["lag1_global"])
        self.assertEqual(first[cid]["global_h"],second[cid]["global_h"])
        self.assertEqual(first[cid]["country_eb"],second[cid]["country_eb"])

    def test_unresolved_target_year_is_not_scored_as_no_onset(self):
        original=panel(2022);target=panel(2024)
        del target["201"][2024]
        rows,folds=evaluate_at_origin(original,target,2022)
        self.assertEqual(len(rows),391)
        self.assertEqual(folds[-1]["unresolved"],1)
        self.assertFalse(any(r["country"]=="201" and r["year"]==2024 for r in rows))
        for code in list(target)[:10]:
            del target[code][2023]
        with self.assertRaisesRegex(ValueError,"unresolved"):
            evaluate_at_origin(original,target,2022)

if __name__=="__main__":
    unittest.main()
