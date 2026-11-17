#!/usr/bin/env python3
"""Synthetic controls for exact source-label transition impact."""
import copy
import unittest

from audit_geo_ged_transition_revision_impact import summarize


def fixture(flips, years=(2013, 2014, 2015, 2016), countries=2):
    annual = [{"target_year": y, "binary_best_ge25_label_flips":
               sum(f["target_year"] == y for f in flips)} for y in years]
    return {
        "historical_model_fitting_authorized": False,
        "GEO2027_GEO2028_forecasts_modified": False,
        "source_zip_sha256": {"a": "illustrative-only"},
        "pairs": [{
            "old_version": "synthetic_a",
            "new_version": "synthetic_b",
            "is_consecutive_release": True,
            "comparison": {
                "target_years": list(years),
                "eligible_countries_per_year": countries,
                "observed_country_years": len(years) * countries,
                "best_ge25_binary_label_change_n": len(flips),
                "binary_flip_details": flips,
                "annual": annual,
                "excluded_GWNO_due_official_GED_coverage": [],
            },
        }],
    }


def flip(country, year):
    return {"GWNO": country, "target_year": year, "old_active": False, "new_active": True}


class TestGEDTransitionImpact(unittest.TestCase):
    def test_one_interior_binary_flip_changes_two_transitions(self):
        row = summarize(fixture([flip(616, 2014)]))["pairs"][0]
        self.assertEqual(row["revised_single_year_binary_labels"], 1)
        self.assertEqual(row["revised_two_year_transition_labels"], 2)
        self.assertEqual(row["eligible_country_transitions"], 6)

    def test_boundary_year_only_one_transition(self):
        row = summarize(fixture([flip(616, 2013)]))["pairs"][0]
        self.assertEqual(row["revised_two_year_transition_labels"], 1)

    def test_adjacent_flips_union_avoids_double_counting(self):
        row = summarize(fixture([flip(616, 2014), flip(616, 2015)]))["pairs"][0]
        self.assertEqual(row["revised_two_year_transition_labels"], 3)

    def test_independent_countries_do_not_collapse(self):
        row = summarize(fixture([flip(616, 2014), flip(541, 2014)]))["pairs"][0]
        self.assertEqual(row["revised_two_year_transition_labels"], 4)

    def test_duplicate_flip_fails_closed(self):
        with self.assertRaises(ValueError):
            summarize(fixture([flip(616, 2014), flip(616, 2014)]))

    def test_source_coverage_failure(self):
        sample = fixture([flip(616, 2014)])
        sample["pairs"][0]["comparison"]["observed_country_years"] -= 1
        with self.assertRaises(ValueError):
            summarize(sample)

    def test_historical_asof_claim_refused(self):
        sample = fixture([])
        sample["historical_model_fitting_authorized"] = True
        with self.assertRaises(ValueError):
            summarize(sample)

    def test_nonconsecutive_years_refused(self):
        with self.assertRaises(ValueError):
            summarize(fixture([], years=(2013, 2015, 2016)))


if __name__ == "__main__":
    unittest.main()
