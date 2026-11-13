"""Adversarial and exhaustive-64-strata tests, with all first issues SHA checked."""
import copy
import math
import unittest

import build_2027_prospective_registry as registry
import diagnose_acd2027_brier_pivot as model


class ACD2027ConditionalBrierFrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs, cls.manifests = registry.read_issued()
        cls.report = model.diagnose(cls.docs, cls.manifests)

    def test_south_sudan_is_single_fixed_2024_absence_and_2025_presence(self):
        r = self.report
        self.assertEqual(r["pivotal_country_gwno"], 626)
        self.assertEqual(r["pivotal_country_name"], "South Sudan")
        self.assertFalse(r["pivotal_country_active_2024"])
        self.assertTrue(r["pivotal_country_active_2025"])
        self.assertEqual(r["n_original_acd_country_questions"], 32)
        self.assertEqual(r["source_issued_acd_sha256"], registry.EXPECTED["acd"][1])
        self.assertEqual(r["2027_outcomes_used"], 0)
        self.assertEqual(r["research_status"], "DERIVED_EX_ANTE_HYPOTHETICAL_NOT_ISSUED_FORECAST")
        self.assertTrue(r["comparison_is_not_a_new_primary_metric"])
        self.assertAlmostEqual(
            r["share_of_sum_squared_probability_differences_due_to_pivotal_country"],
            .9620710853045114, places=11)

    def test_all_64_count_conditioned_binary_scenarios_match_individual_brier(self):
        r = self.report
        pivot = next(x for x in self.docs["acd"]["countries"] if x["country_id"] == 626)
        other = [x for x in self.docs["acd"]["countries"] if x["country_id"] != 626]
        self.assertEqual(len(other), 31)
        self.assertEqual(len(r["all_64_count_conditioned_hypothetical_scenarios"]), 64)
        for case in r["all_64_count_conditioned_hypothetical_scenarios"]:
            k = case["other_31_2027_acd_absences"]
            pivot_y = int(case["pivotal_country_2027_acd_present"])
            y_other = [0] * k + [1] * (31 - k)
            actual = model.brier_difference(
                pivot["p_global_recent5"], pivot["p_lag1_group"], pivot_y)
            actual += sum(model.brier_difference(
                row["p_global_recent5"], row["p_lag1_group"], y)
                for row, y in zip(other, y_other))
            self.assertAlmostEqual(actual / 32,
                                   case["delta_brier_primary_minus_lag1"], places=14)

    def test_exact_pivotal_sign_frontier_requires_no_independence(self):
        cases = self.report["conditional_frontier"]
        self.assertEqual(cases["absent"]["primary_wins_if_other_absences"], [])
        self.assertEqual(cases["absent"]["lag1_wins_if_other_absences"], list(range(32)))
        self.assertEqual(cases["present"]["primary_wins_if_other_absences"],
                         list(range(13)))
        self.assertEqual(cases["present"]["lag1_wins_if_other_absences"],
                         list(range(13, 32)))
        self.assertEqual(cases["present"]["ties_if_other_absences"], [])
        self.assertAlmostEqual(cases["present"]["maximum_delta"],
                               .01264699599787839, places=12)
        self.assertAlmostEqual(cases["absent"]["minimum_delta"],
                               .010582464680253418, places=12)

    def test_binary_score_algebra_and_invalid_inputs(self):
        self.assertAlmostEqual(model.brier_difference(.8, .6, 0), .28)
        self.assertAlmostEqual(model.brier_difference(.8, .6, 1), -.12)
        self.assertAlmostEqual(
            model.brier_difference(.8, .6, 0) -
            model.brier_difference(.8, .6, 1), 2 * (.8 - .6))
        for p, q, y in ((0, .5, 0), (.5, 1, 1), (math.nan, .5, 0),
                        (.5, .5, 0.5), (.5, .5, True)):
            with self.assertRaises(ValueError):
                model.brier_difference(p, q, y)

    def test_origin_and_outcome_tampering_are_rejected(self):
        bad = copy.deepcopy(self.docs)
        bad["acd"]["countries"][0]["also_active_in_2024"] = False
        with self.assertRaisesRegex(ValueError, "1\\+31"):
            model.diagnose(bad, self.manifests)
        bad = copy.deepcopy(self.docs)
        pivot = next(x for x in bad["acd"]["countries"] if x["country_id"] == 626)
        pivot["p_lag1_group"] = .848030607957
        with self.assertRaisesRegex(ValueError, "stratification"):
            model.diagnose(bad, self.manifests)
        bad = copy.deepcopy(self.docs)
        bad["acd"]["2027_outcomes_resolved"] = 1
        with self.assertRaisesRegex(ValueError, "unresolved"):
            model.diagnose(bad, self.manifests)


if __name__ == "__main__":
    unittest.main()
