#!/usr/bin/env python3
"""Synthetic adversarial tests: no real UCDP event identifiers or people."""
import csv
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parent))
import audit_candidate_ged_event_dyad_fates as a
from check_ucdp_candidate_asof import SourceError


def row(eid,year,country,violence,when,best,status="Clear",dyad="7",
        precision=1,end=None):
    return {
        "id":eid,"year":str(year),"country_id":str(country),
        "type_of_violence":str(violence),"date_prec":str(precision),
        "date_start":when,"date_end":when if end is None else end,
        "best":str(best),"code_status":status,"dyad_new_id":dyad,
        "side_a_new_id":"100","side_b_new_id":"200"
    }


def csv_bytes(events):
    stream=io.StringIO(newline="")
    w=csv.DictWriter(stream,fieldnames=[
        "id","year","country_id","type_of_violence","date_prec",
        "date_start","date_end","best","code_status","dyad_new_id",
        "side_a_new_id","side_b_new_id"])
    w.writeheader()
    w.writerows(events)
    return stream.getvalue().encode("utf8")


def annual_zip(year,events):
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"GEDEvent_v{a.EDITION[year]}_1.csv",csv_bytes(events))
    return buffer.getvalue()


def parse(ev):
    return a.parse_event(ev)


def case_exp(year,country,cand,ged,status,events,shared,retained):
    return {"year":year,"country_id":country,"country":f"Synthetic {country}",
        "candidate_q3_may30_best":cand,"ged_first_annual_may30_best":ged,
        "candidate_code_status_best":status,"candidate_state_events":events,
        "candidate_same_country_window_exact_id_match_count":shared,
        "retained_ged":retained}


class EventFateTests(unittest.TestCase):
    def test_exact_shared_death_reestimation_and_annual_only(self):
        candidate=[parse(row("x",2025,140,1,"2025-05-11",7,"Clear","D1"))]
        annual_same=parse(row("x",2025,140,1,"2025-05-11",4,"Clear","D2"))
        annual_added=parse(row("new",2025,140,1,"2025-05-12",3,"Clear","D3"))
        exp=case_exp(2025,140,7,7,{"clear":7},1,1,True)
        result=a.analyze_case(2025,140,candidate,[annual_same,annual_added],
                              {"x":annual_same},{"D2","D3"},exp,
                              {"candidate_dyad":True,"annual_dyad":True})
        self.assertEqual(result["shared_eligible_same_id_events"],1)
        self.assertEqual(result["shared_candidate_best"],7)
        self.assertEqual(result["shared_ged_best"],4)
        self.assertEqual(result["annual_only_best"],3)
        self.assertEqual(result["candidate_only_best"],0)
        self.assertEqual(result["delta_best_shared_event_reestimation"],-3)
        self.assertEqual(result["shared_id_dyad_changed"],1)
        self.assertTrue(result["decomposition_reconciles"])

    def test_absent_id_never_interpreted_as_absent_violence(self):
        candidate=[parse(row("a",2024,771,1,"2024-05-05",3,"Clear","D8")),
                   parse(row("b",2024,771,1,"2024-05-12",2,"Clear","D8"))]
        exp=case_exp(2024,771,5,0,{"clear":5},2,0,False)
        res=a.analyze_case(2024,771,candidate,[],{},set(),exp,
                           {"candidate_dyad":True,"annual_dyad":True})
        self.assertEqual(res["candidate_event_id_fates"],
                         {"id_absent_from_annual_all_years":2})
        self.assertEqual(res["candidate_only_best"],5)
        self.assertEqual(res["candidate_nonshared_ids_with_dyad_absent_from_annual_state_year"],2)
        self.assertTrue(res["candidate_minus_ged_cannot_be_interpreted_as_unreal_violence"])

    def test_country_type_temporal_and_event_year_changes_reported_separately(self):
        base=parse(row("x",2025,620,1,"2025-05-10",5))
        cases=[
            (row("x",2024,620,1,"2024-05-10",5),"id_found_in_different_event_year"),
            (row("x",2025,777,1,"2025-05-10",5),"id_reassigned_country"),
            (row("x",2025,620,2,"2025-05-10",5),"id_retyped_nonstate_or_unilateral"),
            (row("x",2025,620,1,"2025-05-10",5,precision=4),"id_changed_temporal_precision"),
            (row("x",2025,620,1,"2025-07-10",5),"id_moved_outside_window"),
            (row("x",2025,777,2,"2025-07-10",5),"id_reassigned_country"),
        ]
        for original,expected in cases:
            with self.subTest(expected=expected):
                change,flags=a.fate(base,parse(original),2025,620)
                self.assertEqual(change,expected)
                if original["country_id"]=="777" and original["type_of_violence"]=="2":
                    self.assertIn("violence_type_changed",flags)
                    self.assertIn("country_changed",flags)

    def test_strict_eligibility_parse_and_double_ids(self):
        rows=[
            row("a",2025,130,1,"2025-05-01",2),
            row("b",2025,130,1,"2025-05-30",3),
            row("c",2025,130,1,"2025-05-31",99),
            row("d",2025,130,1,"2025-04-30",99,end="2025-05-02"),
            row("e",2025,130,1,"2025-05-20",99,precision=0),
            row("f",2025,130,2,"2025-05-21",99),
        ]
        meta,events=a.candidate_focus(csv_bytes(rows),2025,{130:1})
        self.assertEqual(meta["eligible_focus_events"],2)
        self.assertEqual(sum(e["best"] for e in events[130]),5)
        self.assertTrue(meta["has_dyad_new_id"])
        with self.assertRaises(SourceError):
            a.candidate_focus(csv_bytes(rows+[rows[0]]),2025,{130:1})
        with self.assertRaises(SourceError):
            a.candidate_focus(csv_bytes([row("x",2025,130,1,"2025-05-11",-2)]),2025,{130:1})

    def test_annual_zip_index_handles_other_year_and_dyad_target_year(self):
        events=[
            row("seen",2021,135,1,"2021-05-12",16,dyad="D1"),
            row("other-year",2020,135,1,"2020-05-12",3,dyad="D2"),
            row("retype",2021,135,3,"2021-05-11",9,dyad="D3"),
            row("only",2021,135,1,"2021-05-21",3,dyad="D4"),
        ]
        raw=annual_zip(2021,events)
        meta,selected,index,dyads=a.annual_focus(
            raw,2021,{135:1},{"seen","other-year","retype"})
        self.assertEqual(meta["target_year_rows"],3)
        self.assertEqual(len(selected[135]),2)
        self.assertEqual(index["other-year"]["year"],2020)
        self.assertIn("D1",dyads)
        self.assertNotIn("D2",dyads)
        self.assertNotIn("D3",dyads)

    def test_invalid_case_totals_and_status_do_not_slip_through(self):
        event=parse(row("a",2022,461,1,"2022-05-03",8,"Check deaths"))
        expected=case_exp(2022,461,8,0,{"check deaths":8},1,0,False)
        with self.assertRaises(SourceError):
            a.analyze_case(2022,461,[event],[],{},set(),{
                **expected,"candidate_q3_may30_best":9
            },{"candidate_dyad":True,"annual_dyad":True})
        with self.assertRaises(SourceError):
            a.analyze_case(2022,461,[event],[],{},set(),{
                **expected,"candidate_code_status_best":{"clear":8}
            },{"candidate_dyad":True,"annual_dyad":True})


if __name__=="__main__":
    unittest.main()
