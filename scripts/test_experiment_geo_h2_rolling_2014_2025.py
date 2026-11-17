"""Synthetic-only rolling 2014..2025 GEO H2 chronology and edition checks."""
from __future__ import annotations

import copy
import json
import unittest

from audit_geo2027_global_only_matched_issue import ISSUE
from backtest_archived_country_vintages import SOURCES
from diagnose_geo2028_historical_forecast_vintage_drift import _fit_at_origin
from experiment_geo2027_intensity_markov_cross_release import (
    counts_to_binary, four_state_forecast,
)
from experiment_geo_h2_rolling_2014_2025 import (
    HORIZON, N, ORIGINS, TARGETS, YEARS_EARLY, YEARS_LATE,
    _baseline_scores, _build_fold, _compare_tracks, _proper_score,
    fold_specs, replay,
)
from test_experiment_geo2027_intensity_markov_cross_release import sample


class RollingHistoricalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ids=sorted(r["country_id"] for r in
                       json.loads(ISSUE.read_text(encoding="utf8"))["countries"])

    def test_12_unique_years_full_196_and_two_distinct_vintage_tracks(self):
        primary=fold_specs("fixed_first_vintage_then_latest")
        sensitivity=fold_specs("later_vintage_stress")
        self.assertEqual(ORIGINS,tuple(range(2012,2024)))
        self.assertEqual(TARGETS,tuple(range(2014,2026)))
        self.assertEqual([x["target_year"] for x in primary], list(TARGETS))
        self.assertEqual(len(primary),12)
        self.assertEqual(12*196,N)
        self.assertEqual([x["origin_release"] for x in primary].count("23.1"),11)
        self.assertEqual(primary[-1]["origin_release"],"24.1")
        self.assertEqual(primary[-1]["outcome_release"],"26.1")
        self.assertEqual(sensitivity[0]["origin_release"],"24.1")
        self.assertEqual(sensitivity[0]["outcome_release"],"26.1")
        self.assertEqual((YEARS_EARLY,YEARS_LATE),
                         (tuple(range(2014,2020)),tuple(range(2020,2026))))
        with self.assertRaises(ValueError):
            fold_specs("look_at_outcomes_then_choose_winner")

    def test_original_fixed_four_state_contract_and_explicit_old_origins(self):
        data=sample()
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            four_state_forecast(data,2012)
        early,meta=four_state_forecast(
            data,2012,historical_rolling_diagnostic=True)
        self.assertEqual(meta["cutoff_max"],2012)
        self.assertEqual(meta["eligible_countries"],196)
        self.assertEqual(set(early),set(data))
        at2022,_=four_state_forecast(data,2022)
        diagnostic,_=four_state_forecast(
            data,2022,historical_rolling_diagnostic=True)
        self.assertEqual(at2022,diagnostic)

    def test_rolling_historical_predictions_do_not_use_future_records(self):
        data=sample()
        original,_=four_state_forecast(
            data,2015,historical_rolling_diagnostic=True)
        binary,_=_fit_at_origin(counts_to_binary(data),2015,
                                fixed_cohort=list(data))
        touched=copy.deepcopy(data)
        for hist in touched.values():
            for year in range(2016,2026):
                hist[year] = 100_000 if year%2 else 0
        after,_=four_state_forecast(
            touched,2015,historical_rolling_diagnostic=True)
        second,_=_fit_at_origin(counts_to_binary(touched),2015,
                                fixed_cohort=list(data))
        self.assertEqual(original,after)
        self.assertEqual(binary,second)

    def test_binary_score_math_and_absence_fails(self):
        self.assertEqual(_proper_score(.2,0)[0],.04)
        self.assertAlmostEqual(_proper_score(.2,1)[0],.64)
        with self.assertRaises(ValueError):
            _proper_score(1.,0)
        with self.assertRaises(ValueError):
            _proper_score(float("nan"),1)
        for invalid in (True,-1,"0"):
            with self.assertRaises(ValueError):
                _proper_score(.6,invalid)
        rows=[{
            "country_id":1,"target_year":2024,
            "official_fatalities_estimates":(0,25,30),
            "p_global_markov":.3,"p_baseline_global_5y":.4,
        },{
            "country_id":2,"target_year":2024,
            "official_fatalities_estimates":(0,0,0),
            "p_global_markov":.7,"p_baseline_global_5y":.5,
        }]
        scored=_baseline_scores(rows)
        self.assertAlmostEqual(scored["low"]["global_markov_h2"]["brier"],
                               (.3**2+.7**2)/2)
        self.assertAlmostEqual(scored["best"]["global_markov_h2"]["brier"],
                               ((1-.3)**2+.7**2)/2)

    def test_vintage_overlap_not_an_extra_independent_sample(self):
        def r(y,c,p,q,state,best):
            return {"target_year":y,"country_id":c,
                    "p_original_binary":p,"p_intensity_markov":q,
                    "origin_active":state,
                    "official_fatalities_estimates":(0,best,best)}
        earlier=[r(y,c,.2,.3,0,0) for y in TARGETS for c in self.ids]
        later=copy.deepcopy(earlier)
        later[0]["p_original_binary"]=.25
        later[1]["origin_active"]=1
        later[2]["official_fatalities_estimates"]=(0,25,25)
        result=_compare_tracks(earlier,later)
        self.assertEqual(result["counts"],{
            "origin_binary_changed":1,
            "outcome_best_label_changed":1,
            "either_markov_probability_changed":1,
        })
        self.assertTrue(result["two_tracks_same_country_years_not_independent"])
        self.assertEqual(len(result["annual_changed_label_and_forecast_counts"]),12)
        with self.assertRaisesRegex(ValueError,"mismatched"):
            _compare_tracks(earlier,later[:-1])

    def test_refuses_bad_edition_cutoff_and_fake_four_sources(self):
        issue=json.loads(ISSUE.read_text(encoding="utf8"))
        with self.assertRaisesRegex(ValueError,"Four official archives"):
            replay({}, {}, issue, {}, {}, {})
        with self.assertRaises(ValueError):
            _build_fold({
                "origin_year":2012,"target_year":2014,
                "origin_release":"23.1","outcome_release":"23.1",
            }, {}, {}, self.ids)
        self.assertEqual(SOURCES["23.1"]["last_year"],2022)
        self.assertEqual(SOURCES["25.1"]["last_year"],2024)
        self.assertEqual(SOURCES["26.1"]["last_year"],2025)


if __name__=="__main__":
    unittest.main()
