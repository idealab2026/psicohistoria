"""Adversarial temporal + country-block tests for LOG1P calibration transfer."""
from __future__ import annotations

import copy
import json
import unittest

from audit_geo2027_log1p_shadow_issue import (
    ISSUE, ORIGINAL, MANIFEST, audit as audit_issue,
)
from audit_geo2027_log1p_issued_death_stress import ALERTS
from test_experiment_geo2027_intensity_markov_cross_release import sample
from experiment_geo2027_log1p_rolling_year_vintage import (
    historical_ledger, fit_target, year_scores,
)
from experiment_geo2027_log1p_country_block_transfer import (
    calibration_training, omit_country_fit, one_year,
    score_gap, TARGETS, COMPARISONS, RIDGE, study,
)


class CountryBlockTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=sample()
        cls.ids=sorted(cls.source)
        cls.names={cid:"Toy country "+str(cid) for cid in cls.ids}
        cls.ledger=historical_ledger(cls.source,2025,cls.ids)

    def test_train_refit_really_removes_every_label_of_heldout_country(self):
        training=calibration_training(self.ledger,2025)
        cid=self.ids[0]
        excluded_beta,meta=omit_country_fit(training,cid,2025)
        full_beta,_=fit_target(self.ledger,2025)
        self.assertEqual(meta["country_id"],cid)
        self.assertEqual(meta["removed_historical_rows"],12)
        self.assertEqual(meta["remaining_historical_train_n"],len(training)-12)
        self.assertEqual(meta["last_training_label_year"],2023)
        self.assertEqual(meta["last_training_feature_year"],2021)
        self.assertTrue(meta["markov_offset_stays_original_with_country_history"])
        self.assertNotEqual(full_beta,excluded_beta)

    def test_label_at_origin_plus_one_or_target_does_not_enter_refit(self):
        source=copy.deepcopy(self.source)
        a=historical_ledger(source,2025,self.ids)
        altered=copy.deepcopy(source)
        for cid,h in altered.items():
            h[2024]=10000 if cid%3 else 0
            h[2025]=0 if cid%4 else 10000
        b=historical_ledger(altered,2025,self.ids)
        train_a=calibration_training(a,2025)
        train_b=calibration_training(b,2025)
        self.assertEqual(train_a,train_b)
        for cid in self.ids[:3]:
            beta_a,meta_a=omit_country_fit(train_a,cid,2025)
            beta_b,meta_b=omit_country_fit(train_b,cid,2025)
            self.assertEqual(beta_a,beta_b)
            self.assertEqual(meta_a,meta_b)

    def test_country_origin_death_feature_still_available_for_evaluation(self):
        target=2024
        training=calibration_training(self.ledger,target)
        affected=[r for r in self.ledger[target]
                  if 1<=r["origin_deaths"]<=24]
        self.assertGreater(len(affected),0)
        row=affected[0]
        fitted,info=omit_country_fit(training,row["country_id"],target)
        self.assertEqual(info["last_training_label_year"],target-2)
        self.assertEqual(info["last_training_feature_year"],target-4)
        self.assertEqual(row["origin_year"],target-2)
        self.assertTrue(0<row["p_original_binary"]<1)
        self.assertEqual(row["origin_state"],0)
        self.assertEqual(len(fitted),3)

    def test_counterfactual_brier_effect_matches_exact_loss(self):
        self.assertAlmostEqual(score_gap(.12,.30,0),.30**2-.12**2)
        self.assertAlmostEqual(score_gap(.12,.30,1),(.30-1)**2-(.12-1)**2)
        self.assertLess(score_gap(.12,.30,1),0)
        for inputs in ((0,.3,1),(.1,1,0),(.1,.3,5)):
            with self.assertRaises(ValueError):
                score_gap(*inputs)

    def test_one_year_full_reconstructs_previous_brier_and_blocking_is_finite(self):
        target=2017
        beta,meta=fit_target(self.ledger,target)
        scores,_=year_scores(self.ledger[target],beta)
        reference={"current_edition":"26.1","rolling_result":{"by_version":{
            "26.1":{"annual":[{
                "target_year":target,
                "fit":meta,
                "by_alpha":scores,
            }]}
        }}}
        result=one_year(self.ledger,target,self.names,reference,
                        full_details=True)
        self.assertEqual(result["risk_n"],196)
        self.assertEqual(result["training_labels_latest_year"],2015)
        self.assertEqual(result["training_features_latest_year"],2013)
        self.assertEqual(result["subthreshold_1_to_24_n"],
                         len(result["all_subthreshold_cases"]))
        self.assertTrue(result["country_historical_calibration_rows_excluded_per_case"])
        self.assertTrue(result["country_markov_history_not_excluded"])
        self.assertAlmostEqual(
            result["fullfit_delta_Brier_annual"],
            scores["1.0"]["brier"]-scores["0.0"]["brier"],places=9)
        self.assertTrue(-1<=result["blocked_delta_Brier_within_subthreshold"]<=1)
        self.assertTrue(all(
            r["historical_country_removed_for_calibration"]["removed_historical_rows"]==4
            for r in result["all_subthreshold_cases"]))

    def test_comparison_design_and_legacy_provenance(self):
        self.assertEqual(TARGETS,tuple(range(2017,2026)))
        self.assertEqual(len(COMPARISONS),13)
        self.assertEqual(
            [x for x in COMPARISONS if x[1]==2017],
            [("26.1",2017),("23.1",2017),("24.1",2017),("25.1",2017)])
        self.assertEqual(RIDGE,5.0)
        with self.assertRaisesRegex(ValueError,"provenance"):
            study({},self.names,{"schema":"tampered"},{"schema":"tampered"})

    def test_2027_issue_still_sha_frozen_and_all_196_outcomes_unresolved(self):
        v=audit_issue(ISSUE.read_bytes(),MANIFEST.read_bytes(),
                      ORIGINAL.read_bytes())
        self.assertEqual(v["country_n"],196)
        self.assertEqual(v["future_2027_outcomes_resolved"],0)


if __name__=="__main__":
    unittest.main()
