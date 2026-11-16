"""No-leak and matched-source tests for global-only Markov H2 LOG1P transfer."""
from __future__ import annotations

import copy
import json
import unittest

from audit_geo2027_log1p_shadow_issue import (
    ISSUE, MANIFEST, ORIGINAL, audit as audit_issue,
)
from experiment_geo2027_intensity_markov_cross_release import counts_to_binary
from experiment_geo2027_log1p_rolling_year_vintage import historical_ledger
from experiment_geo2027_log1p_country_block_transfer import calibration_training
from experiment_geo2027_log1p_markov_country_history_ablation import (
    _count_transitions, markov_counterfactual_offsets, VARIANTS,
)
from experiment_geo2027_log1p_matched_global_only import (
    make_snapshots, matched_training_rows, matched_fit,
    markov_global_only_offset, scoring_pair, _summary, study,
)
from test_experiment_geo2027_intensity_markov_cross_release import sample


class MatchedGlobalOnlyTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=sample()
        cls.ids=sorted(cls.source)
        cls.ledger=historical_ledger(cls.source,2025,cls.ids)
        cls.binary=counts_to_binary(cls.source)

    def test_evaluation_offset_is_exact_previous_global_only_ablation(self):
        for origin in (2015,2017,2021,2023):
            global_counts,loc=_count_transitions(self.binary,origin)
            for cid in self.ids[::13]:
                state=self.binary[cid][origin]
                matched=markov_global_only_offset(
                    global_counts,loc,state,cid)
                previous=markov_counterfactual_offsets(
                    global_counts,loc[cid],state)[VARIANTS[2]]
                self.assertEqual(matched,previous)

    def test_training_row_excludes_both_heldout_target_and_training_country(self):
        origin=2015
        cid=self.ids[0]
        other=self.ids[1]
        source=copy.deepcopy(self.binary)
        global_counts,locals_by_country=_count_transitions(source,origin)
        training=markov_global_only_offset(
            global_counts,locals_by_country,0,cid,other)
        without=copy.deepcopy(source)
        without.pop(cid)
        without.pop(other)
        global_direct,_=_count_transitions(without,origin)
        empty={777:[[0,0],[0,0]]}
        direct=markov_global_only_offset(global_direct,empty,0,777)
        self.assertEqual(training,direct)

    def test_pre_origin_target_transition_mutation_does_not_change_matched_training_offsets(self):
        origin=2017
        target=2019
        withheld=self.ids[0]
        training=calibration_training(self.ledger,target)
        snaps=make_snapshots(self.binary,training,origin)
        transformed=matched_training_rows(training,snaps,withheld,target)
        altered=copy.deepcopy(self.binary)
        for year in range(1989,origin+1):
            if year in altered[withheld]:
                altered[withheld][year]=1-altered[withheld][year]
        another=make_snapshots(altered,training,origin)
        modified=matched_training_rows(training,another,withheld,target)
        self.assertEqual(transformed,modified)

    def test_no_future_training_labels_or_future_Markov_transitions(self):
        target=2025
        withheld=self.ids[0]
        original=calibration_training(self.ledger,target)
        snapshots=make_snapshots(self.binary,original,target-2)
        a=matched_training_rows(original,snapshots,withheld,target)
        mutated=copy.deepcopy(self.source)
        for cid,h in mutated.items():
            h[2024]=1000 if cid%2 else 0
            h[2025]=1000 if cid%3 else 0
        future=historical_ledger(mutated,2025,self.ids)
        future_train=calibration_training(future,target)
        future_snapshots=make_snapshots(counts_to_binary(mutated),future_train,
                                        target-2)
        b=matched_training_rows(future_train,future_snapshots,withheld,target)
        self.assertEqual(a,b)
        self.assertTrue(all(r["country_id"]!=withheld for r in a))
        self.assertEqual(max(r["target_year"] for r in a),2023)
        self.assertEqual(max(r["origin_year"] for r in a),2021)

    def test_matched_logistic_refits_and_does_not_use_country_historical_labels(self):
        target=2017
        training=calibration_training(self.ledger,target)
        snapshots=make_snapshots(self.binary,training,target-2)
        withheld=self.ids[0]
        beta,meta=matched_fit(training,snapshots,withheld,target)
        self.assertEqual(len(beta),3)
        self.assertTrue(meta["target_country_training_labels_used"] is False)
        self.assertTrue(meta["target_country_training_transition_counts_used"] is False)
        self.assertEqual(meta["last_training_label_year"],2015)
        self.assertEqual(meta["last_training_feature_year"],2013)
        self.assertEqual(meta["fit_n"],len(training)-4)
        self.assertNotEqual(beta,(0.,0.,0.))

    def test_country_score_identity_and_summation(self):
        a=scoring_pair(.1,9,(0.,1.,.3),0)
        b=scoring_pair(.2,23,(0.,1.,.3),1)
        self.assertAlmostEqual(
            a["delta_alpha1_minus_alpha0"],
            a["alpha1_loss"]-a["alpha0_loss"])
        self.assertAlmostEqual(
            b["delta_alpha1_minus_alpha0"],
            b["alpha1_loss"]-b["alpha0_loss"])
        rows=[{"s":a},{"s":b}]
        z=_summary(rows,"s",196)
        self.assertEqual(z["n_affected"],2)
        self.assertAlmostEqual(z[
            "delta_alpha1_minus_alpha0_on_full_reference_risk_n"],
            (a["delta_alpha1_minus_alpha0"]+
             b["delta_alpha1_minus_alpha0"])/196,places=10)

    def test_bogus_country_and_short_global_fail_closed(self):
        global_counts,locals_by_country=_count_transitions(self.binary,2017)
        for args in [
            (global_counts,locals_by_country,0,999999,None),
            (global_counts,locals_by_country,0,self.ids[0],self.ids[0]),
            (global_counts,locals_by_country,3,self.ids[0],None),
        ]:
            with self.assertRaises(ValueError):
                markov_global_only_offset(*args)
        with self.assertRaises(ValueError):
            matched_training_rows([],{},self.ids[0],2025)
        with self.assertRaisesRegex(ValueError,"provenance"):
            study({}, {}, {"schema":"invalid"})

    def test_frozen_2027_issue_has_196_and_zero_observed_outcomes(self):
        result=audit_issue(ISSUE.read_bytes(),MANIFEST.read_bytes(),
                           ORIGINAL.read_bytes())
        self.assertEqual(result["country_n"],196)
        self.assertEqual(result["future_2027_outcomes_resolved"],0)


if __name__=="__main__":
    unittest.main()
