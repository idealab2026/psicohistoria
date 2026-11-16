"""Synthetic mathematical country Brier attribution tests with no live network."""
from __future__ import annotations

import copy
import json
import unittest

from audit_geo2027_log1p_shadow_issue import (
    ISSUE, MANIFEST, ORIGINAL, audit as audit_issue,
)
from experiment_geo2027_log1p_rolling_year_vintage import (
    historical_ledger, fit_target, year_scores,
)
from diagnose_geo2027_log1p_annual_country_reversals import (
    brier_effect, bucket, compute_case, explain_year, replay, sign,
)
from test_experiment_geo2027_intensity_markov_cross_release import sample


class CountryYearReversalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=sample()
        cls.ids=sorted(cls.source)
        cls.names={cid:"Country "+str(cid) for cid in cls.ids}
        cls.ledger=historical_ledger(cls.source,2025,cls.ids)

    def test_exact_brier_paired_identity_sign(self):
        self.assertAlmostEqual(brier_effect(.3,.5,1),-.24)
        self.assertAlmostEqual(brier_effect(.3,.5,0),.16)
        self.assertEqual(sign(-.24),"full_intensity_better")
        self.assertEqual(sign(.16),"inactive_removed_better")
        self.assertEqual(sign(0),"effectively_equal")
        for p0,p1,y in ((0,.5,0),(.2,1,0),(.2,.4,2)):
            with self.assertRaises(ValueError):
                brier_effect(p0,p1,y)

    def test_0_and_25plus_count_cannot_change_alpha_0_vs_1(self):
        beta=(0.1,1.2,1.7)
        base={"country_id":1,"target_year":2025,
              "origin_year":2023,"p_original_binary":.3}
        for deaths in (0,25,140,10000):
            state=int(deaths>=25)
            row={**base,"origin_deaths":deaths,
                 "origin_state":state,"outcome":1}
            result=compute_case(row,beta,"Toy")
            self.assertEqual(result["alpha0_p_active"],
                             result["alpha1_p_active"])
            self.assertEqual(result[
                "alpha1_minus_alpha0_delta_Brier_exact_for_aggregation"],0)
        self.assertEqual(bucket(0),"zero")
        self.assertEqual(bucket(24),"inactive_1_to_24")
        self.assertEqual(bucket(25),"active_25_plus")
        with self.assertRaises(ValueError):
            bucket(-1)

    def test_one_to_24_changes_brier_outcome_dependence(self):
        base={"country_id":2,"origin_deaths":10,"origin_state":0,
              "p_original_binary":.2}
        beta=(0.,1.5,0.)
        active=compute_case({**base,"outcome":1},beta,"Country2")
        inactive=compute_case({**base,"outcome":0},beta,"Country2")
        self.assertLess(active["alpha1_minus_alpha0_delta_Brier_sum"],0)
        self.assertGreater(inactive["alpha1_minus_alpha0_delta_Brier_sum"],0)
        self.assertEqual(active["origin_deaths_bucket"],"inactive_1_to_24")
        self.assertEqual(active["event_class"],"inactive_to_active")
        self.assertEqual(inactive["event_class"],"inactive_to_inactive")

    def test_year_exact_contributions_and_no_refit_loo(self):
        for target in (2017,2025):
            beta,_=fit_target(self.ledger,target)
            annual,_=year_scores(self.ledger[target],beta)
            delta=annual["1.0"]["brier"]-annual["0.0"]["brier"]
            prior={"alpha1_minus_alpha0_delta_Brier":round(delta,12),
                "alpha1_vs_alpha0_brier_winner":sign(delta)}
            out=explain_year(self.ledger[target],beta,self.names,prior)
            self.assertEqual(out["country_n"],196)
            self.assertEqual(out["n_affected_historical_country_rows"],
                             out["origin_1_to_24_n"])
            self.assertEqual(out["by_origin_deaths_bucket"]["zero"][
                "nonzero_delta_n"],0)
            self.assertEqual(out["by_origin_deaths_bucket"]["active_25_plus"][
                "nonzero_delta_n"],0)
            self.assertAlmostEqual(
                out["year_brier_delta_alpha1_minus_alpha0"],delta,places=10)
            self.assertAlmostEqual(
                out["paired_total_sum_difference"],
                delta*196,places=8)
            self.assertTrue(0<=out["top1_share_of_absolute_country_effects"]<=1)
            self.assertTrue(0<=out["top3_share_of_absolute_country_effects"]<=1)
            self.assertGreaterEqual(out["top3_share_of_absolute_country_effects"],
                                    out["top1_share_of_absolute_country_effects"])
            self.assertTrue(all(x["origin_deaths_bucket"]=="inactive_1_to_24"
                                for x in out["all_origin_1_to_24_country_effects"]))

    def test_mutating_target_outcome_does_not_affect_prior_rolling_fit(self):
        a=copy.deepcopy(self.source)
        b=copy.deepcopy(self.source)
        for cid,h in b.items():
            h[2025]=1000 if cid%2 else 0
        la=historical_ledger(a,2025,self.ids)
        lb=historical_ledger(b,2025,self.ids)
        fit_a,meta_a=fit_target(la,2025)
        fit_b,meta_b=fit_target(lb,2025)
        self.assertEqual(fit_a,fit_b)
        self.assertEqual(meta_a,meta_b)
        self.assertNotEqual(la[2025],lb[2025])

    def test_prior_result_mismatch_fail_closed(self):
        beta,_=fit_target(self.ledger,2017)
        with self.assertRaises(AssertionError):
            explain_year(self.ledger[2017],beta,self.names,
                {"alpha1_minus_alpha0_delta_Brier":7,
                 "alpha1_vs_alpha0_brier_winner":"inactive_removed_better"})
        with self.assertRaisesRegex(ValueError,"provenance"):
            replay({},self.names,{"schema":"tampered"})

    def test_no_prospective_2027_changes_or_new_issues(self):
        result=audit_issue(ISSUE.read_bytes(),MANIFEST.read_bytes(),
                           ORIGINAL.read_bytes())
        self.assertEqual(result["country_n"],196)
        self.assertEqual(result["future_2027_outcomes_resolved"],0)


if __name__=="__main__":
    unittest.main()
