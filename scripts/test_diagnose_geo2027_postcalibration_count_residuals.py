"""Synthetic-only tests: no actual or fabricated GEO2027 outcome records."""
from __future__ import annotations

import copy
import math
import unittest

from diagnose_geo2027_postcalibration_count_residuals import (
    aggregate, annual_metrics, diagnose,
)
from experiment_geo2027_temporal_calibration import (
    logistic_shift, REVISED_VALIDATION_YEARS, SEPARATE_VALIDATION_YEARS,
)
from evaluate_geo2027_calibrated_shadow_official import load_authenticated


def rows_for_years(years):
    result=[]
    for year in years:
        for cid in range(1,197):
            state=int(cid<=34)
            # Fixed source labels and scores; tests are NOT 2027 data.
            y=state if cid%25 else 1-state
            result.append({
                "country_id":cid,
                "origin_state":state,
                "target_year":year,
                "outcome":y,
                "p_model":(.75 if state else .05)+cid/1e5,
                "p_global_markov":.7 if state else .07,
            })
    return result


class PostCalibrationCountResidualTests(unittest.TestCase):
    def test_annual_models_use_same_2024_outcomes(self):
        rows=rows_for_years([2024])
        alpha=-.5
        report=annual_metrics(rows,2024,0,alpha)
        self.assertEqual(report["n"],162)
        self.assertEqual(report["origin_state"],0)
        self.assertEqual(report["observed_transitions"],6)
        self.assertEqual(set(report["models"]),{
            "issued_country_markov","historical_odds_intercept",
            "original_global_markov",
        })
        original=report["models"]["issued_country_markov"]
        calibrated=report["models"]["historical_odds_intercept"]
        self.assertEqual(original["n"],calibrated["n"])
        self.assertEqual(original["observed_transitions"],
                         calibrated["observed_transitions"])
        self.assertLess(calibrated["expected_transitions"],
                        original["expected_transitions"])
        self.assertAlmostEqual(
            calibrated["independence_count_variance"],
            sum(logistic_shift(row["p_model"],alpha)*
                (1-logistic_shift(row["p_model"],alpha))
                for row in rows if row["origin_state"]==0),
        )
        self.assertAlmostEqual(
            original["squared_standardized_count_residual_independence"],
            (original["observed_transitions"]-original["expected_transitions"])**2/
            original["independence_count_variance"]
        )
        self.assertFalse(original["these_tails_are_valid_significance_p_values"])
        self.assertGreaterEqual(
            original["illustrative_poisson_binomial_independence_p_at_most_observed"],0
        )

    def test_same_labels_calibrator_can_improve_or_worsen_count_fit(self):
        sample=rows_for_years([2024])
        original=annual_metrics(sample,2024,1,0.)
        smaller=annual_metrics(sample,2024,1,-.8)
        # A shifted intercept must change both E and conditional variance.
        self.assertAlmostEqual(
            original["models"]["issued_country_markov"]["expected_transitions"],
            original["models"]["historical_odds_intercept"]["expected_transitions"])
        self.assertNotAlmostEqual(
            smaller["models"]["issued_country_markov"]["independence_count_variance"],
            smaller["models"]["historical_odds_intercept"]["independence_count_variance"])
        self.assertEqual(smaller["observed_transitions"],original["observed_transitions"])

    def test_revised_and_source_separated_periods_cannot_mix(self):
        alphas={0:-.2,1:-.6}
        revised=aggregate(rows_for_years(REVISED_VALIDATION_YEARS),
                          REVISED_VALIDATION_YEARS,alphas,
                          period="REVISED_2020_2023")
        external=aggregate(rows_for_years(SEPARATE_VALIDATION_YEARS),
                           SEPARATE_VALIDATION_YEARS,alphas,
                           period="SEPARATED_RELEASES_2024_2025")
        self.assertEqual(revised["0"]["n_target_years"],4)
        self.assertEqual(external["1"]["n_target_years"],2)
        self.assertEqual(external["0"]["models"]["issued_country_markov"][
            "country_years"],324)
        self.assertEqual(external["1"]["models"]["issued_country_markov"][
            "country_years"],68)
        for panel in (revised,external):
            for s in ("0","1"):
                g=panel[s]
                self.assertEqual(g["models"]["issued_country_markov"][
                    "observed_transitions"],g["models"]["historical_odds_intercept"][
                    "observed_transitions"])
                self.assertAlmostEqual(
                    g["calibrated_minus_original_weighted_brier"],
                    g["models"]["historical_odds_intercept"][
                        "brier_weighted_by_country_years"] -
                    g["models"]["issued_country_markov"][
                        "brier_weighted_by_country_years"])
        with self.assertRaisesRegex(ValueError,"fixed full evaluation"):
            aggregate(rows_for_years([2024]),[2024],alphas,
                      period="SEPARATED_RELEASES_2024_2025")
        with self.assertRaisesRegex(ValueError,"two original training-only"):
            aggregate(rows_for_years(SEPARATE_VALIDATION_YEARS),
                      SEPARATE_VALIDATION_YEARS,{0:-.2},
                      period="SEPARATED_RELEASES_2024_2025")

    def test_missing_label_duplicate_id_and_modified_forecast_fail(self):
        rows=rows_for_years([2025])
        corrupted=copy.deepcopy(rows)
        corrupted[0]["outcome"]=None
        with self.assertRaisesRegex(ValueError,"Missing future"):
            annual_metrics(corrupted,2025,1,-.3)
        corrupted=copy.deepcopy(rows)
        corrupted[0]["p_model"]=float("nan")
        with self.assertRaisesRegex(ValueError,"Invalid frozen"):
            annual_metrics(corrupted,2025,1,-.3)
        duplicated=rows+[copy.deepcopy(rows[0])]
        with self.assertRaisesRegex(ValueError,"duplicated"):
            annual_metrics(duplicated,2025,1,-.3)
        with self.assertRaisesRegex(ValueError,"outside frozen"):
            annual_metrics(rows,2027,1,-.3)
        with self.assertRaisesRegex(ValueError,"finite frozen"):
            annual_metrics(rows,2025,1,float("nan"))

    def test_issued_2027_original_and_shadow_both_still_unresolved(self):
        original,shadow,manifest=load_authenticated()
        self.assertEqual(len(original["countries"]),196)
        self.assertEqual(len(shadow["countries"]),196)
        self.assertEqual(shadow["2027_outcomes_resolved"],0)
        self.assertFalse(shadow["prospective_predictive_skill_demonstrated"])
        self.assertFalse(shadow["original_forecast_altered"])
        self.assertEqual(manifest["shadow_forecast_sha256"],
                         "1d0880f6e95e77d5e203b186e45a035676c7f724ecbe6a8b323f776b9eaa9188")


if __name__=="__main__":
    unittest.main()
