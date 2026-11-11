import unittest
import json
from copy import deepcopy
from forecast_2027_newconf import (
    calculate,build,validate,ISSUE_ID,SCHEMA,N,HORIZON
)
from probe_newconf_2027_acd261 import activity_2025

def fixture():
    panel={}
    active=set()
    for idx in range(1,197):
        cid=str(idx)
        h={}
        for y in range(1946,2025):
            positive=int(y%5==0 and idx%19==0)
            h[y]={"newconf":positive,"onset2":0,
                  "newconf_episodes":positive,"onset2_episodes":0,
                  "multiple_episode_rows":1}
            if y<=2024 and (idx%7==0 or idx%13==0 and y%2==0):
                active.add((cid,y))
        panel[cid]=h
    active2025=set(str(i) for i in range(1,33))
    return panel,active,active2025

class ProspectiveNewconf2027Tests(unittest.TestCase):
    def test_source_frozen_deterministic_cohort_and_all_probabilities(self):
        panel,act,origin=fixture()
        doc=build(b"model-code-canonical",panel,act,origin)
        self.assertTrue(validate(doc))
        self.assertEqual(doc["forecast_id"],ISSUE_ID)
        self.assertEqual(doc["schema"],SCHEMA)
        self.assertEqual(doc["target"]["year"],2027)
        self.assertEqual(doc["source"]["training_newconf_last_year"],2024)
        self.assertEqual(doc["source"]["origin_conflict_activity_year"],2025)
        self.assertEqual(doc["protocol"]["calendar_horizon_years"],HORIZON)
        self.assertEqual(doc["training_summary"]["countries"],N)
        self.assertEqual(doc["training_summary"]["active_in_origin_2025"],32)
        self.assertEqual(len(doc["countries"]),196)
        self.assertEqual(sum(x["active_intrastate_2025"] for x in doc["countries"]),32)
        self.assertEqual(doc,build(b"model-code-canonical",panel,act,origin))
        self.assertTrue(all(0<x["p_model"]<1 for x in doc["countries"]))
        self.assertEqual(doc["protocol"]["skill_demonstrated"],False)
        self.assertEqual(doc["provenance"]["statebased_geo2027_separate_and_unchanged"],True)
        self.assertFalse(doc["source"]["2026_2027_labels_observed"] if "2026_2027_labels_observed" in doc["source"] else doc["source"]["newconf_2027_outcome_observed"])
        self.assertEqual(doc["provenance"]["forecasts_issued_before_current"],0)

    def test_no_future_year_can_be_fitted_even_when_present_in_panel(self):
        p,a,o=fixture()
        p["1"][2025]={"newconf":1}
        with self.assertRaisesRegex(ValueError,"Future newconf training labels"):
            calculate(p,a,o)
        p,a,o=fixture()
        a.add(("1",2025))
        with self.assertRaisesRegex(ValueError,"Only frozen ACD 25.1"):
            calculate(p,a,o)

    def test_origin_2025_only_changes_conditional_group_not_training(self):
        p,a,o=fixture()
        c1,train1=calculate(p,a,o)
        o.remove("1");o.add("40")
        c2,train2=calculate(p,a,o)
        self.assertEqual(train1["training_country_years"],train2["training_country_years"])
        self.assertEqual(train1["global_full_probability"],train2["global_full_probability"])
        self.assertNotEqual(c1[0]["p_model"],c2[0]["p_model"])
        self.assertEqual(c1[0]["p_country_eb"],c2[0]["p_country_eb"])
        self.assertEqual(c1[0]["p_baseline_global_5y"],c2[0]["p_baseline_global_5y"])

    def test_block_missing_country_and_bad_issue_shape(self):
        p,a,o=fixture()
        del p["196"][2024]
        with self.assertRaisesRegex(ValueError,"Wrong fixed official"):
            calculate(p,a,o)
        p,a,o=fixture()
        d=build(b"script",p,a,o)
        d["countries"][0]["p_model"]=1.2
        with self.assertRaisesRegex(ValueError,"Predictions not valid probabilities"):
            validate(d)
        d=build(b"script",p,a,o)
        d["protocol"]["skill_demonstrated"]=True
        with self.assertRaisesRegex(ValueError,"Must not assert skill"):
            validate(d)
        d=build(b"script",p,a,o)
        d["target"]["year"]=2026
        with self.assertRaisesRegex(ValueError,"chronology invalid"):
            validate(d)

    def test_official_261_hash_cannot_be_skipped(self):
        with self.assertRaisesRegex(ValueError,"source hash changed"):
            activity_2025(lambda url,limit:b"untrusted data")

if __name__=="__main__":
    unittest.main()
