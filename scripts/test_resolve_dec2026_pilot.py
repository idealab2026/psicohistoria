import unittest,hashlib,io,zipfile
from datetime import datetime,timezone
from resolve_dec2026_pilot import gate,registry_entry,count_year,combine,evaluate,issuance
def utc(s): return datetime.fromisoformat(s+"T00:00:00+00:00")
def fixture(year,rows):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w") as z:
        z.writestr(f"GEDEvent_v{str(year+1)[-2:]}_1.csv","id,year,country_id,type_of_violence,date_prec,best,date_start,date_end\n"+"\n".join(rows)+"\n")
    raw=buf.getvalue();return raw,hashlib.sha256(raw).hexdigest()
class Tests(unittest.TestCase):
    def test_calendar_gate(self):
        for h in (30,90):
            with self.assertRaises(ValueError): gate(h,utc("2026-11-24"))
        gate(30,utc("2027-01-01"))
        with self.assertRaises(ValueError): gate(90,utc("2027-12-31"))
        gate(90,utc("2028-01-01"))
    def test_registry(self):
        m={"year":2026,"edition":"27.1","url":"https://ucdp.uu.se/downloads/ged/ged271-csv.zip","sha256":"a"*64,"review_commit":"b"*40,"status":"OFFICIAL_FIRST_EDITION_REVIEWED","evidence_url":"https://ucdp.uu.se/downloads/","observed_at_utc":"2027-06-01T00:00:00Z"}
        self.assertEqual(registry_entry(m,2026,utc("2027-06-02")),"27")
        for patch in ({"edition":"28.1"},{"observed_at_utc":"2026-12-31T00:00:00Z"},{"status":"UNREVIEWED"}):
            with self.assertRaises(ValueError): registry_entry({**m,**patch},2026,utc("2027-06-02"))
    def test_exact_window_and_revision_exclusion(self):
        a,sha=fixture(2026,["a,2026,1,1,1,5,2026-12-01,2026-12-01","b,2026,1,1,2,7,2026-12-30,2026-12-31","c,2026,1,2,1,30,2026-12-02,2026-12-02","d,2026,1,1,3,30,2026-12-02,2026-12-02","e,2026,1,1,1,30,2026-11-30,2026-12-01"])
        self.assertEqual(count_year(a,2026,{1,2},30,sha),({1:5,2:0},{"a"}))
        first=count_year(a,2026,{1,2},90,sha)
        b,bs=fixture(2027,["a,2026,1,1,1,999,2026-12-01,2026-12-01","f,2027,2,1,1,10,2027-02-28,2027-02-28","g,2027,2,1,1,50,2027-02-28,2027-03-01"])
        second=count_year(b,2027,{1,2},90,bs)
        self.assertEqual(combine([first,second],{1,2}),{1:12,2:10})
        with self.assertRaises(ValueError): combine([first,first],{1,2})
        with self.assertRaises(ValueError): count_year(a,2026,{1,2},30,"0"*64)
    def test_duplicate_and_future_coverage(self):
        row="a,2026,1,1,1,1,2026-12-01,2026-12-01"
        for rows in ([row,row],[row,"f,2027,1,1,1,1,2027-01-01,2027-01-01"]):
            raw,sha=fixture(2026,rows)
            with self.assertRaises(ValueError): count_year(raw,2026,{1},30,sha)
    def test_synthetic_labels_frozen_risk_sets(self):
        doc,ids=issuance()
        counts=dict.fromkeys(ids,0)
        for h in (30,90):
            result=evaluate(doc,counts,h)
            self.assertEqual([x["n"] for x in result],[155,162,164,171])
            self.assertTrue(all(x["positives"]==0 for x in result))
            for x in result:
                self.assertEqual(len(x["models"]),6)
                self.assertIsNone(x["models"]["global"]["alerts"]["5"]["recall"])
        with self.assertRaises(ValueError): evaluate(doc,{1:0},90)
if __name__=="__main__": unittest.main()
