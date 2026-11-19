#!/usr/bin/env python3
"""Synthetic adversarial controls for preregistered 2021-22 GED screening."""
import copy
from datetime import date, timedelta
import unittest
from unittest.mock import patch

import audit_geo_ged251_stratified_linkage as m


def ev(eid, year=2021, gwno=516, day=5, duration=0, wp=1, lat=-2.7, lon=29.2):
    start = date(year, 6, day)
    return dict(id=eid, year=year, GWNO=gwno, best=1, start=start,
                end=start + timedelta(days=duration), where_prec=wp,
                lat=lat, lon=lon)


class StratifiedScreening(unittest.TestCase):
    def test_stratum_separation_date_and_precision(self):
        self.assertEqual(m.classify_stratum(ev(1)), "day_highgeo")
        self.assertEqual(m.classify_stratum(ev(2, wp=3)), "day_lowgeo")
        self.assertEqual(m.classify_stratum(ev(3, duration=2)), "interval_highgeo")
        self.assertEqual(m.classify_stratum(ev(4, duration=2, wp=7)), "interval_lowgeo")

    def test_sample_deterministic_without_collision_knowledge(self):
        a = [ev(i, year=2021+(i%2), gwno=500+i,
                duration=(i%2), wp=3 if i%4>=2 else 1)
             for i in range(1, 21)]
        # Explicitly ensure at least one of each of the four strata.
        s1, groups = m.pick_sample(a, n=1)
        s2, groups2 = m.pick_sample(list(reversed(a)), n=1)
        self.assertEqual([e["id"] for e in s1], [e["id"] for e in s2])
        self.assertEqual(groups, groups2)
        self.assertEqual(len(s1), 4)

    def test_same_place_far_time_not_direct_candidate(self):
        a, b = ev(1, day=2), ev(2, day=20)
        r = m.inspect_anchor(a, {(516,2021):[a,b]})
        self.assertEqual(r["location_only_neighbors_25km"], 1)
        self.assertEqual(r["space_time_neighbors_gap3d_25km"], 0)
        self.assertFalse(r["identity_or_duplicate_proven"])

    def test_same_time_far_place_not_direct_candidate(self):
        a, b = ev(1), ev(2, lon=31.0)
        r = m.inspect_anchor(a, {(516,2021):[a,b]})
        self.assertEqual(r["time_only_neighbors_gap3d"], 1)
        self.assertEqual(r["space_time_neighbors_gap3d_25km"], 0)

    def test_coarse_location_can_create_false_precision(self):
        a, b = ev(1, wp=4), ev(2, wp=5)
        r = m.inspect_anchor(a, {(516,2021):[a,b]})
        self.assertEqual(r["space_time_neighbors_gap3d_25km"], 1)
        self.assertEqual(r["both_high_geo_precision_neighbors_gap3d_25km"], 0)
        self.assertFalse(r["identity_or_duplicate_proven"])

    def test_precise_neighbor_never_certain_duplicate(self):
        a, b = ev(1), ev(2)
        r = m.inspect_anchor(a, {(516,2021):[a,b]})
        self.assertEqual(r["both_high_geo_precision_neighbors_gap3d_25km"], 1)
        self.assertFalse(r["identity_or_duplicate_proven"])

    def test_interval_overlap_and_three_day_boundary(self):
        a = ev(1,day=5,duration=2)
        b = ev(2,day=10)
        c = ev(3,day=11)
        self.assertEqual(m.gap_days(a,b),3)
        self.assertEqual(m.gap_days(a,c),4)
        r = m.inspect_anchor(a,{(516,2021):[a,b,c]})
        self.assertEqual(r["space_time_neighbors_gap3d_25km"],1)

    def test_other_country_same_coordinates_not_neighbor(self):
        a, b = ev(1,gwno=516), ev(2,gwno=517)
        r = m.inspect_anchor(a,{(516,2021):[a],(517,2021):[b]})
        self.assertEqual(r["same_country_year_other_GED_events"],0)

    def test_wrong_violence_type_and_bad_date_excluded(self):
        raw = dict(id="12",year="2021",country_id="516",best="10",
                   type_of_violence="2",date_start="2021-06-05 00:00:00.000",
                   date_end="2021-06-05 00:00:00.000",
                   where_prec="1",latitude="-2.7",longitude="29.2")
        self.assertIsNone(m.parse_row(raw,{516}))
        raw["type_of_violence"]="1"
        self.assertEqual(m.parse_row(raw,{516})["id"],12)
        raw["date_end"]="2020-06-05 00:00:00.000"
        self.assertIsNone(m.parse_row(raw,{516}))

    def test_mismatched_official_zip_rejected(self):
        with self.assertRaises(ValueError):
            m.parse_ged(b"not-an-official-zip", {516})

    def test_country_diversity_preference(self):
        a = [ev(i, gwno=516) for i in range(1, 6)]
        a += [ev(6, gwno=517)]
        a += [ev(7, wp=3), ev(8, duration=2),
              ev(9, duration=2, wp=3)]
        sample, _ = m.pick_sample(a, n=1)
        self.assertEqual(len(sample),4)

    def test_detect_zero_distance_is_not_individual_confirmation(self):
        a,b=ev(1),ev(2)
        r=m.inspect_anchor(a,{(516,2021):[a,b]})
        self.assertEqual(r["space_time_neighbors_gap0d_5km"],1)
        self.assertFalse(r["identity_or_duplicate_proven"])


if __name__ == "__main__":
    unittest.main()
