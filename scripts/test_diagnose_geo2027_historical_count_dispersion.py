"""Synthetic old-year panels only; no source or 2027 target outcomes are fabricated."""
import copy
import unittest

from backtest_archived_country_vintages import SOURCES
from diagnose_geo2027_historical_count_dispersion import (
    REVISED_TARGET_YEARS, SEPARATED_TARGET_YEARS,
    diagnose, group_year, panel,
)


def make_toy(years, two_vintages=False):
    result=[]
    for year in years:
        active=37 if year==2024 else 34 if year==2025 else 35
        stays=31 if year==2024 else 30 if year==2025 else 30
        for cid in range(1,197):
            state=int(cid<=active)
            new_event=int(active < cid <= active+4)
            outcome=int(cid<=stays or new_event)
            result.append({
                "target_year":year,
                "country_id":cid,
                "origin_state":state,
                "outcome":outcome,
                "p_model": .82 if state else .025,
                "p_global_markov": .75 if state else .05,
            })
    return result


class CountDispersionDiagnosticsTests(unittest.TestCase):
    def test_yearly_expected_count_var_and_residual(self):
        source=make_toy([2019])
        entry=group_year(source,2019,0)
        active=group_year(source,2019,1)
        self.assertEqual(entry["n"],161)
        self.assertEqual(entry["observed_transitions"],4)
        self.assertAlmostEqual(entry["expected_transitions_given_original_model"],161*.025)
        self.assertAlmostEqual(entry["variance_under_country_independence"],
                               161*.025*.975)
        self.assertEqual(active["n"],35)
        self.assertEqual(active["observed_transitions"],5)
        self.assertAlmostEqual(active["expected_transitions_given_original_model"],
                               35*.18)
        self.assertGreaterEqual(entry["count_pearson_contribution"],0)
        self.assertGreaterEqual(active["count_pearson_contribution"],0)

    def test_pooled_year_only_metrics_not_country_tables(self):
        source=make_toy([2018,2019])
        report=panel(source,(2018,2019))
        self.assertEqual(set(report),{"0","1"})
        self.assertEqual(report["0"]["n_country_years"],322)
        self.assertEqual(report["1"]["n_country_years"],70)
        self.assertEqual(report["0"]["observed_transitions"],8)
        self.assertEqual(report["1"]["observed_transitions"],10)
        self.assertEqual(len(report["0"]["yearly_aggregate_count_residuals"]),2)
        self.assertIn("pearson_dispersion_ratio_global_markov",report["0"])
        self.assertNotIn("country_id",str(report))

    def test_ex_ante_state_unobserved_outcome_and_duplicates_fail(self):
        source=make_toy([2019])
        bad=copy.deepcopy(source)
        bad[0]["outcome"]=None
        with self.assertRaisesRegex(ValueError, "Unresolved"):
            group_year(bad,2019,1)
        bad=copy.deepcopy(source)
        bad[0]["p_model"]=float("nan")
        with self.assertRaisesRegex(ValueError, "Invalid"):
            group_year(bad,2019,1)
        bad=copy.deepcopy(source)
        bad.append(dict(bad[0]))
        with self.assertRaisesRegex(ValueError, "duplicated"):
            group_year(bad,2019,1)
        with self.assertRaisesRegex(ValueError, "Unknown"):
            group_year(source,2019,0,"new_model")
        with self.assertRaisesRegex(ValueError, "Invalid time"):
            panel(source,[2019,2019])

    def test_12_revised_and_two_release_split_explicitly_unverified(self):
        rolled=make_toy(REVISED_TARGET_YEARS)
        external=make_toy(SEPARATED_TARGET_YEARS)
        self.assertEqual(len(external),392)
        self.assertEqual(sum(r["outcome"] for r in external),69)
        fingerprint={k:v["sha256"] for k,v in SOURCES.items()}
        report=diagnose(rolled,external,fingerprint)
        self.assertEqual(len(report["rolling_origin_reference_years"]),12)
        self.assertEqual(len(report["separate_release_target_years"]),2)
        self.assertFalse(report["structural_cross_country_correlation_identified"])
        self.assertFalse(report["source_release_dates_independently_notarized"])
        self.assertFalse(report["independent_forecast_skill_demonstrated"])
        self.assertFalse(report["2027_forecast_and_alerts_changed"])
        self.assertEqual(report["2027_outcomes_observed"],0)
        self.assertEqual(report["cross_release_2_year_count_diagnostics"]["0"][
            "number_of_target_years"],2)
        changed=dict(fingerprint)
        changed["26.1"]="not-official"
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            diagnose(rolled,external,changed)
        altered=copy.deepcopy(external)
        altered[0]["outcome"]=1-altered[0]["outcome"]
        with self.assertRaisesRegex(ValueError, "holdout changed"):
            diagnose(rolled,altered,fingerprint)


if __name__=="__main__":
    unittest.main()
