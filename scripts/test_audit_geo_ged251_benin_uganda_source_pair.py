#!/usr/bin/env python3
"""Adversarial tests for Benin/Uganda GED25.1 source provenance checks."""
import unittest
import audit_geo_ged251_benin_uganda_source_pair as m

def sample(eid,best=1,country=434):
    return {
        "id":str(eid),"country_id":str(country),"year":"2022",
        "type_of_violence":"1","best":str(best),"low":str(best),
        "high":str(best),"date_start":"2022-01-01",
        "date_end":"2022-01-01","date_prec":"1",
        "where_prec":"2","where_coordinates":"Village A",
        "where_description":"Village A","latitude":"10.12",
        "longitude":"2.33","dyad_new_id":"123",
        "dyad_name":"Government - Armed group",
        "event_clarity":"1","source_article":
            "Report Agency, 2022-01-02, First source article title",
        "source_original":"Local reporter",
        "source_date":"2022-01-02",
        "source_office":"Report Agency",
        "source_headline":"First source article title",
        "number_of_sources":"1","adm_1":"Region","adm_2":"County",
        "side_a":"Government of test","side_b":"Armed group",
    }

class GED251PairSource(unittest.TestCase):
    def test_pinned_contract_matches_actual_prior_census(self):
        prior,cases=m.check_existing_case_contract()
        self.assertEqual(prior["marginal_candidate_pairs_with_one_row_pivot_n"],2)
        self.assertEqual(len(cases),2)
        self.assertEqual({name for name,_ in cases},{"benin_2022","uganda_2022"})

    def test_normalization_deduplicates_spacing(self):
        x=m.citation_fragments("  One  publisher, 2022-01-01, Article /// Other publisher, 2022-01-02, News ")
        self.assertEqual(x,["One publisher, 2022-01-01, Article",
                            "Other publisher, 2022-01-02, News"])

    def test_distinct_source_fragments_are_not_witness_identity(self):
        a=sample(431254,best=8)
        b=sample(431259)
        b["source_article"]="Other Bureau, 2022-01-03, Independent news title"
        out=m.summarize_case(m.CASES["benin_2022"],{431254:a,431259:b})
        self.assertEqual(out["common_identical_normalized_UCDP_bibliographic_citations_n"],0)
        self.assertFalse(out["duplicate_event_proven"])
        self.assertFalse(out["independent_publisher_primary_witness_verified"])

    def test_shared_reference_is_not_proven_duplicate(self):
        a=sample(431254,best=8)
        b=sample(431259)
        out=m.summarize_case(m.CASES["benin_2022"],{431254:a,431259:b})
        self.assertEqual(out["common_identical_normalized_UCDP_bibliographic_citations_n"],1)
        self.assertFalse(out["duplicate_event_proven"])
        self.assertFalse(out["identical_victims_verified"])

    def test_raw_full_article_field_not_republished(self):
        a=sample(431254,best=8)
        b=sample(431259)
        out=m.summarize_case(m.CASES["benin_2022"],{431254:a,431259:b})
        for ev in out["events"]:
            self.assertNotIn("citation_preview",ev)
            self.assertNotIn("citation_fingerprints",ev)
            self.assertIn("citation_fingerprint_sha256",ev)

    def test_mismatch_fatalities_fails_closed(self):
        with self.assertRaises(ValueError):
            m.summarize_case(m.CASES["benin_2022"],{
                431254:sample(431254,best=7),431259:sample(431259)})

    def test_mismatch_violence_fails_closed(self):
        a,b=sample(444764,country=500),sample(444765,country=500)
        b["type_of_violence"]="2"
        with self.assertRaises(ValueError):
            m.summarize_case(m.CASES["uganda_2022"],{444764:a,444765:b})

    def test_unsupported_event_precision_fails_closed(self):
        x=sample(431254,best=8)
        x["where_prec"]="0"
        with self.assertRaises(ValueError):
            m.parse_source_row(x)

    def test_invalid_event_range_fails_closed(self):
        x=sample(431254,best=8)
        x["date_end"]="2021-01-01"
        with self.assertRaises(ValueError):
            m.parse_source_row(x)

    def test_audit_original_zip_still_immutable(self):
        self.assertEqual(m.GED_SHA,"e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d")

if __name__=="__main__":
    unittest.main()
