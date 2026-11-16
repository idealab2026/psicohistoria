"""Fixed-issuance hypothetical 2025 death-count sensitivity contracts."""
from __future__ import annotations

import json
import unittest

from audit_geo2027_log1p_issued_death_stress import (
    ALERTS, ISSUE, ORIGINAL, MARGINS, certified_topk,
    death_range, envelope, study,
)
from audit_geo2027_log1p_shadow_issue import audit as audit_issue, MANIFEST


class IssuedLog1pDeathStressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.issue=json.loads(ISSUE.read_bytes())
        cls.original=json.loads(ORIGINAL.read_bytes())
        cls.alerts=json.loads(ALERTS.read_bytes())
        cls.beta=cls.issue["training"]["final_beta_log1p"]

    def test_frozen_separate_shadow_still_sha_authenticated(self):
        result=audit_issue(ISSUE.read_bytes(),MANIFEST.read_bytes(),
                           ORIGINAL.read_bytes())
        self.assertEqual(result["country_n"],196)
        self.assertEqual(result["future_2027_outcomes_resolved"],0)

    def test_all_margin_ranges_preserve_25_death_original_state(self):
        for margin in MARGINS:
            for deaths,state in ((0,0),(1,0),(14,0),(24,0),
                                  (25,1),(27,1),(100,1),(90323,1)):
                lo,hi=death_range(deaths,state,margin)
                self.assertLessEqual(lo,deaths)
                self.assertGreaterEqual(hi,deaths)
                self.assertEqual(int(lo>=25),state)
                self.assertEqual(int(hi>=25),state)
        self.assertEqual(death_range(0,0,10),(0,10))
        self.assertEqual(death_range(24,0,10),(14,24))
        self.assertEqual(death_range(25,1,10),(25,35))
        self.assertEqual(death_range(35,1,10),(25,45))

    def test_illegal_crossings_and_noninteger_counts_fail_closed(self):
        for args in [(-1,0,5),(0,1,5),(25,0,5),(True,0,5),
                     (0,0,2),(0,0,1.5),(40,2,5)]:
            with self.subTest(args=args),self.assertRaises(ValueError):
                death_range(*args)

    def test_real_issued_burundi_zero_to_ten_stress_not_reissued(self):
        burundi=next(x for x in self.issue["countries"]
                     if x["country"]=="Burundi")
        self.assertEqual(burundi["origin_deaths_best_2025"],0)
        self.assertEqual(burundi["origin_binary_state_2025"],0)
        b=envelope(burundi,self.beta,10)
        self.assertEqual((b["low_deaths"],b["high_deaths"]),(0,10))
        self.assertGreater(b["max_abs_change_pp"],15)
        self.assertLessEqual(
            b["full_width_pp"],
            b["certified_logistic_lipschitz_bound_width_pp"]+1e-5)
        self.assertAlmostEqual(
            b["low_p_active"],
            burundi["log1p_shadow_p_active_2027"],places=10)

    def test_nested_margins_never_shrink_country_envelopes(self):
        for row in self.issue["countries"]:
            previous=None
            for m in MARGINS:
                b=envelope(row,self.beta,m)
                if previous is not None:
                    self.assertLessEqual(
                        b["low_p_active"],previous["low_p_active"]+1e-11)
                    self.assertGreaterEqual(
                        b["high_p_active"],previous["high_p_active"]-1e-11)
                previous=b

    def test_certified_rank_monotone_under_independent_interval_endpoints(self):
        # N=4 toy and k=2: first two are mandatory under their exact intervals
        risk={
            1:{"lo":.90,"centre":.93,"hi":.95},
            2:{"lo":.80,"centre":.82,"hi":.83},
            3:{"lo":.60,"centre":.66,"hi":.72},
            4:{"lo":.15,"centre":.20,"hi":.25},
        }
        a=certified_topk(risk,2)
        self.assertEqual(a["nominal_ordered"],[1,2])
        self.assertEqual(a["mandatory"],[1,2])
        self.assertEqual(a["possible"],[1,2])
        self.assertTrue(a["all_nominal_members_certified_in_variant"])

    def test_certified_topk_detects_ambiguous_members_and_ties(self):
        x={
            1:{"lo":.60,"centre":.80,"hi":.90},
            2:{"lo":.70,"centre":.75,"hi":.80},
            3:{"lo":.75,"centre":.80,"hi":.85},
            4:{"lo":.10,"centre":.10,"hi":.20},
        }
        a=certified_topk(x,1)
        self.assertEqual(a["nominal_ordered"],[1])
        self.assertEqual(a["mandatory"],[])
        self.assertEqual(a["possible"],[1,2,3])
        self.assertEqual(a["nominal_not_mandatory"],[1])
        self.assertEqual(a["possible_outside_nominal"],[2,3])
        x[2]={"lo":.80,"centre":.80,"hi":.80}
        x[1]={"lo":.80,"centre":.80,"hi":.80}
        x[3]={"lo":.20,"centre":.20,"hi":.20}
        a=certified_topk(x,1)
        self.assertEqual(a["nominal_ordered"],[1])
        self.assertEqual(a["mandatory"],[1])
        self.assertEqual(a["possible"],[1])

    def test_malformed_intervals_and_small_cohort_rejected(self):
        with self.assertRaises(ValueError):
            certified_topk({1:{"lo":.1,"centre":.2,"hi":.3}},1)
        with self.assertRaises(ValueError):
            certified_topk({1:{"lo":.5,"centre":.2,"hi":.8},
                            2:{"lo":.1,"centre":.2,"hi":.3}},1)

    def test_all_196_country_stress_reports_and_original_alerts_untouched(self):
        report=study(self.issue,self.original,self.alerts)
        self.assertEqual(report["n_issued_countries"],196)
        self.assertEqual(report["perturbation_absolute_death_margins"],[1,5,10])
        self.assertEqual(report["future_2027_outcomes_resolved"],0)
        self.assertFalse(report["any_first_issued_probability_changed"])
        self.assertEqual(report["n_first_issued_alerts_changed"],0)
        self.assertEqual(len(report["country_envelopes"]),196)
        self.assertEqual(
            [s["n_2025_origin_exact_zero_deaths"]
             for s in report["scenario_summaries"]],[154]*3)
        for s in report["scenario_summaries"]:
            self.assertLessEqual(s["counterfactual_expected_sum_low"],
                                 s["issued_expected_active_count_sum"]+1e-9)
            self.assertGreaterEqual(s["counterfactual_expected_sum_high"],
                                    s["issued_expected_active_count_sum"]-1e-9)
            for state in (0,1):
                rr=s["risk_group_rank_certification"][str(state)]
                self.assertGreaterEqual(rr["possible_n"],rr["k"])
                self.assertLessEqual(rr["mandatory_n"],rr["k"])


if __name__=="__main__":
    unittest.main()
