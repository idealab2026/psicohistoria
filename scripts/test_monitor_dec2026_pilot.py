import unittest,hashlib
from datetime import date,datetime,timezone
from monitor_dec2026_pilot import verify_prefix,read_snapshot,progress,filename,version
from resolve_dec2026_pilot import issuance
HEADER="id,country_id,type_of_violence,date_prec,date_start,date_end,best\n"
def dt(s): return datetime.fromisoformat(s+"T00:00:00+00:00")
def entry(y,m,raw,observed):
    return {"year":y,"month":m,"version":version(y,m),"url":"https://ucdp.uu.se/downloads/candidateged/"+filename(y,m),"status":"OFFICIAL_MONTHLY_REVIEWED","evidence_url":"https://ucdp.uu.se/downloads/","sha256":hashlib.sha256(raw).hexdigest(),"review_commit":"a"*40,"observed_at_utc":observed+"T00:00:00Z"}
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc,cls.ids=issuance()
        cls.c=next(x["country_id"] for x in cls.doc["cells"][0]["countries"] if x["eligible"])
    def test_prefix_and_dates(self):
        d=entry(2026,12,b"x","2027-01-15")
        j=entry(2027,1,b"y","2027-02-15")
        self.assertEqual(verify_prefix([d,j],dt("2027-02-16")),date(2027,1,31))
        for e,now in (([d],dt("2026-12-31")),([j],dt("2027-02-16")),([d,d],dt("2027-02-16")),([d,j],dt("2027-02-01"))):
            with self.assertRaises(ValueError): verify_prefix(e,now)
    def test_source_bytes_month_and_clock(self):
        raw=(HEADER+f"a,{self.c},1,1,2026-12-10,2026-12-10,10\n").encode()
        m=entry(2026,12,raw,"2027-01-15")
        self.assertEqual(len(read_snapshot(raw,m)),1)
        with self.assertRaises(ValueError): read_snapshot(raw+b" ",m)
        with self.assertRaises(ValueError): read_snapshot(raw,entry(2027,1,raw,"2027-02-15"))
        later=(HEADER+f"a,{self.c},1,1,2026-12-10,2026-12-10,10\nb,{self.c},1,1,2027-01-15,2027-01-15,1\n").encode()
        with self.assertRaises(ValueError): read_snapshot(later,entry(2026,12,later,"2027-01-15"))
    def test_revision_and_horizon(self):
        c=self.c;d=date(2026,12,10);last=date(2026,12,31);j=date(2027,1,10)
        first={"a":(c,1,1,10,d,d),"b":(c,1,1,10,last,last),"outside":(c,2,1,100,d,d)}
        def status(report,t,h):
            cell=next(x for x in report["cells"] if (x["threshold"],x["horizon"])==(t,h))
            return next(x["status"] for x in cell["countries"] if x["country_id"]==c)
        a=progress(self.doc,self.ids,[first],last)
        self.assertEqual(status(a,10,30),"PROVISIONAL_THRESHOLD_RECORDED")
        self.assertEqual(status(a,25,90),"THRESHOLD_NOT_RECORDED")
        second={"a":(c,1,1,0,d,d),"j":(c,1,1,15,j,j)}
        b=progress(self.doc,self.ids,[first,second],date(2027,1,31))
        self.assertEqual(status(b,10,30),"THRESHOLD_NOT_RECORDED")
        self.assertEqual(status(b,25,90),"PROVISIONAL_THRESHOLD_RECORDED")
        self.assertEqual(b["outcomes_resolved"],0)
        self.assertFalse(b["scores_computed"])
        self.assertTrue(all(not x["resolved"] for cell in b["cells"] for x in cell["countries"]))
        self.assertEqual([x["n_eligible"] for x in b["cells"]],[155,155,162,162,164,164,171,171])
    def test_zero_records_not_negative_resolution(self):
        a=progress(self.doc,self.ids,[{}],date(2026,12,31))
        self.assertEqual(a["cells"][0]["threshold_not_recorded"],155)
        self.assertEqual(a["outcomes_resolved"],0)
        self.assertTrue(a["cells"][0]["window_calendar_complete"])
        self.assertFalse(a["cells"][1]["window_calendar_complete"])
        with self.assertRaises(ValueError): progress(self.doc,self.ids,[{}],date(2027,2,28))
if __name__=="__main__": unittest.main()
