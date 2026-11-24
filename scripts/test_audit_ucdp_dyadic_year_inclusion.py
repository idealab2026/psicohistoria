#!/usr/bin/env python3
"""Adversarial synthetic data for country/dyad-year inclusion; never real UCDP."""
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parent))
import audit_ucdp_dyadic_year_inclusion as audit
from check_ucdp_candidate_asof import SourceError


def zipped(rows):
    buffer=io.BytesIO()
    contents=io.StringIO(newline="")
    columns=("dyad_id","year","conflict_id","side_a_id","side_b_id")
    w=csv.DictWriter(contents,fieldnames=columns)
    w.writeheader()
    for dyad,year in rows:
        w.writerow({"dyad_id":dyad,"year":year,"conflict_id":22,
                    "side_a_id":12,"side_b_id":32})
    with zipfile.ZipFile(buffer,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("ucdp-dyadic-221.csv",contents.getvalue().encode())
    return buffer.getvalue()


class DyadYearTests(unittest.TestCase):
    def test_source_only_census_and_sha_integrity(self):
        raw={url:zipped([(11,year)]) for year,url in audit.ORIGINAL_URLS.items()}
        census=audit.source_census(raw.__getitem__)
        self.assertEqual(census["status"],"SOURCE_ONLY_CENSUS_NO_DYADYEAR_OUTCOMES_READ")
        self.assertEqual(len(census["sources"]),4)
        self.assertEqual(len(census["sources"][0]["zip_sha256"]),64)
        self.assertIn("dyad_id",census["sources"][0]["csv_header_only"]["columns"])
        with self.assertRaises(SourceError):
            audit.identify_csv_member(b"not-zip")

    def test_dyad_year_exact_not_any_year(self):
        raw=zipped([(11,2024),(12,2025),(11,2023)])
        meta,active,ever=audit.parse_dyadic_year(raw,2024)
        self.assertEqual(active,{11})
        self.assertIn(12,ever)
        self.assertNotIn(12,active)
        self.assertEqual(meta["target_year_rows"],1)
        with self.assertRaises(SourceError):
            audit.parse_dyadic_year(zipped([(11,2024),(11,2024)]),2024)

    def test_missing_dyad_is_not_inactive_and_aggregate_conservation(self):
        from audit_candidate_ged_event_dyad_fates import parse_event
        def candidate(eid,dyad,best):
            return parse_event({"id":eid,"country_id":"501","year":"2025",
                "type_of_violence":"1","date_prec":"1",
                "date_start":"2025-05-08","date_end":"2025-05-08",
                "best":str(best),"code_status":"Check dyad","dyad_new_id":dyad})
        cases=[candidate("a","11",3),candidate("b","11",2),
               candidate("c","",5),candidate("d","12",7)]
        expected={"year":2025,"country_id":501,"country":"Synthetic",
            "retained_ged_threshold_5":False,"candidate_q3_best":17,
            "ged_first_annual_best":0,"candidate_n_eligible_events":4,
            "candidate_code_status_best":{"check dyad":17}}
        out=audit.analyze_case(expected,cases,{11},{11,12},{11:16,12:7})
        self.assertEqual(out["n_candidate_may_events_unavailable_dyad"],1)
        self.assertEqual(out["n_distinct_candidate_may_dyads_active_in_original_dyadic_year"],1)
        self.assertEqual(out["n_distinct_candidate_may_dyads_not_active_in_original_dyadic_year"],1)
        self.assertEqual(out["candidate_may_best_active_dyads"],5)
        self.assertEqual(out["candidate_may_best_inactive_dyads"],7)
        self.assertEqual(out["n_distinct_candidate_may_dyads_not_active_that_appear_in_dyadic_other_year"],1)
        self.assertEqual(out["n_distinct_candidate_may_dyads_ever_active_in_historical_dyadic_edition"],2)
        self.assertEqual(out["n_candidate_q3_jan_sep_dyads_ge25_best"],0)
        # If a dyad is active in a different year, UCDP GED can still include its events.
        # It must NOT be misclassified as never eligible in historical Dyadic.
        peru_like=audit.analyze_case(expected,cases,set(),{11,12},{11:16,12:7})
        self.assertEqual(peru_like["n_distinct_candidate_may_dyads_active_in_original_dyadic_year"],0)
        self.assertEqual(peru_like["n_distinct_candidate_may_dyads_ever_active_in_historical_dyadic_edition"],2)
        with self.assertRaises(SourceError):
            audit.analyze_case({**expected,"candidate_q3_best":18},
                               cases,{11},{11,12},{11:16,12:7})

    def test_numeric_dyad_and_year_date_window(self):
        self.assertIsNone(audit.numeric_dyad(""))
        self.assertIsNone(audit.numeric_dyad("Unknown"))
        self.assertIsNone(audit.numeric_dyad("-200"))
        self.assertEqual(audit.numeric_dyad("012"),12)
        import csv
        s=io.StringIO(newline="")
        cols=["id","year","country_id","type_of_violence","date_prec",
              "date_start","date_end","best","dyad_new_id"]
        w=csv.DictWriter(s,fieldnames=cols);w.writeheader()
        for date_,value in (("2022-01-01",10),("2022-09-30",11),("2022-10-01",99)):
            w.writerow({"id":date_,"year":2022,"country_id":111,
                "type_of_violence":1,"date_prec":1,"date_start":date_,
                "date_end":date_,"best":value,"dyad_new_id":23})
        totals,events=audit.candidate_q3_year_by_dyad(s.getvalue().encode(),
                                                      2022,{23})
        self.assertEqual(totals[23],21)
        self.assertEqual(events[23],2)


if __name__=="__main__":
    unittest.main()
