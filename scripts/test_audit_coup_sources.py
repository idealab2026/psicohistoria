import unittest,io,zipfile,json
from audit_coup_sources import csv_schema,xlsx_schema,doi_metadata
class Tests(unittest.TestCase):
    def test_csv(self):
        self.assertEqual(csv_schema(b"country,year,coup\nX,2025,1\n")["columns"],3)
        with self.assertRaises(ValueError): csv_schema(b"1,2025,1\n")
    def test_xlsx(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,"w") as z:
            z.writestr("xl/workbook.xml",'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="Test"/></sheets></workbook>')
            z.writestr("xl/worksheets/sheet1.xml","ignored")
        self.assertEqual(xlsx_schema(b.getvalue()),{"sheet_count":1,"worksheet_members":1})
    def test_doi(self):
        doi="10.13012/B2IDB-9651987_V10"
        d={"data":{"attributes":{"doi":doi,"types":{"resourceTypeGeneral":"Dataset"},"url":"https://databank.illinois.edu/datasets/IDB-example"}}}
        self.assertEqual(doi_metadata(json.dumps(d).encode(),doi)["doi"],doi)
        with self.assertRaises(ValueError): doi_metadata(json.dumps(d).encode(),doi+"x")
if __name__=="__main__": unittest.main()
