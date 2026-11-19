#!/usr/bin/env python3
"""Adversarial tests: Uganda December GED metadata, not source adjudication."""
import unittest
import audit_geo_uganda2022_december_source_families as m

def row(eid,best,date_start,date_end):
    return {
        "id":str(eid),"country_id":"500","year":"2022",
        "type_of_violence":"1","dyad_new_id":"16938",
        "best":str(best),"low":str(best),"high":str(best),
        "date_start":date_start,"date_end":date_end,
        "date_prec":"2","where_prec":"2","event_clarity":"1",
        "where_coordinates":"Ntoroko district",
        "where_description":"River border",
        "latitude":"1.0","longitude":"30.5",
        "dyad_name":"Government of Uganda - IS",
        "side_a":"Government of Uganda","side_b":"IS",
        "adm_1":"Ntoroko","adm_2":"Local council",
        "number_of_sources":"2",
        "source_article":'"Agency A,2022-12-15,Battle in West Uganda";"Agency B,2022-12-16,Follow-up"',
        "source_original":"Uganda army spokesman",
        "source_office":"Agency A;Agency B",
        "source_headline":"Battle in West Uganda;Follow-up",
        "source_date":"2022-12-15;2022-12-16"
    }


class DecemberGED(unittest.TestCase):
    def test_upstream_fixed_six_events_have_23_december(self):
        frozen=m.fixed_prior_contract()
        self.assertEqual(frozen["statebased_dyad_n"],1)
        self.assertEqual(sum(m.EXPECTED_BEST.values()),23)
        self.assertEqual(len(m.DECEMBER_IDS),4)

    def test_supported_2022_source_records(self):
        ev,_=m.normalize_and_publish(
            460796,row(460796,19,"2022-12-12","2022-12-13"))
        self.assertEqual(ev["best"],19)
        self.assertEqual(ev["number_of_sources"],2)
        self.assertEqual(len(ev["GED_source_article_fingerprints"]),2)
        self.assertFalse(ev["independently_verified_fatality_or_rebel_status"])

    def test_zero_best_is_not_missing(self):
        ev,_=m.normalize_and_publish(
            460862,row(460862,0,"2022-12-13","2022-12-27"))
        self.assertEqual(ev["best"],0)
        self.assertFalse(ev["duplicate_event_verified"])

    def test_inconsistent_case_fatality_rejected(self):
        with self.assertRaises(ValueError):
            m.normalize_and_publish(460796,
                row(460796,18,"2022-12-12","2022-12-13"))

    def test_wrong_country_rejected(self):
        r=row(460796,19,"2022-12-12","2022-12-13")
        r["country_id"]="501"
        with self.assertRaises(ValueError):
            m.normalize_and_publish(460796,r)

    def test_wrong_dyad_rejected(self):
        r=row(460796,19,"2022-12-12","2022-12-13")
        r["dyad_new_id"]="16939"
        with self.assertRaises(ValueError):
            m.normalize_and_publish(460796,r)

    def test_zero_best_wrong_date_rejected(self):
        with self.assertRaises(ValueError):
            m.normalize_and_publish(460862,
                row(460862,0,"2022-12-14","2022-12-27"))

    def test_reused_article_titles_are_not_two_independent_witnesses(self):
        r=row(460796,19,"2022-12-12","2022-12-13")
        e,_=m.normalize_and_publish(460796,r)
        self.assertFalse(e["independently_verified_fatality_or_rebel_status"])
        self.assertEqual(e["number_of_sources"],2)

    def test_malformed_source_count_fails_closed(self):
        r=row(460796,19,"2022-12-12","2022-12-13")
        r["number_of_sources"]="3"
        with self.assertRaises(ValueError):
            m.normalize_and_publish(460796,r)

    def test_not_a_source_if_not_official_archive(self):
        with self.assertRaises(ValueError):
            m.official_december_metadata(b"any zip")

    def editorial_case_fixture(self):
        return {
            460796:{"date_start":"2022-12-12","date_end":"2022-12-13",
                    "best":19,"high":19,"date_prec":2},
            460859:{"date_start":"2022-12-21","date_end":"2022-12-21",
                    "best":2,"high":2,"date_prec":1},
            460862:{"date_start":"2022-12-13","date_end":"2022-12-27",
                    "best":0,"high":3,"date_prec":4},
            462156:{"date_start":"2022-12-19","date_end":"2022-12-19",
                    "best":2,"high":2,"date_prec":1},
        }

    def test_external_review_exact_date_and_zero_best_controls(self):
        a=m.audit_public_review(self.editorial_case_fixture())
        self.assertEqual(a["GED_exact_date_vs_contemporary_event_day_discrepancies"],
                         [460859,462156])
        self.assertFalse(a["independently_verified_full_19_fatality_roster"])
        self.assertEqual(a["December_events_reclassified"],0)

    def test_source_review_does_not_silently_change_exact_date_precision(self):
        rows=self.editorial_case_fixture()
        rows[460859]["date_prec"]=2
        with self.assertRaises(ValueError):
            m.audit_public_review(rows)

    def test_historical_date_mismatch_not_silently_corrected(self):
        rows=self.editorial_case_fixture()
        rows[462156]["date_start"]="2022-12-18"
        with self.assertRaises(ValueError):
            m.audit_public_review(rows)

    def test_duplicate_GED_citations_inside_single_row_are_not_sources(self):
        r=row(460796,19,"2022-12-12","2022-12-13")
        r["source_article"]='"Agency A,2022-12-15,One report";"Agency A,2022-12-15,One report"'
        ev,_=m.normalize_and_publish(460796,r)
        self.assertEqual(ev["number_of_sources"],2)
        self.assertEqual(ev["distinct_GED_bibliographic_refs_n"],1)
        self.assertEqual(ev["repeated_identical_bibliographic_fragments_n"],1)

    def test_label_recode_or_independent_roster_claim_rejected(self):
        from pathlib import Path
        import json
        import tempfile
        from unittest.mock import patch
        original=json.loads(m.PUBLIC_REVIEW.read_text(encoding="utf-8"))
        original["event_fatality_labels_modified"]=True
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.json"
            p.write_text(json.dumps(original),encoding="utf-8")
            with patch.object(m,"PUBLIC_REVIEW",p):
                with self.assertRaises(ValueError):
                    m.audit_public_review(self.editorial_case_fixture())

    def test_original_issue_unchanged(self):
        self.assertEqual(m.GED_SHA,
            "e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d")

if __name__=="__main__":
    unittest.main()
