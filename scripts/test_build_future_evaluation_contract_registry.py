"""Original source, 4 endpoints, future-date and completeness guards."""
import copy
import unittest

import build_future_evaluation_contract_registry as index
from evaluate_2027_official import validate_future_source as geo_gate


class UnifiedFutureEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original,cls.geo28,cls.m28=index.authenticated_sources()
        cls.report=index.build_index(cls.original,cls.geo28,cls.m28)

    def test_exact_four_and_620_not_independent(self):
        d=self.report
        self.assertEqual(d["n_forecast_emissions"],4)
        self.assertEqual(d["first_issued_2027_country_endpoint_questions"],424)
        self.assertEqual(d["additional_issued_GEO2028_country_questions"],196)
        self.assertEqual(d["total_issued_country_endpoint_year_questions"],620)
        self.assertEqual(d["n_future_outcomes_independently_certified"],0)
        self.assertFalse(d["global_prospective_skill_demonstrated"])
        self.assertTrue(d["cross_endpoint_country_overlap_present"])
        self.assertTrue(d["cross_year_2027_2028_GEO_origin_overlap_present"])
        self.assertEqual(d["ordered_cohorts"],["GEO2027","NEWCONF2027","ACD2027","GEO2028"])
        self.assertEqual([x["issued_country_questions"] for x in d["cohorts"]],
                         [196,196,32,196])
        self.assertEqual([x["provisional_score_min_coverage"] for x in d["cohorts"]],
                         [187,187,32,196])
        self.assertEqual([x["complete_source_coverage_required_for_certification"]
                          for x in d["cohorts"]],[196,196,32,196])
        self.assertEqual([x["target_year"] for x in d["cohorts"]],[2027,2027,2027,2028])
        self.assertEqual([x["horizon_years"] for x in d["cohorts"]],[2,2,2,3])
        self.assertTrue(all(
            x["iid_country_bootstrap_disabled_in_official_candidate_evaluator"] is True
            and x["statistical_confidence_interval_claimed"] is False
            for x in d["cohorts"]))
        self.assertEqual(
            [x["sharp_missing_label_brier_region_available"] for x in d["cohorts"]],
            [True,True,False,False])
        self.assertTrue(all(x["source_independently_verified_full_future_release"] is False
                            and x["future_country_labels_certified"]==0
                            and x["official_scores_certified"] is False
                            and x["candidate_scores_available_now"] is False
                            for x in d["cohorts"]))

    def test_new_geo2028_is_not_fake_fourth_2027_endpoint(self):
        old={x["cohort"]:x for x in self.report["cohorts"]}
        self.assertEqual(old["GEO2027"]["source_family"],
                         old["GEO2028"]["source_family"])
        self.assertTrue(old["GEO2028"]["depends_on_same_2025_origin_as_GEO2027"])
        self.assertEqual(old["GEO2027"]["first_eligible_source_date"],"2028-01-01")
        self.assertEqual(old["GEO2028"]["first_eligible_source_date"],"2029-01-01")
        self.assertNotEqual(old["GEO2028"]["forecast_sha256"],
                            old["GEO2027"]["forecast_sha256"])
        self.assertNotEqual(old["ACD2027"]["event_definition"],
                            old["NEWCONF2027"]["event_definition"])

    def test_source_frozen_2027_and_2028_denom_and_identity_fail_closed(self):
        changes=[
            ("old",lambda d:d.__setitem__("n_unique_country_endpoint_rows",425)),
            ("old",lambda d:d["rows"][0].__setitem__("observed_2027",1)),
            ("old",lambda d:d["cohorts"]["GEO2027"].__setitem__("primary_model","p_other")),
            ("geo",lambda d:d.__setitem__("2028_outcomes_resolved",1)),
            ("geo",lambda d:d["countries"][0].__setitem__(
                "p_issued_geo2027_2step_for_temporal_comparison_only",.1)),
            ("manifest",lambda d:d.__setitem__("forecast_sha256","0"*64)),
            ("manifest",lambda d:d.__setitem__("independently_notarized",True)),
        ]
        for tag,mutate in changes:
            orig=copy.deepcopy(self.original)
            geo=copy.deepcopy(self.geo28)
            man=copy.deepcopy(self.m28)
            mutate({"old":orig,"geo":geo,"manifest":man}[tag])
            with self.subTest(tag=tag):
                with self.assertRaises(ValueError):
                    index.build_index(orig,geo,man)

    def test_iid_bootstrap_cannot_reappear_in_evaluator_or_index(self):
        self.assertTrue(index.ensure_future_gates())
        self.assertNotIn("bootstrap_interval",vars(index.geo27))
        self.assertNotIn("bootstrap_delta",vars(index.new27))
        self.assertNotIn("random",vars(index.geo27))
        self.assertNotIn("random",vars(index.new27))
        for c in self.report["cohorts"]:
            self.assertTrue(c["iid_country_bootstrap_disabled_in_official_candidate_evaluator"])
            self.assertFalse(c["statistical_confidence_interval_claimed"])
            self.assertNotIn("genera un bootstrap",c["experimental_interval_warning"])

    def test_original_evaluators_reject_stale_2027_source_vintages(self):
        self.assertTrue(index.ensure_future_gates())
        sha="a"*64
        for vintage in ("261","271"):
            with self.assertRaisesRegex(ValueError,"28.1"):
                geo_gate("https://ucdp.uu.se/downloads/organizedviolencecy/"
                         "organizedviolencecy-"+vintage+"-csv.zip",
                         sha,"2028-10-01")
        self.assertTrue(geo_gate("https://ucdp.uu.se/downloads/organizedviolencecy/"
                                 "organizedviolencecy-281-csv.zip",sha,"2028-10-01"))
        with self.assertRaises(ValueError):
            geo_gate("https://ucdp.uu.se.evil.test/downloads/organizedviolencecy/"
                     "organizedviolencecy-281-csv.zip",sha,"2028-10-01")


if __name__=="__main__":
    unittest.main()
