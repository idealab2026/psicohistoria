import unittest
from experiment_annual_ged_rolling_probability import load, run, predict, validate, score, decompose_q1_gain
class Tests(unittest.TestCase):
    def test_actual(self):
        result=run(load())
        self.assertEqual(len(result["results"]),8)
        self.assertEqual(result["new_forecasts"],0)
        self.assertEqual(result["modified_prior_forecasts"],0)
        for row in result["results"]:
            self.assertEqual(len(row["folds"]),2)
            self.assertEqual([f["origin"] for f in row["folds"]],[2024,2025])
            self.assertTrue(all(f["train_years"]==[2021,2022] for f in row["folds"]))
    def test_class_attribution_conserves_gain(self):
        result=run(load())
        for row in result["results"]:
            parts=row["q1_brier_gain_by_outcome"]
            self.assertEqual(sum(x["n"] for x in parts.values()),row["n_test"])
            self.assertEqual(parts["positive"]["n"],row["positives"])
            gain=row["scores"]["global"]["brier"]-row["scores"]["q1_nonzero"]["brier"]
            self.assertAlmostEqual(sum(x["brier_gain_contribution"] for x in parts.values()),gain,places=8)
            if not row["positives"]:
                self.assertIsNone(parts["positive"]["q1_mean_probability"])
                self.assertEqual(parts["positive"]["brier_gain_contribution"],0)
        sample=decompose_q1_gain([(0.1,0.2,0.1),(0.1,0.2,0.1)],[0,1])
        self.assertLess(sample["negative"]["brier_gain_contribution"],0)
        self.assertGreater(sample["positive"]["brier_gain_contribution"],0)
    def test_future_label_rejected(self):
        for y in (2024,2025,2026):
            with self.assertRaises(ValueError):
                predict([(y,1,0,0,0)],[(2025,1,0,0,0)],2025,5,30)
    def test_test_outcomes_not_inputs(self):
        train=[(2021,1,0,5,5),(2022,1,1,0,0)]
        self.assertEqual(predict(train,[(2024,1,0,0,0)],2024,5,30),
                         predict(train,[(2024,1,0,999,999)],2024,5,30))
    def test_duplicate_rejected(self):
        rows=load()
        with self.assertRaises(ValueError):
            validate(rows[:-1]+[rows[0]])
    def test_invalid_probability_rejected(self):
        for p in (0,1,-0.1):
            with self.assertRaises(ValueError):
                score([p],[1])
if __name__=="__main__":
    unittest.main()
