import io
import zipfile
import unittest
from probe_ucdp_organized_vintages import discover,source_metadata,inspect

ARCHIVE_HTML="""<html><body>
<h2>UCDP Country-Year Dataset on Organized Violence within Country Borders</h2>
<p>version 25.1: <a href="/downloads/organizedviolencecy/organizedviolencecy-251-csv.zip">CSV</a> |
<a href="/downloads/organizedviolencecy/organizedviolencecy-251.xlsx">EXCEL</a> |
<a href="/downloads/organizedviolencecy/Codebook_251.pdf">Codebook</a></p>
<p>version 24.1: <a href="/downloads/organizedviolencecy/organizedviolencecy-241-csv.zip">CSV</a></p>
<p>version 23.1: <a href="/downloads/organizedviolencecy/organizedviolencecy-231.xlsx">EXCEL</a></p>
<h2>UCDP Violent Political Protest Dataset</h2>
<p>version 25.1: <a href="/downloads/other/irrelevant.csv">CSV</a></p></body></html>"""

def csv_data():
    return ("country_id,year,sb_total_deaths_best\n100,2022,25\n100,2023,0\n101,2022,7\n").encode()

def zipped_csv():
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,"w") as archive:
        archive.writestr("countryyear.csv",csv_data())
    return buffer.getvalue()

class UCDPArchiveProbe(unittest.TestCase):
    def test_discovers_archived_versions_only_from_correct_section(self):
        x=discover(ARCHIVE_HTML)
        self.assertEqual(list(sorted(x)),["23.1","24.1","25.1"])
        self.assertEqual([link["format"] for link in x["25.1"]],["CSV","EXCEL"])
        self.assertTrue(x["23.1"][0]["url"].endswith(".xlsx"))

    def test_country_year_csv_schema_and_uniqueness(self):
        r=source_metadata(csv_data(),"CSV")
        self.assertEqual(r["rows"],3)
        self.assertEqual(r["last_year"],2023)
        self.assertEqual(r["deaths_field"],"sb_total_deaths_best")
        self.assertEqual(source_metadata(zipped_csv(),"CSV")["format"],"CSV_ZIP")
        with self.assertRaisesRegex(ValueError,"duplication"):
            source_metadata(csv_data()+b"100,2023,7\n","CSV")

    def test_xlsx_accepted_as_provenance_pending_field_validation(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,"w") as z:
            z.writestr("xl/workbook.xml","<workbook/>")
            z.writestr("xl/worksheets/sheet1.xml",
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>country_id_cy</t></is></c>'
                '<c r="B1" t="inlineStr"><is><t>year_cy</t></is></c></row></sheetData></worksheet>')
        report=source_metadata(out.getvalue(),"EXCEL")
        self.assertEqual(report["format"],"XLSX")
        self.assertTrue(report["requires_column_validation"])
        self.assertEqual(report["country_id_field"],"country_id_cy")
        self.assertEqual(report["year_field"],"year_cy")

    def test_probe_never_claims_original_release_dates(self):
        expected={
            "https://ucdp.uu.se/downloads/olddw.html":ARCHIVE_HTML.encode(),
            "https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-251-csv.zip":zipped_csv(),
            "https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-241-csv.zip":zipped_csv(),
            "https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-231.xlsx":None,
        }
        def fake(url):
            if expected[url] is None:raise FileNotFoundError("old XLSX missing")
            return expected[url]
        v=inspect(fake)
        self.assertFalse(v["historical_availability_independently_certified"])
        self.assertEqual(v["versions"]["24.1"]["results"][0]["download_status"],"retrieved")
        self.assertEqual(v["versions"]["23.1"]["results"][0]["download_status"],"unavailable")

if __name__=="__main__":unittest.main()
