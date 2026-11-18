#!/usr/bin/env python3
"""Empirical editorial rate sensitivity: strict source and held-out controls."""
import unittest

from experiment_geo_h2_empirical_revision_rate_shadow import (
    N, TRAIN_N, CUTOFF, ALPHA, TRAIN_PAIRS, HOLDOUT_PAIR,
    revision_event, state_revision_counts, jeffreys_rates, score_holdout,
    conditional_h2, evaluate,
)


class EditorialRateTest(unittest.TestCase):
    def test_protocol_and_split_frozen(self):
        self.assertEqual((N, TRAIN_N, CUTOFF, ALPHA),(196,199,2021,.5))
        self.assertEqual(TRAIN_PAIRS,(("23.1","24.1"),("24.1","25.1")))
        self.assertEqual(HOLDOUT_PAIR,("25.1","26.1"))

    def test_zero_low_is_asymmetric_and_not_all_revisions(self):
        self.assertEqual(revision_event(0,24),(0,1))
        self.assertEqual(revision_event(24,0),(1,0))
        self.assertEqual(revision_event(0,25),(0,2))
        self.assertEqual(revision_event(90,113),(2,3))

    def test_bad_fatalities_rejected(self):
        for a,b in ((-1,0),(0,-1),(0,1.0),("0",0)):
            with self.assertRaises(ValueError):
                revision_event(a,b)

    def test_jeffreys_beta_nonzero_when_crossing_unseen(self):
        d={0:{"n":100,"cross_to_adjacent":0},
           1:{"n":200,"cross_to_adjacent":2}}
        p=jeffreys_rates(d)
        self.assertAlmostEqual(p[0],.5/101)
        self.assertAlmostEqual(p[1],2.5/201)

    def test_unrealistic_denominator_rejected(self):
        d={0:{"n":5,"cross_to_adjacent":1},
           1:{"n":200,"cross_to_adjacent":1}}
        with self.assertRaises(ValueError):
            jeffreys_rates(d)

    def test_cutoff_and_crossing_direction(self):
        old={cid:{2020:0,2021:0,2022:0} for cid in range(1,200)}
        new={cid:dict(h) for cid,h in old.items()}
        new[1][2020]=1
        new[2][2022]=12
        d,events=state_revision_counts(old,new,2021)
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]["GWNO"],1)
        self.assertEqual(events[0]["year"],2020)
        self.assertEqual(d[0]["n"],199*2)

    def test_missing_year_rejected_not_imputed_zero(self):
        old={cid:{2020:0,2021:0} for cid in range(1,200)}
        new={cid:dict(h) for cid,h in old.items()}
        del new[1][2020]
        with self.assertRaises(ValueError):
            state_revision_counts(old,new,2021)

    def test_holdout_event_brier_defined(self):
        counts={0:{"n":200,"cross_to_adjacent":1},
                1:{"n":100,"cross_to_adjacent":0}}
        result=score_holdout({0:.01,1:.02},counts)
        self.assertTrue(result["0"]["mean_holdout_revision_event_brier"]>0)
        self.assertEqual(result["1"]["revised_n"],0)

    def test_invalid_cohort_fail_closed(self):
        with self.assertRaises(ValueError):
            conditional_h2({},2025,[])

    def test_missing_previous_issue_not_accepted(self):
        with self.assertRaises(ValueError):
            evaluate({},[],{})


if __name__=="__main__":
    unittest.main()
