import unittest
from experiment_fin01_vintage_extension import revisions,one_month
from experiment_fin01_monthly_downside import month_index

class VintageTests(unittest.TestCase):
    def test_revision(self):
        a={month_index("199001"):-.05,month_index("199002"):.01}
        b={month_index("199001"):-.049,month_index("199002"):.02}
        x=revisions(a,b)
        self.assertEqual(x["label_changes"],1)
        self.assertEqual(x["return_changes"],2)
    def test_cutoff(self):
        t=month_index("202509")
        with self.assertRaises(ValueError): one_month({t-1:0},{t:0},"202509")
    def test_valid(self):
        t=month_index("202509")
        train={j:0.01 for j in range(t-240,t-1)}
        x=one_month(train,{t:-.05},"202509")
        self.assertEqual(x["result"]["positives"],1)
        self.assertEqual(x["result"]["n"],1)
    def test_missing_overlap(self):
        with self.assertRaises(ValueError): revisions({1:.1},{2:.1})

if __name__=="__main__": unittest.main()
