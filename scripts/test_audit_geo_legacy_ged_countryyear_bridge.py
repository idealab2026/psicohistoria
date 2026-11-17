"""Regression tests for vintage-specific UCDP GED event vs CY measurement."""
from __future__ import annotations

import csv
import hashlib
import io
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from audit_geo_legacy_ged_countryyear_bridge import (
    ARCHIVE, GED_221_CODEBOOK, GED_URLS, SELECTED, VERSIONS,
    compare_state_based, discover_ged, parse_ged, replay,
)


def fake_zip(rows, headers=None):
    if headers is None:
        headers=("id","year","country_id","type_of_violence",
                 "best","low","high")
    buffer=io.StringIO(newline="")
    writer=csv.DictWriter(buffer,fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    result=io.BytesIO()
    with ZipFile(result,"w",compression=ZIP_DEFLATED) as zipfile:
        zipfile.writestr("historical_ged.csv",buffer.getvalue().encode("utf-8"))
    return result.getvalue()


def events(n=1001):
    return [
        {"id":str(i+1),"year":"2018","country_id":"230",
         "type_of_violence":str(i%3+1),
         "best":"2","low":"1","high":"3"}
        for i in range(n)]


class GEDCountryYearBridgeTests(unittest.TestCase):
    def test_official_legacy_GED_section_and_no_cross_dataset_links(self):
        html=(f'<h2>UCDP Georeferenced Event Dataset (GED)</h2>'
              f'<p>GED 23.1: <a href="/downloads/ged/ged231-csv.zip">CSV</a></p>'
              f'<p>GED 22.1: <a href="/downloads/ged/ged221-csv.zip">CSV</a>'
              f' | <a href="/downloads/ged/ged221.pdf">Codebook</a></p>'
              f'<p>GED 19.1: <a href="/downloads/ged/ged191-csv.zip">CSV</a></p>'
              f'<h2>UCDP Other Dataset</h2>'
              f'<p>GED 18.1: <a href="/downloads/ged/fake181-csv.zip">CSV</a></p>')
        got=discover_ged(html.encode())
        self.assertEqual(set(got),{"23.1","22.1","19.1"})
        self.assertEqual(got["22.1"]["CODEBOOK"],GED_221_CODEBOOK)
        self.assertEqual(got["19.1"]["CSV"],GED_URLS["19.1"])
        bad=html.replace("/downloads/ged/ged221-csv.zip","https://example.net/fake.csv")
        with self.assertRaisesRegex(ValueError,"allowlisted"):
            discover_ged(bad.encode())

    def test_event_types_not_combined_and_country_gwno(self):
        raw=fake_zip(events())
        meta,counts=parse_ged(raw,"19.1")
        self.assertEqual(meta["event_count"],1001)
        self.assertEqual(meta["events_by_violence_type"][1],334)
        self.assertEqual(counts[(230,2018)],668)
        self.assertEqual(sum(meta["events_by_violence_type"].values()),1001)
        self.assertEqual(meta["first_recorded_event_year"],2018)
        self.assertEqual(meta["last_recorded_event_year"],2018)
        self.assertTrue(meta["event_ids_unique"])
        self.assertEqual(meta["nonmonotonic_low_best_high_event_n"],0)

    def test_nonmonotonic_source_is_preserved_not_silently_sorted(self):
        rows=events()
        rows[0]["best"]="99"
        rows[0]["high"]="88"
        raw=fake_zip(rows)
        meta,counts=parse_ged(raw,"22.1")
        self.assertEqual(meta["nonmonotonic_low_best_high_event_n"],1)
        self.assertEqual(counts[(230,2018)],765)

    def test_fail_closed_mutated_or_duplicate_or_missing_schema(self):
        raw=fake_zip(events())
        with self.assertRaisesRegex(ValueError,"SHA"):
            parse_ged(raw,"19.1",expected_sha256="0"*64)
        rows=events()
        rows[-1]["id"]="1"
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            parse_ged(fake_zip(rows),"19.1")
        headers=("id","year","country_id","type_of_violence")
        with self.assertRaisesRegex(ValueError,"GED event-table CSV member"):
            parse_ged(fake_zip([{
                "id":"1","year":"2018","country_id":"230",
                "type_of_violence":"1"}],headers),"19.1")
        with self.assertRaises(ValueError):
            parse_ged(b"not a zip","19.1")

    def test_country_year_zero_vs_events_and_threshold_crossings(self):
        cohort=list(range(1,197))
        old={(1,2018):24,(2,2018):25,(3,2018):31}
        ref={(1,2018):25,(2,2018):25,(3,2018):0}
        result=compare_state_based(old,ref,cohort,(2018,))
        self.assertEqual(result["country_years"],196)
        self.assertEqual(result["threshold_disagreement_n"],2)
        self.assertEqual(result["exact_death_count_match_n"],194)
        self.assertEqual(result["total_absolute_death_difference"],32)
        self.assertEqual(result["binary_state_match_n"],194)
        self.assertEqual(result["ged_active_country_year_n"],2)
        self.assertEqual(result["comparison_active_country_year_n"],2)

    def test_source_dimensions_restricted_and_guard_release_mixing(self):
        self.assertEqual(SELECTED,("19.1","22.1","23.1"))
        self.assertIn("17.1",VERSIONS)
        self.assertEqual(GED_URLS["22.1"],
                         "https://ucdp.uu.se/downloads/ged/ged221-csv.zip")
        with self.assertRaisesRegex(ValueError,"Official GED version listing"):
            replay({}, {},list(range(1,197)),{})
        with self.assertRaisesRegex(ValueError,"Fixed issued"):
            compare_state_based({}, {},list(range(1,10)),(2018,))

    def test_distinguish_source_revisions_from_same_vintage_equivalence(self):
        ids=list(range(1,197))
        v23={(1,2018):20,(2,2018):27}
        v22={(1,2018):24,(2,2018):27}
        cy={(1,2018):20,(2,2018):28}
        same=compare_state_based(v23,cy,ids,(2018,))
        older=compare_state_based(v22,cy,ids,(2018,))
        self.assertEqual(same["threshold_disagreement_n"],0)
        self.assertEqual(same["exact_death_count_match_n"],195)
        self.assertEqual(older["total_absolute_death_difference"],5)
        self.assertFalse(same["exact_death_count_match_n"]==196)


if __name__=="__main__":
    unittest.main()
