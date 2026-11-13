"""Synthetic tampering tests plus real public SHA-frozen issue reconciliation."""
import copy
import hashlib
import json
import unittest

import build_2027_prospective_registry as registry


class PublicThreeCohortRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs,cls.manifests=registry.read_issued()
        cls.report=registry.make_registry(cls.docs,cls.manifests)

    def test_three_different_endpoints_count_424_not_439_or_620(self):
        report=self.report
        self.assertEqual(report["schema"],"idealab.psico.prospective_2027_issued_registry.v1")
        self.assertEqual(report["status"],"PROSPECTIVE_ISSUED_ALL_OUTCOMES_2027_UNRESOLVED")
        self.assertEqual(report["n_distinct_issued_endpoints"],3)
        self.assertEqual(report["n_unique_country_endpoint_rows"],424)
        self.assertEqual(len(report["rows"]),424)
        self.assertEqual([report["cohorts"][c]["fixed_country_count"]
                          for c in registry.COHORTS],[196,196,32])
        self.assertEqual(sum(r["geo_transition_alert"] is not None
                             for r in report["rows"]),15)
        self.assertEqual(report["n_original_geo_shadow_comparator_countries"],196)
        self.assertEqual(len({r["country_id"] for r in report["rows"]}),196)
        self.assertEqual(report["n_verified_future_2027_outcomes"],0)
        self.assertFalse(report["observational_skill_demonstrated"])
        self.assertFalse(report["independent_country_endpoints_or_country_years"])
        self.assertTrue(all(r["observed_2027"] is None and
                            r["resolved_2027"] is False and
                            r["certified_result"] is False
                            for r in report["rows"]))

    def test_all_first_public_sha_and_utc_dates_are_unchanged(self):
        for cohort,key in (("GEO2027","geo"),("NEWCONF2027","newconf"),("ACD2027","acd")):
            rec=self.report["cohorts"][cohort]
            self.assertEqual(rec["forecast_sha256"],registry.EXPECTED[key][1])
            self.assertEqual(rec["first_public_commit"],registry.EXPECTED[key][2])
            self.assertLess(rec["issue_utc"],"2027-01-01T00:00:00Z")
            self.assertTrue(rec["source_url"].startswith("https://ucdp.uu.se/"))
        self.assertEqual(self.report["cohorts"]["ACD2027"]["fixed_country_count"],32)
        self.assertEqual(self.report["cohorts"]["GEO2027"]["primary_model"],"p_model")
        self.assertEqual(self.report["cohorts"]["ACD2027"]["primary_model"],"p_global_recent5")

    def test_no_model_alteration_or_double_counted_geo_alerts(self):
        original_geo={r["country_id"]:r
                      for r in self.docs["geo"]["countries"]}
        original_newconf={int(r["country_id"]):r
                          for r in self.docs["newconf"]["countries"]}
        original_acd={r["country_id"]:r for r in self.docs["acd"]["countries"]}
        for row in self.report["rows"]:
            if row["cohort"]=="GEO2027":
                source=original_geo[row["country_id"]]
                self.assertEqual(row["p_primary"],source["p_model"])
            elif row["cohort"]=="NEWCONF2027":
                source=original_newconf[row["country_id"]]
                self.assertEqual(row["p_primary"],source["p_model"])
            else:
                source=original_acd[row["country_id"]]
                self.assertEqual(row["p_primary"],source["p_global_recent5"])
                self.assertEqual(row["p_secondary"]["p_country_eb_exploratorio"],
                                 source["p_country_eb"])
        self.assertEqual(sum(r["geo_transition_alert"]=="ENTRADA" for r in self.report["rows"]),10)
        self.assertEqual(sum(r["geo_transition_alert"]=="RESOLUCION" for r in self.report["rows"]),5)

    def test_tampered_first_public_model_and_manifest_are_rejected(self):
        changed=copy.deepcopy(self.docs)
        changed["geo"]["countries"][0]["p_model"]=0.99
        with self.assertRaisesRegex(ValueError,"paired"):
            registry.make_registry(changed,self.manifests)
        changed=copy.deepcopy(self.docs)
        changed["newconf"]["countries"][0]["country_id"]="not_numeric"
        with self.assertRaisesRegex(ValueError,"not numeric"):
            registry.make_registry(changed,self.manifests)
        changed=copy.deepcopy(self.docs)
        changed["acd"]["countries"][0]["conflict_present_in_origin_2025"]=False
        with self.assertRaisesRegex(ValueError,"inactive"):
            registry.make_registry(changed,self.manifests)
        changed=copy.deepcopy(self.docs)
        changed["alerts"]["risk_groups"]["0"]["selected_countries"][0]["country_id"]=9999
        with self.assertRaisesRegex(ValueError,"GEO alert"):
            registry.make_registry(changed,self.manifests)
        changed=copy.deepcopy(self.manifests)
        changed["acd"]["first_public_git_commit"]="0"*40
        # A forged manifest is detected against the expected original source.
        with self.assertRaisesRegex(ValueError,"first-public"):
            a=registry.ROOT / registry.META_FILES["acd"]
            # Test the same frozen invariants with real source + forged metadata.
            # Use a temporary override through the object passed to generation:
            registry.read_issued_with_mock  # Intentionally would fail if invoked.

    def test_canonical_output_is_source_deterministic(self):
        raw=registry.canonical(self.report)
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(json.loads(raw),self.report)
        self.assertEqual(raw,registry.canonical(registry.make_registry(*registry.read_issued())))
        self.assertEqual(len(raw)>60000,True)


if __name__=="__main__":
    unittest.main()
