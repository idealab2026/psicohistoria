"""Synthetic only; no observed 2027 conflict outcome is used."""
from __future__ import annotations
import copy
import hashlib
import unittest
from unittest.mock import patch

import backtest_ucdp_prio_retention_four_vintages as study
from test_diagnose_ucdp_prio_older_vintages import fake_zip


LAST={
 "20.1":2019,"21.1":2020,"22.1":2021,
 "23.1":2022,"24.1":2023,"25.1":2024,
}


def cohorts():
    active={}
    metadata={}
    for version,last in LAST.items():
        a={(str(cid),year) for cid in range(1,106)
           for year in range(1989,last)}
        stop=last%4
        a.update((str(cid),last) for cid in range(1,26+stop))
        a.update((str(cid),last) for cid in range(41,51-stop))
        active[version]=a
        metadata[version]={
            "sha256_pinned_before_run":True,
            "original_zip_sha256":hashlib.sha256(version.encode()).hexdigest(),
            "last_year":last,
        }
    return active,metadata


class ACDRetentionFourVintagesTests(unittest.TestCase):
    def test_exact_four_source_separated_two_year_folds(self):
        versions,meta=cohorts()
        result=study.diagnose(versions,meta)
        self.assertEqual(result["status"],"SHA_PINNED_EX_POST_FOUR_ORIGIN_TARGET_VINTAGES")
        self.assertEqual(result["fixed_origin_fold_years"],[2019,2020,2021,2022])
        self.assertEqual(result["target_years"],[2021,2022,2023,2024])
        self.assertEqual(len(result["folds"]),4)
        self.assertTrue(result["all_sources_sha_pinned"])
        self.assertFalse(result["historical_predictions_actually_issued_at_origin"])
        self.assertFalse(result["first_source_publication_dates_independently_notarized"])
        self.assertFalse(result["valid_independent_forecast_claim"])
        self.assertFalse(result["cross_country_independence_tested"])
        self.assertEqual(result["2027_outcomes_observed"],0)
        self.assertTrue(result["not_geo2027_statebased_25_death_threshold"])
        self.assertFalse(result["original_geo2027_shadow_newconf_predictions_modified"])
        n=sum(x["n_origin_active_countries"] for x in result["folds"])
        self.assertEqual(result["n_country_year_fold_evaluations"],n)
        for fold in result["folds"]:
            self.assertEqual(fold["target_year"],fold["origin_year"]+2)
            self.assertEqual(fold["origin_training_cutoff"][
                "latest_training_target_year"],fold["origin_year"])
            self.assertFalse(fold["origin_training_cutoff"][
                "future_labels_used_in_training"])
            self.assertEqual(set(fold["models"]),
                             {"p_global_recent5","p_country_eb","p_lag1_group"})
            self.assertEqual(len(set(x["n"] for x in fold["models"].values())),1)
            self.assertGreater(fold["n_target_persistent_country_incidence"],0)
            self.assertLess(fold["n_target_persistent_country_incidence"],
                            fold["n_origin_active_countries"])
            self.assertTrue(0<=fold["models"]["p_country_eb"]["brier"]<=1)

    def test_source_241_sha_pin_gate_and_csv_format(self):
        sample=fake_zip(2023)
        unpinned=dict(study.SOURCE_241)
        unpinned["sha256"]=None
        with patch.object(study,"SOURCE_241",unpinned):
            with self.assertRaisesRegex(ValueError,"SHA-pinned"):
                study.load_241(sample)
            records,info=study.load_241(sample,allow_probe=True)
        self.assertFalse(info["sha256_pinned_before_run"])
        self.assertGreater(len(records),1600)
        spec=dict(study.SOURCE_241)
        spec["sha256"]=hashlib.sha256(sample).hexdigest()
        with patch.object(study,"SOURCE_241",spec):
            records2,info2=study.load_241(sample)
            self.assertEqual(records,records2)
            self.assertTrue(info2["sha256_pinned_before_run"])
            with self.assertRaisesRegex(ValueError,"SHA-256"):
                study.load_241(sample+b"corrupt")
        bad=fake_zip(2023,unsafe=True)
        with patch.object(study,"SOURCE_241",unpinned):
            with self.assertRaisesRegex(ValueError,"ambiguous government"):
                study.load_241(bad,allow_probe=True)

    def test_origin_training_never_loads_two_year_future_labels(self):
        active,meta=cohorts()
        one=active["20.1"]
        preds,fit=study.predict(one,2019)
        self.assertEqual(len(preds),35)
        self.assertEqual(fit["latest_training_target_year"],2019)
        self.assertEqual(fit["origin_max_year"],2019)
        self.assertTrue(all(set(v)=={"p_global_recent5","p_country_eb","p_lag1_group"}
                            for v in preds.values()))
        self.assertGreater(fit["n_training_origin_target_country_pairs"],500)
        with self.assertRaisesRegex(ValueError,"Unapproved"):
            study.train_origin(one,2027)

    def test_no_implicit_zero_for_unmapped_or_duplicate_country_codes(self):
        versions,meta=cohorts()
        wrong=copy.deepcopy(versions)
        # A country in the origin at 2019 absent in *all* target-edition
        # history is unresolvable, not a negative prediction outcome.
        orig_cid=next(cid for cid,year in versions["20.1"] if year==2019)
        wrong["22.1"]={(cid,y) for cid,y in wrong["22.1"] if cid!=orig_cid}
        with self.assertRaisesRegex(ValueError,"no historical code presence"):
            study.compare_pair(versions["20.1"],wrong["22.1"],2019,2021)
        with self.assertRaisesRegex(ValueError,"target horizon"):
            study.compare_pair(versions["20.1"],versions["22.1"],2019,2022)

    def test_missing_frozen_source_or_mislabeled_status_blocks_report(self):
        versions,meta=cohorts()
        altered=copy.deepcopy(meta)
        altered["24.1"]["sha256_pinned_before_run"]=False
        with self.assertRaisesRegex(ValueError,"unpinned"):
            study.diagnose(versions,altered)
        exploratory=study.diagnose(versions,altered,probe=True)
        self.assertEqual(exploratory["status"],"UNPINNED_EXPLORATORY_PROBE_NOT_CERTIFIED")
        changed=copy.deepcopy(versions)
        changed.pop("21.1")
        with self.assertRaisesRegex(ValueError,"All independent"):
            study.diagnose(changed,meta)
        changed=copy.deepcopy(meta)
        changed["20.1"]["last_year"]=2020
        with self.assertRaisesRegex(ValueError,"Wrong historical cutoff"):
            study.diagnose(versions,changed)


if __name__=="__main__":
    unittest.main()
