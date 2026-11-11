import json
import unittest
from copy import deepcopy
from pathlib import Path

from evaluate_2027_newconf_official import (
    COHORT, MIN_RESOLVED, YEAR, FROZEN_SHA, FIRST_COMMIT,
    FORECAST, MANIFEST, GENERATOR,
    load_issued, validate_future_source, parse_official_2027_csv,
    score, bootstrap_delta, calibration, topk_tie_bounds, evaluate,
)

def synthetic():
    rows=[]
    for i in range(1,COHORT+1):
        rows.append({
            "country_id":str(i),
            "p_model":.05 if i%2 else .1,
            "p_baseline_global_5y":.025,
            "p_country_eb":.04,
            "p_activity_global":.06,
            "active_intrastate_2025":int(i<=32),
        })
    return {
       "forecast_id":"PSICO-QGEO01-NEWCONF2027-ORIGIN2025-V1",
       "target":{"year":YEAR},
       "training_summary":{
           "expected_positive_countries_model":14.7,
           "expected_positive_countries_baseline":4.9,
       },
       "countries":rows
    }

def metadata():
    return {"url":"https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-multiple-onset-281.csv",
            "sha256":"a"*64,"claimed_release_date_unverified":"2028-07-01"}

class OfficialNewconf2027CandidateTests(unittest.TestCase):
    def test_original_196_country_issue_is_immutable_before_any_future_label(self):
        doc,manifest=load_issued()
        self.assertEqual(len(doc["countries"]),196)
        self.assertEqual(doc["target"]["year"],2027)
        self.assertEqual(manifest["forecast_sha256"],FROZEN_SHA)
        self.assertEqual(manifest["first_public_forecast_commit"],FIRST_COMMIT)
        self.assertEqual(manifest["outcomes_resolved"],0)
        self.assertFalse(manifest["demonstrated_predictive_skill"])
        self.assertEqual(doc["provenance"]["forecasts_issued_before_current"],0)
        self.assertEqual(sum(x["active_intrastate_2025"] for x in doc["countries"]),32)
        # Fail-closed on a modified local document, even without a future source.
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/"issue.json"
            source.write_bytes(FORECAST.read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError,"First NEWCONF-2027 canonical"):
                load_issued(source,MANIFEST,GENERATOR)

    def test_source_must_have_ucdp_domain_correct_variant_and_post_2027_date(self):
        url="https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-multiple-onset-281.csv"
        self.assertTrue(validate_future_source(url,"f"*64,"2028-03-20"))
        for bad in [
            "http://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-multiple-onset-281.csv",
            "https://ucdp.uu.se.evil.org/downloads/onset/ucdp-intrastate-country-multiple-onset-281.csv",
            "https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-onset-281.csv",
            "https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-multiple-onset-251.csv",
            "https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-multiple-onset-281.csv?test=1",
        ]:
            with self.assertRaises(ValueError):
                validate_future_source(bad,"f"*64,"2028-03-20")
        with self.assertRaisesRegex(ValueError,"before 2028"):
            validate_future_source(url,"f"*64,"2027-10-31")
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            validate_future_source(url,"0"*63,"2028-04-01")

    def test_multiple_episode_rows_are_or_aggregated_without_doubling_countries(self):
        csvdata=(
            "gwno_a,year,newconf,onset2,conflict_id\n"
            "1,2026,1,1,123\n"
            "1,2027,0,0,123\n"
            "1,2027,1,0,456\n"
            "1,2027,1,0,789\n"
            "2,2027,0,1,222\n"
            "3,2027,0,0,333\n"
            "3,2027,0,0,444\n"
            "400,2027,1,0,555\n"
        )
        outcomes,counts=parse_official_2027_csv(csvdata)
        self.assertEqual(outcomes,{"1":1,"2":0,"3":0,"400":1})
        self.assertEqual(counts["source_episode_rows_2027"],7)
        self.assertEqual(counts["source_country_year_groups_2027"],4)
        self.assertEqual(counts["source_duplicate_country_year_groups_2027"],2)
        self.assertEqual(counts["source_extra_episode_rows_over_country_years"],3)
        self.assertEqual(counts["source_newconf_positive_country_years"],2)
        self.assertEqual(counts["source_newconf_positive_episode_rows"],3)

    def test_missing_newconf_episode_is_unresolved_and_onset2_is_not_proxy(self):
        out,cnt=parse_official_2027_csv(
            "gwno_a,year,newconf,onset2\n"
            "1,2027,0,1\n"            # onset2 positive is not our target
            "2,2027,0,0\n"
            "2,2027,,1\n"             # one missing episode invalidates country's label
            "3,2027,,0\n"
            "4,2027,1,0\n"
        )
        self.assertEqual(out,{"1":0,"4":1})
        self.assertEqual(cnt["country_years_with_incomplete_newconf_label"],2)
        self.assertEqual(cnt["source_country_years_resolved"],2)
        with self.assertRaisesRegex(ValueError,"binary"):
            parse_official_2027_csv("gwno_a,year,newconf\n1,2027,2\n")
        with self.assertRaisesRegex(ValueError,"requires unique"):
            parse_official_2027_csv("gwno_a,year,onset2\n1,2027,1\n")
        with self.assertRaisesRegex(ValueError,"No target-year"):
            parse_official_2027_csv("gwno_a,year,newconf\n1,2026,1\n")
        with self.assertRaisesRegex(ValueError,"unmapped GW"):
            parse_official_2027_csv("gwno_a,year,newconf\n,2027,0\n")
        with self.assertRaisesRegex(ValueError,"Malformed"):
            parse_official_2027_csv("gwno_a,year,newconf\n1,2027,1,EXTRA\n")

    def test_coverage_gate_and_untested_country_must_not_be_zero(self):
        d=synthetic()
        outcomes={str(i):int(i==1) for i in range(1,MIN_RESOLVED)}
        r=evaluate(d,outcomes,metadata(),{})
        self.assertEqual(r["issued"],196)
        self.assertEqual(r["resolved"],MIN_RESOLVED-1)
        self.assertEqual(r["unresolved"],196-(MIN_RESOLVED-1))
        self.assertEqual(r["events_resolved"],1)
        self.assertEqual(len(r["unresolved_issued_country_ids"]),r["unresolved"])
        self.assertIsNone(r["scores"])
        self.assertIsNone(r["bootstrap_country_delta_brier_95pct"])
        self.assertIsNone(r["alert_budgets_tie_safe"])
        self.assertFalse(r["enough_coverage_for_exploratory_score"])
        self.assertFalse(r["first_complete_official_2027_release_independently_attested"])
        self.assertFalse(r["future_predictive_skill_independently_verified"])
        self.assertFalse(r["model_or_baseline_ever_refit"])

    def test_95pct_gate_scores_only_observed_country_years(self):
        d=synthetic()
        outcomes={str(i):int(i%14==0) for i in range(1,MIN_RESOLVED+1)}
        results=evaluate(d,outcomes,metadata(),{})
        self.assertEqual(results["resolved"],MIN_RESOLVED)
        self.assertEqual(results["unresolved"],COHORT-MIN_RESOLVED)
        self.assertTrue(results["enough_coverage_for_exploratory_score"])
        self.assertFalse(results["complete_original_cohort_coverage"])
        self.assertEqual(set(results["scores"]),{
            "p_model","p_baseline_global_5y","p_country_eb",
            "p_activity_global","no_newconf_brier_reference"})
        self.assertEqual(sum(b["n"] for b in results["calibration"]),MIN_RESOLVED)
        self.assertIsNone(results["alert_budgets_tie_safe"])
        self.assertEqual(results["model_expected_events_issued"],14.7)
        self.assertFalse(results["future_predictive_skill_independently_verified"])

    def test_tied_alerts_report_best_worst_hits_not_arbitrary_country_id(self):
        rows=[]
        for i in range(196):
            p=.6 if i<6 else .3 if i<26 else .05
            rows.append({
                "country_id":str(i+1),"p_model":p,
                "p_baseline_global_5y":.1,"outcome":int(i in (2,4,7,8,24,30))
            })
        b=topk_tie_bounds(rows,10)
        self.assertEqual(b["higher_probability_countries"],6)
        self.assertEqual(b["boundary_tied_countries"],20)
        self.assertEqual(b["places_within_boundary_tie"],4)
        self.assertEqual(b["lower_possible_hits"],2)
        self.assertEqual(b["upper_possible_hits"],5)
        self.assertFalse(b["unique_hit_count"])
        r=topk_tie_bounds(rows,5)
        self.assertEqual(r["higher_probability_countries"],0)
        self.assertEqual(r["boundary_tied_countries"],6)
        self.assertEqual(r["lower_possible_hits"],1)
        self.assertEqual(r["upper_possible_hits"],2)
        with self.assertRaisesRegex(ValueError,"any issued country outcome is missing"):
            topk_tie_bounds(rows[:-1],10)

    def test_no_false_prospective_skill_even_with_perfect_synthetic_outcomes(self):
        d=synthetic()
        outcomes={str(i):int(i%2==0) for i in range(1,197)}
        report=evaluate(d,outcomes,metadata(),{})
        self.assertTrue(report["complete_original_cohort_coverage"])
        self.assertTrue(report["enough_coverage_for_exploratory_score"])
        self.assertEqual(len(report["alert_budgets_tie_safe"]),3)
        self.assertEqual(sum(x["n"] for x in report["calibration"]),196)
        self.assertAlmostEqual(
            report["delta_brier_model_minus_global_recent"],
            report["scores"]["p_model"]["brier"]-
            report["scores"]["p_baseline_global_5y"]["brier"])
        self.assertFalse(report["future_predictive_skill_independently_verified"])
        self.assertFalse(report["first_complete_official_2027_release_independently_attested"])
        self.assertEqual(bootstrap_delta([
            {"country_id":"1","p_model":.3,"p_baseline_global_5y":.1,"outcome":0},
            {"country_id":"2","p_model":.4,"p_baseline_global_5y":.1,"outcome":1},
        ],100,99),bootstrap_delta([
            {"country_id":"1","p_model":.3,"p_baseline_global_5y":.1,"outcome":0},
            {"country_id":"2","p_model":.4,"p_baseline_global_5y":.1,"outcome":1},
        ],100,99))

if __name__=="__main__":
    unittest.main()
