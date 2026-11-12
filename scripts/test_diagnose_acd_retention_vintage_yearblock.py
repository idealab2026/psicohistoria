"""Synthetic target-year stresses only; no official 2027 outcomes are read."""
from __future__ import annotations

import copy
import unittest

import diagnose_acd_retention_vintage_yearblock as s


def synthetic_four_folds():
    # Synthetic Brier scores produce a slight pooled lag1 advantage that
    # reverses if a particular year is removed. No independent inference.
    return [
        {
            "target_year": year,
            "n_origin_active_countries": n,
            "n_target_persistent_country_incidence": 29,
            "models": {
                "p_global_recent5": {
                    "brier": bg, "logloss": bg + .2,
                },
                "p_country_eb": {
                    "brier": bc, "logloss": bc + .2,
                },
                "p_lag1_group": {
                    "brier": bl, "logloss": bl + .2,
                },
            },
        }
        for year,n,bg,bc,bl in (
            (2021,35,.1425,.1536,.1294),
            (2022,36,.1599,.1629,.1451),
            (2023,32,.0893,.1031,.1014),
            (2024,34,.1262,.1203,.1300),
        )
    ]


class ACDVintageYearBlockStressTests(unittest.TestCase):
    def test_years_to_later_original_target_editions(self):
        self.assertEqual(s.later_editions(2021,"22.1"),
                         ("23.1","24.1","25.1"))
        self.assertEqual(s.later_editions(2022,"23.1"),("24.1","25.1"))
        self.assertEqual(s.later_editions(2023,"24.1"),("25.1",))
        self.assertEqual(s.later_editions(2024,"25.1"),())
        with self.assertRaisesRegex(ValueError,"target-year edition"):
            s.later_editions(2021,"25.1")
        with self.assertRaisesRegex(ValueError,"target-year edition"):
            s.later_editions(2027,"25.1")

    def test_weighted_pooled_brier_and_paired_sign(self):
        years=synthetic_four_folds()
        result=s.summary(years)
        self.assertEqual(result["n_country_year_fold_evaluations"],137)
        self.assertEqual(result["n_persisted"],116)
        expected=sum(
            y["n_origin_active_countries"] * y["models"]["p_lag1_group"]["brier"]
            for y in years
        )/137
        self.assertAlmostEqual(result["pooled_brier"]["p_lag1_group"],expected)
        self.assertAlmostEqual(result["paired_brier_lag1_minus_global_recent5"],
                               result["pooled_brier"]["p_lag1_group"]-
                               result["pooled_brier"]["p_global_recent5"])
        self.assertLess(result["paired_brier_lag1_minus_global_recent5"],0)
        self.assertTrue(result["not_an_independent_test_or_selected_prospective_model"])
        with self.assertRaisesRegex(ValueError,"Unregistered"):
            s.delta(years,"post_hoc_oracle")

    def test_each_missing_year_recalculates_only_remaining_three(self):
        folds=synthetic_four_folds()
        jackknife=s.leave_one_target_year_out(folds)
        self.assertEqual([x["withheld_target_year"] for x in jackknife],
                         [2021,2022,2023,2024])
        for x in jackknife:
            a=x["three_year_pooled"]
            self.assertEqual(len(a["target_years"]),3)
            self.assertNotIn(x["withheld_target_year"],a["target_years"])
            self.assertEqual(a["n_country_year_fold_evaluations"],
                             137-next(y["n_origin_active_countries"]
                                      for y in folds
                                      if y["target_year"]==x["withheld_target_year"]))
            self.assertTrue(x["not_an_independent_year_test"])
            self.assertTrue(x["no_model_retraining_or_hyperparameter_tuning"])
        bad=copy.deepcopy(folds)
        bad[0]["target_year"]=2025
        with self.assertRaisesRegex(ValueError,"four-year"):
            s.leave_one_target_year_out(bad)

    def test_no_success_claim_from_one_favorable_year_or_changed_baseline(self):
        folds=synthetic_four_folds()
        with self.assertRaisesRegex(ValueError,"duplicated"):
            s.summary(folds+[copy.deepcopy(folds[0])])
        with self.assertRaisesRegex(ValueError,"empty"):
            s.delta([],"p_lag1_group")
        with self.assertRaisesRegex(ValueError,"Missing source-frozen"):
            s.validate_baseline({}, {}, None)
        altered=copy.deepcopy(folds)
        altered[0]["models"]["p_lag1_group"]["brier"]=.88
        self.assertGreater(s.summary(altered)["paired_brier_lag1_minus_global_recent5"],0)
        self.assertFalse(s.summary(altered)["brier_winner_descriptive"] ==
                         "p_lag1_group")

    def test_no_modified_issued_2027_forecasts(self):
        from evaluate_geo2027_calibrated_shadow_official import load_authenticated
        original,shadow,manifest=load_authenticated()
        self.assertEqual(len(original["countries"]),196)
        self.assertEqual(len(shadow["countries"]),196)
        self.assertEqual(shadow["2027_outcomes_resolved"],0)
        self.assertFalse(shadow["original_forecast_altered"])
        self.assertFalse(shadow["original_alerts_altered"])
        self.assertEqual(manifest["shadow_forecast_sha256"],
                         "1d0880f6e95e77d5e203b186e45a035676c7f724ecbe6a8b323f776b9eaa9188")


if __name__=="__main__":
    unittest.main()
