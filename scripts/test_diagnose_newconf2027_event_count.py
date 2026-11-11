import math
import unittest

from diagnose_newconf2027_event_count import diagnose, poisson_binomial, quantile


class EventCountDiagnosticTests(unittest.TestCase):
    def test_two_bernoullis(self):
        self.assertEqual(len(poisson_binomial([0.2, 0.5])), 3)
        for observed, expected in zip(poisson_binomial([0.2, 0.5]), [0.4, 0.5, 0.1]):
            self.assertAlmostEqual(observed, expected)
        self.assertEqual(quantile(poisson_binomial([0.2, 0.5]), 0.975), 2)

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


if __name__ == "__main__":
    unittest.main()
