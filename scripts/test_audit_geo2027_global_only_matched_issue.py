"""Immutable first-complete 196-country issue and strict future scoring tests."""
from __future__ import annotations

import copy
import json
import unittest

from audit_geo2027_log1p_shadow_issue import (
    ISSUE as OLD_SHADOW, MANIFEST as OLD_MANIFEST, ORIGINAL,
)
from audit_geo2027_log1p_issued_death_stress import ALERTS
from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, FROZEN_SHA256, FIRST_COMMIT,
    audit, prospective_full196_score, sha,
)


class GlobalOnlyFirstCompleteIssueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.issue_bytes=ISSUE.read_bytes()
        cls.manifest_bytes=MANIFEST.read_bytes()
        cls.original_bytes=ORIGINAL.read_bytes()
        cls.old_shadow_bytes=OLD_SHADOW.read_bytes()
        cls.old_manifest_bytes=OLD_MANIFEST.read_bytes()
        cls.alerts_bytes=ALERTS.read_bytes()
        cls.issue=json.loads(cls.issue_bytes)

    def verified(self,issue=None,manifest=None):
        return audit(
            self.issue_bytes if issue is None else issue,
            self.manifest_bytes if manifest is None else manifest,
            self.original_bytes,
            self.old_shadow_bytes,
            self.old_manifest_bytes,
            self.alerts_bytes)

    def test_immutable_first_public_sha_and_source_manifest(self):
        result=self.verified()
        self.assertEqual(sha(self.issue_bytes),FROZEN_SHA256)
        self.assertEqual(result["first_complete_public_commit"],FIRST_COMMIT)
        self.assertEqual(result["country_n"],196)
        self.assertEqual(result["official_2027_outcomes_resolved"],0)

    def test_exact_196_original_country_membership_and_0_1_arms(self):
        rows=self.issue["countries"]
        self.assertEqual(len(rows),196)
        self.assertEqual(
            [r["country_id"] for r in rows],
            sorted({r["country_id"] for r in rows}))
        self.assertTrue(all(r["country_supervised_training_rows_withheld"]>=1
                            for r in rows))
        zero=[r for r in rows if r["origin_deaths_best_2025"]==0]
        middle=[r for r in rows if 1<=r["origin_deaths_best_2025"]<25]
        active=[r for r in rows if r["origin_deaths_best_2025"]>=25]
        self.assertEqual((len(zero),len(middle),len(active)),(154,8,34))
        for r in zero+active:
            self.assertEqual(r["global_only_alpha0_p_active_2027"],
                             r["global_only_alpha1_p_active_2027"])

    def test_changed_issued_probability_fails_even_when_model_metadata_unchanged(self):
        mutated=copy.deepcopy(self.issue)
        mutated["countries"][0]["global_only_alpha1_p_active_2027"]+=.00000001
        with self.assertRaisesRegex(ValueError,"SHA"):
            self.verified((json.dumps(mutated,sort_keys=True,indent=2,
                                      ensure_ascii=False)+"\n").encode())

    def test_changed_first_complete_manifest_fails(self):
        manifest=json.loads(self.manifest_bytes)
        manifest["first_complete_forecast_commit"]="0"*40
        with self.assertRaisesRegex(ValueError,"manifest"):
            self.verified(manifest=json.dumps(manifest).encode())

    def test_future_scoring_rejects_one_missing_country_as_nonzero_or_zero(self):
        labels={r["country_id"]:0 for r in self.issue["countries"]}
        missing=labels.copy()
        missing.pop(next(iter(missing)))
        with self.assertRaisesRegex(ValueError,"196"):
            prospective_full196_score(self.issue,missing)
        extra=labels.copy()
        extra[123456]=0
        with self.assertRaisesRegex(ValueError,"196"):
            prospective_full196_score(self.issue,extra)
        invalid=labels.copy()
        invalid[next(iter(invalid))]=None
        with self.assertRaisesRegex(ValueError,"196"):
            prospective_full196_score(self.issue,invalid)
        invalid=labels.copy()
        invalid[next(iter(invalid))]=False
        with self.assertRaisesRegex(ValueError,"196"):
            prospective_full196_score(self.issue,invalid)

    def test_future_scoring_synthetic_all_zero_and_one_exact_full_cohort(self):
        # Synthetic unit tests ONLY. Neither result is a real UCDP outcome.
        ids=[r["country_id"] for r in self.issue["countries"]]
        for y in (0,1):
            got=prospective_full196_score(self.issue,{cid:y for cid in ids})
            self.assertEqual(got["n_country_labels"],196)
            self.assertEqual(got["positive_labels"],196*y)
            self.assertEqual(len(got["metrics"]),5)
            self.assertEqual(len(got["predeclared_paired_differences"]),7)
            new=got["metrics"]["global_only_alpha1"]["brier"]
            old=got["metrics"]["original_LOG1P"]["brier"]
            self.assertAlmostEqual(
                got["predeclared_paired_differences"][
                    "primary_Brier_globalonly_alpha1_minus_original_LOG1P"],
                new-old)
            for m in got["metrics"].values():
                self.assertTrue(0<=m["brier"]<=1)
                self.assertGreater(m["logloss"],0)

    def test_future_scoring_cannot_mark_issued_file_as_resolved(self):
        modified=copy.deepcopy(self.issue)
        modified["official_2027_outcomes_resolved"]=196
        zeros={r["country_id"]:0 for r in modified["countries"]}
        with self.assertRaises(ValueError):
            prospective_full196_score(modified,zeros)


if __name__=="__main__":
    unittest.main()
