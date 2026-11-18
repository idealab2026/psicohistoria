#!/usr/bin/env python3
"""Four-state source observation model and latent identifiability controls."""
import math
import unittest

from experiment_geo_h2_fourstate_observation_identifiability import (
    STATE_COUNT, TRAIN_CUTOFF, TRAIN_PAIRS, HOLDOUT_PAIR,
    DIRICHLET, MAX_ADJACENT_LATENT_MASS, N_COUNTRIES,
    pair_confusion, aggregate_matrices, posterior_kernel,
    evaluate_holdout, latent_bounds, vintage_sequence_diagnostics, analyze,
)


class ObservationKernelTest(unittest.TestCase):
    def test_frozen_holdout_and_identifiability_assumption(self):
        self.assertEqual(TRAIN_PAIRS,(("23.1","24.1"),("24.1","25.1")))
        self.assertEqual(HOLDOUT_PAIR,("25.1","26.1"))
        self.assertEqual((TRAIN_CUTOFF,STATE_COUNT,N_COUNTRIES),(2021,4,196))
        self.assertEqual((DIRICHLET,MAX_ADJACENT_LATENT_MASS),(.5,.1))

    def test_dirichlet_four_by_four_stochastic_kernel(self):
        c=[[100,2,0,0],[0,30,1,0],[0,0,20,1],[0,0,0,40]]
        q=posterior_kernel(c)
        self.assertEqual(len(q),4)
        for row in q:
            self.assertAlmostEqual(sum(row),1,places=14)
            self.assertTrue(all(0<x<1 for x in row))
        self.assertAlmostEqual(q[0][1],2.5/104,places=14)

    def test_never_replace_absent_history_with_zero(self):
        old={cid:{2020:0,2021:0} for cid in range(1,200)}
        new={cid:dict(h) for cid,h in old.items()}
        del new[1][2020]
        with self.assertRaises(ValueError):
            pair_confusion(old,new)

    def test_cutoff_excludes_future_edit(self):
        old={cid:{2020:0,2021:0,2022:0} for cid in range(1,200)}
        new={cid:dict(h) for cid,h in old.items()}
        new[1][2021]=2
        new[2][2022]=100
        matrix,changed=pair_confusion(old,new,cutoff=2021)
        self.assertEqual(len(changed),1)
        self.assertEqual((changed[0]["GWNO"],changed[0]["year"]),(1,2021))
        self.assertEqual(matrix[0][1],1)
        self.assertEqual(sum(map(sum,matrix)),199*2)

    def test_sum_source_matrices(self):
        a=[[0]*4 for _ in range(4)]
        b=[[0]*4 for _ in range(4)]
        a[0][0]=10
        b[0][1]=2
        self.assertEqual(aggregate_matrices([a,b])[0],[10,2,0,0])

    def test_heldout_multiclass_proper_brier_identity(self):
        c=[[100,0,0,0],[0,20,0,0],[0,0,30,0],[0,0,0,25]]
        q=[[.997,.001,.001,.001],
           [.001,.997,.001,.001],
           [.001,.001,.997,.001],
           [.001,.001,.001,.997]]
        d=evaluate_holdout(c,q)
        self.assertEqual(d["heldout_category_changes"],0)
        self.assertAlmostEqual(d["mean_multiclass_brier_next_recording"],
                               (.003**2+3*.001**2),places=13)

    def test_no_assumption_4_state_convex_hull(self):
        p=[.03,.25,.55,.9]
        unbounded,conditional=latent_bounds(p,0)
        self.assertEqual(unbounded,[.03,.9])
        self.assertAlmostEqual(conditional[0],.03)
        self.assertAlmostEqual(conditional[1],.052)

    def test_assumption_for_2_3_makes_state_exact_only_under_that_assumption(self):
        p=[.03,.25,.55,.9]
        unbounded,conditional=latent_bounds(p,3)
        self.assertEqual(unbounded,[.03,.9])
        self.assertEqual(conditional,[.9,.9])

    def test_negative_or_out_of_range_latent_scenarios_refused(self):
        for p,state in (([-.1,.1,.2,.3],0),([0,.1,.2,.3],9),
                        ([.1,.2,.3,float("nan")],1),([.1,.2],0)):
            with self.assertRaises(ValueError):
                latent_bounds(p,state)

    def test_three_version_reversal_not_truth(self):
        # Build four comparable tiny synthetic panels and a reversal:
        # old(0) -> second(1) -> third(0) -> fourth(0).
        data={v:{cid:{2020:0,2021:0} for cid in range(1,200)}
              for v in ("23.1","24.1","25.1","26.1")}
        data["24.1"][1][2020]=3
        result=vintage_sequence_diagnostics(data)
        self.assertEqual(result["middle_different_then_returned_to_first_n"],1)
        self.assertEqual(result["first_and_last_disagree_n"],0)
        self.assertEqual(result["ever_changed_four_state_n"],1)
        self.assertEqual(result["stable_across_all_four_n"],397)

    def test_unverified_releases_fail_closed(self):
        with self.assertRaises(ValueError):
            analyze({},[],{},{})


if __name__=="__main__":
    unittest.main()
