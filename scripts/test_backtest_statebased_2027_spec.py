import unittest
from backtest_statebased_2027_spec import (
 TARGET_YEARS,HORIZON,MIN_FOLD,BINS,_annual_frame,_metrics,_reliability,
 _pairwise_uncertainty,evaluate,from_zip
)

def example():
    # 196 synthetic countries, 1989–2025, two state classes and persistence.
    data={}
    for country in range(1,197):
        h={}
        for year in range(1989,2026):
            if country%4==0:
                v=int(year%9 in (0,1,2,3,4))
            elif country%7==0:
                v=int(year%13==0)
            else:
                v=0
            h[year]=v
        data[country]=h
    return data

class Historical2027SpecificationTests(unittest.TestCase):
    def test_fixed_two_year_origins_and_all_comparators(self):
        result=evaluate(example())
        self.assertEqual(result["target_years"],list(range(2012,2026)))
        self.assertEqual(result["country_years"],196*14)
        self.assertEqual(result["unique_countries"],196)
        self.assertEqual(len(result["cohorts_by_year"]),14)
        self.assertTrue(all(y["origin_cutoff"]==y["target_year"]-2
                            for y in result["cohorts_by_year"]))
        self.assertEqual(set(result["pooled_scores"]),{
            "p_model","p_global_markov","p_baseline_global_5y"})
        self.assertEqual(result["prospective_2027_outcomes_resolved"],0)
        self.assertFalse(result["prospective_skill_demonstrated"])
        self.assertEqual(result["analysis_type"],
            "RETROSPECTIVE_REVISED_26_1_NOT_ASOF_OR_PROSPECTIVE")
        self.assertEqual(sum(v["n"] for v in result["reliability"]["model"]),196*14)
        self.assertEqual(len(result["leave_one_target_year_out_deltas"]["p_global_markov"]),14)

    def test_future_target_label_does_not_change_origin_year_forecasts(self):
        h=example()
        before,_=_annual_frame(h,2023)
        h[4][2025]=1-h[4][2025]
        after,_=_annual_frame(h,2023)
        keys=("country_id","p_model","p_global_markov","p_baseline_global_5y")
        self.assertEqual([tuple(r[x] for x in keys) for r in before],
                         [tuple(r[x] for x in keys) for r in after])
        self.assertNotEqual(_metrics(before)["_UNDEFINED_"] if False else
                            _metrics(before)["p_model"]["brier"],
                            _metrics(after)["p_model"]["brier"])

    def test_missing_future_country_label_is_unresolved_not_negative(self):
        h=example()
        before,meta=_annual_frame(h,2023)
        self.assertEqual(meta["unresolved"],0)
        del h[2][2025]
        after,meta=_annual_frame(h,2023)
        self.assertEqual(len(after),195)
        self.assertEqual(meta["origin_cohort"],196)
        self.assertEqual(meta["unresolved"],1)
        self.assertNotIn(2,{r["country_id"] for r in after})

    def test_conflicting_or_inadequate_training_fails_closed(self):
        h=example()
        with self.assertRaisesRegex(ValueError,"fixed historical"):
            _annual_frame(h,2007)
        with self.assertRaisesRegex(ValueError,"fixed historical"):
            _annual_frame(h,2024)
        h[1][2026]=1
        with self.assertRaisesRegex(ValueError,"Invalid official binary"):
            _annual_frame(h,2023)
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            from_zip(b"altered")

    def test_calibration_groups_account_for_every_observation(self):
        rows=[
            {"country_id":1,"outcome":0,"p_model":.025,"p_global_markov":.05,"p_baseline_global_5y":.2},
            {"country_id":2,"outcome":1,"p_model":.999,"p_global_markov":.7,"p_baseline_global_5y":.2},
            {"country_id":3,"outcome":1,"p_model":.35,"p_global_markov":.4,"p_baseline_global_5y":.2},
        ]
        bins=_reliability(rows,"p_model")
        self.assertEqual(len(bins),len(BINS)-1)
        self.assertEqual(sum(v["n"] for v in bins),len(rows))
        self.assertEqual(_metrics(rows)["p_model"]["brier"],
                         ((.025)**2+(.001)**2+(.65)**2)/3)
        self.assertEqual(_pairwise_uncertainty(rows,"p_global_markov",100,5),
                         _pairwise_uncertainty(rows,"p_global_markov",100,5))

if __name__=="__main__":
    unittest.main()
