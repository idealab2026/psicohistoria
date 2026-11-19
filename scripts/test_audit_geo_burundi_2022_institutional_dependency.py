#!/usr/bin/env python3
"""Institutional source/casualty boundary tests for Burundi June 2022."""
import unittest
from unittest.mock import patch

import audit_geo_burundi_2022_institutional_dependency as m


def prior_reference():
    return {
        "schema":"idealab.psico.geo_burundi_2022_documentary_source_genealogy.v1",
        "original_GEO2027_SHA256":"dummy_original_issue_SHA",
        "prior_GED_event_id":442626,
        "prior_GED_best_deaths":10,
        "prior_GDELT_no_local_100km_footprint":True,
        "original_GEO2027_GEO2028_not_modified":True,
        "verified_independent_named_victim_lists_n":0,
        "verified_disjoint_firsthand_witness_sets_n":0,
        "source_snapshot_sha256_not_remote_page_byte_hash":"0"*64,
        "sources":[{"id":s} for s in (
            "sos_20220621","iteka_q2_2022","aprodh_june2022",
            "hitamwoneza_20220622","icg_crisiswatch_june2022",
            "rwanda_bus_reuters_20220620")],
    }


class BurundiInstitutionalDependency(unittest.TestCase):
    def setUp(self):
        p=patch.object(m,"SOURCE_SHA256","dummy_original_issue_SHA")
        p.start()
        self.addCleanup(p.stop)

    def test_frozen_prior_and_target_hard_guard(self):
        x=prior_reference()
        m.validate_anchor(x)
        for key,bad in (("prior_GED_best_deaths",9),
                        ("prior_GDELT_no_local_100km_footprint",False),
                        ("original_GEO2027_GEO2028_not_modified",False),
                        ("verified_disjoint_firsthand_witness_sets_n",2)):
            y=prior_reference()
            y[key]=bad
            with self.assertRaises(ValueError):
                m.validate_anchor(y)

    def test_four_extra_documents_three_institutions(self):
        r=m.build_report(prior_reference())
        self.assertEqual(r["new_institutional_document_entries_n"],4)
        self.assertEqual(r["new_distinct_institutional_families_n"],3)
        self.assertEqual(r["total_reviewed_source_records_n"],10)
        self.assertEqual(len(r["new_dependency_edges"]),4)

    def test_belgium_two_reports_cite_sos_not_extra_witness(self):
        r=m.build_report(prior_reference())
        for id_ in ("cgrs_belgium_20221012","cgrs_belgium_20230531"):
            entry=next(x for x in r["new_institutional_documents"] if x["id"]==id_)
            self.assertTrue(entry["has_footnote_directly_to_sos_20220621"])
            self.assertEqual(entry["reported_fatalities"],10)
            self.assertEqual(entry["reported_date_range"],["2022-06-18","2022-06-20"])
            self.assertEqual(entry["directly_identified_fatality_records_n"],0)
            edge=next(x for x in r["new_dependency_edges"] if x["from"]==id_ and
                      x["to"]=="sos_20220621")
            self.assertTrue(edge["directed"])
            self.assertFalse(edge["fatality_confirmation_independent"])

    def test_fews_reports_occurrence_only_no_casualties(self):
        r=m.build_report(prior_reference())
        doc=next(x for x in r["new_institutional_documents"] if x["id"]=="fewsnet_burundi_202210")
        self.assertEqual(doc["reported_date_range"],["2022-06-19","2022-06-21"])
        self.assertIsNone(doc["reported_fatalities"])
        self.assertTrue(r["claim_classification"]["event_exists"]["fewsnet_confirms_event_occurrence_as_reported"])
        self.assertFalse(r["claim_classification"]["event_exists"]["fewsnet_upstream_reporting_provenance_known"])
        self.assertFalse(r["claim_classification"]["event_exists"]["fewsnet_reports_fatality_count"])

    def test_sos_torture_three_homicides_not_ten_combat_death_contradiction(self):
        r=m.build_report(prior_reference())
        obs=r["claim_classification"]["human_rights_monitoring_omission"]
        self.assertEqual(obs["period"],["2022-06-18","2022-06-25"])
        self.assertEqual(obs["reported_homicides_in_scope_n"],3)
        self.assertFalse(obs["scope_is_exhaustive_of_rebel_combat_deaths"])
        self.assertFalse(obs["omission_proves_no_ten_battle_deaths"])
        self.assertFalse(r["sos_torture_three_homicides_can_be_compared_as_total_statebased_deaths"])

    def test_precise_dates_cannot_be_assumed_identical(self):
        r=m.build_report(prior_reference())
        t=r["claim_classification"]["temporal_scope"]
        self.assertEqual(t["early_window"],["2022-06-18","2022-06-20"])
        self.assertEqual(t["late_window"],["2022-06-19","2022-06-21"])
        self.assertEqual(t["window_intersection"],["2022-06-19","2022-06-20"])
        self.assertIs(t["exact_first_last_day_independently_verified"],False)

    def test_acled_secondary_context_not_firsthand_acled_retrieval(self):
        r=m.build_report(prior_reference())
        a=r["claim_classification"]["secondary_ACLED_reporting"]
        self.assertFalse(a["ACLED_firsthand_event_data_obtained"])
        self.assertFalse(a["ACLED_confirms_ten_fatalities_independently"])

    def test_no_remote_pdf_SHA_misrepresented(self):
        r=m.build_report(prior_reference())
        self.assertFalse(r["source_documents_bytes_SHA256_pinned"])
        self.assertEqual(len(r["new_source_metadata_and_assertions_sha256_not_remote_pdf_bytes"]),64)
        self.assertFalse(r["statistical_independence_or_true_error_rate_estimated"])
        self.assertFalse(r["original_GEO2027_GEO2028_issued_vectors_modified"])

    def test_unregistered_host_fails_closed(self):
        src=dict(m.NEW_SOURCES[0])
        src["url"]="https://untrusted.example.com/content.pdf"
        with patch.object(m,"NEW_SOURCES",(src,)+m.NEW_SOURCES[1:]):
            with self.assertRaises(ValueError):
                m.check_documents_and_edges(prior_reference())

    def test_unverified_forensic_witness_count_rejected(self):
        src=dict(m.NEW_SOURCES[2])
        src["directly_identified_fatality_records_n"]=10
        with patch.object(m,"NEW_SOURCES",m.NEW_SOURCES[:2]+(src,)+m.NEW_SOURCES[3:]):
            with self.assertRaises(ValueError):
                m.check_documents_and_edges(prior_reference())

    def test_mutated_direct_dependency_rejected(self):
        edge=dict(m.NEW_EDGES[0])
        edge["fatality_confirmation_independent"]=True
        with patch.object(m,"NEW_EDGES",(edge,)+m.NEW_EDGES[1:]):
            with self.assertRaises(ValueError):
                m.check_documents_and_edges(prior_reference())


if __name__=="__main__":
    unittest.main()
