"""Official source-frozen name crosswalk tests. No future labels and no model fitting."""
import copy
import json
import unittest

from publish_acd2027_named_country_view import (
    make_view, canonical, MODELS, VIEW_ID,
)
from prepare_acd2027_prospective_retention import ISSUE_PATH
from prepare_geo2027_transition_alerts import FORECAST_PATH,MANIFEST_PATH


class ACD2027OfficialCountryNamesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acd=ISSUE_PATH.read_bytes()
        cls.geo=FORECAST_PATH.read_bytes()
        cls.manifest=json.loads(MANIFEST_PATH.read_text(encoding="utf8"))

    def test_all_32_names_unique_and_prospective_rows_immutable(self):
        d=make_view(self.acd,self.geo,self.manifest)
        self.assertEqual(d["view_id"],VIEW_ID)
        self.assertEqual(d["fixed_country_count"],32)
        self.assertEqual(len(d["rows"]),32)
        self.assertEqual(d["observed_target_2027_labels"],0)
        self.assertFalse(d["new_forecast_issued"])
        self.assertFalse(d["original_acd_geo_shadow_alerts_newconf_probabilities_changed"])
        self.assertEqual(d["primary_model"],"p_global_recent5")
        self.assertEqual([x["secondary_country_eb_rank"] for x in d["rows"]],
                         list(range(1,33)))
        self.assertEqual(len({x["gwno_country_id"] for x in d["rows"]}),32)
        self.assertEqual(len({x["country_name_from_original_geo_source"]
                             for x in d["rows"]}),32)
        self.assertEqual(d["rows"][0]["p_secondary_country_eb"],
                         max(x["p_secondary_country_eb"] for x in d["rows"]))
        self.assertTrue(all(x["secondary_ranking_not_prospectively_validated"]
                            for x in d["rows"]))
        self.assertEqual(canonical(d),canonical(
            make_view(self.acd,self.geo,self.manifest)))

    def test_all_model_sums_match_original_first_public_vector(self):
        d=make_view(self.acd,self.geo,self.manifest)
        origin=json.loads(self.acd)
        self.assertEqual(origin["2027_outcomes_resolved"],0)
        self.assertEqual(origin["source_data_last_year"],2025)
        self.assertEqual(d["all_three_model_expected_persistent_counts"],
                         origin["model_expected_2027_persistence"])
        for model,key in (
            ("p_global_recent5","p_primary_global_recent5"),
            ("p_country_eb","p_secondary_country_eb"),
            ("p_lag1_group","p_secondary_lag1_group"),
        ):
            self.assertAlmostEqual(
                sum(r[key] for r in d["rows"]),
                origin["model_expected_2027_persistence"][model],
                places=9,
            )

    def test_frozen_gw_country_crosswalk_rejects_modified_files(self):
        with self.assertRaisesRegex(ValueError,"probabilities modified"):
            make_view(self.acd+b" ",self.geo,self.manifest)
        with self.assertRaisesRegex(ValueError,"probabilities modified"):
            make_view(self.acd,self.geo+b" ",self.manifest)
        old=copy.deepcopy(self.manifest)
        old["forecast_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"already issued GEO2027"):
            make_view(self.acd,self.geo,old)


if __name__=="__main__":
    unittest.main()
