"""Strict first-issued ACD2027 manifest and immutable-generator tamper tests."""
import copy
import json
import unittest

from audit_issued_acd2027_retention import (
    ISSUE_PATH, MANIFEST, GENERATOR, EXPECTED_ISSUE_SHA256,
    EXPECTED_GENERATOR_BLOB, audit, git_blob_hash,
)
from prepare_acd2027_prospective_retention import (
    FORECAST_ID, ORIGIN, TARGET, ACD_SOURCE_SHA256,
)


class FirstIssuedACD2027IntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=ISSUE_PATH.read_bytes()
        cls.manifest=json.loads(MANIFEST.read_text(encoding="utf8"))
        cls.generator=GENERATOR.read_bytes()

    def attempt(self,manifest=None,raw=None,generator=None):
        return audit(
            self.raw if raw is None else raw,
            self.manifest if manifest is None else manifest,
            self.generator if generator is None else generator,
            b"not a genuine UCDP ZIP; reject before consuming",
        )

    def test_file_identity_and_source_generator_are_immutable(self):
        import hashlib
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),EXPECTED_ISSUE_SHA256)
        self.assertEqual(git_blob_hash(self.generator),EXPECTED_GENERATOR_BLOB)
        self.assertEqual(self.manifest["origin_year"],ORIGIN)
        self.assertEqual(self.manifest["target_year"],TARGET)
        self.assertEqual(self.manifest["forecast_id"],FORECAST_ID)
        self.assertEqual(self.manifest["2027_outcomes_resolved"],0)
        self.assertEqual(self.manifest["origin_risk_set_country_count"],32)
        self.assertEqual(ACD_SOURCE_SHA256,self.manifest["source_zip_sha256"])
        d=json.loads(self.raw)
        self.assertEqual(len(d["countries"]),32)
        self.assertEqual(d["2027_outcomes_resolved"],0)
        self.assertFalse(d["actual_2027_outcomes_used"])

    def test_cannot_substitute_a_future_outcome_in_manifest(self):
        for name,value in (
            ("2027_outcomes_resolved",1),
            ("prospective_predictive_skill_demonstrated",True),
            ("source_data_last_year",2026),
            ("target_year",2026),
            ("origin_risk_set_country_count",196),
            ("full_196_country_forecast",True),
            ("trained_on_2027_labels",True),
            ("no_2026_labels_used",False),
            ("original_geo2027_and_alerts_modified",True),
            ("first_public_git_commit","0"*40),
            ("first_public_git_commit_utc","2027-01-01T00:00:00Z"),
        ):
            m=copy.deepcopy(self.manifest)
            m[name]=value
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    self.attempt(manifest=m)

    def test_cannot_rewrite_public_issue_or_its_generator(self):
        with self.assertRaisesRegex(ValueError,"forecast SHA-256"):
            self.attempt(raw=self.raw+b" ")
        with self.assertRaisesRegex(ValueError,"generator modified"):
            self.attempt(generator=self.generator+b" altered")
        with self.assertRaisesRegex(ValueError,"source hash"):
            self.attempt()

    def test_syntactic_timestamp_alone_does_not_claim_notarization(self):
        m=copy.deepcopy(self.manifest)
        m["first_issue_timestamp_independently_notarized"]=True
        with self.assertRaisesRegex(ValueError,"manifest altered"):
            self.attempt(manifest=m)
        m=copy.deepcopy(self.manifest)
        m["first_public_git_commit_utc"]="2026-11-12"
        with self.assertRaisesRegex(ValueError,"timestamp invalid"):
            self.attempt(manifest=m)


if __name__=="__main__":
    unittest.main()
