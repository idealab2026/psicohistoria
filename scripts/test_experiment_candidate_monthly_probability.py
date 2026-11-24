import unittest
from experiment_candidate_monthly_probability import evaluate,validate_panel,YEARS
def panel():
    return [(y,c,0, int(c==1)*5,int(c<=2)*10) for y in YEARS for c in range(1,197)]
class Tests(unittest.TestCase):
    def test_folds_and_ablation(self):
        r=evaluate(panel())
        self.assertEqual(len(r["results"]),8)
        for row in r["results"]:
            a,b=row["folds"]
            self.assertEqual(a["train_years"],[2021])
            self.assertEqual(b["train_years"],[2021,2022,2023])
            self.assertEqual(b["without_2023"]["train_years"],[2021,2022])
            self.assertEqual(b["n_test"],196)
            self.assertEqual(row["n_test"],392)
    def test_test_year_labels_do_not_change_prior_fold(self):
        a=panel()
        b=[(y,c,q,999,999) if y==2025 else (y,c,q,u,v) for y,c,q,u,v in a]
        for x,y in zip(evaluate(a)["results"],evaluate(b)["results"]):
            self.assertEqual(x["folds"][0],y["folds"][0])
    def test_bad_panel(self):
        p=panel()
        with self.assertRaises(ValueError): validate_panel(p[:-1]+[p[0]])
if __name__=="__main__": unittest.main()
