"""Zero-future-data tests for GEO2028 196-country official scoring contract."""
import copy
from datetime import date
import hashlib
import json
from pathlib import Path
import unittest

import evaluate_geo2028_first_complete_official as s


def fake_rows():
    issued,_=s.load_immutable_issue()
    return issued


def candidate_provenance():
    return {
        "first_complete_release_independently_certified":False,
        "url_hash_date_are_not_independent_source_attestation":True,
        "release_date_operator_supplied":"2029-09-01",
    }


class GEO2028OfficialGateTests(unittest.TestCase):
    def test_authenticate_complete_original_issued_probabilities(self):
        doc,manifest=s.load_immutable_issue()
        self.assertEqual(doc["forecast_id"],"PSICO-GEO2028-STATEBASED25-H3-ORIGIN2025-V1")
        self.assertEqual(doc["target"]["year"],2028)
        self.assertEqual(doc["origin"]["official_data_last_year"],2025)
        self.assertEqual(doc["protocol"]["horizon_years"],3)
        self.assertEqual(len(doc["countries"]),196)
        self.assertEqual(manifest["forecast_sha256"],s.first_issue.ISSUE_SHA)
        self.assertEqual(s.sha256(
            (s.ROOT/s.first_issue.SOURCE_PATH).read_bytes()),
            s.first_issue.ISSUE_SHA)
        self.assertFalse(doc["prospective_predictive_skill_demonstrated"])

    def test_source_gate_rejects_pre_2029_fake_or_future_dates_and_domain(self):
        url="https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-291-csv.zip"
        sha="a"*64
        valid=s.validate_candidate_source(
            url,sha,"2029-08-01",as_of=date(2030,1,1)
        )
        self.assertFalse(valid["first_complete_release_independently_certified"])
        self.assertEqual(valid["claimed_release_version_from_filename"],"291")
        self.assertTrue(valid["url_hash_date_are_not_independent_source_attestation"])
        for wrong in (
            "http://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-291-csv.zip",
            "https://ucdp.uu.se.evil.test/downloads/organizedviolencecy/organizedviolencecy-291-csv.zip",
            "https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-261-csv.zip",
            "https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-281-csv.zip",
            "https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-291-csv.zip?flag=1",
            "https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-291-csv.zip#fragment",
            "https://ucdp.uu.se/downloads/onset/organizedviolencecy-291-csv.zip",
        ):
            with self.subTest(url=wrong):
                with self.assertRaisesRegex(ValueError,"official"):
                    s.validate_candidate_source(wrong,sha,"2029-08-01",
                                                as_of=date(2030,1,1))
        for when,asof in (
            ("2026-11-15",date(2030,1,1)),
            ("2028-12-31",date(2030,1,1)),
            ("2029-08-01",date(2026,11,15)),
            ("2035-01-01",date(2030,1,1)),
        ):
            with self.assertRaisesRegex(ValueError,"before 2029 or in the future"):
                s.validate_candidate_source(url,sha,when,as_of=asof)
        for incorrect in ("x"*64,"A"*64,"bad"):
            with self.assertRaisesRegex(ValueError,"SHA-256"):
                s.validate_candidate_source(url,incorrect,"2029-08-01",
                                            as_of=date(2030,1,1))

    def test_parser_exact_2028_binary_year_and_no_implicit_zero(self):
        text=("country_id,year,sb_total_deaths_best\n"
              "2,2025,140\n2,2028,24\n20,2028,25\n40,2028,0\n"
              "41,2027,300\n")
        self.assertEqual(s.parse_target_2028_csv(text),{2:0,20:1,40:0})
        other=("country_id_cy,year_cy,sb_total_deaths_best_cy\n"
               "2,2028,25\n20,2028,24\n")
        self.assertEqual(s.parse_target_2028_csv(other),{2:1,20:0})
        for bad in (
            text+"2,2028,30\n",
            "country_id,year,sb_total_deaths_best\n2,2027,30\n",
            "country_id,year,sb_total_deaths_best\n2,2028,\n",
            "country_id,year,sb_total_deaths_best\n2,2028,-1\n",
            "country_id,year,sb_total_deaths_best\n2,2028,24.5\n",
            "country_id,year,sb_total_deaths_best\n2,2028,unknown\n",
            "country_id,year,sb_total_deaths_best\n2,2028,0\n2,2028,24\n",
            "country_id,year,sb_total_deaths_best\n2,2028,25,too-many\n",
            "country_id,year,sb_total_deaths_best,sb_total_deaths_best\n2,2028,25,0\n",
            "country_id,year,sb_total_deaths_best,country_id_cy\n2,2028,25,2\n",
        ):
            with self.subTest(csv=bad[:65]):
                with self.assertRaises(ValueError):
                    s.parse_target_2028_csv(bad)

    def test_no_scores_before_all_196_explicit_outcomes(self):
        doc=fake_rows()
        ids=[r["country_id"] for r in doc["countries"]]
        for count in (0,1,186,187,195):
            outcomes={cid:0 for cid in ids[:count]}
            results=s.score_eligible_candidate(doc,outcomes,candidate_provenance())
            self.assertEqual(results["resolved_country_outcomes"],count)
            self.assertEqual(results["unresolved_country_outcomes"],196-count)
            self.assertIsNone(results["scores"])
            self.assertIsNone(results["observed_2028_event_count"])
            self.assertIsNone(results["calibration_by_origin_state_and_probability_bin"])
            self.assertFalse(results["first_complete_release_independently_attested"])
            self.assertFalse(results["prospective_skill_demonstrated"])
            self.assertFalse(results["country_outcomes_assumed_iid"])

    def test_exact_score_and_brier_delta_only_at_full_196_coverage(self):
        doc=fake_rows()
        ids=[r["country_id"] for r in doc["countries"]]
        outcomes={cid:int(i%9==0) for i,cid in enumerate(ids)}
        outcomes[1999]=1  # extra unissued country does not enter Brier
        result=s.score_eligible_candidate(doc,outcomes,candidate_provenance())
        self.assertEqual(result["status"],"COMPLETE_196_SOURCE_CANDIDATE_UNCERTIFIED")
        self.assertEqual(result["resolved_country_outcomes"],196)
        self.assertEqual(result["extra_future_source_gwno_ignored"],1)
        self.assertEqual(result["observed_2028_event_count"],sum(outcomes[cid] for cid in ids))
        self.assertEqual(result["2027_outcomes_used"],0)
        self.assertIsNone(result.get("iid_bootstrap_confidence_interval"))
        self.assertFalse(result["iid_bootstrap_or_confidence_intervals_present"])
        expected=sum((r["p_model"]-outcomes[r["country_id"]])**2
                     for r in doc["countries"])/196
        self.assertAlmostEqual(result["scores"]["p_model"]["brier"],expected)
        self.assertAlmostEqual(result["paired_brier_delta_model_minus_global5y"],
                               expected-result["scores"]["p_baseline_global_5y"]["brier"])
        self.assertAlmostEqual(result["paired_brier_delta_model_minus_global_markov"],
                               expected-result["scores"]["p_global_markov_3step"]["brier"])
        self.assertEqual(sum(x["n"] for x in result[
            "calibration_by_origin_state_and_probability_bin"]["five_fixed_probability_bins"]),196)
        self.assertEqual(sum(x["n"] for x in result[
            "calibration_by_origin_state_and_probability_bin"]["by_origin_2025_state"].values()),196)
        self.assertFalse(result["automatic_primary_model_change_authorized"])
        self.assertFalse(result["prospective_skill_demonstrated"])

    def test_wrong_origin_horizon_counters_future_labels_or_self_attestation(self):
        doc=fake_rows()
        ids=[r["country_id"] for r in doc["countries"]]
        all_out={cid:0 for cid in ids}
        for location,value in (
            ("target",2027),
            ("origin",2026),
            ("horizon",2),
            ("resolved",1),
            ("skill",True),
        ):
            d=copy.deepcopy(doc)
            if location=="target":d["target"]["year"]=value
            if location=="origin":d["origin"]["year"]=value
            if location=="horizon":d["protocol"]["horizon_years"]=value
            if location=="resolved":d["2028_outcomes_resolved"]=value
            if location=="skill":d["prospective_predictive_skill_demonstrated"]=value
            with self.subTest(location=location):
                with self.assertRaisesRegex(ValueError,"altered prospective"):
                    s.score_eligible_candidate(d,all_out,candidate_provenance())
        for flags in (
            {"first_complete_release_independently_certified":True},
            {"url_hash_date_are_not_independent_source_attestation":False},
        ):
            p={**candidate_provenance(),**flags}
            with self.assertRaisesRegex(ValueError,"No self-certification"):
                s.score_eligible_candidate(doc,all_out,p)
        for weird in (
            {ids[0]:None},
            {ids[0]:-1},
            {ids[0]:True},
            {ids[0]:float("nan")},
        ):
            with self.assertRaisesRegex(ValueError,"Invalid future"):
                s.score_eligible_candidate(doc,weird,candidate_provenance())

    def test_model_probabilities_not_changed_by_candidate_scores(self):
        d=fake_rows()
        first=d["countries"][0]["p_model"]
        outcomes={r["country_id"]:int(r["last_observed_state_2025"])
                  for r in d["countries"]}
        s.score_eligible_candidate(d,outcomes,candidate_provenance())
        self.assertEqual(d["countries"][0]["p_model"],first)
        self.assertEqual(d["2028_outcomes_resolved"],0)
        self.assertEqual(d["prospective_predictive_skill_demonstrated"],False)


if __name__=="__main__":
    unittest.main()
