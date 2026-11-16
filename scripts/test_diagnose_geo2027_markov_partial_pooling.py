"""Synthetic and immutable-issue tests for Markov partial pooling source stability."""
from __future__ import annotations

import copy
import math
import unittest

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit as audit_issued,
)
from experiment_geo2027_intensity_markov_cross_release import counts_to_binary
from experiment_geo2027_log1p_nested_h2 import binary_h2_until
from diagnose_geo2027_markov_partial_pooling import (
    ORIGINS, WEIGHTS, _by_group, build_counts, raw_markov,
    replay_snapshot, summary, vintage_pair, study,
)
from test_experiment_geo2027_intensity_markov_cross_release import sample


class PartialPoolingVintageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=sample()
        cls.ids=sorted(cls.source)
        cls.binary=counts_to_binary(cls.source)

    def test_issued_forecasts_sha_frozen_and_future_2027_not_scored(self):
        result=audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),
                            ORIGINAL.read_bytes(),OLD_SHADOW.read_bytes(),
                            OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
        self.assertEqual(result["country_n"],196)
        self.assertEqual(result["official_2027_outcomes_resolved"],0)
        self.assertEqual(WEIGHTS,(0.,.25,.5,1.))

    def test_exact_original_markov_2022_and_2023_formula(self):
        for origin in (2022,2023):
            g,local=build_counts(self.binary,origin)
            original=binary_h2_until(self.binary,origin)
            for cid in self.ids[::11]:
                state=self.binary[cid][origin]
                p=raw_markov(g,local[cid],state,1.,False)
                self.assertEqual(p,original[cid])
                global_only=raw_markov(g,local[cid],state,0.,True)
                self.assertTrue(0<global_only<1)

    def test_zero_weight_equals_exact_leave_country_out_global_prior(self):
        g=[[800,120],[150,250]]
        own=[[20,5],[3,9]]
        without=[[780,115],[147,241]]
        q=[(row[1]+1)/(sum(row)+2) for row in without]
        for state in (0,1):
            p=round((1-q[state])*q[0]+q[state]*q[1],12)
            self.assertEqual(raw_markov(g,own,state,0.,True),p)

    def test_state_specific_own_effective_weight_respects_prior_20(self):
        cases,_=replay_snapshot(self.source,2025,self.ids)
        self.assertEqual(len(cases),196)
        for case in cases.values():
            n=case["local_transition_exposures_state0"]
            self.assertAlmostEqual(case["national_fraction_state0"],
                                   n/(n+20))
            self.assertEqual(
                case["country_origin_state"],
                int(case["country_deaths_at_origin"]>=25))
            self.assertEqual(len(case["p_partial_pool_grid"]),4)
            for w in WEIGHTS:
                self.assertTrue(0<case["p_partial_pool_grid"][str(w)]<1)

    def test_no_post_origin_source_data_leak_even_if_new_years_in_source(self):
        for origin in ORIGINS:
            original,_=replay_snapshot(self.source,origin,self.ids)
            extra=copy.deepcopy(self.source)
            for cid,h in extra.items():
                for y in range(origin+1,2028):
                    h[y]=100000 if (cid+y)%3 else 0
            later,_=replay_snapshot(extra,origin,self.ids)
            self.assertEqual(original,later)

    def test_future_edit_to_2023_does_not_revise_2022_origin(self):
        origin=2022
        old,_=replay_snapshot(self.source,origin,self.ids)
        source=copy.deepcopy(self.source)
        for cid,h in source.items():
            h[2023]=100000 if cid%2 else 0
        new,_=replay_snapshot(source,origin,self.ids)
        self.assertEqual(old,new)

    def test_vintage_revision_0_to_10_best_deaths_does_not_change_binary_markov(self):
        original,_=replay_snapshot(self.source,2022,self.ids)
        altered=copy.deepcopy(self.source)
        cid=next(cid for cid,h in altered.items() if h[2022]==0)
        altered[cid][2022]=10
        revised,_=replay_snapshot(altered,2022,self.ids)
        pair=vintage_pair(original,revised,"23.1","24.1",2022)
        self.assertEqual(pair["countries_with_revised_origin_best_deaths"],1)
        self.assertEqual(pair["countries_with_revised_origin_binary_state"],0)
        for w in WEIGHTS:
            v=pair["risk_revision_by_prespecified_local_history_weight"][str(w)]
            self.assertEqual(v["absolute_risk_revision_pp"]["max"],0.)

    def test_vintage_revision_crossing_25_must_change_binary_origin_state(self):
        original,_=replay_snapshot(self.source,2022,self.ids)
        altered=copy.deepcopy(self.source)
        cid=next(cid for cid,h in altered.items() if h[2022]==0)
        altered[cid][2022]=25
        revised,_=replay_snapshot(altered,2022,self.ids)
        pair=vintage_pair(original,revised,"23.1","24.1",2022)
        self.assertEqual(pair["countries_with_revised_origin_best_deaths"],1)
        self.assertEqual(pair["countries_with_revised_origin_binary_state"],1)
        self.assertGreater(
            pair["risk_revision_by_prespecified_local_history_weight"]["0.0"][
                "absolute_risk_revision_pp"]["max"],0)

    def test_percentile_and_fail_closed_tables(self):
        m=summary([0.,2.,4.,6.])
        self.assertEqual(m["n"],4)
        self.assertAlmostEqual(m["median"],3.)
        self.assertAlmostEqual(m["mean"],3.)
        for values in ([],[float("nan")],[float("inf")]):
            with self.assertRaises(ValueError):
                summary(values)
        with self.assertRaises(ValueError):
            raw_markov([[500,10],[50,350]],[[0,0],[0,0]],0,-.5)
        with self.assertRaises(ValueError):
            raw_markov([[500,10],[50,350]],[[501,0],[0,0]],0,1)
        with self.assertRaisesRegex(ValueError,"source"):
            study({}, {}, {}, {})


if __name__=="__main__":
    unittest.main()
