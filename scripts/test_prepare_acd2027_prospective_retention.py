"""Adversarial synthetic-only tests of unissued 2027 intrastate ACD candidate."""
import csv
import io
import json
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED

import prepare_acd2027_prospective_retention as s
from backtest_ucdp_prio_retention_four_vintages import (
    PRIOR_STRENGTH, RECENT_ORIGIN_YEARS,
)


def synthetic_active():
    return {(str(cid),year)
            for cid in range(1,106)
            for year in range(2000,2026)
            if year<2025 or cid<=40}


def fake_source(*,future=False,duplicate=False):
    buff=io.StringIO()
    fieldnames=["conflict_id","year","type_of_conflict","gwno_a","gwno_loc"]
    writer=csv.DictWriter(buff,fieldnames=fieldnames)
    writer.writeheader()
    for cid,year in sorted(synthetic_active()):
        writer.writerow({"conflict_id":str(10000+int(cid)),
            "year":str(year),"type_of_conflict":"3",
            "gwno_a":cid,"gwno_loc":cid})
    if duplicate:
        writer.writerow({"conflict_id":"10001","year":"2025",
                         "type_of_conflict":"3","gwno_a":"1","gwno_loc":"1"})
    if future:
        writer.writerow({"conflict_id":"10001","year":"2027",
                         "type_of_conflict":"3","gwno_a":"1","gwno_loc":"1"})
    raw=io.BytesIO()
    with ZipFile(raw,"w",ZIP_DEFLATED) as z:
        z.writestr("official-format-test.csv",buff.getvalue())
    return raw.getvalue()


class GenuineACDRetentionIssueTests(unittest.TestCase):
    def test_historical_country_risk_set_and_probability_frozen_recipe(self):
        source={"pinned":True,"last_observed_year":2025,
                "no_actual_2027_outcomes":True,"source_zip_sha256":"a"*64}
        doc=s.forecast(synthetic_active(),source)
        self.assertEqual(doc["forecast_id"],s.FORECAST_ID)
        self.assertEqual(doc["origin_year"],2025)
        self.assertEqual(doc["target_year"],2027)
        self.assertEqual(doc["n_origin_active_countries"],40)
        self.assertEqual(len(doc["countries"]),40)
        self.assertEqual(doc["primary_model"],"p_global_recent5")
        self.assertEqual(doc["secondary_models"],["p_country_eb","p_lag1_group"])
        self.assertEqual(doc["training_target_latest_year"],2025)
        self.assertEqual(doc["training_origin_latest_year"],2023)
        self.assertEqual(doc["training_recent_origin_years"],[2019,2020,2021,2022,2023])
        self.assertEqual(doc["2027_outcomes_resolved"],0)
        self.assertFalse(doc["prospective_skill_demonstrated"])
        self.assertFalse(doc["actual_2027_outcomes_used"])
        self.assertTrue(doc["historical_model_selection_exploratory_post_hoc"])
        self.assertTrue(doc["forecast_not_for_full_196_country_universe"])
        self.assertEqual([v["country_id"] for v in doc["countries"]],list(range(1,41)))
        self.assertTrue(all(0<v["p_global_recent5"]<1 and
                            0<v["p_country_eb"]<1 and
                            0<v["p_lag1_group"]<1
                            for v in doc["countries"]))
        self.assertEqual(s.canonical(doc),s.canonical(s.forecast(synthetic_active(),source)))
        self.assertEqual(json.loads(s.canonical(doc)),doc)

    def test_source_sha_must_be_frozen_before_factual_forecast(self):
        raw=fake_source()
        with self.assertRaisesRegex(ValueError,"not SHA-pinned"):
            s.official_source(raw)
        active,meta=s.official_source(raw,probe=True)
        self.assertFalse(meta["pinned"])
        self.assertEqual(meta["intrastate_2025_risk_countries"],40)
        self.assertEqual(len(active),len(synthetic_active()))
        with self.assertRaisesRegex(ValueError,"Unpinned"):
            s.forecast(active,meta)
        import hashlib
        with patch.object(s,"SOURCE_SHA256",hashlib.sha256(raw).hexdigest()):
            active2,meta2=s.official_source(raw)
            self.assertTrue(meta2["pinned"])
            self.assertEqual(active,active2)
            with self.assertRaisesRegex(ValueError,"hash changed"):
                s.official_source(raw+b"corrupted")

    def test_no_future_outcomes_or_duplicate_conflict_years(self):
        with self.assertRaisesRegex(ValueError,"2026/27"):
            s.official_source(fake_source(future=True),probe=True)
        with self.assertRaisesRegex(ValueError,"Duplicated"):
            s.official_source(fake_source(duplicate=True),probe=True)
        source={"pinned":True,"last_observed_year":2025,
                "no_actual_2027_outcomes":True,"source_zip_sha256":"a"*64}
        future=set(synthetic_active())
        future.add(("1",2027))
        with self.assertRaisesRegex(ValueError,"Future outcomes"):
            s.forecast(future,source)
        corrupted=dict(source,no_actual_2027_outcomes=False)
        with self.assertRaisesRegex(ValueError,"Unpinned"):
            s.forecast(synthetic_active(),corrupted)

    def test_primary_is_global_recent_rate_not_selected_from_favorable_fold(self):
        d=s.forecast(synthetic_active(),
            {"pinned":True,"last_observed_year":2025,
             "no_actual_2027_outcomes":True,"source_zip_sha256":"a"*64})
        p={v["p_global_recent5"] for v in d["countries"]}
        self.assertEqual(len(p),1)
        self.assertAlmostEqual(next(iter(p)),d["model_expected_2027_persistence"][
            "p_global_recent5"]/40)
        self.assertGreater(d["training_n_country_years"],500)
        self.assertGreater(d["training_n_persisted"],0)
        self.assertEqual(PRIOR_STRENGTH,12)
        self.assertEqual(RECENT_ORIGIN_YEARS,5)


if __name__=="__main__":
    unittest.main()
