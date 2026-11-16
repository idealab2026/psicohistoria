"""UCDP official zero-coded state-based death semantics and GWNO completeness."""
from __future__ import annotations

import io
import json
import unittest
from zipfile import ZipFile

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit as audit_issued,
)
from audit_geo2027_ucdp_zero_coding import (
    EXPECTED_ROWS, KEYS, VERSION_ORDER, _xlsx_named_rows,
    bool_flag, strict_int, yearly_coverage, study,
)


class UCDPZeroCodingSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.issue=json.loads(ISSUE.read_text(encoding="utf8"))
        cls.ids=sorted(r["country_id"] for r in cls.issue["countries"])

    def test_issued_sha_contract_and_exact_2025_frozen_196(self):
        result=audit_issued(
            ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
            OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),
            ALERTS.read_bytes())
        self.assertEqual(result["country_n"],196)
        self.assertEqual(result["official_2027_outcomes_resolved"],0)
        self.assertEqual(len(self.ids),196)
        self.assertEqual(set(VERSION_ORDER),set(EXPECTED_ROWS))
        self.assertEqual(EXPECTED_ROWS["26.1"],7132)
        self.assertTrue(all("sb_exist" in KEYS[v][-1] for v in VERSION_ORDER))

    def test_official_coded_zero_but_existence_one_is_possible_and_not_missing(self):
        ids=self.ids
        rows={
            (ids[0],2025):{"deaths":0,"sb_exist":1},
            (ids[1],2025):{"deaths":0,"sb_exist":0},
            (ids[2],2025):{"deaths":17,"sb_exist":1},
            (ids[3],2025):{"deaths":25,"sb_exist":1},
            (ids[4],2025):{"deaths":40,"sb_exist":0},
        }
        a=yearly_coverage(rows,ids,2025)
        self.assertEqual(a["explicit_rows_n"],5)
        self.assertEqual(len(a["first_issued_GWNO_missing_ids"]),191)
        self.assertEqual(a["literal_zero_best_fatalities_n"],2)
        self.assertEqual(a["best_deaths_1_to_24_n"],1)
        self.assertEqual(a["best_deaths_25_plus_n"],2)
        self.assertEqual(a["zero_best_but_existence_flag_1_n"],1)
        self.assertEqual(a["best_positive_but_existence_flag_0_n"],1)
        self.assertTrue(a["zero_best_does_not_prove_no_fatal_organized_violence"])
        self.assertTrue(a["explicit_country_year_missing_is_not_implicit_zero"])

    def test_full196_coverage_does_not_infer_missing_from_zero(self):
        ids=self.ids
        rows={(cid,2025):{"deaths":0,"sb_exist":0} for cid in ids}
        a=yearly_coverage(rows,ids,2025)
        self.assertEqual(a["explicit_rows_n"],196)
        self.assertEqual(a["literal_zero_best_fatalities_n"],196)
        self.assertEqual(a["zero_best_and_existence_flag_0_n"],196)
        del rows[(ids[-1],2025)]
        b=yearly_coverage(rows,ids,2025)
        self.assertEqual(b["explicit_rows_n"],195)
        self.assertEqual(b["first_issued_GWNO_missing_ids"],[ids[-1]])
        self.assertEqual(b["literal_zero_best_fatalities_n"],195)

    def test_flag_and_numeric_field_strictness(self):
        for v in (0,"0"," false ","FALSE"):
            self.assertEqual(bool_flag(v),0)
        for v in (1,"1"," true ","TRUE"):
            self.assertEqual(bool_flag(v),1)
        for v in (-1,2,"","N/A",None,"1.0","no","yes",True):
            with self.subTest(v=v):
                with self.assertRaises(ValueError):
                    bool_flag(v)
        for val in ("","1.0","-1","nan",None,True):
            with self.subTest(val=val):
                with self.assertRaises(ValueError):
                    strict_int(val,"death count")
        self.assertEqual(strict_int("0", "n"),0)
        self.assertEqual(strict_int("25","n"),25)

    def test_minimal_xlsx_named_stream_handles_4_schema_columns(self):
        ns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        headers=KEYS["23.1"]
        headercells="".join(
            f'<c r="{chr(65+i)}1" t="inlineStr"><is><t>{h}</t></is></c>'
            for i,h in enumerate(headers))
        rowcells=(
            '<c r="A2"><v>2</v></c>'
            '<c r="B2"><v>2022</v></c>'
            '<c r="C2"><v>0</v></c>'
            '<c r="D2"><v>1</v></c>')
        xml=(f'<worksheet xmlns="{ns}"><sheetData>'
             f'<row r="1">{headercells}</row>'
             f'<row r="2">{rowcells}</row>'
             f'</sheetData></worksheet>').encode()
        stream=io.BytesIO()
        with ZipFile(stream,"w") as z:
            z.writestr("xl/worksheets/sheet1.xml",xml)
        rows=list(_xlsx_named_rows(stream.getvalue(),headers))
        self.assertEqual(rows,[("2","2022","0","1")])

    def test_no_future_outcome_can_be_substituted_for_official_archive(self):
        with self.assertRaisesRegex(ValueError,"all four"):
            study({},self.issue)


if __name__=="__main__":
    unittest.main()
