import io
import zipfile
import unittest
from probe_ucdp_prio_incidence import (
    SOURCES,source_zip,parse_country_code,audit
)

def archive(rows):
    head="conflict_id,year,type_of_conflict,gwno_a,gwno_loc\n"
    content=head+"\n".join(rows)+"\n"
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("ucdp-prio-conflicts.csv",content)
    return stream.getvalue()

class PRIOProvenanceProbeTests(unittest.TestCase):
    def test_zip_parser_rejects_foreign_schema_and_corrupted_bytes(self):
        with self.assertRaisesRegex(ValueError,"not a ZIP"):
            source_zip(b"country,year\n")
        with self.assertRaisesRegex(ValueError,"schema is incompatible"):
            source_zip(self._bad_schema_zip())
    @staticmethod
    def _bad_schema_zip():
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,"w") as z:
            z.writestr("bad.csv","year,other\n2022,1\n")
        return stream.getvalue()

    def test_unambiguous_only(self):
        self.assertEqual(parse_country_code(" 101 "),"101")
        self.assertIsNone(parse_country_code("101,102"))
        self.assertIsNone(parse_country_code(""))
        self.assertIsNone(parse_country_code("N/A"))

    def test_conflict_years_aggregate_without_confusing_interstate_or_multiple_locations(self):
        rows23=[
           "1,2020,3,101,101",
           "2,2022,4,101,101",
           "3,2022,4,101,101",
           "4,2022,2,102,102",
           "5,2022,3,102,101",
           '6,2022,3,"102,103","102,103"',
        ]
        rows25=[
           "1,2020,3,101,101",
           "2,2024,3,102,102"
        ]
        archives={SOURCES["23.1"]:archive(rows23),SOURCES["25.1"]:archive(rows25)}
        def fake_fetch(url,limit):
            self.assertLessEqual(len(archives[url]),limit)
            return archives[url]
        def fake_onset(version):
            end={"23.1":2022,"25.1":2024}[version]
            return {
                "101":{end:(0,0)},
                "102":{end:(1,0)},
            },{"max_year":end,"sha256":"sha-fixture"}
        summary=audit(fake_fetch,fake_onset)
        a=summary["versions"]["23.1"]
        self.assertEqual(a["raw_conflict_year_rows"],6)
        self.assertEqual(a["unique_intrastate_country_years"],3)
        self.assertEqual(a["missing_or_multiple_government_codes"],1)
        self.assertEqual(a["different_singleton_gwno_a_and_gwno_loc"],1)
        self.assertEqual(a["row_counts_by_conflict_type"],{"2":1,"3":3,"4":2})
        self.assertEqual(a["latest_year_countries_active"],2)
        self.assertEqual(a["latest_year_onset_universe"],2)
        self.assertEqual(summary["versions"]["25.1"]["latest_year"],2024)
        self.assertFalse(summary["historical_release_dates_independently_authenticated"])
        self.assertFalse(summary["country_year_labels_or_predictions_published"])

if __name__=="__main__":
    unittest.main()
