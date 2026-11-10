import unittest

from test_backtest_archived_country_vintages import versions,metadata
from diagnose_2027_origin_state import rows_from_vintages
from evaluate_2027_new_entries import (
    frozen_two_year_entry_prior,average_precision,roc_auc,top_alerts,
    _format_fold,evaluate,FOLDS
)

class NewEntryComparatorTests(unittest.TestCase):
    def test_entry_prior_uses_only_two_year_pairs_known_at_origin(self):
        files=versions()
        base=frozen_two_year_entry_prior(files["23.1"],2022)
        self.assertEqual(base["eligible_countries_at_origin"],196)
        self.assertEqual(base["historical_last_eligible_origin_year"],2020)
        self.assertGreater(base["historical_inactive_exposures"],100)
        self.assertLess(base["historical_two_year_entries"],base["historical_inactive_exposures"])
        self.assertFalse(base["future_outcomes_used"])
        self.assertTrue(0<base["probability"]<1)
        changed=versions()
        changed["25.1"][1][2024]=1-changed["25.1"][1][2024]
        self.assertEqual(base,frozen_two_year_entry_prior(changed["23.1"],2022))
        changed["23.1"][1][2023]=1
        with self.assertRaisesRegex(ValueError,"beyond edition cutoff"):
            frozen_two_year_entry_prior(changed["23.1"],2022)

    def test_entry_prior_is_not_derived_from_future_evaluation_survivors(self):
        files=versions()
        base=frozen_two_year_entry_prior(files["24.1"],2023)
        del files["26.1"][1][2025]
        self.assertEqual(base,frozen_two_year_entry_prior(files["24.1"],2023))
        self.assertEqual(base["historical_last_eligible_origin_year"],2021)

    def test_tied_probabilities_have_tie_aware_precision(self):
        rows=[
          {"country_id":1,"outcome":1,"p_model":.5},
          {"country_id":2,"outcome":0,"p_model":.5},
          {"country_id":3,"outcome":1,"p_model":.2},
          {"country_id":4,"outcome":0,"p_model":.1},
        ]
        self.assertAlmostEqual(average_precision(rows,"p_model"),.5*.5+.5*(2/3))
        self.assertAlmostEqual(roc_auc(rows,"p_model"),.625)
        self.assertIsNone(average_precision([
           {"outcome":0,"p_model":.1}],"p_model"))
        self.assertIsNone(roc_auc([
           {"outcome":1,"p_model":.1}],"p_model"))
        self.assertAlmostEqual(roc_auc([
           {"outcome":1,"p_model":.1},
           {"outcome":0,"p_model":.1}],"p_model"),.5)

    def test_conditional_ranking_excludes_already_active_countries(self):
        synthetic=[
          {"country_id":cid,"outcome":int(cid in (1,6,11)),
           "p_model":1-cid/100}
          for cid in range(1,151)
        ]
        top=top_alerts(synthetic)
        self.assertEqual(top["5"]["hits"],1)
        self.assertEqual(top["10"]["hits"],2)
        self.assertEqual(top["20"]["hits"],3)
        self.assertAlmostEqual(top["10"]["random_expected_hits"],10*3/150)
        self.assertTrue(all(x["budget"] in (5,10,20) for x in top.values()))
        self.assertEqual(top_alerts(synthetic),top)

    def test_each_origin_has_predefined_conditional_reference(self):
        src=versions()
        for version,target in (("25.1",2024),("26.1",2025)):
            for cid in src[version]:
                src[version][cid][target]=int(cid in (1,2,3,4))
        batches=rows_from_vintages(src)
        self.assertEqual(len(batches),2)
        for fold,rows,details in batches:
            prior=frozen_two_year_entry_prior(src[fold["origin_release"]],fold["origin_year"])
            selected,summary=_format_fold(fold,rows,prior)
            self.assertEqual(summary["n"],len(selected))
            self.assertEqual(set(summary["scores"]),{
                "p_model","p_global_markov","p_entry_prior_2y"})
            self.assertEqual(set(summary["alert_budgets"]),{"5","10","20"})
            self.assertTrue(all(v["p_entry_prior_2y"]==prior["probability"] for v in selected))
            self.assertTrue(all(v["origin_active"]==0 for v in selected))
            self.assertEqual(summary["entry_training"]["historical_last_eligible_origin_year"],
                             fold["origin_year"]-2)
            self.assertEqual(summary["average_precision"]["entry_prior"],
                             summary["observed_entry_rate"])
            self.assertEqual(summary["roc_auc"]["entry_prior"],.5)

    def test_synthetic_data_cannot_masquerade_as_pinned_321_country_panel(self):
        with self.assertRaisesRegex(ValueError,"Published 2024/25 threshold-entry cohort changed"):
            evaluate(versions(),metadata())

if __name__=="__main__":
    unittest.main()
