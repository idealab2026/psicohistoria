"""Synthetic calibration tests only; NO real or future 2027 outcomes."""
import copy
import math
import unittest

from backtest_archived_country_vintages import SOURCES
from diagnose_geo2027_historical_count_dispersion import (
    REVISED_TARGET_YEARS,SEPARATED_TARGET_YEARS,
    diagnose as original_count_diagnostic,
)
from experiment_geo2027_temporal_calibration import (
    TRAIN_YEARS,REVISED_VALIDATION_YEARS,SEPARATE_VALIDATION_YEARS,
    evaluate,fit_intercept,logistic_shift,score,transition_pair,
)
from test_diagnose_geo2027_historical_count_dispersion import make_toy


def fake():
    revised=make_toy(REVISED_TARGET_YEARS)
    external=make_toy(SEPARATED_TARGET_YEARS)
    hashes={k:v["sha256"] for k,v in SOURCES.items()}
    previous=original_count_diagnostic(revised,external,hashes)
    return revised,external,hashes,previous


class TemporalInterceptCalibrationTests(unittest.TestCase):
    def test_train_only_intercept_matches_observed_count(self):
        observations=[(.20,1)]*5+[(.20,0)]*95
        alpha=fit_intercept(observations)
        self.assertLess(alpha,0)
        self.assertAlmostEqual(logistic_shift(.2,alpha),.05,places=10)
        self.assertAlmostEqual(math.exp(alpha),
                               (.05/.95)/(.2/.8),places=10)
        self.assertAlmostEqual(sum(logistic_shift(p,alpha) for p,_ in observations),5)
        self.assertAlmostEqual(logistic_shift(.01,0),.01)

    def test_invalid_probabilities_labels_and_single_class_rejected(self):
        for bad in ([(.1,0)]*99,[(-.1,1)]*100,[(float("nan"),1)]*100,
                    [(.2,0)]*100,[(.2,1)]*100,
                    [(.2,None)]*100):
            with self.subTest(candidate=repr(bad[:2])):
                if bad == [(.2,1)]*100:
                    with self.assertRaisesRegex(ValueError,"single-class"):
                        fit_intercept(bad)
                else:
                    with self.assertRaises(ValueError):
                        fit_intercept(bad)
        with self.assertRaises(ValueError):
            logistic_shift(float("nan"),0)
        with self.assertRaises(ValueError):
            logistic_shift(.5,float("inf"))

    def test_original_unchanged_and_temporal_splits_are_disjoint(self):
        revised,external,hashes,previous=fake()
        output=evaluate(revised,external,hashes,previous)
        self.assertEqual(output["train_years_revised_26_1"],list(TRAIN_YEARS))
        self.assertEqual(output["validation_years_revised_26_1"],
                         list(REVISED_VALIDATION_YEARS))
        self.assertEqual(output["external_label_years_source_separated"],
                         list(SEPARATE_VALIDATION_YEARS))
        self.assertTrue(set(TRAIN_YEARS).isdisjoint(REVISED_VALIDATION_YEARS))
        self.assertTrue(set(TRAIN_YEARS).isdisjoint(SEPARATE_VALIDATION_YEARS))
        self.assertEqual(output["prospective_2027_results_observed"],0)
        self.assertFalse(output["prospective_2027_forecast_modified"])
        self.assertFalse(output["external_holdout_confirmatory"])
        self.assertFalse(output["original_probabilities_retrained_or_modified"])
        self.assertEqual(set(output["per_known_origin_state"]),{"0","1"})
        for state in ("0","1"):
            obj=output["per_known_origin_state"][state]
            self.assertEqual(obj["train_revised_2012_2019"]["country_years"],
                             len(TRAIN_YEARS)*(161 if state=="0" else 35))
            self.assertEqual(len(obj["cross_vintage_by_year"]),2)
            self.assertGreater(obj["odds_multiplier"],0)
            self.assertIn("brier",obj["evaluation_separate_source_2024_2025"]["original_country_markov"])
            self.assertEqual(
                obj["evaluation_separate_source_2024_2025"]["observed_transitions"],
                8 if state=="0" else 10,
            )

    def test_fails_on_changed_original_cross_release_or_source_hash(self):
        old,outside,hashes,previous=fake()
        bad=copy.deepcopy(outside)
        bad[0]["outcome"]=1-bad[0]["outcome"]
        with self.assertRaisesRegex(ValueError,"392/69"):
            evaluate(old,bad,hashes,previous)
        wrong=dict(hashes)
        wrong["24.1"]="bad"
        with self.assertRaisesRegex(ValueError,"SHA"):
            evaluate(old,outside,wrong,previous)
        with self.assertRaisesRegex(ValueError,"[Oo]riginal committed"):
            evaluate(old,outside,hashes,{**previous,"status":"altered"})
        with self.assertRaisesRegex(ValueError,"training/development"):
            evaluate(old[:-196],outside,hashes,previous)

    def test_group_scoring_uses_transition_not_violence_label(self):
        rows=make_toy([2019])
        active=[r for r in rows if r["origin_state"]==1]
        entry=[r for r in rows if r["origin_state"]==0]
        a=score(active,0)
        b=score(entry,0)
        self.assertEqual(a["observed_transitions"],5)
        self.assertEqual(b["observed_transitions"],4)
        self.assertAlmostEqual(a["original_country_markov"]["mean_probability"],.18)
        self.assertAlmostEqual(b["original_country_markov"]["mean_probability"],.025)
        with self.assertRaisesRegex(ValueError,"Mixed"):
            score(rows,0)
        bad=copy.deepcopy(active)
        bad[0]["outcome"]=None
        with self.assertRaisesRegex(ValueError,"Missing"):
            transition_pair(bad[0])


if __name__=="__main__":
    unittest.main()
