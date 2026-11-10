import unittest
from pathlib import Path
from evaluate_2027_official import (
    YEAR,COHORT,MIN_RESOLVED,FORECAST_SHA,load_frozen_issue,
    validate_future_source,parse_2027_outcomes,summary_scores,
    bootstrap_interval,evaluate
)

ROOT=Path(__file__).resolve().parents[1]

def sample():
    rows=[]
    for i in range(1,COHORT+1):
        rows.append({
            "country_id":i,"country":f"Test country {i}",
            "p_model":0.1 if i%2 else 0.7,
            "p_baseline_global_5y":0.2,
            "p_global_markov":0.3,
            "last_observed_state_2025":i%2
        })
    return {
        "forecast_id":"PSICO-GEO2027-STATEBASED25-V1",
        "target":{"year":2027},
        "countries":rows,
    }

class GenuineOnlyResolution(unittest.TestCase):
    def test_read_frozen_public_document_exact_sha(self):
        doc,proof=load_frozen_issue(
            ROOT/"data/forecast-2027-ucdp261.json",
            ROOT/"data/forecast-2027-manifest.json")
        self.assertEqual(doc["forecast_id"],proof["forecast_id"])
        self.assertEqual(len(doc["countries"]),196)
        self.assertEqual(proof["forecast_sha256"],FORECAST_SHA)
        self.assertFalse(proof["demonstrated_predictive_skill"])

    def test_rejects_fake_official_release_or_2027_publication_dates(self):
        url="https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-281-csv.zip"
        sha="a"*64
        self.assertTrue(validate_future_source(url,sha,"2028-10-01"))
        for invalid in (
            "https://example.com/downloads/organizedviolencecy/organizedviolencecy-281-csv.zip",
            "https://ucdp.uu.se.evil.com/downloads/organizedviolencecy/organizedviolencecy-281-csv.zip",
            "http://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-281-csv.zip"
        ):
            with self.assertRaisesRegex(ValueError,"official"):
                validate_future_source(invalid,sha,"2028-10-01")
        with self.assertRaisesRegex(ValueError,"cannot have been published"):
            validate_future_source(url,sha,"2027-12-30")
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            validate_future_source(url,"bad","2028-10-01")

    def test_future_country_year_labels_are_distinct_and_missing_not_zero(self):
        csv="country_id,year,sb_total_deaths_best\n"+(
            "101,2025,100\n101,2027,24\n102,2027,25\n103,2027,0\n")
        out=parse_2027_outcomes(csv)
        self.assertEqual(out,{101:0,102:1,103:0})
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            parse_2027_outcomes(csv+"101,2027,0\n")
        with self.assertRaisesRegex(ValueError,"does not contain target"):
            parse_2027_outcomes("country_id,year,sb_total_deaths_best\n101,2026,30\n")

    def test_do_not_publish_scores_if_more_than_5pct_missing(self):
        f=sample()
        outcomes={i:0 for i in range(1,MIN_RESOLVED)}
        r=evaluate(f,outcomes,{"url":"synthetic-offline-test"})
        self.assertEqual(r["issued"],196)
        self.assertEqual(r["resolved"],MIN_RESOLVED-1)
        self.assertEqual(r["unresolved"],196-(MIN_RESOLVED-1))
        self.assertIsNone(r["scores"])
        self.assertIsNone(r["interval_delta_brier_model_minus_baseline"])
        self.assertFalse(r["coverage_95pct_gate_passed"])
        self.assertFalse(r["prospective_skill_independently_verified"])
        self.assertEqual(r["status"],"SELF_REPORTED_OFFICIAL_SOURCE_NEEDS_FIRST_RELEASE_ATTESTATION")

    def test_scoring_uses_exactly_frozen_probabilities_not_retraining(self):
        f=sample()
        outcomes={i:int(i%11==0) for i in range(1,197)}
        r=evaluate(f,outcomes,{"url":"synthetic-offline-test"})
        self.assertEqual(r["resolved"],196)
        self.assertEqual(r["events"],sum(outcomes.values()))
        self.assertTrue(r["coverage_95pct_gate_passed"])
        self.assertEqual(len(r["calibration_bins"]),5)
        self.assertEqual(sum(x["n"] for x in r["calibration_bins"]),196)
        self.assertIsNotNone(r["scores"]["model"]["logloss"])
        self.assertLessEqual(r["interval_delta_brier_model_minus_baseline"][0],
                             r["interval_delta_brier_model_minus_baseline"][1])
        self.assertFalse(r["prospective_skill_independently_verified"])
        # A future country's outcome is never treated as missing/negative in the issue.
        self.assertEqual(f["countries"][0]["p_model"],0.1)

    def test_metric_and_resampling_are_deterministic(self):
        rows=[{"country_id":1,"p_model":0.2,"p_baseline_global_5y":0.3,
               "p_global_markov":0.4,"outcome":0},
              {"country_id":2,"p_model":0.8,"p_baseline_global_5y":0.3,
               "p_global_markov":0.4,"outcome":1},
              {"country_id":3,"p_model":0.6,"p_baseline_global_5y":0.3,
               "p_global_markov":0.4,"outcome":1}]
        self.assertAlmostEqual(summary_scores(rows,"p_model")["brier"],0.08,places=12)
        self.assertEqual(bootstrap_interval(rows,replications=100,seed=12),
                         bootstrap_interval(rows,replications=100,seed=12))

if __name__=="__main__":unittest.main()
