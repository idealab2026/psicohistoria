import unittest

from test_backtest_archived_country_vintages import versions,metadata
from diagnose_2027_origin_state import (
    GROUP_LABELS,TOP_K,rows_from_vintages,group_stats,rank_summary,evaluate
)

def fixture():
    data=versions()
    # Two outcomes pinned to the same 69-positives cohort as the official test.
    for cid in range(1,197):
        data["25.1"][cid][2024]=int(cid<=35)
        data["26.1"][cid][2025]=int(cid<=34)
    return data

class OriginStateDiagnostics(unittest.TestCase):
    def test_conditional_metrics_account_for_every_country_and_new_threshold_entry(self):
        result=evaluate(fixture(),metadata())
        self.assertEqual(result["pooled_total"],392)
        self.assertEqual(result["pooled_positive"],69)
        self.assertEqual(result["target_years"],[2024,2025])
        self.assertEqual(result["observation_horizon_calendar_steps"],2)
        self.assertEqual(result["true_issued_prospective_forecasts_evaluated"],0)
        self.assertFalse(result["first_historical_release_timestamps_verified"])
        self.assertTrue(result["original_2027_forecast_unchanged"])
        self.assertIn("not necessarily conflict onset",result["false_interpretation_prohibited"])
        inactive=result["conditional_groups"]["BELOW_25_AT_ORIGIN"]
        active=result["conditional_groups"]["AT_LEAST_25_AT_ORIGIN"]
        self.assertEqual(inactive["country_years"]+active["country_years"],392)
        self.assertEqual(inactive["positive_threshold_outcomes"]+active["positive_threshold_outcomes"],69)
        self.assertTrue(0<inactive["country_years"]<392)
        self.assertTrue(0<active["country_years"]<392)
        self.assertEqual(sum(x["inactive_to_active"] for x in result["annual"]),
                         inactive["positive_threshold_outcomes"])
        self.assertEqual(sum(x["active_to_active"] for x in result["annual"]),
                         active["positive_threshold_outcomes"])
        self.assertTrue(all(len(x["top_k"])==3 for x in result["annual"]))

    def test_target_outcome_changes_scores_but_never_training_risk(self):
        data=fixture()
        before=evaluate(data,metadata())
        data["25.1"][1][2024]=0
        with self.assertRaisesRegex(ValueError,"pinned study"):
            evaluate(data,metadata())
        # Training and probabilities remain invariant even if an outcome changes.
        records=rows_from_vintages(data)
        original=rows_from_vintages(fixture())
        self.assertEqual([x["p_model"] for x in records[0][1]],
                         [x["p_model"] for x in original[0][1]])

    def test_fail_closed_on_future_rows_in_historical_origin(self):
        data=fixture()
        data["23.1"][1][2023]=1
        with self.assertRaisesRegex(ValueError,"cutoffs"):
            rows_from_vintages(data)

    def test_alert_budgets_are_frozen_and_deterministic(self):
        rows=[
            {"country_id":i+1,"p_model":1-(i/100),"outcome":int(i in (0,2,8,50))}
            for i in range(60)
        ]
        top=rank_summary(rows)
        self.assertEqual(set(top),{"10","20","35"})
        self.assertEqual(top["10"]["true_positives"],3)
        self.assertAlmostEqual(top["10"]["precision_at_k"],.3)
        self.assertAlmostEqual(top["10"]["recall_at_k"],.75)
        self.assertEqual(top["10"]["random_ranking_expected_hits"],10*4/60)
        self.assertEqual(rank_summary(rows),top)
        with self.assertRaisesRegex(ValueError,"Budget"):
            rank_summary(rows[:15])

    def test_country_subgroup_score_and_calibration_are_aggregates(self):
        group=[
            {"country_id":i,"p_model":.1,"p_global_markov":.2,
             "p_baseline_global_5y":.3,"outcome":int(i%10==0)}
            for i in range(1,101)
        ]
        scores=group_stats(group)
        self.assertEqual(scores["country_years"],100)
        self.assertEqual(scores["positive_threshold_outcomes"],10)
        self.assertAlmostEqual(scores["observed_rate"],.1)
        self.assertEqual(sum(x["n"] for x in scores["calibration_bins"]),100)

if __name__=="__main__":unittest.main()
