#!/usr/bin/env python3
"""Synthetic-only UCDP annual-resolution tests, never real outcomes."""
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
import audit_candidate_ged_2021_22 as ex
from check_ucdp_candidate_asof import SourceError


def csv_payload(rows, annual=False):
    keys = ("id","year","country_id","type_of_violence","date_prec","date_start",
            "date_end","best") if annual else (
            "id","country_id","type_of_violence","date_prec","date_start",
            "date_end","best","code_status")
    stream=io.StringIO(newline="")
    w=csv.DictWriter(stream,fieldnames=keys)
    w.writeheader()
    for row in rows:
        w.writerow(dict(zip(keys,row)))
    return stream.getvalue().encode("utf8")


def zipped_annual(year,rows):
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,"w",zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"GEDEvent_v{year+1-2000}_1.csv",csv_payload(rows,True))
    return mem.getvalue()


def sample_settings():
    names=[{"country_id":c,"country":f"synthetic-{c}"} for c in range(1,197)]
    universe=json.dumps({"countries":names}).encode("utf8")
    candidate_raw={}
    annual_raw={}
    prior_sources=[]
    prior_year={}
    for y in ex.YEARS:
        prior_year[str(y)]={}
        for m in (3,9):
            dt=f"{y}-03-02" if m==3 else f"{y}-05-12"
            v=3 if m==3 else 6
            row=(f"same-{y}",1,1,1,dt,dt,v,"Clear")
            blob=csv_payload([row])
            url=ex.source_url(y,m)
            candidate_raw[url]=blob
            prior_sources.append({"year":y,"month":m,"source_url":url,
                                  "sha256":hashlib.sha256(blob).hexdigest(),
                                  "source_bytes":len(blob)})
        annual_raw[ex.ORIGINAL_ZIP_URLS[y]]=zipped_annual(y,[
            (f"same-{y}",y,1,1,1,f"{y}-05-12",f"{y}-05-12",5),
            (f"ged-{y}",y,2,1,1,f"{y}-05-12",f"{y}-05-12",8)
        ])
    for t in ex.THRESHOLDS:
        prior_year[str(t)]={}
        for h in ex.HORIZONS:
            prior_year[str(t)][str(h)]={}
            for y in ex.YEARS:
                positive=int(t in (5,))  # q1 prior=3, q3 result=6
                risk=195 if t==1 else 196
                prior_year[str(t)][str(h)][str(y)]={
                    "at_risk":risk,"positive":positive}
    grid={"status":"EXPLORATORY_HISTORICAL_NOT_ASOF_NOT_ISSUED",
          "universe_sha256":hashlib.sha256(universe).hexdigest(),
          "source_snapshots":prior_sources,
          "yearly_threshold_rates":prior_year}
    previous={"status":"RETROSPECTIVE_FINAL_VINTAGE_COMPARISON_NOT_PROSPECTIVE",
              "by_year_threshold_and_horizon":{
                str(y):{str(t):{str(h):{"q3_vs_annual":{
                    "n_at_risk":196,"candidate_positive":0,"ged_positive":0,
                    "both_positive":0,"candidate_only":0,"ged_only":0,
                    "both_negative":196,"disagreements":0}}
                    for h in ex.HORIZONS} for t in ex.THRESHOLDS} for y in (2024,2025)
              }}
    sha={y:hashlib.sha256(annual_raw[ex.ORIGINAL_ZIP_URLS[y]]).hexdigest()
         for y in ex.YEARS}
    return candidate_raw,annual_raw,universe,grid,previous,sha


class EarlyAnnualGEDTests(unittest.TestCase):
    def test_official_versions_and_source_only_census(self):
        self.assertEqual(ex.ORIGINAL_ZIP_URLS[2021].split("/")[-1],"ged221-csv.zip")
        self.assertEqual(ex.ORIGINAL_ZIP_URLS[2022].split("/")[-1],"ged231-csv.zip")
        _, annual, _, _, _, _=sample_settings()
        manifest=ex.source_census(annual.__getitem__)
        self.assertEqual(manifest["status"],"SOURCES_ONLY_NO_GED_OUTCOMES_READ")
        self.assertEqual(len(manifest["manifest"]),2)
        self.assertEqual(len(manifest["manifest"][0]["sha256"]),64)
        with self.assertRaises(SourceError):
            ex.scan_annual_zip(b"not-zip",2021,{1})

    def test_candidates_only_exact_earlier_eligible_dates_and_no_duplicate_ids(self):
        f=csv_payload([
            ("a",1,1,1,"2022-05-01","2022-05-01",2,"Clear"),
            ("b",1,1,1,"2022-05-30","2022-05-30",3,"Check dyad"),
            ("c",1,1,1,"2022-07-29","2022-07-29",4,"Clear"),
            ("d",1,1,1,"2022-07-30","2022-07-30",100,"Clear"),
            ("e",1,1,1,"2022-04-30","2022-05-02",200,"Clear"),
            ("f",1,1,0,"2022-05-09","2022-05-09",999,"Clear"),
            ("g",1,2,1,"2022-05-09","2022-05-09",999,"Clear"),
        ])
        meta,events=ex.scan_candidate(f,2022,9,{1})
        thirty,ids,_=ex.rollup(events,2022,30)
        ninety,_,_=ex.rollup(events,2022,90)
        self.assertEqual(thirty[1],5)
        self.assertEqual(ninety[1],9)
        self.assertEqual(set(ids[1]),{"a","b"})
        self.assertEqual(meta["skip_unknown_precision_zero"],1)
        with self.assertRaises(SourceError):
            ex.scan_candidate(csv_payload([("dup",1,1,1,"2022-05-01","2022-05-01",2,"Clear")]*2),
                              2022,9,{1})

    def test_annual_target_year_exclusion_and_event_crossing(self):
        raw=zipped_annual(2022,[
            ("old",2021,1,1,1,"2021-05-12","2021-05-12",999),
            ("a",2022,1,1,1,"2022-05-01","2022-05-01",4),
            ("b",2022,1,1,1,"2022-05-30","2022-05-30",3),
            ("c",2022,1,1,1,"2022-07-29","2022-07-29",5),
            ("d",2022,1,1,1,"2022-04-30","2022-05-02",999),
            ("e",2022,1,3,1,"2022-05-12","2022-05-12",999),
        ])
        meta,events,index=ex.scan_annual_zip(raw,2022,{1})
        thirty,_,_=ex.rollup(events,2022,30)
        ninety,_,_=ex.rollup(events,2022,90)
        self.assertEqual(meta["target_year_rows"],5)
        self.assertEqual(thirty[1],7)
        self.assertEqual(ninety[1],12)
        self.assertNotIn("old",index)
        self.assertIn("d",index)

    def test_full_two_year_report_and_anti_tamper(self):
        c,a,u,g,p,h=sample_settings()
        result=ex.build_report(cand_fetcher=c.__getitem__,ged_fetcher=a.__getitem__,
                               universe=u,grid=g,previous=p,annual_pins=h)
        self.assertEqual(len(result["country_vectors_new"]),392)
        self.assertEqual(len(result["source_provenance"]),6)
        self.assertEqual(result["new_prospective_issues"],0)
        self.assertFalse(result["candidate_original_release_dates_certified"])
        row=result["years_new_by_threshold_horizon"]["2021"]["5"]["30"]["candidate_q3_vs_annual"]
        self.assertEqual((row["both_positive"],row["ged_only"],row["candidate_only"]),(1,1,0))
        pooled=result["pooled_2021_22_24_25_results"]["5"]["30"]
        self.assertEqual((pooled["both_positive"],pooled["ged_only"]),(2,2))
        # No source bytes can be modified without blocking.
        a[ex.ORIGINAL_ZIP_URLS[2021]]+=b"\n"
        with self.assertRaises(SourceError):
            ex.build_report(cand_fetcher=c.__getitem__,ged_fetcher=a.__getitem__,
                            universe=u,grid=g,previous=p,annual_pins=h)


if __name__=="__main__":
    unittest.main()
