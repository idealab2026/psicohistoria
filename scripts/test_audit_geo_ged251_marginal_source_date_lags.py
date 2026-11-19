#!/usr/bin/env python3
"""Adversarial guards: publishing dates are NOT dates of violent incidents."""
from datetime import date
import unittest
from unittest.mock import patch

import audit_geo_ged251_marginal_source_date_lags as m


class SourceDateSemantics(unittest.TestCase):
    def test_UCDP_1753_missing_sentinel_is_not_a_historical_lag(self):
        good,missing,invalid=m.publication_dates("1753-01-01;2022-06-24")
        self.assertEqual(good,[date(2022,6,24)])
        self.assertEqual((missing,invalid),(1,0))

    def test_all_dates_missing(self):
        good,missing,invalid=m.publication_dates("NA;1753-01-01;")
        self.assertEqual(good,[])
        self.assertEqual(missing,3)
        self.assertEqual(invalid,0)

    def test_invalid_date_retained_as_invalid_not_imputed(self):
        good,missing,invalid=m.publication_dates("garbage;2022-13-33;2022-12-20")
        self.assertEqual(good,[date(2022,12,20)])
        self.assertEqual((missing,invalid),(0,2))

    def test_publication_is_normal_next_day_not_an_error(self):
        v=m.lag_classification(date(2022,12,20),date(2022,12,19),
                               date(2022,12,19),1)
        self.assertEqual(v,"publication_one_day_after_event_end")
        self.assertNotIn("error",v)

    def test_exact_day_same_day_category(self):
        self.assertEqual(m.lag_classification(date(2022,6,2),date(2022,6,2),
                          date(2022,6,2),1),"publication_within_event_window")

    def test_publication_after_multiday_event_end(self):
        self.assertEqual(m.lag_classification(date(2022,6,15),date(2022,6,1),
                          date(2022,6,10),4),
                         "publication_2_to_7_days_after_event_end")

    def test_during_event_window_is_not_an_inversion(self):
        self.assertEqual(m.lag_classification(date(2022,6,3),date(2022,6,1),
                          date(2022,6,10),4),"publication_within_event_window")

    def test_publication_before_start_is_only_a_review_trigger(self):
        self.assertEqual(m.lag_classification(date(2022,6,1),date(2022,6,2),
                          date(2022,6,2),1),
                          "publication_before_event_window_not_a_proven_date_error")

    def test_missing_publication_has_no_imputed_lag(self):
        self.assertEqual(m.lag_classification(None,date(2022,6,2),
                          date(2022,6,2),1),"no_valid_publication_date")

    def test_long_reporting_delay(self):
        self.assertEqual(m.lag_classification(date(2023,3,30),date(2022,6,1),
                          date(2022,6,1),1),
                          "publication_over_30_days_after_event_end")

    def test_reversed_time_window_rejected(self):
        with self.assertRaises(ValueError):
            m.lag_classification(date(2022,6,2),date(2022,6,3),
                          date(2022,6,1),1)

    def test_marginal_countryyear_cohort_is_locked(self):
        base,selection=m.read_source_cohort()
        self.assertEqual(len(selection),14)
        self.assertEqual(base["marginal_pivotal_event_rows_n"],13)
        self.assertEqual(base["total_frame_country_year_cells_n"],392)

    def test_prior_source_text_discordances_require_real_reported_dates(self):
        observed={
            (500,2022):[
                {"GED_event_id":460859,"GWNO":500,"year":2022,
                 "date_start":"2022-12-21",
                 "date_end":"2022-12-21","date_prec":1,"best":2,
                 "earliest_publication_date":"2022-12-21"},
                {"GED_event_id":462156,"GWNO":500,"year":2022,
                 "date_start":"2022-12-19",
                 "date_end":"2022-12-19","date_prec":1,"best":2,
                 "earliest_publication_date":"2022-12-19"},
            ]}
        v=m.manual_text_discordances(observed)
        self.assertEqual([x["GED_event_id"] for x in v],[460859,462156])
        self.assertEqual([x["coded_minus_reported_event_day_days"]
                          for x in v],[1,1])
        self.assertFalse(any(x["coding_error_adjudicated"] for x in v))

    def test_unchanged_issued_GED25_1_source(self):
        self.assertEqual(m.GED_SHA,
            "e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d")


if __name__=="__main__":
    unittest.main()
