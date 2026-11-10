import io
import zipfile
import unittest

from backtest_archived_country_vintages import (
    SOURCES,FOLDS,official_rows,read_xlsx_rows,run_folds
)

def histories(last):
    data={}
    for cid in range(1,197):
        h={}
        for year in range(1989,last+1):
            h[year]=int((cid%7==0 and year%5 in (0,1,2,3)) or
                        (cid%11==0 and year%4 in (1,2)))
        data[cid]=h
    return data

def versions():
    return {v:histories(SOURCES[v]["last_year"]) for v in SOURCES}

def metadata():
    return {v:{"url":s["url"],"sha256":s["sha256"],
               "last_year":s["last_year"],"rows":100} for v,s in SOURCES.items()}

class ArchivedCountryVintageTests(unittest.TestCase):
    def test_multiple_origins_have_strict_two_year_horizon_and_no_future_training(self):
        result=run_folds(versions(),metadata())
        self.assertEqual(result["country_years"],392)
        self.assertEqual([f["evaluated_year"] for f in result["folds"]],[2024,2025])
        self.assertEqual([f["origin_max_year"] for f in result["folds"]],[2022,2023])
        self.assertEqual([f["origin_version"] for f in result["folds"]],["23.1","24.1"])
        self.assertFalse(result["historical_forecasts_actually_issued"])
        self.assertFalse(result["original_release_timestamps_independently_notarized"])
        self.assertFalse(result["prospective_skill_demonstrated"])
        self.assertEqual(result["prospective_2027_outcomes_resolved"],0)
        self.assertEqual(result["historical_revision_diagnostics"][0]["revised_binary_labels"],0)

    def test_modified_holdout_outcomes_do_not_modify_historical_origin_predictions(self):
        dataset=versions()
        a=run_folds(dataset,metadata())
        # All training year cells unchanged; only target outcome altered.
        dataset["25.1"][12][2024]=1-dataset["25.1"][12][2024]
        b=run_folds(dataset,metadata())
        self.assertNotEqual(a["folds"][0]["scores"]["p_model"]["brier"],
                            b["folds"][0]["scores"]["p_model"]["brier"])
        self.assertEqual(a["folds"][0]["baseline_probability"],
                         b["folds"][0]["baseline_probability"])
        self.assertEqual(a["folds"][1]["scores"],b["folds"][1]["scores"])
        self.assertEqual(b["historical_revision_diagnostics"][0]["revised_binary_labels"],0)

    def test_origin_with_excess_future_year_is_blocked(self):
        dataset=versions()
        dataset["23.1"][1][2023]=1
        with self.assertRaisesRegex(ValueError,"Origin source"):
            run_folds(dataset,metadata())

    def test_sha_pins_must_match_each_exact_official_zip(self):
        with self.assertRaisesRegex(ValueError,"not pinned"):
            official_rows(b"fabricated","24.1")
        with self.assertRaisesRegex(ValueError,"not pinned"):
            official_rows(b"fabricated","23.1")

    def test_read_xlsx_rows_without_risk_of_macros_or_formula_evaluation(self):
        raw=io.BytesIO()
        prefix="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        with zipfile.ZipFile(raw,"w") as z:
            z.writestr("xl/worksheets/sheet1.xml",
                f'<worksheet xmlns="{prefix}"><sheetData>'
                '<row r="1">'
                '<c r="A1" t="inlineStr"><is><t>country_id_cy</t></is></c>'
                '<c r="B1" t="inlineStr"><is><t>year_cy</t></is></c>'
                '<c r="C1" t="inlineStr"><is><t>sb_total_deaths_best_cy</t></is></c>'
                '</row><row r="2"><c r="A2"><v>101</v></c>'
                '<c r="B2"><v>2022</v></c><c r="C2"><v>25</v></c></row>'
                '</sheetData></worksheet>')
        self.assertEqual(list(read_xlsx_rows(raw.getvalue())),[("101","2022","25")])

    def test_missing_target_remains_unresolved(self):
        dataset=versions()
        del dataset["26.1"][12][2025]
        result=run_folds(dataset,metadata())
        self.assertEqual(result["folds"][1]["unresolved"],1)
        self.assertEqual(result["folds"][1]["resolved"],195)
        self.assertEqual(result["country_years"],391)

if __name__=="__main__":
    unittest.main()
