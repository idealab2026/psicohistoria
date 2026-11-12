"""No official or fabricated 2027 observations: only adversarial synthetic algebra."""
import copy
import itertools
import math
import unittest

from diagnose_geo2027_shadow_break_even import (
    COUNT, EXPECTED_SHADOW_SHA256, diagnose, frontier, score_leverage,
)
from evaluate_geo2027_calibrated_shadow_official import (
    load_authenticated, pair_metrics,
)


class ShadowBreakEvenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original,cls.shadow,cls.manifest=load_authenticated()
        cls.leverage=score_leverage(cls.original,cls.shadow)

    def test_toy_three_country_sharp_frontier_matches_exhaustive_enumeration(self):
        toy=[
            {"country_id":1,"persistence_delta_sse":-.2,"transition_penalty_sse":.3},
            {"country_id":2,"persistence_delta_sse":-.2,"transition_penalty_sse":.5},
            {"country_id":3,"persistence_delta_sse":-.2,"transition_penalty_sse":.7},
        ]
        report=frontier(toy)
        self.assertEqual(report["fewest_transitions_original_can_beat_shadow"],1)
        self.assertEqual(report["fewest_transitions_original_must_beat_shadow"],2)
        for k in range(4):
            possible=[(-.6 + sum(toy[i]["transition_penalty_sse"]
                                  for i in chosen))/3
                      for chosen in itertools.combinations(range(3),k)]
            row=report["sharp_bounds_by_total_number_of_transitions"][k]
            self.assertAlmostEqual(row["best_case_shadow_delta_brier"],min(possible))
            self.assertAlmostEqual(row["worst_case_shadow_delta_brier"],max(possible))
        self.assertEqual(report["sharp_bounds_by_total_number_of_transitions"][0][
            "classification"],"SHADOW_BEATS_ORIGINAL_FOR_ANY_K_COUNTRIES")
        self.assertEqual(report["sharp_bounds_by_total_number_of_transitions"][1][
            "classification"],"IDENTITY_OF_TRANSITIONING_COUNTRIES_MATTERS_OR_TIE_POSSIBLE")
        self.assertEqual(report["sharp_bounds_by_total_number_of_transitions"][2][
            "classification"],"ORIGINAL_BEATS_SHADOW_FOR_ANY_K_COUNTRIES")

    def test_original_issued_source_and_196_break_even_invariants(self):
        report=diagnose(self.original,self.shadow,self.manifest)
        self.assertEqual(report["target_year"],2027)
        self.assertEqual(report["2027_outcomes_observed"],0)
        self.assertFalse(report["observed_2027_scenarios_used"])
        self.assertFalse(report["original_forecast_or_shadow_modified"])
        self.assertEqual(report["shadow_issued_forecast_sha256"],EXPECTED_SHADOW_SHA256)
        overall=report["total_196_country_exact_frontier"]
        self.assertEqual(overall["n"],COUNT)
        self.assertEqual(len(overall["sharp_bounds_by_total_number_of_transitions"]),COUNT+1)
        self.assertEqual(overall["fewest_transitions_original_can_beat_shadow"],6)
        self.assertEqual(overall["fewest_transitions_original_must_beat_shadow"],128)
        self.assertLess(overall["all_persist_delta_brier_shadow_minus_original"],0)
        self.assertGreater(overall["all_transition_delta_brier_shadow_minus_original"],0)
        self.assertEqual(report["by_known_2025_origin_state"]["0"]["n"],162)
        self.assertEqual(report["by_known_2025_origin_state"]["1"]["n"],34)
        self.assertEqual(len(report["highest_brier_leverage_not_highest_probability_of_transition"]),10)
        self.assertAlmostEqual(
            report["expected_paired_brier_delta_if_original_probabilities_are_true"],
            report["per_country_squared_forecast_differences_mean"])
        self.assertAlmostEqual(
            report["expected_paired_brier_delta_if_shadow_probabilities_are_true"],
            -report["per_country_squared_forecast_differences_mean"])
        self.assertAlmostEqual(
            report["expected_paired_brier_delta_if_original_probabilities_are_true"],
            0.001935054487972817,places=12)

    def test_exact_frontier_equals_actual_paired_brier_for_selected_outcome_sets(self):
        old=self.original["countries"]
        new=self.shadow["countries"]
        base=old[0]["last_observed_state_2025"]
        ordered_high=sorted(self.leverage,key=lambda x:-x["transition_penalty_sse"])
        ordered_low=sorted(self.leverage,key=lambda x:x["transition_penalty_sse"])
        issued_pairs=[{
            "country_id":a["country_id"],
            "origin_state":a["last_observed_state_2025"],
            "p_original":a["p_model"],
            "p_shadow":b["shadow_p_active_2027"],
        } for a,b in zip(old,new)]
        snap=frontier(self.leverage)["sharp_bounds_by_total_number_of_transitions"]
        for k in (0,1,5,6,10,50,100,127,128,196):
            for order,key in ((ordered_high,"worst_case_shadow_delta_brier"),
                              (ordered_low,"best_case_shadow_delta_brier")):
                transitioning={r["country_id"] for r in order[:k]}
                labels={r["country_id"]:(
                    1-r["last_observed_state_2025"] if r["country_id"] in transitioning
                    else r["last_observed_state_2025"]) for r in old}
                score=pair_metrics(issued_pairs,labels)
                self.assertAlmostEqual(
                    score["primary_delta_brier_shadow_minus_original"],
                    snap[k][key],places=11)

    def test_reject_modified_source_labels_and_nonmonotone_calibration(self):
        changed=copy.deepcopy(self.shadow)
        changed["countries"][0]["shadow_p_active_2027"]=(
            self.original["countries"][0]["p_model"] + .1)
        with self.assertRaisesRegex(ValueError,"monotone"):
            score_leverage(self.original,changed)
        changed=copy.deepcopy(self.shadow)
        changed["countries"][0]["original_issued_p_active_2027"]+=.01
        with self.assertRaisesRegex(ValueError,"Mismatch"):
            score_leverage(self.original,changed)
        wrong=copy.deepcopy(self.manifest)
        wrong["2027_outcomes_resolved"]=1
        with self.assertRaisesRegex(ValueError,"issuance"):
            diagnose(self.original,self.shadow,wrong)
        with self.assertRaisesRegex(ValueError,"unique"):
            frontier([self.leverage[0],self.leverage[0]])
        with self.assertRaisesRegex(ValueError,"Invalid"):
            frontier([{"country_id":7,
                       "persistence_delta_sse":-.2,
                       "transition_penalty_sse":-1}])

    def test_no_country_switch_probability_is_learned(self):
        result=diagnose(self.original,self.shadow,self.manifest)
        self.assertNotIn("estimated_correlation",result)
        self.assertNotIn("2027_observations",result)
        self.assertIn("NOT_EVIDENCE_OF_SKILL",result["status"])
        self.assertTrue(all(
            r["2025_origin_state"]==1 for r in result[
                "highest_brier_leverage_not_highest_probability_of_transition"][:6]
        ))


if __name__=="__main__":
    unittest.main()
