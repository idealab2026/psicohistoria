#!/usr/bin/env python3
"""UCDP GED / GDELT media-footprint matcher: synthetic tests and fail-closed controls."""
import io
import unittest
from datetime import date,timedelta
from zipfile import ZipFile,ZIP_DEFLATED
from unittest.mock import patch

from audit_geo_ged_gdelt_independent_media_events import (
    CASES, EVENTS_PER_CASE, GDELT_BASE, MIN_GDELT_ROWS,
    eligible_ged_event, gdelt_day_url, geo_km, parse_gdelt_day,
    match_event, anchored_cases, analyze,
)


def official_event(**overrides):
    row={
        "id":"123","year":"2021","country_id":"517","best":"7",
        "date_start":"2021-06-03","date_end":"2021-06-03",
        "latitude":"-1.95","longitude":"30.05","type_of_violence":"1"}
    row.update(overrides)
    return row


def zipped(lines,name="20210603.export.CSV"):
    output=io.BytesIO()
    with ZipFile(output,"w",ZIP_DEFLATED) as z:
        z.writestr(name,"\n".join("\t".join(v) for v in lines)+"\n")
    return output.getvalue()


def gdelt_row(gid=51,day="20210603",country="RW",root="18",
              lat="-1.95",lon="30.05"):
    parts=[""]*58
    parts[0]=str(gid)
    parts[1]=day
    parts[28]=root
    parts[51]=country
    parts[53]=lat
    parts[54]=lon
    return parts


class GedGdeltMediaTests(unittest.TestCase):
    def test_predeclared_cases_not_tuned_to_matching(self):
        self.assertEqual(CASES,(
            (517,2021,"RW","23.1->24.1"),
            (516,2022,"BY","23.1->24.1"),
            (101,2021,"VE","24.1->25.1")))
        self.assertEqual(EVENTS_PER_CASE,2)

    def test_ged_dates_reject_uncertain_period(self):
        self.assertIsNotNone(eligible_ged_event(official_event()))
        self.assertIsNone(eligible_ged_event(official_event(date_end="2021-06-07")))
        self.assertIsNone(eligible_ged_event(official_event(date_start="2020-01-01")))
        self.assertIsNone(eligible_ged_event(official_event(best="0")))
        self.assertIsNone(eligible_ged_event(official_event(latitude="999")))

    def test_date_window_includes_report_lag_only(self):
        d=date(2021,6,3)
        self.assertEqual(gdelt_day_url(d),
                         GDELT_BASE+"20210603.export.CSV.zip")
        self.assertEqual(gdelt_day_url(d+timedelta(days=1)),
                         GDELT_BASE+"20210604.export.CSV.zip")
        with self.assertRaises(ValueError):
            gdelt_day_url(date(2008,1,1))

    def test_haversine_bounded_and_geographically_plausible(self):
        self.assertAlmostEqual(geo_km(-1.95,30.05,-1.95,30.05),0.)
        self.assertLess(geo_km(-1.95,30.05,-2.,30.08),10)
        self.assertGreater(geo_km(-1.95,30.05,45.,30.08),1000)

    def test_gdelt_v1_tab_delimited_parser(self):
        rows=[gdelt_row(gid=i) for i in range(1,MIN_GDELT_ROWS+1)]
        rows[0]=gdelt_row(gid=1,country="VE")
        data=parse_gdelt_day(zipped(rows),date(2021,6,3),{"RW"})
        self.assertEqual(data["total_news_coded_events"],MIN_GDELT_ROWS)
        self.assertEqual(data["selected_country_rows"],MIN_GDELT_ROWS-1)
        self.assertEqual(data["geocoded_selected_country_rows"],MIN_GDELT_ROWS-1)
        self.assertTrue(all(x["violent_root"] for x in data["events"]))

    def test_spatial_match_requires_date_country_and_violence(self):
        sample={"event_date":"2021-06-03","lat":-1.95,"lon":30.05}
        obs=[
            {"GDELT_event_id":1,"SQLDATE":"20210603","CAMEO_root":"18",
             "violent_root":True,"FIPS":"RW","lat":-1.95,"lon":30.05},
            {"GDELT_event_id":2,"SQLDATE":"20210603","CAMEO_root":"14",
             "violent_root":False,"FIPS":"RW","lat":-1.95,"lon":30.05},
            {"GDELT_event_id":3,"SQLDATE":"20210604","CAMEO_root":"19",
             "violent_root":True,"FIPS":"RW","lat":-1.95,"lon":30.05},
            {"GDELT_event_id":4,"SQLDATE":"20210603","CAMEO_root":"20",
             "violent_root":True,"FIPS":"VE","lat":-1.95,"lon":30.05},
            {"GDELT_event_id":5,"SQLDATE":"20210603","CAMEO_root":"19",
             "violent_root":True,"FIPS":"RW","lat":50.,"lon":30.05},
        ]
        result=match_event(sample,obs,"RW")
        self.assertEqual(result["violent_same_date_near100km_n"],1)
        self.assertEqual(result["violent_same_date_near25km_n"],1)
        self.assertEqual(result["same_date_country_nonviolent_near100km_n"],1)
        self.assertEqual(result["same_SQLDATE_same_FIPS_violent_root_events_n"],2)
        self.assertIs(result["fatality_confirmation_from_GDELT"],False)

    def test_match_without_news_is_not_disproof(self):
        event={"event_date":"2022-05-05","lat":-3.3,"lon":29.9}
        result=match_event(event,[],"BY")
        self.assertEqual(result["violent_same_date_near100km_n"],0)
        self.assertIs(result["one_to_one_event_match_verified"],False)

    def test_anchor_revised_zero_to_low_only(self):
        folds=[]
        for cid,y,fips,pair in CASES:
            folds.append({"source_pair":pair,"origin_year":y,
                          "training_zero_low_events":[
                              {"GWNO":cid,"year":y,"old":0,"new":1}]})
        base={"schema":"idealab.psico.geo_h2_three_adjacent_vintage_zero_low_11_origin.v1",
              "original_GEO2027_SHA256":"abc",
              "historical_asof_issues_genuinely_timestamped":False,
              "folds":folds}
        with patch("audit_geo_ged_gdelt_independent_media_events.SOURCE_SHA256","abc"):
            self.assertEqual(len(anchored_cases(base)),3)
            base["folds"][0]["training_zero_low_events"][0]["new"]=30
            with self.assertRaises(ValueError):
                anchored_cases(base)

    def test_original_issue_provenance_rejection(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):
            analyze({"case_selection":{}},{},{})


if __name__=="__main__":
    unittest.main()
