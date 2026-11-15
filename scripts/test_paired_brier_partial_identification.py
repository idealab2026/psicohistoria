"""Finite-cohort sharp Brier identification, no country-IID or confidence claim."""
import itertools
import math
import unittest

from paired_brier_partial_identification import sharp_partial_paired_brier


def rows(n=3):
    p=(.2,.8,.35)
    q=(.6,.3,.45)
    return [{"country_id":i+1,"p_model":p[i],"p_baseline_global_5y":q[i]}
            for i in range(n)]


def observed_delta(original,complete):
    return sum(
        (r["p_model"]-complete[r["country_id"]])**2-
        (r["p_baseline_global_5y"]-complete[r["country_id"]])**2
        for r in original)/len(original)


class ExactFiniteCohortTests(unittest.TestCase):
    def test_all_binary_completion_extrema_are_exact_for_any_missing_subset(self):
        original=rows()
        for present in itertools.product((False,True),repeat=3):
            fixed={r["country_id"]:int(i%2==0)
                   for i,r in enumerate(original) if present[i]}
            missing=[r["country_id"] for r in original
                     if r["country_id"] not in fixed]
            candidates=[]
            for possibilities in itertools.product((0,1),repeat=len(missing)):
                complete={**fixed,**dict(zip(missing,possibilities))}
                candidates.append(observed_delta(original,complete))
            result=sharp_partial_paired_brier(
                original,fixed,"p_model","p_baseline_global_5y",
                cohort_size=len(original))
            self.assertAlmostEqual(result["lower_full_cohort_delta_brier"],
                                   min(candidates),places=14)
            self.assertAlmostEqual(result["upper_full_cohort_delta_brier"],
                                   max(candidates),places=14)
            self.assertEqual(result["unresolved_country_outcomes"],len(missing))
            self.assertEqual(result["resolved_country_outcomes"],len(fixed))
            self.assertEqual(
                result["observed_full_cohort_delta_brier_if_complete"] is None,
                bool(missing))
            self.assertFalse(result["iid_country_assumption"])
            self.assertFalse(result["bootstrap_resampling_used"])
            self.assertIsNone(result["confidence_level"])
            self.assertIsNone(result["p_value"])
            self.assertFalse(result["prospective_skill_established"])
            self.assertTrue(result["sharp_for_each_missing_country_label_free_0_or_1"])

    def test_risk_set_denominator_stays_three_when_one_country_unresolved(self):
        original=rows()
        known={1:0,2:1}
        x=sharp_partial_paired_brier(
            original,known,"p_model","p_baseline_global_5y",cohort_size=3)
        self.assertEqual(x["fixed_issued_cohort_n"],3)
        self.assertEqual(x["unresolved_country_ids"],[3])
        self.assertIsNone(x["observed_full_cohort_delta_brier_if_complete"])
        # The source could have a different future country not among first-issued ones.
        extra=sharp_partial_paired_brier(
            original,{**known,777:1},"p_model","p_baseline_global_5y",
            cohort_size=3)
        self.assertEqual(x,extra)

    def test_when_all_labels_observed_region_collapses_to_paired_brier(self):
        d={1:0,2:1,3:0}
        x=sharp_partial_paired_brier(
            rows(),d,"p_model","p_baseline_global_5y",cohort_size=3)
        expected=observed_delta(rows(),d)
        self.assertAlmostEqual(x["lower_full_cohort_delta_brier"],expected,places=14)
        self.assertAlmostEqual(x["upper_full_cohort_delta_brier"],expected,places=14)
        self.assertAlmostEqual(x["observed_full_cohort_delta_brier_if_complete"],
                               expected,places=14)

    def test_invalid_binary_labels_and_unissued_probabilities_fail_closed(self):
        for bad in (None,True,-1,2,float("nan"),.5):
            with self.subTest(outcome=bad):
                with self.assertRaises(ValueError):
                    sharp_partial_paired_brier(
                        rows(),{1:bad},"p_model","p_baseline_global_5y",
                        cohort_size=3)
        for bad in (None,False,0,1,float("nan"),float("inf")):
            r=rows()
            r[0]["p_model"]=bad
            with self.subTest(probability=bad):
                with self.assertRaises(ValueError):
                    sharp_partial_paired_brier(
                        r,{},"p_model","p_baseline_global_5y",cohort_size=3)
        duplicate=rows()
        duplicate[1]["country_id"]=1
        with self.assertRaisesRegex(ValueError,"repeated"):
            sharp_partial_paired_brier(
                duplicate,{},"p_model","p_baseline_global_5y",
                cohort_size=3)
        with self.assertRaisesRegex(ValueError,"fixed issued"):
            sharp_partial_paired_brier(
                rows(),{},"p_model","p_baseline_global_5y",cohort_size=196)
        with self.assertRaisesRegex(ValueError,"fixed issued"):
            sharp_partial_paired_brier(
                rows(),{},"p_model","p_model",cohort_size=3)

    def test_newconf_string_gwno_works_exactly_the_same_without_episodes(self):
        original=[{**r,"country_id":str(r["country_id"])} for r in rows()]
        outcomes={"1":1,"3":0}
        x=sharp_partial_paired_brier(
            original,outcomes,"p_model","p_baseline_global_5y",cohort_size=3)
        self.assertEqual(x["resolved_country_outcomes"],2)
        self.assertEqual(x["unresolved_country_ids"],["2"])
        y={str(k):v for k,v in {1:1,3:0}.items()}
        values=[observed_delta(original,{**y,"2":missing}) for missing in (0,1)]
        self.assertAlmostEqual(x["lower_full_cohort_delta_brier"],min(values))
        self.assertAlmostEqual(x["upper_full_cohort_delta_brier"],max(values))


if __name__=="__main__":
    unittest.main()
