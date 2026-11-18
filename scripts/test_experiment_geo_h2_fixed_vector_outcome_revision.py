#!/usr/bin/env python3
"""Synthetic tests for observed Brier source revision with identical forecasts."""
import copy
import math
import unittest
from experiment_geo_h2_fixed_vector_outcome_revision import fixed_score_change, FIELDS


def rows(changed=False, model_offset=0.0):
    output={}
    for cid in range(1,197):
        y=changed and cid==17
        p=0.2+model_offset
        output[cid]={
            "country_id":cid,
            "target_year":2017,
            "origin_active":0,
            "official_fatalities_estimates":(30,30,30) if y else (0,0,0),
            "p_original_binary":p,
            "p_intensity_markov":p+0.1,
            "p_global_markov":0.4,
            "p_baseline_global_5y":0.5,
        }
    return output


class TestObservedBrierRevision(unittest.TestCase):
    def test_one_real_label_change_only(self):
        a,b=rows(),rows(changed=True)
        result=fixed_score_change(a,b,set(a))
        self.assertEqual(result["country_n"],196)
        self.assertEqual(result["label_revisions_n"],1)
        self.assertEqual(result["revised_countries"][0]["country_id"],17)
        self.assertAlmostEqual(result["observed_brier_shift_new_minus_old"]["p_original_binary"],(1-2*0.2)/196)
        self.assertAlmostEqual(result["observed_brier_shift_new_minus_old"]["p_intensity_markov"],(1-2*0.3)/196)
        self.assertAlmostEqual(result["observed_fourstate_minus_binary_delta_brier_shift"],-0.2/196)

    def test_zero_revisions_exact_zero(self):
        a=rows()
        result=fixed_score_change(a,copy.deepcopy(a),set(a))
        self.assertEqual(result["label_revisions_n"],0)
        self.assertTrue(all(v==0 for v in result["observed_brier_shift_new_minus_old"].values()))

    def test_changed_forecast_rejected(self):
        a,b=rows(),rows(changed=True,model_offset=0.01)
        with self.assertRaises(ValueError):
            fixed_score_change(a,b,set(a))

    def test_missing_country_rejected(self):
        a,b=rows(),rows(changed=True)
        del b[17]
        with self.assertRaises(ValueError):
            fixed_score_change(a,b,set(a))

    def test_mismatched_origin_rejected(self):
        a,b=rows(),rows(changed=True)
        b[17]["origin_active"]=1
        with self.assertRaises(ValueError):
            fixed_score_change(a,b,set(a))

    def test_mismatched_year_rejected(self):
        a,b=rows(),rows(changed=True)
        b[17]["target_year"]=2018
        with self.assertRaises(ValueError):
            fixed_score_change(a,b,set(a))

    def test_invalid_probability_rejected(self):
        a,b=rows(),rows(changed=True)
        b[17]["p_original_binary"]=float("nan")
        with self.assertRaises(ValueError):
            fixed_score_change(a,b,set(a))


if __name__=="__main__":
    unittest.main()
