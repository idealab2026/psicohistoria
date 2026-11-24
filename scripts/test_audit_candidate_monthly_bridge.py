import unittest
from datetime import date
from audit_candidate_monthly_bridge import union,counts,compare
class BridgeTest(unittest.TestCase):
    def test_revisions_before_filter(self):
        a=(2,1,1,5,date(2023,1,1),date(2023,1,1))
        b=(2,2,1,5,date(2023,1,1),date(2023,1,1))
        rows,stats=union([{"x":a},{"x":b}])
        self.assertEqual(counts(rows,2023,[2]),{2:0})
        self.assertEqual(stats,{"repeated_ids":1,"changed_representations":1})
    def test_quarter_end_exclusion(self):
        a=(2,1,1,5,date(2023,3,31),date(2023,4,1))
        self.assertEqual(counts({"x":a},2023,[2]),{2:0})
    def test_risk_membership(self):
        d=compare({2:0,3:5},{2:1,3:4})
        self.assertEqual(d["country_counts_changed"],2)
        self.assertEqual(d["risk_sets"]["5"]["changed_membership"],1)
if __name__=="__main__": unittest.main()
