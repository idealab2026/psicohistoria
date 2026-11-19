#!/usr/bin/env python3
"""Togo GED440185: one prior bibliography date never disproves May11 assault."""
import copy
import unittest
import audit_geo_togo2022_440185_source_genealogy as m


def fixture():
    dates=["2022-05-05","2022-05-11","2022-05-12","2022-05-13",
           "2022-05-19","2022-05-19","2022-05-20","2022-05-26"]
    return {
        "id":"440185","country_id":"461","year":"2022",
        "type_of_violence":"1","best":"23","low":"23","high":"23",
        "deaths_a":"8","deaths_b":"15","deaths_civilians":"0",
        "deaths_unknown":"0","date_start":"2022-05-11","date_end":"2022-05-11",
        "date_prec":"1","where_prec":"2",
        "dyad_new_id":"123","dyad_name":"Government of Togo - JNIM",
        "side_a":"Government of Togo","side_b":"JNIM",
        "source_article":";".join(
            f'"Agency{i},{day},Report about military post"' for i,day
            in enumerate(dates)),
        "source_date":";".join(dates),
        "source_office":";".join(f"Agency{i}" for i in range(8)),
        "source_original":"Togo government",
        "number_of_sources":"8",
    }


class TogoSources(unittest.TestCase):
    def test_event_was_selected_without_reading_source_titles(self):
        _,r=m.check_source_preselection()
        self.assertEqual((r["GED_event_id"],r["best"]),(440185,23))
        self.assertTrue(r["single_event_deletion_would_cross_25"])

    def test_pre_event_publication_is_not_event_day_error(self):
        row=m.interpret_ged_row(fixture())
        self.assertEqual(row["bibliographic_pre_event_references_n"],1)
        self.assertFalse(row["pre_event_bibliography_is_proven_coding_error"])
        self.assertEqual(row["UCDP_GED_event_day"],"2022-05-11")
        self.assertEqual(row["bibliographic_references_n"],8)

    def test_event_side_components_sum_exactly_to_best(self):
        row=m.interpret_ged_row(fixture())
        fatal=row["official_GED_fatality_components"]
        self.assertEqual(sum(fatal[k] for k in ("deaths_a","deaths_b",
                      "deaths_civilians","deaths_unknown")),fatal["best"])

    def test_fewer_sources_than_dates_fails_closed(self):
        r=fixture()
        r["number_of_sources"]="7"
        with self.assertRaises(ValueError):
            m.interpret_ged_row(r)

    def test_invalid_casualty_total_fails_closed(self):
        r=fixture()
        r["deaths_a"]="9"
        with self.assertRaises(ValueError):
            m.interpret_ged_row(r)

    def test_date_change_or_wrong_country_fails_closed(self):
        for key,changed in (("date_start","2022-05-10"),
                            ("country_id","500"),("best","22")):
            r=fixture()
            r[key]=changed
            with self.assertRaises(ValueError):
                m.interpret_ged_row(r)

    def test_public_review_is_not_victim_validation(self):
        import json
        review=json.loads(m.GOV_REVIEW.read_text(encoding="utf-8"))
        result=m.validate_public_review(m.interpret_ged_row(fixture()),review)
        self.assertFalse(result["GED_best_correction_justified"])
        self.assertFalse(result["later_additional_assailant_deaths_documentarily_independent"])
        self.assertTrue(result["exact_11May_event_day_contemporaneously_supported"])

    def test_if_claims_independent_15_dead_it_is_rejected(self):
        import json
        review=json.loads(m.GOV_REVIEW.read_text(encoding="utf-8"))
        review["claims_15_assailant_fatalities_independently_verified"]=True
        with self.assertRaises(ValueError):
            m.validate_public_review(m.interpret_ged_row(fixture()),review)

    def test_if_false_publication_date_coding_error_is_claimed_it_is_rejected(self):
        import json
        review=json.loads(m.GOV_REVIEW.read_text(encoding="utf-8"))
        review["source_before_11May_explains_event_day_error"]=True
        with self.assertRaises(ValueError):
            m.validate_public_review(m.interpret_ged_row(fixture()),review)

    def test_if_original_GEO_prediction_is_changed_it_is_rejected(self):
        import json
        review=json.loads(m.GOV_REVIEW.read_text(encoding="utf-8"))
        review["issued_GEO_probabilities_modified"]=True
        with self.assertRaises(ValueError):
            m.validate_public_review(m.interpret_ged_row(fixture()),review)

    def test_non_UCDP_official_bytes_rejected(self):
        with self.assertRaises(ValueError):
            m.original_ged_row(b"unverified media source")

    def test_original_official_UCDP_issue_still_immutable(self):
        self.assertEqual(m.GED_SHA,
            "e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d")


if __name__=="__main__":
    unittest.main()
