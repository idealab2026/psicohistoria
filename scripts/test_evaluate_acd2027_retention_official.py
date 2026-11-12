"""Synthetic adversarial future-source tests; NO actual 2027 outcomes are used."""
import copy
import csv
import hashlib
import io
import json
import math
import unittest
from unittest.mock import patch
from zipfile import ZipFile,ZIP_DEFLATED

import evaluate_acd2027_retention_official as future


def fake_future_zip(ids, *,active=(),drop=(),bad=None,extra_2027=True):
    buff=io.StringIO()
    fieldnames=("conflict_id","year","type_of_conflict","gwno_a","gwno_loc")
    w=csv.DictWriter(buff,fieldnames=fieldnames)
    w.writeheader()
    for cid in ids:
        if cid in drop:
            continue
        w.writerow({
            "conflict_id":str(1000+cid),"year":"2025",
            "type_of_conflict":"3","gwno_a":str(cid),"gwno_loc":str(cid)})
    for cid in active:
        w.writerow({
            "conflict_id":str(2000+cid),"year":"2027",
            "type_of_conflict":"4","gwno_a":str(cid),"gwno_loc":str(cid)})
    if bad=="duplicate":
        cid=active[0]
        w.writerow({
            "conflict_id":str(2000+cid),"year":"2027",
            "type_of_conflict":"4","gwno_a":str(cid),"gwno_loc":str(cid)})
    if bad=="ambiguous":
        cid=ids[0]
        w.writerow({
            "conflict_id":"99999","year":"2027",
            "type_of_conflict":"3","gwno_a":str(cid),"gwno_loc":"999"})
    if bad=="unsupported":
        cid=ids[0]
        w.writerow({
            "conflict_id":"99998","year":"2027",
            "type_of_conflict":"9","gwno_a":str(cid),"gwno_loc":str(cid)})
    if bad=="malformed":
        w.writerow({
            "conflict_id":"99997","year":"2029",
            "type_of_conflict":"3","gwno_a":str(ids[0]),"gwno_loc":str(ids[0])})
    if extra_2027 and not active and bad is None:
        # Other source country had 2027 activity, so report's target year exists.
        w.writerow({"conflict_id":"99996","year":"2027","type_of_conflict":"3",
                    "gwno_a":"1999","gwno_loc":"1999"})
    bio=io.BytesIO()
    with ZipFile(bio,"w",ZIP_DEFLATED) as archive:
        archive.writestr("ucdp-prio-281-synthetic.csv",buff.getvalue())
    return bio.getvalue()


class ACD2027FutureOfficialContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.issued=future.authenticated_issue()
        cls.ids=[x["country_id"] for x in cls.issued["countries"]]

    def claim(self):
        return future.validate_future_source(
            "https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-281-csv.zip",
            "0"*64,"2028-06-01")

    def test_first_issue_forecast_unchanged_and_unobserved(self):
        d=self.issued
        self.assertEqual(len(d["countries"]),32)
        self.assertEqual(d["2027_outcomes_resolved"],0)
        self.assertFalse(d["prospective_skill_demonstrated"])
        self.assertEqual(d["primary_model"],"p_global_recent5")
        self.assertEqual(sum(x["p_global_recent5"] for x in d["countries"]),
                         32*0.859195402299)
        raw=future.ISSUE_PATH.read_bytes()
        with self.assertRaisesRegex(ValueError,"original 2026 first-public|risk set"):
            future.authenticated_issue(issue_raw=raw+b" ")
        altered=json.loads(future.MANIFEST.read_text(encoding="utf8"))
        altered["first_public_git_commit"]="0"*40
        with self.assertRaisesRegex(ValueError,"original 2026 first-public|commitment"):
            future.authenticated_issue(manifest=altered)
        altered=json.loads(future.AUDIT_PATH.read_text(encoding="utf8"))
        altered["2027_outcomes_resolved"]=1
        with self.assertRaisesRegex(ValueError,"original 2026 first-public|commitment"):
            future.authenticated_issue(issued_audit=altered)

    def test_validate_only_first_possible_full_2027_release_shape(self):
        self.assertFalse(self.claim()["first_complete_publication_independently_verified"])
        for url in (
            "https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-271-csv.zip",
            "https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-291-csv.zip",
            "https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-281-csv.zip?q=1",
            "https://bad.example/downloads/ucdpprio/ucdp-prio-acd-281-csv.zip",
            "http://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-281-csv.zip",
            "https://ucdp.uu.se.evil.net/downloads/ucdpprio/ucdp-prio-acd-281-csv.zip",
        ):
            with self.subTest(url=url),self.assertRaises(ValueError):
                future.validate_future_source(url,"0"*64,"2028-03-05")
        for when in ("2026-11-13","2027-12-31","2028-02-30",
                     "not-a-date","2028-02-01T20:00:00"):
            with self.subTest(date=when),self.assertRaises(ValueError):
                future.validate_future_source(
                    "https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-281-csv.zip",
                    "0"*64,when)
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            future.validate_future_source(
                "https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-281-csv.zip",
                "not-64-hex","2028-06-01")

    def test_complete_synthetic_cover_32_exactly_and_compare_three(self):
        raw=fake_future_zip(self.ids,active=self.ids[:5])
        candidate=future.parse_future_archive(raw)
        self.assertEqual(candidate["source_last_year"],2027)
        self.assertEqual(candidate["official_2027_valid_intrastate_conflict_year_rows"],5)
        report=future.candidate_evaluation(self.issued,candidate,self.claim(),True)
        self.assertEqual(report["status"],"ALL_32_CODED_CANDIDATE_SCORES_UNCERTIFIED")
        self.assertTrue(report["target_label_coverage_internally_complete"])
        self.assertEqual(report["n_issued_country_codes_seen_in_historical_source"],32)
        self.assertEqual(report["missing_issued_country_ids"],[])
        self.assertFalse(report["independently_verified_first_complete_official_release"])
        self.assertFalse(report["source_completeness_independently_proven"])
        self.assertFalse(report["2027_scores_independently_certified"])
        self.assertFalse(report["prospective_skill_demonstrated_by_this_source"])
        scored=report["metric_values_candidate_only"]
        self.assertEqual(scored["n_issued_country_risk_set"],32)
        self.assertEqual(scored["n_2027_intrastate_persistence_recorded"],5)
        self.assertEqual(set(scored["models"]),set(future.MODELS))
        self.assertAlmostEqual(
            scored["models"]["p_global_recent5"]["expected_at_2026_issuance"],
            self.issued["model_expected_2027_persistence"]["p_global_recent5"],
            places=9)
        p=self.issued["countries"][0]["p_global_recent5"]
        self.assertAlmostEqual(
            scored["models"]["p_global_recent5"]["brier"],
            (5*(1-p)**2+27*p*p)/32)
        self.assertFalse(scored["independent_iid_significance_test_performed"])

    def test_missing_any_one_issued_country_never_becomes_zero(self):
        missing=self.ids[6]
        raw=fake_future_zip(self.ids,active=self.ids[:3],drop=(missing,))
        d=future.parse_future_archive(raw)
        result=future.candidate_evaluation(self.issued,d,self.claim(),True)
        self.assertEqual(result["status"],"INSUFFICIENT_SOURCE_COVERAGE_NO_SCORE")
        self.assertEqual(result["missing_issued_country_ids"],[missing])
        self.assertIsNone(result["metric_values_candidate_only"])
        self.assertFalse(result["target_label_coverage_internally_complete"])
        with self.assertRaisesRegex(ValueError,"hash"):
            future.candidate_evaluation(self.issued,d,self.claim(),False)

    def test_ambiguous_target_and_unsupported_type_never_score(self):
        for bad,field in (
            ("ambiguous","official_2027_ambiguous_intrastate_rows"),
            ("unsupported","official_2027_unsupported_type_rows"),
        ):
            with self.subTest(bad=bad):
                raw=fake_future_zip(self.ids,active=self.ids[:4],bad=bad)
                parsed=future.parse_future_archive(raw)
                self.assertEqual(parsed[field],1)
                result=future.candidate_evaluation(
                    self.issued,parsed,self.claim(),True)
                self.assertEqual(result["status"],"INSUFFICIENT_SOURCE_COVERAGE_NO_SCORE")
                self.assertIsNone(result["metric_values_candidate_only"])
        with self.assertRaisesRegex(ValueError,"Duplicated"):
            future.parse_future_archive(
                fake_future_zip(self.ids,active=self.ids[:2],bad="duplicate"))
        with self.assertRaisesRegex(ValueError,"1946"):
            future.parse_future_archive(
                fake_future_zip(self.ids,active=self.ids[:2],bad="malformed"))

    def test_incomplete_candidate_year_or_invalid_label_never_scores(self):
        with self.assertRaisesRegex(ValueError,"full-year 2027"):
            future.parse_future_archive(
                fake_future_zip(self.ids,active=(),extra_2027=False))
        ids=set(self.ids)
        with self.assertRaisesRegex(ValueError,"EXACTLY"):
            future.score_same_issued_countries(
                self.issued,{cid:0 for cid in list(self.ids)[:-1]})
        wrong={cid:0 for cid in ids}
        wrong[self.ids[0]]=None
        with self.assertRaisesRegex(ValueError,"invalid future"):
            future.score_same_issued_countries(self.issued,wrong)
        wrong={cid:0 for cid in ids}
        wrong[self.ids[0]]=True
        with self.assertRaisesRegex(ValueError,"invalid future"):
            future.score_same_issued_countries(self.issued,wrong)


if __name__=="__main__":
    unittest.main()
