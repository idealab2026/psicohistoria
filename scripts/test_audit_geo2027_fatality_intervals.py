"""Synthetic-only tests: no official 2027 outcomes, no empirical Brier claims."""
from __future__ import annotations

from datetime import date
import hashlib
import io
import itertools
import json
import unittest
from zipfile import ZipFile

from audit_geo2027_fatality_intervals import (
    N, PAIR_P, PAIR_Q, SCHEMA, _delta_brier, evaluate_intervals,
    extract_official_intervals, sensitivity,
)
from resolve_geo2027_first_complete_official import (
    META_SCHEMA, loaded_immutable_issues, preflight,
)


class Geo2027FatalityIntervalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.issue, cls.ids = loaded_immutable_issues()
        cls.asof = date(2028, 3, 1)
        cls.synthetic = cls.make_csv()

    @classmethod
    def make_csv(cls, *, suffix=False, missing=None, duplicate=False,
                 override=None, extra_later=False):
        suffix = "_cy" if suffix else ""
        names = ["country_id" + suffix, "year" + suffix,
                 "sb_total_deaths_low" + suffix,
                 "sb_total_deaths_best" + suffix,
                 "sb_total_deaths_high" + suffix]
        lines = [",".join(names)]
        for i, cid in enumerate(cls.ids):
            if cid == missing:
                continue
            val = {
                0: (24, 25, 26),
                1: (24, 24, 25),
                2: (25, 25, 29),
                4: (20, 24, 30),
            }.get(i, (0, 0, 0))
            val = (override or {}).get(cid, val)
            lines.append(f"{cid},2027,{val[0]},{val[1]},{val[2]}")
        if duplicate:
            lines.append(f"{cls.ids[0]},2027,24,25,26")
        if extra_later:
            lines.append(f"{cls.ids[0]},2028,0,0,0")
        return ("\n".join(lines) + "\n").encode("utf-8")

    def review(self, raw):
        return {
            "schema": META_SCHEMA,
            "dataset": "UCDP OrganizedViolenceCY",
            "year_target": 2027,
            "outcome_column": "sb_total_deaths_best",
            "state_based_threshold": 25,
            "edition": "synthetic-fixture-not-official",
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "official_publication_date": "2028-01-12",
            "human_reviewed_at_utc": "2028-02-01T12:00:00Z",
            "official_source_landing_page": "https://example.org/synthetic",
            "official_source_download_url": "https://example.org/synthetic.csv",
            "official_archive_release_listing_url": "https://example.org/releases",
            "verified_official_release_by_human": True,
            "human_review_first_complete_196_by_edition": True,
            "human_review_previous_2027_editions": True,
            "source_country_universe_check": "first_issued_196_GWNO",
            "first_complete_review_evidence": (
                "SYNTHETIC TEST FIXTURE ONLY. This artificially enumerates all "
                "196 country-year rows and is NOT any UCDP release or a claim "
                "that such a release exists at the time of this test."
            ),
            "earlier_release_inventory": [],
        }

    def test_2026_is_not_ready(self):
        state = preflight()
        self.assertEqual(state["n_official_2027_labels_resolved"], 0)
        self.assertFalse(state["first_complete_verified_official_source_available"])
        self.assertEqual(len(self.issue["countries"]), N)

    def test_exact_low_best_high_threshold_partition(self):
        intervals = extract_official_intervals(self.synthetic, self.ids)
        self.assertEqual(len(intervals), 196)
        self.assertEqual(intervals[self.ids[0]], (24, 25, 26))
        result = sensitivity(self.issue, intervals)
        self.assertEqual(result["schema"], SCHEMA)
        self.assertEqual(result["threshold_ambiguous_countries_n"], 3)
        self.assertEqual(result["threshold_ambiguous_GWNO"],
                         sorted([self.ids[0], self.ids[1], self.ids[4]]))
        self.assertEqual(result["certain_active_across_low_high_n"], 1)
        self.assertEqual(result["certain_inactive_across_low_high_n"], 192)
        self.assertEqual([result[f"{x}_scenario_active_n"] for x in
                          ("low", "best", "high")], [1, 2, 4])

    def test_sharp_bounds_bruteforce_all_three_ambiguous_labels(self):
        intervals = extract_official_intervals(self.synthetic, self.ids)
        bound = sensitivity(self.issue, intervals)
        flexible = [self.ids[0], self.ids[1], self.ids[4]]
        deltas = []
        for choices in itertools.product((0, 1), repeat=len(flexible)):
            assignment = dict(zip(flexible, choices))
            val = 0.
            for row in self.issue["countries"]:
                cid = row["country_id"]
                y = assignment.get(cid, int(intervals[cid][0] >= 25))
                val += _delta_brier(row[PAIR_P], row[PAIR_Q], y)
            deltas.append(val / N)
        self.assertAlmostEqual(min(deltas),
            bound["sharp_algebraic_lower_delta_brier"], places=13)
        self.assertAlmostEqual(max(deltas),
            bound["sharp_algebraic_upper_delta_brier"], places=13)
        self.assertLessEqual(bound["sharp_algebraic_lower_delta_brier"],
                             bound["delta_brier_best"])
        self.assertGreaterEqual(bound["sharp_algebraic_upper_delta_brier"],
                                bound["delta_brier_best"])

    def test_valid_suffix_zip_and_2028_rows_do_not_change_2027(self):
        plain = extract_official_intervals(self.synthetic, self.ids)
        self.assertEqual(plain, extract_official_intervals(
            self.make_csv(suffix=True, extra_later=True), self.ids))
        raw = io.BytesIO()
        with ZipFile(raw, "w") as z:
            z.writestr("ucdp_country_year.csv", self.synthetic)
        self.assertEqual(plain, extract_official_intervals(
            raw.getvalue(), self.ids))

    def test_missing_duplicate_negative_and_fractional_fail(self):
        invalid = [
            self.make_csv(missing=self.ids[1]),
            self.make_csv(duplicate=True),
            self.make_csv(override={self.ids[0]: (-1, 25, 26)}),
            self.make_csv(override={self.ids[0]: ("24.0", 25, 26)}),

        ]
        for raw in invalid:
            with self.subTest(raw=raw[-80:]):
                with self.assertRaises((ValueError, AssertionError)):
                    extract_official_intervals(raw, self.ids)

    def test_nonmonotonic_official_estimates_are_valid_and_flagged(self):
        raw = self.make_csv(override={
            self.ids[0]: (0, 26, 24),  # best active, high inactive
            self.ids[1]: (26, 25, 27), # low larger than best
        })
        triples = extract_official_intervals(raw, self.ids)
        output = sensitivity(self.issue, triples)
        self.assertEqual(output["nonmonotonic_official_triples_n"], 2)
        self.assertEqual(output["best_exceeds_high_GWNO"], [self.ids[0]])
        self.assertEqual(output["low_exceeds_best_GWNO"], [self.ids[1]])
        self.assertIn(self.ids[0], output["threshold_ambiguous_GWNO"])
        self.assertLessEqual(output["sharp_algebraic_lower_delta_brier"],
                             output["delta_brier_best"])
        self.assertGreaterEqual(output["sharp_algebraic_upper_delta_brier"],
                                output["delta_brier_best"])

    def test_missing_low_high_columns_fail_closed(self):
        lines = ["country_id,year,sb_total_deaths_best"]
        lines += [f"{cid},2027,0" for cid in self.ids]
        with self.assertRaisesRegex(ValueError, "low/best/high"):
            extract_official_intervals(
                ("\n".join(lines) + "\n").encode(), self.ids)

    def test_full_future_gate_and_primary_best_score_identical_synthetic(self):
        result = evaluate_intervals(
            self.synthetic, self.review(self.synthetic), as_of_date=self.asof)
        self.assertEqual(result["status"],
            "SECONDARY_OPERATOR_ATTESTED_SOURCE_NOT_MACHINE_AUTHENTICATED")
        self.assertEqual(result["source_coverage"][
            "countries_2027_matched_to_first_issued_GWNO"], 196)
        self.assertTrue(result["primary_Brier_identity_reverified"])
        self.assertEqual(result["secondary_sensitivity"][
            "threshold_ambiguous_countries_n"], 3)
        self.assertTrue(result["2027_primary_score_unchanged"])

    def test_future_review_hash_and_publication_gates_cannot_be_bypassed(self):
        review = self.review(self.synthetic)
        review["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA"):
            evaluate_intervals(self.synthetic, review, as_of_date=self.asof)
        review = self.review(self.synthetic)
        with self.assertRaises(ValueError):
            evaluate_intervals(self.synthetic, review,
                               as_of_date=date(2026, 11, 17))


if __name__ == "__main__":
    unittest.main()
