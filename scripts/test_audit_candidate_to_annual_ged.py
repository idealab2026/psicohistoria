#!/usr/bin/env python3
"""Adversarial synthetic tests; all country/event labels are fictitious."""
import csv
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_candidate_to_annual_ged as experiment
from check_ucdp_candidate_asof import SourceError


def csv_rows(rows, annual=False):
    columns = ("id", "year", "country_id", "type_of_violence", "date_prec",
               "date_start", "date_end", "best") if annual else (
               "id", "country_id", "type_of_violence", "date_prec",
               "date_start", "date_end", "best", "code_status")
    f=io.StringIO(newline="")
    writer=csv.DictWriter(f,fieldnames=columns)
    writer.writeheader()
    for row in rows:
        writer.writerow(dict(zip(columns,row)))
    return f.getvalue().encode("utf8")


def ged_zip(year, rows, extra_member=False):
    data=io.BytesIO()
    member=f"GEDEvent_v{25 if year==2024 else 26}_1.csv"
    with zipfile.ZipFile(data,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr(member,csv_rows(rows,annual=True))
        if extra_member:
            z.writestr("README.txt","Synthetic GED ZIP fixture")
    return data.getvalue()


class CandidateAnnualValidationTests(unittest.TestCase):
    def test_source_census_no_labels_and_strict_zip_header(self):
        raw={
            experiment.GED_URL[2024]:ged_zip(2024,[
                ("an1",2024,1,1,1,"2024-05-12","2024-05-12",5)
            ],True),
            experiment.GED_URL[2025]:ged_zip(2025,[
                ("an2",2025,1,1,1,"2025-05-12","2025-05-12",5)
            ],True),
        }
        census=experiment.annual_census(raw.__getitem__)
        self.assertEqual(census["status"],"SOURCES_ONLY_NO_OUTCOMES_EVALUATED")
        self.assertEqual(len(census["sources"]),2)
        self.assertEqual(len(census["sources"][0]["source_sha256"]),64)
        with self.assertRaises(SourceError):
            experiment.examine_zip(b"not actually an archive")

    def test_annual_exact_30_and_90_days_and_no_year_leakage(self):
        raw=ged_zip(2024,[
            ("old",2023,1,1,1,"2023-05-15","2023-05-15",900),
            ("first",2024,1,1,1,"2024-05-01","2024-05-01",3),
            ("last30",2024,1,1,1,"2024-05-30","2024-05-30",4),
            ("next",2024,1,1,1,"2024-05-31","2024-05-31",5),
            ("last90",2024,1,1,1,"2024-07-29","2024-07-29",6),
            ("beyond",2024,1,1,1,"2024-07-30","2024-07-30",1000),
            ("cross",2024,1,1,1,"2024-04-30","2024-05-01",999),
            ("nstate",2024,1,2,1,"2024-05-15","2024-05-15",800),
            ("imprecise",2024,1,1,4,"2024-05-16","2024-05-16",400),
        ],True)
        meta,events,id_index=experiment.read_annual(raw,2024,{1})
        day30,ids30,_=experiment.rollup(events,2024,30)
        day90,ids90,_=experiment.rollup(events,2024,90)
        self.assertEqual(day30[1],7)
        self.assertEqual(day90[1],18)
        self.assertEqual(set(ids30[1]),{"first","last30"})
        self.assertIn("beyond",id_index)
        self.assertNotIn("old",id_index)
        self.assertEqual(meta["target_year_rows"],8)

    def test_confusion_denominator_and_id_match_not_causality(self):
        prior={1:3,2:0}
        cand={1:7,2:0}
        ged={1:0,2:8}
        comparison=experiment.paired_metrics(prior,cand,ged,5,{1:"A",2:"B"})
        self.assertEqual(comparison["n_at_risk"],2)
        self.assertEqual(comparison["candidate_only_country_ids"],[1])
        self.assertEqual(comparison["ged_only_country_ids"],[2])
        self.assertEqual(comparison["candidate_positive_matching_ged_share"],0)
        self.assertEqual(comparison["candidate_sensitivity_to_ged_label"],0)
        measured=experiment.matching_event_ids({1:["a","b"]},{"a":(1,1,None,None)},{1:["b"]},{1:"A"})
        self.assertEqual(measured["candidate_id_in_annual_target_year_any_type_any_date"],1)
        self.assertEqual(measured["candidate_id_in_annual_same_country_same_window"],1)

    def test_full_report_replays_six_vintages_and_two_annual_source_hashes(self):
        population=list(range(1,197))
        raw_universe=json.dumps({"countries":[
            {"country_id":c,"country":f"Synthetic {c}"} for c in population
        ]}).encode("utf8")
        candidates={}
        originals={}
        archive_rows=[]
        annual_inputs={}
        threshold_rows={}
        saved_years=[]
        for year in experiment.YEARS:
            sources={}
            for month in (3,6,9):
                url=(experiment.archive_url(year,month) if month!=6
                     else experiment.url_for(year,2))
                death=3 if month==3 else 6 if month==6 else 4
                dt=f"{year}-03-02" if month==3 else f"{year}-05-12"
                raw=csv_rows([(
                    f"same-{year}-{month}",1,1,1,dt,dt,death,
                    "Check dyad" if month==9 else "Clear"
                )])
                candidates[url]=raw
                archive_rows.append({"year":year,"month":month,
                    "source_url":url,"source_sha256":hashlib.sha256(raw).hexdigest()})
            annual_inputs[experiment.GED_URL[year]]=ged_zip(year,[
                (f"same-{year}-9",year,1,1,1,f"{year}-05-12",f"{year}-05-12",7),
                (f"annual-new-{year}",year,2,1,1,f"{year}-05-16",f"{year}-05-16",8),
            ])
            threshold_rows[str(year)]={
                str(t):{str(h):{"at_risk":195 if t==1 else 196,
                               "positive":0}
                        for h in experiment.HORIZONS}
                for t in experiment.THRESHOLDS
            }
            saved_years.append({"year":year,"thresholds":{
                "5":{"risk_set":196,
                      "q2_positive_country_ids":[1],
                      "q3_positive_country_ids":[]}
            }})
        rates={str(t):{str(h):{
            str(year):threshold_rows[str(year)][str(t)][str(h)]
            for year in experiment.YEARS
        } for h in experiment.HORIZONS} for t in experiment.THRESHOLDS}
        registry={"status":"RETROSPECTIVE_REVISIONS_NOT_ASOF_NOT_PROSPECTIVE",
                  "nine_official_archives":archive_rows}
        stability={"status":"POST_SELECTION_SOURCE_REVISION_SENSITIVITY_NOT_PROSPECTIVE",
                   "may_label_revision_by_year":saved_years}
        grid={"universe_sha256":hashlib.sha256(raw_universe).hexdigest(),
              "yearly_threshold_rates":rates}
        pins={year:hashlib.sha256(annual_inputs[experiment.GED_URL[year]]).hexdigest()
              for year in experiment.YEARS}
        result=experiment.build_report(candidate_fetcher=candidates.__getitem__,
            annual_fetcher=annual_inputs.__getitem__,raw_universe=raw_universe,
            candidate_registry=registry,prior_stability=stability,prior_grid=grid,
            annual_pins=pins)
        self.assertEqual(len(result["country_vectors"]),392)
        self.assertEqual(len(result["source_details"]),8)
        self.assertEqual(result["prospective_issued_probabilities"],0)
        x=result["by_year_threshold_and_horizon"]["2024"]["5"]["30"]
        self.assertEqual(x["q2_vs_annual"]["both_positive"],1)
        self.assertEqual(x["q3_vs_annual"]["ged_only"],2)
        self.assertEqual(result["candidate_q3_may_exact_id_overlap_with_annual"]["2024"][
            "candidate_id_in_annual_same_country_same_window"],1)
        modified=dict(annual_inputs)
        modified[experiment.GED_URL[2025]]=modified[experiment.GED_URL[2025]]+b"\n"
        with self.assertRaises(SourceError):
            experiment.build_report(candidate_fetcher=candidates.__getitem__,
                annual_fetcher=modified.__getitem__,raw_universe=raw_universe,
                candidate_registry=registry,prior_stability=stability,prior_grid=grid,
                annual_pins=pins)


if __name__=="__main__":
    unittest.main()
