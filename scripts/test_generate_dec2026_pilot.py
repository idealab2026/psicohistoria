import unittest
from datetime import datetime,timezone,date
from generate_dec2026_pilot import generate,time_gate,recent_features,OBS,DEADLINE
class Tests(unittest.TestCase):
    def test_dates(self):
        for t in (OBS,DEADLINE):
            with self.assertRaises(ValueError): time_gate(t)
        time_gate(datetime(2026,11,25,tzinfo=timezone.utc))
    def test_complete_and_excluded(self):
        panel=[(y,c,0,int(c==1)*5,int(c==1)*10) for y in (2021,2022,2023,2025) for c in range(1,197)]
        other={(x[0],x[1]):0 for x in panel}
        q=dict.fromkeys(range(1,197),0);q[1]=10
        o=dict.fromkeys(q,0)
        a=generate(panel,other,q,o,[])
        self.assertEqual(len(a["cells"]),8)
        for cell in a["cells"]:
            self.assertEqual(len(cell["countries"]),196)
            self.assertEqual(cell["target_end"],"2026-12-30" if cell["horizon"]==30 else "2027-02-28")
            row=cell["countries"][0]
            self.assertEqual(row["eligible"],cell["threshold"]>10)
            if not row["eligible"]: self.assertIsNone(row["probabilities"])
        b=generate([(y,c,z,999,999) if y==2025 else (y,c,z,u,v) for y,c,z,u,v in panel],other,q,o,[])
        self.assertEqual(a,b)
    def test_recent_boundary(self):
        x=date(2026,10,31)
        y=date(2026,11,1)
        q,o=recent_features({"a":(1,1,1,3,x,x),"b":(1,2,1,4,x,x),"c":(1,1,1,7,x,y)}, {1,2})
        self.assertEqual(q,{1:3,2:0});self.assertEqual(o,{1:4,2:0})
if __name__=="__main__": unittest.main()
