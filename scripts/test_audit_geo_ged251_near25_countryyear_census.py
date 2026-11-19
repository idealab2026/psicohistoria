#!/usr/bin/env python3
"""Boundary tests for near-25 fatality country-year riskset protocol."""
import unittest
from datetime import date, timedelta

import audit_geo_ged251_near25_countryyear_census as m


def ev(eid, day=1, lon=29, lat=0, precision=1):
    t=date(2022,6,day)
    return {"id":eid,"start":t,"end":t,"lat":lat,
            "lon":lon,"where_prec":precision,"best":1}


class NearThresholdAnnual(unittest.TestCase):
    def test_bands_are_exhaustive_and_boundary_correct(self):
        expected={0:"no_recorded_type1_deaths",1:"positive_below_band",
                  14:"positive_below_band",15:"below25_in_band",
                  24:"below25_in_band",25:"at_or_above25_in_band",
                  35:"at_or_above25_in_band",36:"above_band"}
        for k,v in expected.items():
            self.assertEqual(m.bands_partition(k),v)
        with self.assertRaises(ValueError):
            m.bands_partition(-1)

    def test_deletion_pivotal_only_if_active(self):
        self.assertFalse(m.pivotal_under_one_record_removal(24,24))
        self.assertTrue(m.pivotal_under_one_record_removal(25,1))
        self.assertTrue(m.pivotal_under_one_record_removal(30,6))
        self.assertFalse(m.pivotal_under_one_record_removal(30,5))
        self.assertFalse(m.pivotal_under_one_record_removal(36,10))
        self.assertTrue(m.pivotal_under_one_record_removal(36,12))

    def test_inconsistent_fatalities_rejected(self):
        for t,b in ((25,26),(0,1),(-1,1),(20,-1)):
            with self.assertRaises(ValueError):
                m.pivotal_under_one_record_removal(t,b)

    def test_same_location_distant_day_excluded(self):
        pairs=m.candidates_in_country_year([ev(1,1),ev(2,20)])
        self.assertEqual(len(pairs),0)

    def test_same_time_different_geo_excluded(self):
        pairs=m.candidates_in_country_year([ev(1),ev(2,lon=33)])
        self.assertEqual(len(pairs),0)

    def test_identical_location_same_time_is_only_candidate(self):
        pairs=m.candidates_in_country_year([ev(2),ev(1)])
        self.assertEqual(len(pairs),1)
        self.assertEqual(pairs[0]["pair_ids"],[1,2])
        self.assertFalse(pairs[0]["duplicate_identity_proven"] if
                         "duplicate_identity_proven" in pairs[0] else False)

    def test_high_vs_low_location_precision(self):
        pair=m.candidates_in_country_year([
            ev(1,precision=1),ev(2,precision=4)])[0]
        self.assertFalse(pair["both_where_prec_1_or_2"])

    def test_inclusive_window_and_threshold_constants(self):
        self.assertEqual((m.BAND_MIN,m.BAND_MAX),(15,35))
        self.assertEqual(m.TARGET_THRESHOLD,25)
        self.assertEqual(m.YEARS,(2021,2022))
        self.assertEqual(m.NEAR_GAP_DAYS,3)
        self.assertEqual(m.NEAR_KM,25)


if __name__=="__main__":
    unittest.main()
