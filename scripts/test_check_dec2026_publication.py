import unittest
from datetime import timedelta
from check_dec2026_publication import check,digest,ROOT
from experiment_annual_ged_rolling_probability import load,validate
import json
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rows=load();validate(rows)
        cls.ids={x[1] for x in rows}
        cls.raw=(ROOT/"data/forecast-dec2026-pilot.json").read_bytes()
        cls.receipt=json.loads((ROOT/"data/forecast-dec2026-pilot-manifest.json").read_text())
        cls.sources=json.loads((ROOT/"data/candidate-october-2026-source-observation.json").read_text())["source_manifest"]
    def test_actual(self):
        report=check(self.raw,self.receipt,self.ids,self.sources)
        self.assertEqual(report["eligible_country_scenarios"],1304)
        self.assertEqual(report["probability_values"],7824)
    def test_late_publication(self):
        with self.assertRaises(ValueError):
            check(self.raw,{**self.receipt,"document_published_at_utc":"2026-12-01T00:00:00Z"},self.ids,self.sources)
    def test_byte_change(self):
        with self.assertRaises(ValueError):
            check(self.raw+b" ",self.receipt,self.ids,self.sources)
    def test_claim_rejected(self):
        with self.assertRaises(ValueError):
            check(self.raw,{**self.receipt,"demonstrated_predictive_skill":True},self.ids,self.sources)
if __name__=="__main__": unittest.main()
