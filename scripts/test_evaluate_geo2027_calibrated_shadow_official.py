"""Synthetic-only 2027 outcomes: no factual outcome record is used."""
import copy
import unittest

from evaluate_geo2027_calibrated_shadow_official import (
    COUNTRIES,EXPECTED_SHADOW_FIRST_COMMIT,EXPECTED_SHADOW_SHA256,
    evaluate,load_authenticated,pair_metrics,
)


class GeoShadowFuturePairedContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original,cls.shadow,cls.manifest=load_authenticated()
        cls.rows=cls.original["countries"]

    def labels(self,transition=False):
        return {r["country_id"]:(
            1-r["last_observed_state_2025"] if transition else
            r["last_observed_state_2025"])
            for r in self.rows}

    def test_frozen_issued_shadow_is_still_future_unresolved(self):
        self.assertEqual(self.manifest["first_public_shadow_commit"],
                         EXPECTED_SHADOW_FIRST_COMMIT)
        self.assertEqual(self.manifest["shadow_forecast_sha256"],
                         EXPECTED_SHADOW_SHA256)
        self.assertEqual(self.shadow["2027_outcomes_resolved"],0)
        self.assertFalse(self.shadow["prospective_predictive_skill_demonstrated"])
        self.assertTrue(self.shadow["design_posthoc_not_independently_confirmatory"])
        self.assertEqual(len(self.shadow["countries"]),COUNTRIES)

    def test_no_transition_synthetic_cohort_shadow_wins_paired_loss(self):
        result=evaluate(self.original,self.shadow,self.labels(),{
            "source":"synthetic"}, {"source_2027_rows":196})
        self.assertEqual(result["status"],"FULL_COVERAGE_CANDIDATE_STILL_UNCERTIFIED")
        self.assertEqual((result["resolved_country_years"],result["unresolved_country_years"]),
                         (196,0))
        score=result["primary_196_country_paired_comparison"]
        self.assertEqual(score["country_years"],196)
        self.assertEqual(score["observed_active_2027"],34)
        self.assertLess(score["primary_delta_brier_shadow_minus_original"],0)
        self.assertLess(score["secondary_delta_log_loss_shadow_minus_original"],0)
        self.assertEqual(score["per_country_brier_shadow_better_count"],196)
        self.assertEqual(score["per_country_brier_shadow_worse_count"],0)
        self.assertEqual(
            [result["by_2025_known_origin_state"][k]["country_years"] for k in ("0","1")],
            [162,34]
        )
        self.assertFalse(result["source_first_complete_release_independently_certified"])
        self.assertFalse(result["prospective_skill_independently_certified"])

    def test_all_transition_synthetic_cohort_original_wins(self):
        result=evaluate(self.original,self.shadow,self.labels(transition=True),{}, {})
        self.assertEqual(result["status"],"FULL_COVERAGE_CANDIDATE_STILL_UNCERTIFIED")
        score=result["primary_196_country_paired_comparison"]
        self.assertEqual(score["observed_active_2027"],162)
        self.assertGreater(score["primary_delta_brier_shadow_minus_original"],0)
        self.assertGreater(score["secondary_delta_log_loss_shadow_minus_original"],0)
        self.assertEqual(score["per_country_brier_shadow_worse_count"],196)

    def test_missing_nonalert_country_does_not_produce_misleading_196_score(self):
        labels=self.labels()
        # A missing label outside the first item is still a hard blocker.
        removed=self.rows[-1]["country_id"]
        labels.pop(removed)
        score=evaluate(self.original,self.shadow,labels,{}, {})
        self.assertEqual(score["status"],"PARTIAL_OFFICIAL_2027_COVERAGE_NO_SCORES")
        self.assertEqual(score["resolved_country_years"],195)
        self.assertEqual(score["unresolved_country_ids"],[removed])
        self.assertIsNone(score["primary_196_country_paired_comparison"])
        self.assertIsNone(score["by_2025_known_origin_state"])
        labels[removed]=0
        labels[1999]=1
        complete=evaluate(self.original,self.shadow,labels,{}, {})
        self.assertEqual(complete["unissued_extra_country_ids_ignored"],1)
        self.assertEqual(complete["resolved_country_years"],196)

    def test_corrupt_source_identity_and_nonbinary_labels_fail(self):
        labels=self.labels()
        wrong=copy.deepcopy(self.shadow)
        wrong["countries"][0]["original_issued_p_active_2027"]+=0.01
        with self.assertRaisesRegex(ValueError,"cannot be paired"):
            evaluate(self.original,wrong,labels,{}, {})
        wrong=copy.deepcopy(self.shadow)
        wrong["countries"][1]["country_id"]=9999
        with self.assertRaisesRegex(ValueError,"ID ordering"):
            evaluate(self.original,wrong,labels,{}, {})
        labels[self.rows[0]["country_id"]]=None
        with self.assertRaisesRegex(ValueError,"Malformed"):
            evaluate(self.original,self.shadow,labels,{}, {})
        with self.assertRaisesRegex(ValueError,"empty"):
            pair_metrics([],{})


if __name__=="__main__":
    unittest.main()
