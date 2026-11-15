"""No UCDP 2026 source exists yet: exercise attribution on synthetic histories ONLY."""
from datetime import date
import copy
import math
import unittest

import forecast_2027_statebased as geo27
import prepare_geo2028_three_year as geo28_original
import prepare_geo2028_origin2026 as future
import decompose_geo2028_origin2026_update as attribution
from test_prepare_geo2028_origin2026 import new_origin_data,csv_rows,archive,pin


def fake_original_2025():
    from test_forecast_2027_statebased import toy
    records,names=toy()
    row27,_=geo27.estimate_from_history(records,names)
    valid27={
        "forecast_id":geo27.PROTOCOL_ID,
        "source":{"sha256":geo28_original.SOURCE_SHA,"data_last_year":2025},
        "target":{"year":2027},
        "countries":row27,
    }
    rows28,_=geo28_original.build_from_records(records,names,valid27)
    first={
        "schema":geo28_original.SCHEMA,
        "forecast_id":geo28_original.PROTOCOL_ID,
        "origin":{"year":2025,"official_sha256":geo28_original.SOURCE_SHA},
        "target":{"year":2028},
        "protocol":{"horizon_years":3},
        "2028_outcomes_resolved":0,
        "prospective_predictive_skill_demonstrated":False,
        "countries":rows28,
    }
    return first


def synthetic_inputs():
    records,names=new_origin_data()
    original=fake_original_2025()
    raw=archive(csv_rows(records,names))
    candidate=future.build_candidate(raw,pin(raw),original,as_of=date(2027,8,1))
    return records,names,original,candidate


class RolloverAttributionExAnteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records,cls.names,cls.original,cls.new=synthetic_inputs()

    def test_exact_three_component_telescope_for_all_matched_countries(self):
        x=attribution.decompose_for_source(self.records,self.names,self.original,self.new)
        self.assertEqual(x["fully_matched_country_count"],196)
        self.assertEqual(x["original_2025_origin_n"],196)
        self.assertEqual(x["new_2026_origin_27_1_n"],196)
        self.assertEqual(x["matched_2025_state_revision_count"],0)
        self.assertEqual(x["2028_official_outcomes_observed"],0)
        self.assertFalse(x["model_probabilities_origin2026_publicly_issued"])
        self.assertFalse(x["source_pin_is_independently_certified"])
        self.assertFalse(x["prospective_skill_demonstrated"])
        self.assertTrue(x["decomposition_is_order_dependent_and_not_causal"])
        self.assertFalse(x["country_years_independent_replications"])
        self.assertNotIn("country_2028_truth",x)
        self.assertEqual(len(x["country_decomposition"]),196)
        self.assertTrue(any(abs(row["2026_observed_state_surprise_component"])>1e-6
                            for row in x["country_decomposition"]))
        self.assertTrue(any(abs(row["2026_model_refit_component"])>1e-6
                            for row in x["country_decomposition"]))
        for row in x["country_decomposition"]:
            with self.subTest(country=row["country_id"]):
                self.assertLess(abs(row["vintage_revision_plus_population_component"]),2e-12)
                component_sum=sum(row[k] for k in (
                    "vintage_revision_plus_population_component",
                    "2026_observed_state_surprise_component",
                    "2026_model_refit_component"))
                self.assertAlmostEqual(component_sum,
                                       row["total_forecast_change_D_minus_A"],
                                       places=10)
                self.assertAlmostEqual(
                    row["D_p2028_new_origin2026_refit_h2"]-
                    row["A_p2028_first_issued_2025_h3"],
                    row["total_forecast_change_D_minus_A"],
                    places=10)
                self.assertEqual(row["2025_state_first_issued_source_26_1"],
                                 row["2025_state_revised_source_27_1"])
        self.assertLess(abs(x["baseline_vintage_population_component"]),2e-12)
        self.assertAlmostEqual(
            x["baseline_total_change"],
            x["baseline_vintage_population_component"]+
            x["baseline_rolling_window_new_data_component"],places=10)

    def test_revisions_are_separated_from_new_observations_and_kernel_refit(self):
        records=copy.deepcopy(self.records)
        records[2][2025]=1-records[2][2025]  # late revision of past label
        records[5][2011]=1-records[5][2011]  # revision of earlier transition
        raw=archive(csv_rows(records,self.names))
        candidate=future.build_candidate(raw,pin(raw),self.original,
                                         as_of=date(2027,8,1))
        result=attribution.decompose_for_source(
            records,self.names,self.original,candidate)
        self.assertEqual(result["matched_2025_state_revisions"],[2])
        self.assertEqual(result["matched_2025_state_revision_count"],1)
        # Other countries can change due to GLOBAL transition revisions:
        # "vintage" is NOT exclusively each country's 2025 state revision.
        self.assertTrue(any(abs(r["vintage_revision_plus_population_component"])>1e-7
                            for r in result["country_decomposition"]))
        self.assertEqual(result["fully_matched_country_count"],196)
        for item in result["country_decomposition"]:
            self.assertAlmostEqual(
                sum(item[k] for k in (
                    "vintage_revision_plus_population_component",
                    "2026_observed_state_surprise_component",
                    "2026_model_refit_component")),
                item["total_forecast_change_D_minus_A"],places=10)
        self.assertNotEqual(
            result["original_global_baseline_2021_2025_26_1"],
            result["revised_global_baseline_2021_2025_27_1"])

    def test_dynamic_cohorts_remain_paired_only_on_matched_gwno(self):
        records=copy.deepcopy(self.records)
        names=copy.deepcopy(self.names)
        del records[1][2026]
        records[197]={y:0 for y in range(1989,2027)}
        names[197]="Synthetic Country 197"
        raw=archive(csv_rows(records,names))
        candidate=future.build_candidate(raw,pin(raw),self.original,
                                         as_of=date(2027,8,1))
        result=attribution.decompose_for_source(records,names,self.original,candidate)
        self.assertEqual(result["fully_matched_country_count"],195)
        self.assertEqual(result["new_origin_only_country_ids"],[197])
        self.assertEqual(result["original_origin_no_longer_in_2026_cohort"],[1])
        self.assertEqual(result["revised_2025_origin_27_1_n"],197)
        self.assertEqual(len(result["country_decomposition"]),195)
        self.assertEqual(result["triple_match_excluded_from_2025_revision_cohort"],[])

    def test_markov_state_surprise_is_precisely_conditional_2026_news(self):
        x=attribution.decompose_for_source(self.records,self.names,self.original,self.new)
        kernels,reference,_=attribution._fit_source_year(self.records,self.names,2025)
        for r in x["country_decomposition"]:
            cid=r["country_id"];q=kernels[cid]
            p1=attribution.nstep(self.records[cid][2025],q,1)
            f0=attribution.nstep(0,q,2)
            f1=attribution.nstep(1,q,2)
            surprise=(self.records[cid][2026]-p1)*(f1-f0)
            self.assertAlmostEqual(r["2026_observed_state_surprise_component"],
                                   surprise,places=10)
            self.assertAlmostEqual(
                r["B_p2028_revised_2025_h3"],
                (1-p1)*f0+p1*f1,places=10)
            self.assertEqual(reference[cid]["last_observed_state_2025"],
                             self.records[cid][2025])

    def test_source_and_candidate_tampering_are_rejected(self):
        bad=copy.deepcopy(self.new)
        bad["countries"][0]["p_model"]+=.01
        with self.assertRaisesRegex(ValueError,"not source reproducible"):
            attribution.decompose_for_source(
                self.records,self.names,self.original,bad)
        bad=copy.deepcopy(self.new)
        bad["model_fit"]["cohort_n"]=195
        with self.assertRaisesRegex(ValueError,"not source reproducible"):
            attribution.decompose_for_source(
                self.records,self.names,self.original,bad)
        original=copy.deepcopy(self.original)
        original["origin"]["official_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"not validated"):
            attribution.decompose_for_source(
                self.records,self.names,original,self.new)
        original=copy.deepcopy(self.original)
        original["prospective_predictive_skill_demonstrated"]=True
        with self.assertRaisesRegex(ValueError,"not validated"):
            attribution.decompose_for_source(
                self.records,self.names,original,self.new)
        badrecords=copy.deepcopy(self.records)
        badrecords[3][2028]=1
        with self.assertRaisesRegex(ValueError,"contaminated"):
            attribution.decompose_for_source(
                badrecords,self.names,self.original,self.new)
        bad=copy.deepcopy(self.new)
        bad["n_issued_country_questions"]=196
        with self.assertRaisesRegex(ValueError,"Unsafe chronology"):
            attribution.decompose_for_source(
                self.records,self.names,self.original,bad)

    def test_reject_future_causal_or_independent_sample_claims_by_construction(self):
        x=attribution.decompose_for_source(self.records,self.names,self.original,self.new)
        self.assertEqual(x["method"],attribution.METHOD)
        self.assertFalse(x["country_years_independent_replications"])
        self.assertTrue(x["decomposition_is_order_dependent_and_not_causal"])
        self.assertEqual(x["original_source_release"],"26.1")
        self.assertEqual(x["new_source_release"],"27.1")
        self.assertEqual(x["forecast_target_year"],2028)
        self.assertEqual(x["origin_2025_horizon_years"],3)
        self.assertEqual(x["origin_2026_horizon_years"],2)
        self.assertIn("NOT independent",x["methodological_caveat"])
        self.assertNotIn("p_value",x)
        self.assertNotIn("confidence_interval",x)
        self.assertEqual(x["first_issued_GEO2028_2025_origin_sha256"],
                         attribution.PRIOR_SHA)
        self.assertEqual(attribution.origin.canonical(x),
                         attribution.origin.canonical(
                             attribution.decompose_for_source(
                                 self.records,self.names,self.original,self.new)))


if __name__=="__main__":
    unittest.main()
