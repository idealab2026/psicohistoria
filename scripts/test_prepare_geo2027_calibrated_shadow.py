"""Adversarial contract tests for pre-2027 calibrated shadow issuance."""
from __future__ import annotations

import copy
import json
import math
import unittest

from prepare_geo2027_calibrated_shadow import (
    ALERT_PATH, EXPECTED_ALPHA, EXPECTED_COUNTS, FORECAST_PATH, MANIFEST_PATH,
    ORIGINAL_FIRST_COMMIT, REPORT_PATH, SOURCE_SHA256, SHADOW_ID,
    authenticated_inputs, canonical, construct, sha,
)


def official_fixture():
    original = FORECAST_PATH.read_bytes()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf8"))
    calibration = REPORT_PATH.read_bytes()
    alerts = ALERT_PATH.read_bytes()
    return original, manifest, calibration, alerts


class CalibratedGeo2027ShadowTests(unittest.TestCase):
    def test_shadow_never_mutates_any_issued_country_probability(self):
        original, manifest, calibration, alerts = official_fixture()
        self.assertEqual(sha(original), SOURCE_SHA256)
        doc = construct(original, manifest, calibration, alerts, b"script bytes")
        self.assertEqual(doc["forecast_id"], SHADOW_ID)
        self.assertEqual(doc["n_countries"], 196)
        self.assertEqual(doc["n_initially_inactive"], 162)
        self.assertEqual(doc["n_initially_active"], 34)
        self.assertEqual(doc["2027_outcomes_resolved"], 0)
        self.assertFalse(doc["original_forecast_altered"])
        self.assertFalse(doc["original_alerts_altered"])
        self.assertFalse(doc["prospective_predictive_skill_demonstrated"])
        self.assertTrue(doc["design_posthoc_not_independently_confirmatory"])
        self.assertEqual(doc["original_forecast_first_public_commit"], ORIGINAL_FIRST_COMMIT)
        self.assertEqual(doc["training_only_calibration_intercepts_log_odds"],
                         {str(k):EXPECTED_ALPHA[k] for k in (0,1)})
        self.assertEqual(doc["calibration_train_years_revised_26_1"],
                         list(range(2012,2020)))
        ids = [v["country_id"] for v in doc["countries"]]
        self.assertEqual(len(set(ids)),196)
        original_doc = json.loads(original)
        self.assertEqual(
            [row["p_model"] for row in original_doc["countries"]],
            [row["original_issued_p_active_2027"] for row in doc["countries"]]
        )
        self.assertEqual(sha(original),SOURCE_SHA256)
        self.assertEqual(doc,construct(*official_fixture(),b"script bytes"))
        self.assertEqual(canonical(doc)[-1:],b"\n")

    def test_alert_positions_ranking_and_direction_preserved(self):
        original,manifest,calibration,alerts=official_fixture()
        doc=construct(original,manifest,calibration,alerts,b"script")
        for state in (0,1):
            g=[r for r in doc["countries"] if r["origin_state_2025"]==state]
            self.assertEqual(len(g),EXPECTED_COUNTS[state])
            original_q=[r["original_issued_p_active_2027"] if state==0
                        else 1-r["original_issued_p_active_2027"] for r in g]
            shadow_q=[r["shadow_p_transition_2027"] for r in g]
            self.assertTrue(all(b<a for a,b in zip(original_q,shadow_q)))
            for row in g:
                self.assertAlmostEqual(
                    row["shadow_p_active_2027"] if state==0
                    else 1-row["shadow_p_active_2027"],
                    row["shadow_p_transition_2027"],delta=1.1e-12)
            a=doc["original_15_alert_expected_hits"][str(state)]
            self.assertEqual(a["fixed_issued_alert_budget"],10 if state==0 else 5)
            self.assertLess(a["expected_hits_shadow"],a["expected_hits_original"])
            self.assertFalse(a["alert_selection_changed"])

    def test_original_issue_and_training_contract_cannot_be_tampered(self):
        original,manifest,calibration,alerts=official_fixture()
        with self.assertRaisesRegex(ValueError,"modified"):
            construct(original+b" ",manifest,calibration,alerts,b"script")
        wrong=copy.deepcopy(manifest)
        wrong["first_public_forecast_commit"]="0"*40
        with self.assertRaisesRegex(ValueError,"first public commit"):
            construct(original,wrong,calibration,alerts,b"script")
        obj=json.loads(calibration)
        obj["per_known_origin_state"]["0"][
            "alpha_log_odds_shift_estimated_from_2012_2019_only"]+=.1
        with self.assertRaisesRegex(ValueError,"intercept"):
            construct(original,manifest,canonical(obj),alerts,b"script")
        obj=json.loads(calibration)
        obj["prospective_2027_results_observed"]=1
        with self.assertRaisesRegex(ValueError,"provenance"):
            construct(original,manifest,canonical(obj),alerts,b"script")
        obj=json.loads(calibration)
        obj["external_holdout_confirmatory"]=True
        with self.assertRaisesRegex(ValueError,"provenance"):
            construct(original,manifest,canonical(obj),alerts,b"script")
        altered=json.loads(alerts)
        altered["2027_outcomes_resolved"]=1
        with self.assertRaisesRegex(ValueError,"alert cohort"):
            construct(original,manifest,canonical(json.loads(calibration)),
                      canonical(altered),b"script")

    def test_original_vintages_stay_immutable(self):
        original,manifest,calibration,alerts=official_fixture()
        original_doc,rows,alphas,alert=authenticated_inputs(
            original,manifest,calibration,alerts)
        self.assertEqual(original_doc["source"]["data_last_year"],2025)
        self.assertEqual(original_doc["target"]["year"],2027)
        self.assertEqual(set(alphas),{0,1})
        self.assertEqual(len(rows),196)
        self.assertFalse(any("outcome_2027" in row for row in rows))


if __name__=="__main__":
    unittest.main()
