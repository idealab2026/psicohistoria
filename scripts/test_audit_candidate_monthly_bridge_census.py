import unittest
from audit_candidate_monthly_bridge_census import header_metadata,CSV_URLS,MONTHLY_YEARS
from check_ucdp_candidate_asof import SourceError
class CensusTest(unittest.TestCase):
    def test_complete_source_list(self):
        self.assertEqual(len(CSV_URLS),16)
        self.assertEqual(len(set(CSV_URLS)),16)
        for y in MONTHLY_YEARS:
            for m in (1,2,3):
                self.assertTrue(any(x.endswith(f"GEDEvent_v{y%100}_0_{m}.csv") for x in CSV_URLS))
    def test_header_not_rows(self):
        header=b"id,country_id,type_of_violence,date_prec,date_start,date_end,best\n"
        self.assertEqual(header_metadata(header+b"not,an,eligible,event\n"),header_metadata(header))
    def test_bad_header(self):
        for raw in (b"",b"id,id,country_id\n",b"id,country_id\n"):
            with self.assertRaises(SourceError):
                header_metadata(raw)
if __name__=="__main__": unittest.main()
