"""Prospective GEO2028 horizon-three specification before issuing outcomes."""
import copy
import math
import unittest

import forecast_2027_statebased as original
import prepare_geo2028_three_year as prep
from test_forecast_2027_statebased import toy


def old_issued_from_toy():
    records,names=toy()
    rows,_=original.estimate_from_history(records,names)
    issued={
        "forecast_id":original.PROTOCOL_ID,
        "target":{"year":2027},
        "source":{"sha256":prep.SOURCE_SHA,"data_last_year":2025},
        "countries":rows,
    }
    return records,names,issued


class GEO2028ThreeYearTests(unittest.TestCase):
    def test_three_step_composition_binary_and_not_two_step(self):
        q=(.1,.8)
        a=prep.nsteps(0,q,2)
        b=prep.nsteps(0,q,3)
        self.assertAlmostEqual(a,(1-.1)*.1+.1*.8,places=12)
        self.assertAlmostEqual(b,.1+(.8-.1)*a,places=12)
        self.assertNotAlmostEqual(a,b)
        self.assertAlmostEqual(prep.nsteps(1,q,3),.1+(.8-.1)*
            (.1+(.8-.1)*.8),places=12)
        for args in ((0,q,1),(0,q,4),(2,q,3),(True,q,3),
                     (0,(float("nan"),.5),3),(0,(1.,.5),3)):
            with self.assertRaises(ValueError):
                prep.nsteps(*args)

    def test_all_original_2027_probabilities_match_before_projection(self):
        records,names,issued=old_issued_from_toy()
        rows,summary=prep.build_from_records(records,names,issued)
        self.assertEqual(len(rows),196)
        self.assertEqual(len({x["country_id"] for x in rows}),196)
        self.assertEqual(rows[0]["country_id"],1)
        self.assertEqual(rows[-1]["country_id"],196)
        self.assertEqual(summary["cohort_n"],196)
        orig={x["country_id"]:x for x in issued["countries"]}
        for x in rows:
            self.assertEqual(
                x["p_issued_geo2027_2step_for_temporal_comparison_only"],
                orig[x["country_id"]]["p_model"])
            self.assertEqual(x["p_baseline_global_5y"],
                             orig[x["country_id"]]["p_baseline_global_5y"])
            self.assertTrue(0<x["p_model"]<1)
        self.assertGreater(len(set(x["p_model"] for x in rows)),2)

    def test_retired_historical_countries_can_exist_outside_196_riskset(self):
        records,names,_=old_issued_from_toy()
        records[997]={year:int(year%2==0) for year in range(1989,1999)}
        names[997]="Retired historical government territory"
        original_rows,_=original.estimate_from_history(records,names)
        prior={
            "forecast_id":original.PROTOCOL_ID,
            "target":{"year":2027},
            "source":{"sha256":prep.SOURCE_SHA,"data_last_year":2025},
            "countries":original_rows,
        }
        rows,_=prep.build_from_records(records,names,prior)
        self.assertEqual(len(rows),196)
        self.assertNotIn(997,{row["country_id"] for row in rows})

    def test_rejects_retroactively_rewritten_original_geo2027(self):
        records,names,issued=old_issued_from_toy()
        tampered=copy.deepcopy(issued)
        tampered["countries"][0]["p_model"]+=.00001
        with self.assertRaisesRegex(ValueError,"not reproducible"):
            prep.build_from_records(records,names,tampered)
        tampered=copy.deepcopy(issued)
        tampered["source"]["sha256"]="wrong"
        with self.assertRaisesRegex(ValueError,"not authenticated"):
            prep.build_from_records(records,names,tampered)
        tampered=copy.deepcopy(issued)
        tampered["target"]["year"]=2028
        with self.assertRaisesRegex(ValueError,"not authenticated"):
            prep.build_from_records(records,names,tampered)

    def test_rejects_any_2026_2027_or_2028_training_records(self):
        records,names,issued=old_issued_from_toy()
        for year in (2026,2027,2028):
            changed=copy.deepcopy(records)
            changed[1][year]=1
            with self.assertRaisesRegex(ValueError,"Future"):
                prep.build_from_records(changed,names,issued)
        with self.assertRaisesRegex(ValueError,"source SHA mismatch"):
            prep.build_forecast(b"fake later official source",issued)

    def test_frozen_candidate_no_2027_scoring_or_horizon_misreport(self):
        records,names,issued=old_issued_from_toy()
        rows,summary=prep.build_from_records(records,names,issued)
        doc={
            "schema":prep.SCHEMA,"forecast_id":prep.PROTOCOL_ID,
            "state":"CANDIDATE_BEFORE_FIRST_PUBLIC_2028_ISSUE",
            "target":{"year":2028},
            "origin":{"year":2025,"official_data_last_year":2025,
                      "official_sha256":prep.SOURCE_SHA},
            "protocol":{
                "horizon_years":3,
                "not_independent_rolling_origin_two_year_replication":True,
            },
            "first_issue_provenance":{"original_GEO2027_SHA256":prep.EXPECTED_ORIGIN},
            "2028_outcomes_resolved":0,
            "prospective_predictive_skill_demonstrated":False,
            "countries":rows,"n_countries":196,
            "model_expected_2028_active_countries":{
                k:round(sum(x[k] for x in rows),12)
                for k in ("p_model","p_global_markov_3step","p_baseline_global_5y")},
        }
        self.assertTrue(prep.validate_forecast(doc))
        for path,value in (
            (("target","year"),2027),
            (("origin","official_data_last_year"),2026),
            (("protocol","horizon_years"),2),
            (("protocol","not_independent_rolling_origin_two_year_replication"),False),
            (("first_issue_provenance","original_GEO2027_SHA256"),"tampered"),
            (("2028_outcomes_resolved",),1),
            (("prospective_predictive_skill_demonstrated",),True),
        ):
            t=copy.deepcopy(doc)
            pointer=t
            for key in path[:-1]:
                pointer=pointer[key]
            pointer[path[-1]]=value
            with self.assertRaisesRegex(ValueError,"Unsafe"):
                prep.validate_forecast(t)
        t=copy.deepcopy(doc)
        t["countries"][0]["p_model"]=.0
        with self.assertRaisesRegex(ValueError,"probability"):
            prep.validate_forecast(t)
        t=copy.deepcopy(doc)
        t["model_expected_2028_active_countries"]["p_model"]+=1
        with self.assertRaisesRegex(ValueError,"not consistent"):
            prep.validate_forecast(t)
        t=copy.deepcopy(doc)
        t["countries"][0]["country_id"]=t["countries"][1]["country_id"]
        with self.assertRaisesRegex(ValueError,"identifiers"):
            prep.validate_forecast(t)
        t=copy.deepcopy(doc)
        t["countries"].pop()
        with self.assertRaisesRegex(ValueError,"risk cohort"):
            prep.validate_forecast(t)

    def test_2028_issue_is_different_question_not_independent_2027_replica(self):
        self.assertNotEqual(prep.PROTOCOL_ID,original.PROTOCOL_ID)
        self.assertEqual(prep.TARGET-prep.ORIGIN,3)
        self.assertNotEqual(original.TARGET_YEAR-original.CUTOFF_YEAR,3)
        self.assertEqual(prep.SOURCE_SHA,original.PINNED_SOURCE_SHA256)
        self.assertEqual(prep.EXPECTED_ORIGIN,
                         "5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5")


if __name__=="__main__":
    unittest.main()
