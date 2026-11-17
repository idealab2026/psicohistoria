"""Adversarial temporal-as-of source eligibility tests; no fake forecast issuance."""
from __future__ import annotations

import copy
import json
import unittest

from audit_geo2027_global_only_matched_issue import ISSUE
from backtest_archived_country_vintages import SOURCES
from audit_geo_h2_historical_asof_sources import (
    CODEBOOKS, ROLLING, TWO_FOLD, _avg_folds, audit, classify,
    official_catalog_year_versions,
)


class TemporalProvenanceGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rolling=json.loads(ROLLING.read_text(encoding="utf-8"))
        cls.twofold=json.loads(TWO_FOLD.read_text(encoding="utf-8"))
        cls.issue=json.loads(ISSUE.read_text(encoding="utf-8"))
        cls.hashes={version:"a"*64 for version in CODEBOOKS}
        cls.links={version:[SOURCES[version]["url"]]
                   for version in ("23.1","24.1","25.1")}
        cls.catalog=["23.1","24.1","25.1"]

    def test_official_catalog_entire_section_not_only_known_urls(self):
        html=("""
          <h2>Other dataset</h2><p>version 22.1: CSV</p>
          <h2>UCDP Country-Year Dataset on Organized Violence within
          Country Borders</h2><p>version 25.1: CSV</p>
          <p>version 24.1: CSV</p><p>version 23.1: EXCEL</p>
          <h2>Some other dataset</h2><p>version 22.1: CSV</p>
        """)
        self.assertEqual(official_catalog_year_versions(html),
                         ["23.1","24.1","25.1"])
        with_older=html.replace(
            "<p>version 23.1: EXCEL</p>",
            "<p>version 23.1: EXCEL</p><p>version 22.1: CSV</p>")
        self.assertIn("22.1",official_catalog_year_versions(with_older))
        with self.assertRaises(ValueError):
            official_catalog_year_versions("<h2>Missing</h2>")

    def test_strict_pseudo_origin_not_temporally_valid_by_codebook_year(self):
        for year in range(2014,2026):
            original=next(f for f in self.rolling["primary_unique_year_series"]["folds"]
                          if f["target_year"]==year)
            decision=classify(original["origin_year"],year,
                              original["origin_release"])
            self.assertTrue(decision["source_year_after_simulated_origin"])
            self.assertFalse(decision["origin_year_contemporaneous_file_proven"])
            self.assertFalse(decision["actual_origin_issue_timestamp_notarized"])
            self.assertFalse(decision["exact_original_file_bytes_notarized_before_target"])

    def test_distinct_yearly_temporal_categories_and_no_false_prospective_claim(self):
        for year in range(2014,2026):
            rel="23.1" if year<=2024 else "24.1"
            record=classify(year-2,year,rel)
            expected=("CODEBOOK_YEAR_AFTER_TARGET" if year<=2022
                      else "CODEBOOK_YEAR_EQUALS_TARGET_EXACT_DATE_UNKNOWN"
                      if year==2023 else
                      "CODEBOOK_YEAR_BEFORE_TARGET_NOT_BYTE_NOTARIZED")
            self.assertEqual(record["codebook_year_relative_to_target"],expected)
        with self.assertRaises(ValueError):
            classify(2022,2024,"22.1")
        with self.assertRaises(ValueError):
            classify(2022,2023,"23.1")
        with self.assertRaises(ValueError):
            classify(2024,2026,"23.1")

    def test_real_frozen_12year_score_sign_reversal_and_anchor_stability(self):
        report=audit(self.rolling,self.twofold,self.issue,
                     self.hashes,self.links,self.catalog)
        self.assertEqual(report["genuine_contemporaneously_notarized_historical_issue_count"],0)
        self.assertIsNone(report["strict_asof_rolling_forecast_skill_estimate"])
        self.assertEqual(report["n_target_years_with_prior_year_codebook_but_no_file_time_hash"],2)
        self.assertEqual(report["n_target_years_before_own_source_codebook_year"],9)
        self.assertEqual(report["n_target_years_same_as_source_codebook_year_unresolved"],1)
        self.assertEqual(len(report["year_level_only_eligibility"]),12)
        results=report["score_decomposition_by_source_timing"]
        self.assertEqual(results["not_pre_target_year_based"]["target_years"],
                         list(range(2014,2024)))
        self.assertEqual(results["pre_target_year_only_nonnotarized"]["target_years"],
                         [2024,2025])
        self.assertLess(results["complete_rolling_retrospective_not_asof"]["best_label"][
            "four_state_minus_original_delta_brier"],0)
        self.assertLess(results["not_pre_target_year_based"]["best_label"][
            "four_state_minus_original_delta_brier"],0)
        self.assertGreater(results["pre_target_year_only_nonnotarized"]["best_label"][
            "four_state_minus_original_delta_brier"],0)
        self.assertAlmostEqual(results["pre_target_year_only_nonnotarized"]["best_label"][
            "four_state_minus_original_delta_brier"],0.002365272073254196,places=10)

    def test_malformed_claim_about_earlier_official_version_fails_closed(self):
        older=self.catalog+["22.1"]
        with self.assertRaisesRegex(ValueError,"Prior published source audit"):
            audit(self.rolling,self.twofold,self.issue,
                  self.hashes,self.links,older)
        corrupted=copy.deepcopy(self.rolling)
        corrupted["source_archives_sha256"]["23.1"]="0"*64
        with self.assertRaises(ValueError):
            audit(corrupted,self.twofold,self.issue,
                  self.hashes,self.links,self.catalog)
        with self.assertRaises(ValueError):
            audit(self.rolling,self.twofold,self.issue,
                  {"23.1":"bad","24.1":"a"*64},self.links,self.catalog)
        bad_issue=copy.deepcopy(self.issue)
        bad_issue["official_2027_outcomes_resolved"]=196
        with self.assertRaises(ValueError):
            audit(self.rolling,self.twofold,bad_issue,
                  self.hashes,self.links,self.catalog)

    def test_unbalanced_duplicate_years_are_not_independent_sample(self):
        folds=self.rolling["primary_unique_year_series"]["folds"]
        with self.assertRaises(ValueError):
            _avg_folds([], "best")
        with self.assertRaises(ValueError):
            _avg_folds([folds[0],folds[0]], "best")
        self.assertEqual(_avg_folds(folds[:10],"best")["country_year_n"],1960)
        self.assertEqual(_avg_folds(folds[-2:],"best")["country_year_n"],392)


if __name__=="__main__":
    unittest.main()
