#!/usr/bin/env python3
"""Adversarial tests: source identity, confusion matrix, zero-rule, leakage status."""
import json
import unittest
from audit_candidate_ged_annual_null_baseline import (
    AuditError, SOURCE, build_report, check_cell, metrics
)

class AnnualNullBaselineTests(unittest.TestCase):
    def test_primary_exact_against_zero_rule(self):
        report=build_report()
        rows={(r["threshold_candidate_and_ged"],r["horizon_days"]):r
              for r in report["results"]}
        self.assertEqual(len(rows),8)
        self.assertEqual(len(rows[(5,30)]["annual_breakdown"]),4)
        self.assertEqual(rows[(5,30)]["candidate_only"],5)
        self.assertEqual(rows[(5,30)]["ged_only"],0)
        self.assertEqual(rows[(5,30)]["candidate_minus_always_negative_agreement_pp"],0)
        self.assertEqual(rows[(5,90)]["candidate_only"],15)
        self.assertEqual(rows[(5,90)]["ged_only"],2)
        self.assertEqual(rows[(5,90)]["candidate_minus_always_negative_agreement_pp"],-0.7788162)
        self.assertTrue(report["not_model_accuracy"])
        self.assertTrue(report["not_asof_certified"])
        self.assertEqual(report["new_forecasts_issued"],0)

    def test_example_strong_class_imbalance(self):
        got=metrics({"both_positive":5,"candidate_only":5,
                     "ged_only":0,"both_negative":632,
                     "n_at_risk":642,"candidate_positive":10,
                     "ged_positive":5,"disagreements":5})
        self.assertEqual(got["candidate_annual_agreement"],0.99221184)
        self.assertEqual(got["always_negative_annual_agreement"],0.99221184)
        self.assertEqual(got["candidate_positive_matching_annual_share"],0.5)
        self.assertEqual(got["candidate_annual_recall"],1.0)

    def test_reject_invalid_marginal_and_negative(self):
        cell={"both_positive":5,"candidate_only":5,"ged_only":0,
              "both_negative":632,"n_at_risk":642,"candidate_positive":10,
              "ged_positive":5,"disagreements":5}
        for name,wrong in (("n_at_risk",643),("candidate_positive",11),
                           ("ged_positive",6),("disagreements",4),
                           ("both_negative",-1),("both_positive",True)):
            altered={**cell,name:wrong}
            with self.subTest(name=name),self.assertRaises(AuditError):
                check_cell(altered)

    def test_reject_source_even_if_semantics_unchanged(self):
        raw=SOURCE.read_bytes()
        with self.assertRaisesRegex(AuditError,"SHA-256"):
            build_report(raw+b" ")

    def test_no_fake_recall_when_no_annual_positive(self):
        m=metrics({"both_positive":0,"candidate_only":2,
                   "ged_only":0,"both_negative":159,
                   "n_at_risk":161,"candidate_positive":2,
                   "ged_positive":0,"disagreements":2})
        self.assertIsNone(m["candidate_annual_recall"])
        self.assertIsNone(m["balanced_annual_agreement"])
        self.assertEqual(m["candidate_positive_matching_annual_share"],0)

if __name__=="__main__":
    unittest.main()
