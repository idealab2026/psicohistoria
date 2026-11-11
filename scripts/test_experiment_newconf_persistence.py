"""Synthetic tests only; real official labels stay in separately pinned vintages."""
import copy
import unittest

from experiment_newconf_persistence import estimate, evaluate, persistence_group


def synthetic_panel():
    old, later, activity = {}, {}, set()
    for index in range(196):
        cid = str(index + 1)
        old[cid] = {}
        later[cid] = {}
        for year in range(2000, 2025):
            value = (int(index % 47 == 0 and year % 5 == 0)
                     if year <= 2022 else
                     int((year == 2023 and index in (1, 2))
                         or (year == 2024 and index == 3)))
            row = {"newconf": value, "onset2": 0,
                   "newconf_episodes": value, "multiple_episode_rows": 1}
            if year <= 2022:
                old[cid][year] = row.copy()
            later[cid][year] = row.copy()
            if year <= 2022 and (
                (index % 3 == 1 and year % 3 == 0) or index % 3 == 2
            ):
                activity.add((cid, year))
    return old, later, activity


class NewconfPersistenceTests(unittest.TestCase):
    def test_origin_window_has_no_future_activity(self):
        activity = {("1", 2019), ("1", 2020), ("1", 2022), ("1", 2023)}
        self.assertEqual(persistence_group(activity, "1", 2020), 2)
        self.assertEqual(persistence_group(activity, "1", 2022), 2)
        self.assertEqual(persistence_group(activity, "2", 2022), 0)

    def test_frozen_horizons_and_no_new_forecast(self):
        old, later, activity = synthetic_panel()
        for horizon in (1, 2):
            predictions, fit = estimate(old, activity, 2022, horizon)
            self.assertEqual(len(predictions), 196)
            self.assertEqual(fit["max_fitted_newconf_year"], 2022)
            self.assertTrue(all(0 < p < 1 for p in predictions.values()))
        study = evaluate(old, later, activity, with_ci=False)
        self.assertEqual(study["evaluations"], 392)
        self.assertEqual(study["positive_evaluations"], 3)
        self.assertFalse(study["forecast_2027_modified"])
        self.assertEqual(len(study["by_horizon"]), 2)

    def test_fail_closed_on_future_activity_and_labels(self):
        old, later, activity = synthetic_panel()
        with self.assertRaisesRegex(ValueError, "2022"):
            estimate(old, activity | {("1", 2023)}, 2022, 2)
        modified = copy.deepcopy(old)
        modified["1"][2023] = {"newconf": 1}
        with self.assertRaisesRegex(ValueError, "2022"):
            estimate(modified, activity, 2022, 2)

    def test_external_label_mutation_fails_closed(self):
        old, later, activity = synthetic_panel()
        changed = copy.deepcopy(later)
        changed["1"][2024]["newconf"] = 1
        changed["1"][2024]["newconf_episodes"] = 1
        with self.assertRaisesRegex(ValueError, "external country-year labels changed"):
            evaluate(old, changed, activity, with_ci=False)

    def test_no_posthoc_horizon_tuning(self):
        old, later, activity = synthetic_panel()
        with self.assertRaisesRegex(ValueError, "frozen 2022"):
            estimate(old, activity, 2022, 3)
        with self.assertRaisesRegex(ValueError, "frozen 2022"):
            estimate(old, activity, 2021, 2)


if __name__ == "__main__":
    unittest.main()
