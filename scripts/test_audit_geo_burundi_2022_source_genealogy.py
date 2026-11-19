#!/usr/bin/env python3
"""Burundi June 2022 source independence / allegation and temporal tests."""
import unittest
from unittest.mock import patch

import audit_geo_burundi_2022_source_genealogy as m


def frozen_prior(sha="test-sha"):
    return {
        "schema":"idealab.psico.geo_burundi_2022_statebased_multiday_external_evidence.v1",
        "original_GEO2027_SHA256":sha,
        "two_original_GEO2027_GEO2028_issues_unchanged":True,
        "GED_record":{"GED_event_id":442626,"GWNO":516,
                      "GED_type_of_violence":1,
                      "best_fatalities_estimate":10,
                      "event_start":"2022-06-19","event_end":"2022-06-21"},
        "GDELT_news_events":{
            "same_2022_06_19_to_21_event_date":{"within_100km_n":0}},
    }


class BurundiGenealogyTest(unittest.TestCase):
    def setUp(self):
        self.patch=patch.object(m,"SOURCE_SHA256","test-sha")
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_control_original_event_not_reissued(self):
        m.validate_anchor(frozen_prior())
        p=frozen_prior()
        p["GED_record"]["GED_type_of_violence"]=3
        with self.assertRaises(ValueError):
            m.validate_anchor(p)
        p=frozen_prior()
        p["GDELT_news_events"]["same_2022_06_19_to_21_event_date"]["within_100km_n"]=1
        with self.assertRaises(ValueError):
            m.validate_anchor(p)

    def test_research_registry_six_source_publications_five_burundi(self):
        o=m.build_report(frozen_prior())
        self.assertEqual(len(o["sources"]),6)
        self.assertEqual(o["burundi_reporting_publishers_n"],5)
        self.assertEqual(o["burundi_provisional_editorial_reporting_groups_n"],3)
        self.assertEqual(o["verified_independent_named_victim_lists_n"],0)
        self.assertEqual(o["verified_disjoint_firsthand_witness_sets_n"],0)
        self.assertIs(o["ten_burundi_deaths_confirmed_by_independent_forensic_source"],False)
        self.assertIs(o["source_url_and_claim_manual_review_required"],True)

    def test_cited_press_republication_and_ngo_overlap_never_independent(self):
        o=m.build_report(frozen_prior())
        edges=o["dependency_edges"]
        attribution=next(e for e in edges if
                         e["kind"]=="explicit_editorial_attribution")
        self.assertEqual(attribution["from"],"hitamwoneza_20220622")
        self.assertEqual(attribution["to"],"sos_20220621")
        self.assertTrue(attribution["direction_established"])
        ngo=next(e for e in edges if
                 e["kind"]=="near_verbatim_same_report_unresolved_direction")
        self.assertFalse(ngo["direction_established"])
        self.assertTrue(all(e["count_as_independent_confirmation"] is False
                            for e in edges))

    def test_near_verbatim_ngo_claim_coverage_and_no_two_witnesses(self):
        o=m.build_report(frozen_prior())
        pair=next(x for x in o["semantic_claim_overlap_diagnostic"]
                  if x["left"]=="iteka_q2_2022")
        self.assertGreaterEqual(pair["claim_jaccard"],.8)
        self.assertEqual(o["other_NGO_pair_with_near_verbatim_case_text_n"],1)
        self.assertFalse(o["editorial_groups_proven_statistically_independent"])

    def test_rwanda_bus_attacked_not_burundi_victims(self):
        o=m.build_report(frozen_prior())
        bus=next(s for s in o["sources"]
                 if s["id"]=="rwanda_bus_reuters_20220620")
        self.assertEqual(bus["event"],"rwanda_bus_nyamagabe_2022_06_18")
        self.assertNotIn("casualties_10_deaths",bus["claims"])
        burundi=set(s["id"] for s in o["sources"]
                    if s["event"]=="burundi_kibira_mabayi_2022")
        self.assertNotIn(bus["id"],burundi)
        self.assertFalse(o["Rwandan_force_involvement_proven"])

    def test_date_shift_in_derivative_unresolved(self):
        o=m.build_report(frozen_prior())
        shift=next(x for x in o["reported_temporal_discrepancies"]
                   if x["source"]=="hitamwoneza_20220622")
        self.assertEqual(shift["source_claimed_dates"],["2022-06-18","2022-06-20"])
        self.assertEqual(shift["GED_interval"],["2022-06-19","2022-06-21"])
        self.assertEqual(shift["effect_on_ten_deaths_truth"],"not_determined")

    def test_iteka_received_information_is_not_publication_date(self):
        o=m.build_report(frozen_prior())
        node=next(s for s in o["sources"] if s["id"]=="iteka_q2_2022")
        self.assertEqual(node["publication_date"],"2022-07")
        self.assertFalse(node["own_publication_before_2022_06_21_verified"])
        self.assertIn("information_received_june_20_claimed",node["claims"])

    def test_sources_must_be_explicit_trusted_urls_and_valid_dates(self):
        src=dict(m.SOURCES[0])
        src["url"]="https://untrusted.example.com/report"
        with self.assertRaises(ValueError):
            m.source_date_eligible(src)
        src=dict(m.SOURCES[0])
        src["publication_date"]="2022-02-31"
        with self.assertRaises(ValueError):
            m.source_date_eligible(src)
        src=dict(m.SOURCES[0])
        src["named_independently_verifiable_event_witnesses_n"]=1
        with self.assertRaises(ValueError):
            m.source_date_eligible(src)

    def test_no_source_claims_remote_sha_pinned(self):
        o=m.build_report(frozen_prior())
        self.assertFalse(o["raw_web_pages_or_pdf_bytes_snapshotted"])
        self.assertEqual(len(o["source_snapshot_sha256_not_remote_page_byte_hash"]),64)
        self.assertTrue(o["original_GEO2027_GEO2028_not_modified"])


if __name__=="__main__":
    unittest.main()
