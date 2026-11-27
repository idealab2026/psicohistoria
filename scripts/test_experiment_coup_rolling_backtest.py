import unittest
from experiment_coup_rolling_backtest import forecast,flag,make_index,run,MODELS
class Tests(unittest.TestCase):
    def setUp(self):
        self.rows=[(y,c,int(c==1 and y%3==0)) for y in range(1950,1983) for c in range(1,26) if c!=25 or y>=1980]
    def test_no_future_labels(self):
        test,p=forecast(self.rows,1980)
        changed=[(y,c,1-v if y>=1979 else v) for y,c,v in self.rows]
        _,q=forecast(changed,1980)
        self.assertEqual(p,q)
        self.assertEqual(len(test),25)
        self.assertEqual(p[-1][1],p[-1][2])
        self.assertEqual(p[-1][1],p[-1][3])
    def test_feature_window(self):
        _,h=make_index([(1973,1,1),(1974,1,0),(1978,1,0),(1979,1,1)])
        self.assertEqual(flag(h,1,1980),0)
        self.assertIsNone(flag(h,2,1980))
    def test_aggregate(self):
        d=run(self.rows,(1980,1981,1982))
        self.assertEqual(d["n"],75)
        self.assertEqual(d["years"],3)
        self.assertEqual(set(d["models"]),set(MODELS))
        for m in MODELS:
            self.assertEqual(d["models"][m]["alerts"]["5"]["budget"],15)
if __name__=="__main__": unittest.main()
