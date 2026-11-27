import unittest
from audit_coup_source_vintage_bridge import records,compare,integral

class BridgeTests(unittest.TestCase):
    def test_outcome_revision_not_binary_revision(self):
        x=compare({(2025,1,1,1,1)},{(2025,1,1,1,2)})
        self.assertEqual(x["event_records_added_or_changed"],1)
        self.assertEqual(x["event_records_removed_or_changed"],1)
        self.assertEqual(x["positive_country_years_added"],0)
        self.assertEqual(x["positive_country_years_removed"],0)
    def test_code_revision(self):
        x=compare({(2025,1,1,1,1)},{(2025,2,1,1,1)})
        self.assertEqual(x["positive_country_years_added"],1)
        self.assertEqual(x["positive_country_years_removed"],1)
    def test_year_gate(self):
        a=records([["ccode","year","month","day","coup"],["1","2025","1","1","2"],["","2026","","",""]])
        self.assertEqual(a,{(2025,1,1,1,2)})
    def test_duplicate(self):
        row=["1","2025","1","1","2"]
        with self.assertRaises(ValueError):
            records([["ccode","year","month","day","coup"],row,row])
    def test_integral(self):
        self.assertEqual(integral("1.0"),1)
        with self.assertRaises(ValueError): integral("1.5")

if __name__=="__main__":
    unittest.main()
