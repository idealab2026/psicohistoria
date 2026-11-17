"""Adversarial synthetic checks for historical UCDP low/best/high vintage audit."""
from __future__ import annotations

import io
import json
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit as audit_issued,
)
from audit_geo2027_ucdp_fatality_vintages import (
    EXPECTED_ROWS, FIELDS, VERSION_ORDER, compare_editions, classify,
    read_verified_intervals, snapshot, study, FULL_COHORT_START,
)
from audit_geo2027_ucdp_zero_coding import _xlsx_named_rows
from backtest_archived_country_vintages import SOURCES
from experiment_geo2027_intensity_markov_cross_release import parse_counts


class UCDPFatalityVintageIntervalsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.issue = json.loads(ISSUE.read_text(encoding="utf-8"))
        cls.ids = sorted(x["country_id"] for x in cls.issue["countries"])

    def full_panel(self, version):
        return {
            (cid, year): (0, 0, 0)
            for cid in self.ids
            for year in range(FULL_COHORT_START, SOURCES[version]["last_year"] + 1)
        }

    def test_all_four_sha_and_196_immutable_issued_frozen(self):
        a = audit_issued(
            ISSUE.read_bytes(), MANIFEST.read_bytes(), ORIGINAL.read_bytes(),
            OLD_SHADOW.read_bytes(), OLD_MANIFEST.read_bytes(),
            ALERTS.read_bytes())
        self.assertEqual(a["country_n"], 196)
        self.assertEqual(a["official_2027_outcomes_resolved"], 0)
        self.assertEqual(len(self.ids), 196)
        with self.assertRaises(ValueError):
            parse_counts(b"FAKE_ARCHIVE", "26.1")

    def test_strict_threshold_low_best_high_and_missing(self):
        self.assertEqual(classify((24, 24, 24)), (0, 0, 0))
        self.assertEqual(classify((24, 25, 26)), (0, 1, 1))
        self.assertEqual(classify((24, 24, 25)), (0, 0, 1))
        self.assertEqual(classify((25, 25, 25)), (1, 1, 1))
        for bad in ((26, 25, 27), (0, 26, 25), (-1, 0, 0),
                    ("24", 25, 26), (0, None, 5), (0.0, 0, 0)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                classify(bad)
        panel = {(cid, 2025): (0, 0, 0) for cid in self.ids}
        panel[(self.ids[0], 2025)] = (24, 25, 26)
        panel[(self.ids[1], 2025)] = (24, 24, 25)
        panel[(self.ids[2], 2025)] = (25, 25, 27)
        s = snapshot(panel, self.ids, 2025, show_ids=True)
        self.assertEqual(
            (s["active_low_n"], s["active_best_n"], s["active_high_n"]),
            (1, 2, 3))
        self.assertEqual(s["ambiguous_threshold_n"], 2)
        self.assertEqual(s["best_active_but_low_inactive_GWNO"], [self.ids[0]])
        self.assertEqual(s["best_inactive_but_high_active_GWNO"], [self.ids[1]])
        del panel[(self.ids[-1], 2025)]
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            snapshot(panel, self.ids, 2025)

    def test_23_1_xlsx_named_low_high_columns(self):
        header = FIELDS["23.1"]
        ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        header_cells = "".join(
            f'<c r="{chr(65+i)}1" t="inlineStr"><is><t>{value}</t></is></c>'
            for i, value in enumerate(header))
        values = (self.ids[0], 2022, 24, 25, 31)
        data_cells = "".join(
            f'<c r="{chr(65+i)}2"><v>{value}</v></c>'
            for i, value in enumerate(values))
        xml = (f'<worksheet xmlns="{ns}"><sheetData>'
               f'<row r="1">{header_cells}</row>'
               f'<row r="2">{data_cells}</row></sheetData></worksheet>')
        stream = io.BytesIO()
        with ZipFile(stream, "w") as z:
            z.writestr("xl/worksheets/sheet1.xml", xml.encode())
        result = list(_xlsx_named_rows(stream.getvalue(), header))
        self.assertEqual(result, [tuple(map(str, values))])

    def test_cross_edition_changes_are_independent_of_within_edition_ambiguity(self):
        old = {(cid, 2022): (0, 0, 0) for cid in self.ids}
        newer = dict(old)
        old[(self.ids[0], 2022)] = (24, 24, 28)   # ambiguous best=0
        newer[(self.ids[0], 2022)] = (24, 25, 28) # ambiguous best=1
        old[(self.ids[1], 2022)] = (0, 0, 0)
        newer[(self.ids[1], 2022)] = (25, 25, 28) # definitely active after
        x = compare_editions(old, newer, self.ids, 2022, "23.1", "26.1")
        self.assertEqual(x["changed_best_indicator_n"], 2)
        self.assertEqual(x["changed_ambiguous_indicator_n"], 1)
        self.assertEqual(x["unambiguous_opposite_classification_n"], 1)
        self.assertEqual(x["best_classification_differences_within_old_ambiguous_n"], 1)
        self.assertEqual(x["best_classification_differences_within_new_ambiguous_n"], 1)

    def test_complete_four_vintage_correlated_years_and_no_2027(self):
        panels = {v: self.full_panel(v) for v in VERSION_ORDER}
        # Same 2022 country gets a threshold reinterpretation in revised sources.
        panels["23.1"][(self.ids[0], 2022)] = (24, 24, 28)
        panels["24.1"][(self.ids[0], 2022)] = (24, 25, 28)
        panels["25.1"][(self.ids[0], 2022)] = (24, 25, 28)
        panels["26.1"][(self.ids[0], 2022)] = (24, 25, 28)
        output = study(panels, self.issue)
        self.assertEqual(output["2027_official_outcomes_observed"], 0)
        self.assertEqual(
            sum(len(s) for s in output["all_historical_year_edition_snapshots"].values()), 54)
        self.assertEqual(
            len(output["recent_all_edition_pair_comparisons"]), 10)
        self.assertEqual(
            sum(len(s) for s in output["recent_2022_2025_countrywise_snapshots"].values()), 10)
        pair = next(x for x in output["recent_all_edition_pair_comparisons"]
                    if x["older_edition"] == "23.1" and
                    x["later_edition"] == "26.1" and x["year"] == 2022)
        self.assertEqual(pair["changed_best_indicator_GWNO"], [self.ids[0]])
        self.assertEqual(pair["changed_ambiguous_indicator_n"], 0)
        self.assertTrue(output["low_best_high_are_not_confidence_limits"])
        self.assertTrue(output["retrospective_revisions_are_not_independent"])
        broken = {v:dict(p) for v,p in panels.items()}
        del broken["23.1"][(self.ids[1], 2011)]
        with self.assertRaisesRegex(ValueError, "panel incomplete"):
            study(broken, self.issue)

    def test_raw_row_crosschecks_shapinned_best_and_integrity(self):
        # Tested iterator injection only: the production code calls parse_counts
        # and its real SHA verification, tested separately above.
        cid = self.ids[0]
        testrows = [(str(cid), "2025", "24", "25", "35"),
                    (str(self.ids[1]), "2025", "0", "0", "0")]
        verified = {cid: {2025: 25}, self.ids[1]: {2025: 0}}
        with patch("audit_geo2027_ucdp_fatality_vintages.parse_counts", return_value=verified), \
             patch("audit_geo2027_ucdp_fatality_vintages._csv_named_rows", return_value=iter(testrows)), \
             patch.dict(EXPECTED_ROWS, {"26.1": 2}):
            result = read_verified_intervals(b"mock_binary_not_official", "26.1")
            self.assertEqual(result[(cid, 2025)], (24, 25, 35))
        badrows = [(str(cid), "2025", "24", "26", "35"),
                   (str(self.ids[1]), "2025", "0", "0", "0")]
        with patch("audit_geo2027_ucdp_fatality_vintages.parse_counts", return_value=verified), \
             patch("audit_geo2027_ucdp_fatality_vintages._csv_named_rows", return_value=iter(badrows)), \
             patch.dict(EXPECTED_ROWS, {"26.1": 2}):
            with self.assertRaisesRegex(ValueError, "reconcile"):
                read_verified_intervals(b"mock_binary_not_official", "26.1")


if __name__ == "__main__":
    unittest.main()
