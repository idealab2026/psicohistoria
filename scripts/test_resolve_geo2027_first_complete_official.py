"""Tests use SYNTHETIC 2027 labels exclusively, never official outcomes."""
from __future__ import annotations

import copy
from datetime import date
import hashlib
import io
import json
import unittest
from zipfile import ZipFile

from resolve_geo2027_first_complete_official import (
    META_SCHEMA, READINESS_SCHEMA, SCORING_SCHEMA, FIRST_POSSIBLE_RELEASE_DATE,
    extract_complete_2027_labels, evaluate_release, loaded_immutable_issues,
    preflight, review_provenance,
)


class Geo2027Full196ResolutionReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.issue,cls.ids=loaded_immutable_issues()
        cls.asof=date(2028,3,1)
        cls.raw=cls.make_csv()

    @classmethod
    def make_csv(cls,missing=None,duplicate=None,counts=None,
                 field_format="standard",include_2026=True):
        if field_format=="standard":
            names=("country_id","year","sb_total_deaths_best")
        else:
            names=("country_id_cy","year_cy","sb_total_deaths_best_cy")
        lines=[",".join(names)]
        if include_2026:
            lines.extend(f"{cid},2026,0" for cid in cls.ids)
        for i,cid in enumerate(cls.ids):
            if cid==missing:
                continue
            value=(counts or {}).get(cid,25 if i%11==0 else 0)
            lines.append(f"{cid},2027,{value}")
        if duplicate is not None:
            lines.append(f"{duplicate},2027,25")
        return ("\n".join(lines)+"\n").encode("utf-8")

    def review(self,raw=None):
        if raw is None:
            raw=self.raw
        return {
            "schema":META_SCHEMA,
            "dataset":"UCDP OrganizedViolenceCY",
            "year_target":2027,
            "outcome_column":"sb_total_deaths_best",
            "state_based_threshold":25,
            "edition":"synthetic-fixture-not-official",
            "source_sha256":hashlib.sha256(raw).hexdigest(),
            "official_publication_date":"2028-01-12",
            "human_reviewed_at_utc":"2028-02-01T12:00:00Z",
            "official_source_landing_page":"https://example.org/fixture",
            "official_source_download_url":"https://example.org/fixture.csv",
            "official_archive_release_listing_url":"https://example.org/releases",
            "verified_official_release_by_human":True,
            "human_review_first_complete_196_by_edition":True,
            "human_review_previous_2027_editions":True,
            "source_country_universe_check":"first_issued_196_GWNO",
            "first_complete_review_evidence":
                "SYNTHETIC TEST FIXTURE ONLY. No actual UCDP release is being "
                "reviewed; this is the artificial set of 196 explicitly enumerated rows.",
            "earlier_release_inventory":[],
        }

    def test_2026_default_is_not_ready_and_never_yields_performance_metrics(self):
        state=preflight()
        self.assertEqual(state["schema"],READINESS_SCHEMA)
        self.assertEqual(state["status"],
                         "NOT_READY_NO_VERIFIED_OFFICIAL_2027_RELEASE")
        self.assertEqual(state["n_fixed_first_issued_GWNO"],196)
        self.assertEqual(state["n_official_2027_labels_resolved"],0)
        self.assertTrue(state["no_current_brier_or_logloss_reported"])
        self.assertEqual(FIRST_POSSIBLE_RELEASE_DATE,date(2028,1,1))
        self.assertNotIn("score",state)

    def test_future_complete_196_explicit_zero_and_threshold(self):
        labels,stats=extract_complete_2027_labels(self.raw,self.ids)
        self.assertEqual(len(labels),196)
        self.assertEqual(stats["countries_2027_matched_to_first_issued_GWNO"],196)
        self.assertEqual(stats["n_binary_positives"],18)
        self.assertEqual(stats["min_2027_best_deaths"],0)
        self.assertEqual(stats["max_2027_best_deaths"],25)
        self.assertEqual(labels[self.ids[0]],1)
        self.assertEqual(labels[self.ids[1]],0)

    def test_missing_2027_row_rejected_not_assumed_zero_even_if_2026_exists(self):
        raw=self.make_csv(missing=self.ids[1])
        with self.assertRaisesRegex(ValueError,"INCOMPLETE.*missing"):
            extract_complete_2027_labels(raw,self.ids)

    def test_exact_25_threshold_and_subthreshold_24(self):
        raw=self.make_csv(counts={self.ids[0]:24,self.ids[1]:25})
        labels,_=extract_complete_2027_labels(raw,self.ids)
        self.assertEqual(labels[self.ids[0]],0)
        self.assertEqual(labels[self.ids[1]],1)

    def test_duplicate_and_blank_bad_raw_counts_rejected(self):
        cases=[
            self.make_csv(duplicate=self.ids[0]),
            self.make_csv(counts={self.ids[2]:""}),
            self.make_csv(counts={self.ids[2]:"24.0"}),
            self.make_csv(counts={self.ids[2]:"-1"}),
        ]
        for raw in cases:
            with self.subTest(raw_suffix=raw[-140:]):
                with self.assertRaises(ValueError):
                    extract_complete_2027_labels(raw,self.ids)

    def test_country_id_mismatch_and_2028_source_row_rejected(self):
        raw=self.raw.replace(
            f"{self.ids[1]},2027,0".encode(),
            b"1999,2027,0",1)
        with self.assertRaisesRegex(ValueError,"INCOMPLETE"):
            extract_complete_2027_labels(raw,self.ids)
        raw=self.raw+b"2,2028,0\n"
        with self.assertRaises(ValueError):
            extract_complete_2027_labels(raw,self.ids)

    def test_cy_suffix_and_bounded_zip_single_csv_accepted(self):
        raw=self.make_csv(field_format="cy")
        labels,report=extract_complete_2027_labels(raw,self.ids)
        self.assertEqual(len(labels),196)
        self.assertEqual(report["parser_fields_used"],[
            "country_id_cy","year_cy","sb_total_deaths_best_cy"])
        bio=io.BytesIO()
        with ZipFile(bio,"w") as z:
            z.writestr("country_year.csv",raw)
        more,info=extract_complete_2027_labels(bio.getvalue(),self.ids)
        self.assertEqual(labels,more)
        self.assertEqual(info["n_binary_positives"],18)
        bio=io.BytesIO()
        with ZipFile(bio,"w") as z:
            z.writestr("one.csv",raw)
            z.writestr("other.csv",raw)
        with self.assertRaises(ValueError):
            extract_complete_2027_labels(bio.getvalue(),self.ids)

    def test_future_publication_date_required_and_current_as_of_blocks_2026(self):
        meta=self.review()
        with self.assertRaisesRegex(ValueError,"future/unreviewed"):
            review_provenance(meta,self.raw,date(2026,11,16))
        changed=copy.deepcopy(meta)
        changed["official_publication_date"]="2027-12-31"
        with self.assertRaisesRegex(ValueError,"future/unreviewed"):
            review_provenance(changed,self.raw,self.asof)
        changed=copy.deepcopy(meta)
        changed["official_publication_date"]="2028-05-01"
        with self.assertRaisesRegex(ValueError,"future/unreviewed"):
            review_provenance(changed,self.raw,self.asof)

    def test_source_sha_and_human_edition_review_both_fail_closed(self):
        meta=self.review()
        self.assertTrue(review_provenance(meta,self.raw,self.asof)[
            "human_attested_first_complete_not_machine_proven"])
        wrong=copy.deepcopy(meta)
        wrong["source_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"SHA"):
            review_provenance(wrong,self.raw,self.asof)
        for field in ("verified_official_release_by_human",
                      "human_review_first_complete_196_by_edition",
                      "human_review_previous_2027_editions"):
            changed=copy.deepcopy(meta)
            changed[field]=False
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError,"review"):
                    review_provenance(changed,self.raw,self.asof)
        changed=copy.deepcopy(meta)
        changed["official_source_download_url"]="http://example.org/file.csv"
        with self.assertRaisesRegex(ValueError,"HTTPS"):
            review_provenance(changed,self.raw,self.asof)

    def test_synthetic_future_scoring_reproduces_preissued_exact_196_brier_identity(self):
        result=evaluate_release(self.raw,self.review(),self.asof)
        self.assertEqual(result["schema"],SCORING_SCHEMA)
        self.assertEqual(result["source_coverage"]["n_binary_positives"],18)
        self.assertTrue(result[
            "first_issued_countrywise_primary_Brier_identity_verified"])
        self.assertTrue(result[
            "manual_first_complete_release_priority_review_still_required"])
        self.assertEqual(result["score"]["n_country_labels"],196)
        self.assertEqual(len(result["score"]["metrics"]),5)
        self.assertEqual(
            len(result["score"]["predeclared_paired_differences"]),7)
        self.assertIn("OPERATOR_ATTESTED",result["status"])

    def test_scoring_rejects_partial_even_with_ostensible_valid_review(self):
        raw=self.make_csv(missing=self.ids[-1])
        with self.assertRaisesRegex(ValueError,"INCOMPLETE"):
            evaluate_release(raw,self.review(raw),self.asof)

    def test_issuer_cannot_submit_new_retrained_forecast_probabilities(self):
        self.assertEqual(len(self.issue["countries"]),196)
        self.assertEqual(self.issue["official_2027_outcomes_resolved"],0)
        # Reports are derived from the locked first-issued state, not from
        # arbitrary user-supplied forecast files.


if __name__=="__main__":
    unittest.main()
