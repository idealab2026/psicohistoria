import unittest
import json
from copy import deepcopy
from audit_frozen_newconf_2027 import (
    audit,FORECAST,MANIFEST,GENERATOR,FROZEN_SHA,FROZEN_GENERATOR_SHA,
    PREREG_COMMIT,FIRST_COMMIT
)

class FrozenNewconf2027AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.forecast=FORECAST.read_bytes()
        cls.manifest=json.loads(MANIFEST.read_text())
        cls.generator=GENERATOR.read_bytes()

    def test_real_2027_newconf_file_is_canonical_and_issued_before_target(self):
        result=audit(self.forecast,self.manifest,self.generator)
        self.assertEqual(result["forecast_sha256"],FROZEN_SHA)
        self.assertEqual(result["generator_sha256"],FROZEN_GENERATOR_SHA)
        self.assertEqual(result["preregistered_protocol_main_commit"],PREREG_COMMIT)
        self.assertEqual(result["first_public_forecast_commit"],FIRST_COMMIT)
        self.assertEqual(result["issued_country_count"],196)
        self.assertEqual(result["origin_2025_active_countries"],32)
        self.assertEqual(result["target_year"],2027)
        self.assertEqual(result["model_expected_newconf_country_years"],2.490944756)
        self.assertEqual(result["baseline_expected_newconf_country_years"],1.397148676)
        self.assertEqual(result["target_labels_2027_resolved"],0)
        self.assertFalse(result["independent_skill_demonstrated"])
        self.assertTrue(result["statebased_2027_forecast_unchanged"])

    def test_no_altered_country_probability_or_unknown_country_can_be_issued(self):
        self.assertRaisesRegex(ValueError,"First NEWCONF-2027 canonical",
                               audit,self.forecast.replace(b'"p_model":0.003162675831',
                                                           b'"p_model":0.993162675831',1),
                               self.manifest,self.generator)
        self.assertRaisesRegex(ValueError,"First NEWCONF-2027 canonical",
                               audit,self.forecast+b" ",self.manifest,self.generator)

    def test_public_preregistered_generator_cannot_be_rewritten(self):
        with self.assertRaisesRegex(ValueError,"canonical source or generator"):
            audit(self.forecast,self.manifest,self.generator+b" ")

    def test_manifest_cannot_assert_results_or_skill(self):
        m=deepcopy(self.manifest)
        m["outcomes_resolved"]=1
        with self.assertRaisesRegex(ValueError,"Unverified outcomes"):
            audit(self.forecast,m,self.generator)
        m=deepcopy(self.manifest)
        m["demonstrated_predictive_skill"]=True
        with self.assertRaisesRegex(ValueError,"Unverified outcomes"):
            audit(self.forecast,m,self.generator)
        m=deepcopy(self.manifest)
        m["first_public_forecast_commit"]="0"*40
        with self.assertRaisesRegex(ValueError,"GitHub evidence"):
            audit(self.forecast,m,self.generator)

    def test_original_statebased_sha_and_newconf_sources_are_immutable(self):
        m=deepcopy(self.manifest)
        m["original_statebased_forecast_2027_unchanged_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"original GEO-2027"):
            audit(self.forecast,m,self.generator)
        m=deepcopy(self.manifest)
        m["sources"]["acd_26_1_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"Manifest source hashes"):
            audit(self.forecast,m,self.generator)

if __name__=="__main__":
    unittest.main()
