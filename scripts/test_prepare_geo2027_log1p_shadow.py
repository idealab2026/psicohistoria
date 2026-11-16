"""Never reissue original GEO; synthetic tests for log1p 2027 shadow time and ID."""
from __future__ import annotations

import copy
import unittest

from test_experiment_geo2027_intensity_markov_cross_release import sample
from experiment_geo2027_log1p_nested_h2 import select_and_fit
from prepare_geo2027_log1p_shadow import (
    ID, ORIGIN, SCHEMA, build, origin_internal_rows,
)


class Log1pFutureShadowTests(unittest.TestCase):
    def test_new_forecast_identity_separate_from_frozen_original(self):
        self.assertIn("LOG1P-INTENSITY-SHADOW",ID)
        self.assertEqual(ORIGIN,2025)
        self.assertEqual(SCHEMA,"idealab.psico.geo2027_log1p_intensity_shadow.v1")
        self.assertNotEqual(ID,"PSICO-GEO2027-STATEBASED25-V1")

    def test_2027_and_2026_source_observations_not_used(self):
        base=sample()
        old=origin_internal_rows(base)
        altered=copy.deepcopy(base)
        for cid,h in altered.items():
            h[2026]=1000 if cid%3 else 0
            h[2027]=10000 if cid%5 else 0
        fresh=origin_internal_rows(altered)
        self.assertEqual(old,fresh)
        self.assertEqual(max(r["target_year"] for r in old),2025)
        self.assertEqual(min(r["target_year"] for r in old),2012)
        self.assertTrue(all(r["origin_year"]+2==r["target_year"] for r in old))
        self.assertTrue(all(r["target_year"]<=2025 for r in old))

    def test_fixed_nested_regularization_uses_only_pre_target_labels(self):
        rows=origin_internal_rows(sample())
        beta,control,metadata=select_and_fit(rows,2025)
        self.assertEqual(metadata["inner_fit_targets"],[2012,2017])
        self.assertEqual(metadata["inner_select_targets"],[2018,2020])
        self.assertEqual(metadata["final_train_targets"],[2012,2025])
        self.assertGreater(metadata["final_train_n"],2000)
        self.assertIn(metadata["selected_ridge_lambda"],(5.0,20.0,80.0))
        self.assertEqual(len(beta),3)
        self.assertEqual(control[1:],(0.0,0.0))

    def test_cannot_invent_issued_shadow_from_tampered_source(self):
        with self.assertRaisesRegex(ValueError,"26.1"):
            build(b"tampered",b"{}",b"{}",b"{}")


if __name__=="__main__":
    unittest.main()
