"""Synthetic, source-independent integrity tests for GED20/21 cross-vintage study."""
from __future__ import annotations

import json
import unittest

from audit_geo_ged20_21_coverage_revisions import (
    ALL_URLS, CODEBOOKS, VINTAGES, MIN_YEAR, SYRIA,
    _valid_ids, compare_versions, evaluate, syria_coverage,
)
from audit_geo2027_global_only_matched_issue import ISSUE
from audit_geo_legacy_ged_countryyear_bridge import (
    GED_URLS, GED_221_CODEBOOK, discover_ged,
)


class GED2021HistoricalCoverageTests(unittest.TestCase):
    def setUp(self):
        self.cohort=list(range(1,196))+[SYRIA]

    def test_2020_2021_specific_source_urls_and_codebook_extractions(self):
        self.assertEqual(VINTAGES,("19.1","20.1","21.1","22.1","23.1"))
        self.assertEqual(ALL_URLS["20.1"],"https://ucdp.uu.se/downloads/ged/ged201-csv.zip")
        self.assertEqual(ALL_URLS["21.1"],"https://ucdp.uu.se/downloads/ged/ged211-csv.zip")
        self.assertEqual([CODEBOOKS[v]["data_extracted_on"] for v in ("20.1","21.1")],
                         ["2020-04-07","2021-04-08"])
        self.assertEqual([CODEBOOKS[v]["last_event_year"] for v in ("20.1","21.1")],
                         [2019,2020])
        self.assertEqual(ALL_URLS["22.1"],GED_URLS["22.1"])
        self.assertEqual(ALL_URLS["19.1"],GED_URLS["19.1"])

    def test_clean_Syria_coverage_exclusion_not_zero_outcome(self):
        old={(1,2018):24} # GED19 Syria completely excluded
        new={(1,2018):25,(SYRIA,2018):80}
        baseline=compare_versions(old,new,self.cohort,[2018])
        correct=compare_versions(old,new,self.cohort,[2018],excluded=frozenset({SYRIA}))
        self.assertEqual(baseline["observed_country_years"],196)
        self.assertEqual(baseline["best_ge25_binary_label_change_n"],2)
        self.assertEqual(correct["observed_country_years"],195)
        self.assertEqual(correct["best_ge25_binary_label_change_n"],1)
        self.assertEqual(correct["excluded_GWNO_due_official_GED_coverage"],[SYRIA])
        self.assertEqual(correct["excluded_unobserved_country_years"],1)
        self.assertEqual(correct["binary_flip_details"][0]["GWNO"],1)
        cover=syria_coverage(old,new,self.cohort,2018)
        self.assertEqual(cover["old_best_ge25_year_n"],0)
        self.assertEqual(cover["new_best_ge25_year_n"],1)
        self.assertTrue(cover["old_event_record_absence_is_not_proof_of_no_real_violence"])

    def test_exact_counts_flips_and_yearly_aggregation(self):
        old={(1,2017):24,(2,2017):25,(3,2018):26,(SYRIA,2018):2}
        new={(1,2017):26,(2,2017):25,(3,2018):26,(SYRIA,2018):4}
        t=compare_versions(old,new,self.cohort,[2017,2018])
        self.assertEqual(t["observed_country_years"],392)
        self.assertEqual(t["best_ge25_binary_label_change_n"],1)
        self.assertEqual(t["best_death_count_mismatch_n"],2)
        self.assertEqual(t["exact_best_death_count_match_n"],390)
        self.assertEqual(t["signed_new_minus_old_best_deaths"],4)
        self.assertEqual(t["annual"][0]["binary_best_ge25_label_flips"],1)
        self.assertEqual(t["annual"][1]["binary_best_ge25_label_flips"],0)
        self.assertEqual(t["binary_flip_details"][0]["old_best_statebased_deaths"],24)
        self.assertEqual(t["binary_flip_details"][0]["new_best_statebased_deaths"],26)

    def test_fail_closed_invalid_riskset_years_and_coverage(self):
        for ids in (self.cohort[:-1],self.cohort+[SYRIA],
                    [str(x) for x in self.cohort]):
            with self.assertRaises(ValueError):
                _valid_ids(ids)
        for years in ([],[2018,2018],[1989],[2027]):
            with self.assertRaises(ValueError):
                compare_versions({}, {}, self.cohort, years)
        with self.assertRaisesRegex(ValueError,"Only verified"):
            compare_versions({}, {},self.cohort,[2018],excluded=frozenset({1}))
        with self.assertRaises(ValueError):
            compare_versions({(1,2018):-4},{},self.cohort,[2018])
        with self.assertRaises(ValueError):
            compare_versions({(1,2018):True},{},self.cohort,[2018])

    def test_archive_discovery_distinguishes_specific_20_21_vs_syria(self):
        html=(
            '<h2>UCDP Georeferenced Event Dataset (GED)</h2>'
            '<p>GED 20.1: <a href="/downloads/ged/ged201-csv.zip">CSV</a> '
            '<a href="/downloads/ged/ged201.pdf">Codebook</a></p>'
            '<p>GED 21.1: <a href="/downloads/ged/ged211-csv.zip">CSV</a> '
            '<a href="/downloads/ged/ged211.pdf">Codebook</a></p>'
            '<p>GED Syria 20160101-20191130 (652.1601.1911): '
            '<a href="/downloads/ged/syria-csv.zip">CSV</a></p>'
            '<h2>Next dataset</h2><p>GED 20.1: '
            '<a href="/downloads/ged/other.csv">CSV</a></p>')
        d=discover_ged(html.encode())
        self.assertEqual(set(d),{"20.1","21.1"})
        self.assertEqual(d["20.1"]["CSV"],ALL_URLS["20.1"])
        self.assertEqual(d["21.1"]["CODEBOOK"],CODEBOOKS["21.1"]["url"])

    def test_historical_issue_not_conflated_with_source_replay(self):
        issue=json.loads(ISSUE.read_text(encoding="utf-8"))
        self.assertEqual(issue["official_2027_outcomes_resolved"],0)
        self.assertEqual(len(issue["countries"]),196)
        self.assertEqual(MIN_YEAR,2011)
        with self.assertRaisesRegex(ValueError,"Original GED-CY bridge"):
            evaluate({}, {}, {}, {}, issue)
        with self.assertRaisesRegex(ValueError,"Original GED-CY bridge"):
            evaluate({}, {}, {}, {"schema":"bad"}, issue)


if __name__=="__main__":
    unittest.main()
