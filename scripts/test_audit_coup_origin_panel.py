import unittest
from audit_coup_reconciliation import memberships
from audit_coup_origin_panel import panel
def span(c,a,b):
    return dict(zip(("ccode","styear","stmonth","stday","endyear","endmonth","endday"),(c,*a,*b)))
class Tests(unittest.TestCase):
    def test_origin_set_and_sensitivity(self):
        spans,keys,sets,_=memberships([span(2,(1950,1,1),(1950,6,30)),span(3,(1950,7,1),(1950,12,31)),span(4,(1950,1,1),(1950,6,30))],[{"ccode":c,"year":1950} for c in (2,3,4)])
        raw=b"ccode,year,month,day,coup\n2,1950,7,1,1\n3,1950,8,1,1\n4,1950,1,1,2\n4,1950,8,1,1\n"
        p,d=panel(raw,spans,keys,sets)
        self.assertEqual(p,[(1950,2,0,1),(1950,4,1,1)])
        self.assertEqual(d["date_mismatch_rows"],2)
        self.assertEqual(d["changed_binary_labels"],1)
    def test_duplicate_rejected(self):
        spans,keys,sets,_=memberships([span(2,(1950,1,1),(1950,12,31))],[{"ccode":2,"year":1950}])
        with self.assertRaises(ValueError): panel(b"ccode,year,month,day,coup\n2,1950,1,1,1\n2,1950,1,1,2\n",spans,keys,sets)
if __name__=="__main__": unittest.main()
