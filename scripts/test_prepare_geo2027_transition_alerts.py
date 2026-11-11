"""Reproducibility and anti-tamper tests for *future-only* 2027 alert issuance."""
import copy
import json
import unittest

from prepare_geo2027_transition_alerts import (
    BUDGETS, FORECAST_PATH, MANIFEST_PATH, SOURCE_SHA256, build,
    selection, sha, validate, verify_source,
)


def frozen():
    raw = FORECAST_PATH.read_bytes()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf8"))
    return raw, manifest


class Geo2027AlertIssueTests(unittest.TestCase):
    def test_only_immutable_original_source_accepted(self):
        raw, manifest = frozen()
        self.assertEqual(sha(raw), SOURCE_SHA256)
        original, rows = verify_source(raw, manifest)
        self.assertEqual(len(rows), 196)
        self.assertEqual(sum(r["last_observed_state_2025"] for r in rows), 34)
        self.assertEqual(original["target"]["year"], 2027)
        with self.assertRaisesRegex(ValueError, "modified"):
            verify_source(raw + b" ", manifest)
        with self.assertRaisesRegex(ValueError, "issuance"):
            verify_source(raw, {**manifest, "outcomes_resolved": 1})
        with self.assertRaisesRegex(ValueError, "issuance"):
            verify_source(raw, {**manifest, "first_public_forecast_commit": ""})

    def test_exact_15_unique_alerts_do_not_refit_forecast(self):
        raw, manifest = frozen()
        one = build(raw, manifest, b"fixed-test-script")
        two = build(raw, manifest, b"fixed-test-script")
        self.assertEqual(one, two)
        self.assertTrue(validate(one))
        self.assertEqual(one["generator_sha256"], sha(b"fixed-test-script"))
        self.assertEqual(one["source_forecast_sha256"], SOURCE_SHA256)
        self.assertEqual(one["2027_outcomes_resolved"], 0)
        self.assertFalse(one["demonstrated_prospective_skill"])
        groups = one["risk_groups"]
        self.assertEqual(groups["0"]["eligible_country_count"], 162)
        self.assertEqual(groups["1"]["eligible_country_count"], 34)
        self.assertEqual(groups["0"]["budget"], 10)
        self.assertEqual(groups["1"]["budget"], 5)
        self.assertTrue(all(groups[s]["selection_is_unique_no_boundary_tie"]
                            for s in ("0", "1")))
        for s in ("0", "1"):
            entries = groups[s]["selected_countries"]
            self.assertEqual([v["rank"] for v in entries],
                             list(range(1, len(entries) + 1)))
            probs = [r["transition_probability_model"] for r in entries]
            self.assertEqual(probs, sorted(probs, reverse=True))
        self.assertTrue(groups["0"]["alert_cutoff_score"] >
                        groups["0"]["next_not_selected_score"])
        self.assertTrue(groups["1"]["alert_cutoff_score"] >
                        groups["1"]["next_not_selected_score"])

    def test_no_silent_tie_breaks_at_public_alert_boundary(self):
        _, rows = verify_source(*frozen())
        for state in (0, 1):
            modified = copy.deepcopy(rows)
            eligible = sorted(
                (r for r in modified if r["last_observed_state_2025"] == state),
                key=lambda r: (-r["p_model"] if state == 0 else r["p_model"])
            )
            k = BUDGETS[state]
            # Make the first non-selected candidate tied with the cutoff.
            eligible[k]["p_model"] = eligible[k-1]["p_model"]
            with self.assertRaisesRegex(ValueError, "Tied"):
                selection(modified, state)

    def test_budget_and_order_cannot_change_after_issue(self):
        raw, manifest = frozen()
        original = build(raw, manifest, b"script")
        altered = copy.deepcopy(original)
        altered["risk_groups"]["0"]["budget"] = 11
        with self.assertRaisesRegex(ValueError, "budget"):
            validate(altered)
        altered = copy.deepcopy(original)
        altered["risk_groups"]["0"]["selected_countries"][0]["country_id"] = (
            altered["risk_groups"]["1"]["selected_countries"][0]["country_id"]
        )
        with self.assertRaisesRegex(ValueError, "duplicated"):
            validate(altered)


if __name__ == "__main__":
    unittest.main()
