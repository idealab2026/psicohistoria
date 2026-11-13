"""Exhaustive synthetic pairwise influence contracts; no network required."""
import copy
import math
import unittest

import diagnose_acd_retention_country_influence as country


def row(cid,year,y,p_global,p_lag,p_eb):
    return {
        "country_id":cid,"target_year":year,"observed_acd":y,
        "models":{"p_global_recent5":p_global,"p_lag1_group":p_lag,
                  "p_country_eb":p_eb},
    }


class FixedCountryInfluenceTests(unittest.TestCase):
    def setUp(self):
        # Deliberately has repeated country 10 and fixed, mutually opposed
        # country-year effects. No retraining; deletion across both years.
        self.rows=[
            row(10,2021,1,.8,.2,.7),  # lag1-global +.60
            row(11,2021,1,.8,.7,.6),  # lag1-global +.05
            row(10,2022,0,.8,.2,.7),  # lag1-global -.60
            row(12,2022,0,.8,.3,.6),  # lag1-global -.55
        ]

    def test_paired_brier_algebra(self):
        self.assertAlmostEqual(country.difference(.2,.8,1),.60)
        self.assertAlmostEqual(country.difference(.2,.8,0),-.60)
        self.assertAlmostEqual(country.difference(.3,.8,0),-.55)
        for args in ((0,.5,0), (1,.5,1), (.5,.5,True), (.5,.5,.5),
                     (.5,math.inf,0), (math.nan,.5,1)):
            with self.assertRaises(ValueError):
                country.difference(*args)

    def test_deletion_uses_all_repeated_country_years_without_refit(self):
        report=country.analyze_ledger(self.rows)
        self.assertEqual(report["unique_country_clusters"],3)
        self.assertEqual(report["total_country_year_fold_scores"],4)
        self.assertEqual(report["country_cluster_appearances_histogram"],{1:2,2:1})
        self.assertEqual(report["repeated_country_clusters"],1)
        lag=report["per_model"]["p_lag1_group"]
        self.assertAlmostEqual(lag["pooled_delta_brier_candidate_minus_global"],-.125)
        records={r["country_id"]:r for r in lag["all_leave_one_country_out"]}
        self.assertEqual(records[10]["target_years"],[2021,2022])
        self.assertEqual(records[10]["n_original_fold_appearances"],2)
        self.assertAlmostEqual(records[10]["sum_original_paired_loss_contribution"],0)
        self.assertAlmostEqual(records[10]["leave_one_country_out_delta_brier"],-.25)
        self.assertAlmostEqual(records[12]["leave_one_country_out_delta_brier"],.05/3)
        self.assertTrue(records[12]["reverses_pooled_sign"])
        self.assertEqual(lag["sign_reversals"],[12])
        self.assertEqual(lag["n_sign_reversals"],1)
        self.assertTrue(report["fixed_predictions_no_refit"])

    def test_country_deletion_equals_exact_recomputed_remaining_mean(self):
        report=country.analyze_ledger(self.rows)
        for name in country.MODELS:
            for record in report["per_model"][name]["all_leave_one_country_out"]:
                remaining=[r for r in self.rows
                           if r["country_id"]!=record["country_id"]]
                expected=sum(country.difference(
                    r["models"][name],r["models"][country.PRIMARY_BASELINE],
                    r["observed_acd"]) for r in remaining)/len(remaining)
                self.assertAlmostEqual(record["leave_one_country_out_delta_brier"],
                                       expected,places=14)

    def test_rejects_duplicate_or_missing_or_invalid_historical_rows(self):
        bad=copy.deepcopy(self.rows)
        bad.append(copy.deepcopy(bad[0]))
        with self.assertRaisesRegex(ValueError,"Repeated"):
            country.analyze_ledger(bad)
        bad=copy.deepcopy(self.rows)
        bad[0]["models"].pop("p_country_eb")
        with self.assertRaisesRegex(ValueError,"three ACD"):
            country.analyze_ledger(bad)
        bad=copy.deepcopy(self.rows)
        bad[1]["observed_acd"]=None
        with self.assertRaisesRegex(ValueError,"Invalid historical"):
            country.analyze_ledger(bad)
        bad=copy.deepcopy(self.rows)
        bad[1]["target_year"]=True
        with self.assertRaisesRegex(ValueError,"Invalid historical"):
            country.analyze_ledger(bad)
        with self.assertRaisesRegex(ValueError,"Empty"):
            country.analyze_ledger([])
        with self.assertRaisesRegex(ValueError,"No independent country"):
            country.analyze_ledger([self.rows[0]])

    def test_country_relabel_does_not_retrain(self):
        # The metric depends only on outcomes and frozen probabilities;
        # the country codes only determine cluster membership.
        stats=country.analyze_ledger(self.rows)
        other=copy.deepcopy(self.rows)
        for r in other:
            r["country_id"]+=1000
        changed=country.analyze_ledger(other)
        for model in country.MODELS:
            self.assertEqual(stats["per_model"][model][
                "pooled_delta_brier_candidate_minus_global"],
                changed["per_model"][model][
                    "pooled_delta_brier_candidate_minus_global"])


if __name__=="__main__":
    unittest.main()
