#!/usr/bin/env python3
"""No-death-truth, ZIP, temporal and spatial guards for Burundi multi-day audit."""
import io
import unittest
from datetime import date
from zipfile import ZipFile,ZIP_DEFLATED
from unittest.mock import patch

import audit_geo_burundi_2022_multiday_event_evidence as m


def gdelt_row(gid,sql_date,archive_url,lat,lon,root="19",fips="BY",geo_type=4):
    r=[""]*58
    r[0]=str(gid);r[1]=sql_date
    r[26]=root+"0";r[28]=root
    r[49]=str(geo_type);r[50]="Mabayi, Burundi";r[51]=fips
    r[53]=str(lat);r[54]=str(lon);r[56]="20220621000000"
    r[57]=archive_url
    return r


def archive(rows,day):
    mem=io.BytesIO()
    with ZipFile(mem,"w",ZIP_DEFLATED) as z:
        z.writestr(day+".export.CSV","\n".join("\t".join(r) for r in rows)+"\n")
    return mem.getvalue()


class BurundiMultiDay(unittest.TestCase):
    def test_immutable_fact_and_temporal_contract(self):
        self.assertEqual((m.GED_ID,m.GWNO,m.BEST,m.YEAR),(442626,516,10,2022))
        self.assertEqual([x.isoformat() for x in m.WINDOW],
                         ["2022-06-19","2022-06-20","2022-06-21","2022-06-22"])
        self.assertEqual(m.FIPS,"BY")
        self.assertEqual(m.VIOLENT,{"18","19","20"})

    def test_coded_media_not_death_confirmation(self):
        self.assertEqual(m.DOCUMENTS[0]["reported_fatalities"],10)
        self.assertEqual(m.DOCUMENTS[1]["reported_injured"],8)
        self.assertIn("secondary",m.DOCUMENTS[1]["reporting_type"])

    def test_archive_parse_only_country_and_violent_roots(self):
        rows=[gdelt_row(i,"20220621","https://local.example/a",m.LAT,m.LON)
              for i in range(500)]
        rows[1]=gdelt_row(1,"20220621","https://local.example/b",m.LAT,m.LON,
                          root="14")
        rows[2]=gdelt_row(2,"20220621","https://local.example/c",m.LAT,m.LON,
                          fips="RW")
        with patch.object(m,"EXPECTED_DAILY_SHA256",{}):
            d=m.parse_gdelt_day(archive(rows,"20220621"),date(2022,6,21))
        self.assertEqual(d["all_gdelt_event_rows_n"],500)
        self.assertEqual(d["all_burundi_violent_root_rows_n"],498)
        self.assertEqual(len(d["geocoded_violent_rows"]),498)
        self.assertEqual(d["geocoded_violent_rows"][0]["source_host"],"local.example")

    def test_same_day_interval_near_distance_and_lag_separation(self):
        days={}
        for d in m.WINDOW:
            key=d.strftime("%Y%m%d")
            events=[]
            if key=="20220619":
                events=[
                    {"GDELT_event_id":1,"distance_km":0.0,"geo_type":4,
                     "source_host":"reporter.example","inferred_event_date":"20220619"},
                    {"GDELT_event_id":2,"distance_km":110.,"geo_type":1,
                     "source_host":"other.example","inferred_event_date":"20220619"},
                ]
            if key=="20220622":
                events=[{"GDELT_event_id":3,"distance_km":2.,"geo_type":4,
                         "source_host":"third.example","inferred_event_date":"20220622"}]
            days[key]={"date_of_gdelt_daily_archive":d.isoformat(),
                       "source_archive_sha256":"x"*64,"source_archive_bytes":1000,
                       "all_gdelt_event_rows_n":500,
                       "all_burundi_violent_root_rows_n":len(events),
                       "burundi_violent_root_rows_sql_date_in_window_n":len(events),
                       "geocoded_violent_rows":[{
                           **e,"archive_day":d.isoformat(),"DATEADDED":"20220622",
                           "CAMEO_root":"19","CAMEO_event_code":"190",
                           "ActionGeo_name":"Mabayi",
                           "source_url_sha256":"x"*64} for e in events]}
        r=m.evaluate_window(days)
        self.assertEqual(r["same_2022_06_19_to_21_event_date"]["within_25km_n"],1)
        self.assertEqual(r["same_2022_06_19_to_21_event_date"]["within_250km_n"],2)
        self.assertEqual(r["post_interval_2022_06_22_inferred_event_date_not_a_direct_match"]["within_25km_n"],1)
        self.assertEqual(r["same_2022_06_19_to_21_event_date"]["country_centroid_type1_near100km_n"],0)

    def test_incomplete_source_days_refused(self):
        with self.assertRaises(ValueError):
            m.evaluate_window({})

    def test_prior_exact_not_disguised_as_new_primary_sample(self):
        with self.assertRaises(ValueError):
            m.verify_prior({})
        with self.assertRaises(ValueError):
            m.build_report({},{"GED_event_id":m.GED_ID},{})


if __name__=="__main__":
    unittest.main()
