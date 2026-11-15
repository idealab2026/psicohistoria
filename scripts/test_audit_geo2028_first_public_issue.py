"""Validate genuine pre-target 2028 issue and strict frozen first-public bytes."""
import copy
import json
import unittest

import audit_geo2028_first_public_issue as audit
import build_2027_prospective_registry as registry


class GEO2028FirstPublicIssueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(audit.ROOT/audit.SOURCE_PATH).read_bytes()
        cls.manifest=json.loads((audit.ROOT/audit.MANIFEST_PATH).read_text(encoding="utf8"))
        docs,manifests=registry.read_issued()
        cls.original=docs["geo"]
        cls.ledger=registry.make_registry(docs,manifests)

    def test_exact_first_public_sha_and_196_row_2027_immutable_crosswalk(self):
        v=audit.check_raw(self.raw,self.manifest,self.original,self.ledger)
        self.assertEqual(v["forecast_sha256"],audit.ISSUE_SHA)
        self.assertEqual(v["n_2028_country_issues"],196)
        self.assertEqual(v["n_2027_country_endpoint_issues_still_unresolved"],424)
        self.assertEqual(v["observed_2028_labels_used"],0)
        self.assertTrue(v["original_2027_horizon_2_forecasts_preserved"])
        self.assertFalse(v["cross_year_country_origin_independence_demonstrated"])
        self.assertFalse(v["2028_independently_notarized"])

    def test_adversarial_first_public_issue_change_rejected(self):
        bad=json.loads(self.raw)
        bad["countries"][0]["p_model"]+=.00001
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            audit.check_raw(registry.canonical(bad),
                            self.manifest,self.original,self.ledger)
        bad=json.loads(self.raw)
        bad["target"]["year"]=2027
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            audit.check_raw(registry.canonical(bad),
                            self.manifest,self.original,self.ledger)

    def test_manifest_first_commit_dates_and_false_independence_protected(self):
        for key,value in (
            ("first_public_forecast_commit","not-a-real-first-commit"),
            ("first_public_forecast_commit_utc","2028-11-15T18:27:05Z"),
            ("preregistered_protocol_main_commit","other"),
            ("forecast_sha256","original-file-missing"),
            ("n_issued_country_probabilities",195),
            ("independently_notarized",True),
            ("cross_horizon_2027_2028_outcomes_statistically_independent",True),
            ("actual_2028_outcomes_observed",1),
            ("prospective_predictive_skill_demonstrated",True),
            ("new_2028_TWO_year_origin_2026_forecast_included",True),
        ):
            tampered=copy.deepcopy(self.manifest)
            tampered[key]=value
            with self.subTest(field=key):
                with self.assertRaisesRegex(ValueError,"provenance manifest"):
                    audit.check_raw(self.raw,tampered,self.original,self.ledger)

    def test_crosswalk_and_target_horizon_wont_claim_independent_replica(self):
        original=copy.deepcopy(self.original)
        original["countries"][0]["p_model"]+=.05
        with self.assertRaisesRegex(ValueError,"rewrote original 2027"):
            audit.check_raw(self.raw,self.manifest,original,self.ledger)
        original=copy.deepcopy(self.original)
        original["countries"][0]["country_id"]=9917
        with self.assertRaisesRegex(ValueError,"exact 2027 origin"):
            audit.check_raw(self.raw,self.manifest,original,self.ledger)
        ledger=copy.deepcopy(self.ledger)
        ledger["n_verified_future_2027_outcomes"]=1
        with self.assertRaisesRegex(ValueError,"no longer issued-unresolved"):
            audit.check_raw(self.raw,self.manifest,self.original,ledger)


if __name__=="__main__":
    unittest.main()
