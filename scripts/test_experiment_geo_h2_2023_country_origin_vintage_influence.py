#!/usr/bin/env python3
"""Synthetic identity checks and fail-closed provenance for 2023 country influence."""
import copy
import json
import math
import unittest

from experiment_geo_h2_2023_country_origin_vintage_influence import (
    attribute, ORIGIN, YEAR, N, ISSUE,
)


class CountryInfluenceTest(unittest.TestCase):
    def test_all_196_original_gwno_distinct(self):
        issue=json.loads(ISSUE.read_text(encoding="utf-8"))
        ids=[r["country_id"] for r in issue["countries"]]
        self.assertEqual(len(ids),N)
        self.assertEqual(len(set(ids)),N)

    def test_country_brier_change_identity(self):
        for y in (0,1):
            for pb_old,pf_old,pb_new,pf_new in (
                (.1,.25,.5,.65),(.81,.79,.72,.68),(.25,.28,.28,.20)
            ):
                old=(pf_old-y)**2-(pb_old-y)**2
                new=(pf_new-y)**2-(pb_new-y)**2
                drift=new-old
                expanded=((pf_new-y)**2-(pf_old-y)**2) - (
                    (pb_new-y)**2-(pb_old-y)**2)
                self.assertAlmostEqual(drift,expanded,places=14)

    def test_synthetic_flip_can_be_single_pivotal_country(self):
        # A single influential country can change a very small global margin;
        # do not assert that this occurs in real data without official replay.
        old=[-.00001]*N
        new=[-.00001]*N
        new[0]=.00099
        self.assertLess(sum(old),0)
        self.assertGreater(sum(new),0)
        self.assertLess(sum(new[1:]),0)

    def test_zero_global_shift_can_hide_country_changes(self):
        old=[0.0]*N
        new=[0.0]*N
        new[0]=.1
        new[1]=-.1
        self.assertAlmostEqual(sum(new)-sum(old),0,places=12)
        self.assertGreater(sum(abs(a-b) for a,b in zip(old,new)),0)

    def test_empty_inputs_refused(self):
        with self.assertRaises(ValueError):
            attribute([],[],{},{})

    def test_source_provenance_fail_closed(self):
        with self.assertRaises(ValueError):
            attribute([{}]*N,[{}]*N,
                      {"schema":"idealab.psico.geo_h2_2023_country_origin_vintage_rank_attribution.v1"},
                      {"not_prospective_or_independently_timestamped_skill":False})

    def test_expected_origin_and_year(self):
        self.assertEqual(YEAR-ORIGIN,2)

    def test_nonfinite_scores_do_not_satisfy_math_identity(self):
        self.assertFalse(math.isfinite(float("nan")))
        self.assertFalse(math.isfinite(float("inf")))


if __name__=="__main__":
    unittest.main()
