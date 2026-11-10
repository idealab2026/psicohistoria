import unittest
from evaluate_homogeneous_onset2 import (
  ORIGIN_VERSION,TARGET_VERSION,CUTOFF,TEST_YEARS,predict,score,ranking,
  bootstrap,run,load_homogeneous_sources
)

def synthetic():
    older={}
    newer={}
    for country in range(200,396):
        name=str(country)
        for y in range(1946,2025):
            target=int(country%29==0 and y%3 in (0,1,2))
            newer[(y,name)]=target
            if y<=2022:older[(y,name)]=target
    return {"23.1":older,"25.1":newer}

class HomogeneousOnset2Tests(unittest.TestCase):
    def test_two_years_with_disjoint_origin_and_outcome_sources(self):
        d=synthetic()
        r=run(d)
        self.assertEqual(r["n"],392)
        self.assertEqual([x["year"] for x in r["years"]],[2023,2024])
        self.assertEqual(r["training"]["source_last_year"],2022)
        self.assertEqual(r["training"]["training_country_years"],23*196)
        self.assertEqual(r["training"]["recent_country_years"],5*196)
        self.assertEqual(r["training"]["origin_country_universe"],196)
        self.assertFalse(r["training"]["future_outcome_labels_used_in_fit"])
        self.assertFalse(r["legacy_19_1_included"])
        self.assertFalse(r["historical_forecasts_issued"])
        self.assertFalse(r["skill_demonstrated_prospectively"])
        self.assertEqual(r["actual_2027_results"],0)
        self.assertIn("onset2",r["question"])
        self.assertIn("19.1 edition is deliberately excluded",r["caution"])

    def test_future_labels_change_only_scores_not_origins_predictions(self):
        d=synthetic()
        before,_,info=predict(d["23.1"],d["25.1"])
        d["25.1"][(2024,"200")]=1
        after,_,next_info=predict(d["23.1"],d["25.1"])
        for a,b in zip(before,after):
            self.assertEqual((a["country"],a["target_year"],a["model"],a["global"],a["recent_global"]),
                             (b["country"],b["target_year"],b["model"],b["global"],b["recent_global"]))
        self.assertNotEqual(score(before,"model")["brier"],score(after,"model")["brier"])
        self.assertEqual(info,next_info)

    def test_training_source_with_future_year_rejected(self):
        d=synthetic()
        d["23.1"][(2023,"200")]=1
        with self.assertRaisesRegex(ValueError,"unexpected last year"):
            predict(d["23.1"],d["25.1"])
        d=synthetic()
        del d["23.1"][(2022,"200")]
        with self.assertRaisesRegex(ValueError,"country universe changed"):
            predict(d["23.1"],d["25.1"])

    def test_no_event_logloss_not_defined_for_positive_samples(self):
        d=synthetic()
        rows,_,_=predict(d["23.1"],d["25.1"])
        self.assertIsNone(score(rows,"no_onset")["logloss"])
        self.assertTrue(0<score(rows,"model")["brier"]<1)
        self.assertTrue(0<score(rows,"global")["logloss"]<5)
        result=ranking([r for r in rows if r["target_year"]==2024])
        self.assertEqual(result["n"],196)
        self.assertEqual(set(result["top_k_country_model"]),{"5","10","20"})
        self.assertTrue(0<=result["auc_country_model"]<=1)
        self.assertTrue(0<=result["average_precision_country_model"]<=1)

    def test_source_hashes_prevent_tampering(self):
        with self.assertRaisesRegex(ValueError,"source digest mismatch"):
            load_homogeneous_sources(lambda url,max_bytes:b"fabricated")

    def test_country_bootstrap_deterministic(self):
        d=synthetic()
        rows,_,_=predict(d["23.1"],d["25.1"])
        self.assertEqual(bootstrap(rows,"global",reps=100,seed=9),
                         bootstrap(rows,"global",reps=100,seed=9))
        self.assertEqual(len(bootstrap(rows,"recent_global",reps=100,seed=9)),2)

    def test_incomplete_outcome_year_is_not_assumed_negative(self):
        d=synthetic()
        del d["25.1"][(2024,"200")]
        rows,folds,_=predict(d["23.1"],d["25.1"])
        self.assertEqual(len(rows),391)
        self.assertEqual(folds[-1]["unresolved"],1)
        self.assertNotIn("200", {r["country"] for r in rows if r["target_year"]==2024})
        for country in range(200,210):
            d["25.1"].pop((2024,str(country)),None)
        with self.assertRaisesRegex(ValueError,"Unresolved origin population"):
            predict(d["23.1"],d["25.1"])

if __name__=="__main__":
    unittest.main()
