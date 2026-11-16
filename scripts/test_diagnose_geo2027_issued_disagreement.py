"""Deterministic ex ante 196-country disagreement, no-outcome tests."""
from __future__ import annotations

import copy
import json
import unittest

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit, prospective_full196_score,
)
from diagnose_geo2027_issued_disagreement import (
    analyze, score_sensitivity, group, _ranks,
)


class IssuedDisagreementAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.new=json.loads(ISSUE.read_text(encoding="utf8"))
        cls.old=json.loads(OLD_SHADOW.read_text(encoding="utf8"))
        cls.original=json.loads(ORIGINAL.read_text(encoding="utf8"))
        cls.report=analyze(cls.new,cls.old,cls.original)

    def test_first_complete_issued_sha_and_196_country_evaluation_unresolved(self):
        result=audit(ISSUE.read_bytes(),MANIFEST.read_bytes(),
            ORIGINAL.read_bytes(),OLD_SHADOW.read_bytes(),
            OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
        self.assertEqual(result["country_n"],196)
        self.assertEqual(result["official_2027_outcomes_resolved"],0)
        self.assertEqual(self.report["fixed_original_GWNO_country_n"],196)
        self.assertTrue(self.report["no_new_forecasts_or_alerts_issued"])

    def test_source_ex_ante_intensity_groups_and_no_alpha_effect_outside_1_24(self):
        g=self.report["group_by_origin_deaths"]
        self.assertEqual([g[k]["country_n"] for k in
            ("origin_zero","origin_1_to_24","origin_active")],
            [154,8,34])
        self.assertEqual(sum(v["country_n"] for v in g.values()),196)
        self.assertTrue(self.report[
            "alpha1_minus_alpha0_differs_only_for_8_subthreshold_countries"])
        for r in self.report["all_country_probability_and_future_Brier_conditional_effects"]:
            if r["group"]!="origin_1_to_24":
                self.assertEqual(r["new_global_only_alpha0_p"],
                                 r["new_global_only_alpha1_p"])

    def test_zero_origin_group_global_only_probability_collapse_is_documented(self):
        g=self.report["group_by_origin_deaths"]["origin_zero"]
        self.assertGreater(g["range_old_LOG1P_pp"],20)
        self.assertLess(g["range_new_global_only_pp"],0.1)
        self.assertLess(g["min_new_global_only_probability"],.036)
        self.assertGreater(g["max_new_global_only_probability"],.034)
        self.assertTrue(g["mean_absolute_delta_pp"]>0)

    def test_ranking_churn_not_issued_alert_list(self):
        rs=self.report["rank_disagreement_diagnostics_not_reissued_alerts"]
        self.assertEqual(rs["origin_inactive_top10"]["overlap_n"],6)
        self.assertEqual(rs["origin_active_top5"]["overlap_n"],2)
        self.assertEqual(rs["all_country_top15"]["overlap_n"],11)
        for x in rs.values():
            self.assertTrue(x["not_a_new_issued_alert_list"])
            self.assertEqual(len(x["old_rank"]),x["n"])
            self.assertEqual(len(x["new_rank"]),x["n"])
        self.assertEqual(self.report["n_primary_absolute_delta_at_least_10_pp"],9)
        self.assertEqual(self.report["n_primary_absolute_delta_at_least_5_pp"],27)

    def test_exact_event_and_no_event_Brier_algebra_for_arbitrary_probabilities(self):
        for a,b in ((.03,.2),(.8,.6),(.1,.100001),(.97,.5)):
            d=score_sensitivity(a,b)
            self.assertAlmostEqual(d["no_event_y0"],a*a-b*b)
            self.assertAlmostEqual(d["event_y1"],(a-1)**2-(b-1)**2)
            self.assertAlmostEqual(d["event_y1"]-d["no_event_y0"],-2*(a-b))
        for a,b in ((0,.5),(1,.4),(.2,1)):
            with self.assertRaises(ValueError):
                score_sensitivity(a,b)

    def test_synthetic_full_196_future_labels_match_exact_predeclared_Brier(self):
        cases=self.report["all_country_probability_and_future_Brier_conditional_effects"]
        form=self.report["future_primary_paired_Brier_exact_algebra"]
        ids=[r["country_id"] for r in cases]
        for strategy in (lambda x:0,lambda x:1,lambda x:int(x%3==0)):
            labels={cid:strategy(cid) for cid in ids}
            score=prospective_full196_score(self.new,labels)
            actual=score["predeclared_paired_differences"][
                "primary_Brier_globalonly_alpha1_minus_original_LOG1P"]
            algebra=sum(
                r["primary_Brier_delta_if_event_y1"] if labels[r["country_id"]]
                else r["primary_Brier_delta_if_no_event_y0"]
                for r in cases)/196
            alternate=form["constant_if_all_country_outcomes_were_zero"]-(
                2/196)*sum(
                (r["primary_probability_delta_pp"]/100)*
                labels[r["country_id"]] for r in cases)
            self.assertAlmostEqual(actual,algebra,places=10)
            self.assertAlmostEqual(actual,alternate,places=10)
            self.assertGreaterEqual(actual,
                form["logical_min_over_all_2_power_196_possible_binary_labels"]-1e-9)
            self.assertLessEqual(actual,
                form["logical_max_over_all_2_power_196_possible_binary_labels"]+1e-9)

    def test_provenance_fail_closed_and_does_not_mutate_original_emissions(self):
        changed=copy.deepcopy(self.new)
        changed["official_2027_outcomes_resolved"]=196
        with self.assertRaisesRegex(ValueError,"lineage"):
            analyze(changed,self.old,self.original)
        self.assertEqual(len(self.original["countries"]),196)
        self.assertEqual(self.original["forecast_id"],
            "PSICO-GEO2027-STATEBASED25-V1")
        with self.assertRaises(ValueError):
            group({"origin_deaths_best_2025":-2})


if __name__=="__main__":
    unittest.main()
