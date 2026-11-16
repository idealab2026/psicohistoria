"""No-leakage and exact algebraic contribution tests for Indonesian H2 vintage study."""
from __future__ import annotations

import unittest

from diagnose_geo2027_indonesia_vintage_attribution import (
    counts, model_probability, shapley_revision, subtract, compare,
)


class IndonesiaVintageAttributionTests(unittest.TestCase):
    def setUp(self):
        self.old = [[20, 3], [2, 7]]
        self.new = [[19, 4], [2, 7]]
        self.others0 = [[1000, 30], [31, 220]]
        self.others1 = [[997, 31], [30, 224]]

    def test_shapley_exact_telescope_and_effects(self):
        r = shapley_revision(1, self.old, self.new, self.others0, self.others1)
        a, _, _ = model_probability(1, self.old, self.others0)
        b, _, _ = model_probability(1, self.new, self.others1)
        self.assertAlmostEqual(
            (r["own_historical_transitions_shapley_pp"] +
             r["all_other_countries_transitions_shapley_pp"]) / 100,
            b - a, places=10)
        self.assertAlmostEqual(r["probability_change_pp"] / 100,
                               b - a, places=10)

    def test_only_country_history_changes(self):
        r = shapley_revision(1, self.old, self.new, self.others0, self.others0)
        self.assertAlmostEqual(
            r["all_other_countries_transitions_shapley_pp"], 0.0)
        self.assertAlmostEqual(r["own_historical_transitions_shapley_pp"],
                               r["probability_change_pp"])

    def test_only_other_country_history_changes(self):
        r = shapley_revision(1, self.old, self.old, self.others0, self.others1)
        self.assertAlmostEqual(r["own_historical_transitions_shapley_pp"], 0.0)
        self.assertAlmostEqual(r["all_other_countries_transitions_shapley_pp"],
                               r["probability_change_pp"])

    def test_future_state_is_never_a_training_transition(self):
        history={2019: 0, 2020: 1, 2021: 1, 2022: 1, 2023: 0, 2024: 0}
        self.assertEqual(counts(history, 2022),
                         counts({y:v for y,v in history.items() if y <= 2022},2022))
        self.assertEqual(counts(history,2022), [[0,1],[0,2]])

    def test_reject_unphysical_global_less_than_country_counts(self):
        with self.assertRaisesRegex(ValueError, "exceeds"):
            subtract([[0,0],[0,0]], self.old)

    def test_country_fixed_origin_and_missing_do_not_become_zero(self):
        # Ensure 2022 changed origin is explicitly rejected, not silently
        # assigned to the same risk group.
        old={850: {2019: 0, 2020: 1, 2021: 1, 2022: 1}}
        revised={850: {2019: 0, 2020: 1, 2021: 1, 2022: 0}}
        oldmeta={"global_transition_counts": [[1000,20],[20,150]]}
        with self.assertRaisesRegex(ValueError, "classification changed"):
            compare(old, revised, oldmeta, oldmeta, 850, {}, {})


if __name__ == "__main__":
    unittest.main()
