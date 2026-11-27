import unittest,io,zipfile
from audit_coup_membership import census_zip
def archive(text):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z: z.writestr("states.csv",text)
    return b.getvalue()
class Tests(unittest.TestCase):
    def test_state_year(self):
        raw=archive("ccode,year\n"+"".join(f"2,{y}\n" for y in range(1816,2025)))
        d=census_zip(raw,"System2024")
        self.assertEqual(d["benchmark_rows"],75)
        self.assertEqual(d["annual_membership"]["1950"],1)
    def test_duplicate(self):
        with self.assertRaises(ValueError): census_zip(archive("ccode,year\n2,2024\n2,2024\n"),"System2024")
    def test_intervals(self):
        raw=archive("ccode,styear,stmonth,stday,endyear,endmonth,endday\n2,1816,1,1,2024,12,31\n")
        self.assertEqual(census_zip(raw,"States2024")["rows"],1)
if __name__=="__main__": unittest.main()
