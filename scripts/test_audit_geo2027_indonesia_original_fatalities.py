"""Unit tests of raw UCDP annual state-based fatalities and no-missing-as-zero."""
from __future__ import annotations

import csv
import io
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from audit_geo2027_indonesia_original_fatalities import (
    IDS, YEARS, VERSIONS, exact_nonnegative_int, parse_selected_rows, revision_rows,
)


def synthetic_zip(rows):
    file = io.StringIO()
    writer = csv.DictWriter(file, fieldnames=(
        "country_id_cy", "year_cy", "sb_total_deaths_best_cy"))
    writer.writeheader()
    for cid, year, deaths in rows:
        writer.writerow({"country_id_cy":cid, "year_cy":year,
                         "sb_total_deaths_best_cy":deaths})
    memory=io.BytesIO()
    with ZipFile(memory, "w", ZIP_DEFLATED) as z:
        z.writestr("organized.csv", file.getvalue())
    return memory.getvalue()


def sample():
    base={cid: {y: 8 for y in YEARS} for cid in IDS}
    newer={cid:dict(years) for cid,years in base.items()}
    newer[850][2019]=26
    newer[850][2020]=125
    return {v: base if v in ("23.1", "24.1") else newer for v in VERSIONS}


def fake_prior():
    return {
        "schema": "idealab.psico.geo2027_indonesia_vintage_source_attribution.v1",
        "outcomes_2027_resolved": 0,
        "comparisons": [
            {"comparison": f"23.1->{v}", "countries": {"850": {
                "changed_historical_binary_years": (
                    [] if v=="24.1" else [
                        {"year": 2019, "original_state":0, "revised_state":1},
                        {"year": 2020, "original_state":0, "revised_state":1}
                    ])
            }}} for v in VERSIONS[1:]
        ],
    }


class OriginalDeathsTests(unittest.TestCase):
    def test_source_rows_threshold_and_structural_coverage(self):
        rows=[(cid,year,"24" if year==2019 else "25")
              for cid in IDS for year in YEARS]
        result=parse_selected_rows(synthetic_zip(rows),"24.1")
        self.assertEqual(result[850][2019],24)
        self.assertEqual(result[850][2020],25)

    def test_missing_country_year_is_not_zero(self):
        rows=[(cid,year,5) for cid in IDS for year in YEARS
              if (cid,year)!=(850,2020)]
        with self.assertRaisesRegex(ValueError,"gap"):
            parse_selected_rows(synthetic_zip(rows),"24.1")

    def test_duplicate_is_rejected(self):
        rows=[(cid,year,5) for cid in IDS for year in YEARS]
        rows.append((850,2020,9))
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            parse_selected_rows(synthetic_zip(rows),"24.1")

    def test_valid_decimal_integer_but_never_round(self):
        self.assertEqual(exact_nonnegative_int("25.0","fatalities"),25)
        with self.assertRaisesRegex(ValueError,"Noninteger"):
            exact_nonnegative_int("24.9","fatalities")

    def test_source_year_revisions_match_binary_attribution(self):
        report=revision_rows(sample(),fake_prior())
        self.assertEqual(report["2027_outcomes_observed"],0)
        self.assertEqual(len(report["compared_to_23_1"]),3)
        self.assertEqual(len(report["compared_to_23_1"][1][
            "binary_threshold_changes"]),2)
        self.assertEqual(report["compared_to_23_1"][0][
            "binary_threshold_changes"],[])

    def test_prior_attribution_mismatch_fails_closed(self):
        altered=fake_prior()
        altered["comparisons"][2]["countries"]["850"][
            "changed_historical_binary_years"]=[]
        with self.assertRaisesRegex(ValueError,"contradict"):
            revision_rows(sample(),altered)


if __name__=="__main__":
    unittest.main()
