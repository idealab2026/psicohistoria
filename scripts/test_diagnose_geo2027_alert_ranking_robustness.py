"""Prove sharp 2027 top-k adverse perturbation certificates by vertex enumeration."""
from __future__ import annotations
import copy
import itertools
import json
from pathlib import Path
import unittest

from prepare_geo2027_transition_alerts import FORECAST_PATH,MANIFEST_PATH
from diagnose_geo2027_alert_ranking_robustness import (
 ALERTS,ALERT_MANIFEST,VINTAGE,ALERT_SHA,build,membership_sets,
 historical_scenario_scales,
)


def inputs():
    return (FORECAST_PATH.read_bytes(),
            json.loads(MANIFEST_PATH.read_text(encoding="utf8")),
            ALERTS.read_bytes(),json.loads(ALERT_MANIFEST.read_text(encoding="utf8")),
            Path("scripts/prepare_geo2027_transition_alerts.py").read_bytes(),
            json.loads(VINTAGE.read_text(encoding="utf8")))


def selected(rows,scores,k):
    return set(sorted((r["country_id"] for r in rows),
                      key=lambda cid:(-scores[cid],cid))[:k])


class GEOAlertRobustnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs=inputs()
        cls.report=build(*cls.inputs)

    def test_exact_membership_matches_every_binary_rectangle_vertex(self):
        cases=[
            ([{"country_id":1,"score":.51},{"country_id":2,"score":.49},
              {"country_id":3,"score":.37},{"country_id":4,"score":.18}],2,.025),
            ([{"country_id":1,"score":.51},{"country_id":2,"score":.51},
              {"country_id":3,"score":.51},{"country_id":4,"score":.18}],2,.01),
            ([{"country_id":1,"score":.001},{"country_id":2,"score":.50},
              {"country_id":3,"score":.999},{"country_id":4,"score":.9}],2,.8),
        ]
        for rows,k,eps in cases:
            cert=membership_sets(rows,k,eps)
            outcomes=[]
            for flags in itertools.product((0,1),repeat=len(rows)):
                scores={r["country_id"]:min(1,max(0,r["score"]+(
                        eps if bit else -eps))) for r,bit in zip(rows,flags)}
                outcomes.append(selected(rows,scores,k))
            sure=set.intersection(*outcomes)
            possible=set.union(*outcomes)
            self.assertEqual(set(cert["guaranteed_issued_topk_country_ids"]),sure)
            self.assertEqual(set(cert["outsiders_that_may_enter"])|
                             set(cert["issued_topk_country_ids"]),possible)
            self.assertEqual(cert["selection_invariant_for_all_allowed_score_perturbations"],
                             len(sure)==k)

    def test_original_10_plus_5_alerts_and_exact_boundary_gaps(self):
        x=self.report
        self.assertEqual(x["n_original_issued_alerts"],15)
        self.assertEqual(x["n_origin_country_risk_set"],196)
        self.assertEqual(x["n_new_alerts_or_reissued_frozen_probabilities"],0)
        self.assertEqual(x["n_certified_2027_outcome_labels"],0)
        self.assertFalse(x["prospective_predictive_skill_demonstrated"])
        self.assertFalse(x["joint_country_dependence_estimated"])
        self.assertFalse(x["real_source_revision_2027_observed"])
        self.assertEqual(x["issued_alert_source_sha256"],ALERT_SHA)
        entry=x["group_results"]["0"];exit=x["group_results"]["1"]
        self.assertEqual(entry["issued_country_alert_ids"],
                         [516,433,483,702,373,615,484,640,531,517])
        self.assertEqual(exit["issued_country_alert_ids"],[41,436,540,660,541])
        self.assertEqual([entry["eligible_country_count"],exit["eligible_country_count"]],
                         [162,34])
        self.assertAlmostEqual(entry["issued_boundary_gap_probability"],
                               .130636493830-.124391314236,places=12)
        self.assertAlmostEqual(exit["issued_boundary_gap_probability"],
                               .311596687954-.296608277490,places=12)
        self.assertTrue(entry["perturbation_scenarios"][0][
            "selection_invariant_for_all_allowed_score_perturbations"])
        self.assertTrue(exit["perturbation_scenarios"][0][
            "selection_invariant_for_all_allowed_score_perturbations"])

    def test_historical_p95_stress_stable_but_single_country_max_not_certified(self):
        x=self.report
        for st in ("0","1"):
            group=x["group_results"][st]
            scenarios={r["scenario"]:r for r in group["perturbation_scenarios"]}
            for label in ("NO_PERTURBATION","TWO_TENTHS_PP",
                          "HISTORICAL_H2_LARGEST_WITHIN_PAIR_P95"):
                self.assertTrue(scenarios[label][
                    "selection_invariant_for_all_allowed_score_perturbations"],
                    (st,label))
            self.assertFalse(scenarios["HISTORICAL_H2_MAX_SINGLE_COUNTRY"][
                "selection_invariant_for_all_allowed_score_perturbations"])
            self.assertGreater(scenarios["HISTORICAL_H2_MAX_SINGLE_COUNTRY"][
                "outsiders_that_may_enter_n"],0)
            self.assertTrue(scenarios["TEN_PP"][
                "not_confidence_probability_or_real_future_revision"])

    def test_official_vintage_H2_scale_and_mutated_provenance(self):
        scale=historical_scenario_scales(self.inputs[-1])
        self.assertAlmostEqual(scale["empirical_largest_H2_country_probability_change"],
                               .054606417304,places=12)
        self.assertAlmostEqual(scale["empirical_largest_H2_within_pair_P95_country_change"],
                               .002563631883,places=12)
        self.assertTrue(scale["P95_and_max_are_historical_descriptives_not_future_probabilistic_bounds"])
        self.assertEqual(scale["which_H2_pair_attained_largest"],
                         {"origin":2022,"original_edition":"23.1","later_edition":"26.1"})
        broken=copy.deepcopy(self.inputs[-1])
        broken["source_versions_and_sha256"]["26.1"]="0"*64
        with self.assertRaisesRegex(ValueError,"provenance"):
            historical_scenario_scales(broken)
        broken=copy.deepcopy(self.inputs[-1])
        broken["historical_comparisons"][0]["horizons"][0][
            "p95_absolute_probability_change"]=1.
        with self.assertRaisesRegex(ValueError,"sensitivity"):
            historical_scenario_scales(broken)

    def test_original_sources_and_issued_alert_manifest_are_immutable(self):
        a=list(self.inputs);a[0]+=b"tampered"
        with self.assertRaises(ValueError):build(*a)
        a=list(self.inputs);a[2]=a[2].replace(b"Burundi",b"Corrupted")
        with self.assertRaisesRegex(ValueError,"SHA"):build(*a)
        a=list(self.inputs);a[3]=copy.deepcopy(a[3])
        a[3]["issue_sha256"]="0"*64
        with self.assertRaises(ValueError):build(*a)
        a=list(self.inputs);a[-1]=copy.deepcopy(a[-1])
        a[-1]["prospective_2027_2028_skill_demonstrated"]=True
        with self.assertRaisesRegex(ValueError,"Historical"):build(*a)

    def test_reject_bad_country_ids_probs_and_eps(self):
        original=[{"country_id":1,"score":.45},{"country_id":2,"score":.33},
                  {"country_id":3,"score":.25}]
        for e in (-.1,float("nan"),1.1,True):
            with self.assertRaises(ValueError):membership_sets(original,1,e)
        for rows in (
            [{"country_id":1,"score":.45},{"country_id":1,"score":.33}],
            [{"country_id":1,"score":True},{"country_id":2,"score":.3}],
            [{"country_id":1,"score":1.0},{"country_id":2,"score":.3}],
        ):
            with self.assertRaises(ValueError):membership_sets(rows,1,.1)
        with self.assertRaises(ValueError):membership_sets(original,3,.1)


if __name__=="__main__":
    unittest.main()
