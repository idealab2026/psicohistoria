#!/usr/bin/env python3
"""Fail-closed unit controls for Uganda 2022 UCDP state-based eligibility."""
import copy
import unittest
from pathlib import Path
from unittest.mock import patch

import audit_geo_uganda2022_statebased_eligibility as m


class UCDPDyadEligibility(unittest.TestCase):
    def setup_sources(self):
        pair={
            "pair_ged_ids":[444764,444765],
            "official_type1_best_total":25,
            "same_dyad_id":True,
            "common_identical_normalized_UCDP_bibliographic_citations_n":2,
            "duplicate_event_proven":False
        }
        import json
        return json.loads(m.REVIEW_PATH.read_text()),pair

    def test_one_original_source_not_four_independent_press_witnesses(self):
        review,pair=self.setup_sources()
        res=m.verify_manual_evidence(review,pair)
        self.assertEqual(res["total_publications_reviewed"],8)
        self.assertEqual(res["nonstate_original_witness_groups_verified"],0)
        self.assertEqual(res["separate_reported_persons_n"],2)
        self.assertIn("UGANDA_STATE_JUNE_24_ENANGA",
                      res["publication_origin_groups"])

    def test_june_press_source_origin_cannot_change(self):
        review,pair=self.setup_sources()
        for item in review["sources"]:
            if item["id"]=="softpower_june":
                item["origin_group"]="NEW_INDEPENDENT_WITNESS"
        with self.assertRaises(ValueError):
            m.verify_manual_evidence(review,pair)

    def test_wrong_source_host_rejected(self):
        review,pair=self.setup_sources()
        review["sources"][0]["url"]="https://example.com/unverified"
        with self.assertRaises(ValueError):
            m.verify_manual_evidence(review,pair)

    def test_witness_independence_claim_blocked(self):
        review,pair=self.setup_sources()
        review["independently_verified_combatant_or_conflict_dyad"]=True
        with self.assertRaises(ValueError):
            m.verify_manual_evidence(review,pair)

    def test_event_identity_must_remain_separate_and_unresolved(self):
        review,pair=self.setup_sources()
        review["event_claims"][0]["battle_related_classification"]="VERIFIED"
        with self.assertRaises(ValueError):
            m.verify_manual_evidence(review,pair)

    def test_unapproved_event_id_rejected(self):
        review,pair=self.setup_sources()
        review["event_claims"][0]["GED_event_id"]=444763
        with self.assertRaises(ValueError):
            m.verify_manual_evidence(review,pair)

    def test_actual_forecast_cannot_be_reclassified_from_a_press_claim(self):
        review,pair=self.setup_sources()
        review["revision_of_UCDP_or_GEO_labels"]=True
        with self.assertRaises(ValueError):
            m.verify_manual_evidence(review,pair)

    def test_two_news_reports_are_not_two_original_sources(self):
        review,pair=self.setup_sources()
        first=next(x for x in review["sources"] if x["id"]=="urn_june")
        second=next(x for x in review["sources"] if x["id"]=="softpower_june")
        self.assertEqual(first["origin_group"],second["origin_group"])
        m.verify_manual_evidence(review,pair)

    def test_same_state_source_different_officer_not_independent_family(self):
        review,pair=self.setup_sources()
        res=m.verify_manual_evidence(review,pair)
        self.assertEqual(len(res["publication_origin_groups"]),2)
        self.assertEqual(res["nonstate_original_witness_groups_verified"],0)

    def test_25_vs_24_and_23_mathematically_not_actual_recode(self):
        rows=[{"GED_event_id":444764,"best":1},
              {"GED_event_id":444765,"best":1}]
        self.assertEqual([m.annual_counterfactual(25,drop,rows)[
            "hypothetical_best"] for drop in ([],[444764],[444765],
                                              [444764,444765])],
                         [25,24,24,23])
        self.assertFalse(m.annual_counterfactual(25,[],rows)[
            "crosses_observed_label"])
        for drop in ([444764],[444765],[444764,444765]):
            self.assertTrue(m.annual_counterfactual(25,drop,rows)[
                "crosses_observed_label"])

    def test_invalid_repeated_or_missing_exclusions_fail(self):
        rows=[{"GED_event_id":444764,"best":1}]
        for ids in ([444764,444764],[444765]):
            with self.assertRaises(ValueError):
                m.annual_counterfactual(25,ids,rows)

    def test_nonofficial_GED_ZIP_rejected(self):
        with self.assertRaises(ValueError):
            m.scan_official_uganda_2022(b"fake zip archive")

    def test_original_GED_and_case_targets_locked(self):
        self.assertEqual(m.GED_IDS,(444764,444765))
        self.assertEqual(m.DYAD,"16938")
        self.assertEqual(m.GED_SHA,
           "e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d")


if __name__=="__main__":
    unittest.main()
