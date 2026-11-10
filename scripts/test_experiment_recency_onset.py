import unittest
from experiment_recency_onset import (
 CANDIDATE_WINDOWS,TRAIN_START,SHRINKAGE,INTERNAL_TEST_YEARS,
 frozen_probabilities,year_predictions,scores,evaluate,verified_sources,
)

class RecencyOnsetTests(unittest.TestCase):
    def sample(self,end=2024):
        return {(year,str(code)):int(code%40==0 and year in
                 (2004,2008,2015,2017,2021,2024))
                 for year in range(2000,end+1) for code in range(200,360)}

    def test_all_windows_are_fit_before_target_including_early_truncated_periods(self):
        data=self.sample()
        cohort={str(code) for code in range(200,360)}
        predicted,meta=frozen_probabilities(data,2013,cohort)
        self.assertEqual(meta["source_last_year_used"],2013)
        self.assertEqual(set(meta["recent_global_rates"]),{"5","10","20"})
        self.assertEqual(len(predicted),160)
        self.assertEqual(len(set(predicted["200"])),8)
        self.assertEqual(meta["training_n"],14*160)
        # The 20-year window in 2013 has only 2000-2013 available.
        self.assertAlmostEqual(meta["recent_global_rates"]["20"],meta["full_global"])

    def test_target_labels_cannot_modify_probabilities(self):
        train=self.sample(2022)
        later=self.sample()
        a,_=year_predictions(train,later,2022,2024)
        later[(2024,"201")]=1
        b,_=year_predictions(train,later,2022,2024)
        keys=("global_full","global_5","global_10","global_20",
              "country_full","country_5","country_10","country_20")
        self.assertEqual([[v[key] for key in keys] for v in a],
                         [[v[key] for key in keys] for v in b])
        self.assertNotEqual(scores(a)["global_5"]["brier"],scores(b)["global_5"]["brier"])

    def test_source_data_from_2023_is_not_used_in_2024_training(self):
        src=self.sample()
        before,_=year_predictions(src,src,2022,2024)
        src[(2023,"200")]=1
        src[(2024,"200")]=0
        after,_=year_predictions(src,src,2022,2024)
        self.assertEqual([p["country_5"] for p in before],
                         [p["country_5"] for p in after])

    def test_complete_exploratory_grid_and_no_confirmatory_claim(self):
        v={"23.1":self.sample(2022),"25.1":self.sample(2024)}
        result=evaluate(v)
        self.assertEqual(result["source_vintages"],["23.1","25.1"])
        self.assertTrue(result["legacy_19_1_excluded_due_to_country_year_unit_mismatch"])
        self.assertEqual(result["internally_revised_vintage"]["n"],8*160)
        self.assertEqual(result["cross_release_holdout_2024"]["n"],160)
        self.assertEqual(result["cross_release_holdout_2024"]["events"],4)
        self.assertFalse(result["new_independent_confirmatory_holdout"])
        self.assertEqual(result["prospective_forecasts_issued"],0)
        self.assertFalse(result["skill_demonstrated"])
        self.assertEqual(set(result["cross_release_holdout_2024"]["metrics"]),
            {"global_full","global_5","global_10","global_20",
             "country_full","country_5","country_10","country_20","no_event"})
        self.assertTrue(all(
            abs(result["cross_release_holdout_2024"]["metrics"][k]["brier"])<1
            for k in ("global_full","global_5","global_10","global_20")
        ))

    def test_rejects_future_target_and_incomplete_cohorts(self):
        sample=self.sample()
        with self.assertRaisesRegex(ValueError,"not within declared"):
            year_predictions(sample,sample,2022,2025)
        with self.assertRaisesRegex(ValueError,"fixed grid"):
            frozen_probabilities(sample,2022,{str(i) for i in range(200,360)},(1,2))
        incomplete={key:y for key,y in sample.items()
                    if not (key[0]==2024 and int(key[1])>345)}
        with self.assertRaisesRegex(ValueError,"Insufficient target-country"):
            year_predictions(sample,incomplete,2022,2024)

    def test_hash_pins_disallow_modified_official_data(self):
        with self.assertRaisesRegex(ValueError,"hash mismatch"):
            verified_sources(lambda url,limit:b"tampered")

if __name__=="__main__":unittest.main()
