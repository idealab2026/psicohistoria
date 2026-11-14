"""Offline fail-closed tests for historical annual residual de-bias diagnostics."""
import copy
import math
import unittest

import diagnose_historical_geo_newconf_year_counts as study


def make_year(year,positives,prob=.025):
    if not 0<=positives<=196:
        raise ValueError("Invalid toy incidence")
    return [
        {"country":str(cid),"target_year":year,"origin_year":year-2,
         "horizon":2,"outcome":int(cid<=positives),
         "activity_country":prob,"global_last5":prob+.005}
        for cid in range(1,197)
    ]


class HistoricalAnnualCountTests(unittest.TestCase):
    def test_count_expected_variance_and_residual_are_exact(self):
        rows=make_year(2016,6,prob=.02)
        s=study.count_residual(rows,2016,"activity_country")
        self.assertEqual(s["observed_newconf_country_years"],6)
        self.assertAlmostEqual(s["expected_count_from_origin_only_model"],196*.02)
        self.assertAlmostEqual(s["independence_count_variance_for_model"],
                               196*.02*.98)
        z=(6-196*.02)/math.sqrt(196*.02*.98)
        self.assertAlmostEqual(s["standardized_count_residual"],z)
        self.assertAlmostEqual(s["squared_standardized_count_residual"],z*z)
        self.assertEqual(s["source_issues_outcomes_observed_2027"],0)

    def test_decomposition_bias_squared_plus_centered_component(self):
        seq=[{"target_year":2016+i,"standardized_count_residual":float(z)}
             for i,z in enumerate([1,2,3,4,5,6,7])]
        result=study.annual_decomposition(
            seq,zkey="standardized_count_residual",first_target_year=2016,
            expected_years=7,forward_min_history=3)
        self.assertAlmostEqual(result["mean_signed_standardized_count_residual"],4)
        self.assertAlmostEqual(result["mean_squared_directional_bias_component"],16)
        self.assertAlmostEqual(result["mean_centered_squared_year_residual"],4)
        self.assertAlmostEqual(result["mean_squared_standardized_count_residual"],20)
        self.assertAlmostEqual(result["fraction_of_raw_squared_residual_due_to_mean_bias"],.8)
        self.assertEqual(result["positive_count_residual_years"],7)
        f=result["forward_only_pseudo_bias_adjusted_diagnostics"]
        self.assertEqual(f["n_scored_years"],4)
        self.assertEqual(f["first_scored_target_year"],2019)
        self.assertAlmostEqual(f["annual_adjustment_trace"][0][
            "count_bias_estimate_from_earlier_target_years_only"],2)
        self.assertAlmostEqual(f["annual_adjustment_trace"][0][
            "posthoc_bias_adjusted_standardized_residual"],2)
        self.assertFalse(f["independently_issued_historical_forecasts"])

    def test_year_scoping_horizon_duplicates_and_unresolved_rejected(self):
        rows=make_year(2024,1)
        for bad in (
            rows[:-1],
            rows[:-1]+[copy.deepcopy(rows[0])],
            [{**r,"target_year":2027} if i==0 else r
             for i,r in enumerate(rows)],
            [{**r,"horizon":1} if i==0 else r for i,r in enumerate(rows)],
            [{**r,"outcome":None} if i==0 else r for i,r in enumerate(rows)],
            [{**r,"activity_country":float("nan")} if i==0 else r
             for i,r in enumerate(rows)],
            [{**r,"global_last5":1} if i==0 else r
             for i,r in enumerate(rows)],
        ):
            with self.assertRaises(ValueError):
                study.count_residual(bad,2024,"activity_country" if
                                     bad[0].get("global_last5")!=1 else "global_last5")
        with self.assertRaisesRegex(ValueError,"Unsupported"):
            study.count_residual(rows,2023,"activity_country")
        with self.assertRaisesRegex(ValueError,"Unsupported"):
            study.count_residual(rows,2024,"p_model")

    def test_future_target_year_in_revised_block_fails(self):
        seq=[{"target_year":2016+i,"standardized_count_residual":.1}
             for i in range(7)]
        seq[2]["target_year"]=2027
        with self.assertRaisesRegex(ValueError,"incomplete"):
            study.annual_decomposition(seq,zkey="standardized_count_residual",
                                       first_target_year=2016,
                                       expected_years=7,forward_min_history=3)
        seq=[{"target_year":2016+i,"standardized_count_residual":.1}
             for i in range(7)]
        seq[2]["standardized_count_residual"]=float("inf")
        with self.assertRaisesRegex(ValueError,"Invalid source-derived"):
            study.annual_decomposition(seq,zkey="standardized_count_residual",
                                       first_target_year=2016,
                                       expected_years=7,forward_min_history=3)
        with self.assertRaisesRegex(ValueError,"year panel"):
            study.annual_decomposition(seq[:1],zkey="standardized_count_residual",
                                       first_target_year=2016,
                                       expected_years=7,forward_min_history=3)

    def test_separate_release_is_not_sufficient_for_covariance(self):
        e=study._cross_year_only(
            [{"target_year":2024,"standardized_count_residual":-.3}],
            prior_bias=-.5,zkey="standardized_count_residual")
        self.assertEqual(e["n_separate_release_target_years"],1)
        self.assertAlmostEqual(e["annual"][0]["posthoc_bias_centered_residual"],.2)
        self.assertTrue(e["cannot_estimate_covariance_from_one_or_two_target_years"])
        with self.assertRaises(ValueError):
            study._cross_year_only([],0.,"standardized_count_residual")

    def test_geo_frozen_yearly_count_reanalysis_reproduces_existing_study(self):
        geo=study.geo_existing_frozen_report()
        self.assertEqual(set(geo),{"0","1"})
        for state in geo:
            z=geo[state]["revised_2012_2023"]
            s=geo[state]["source_separated_2024_2025"]
            self.assertEqual(z["n_target_years"],12)
            self.assertEqual(s["n_separate_release_target_years"],2)
            self.assertTrue(s["cannot_estimate_covariance_from_one_or_two_target_years"])
            self.assertAlmostEqual(
                z["mean_squared_standardized_count_residual"],
                z["mean_squared_directional_bias_component"]+
                z["mean_centered_squared_year_residual"],places=12)

    def test_newconf_pinned_196_country_counts_fail_closed(self):
        # Official 23.1 pseudo-origin target positives 2016..22 are fixed.
        year_positives=(6,3,1,5,1,0,2)
        annual={
            model:[study.count_residual(make_year(y,k),y,model)
                   for y,k in zip(study.TARGET_YEARS,year_positives)]
            for model in study.NEWCONF_MODELS
        }
        ext={
            model:[study.count_residual(make_year(2024,1),2024,model)]
            for model in study.NEWCONF_MODELS
        }
        geo=study.geo_existing_frozen_report()
        meta={"23.1":"a","25.1":"b","activity_23.1":"c"}
        report=study.diagnose_from_annual(annual,ext,geo,meta)
        self.assertEqual(report["n_2027_country_endpoint_questions_preserved"],424)
        self.assertEqual(report["2027_outcomes_used"],0)
        self.assertFalse(report["structural_country_correlation_estimated"])
        self.assertFalse(report["sampled_target_years_are_independent_or_confirmatory"])
        altered=copy.deepcopy(annual)
        altered["activity_country"][0]["observed_newconf_country_years"]=7
        with self.assertRaisesRegex(ValueError,"fixed historical sample"):
            study.diagnose_from_annual(altered,ext,geo,meta)
        altered=copy.deepcopy(ext)
        altered["activity_country"][0]["target_year"]=2023
        with self.assertRaisesRegex(ValueError,"2024"):
            study.diagnose_from_annual(annual,altered,geo,meta)


if __name__=="__main__":
    unittest.main()
