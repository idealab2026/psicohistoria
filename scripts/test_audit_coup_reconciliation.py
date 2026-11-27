import unittest
from audit_coup_reconciliation import memberships,reconcile
HEADER="ccode,year,month,day,coup\n"
def span(c,a,b):
    return dict(zip(("ccode","styear","stmonth","stday","endyear","endmonth","endday"),(c,*a,*b)))
class Tests(unittest.TestCase):
    def test_partial_membership(self):
        states=[span(2,(1950,1,1),(1951,12,31)),span(3,(1950,7,1),(1950,12,31))]
        system=[{"ccode":c,"year":y} for c,y in [(2,1950),(2,1951),(3,1950)]]
        spans,keys,sets,d=memberships(states,system)
        self.assertEqual(d["any_day"]["rows"],3)
        self.assertEqual(d["jan1"]["rows"],2)
        self.assertEqual(d["entered_after_jan1"],1)
        raw=(HEADER+"2,1950,1,1,1\n3,1950,7,1,2\n3,1950,6,30,1\n2,1950,0,1,1\n4,1950,1,1,1\n").encode()
        out=reconcile(raw,spans,keys,sets)
        self.assertEqual(out["matched_unique_positive_country_years"],2)
        self.assertEqual(out["positive_years_entering_after_jan1"],1)
        self.assertEqual(out["event_diagnostics"]["unmatched_in_scope_rows"],3)
    def test_duplicate_and_gap(self):
        states=[span(2,(1950,1,1),(1950,2,1)),span(2,(1950,4,1),(1950,12,31))]
        spans,keys,sets,d=memberships(states,[{"ccode":2,"year":1950}])
        self.assertEqual(d["jan1_not_full_year"],1)
        raw=(HEADER+"2,1950,1,1,1\n2,1950,1,1,1\n2,1950,3,1,2\n").encode()
        x=reconcile(raw,spans,keys,sets)
        self.assertEqual(x["event_diagnostics"]["exact_duplicate_rows"],1)
        self.assertEqual(x["event_diagnostics"]["repeated_country_date"],1)
        self.assertEqual(x["event_diagnostics"]["date_outside_membership"],1)
        self.assertEqual(x["matched_unique_positive_country_years"],1)
if __name__=="__main__": unittest.main()
