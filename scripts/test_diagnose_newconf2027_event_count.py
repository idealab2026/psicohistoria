import math
import unittest

from diagnose_newconf2027_event_count import (comonotonic_pmf, dependence_sensitivity, diagnose, poisson_binomial, quantile)


class EventCountDiagnosticTests(unittest.TestCase):
    def test_two_bernoullis(self):
        self.assertEqual(len(poisson_binomial([0.2, 0.5])), 3)
        for observed, expected in zip(poisson_binomial([0.2, 0.5]), [0.4, 0.5, 0.1]):
            self.assertAlmostEqual(observed, expected)
        self.assertEqual(quantile(poisson_binomial([0.2, 0.5]), 0.975), 2)

    def test_comonotonic_extreme_preserves_marginal_expectation(self):
        ps = [0.2, 0.5]
        pmf = comonotonic_pmf(ps)
        for observed, expected in zip(pmf, [0.5, 0.3, 0.2]):
            self.assertAlmostEqual(observed, expected)
        for scenario in dependence_sensitivity(ps):
            self.assertAlmostEqual(scenario["expected_events"], sum(ps))
        self.assertAlmostEqual(dependence_sensitivity(ps)[-1]["p_zero"], 0.5)

    def test_scenario_weight_must_be_unit_interval(self):
        for w in (-0.01, 1.01):
            with self.assertRaises(ValueError):
                dependence_sensitivity([0.3, 0.1], [w])

    def test_refuse_invalid_probability(self):
        for value in (-0.1, 1.1, float("nan"), True):
            with self.assertRaises(ValueError):
                poisson_binomial([value])

    def test_original_issued_forecast_only(self):
        result = diagnose("data/forecast-2027-newconf.json")
        self.assertEqual(result["countries"], 196)
        self.assertEqual(result["2027_outcomes_observed"], 0)
        self.assertEqual(result["status"], "PRE_OUTCOME_MODEL_IMPLIED_ONLY")
        self.assertAlmostEqual(result["expected_events"], 2.490944756323005)
        self.assertAlmostEqual(result["p_zero"], 0.07853812853444322)
        self.assertAlmostEqual(result["p_at_most_one"], 0.2827139961563453)
        self.assertEqual(result["model_implied_central_95_count_range"], [0, 6])
        self.assertTrue(math.isfinite(result["p_six_or_more"]))
        scenarios = result["dependence_sensitivity"]
        self.assertEqual(len(scenarios), 4)
        self.assertAlmostEqual(scenarios[0]["p_zero"], result["p_zero"])
        self.assertAlmostEqual(scenarios[1]["p_zero"], 0.1599138150233989)
        self.assertAlmostEqual(scenarios[2]["p_zero"], 0.2819773447568324)
        self.assertAlmostEqual(scenarios[-1]["p_zero"], 0.892294993424)


if __name__ == "__main__":
    unittest.main()
