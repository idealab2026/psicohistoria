"""Pure tests of exactly matched original Markov and two counterfactual offsets."""
from __future__ import annotations

import copy
import json
import unittest

from audit_geo2027_log1p_shadow_issue import (
    ISSUE, MANIFEST, ORIGINAL, audit as audit_issue,
)
from experiment_geo2027_intensity_markov_cross_release import counts_to_binary
from experiment_geo2027_log1p_nested_h2 import binary_h2_until
from experiment_geo2027_log1p_markov_country_history_ablation import (
    _count_transitions, markov_counterfactual_offsets, _nstep_two,
    VARIANTS, GEO_OWN_PRIOR_WEIGHT, GEO_PRIOR_LAPLACE, study,
)
from test_experiment_geo2027_intensity_markov_cross_release import sample


class MarkovCountryHistoryAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=sample()
        cls.binary=counts_to_binary(cls.source)
        cls.ids=sorted(cls.source)

    def test_original_H2_reproduces_on_multiple_years_and_countries(self):
        for origin in (2015,2017,2022,2023):
            reference=binary_h2_until(self.binary,origin)
            glob,own=_count_transitions(self.binary,origin)
            for cid in self.ids[::17]:
                state=self.binary[cid][origin]
                exact=markov_counterfactual_offsets(glob,own[cid],state)
                self.assertEqual(exact[VARIANTS[0]],reference[cid])
                self.assertTrue(all(0<exact[k]<1 for k in VARIANTS))
                self.assertGreaterEqual(exact["removed_global_transitions"],0)

    def test_global_country_exclusion_is_literal_transition_matrix_subtraction(self):
        glob=[[300,100],[70,230]]
        own=[[50,10],[5,40]]
        z=markov_counterfactual_offsets(glob,own,0)
        self.assertEqual(z["heldout_global_transition_matrix"],
                         [[250,90],[65,190]])
        g=[(z["heldout_global_transition_matrix"][i][1]+1)/
           (sum(z["heldout_global_transition_matrix"][i])+2)
           for i in (0,1)]
        self.assertEqual(z[VARIANTS[2]],round(_nstep_two(0,g),12))
        self.assertNotEqual(z[VARIANTS[0]],z[VARIANTS[1]])
        self.assertNotEqual(z[VARIANTS[1]],z[VARIANTS[2]])
        self.assertEqual(z["removed_global_transitions"],105)

    def test_markov_global_holdout_only_uses_other_countries_for_global_prior(self):
        origin=2023
        cid=self.ids[0]
        all_counts,own=_count_transitions(self.binary,origin)
        z=markov_counterfactual_offsets(all_counts,own[cid],
                                        self.binary[cid][origin])
        others=copy.deepcopy(self.binary)
        others.pop(cid)
        global_excl,_=_count_transitions(others,origin)
        self.assertEqual(z["heldout_global_transition_matrix"],global_excl)
        q=[(global_excl[s][1]+1)/(sum(global_excl[s])+2) for s in (0,1)]
        self.assertEqual(z[VARIANTS[2]],
                         round(_nstep_two(self.binary[cid][origin],q),12))

    def test_after_origin_changes_do_not_affect_global_or_country_markov(self):
        origin=2021
        changed=copy.deepcopy(self.binary)
        for cid,h in changed.items():
            for year in range(origin+1,2026):
                h[year]=(cid+year)%2
        a,loc_a=_count_transitions(self.binary,origin)
        b,loc_b=_count_transitions(changed,origin)
        self.assertEqual(a,b)
        self.assertEqual(loc_a,loc_b)

    def test_zero_own_transition_history_global_only_equals_local(self):
        g=[[500,25],[100,350]]
        z=markov_counterfactual_offsets(g,[[0,0],[0,0]],0)
        self.assertEqual(z[VARIANTS[0]],z[VARIANTS[1]])
        self.assertEqual(z[VARIANTS[1]],z[VARIANTS[2]])

    def test_fail_closed_invalid_gwno_and_tables(self):
        with self.assertRaises(ValueError):
            _count_transitions({1:{2019:8,2020:0}},2020)
        for args in [
            ([[2,1],[2,1]],[[0,0],[0,0]],0),
            ([[300,5],[400,2]],[[300,6],[0,0]],0),
            ([[300,5],[400,2]],[[0,0],[0,0]],3),
            ([[300,5],[400,2]],[[0.0,0],[0,0]],0),
        ]:
            with self.assertRaises(ValueError):
                markov_counterfactual_offsets(*args)

    def test_sha_frozen_196_shadow_and_same_model_parameters(self):
        self.assertEqual((GEO_PRIOR_LAPLACE,GEO_OWN_PRIOR_WEIGHT),(1,20))
        result=audit_issue(ISSUE.read_bytes(),MANIFEST.read_bytes(),
                           ORIGINAL.read_bytes())
        self.assertEqual(result["country_n"],196)
        self.assertEqual(result["future_2027_outcomes_resolved"],0)
        with self.assertRaisesRegex(ValueError,"provenance"):
            study({}, {}, {"schema":"tampered"})


if __name__=="__main__":
    unittest.main()
