"""Exact 3-factor vintage attribution, no leakage, rank tie and SHA guards."""
from __future__ import annotations

import copy
import unittest

from test_experiment_geo2027_intensity_markov_cross_release import sample
from diagnose_geo2027_log1p_historical_vintage_robustness import (
    FACTORS, PAIRS, clipped_original_counts, quantile, shapley_three,
    snapshot, statistics, study, topk_shadow_comparison,
)


class Log1pVintageSensitivityTests(unittest.TestCase):
    def test_shapley_exact_three_factor_additivity(self):
        r=shapley_three(.23,.31,23,118,
                        (.2,.7,1.2),(-.4,1.1,1.8))
        self.assertAlmostEqual(
            sum(r[factor+"_pp"] for factor in FACTORS),
            r["delta_probability_pp"], places=7)
        self.assertTrue(r["algebraic_not_causal"])

    def test_shapley_when_only_one_factor_changes(self):
        p=.43
        deaths=30
        beta=(.1,.5,1.2)
        no=shapley_three(p,p,deaths,deaths,beta,beta)
        self.assertAlmostEqual(no["delta_probability_pp"],0)
        for factor,newvalue in ((0,.55),(1,190),(2,(-.2,1.2,.1))):
            newer=[p,deaths,beta]
            newer[factor]=newvalue
            r=shapley_three(p,newer[0],deaths,newer[1],beta,newer[2])
            for i,name in enumerate(FACTORS):
                if i!=factor:
                    self.assertAlmostEqual(r[name+"_pp"],0,places=8)
            self.assertAlmostEqual(r[FACTORS[factor]+"_pp"],
                                   r["delta_probability_pp"],places=8)

    def test_negative_death_and_out_of_range_original_rejected(self):
        with self.assertRaisesRegex(ValueError,"Malformed"):
            shapley_three(.2,.2,-1,1,(0,0,0),(0,0,0))
        with self.assertRaisesRegex(ValueError,"Malformed"):
            shapley_three(0,.2,1,1,(0,0,0),(0,0,0))

    def test_later_vintage_years_cannot_leak_into_earlier_origin(self):
        original=sample()
        clipped=clipped_original_counts(original,2022)
        modified=copy.deepcopy(original)
        for cid,h in modified.items():
            h[2023]=cid%2*700
            h[2024]=cid%3*500
            h[2025]=cid%4*300
            h[2026]=10000
            h[2027]=100000
        self.assertEqual(clipped,clipped_original_counts(modified,2022))
        names={cid:"Country"+str(cid) for cid in original}
        first,meta=snapshot(original,2022,names)
        later,metadata=snapshot(modified,2022,names)
        self.assertEqual(first,later)
        self.assertEqual(meta,metadata)
        self.assertEqual(meta["training_cutoff"],2022)
        self.assertEqual(meta["post_origin_training_observations"],0)
        self.assertEqual(meta["inner_target_years"],[2012,2022])

    def test_changed_pre_origin_labels_can_change_shadow(self):
        base=sample()
        modified=copy.deepcopy(base)
        for cid,h in modified.items():
            if cid%5==0 and h[2017]>=25:
                h[2017]=24
            if cid%11==0:
                h[2022]=26 if h[2022]<25 else 16
        names={cid:"Country"+str(cid) for cid in base}
        old,_=snapshot(base,2022,names)
        later,_=snapshot(modified,2022,names)
        self.assertTrue(any(
            old[cid]["p_log1p_h2"]!=later[cid]["p_log1p_h2"]
            for cid in old))

    def test_topk_tie_and_risk_set_guard(self):
        rows=[]
        for cid in range(1,197):
            state=int(cid>155)
            base=(.01+.0003*cid if state==0 else .7+.001*cid)
            rows.append({
                "country_id":cid,"old_origin_state":state,
                "revised_origin_state":state,
                "old_shadow_p":base,
                "revised_shadow_p":base,
            })
        names={r["country_id"]:"GW"+str(r["country_id"]) for r in rows}
        a=topk_shadow_comparison(rows,0,10,names)
        self.assertEqual(a["deterministic_swaps_n"],0)
        self.assertTrue(a["old_boundary_unique"])
        # Deliberate boundary tie, should retain uncertainty instead of
        # claiming any tie-independent entry.
        rows[144]["old_shadow_p"]=rows[145]["old_shadow_p"]
        tie=topk_shadow_comparison(rows,0,10,names)
        self.assertFalse(tie["old_boundary_unique"])
        self.assertEqual(tie["definite_entries_not_dependent_on_ties"],[])
        rows[0]["revised_origin_state"]=1
        with self.assertRaisesRegex(ValueError,"state changed"):
            topk_shadow_comparison(rows,0,10,names)

    def test_provenance_guard_requires_unresolved_2027(self):
        with self.assertRaisesRegex(ValueError,"provenance"):
            study({},{},{"schema":"changed"})
        self.assertEqual(len(PAIRS),5)

    def test_quantile_and_196_country_statistics_guards(self):
        self.assertEqual(quantile([1,4,9,16],.95),16)
        with self.assertRaisesRegex(ValueError,"cohort"):
            statistics([])


if __name__=="__main__":
    unittest.main()
