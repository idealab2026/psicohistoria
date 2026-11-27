import copy
import json
import unittest
from datetime import datetime, timezone
from resolve_coup2027_contract import evaluate,digest,ENDPOINT

def raw(x): return json.dumps(x,sort_keys=True).encode()

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.roster=set(range(1,196))
        self.now=datetime(2028,4,1,tzinfo=timezone.utc)
        self.pub="2026-12-20T12:00:00Z"
        self.source=b"synthetic source bytes, not real data"
        self.issue={"target_year":2027,"endpoint":ENDPOINT,"training_last_year":2025,
                    "roster_snapshot":"2024-12-31","issued_at_utc":"2026-12-20T11:00:00Z",
                    "rows":[{"ccode":c,"probabilities":{"global_recent":.1,
                    "country_constrained":.2,"prior5_constrained":.05}} for c in sorted(self.roster)]}
        self.outcome={"endpoint":ENDPOINT,"released_at_utc":"2028-03-10T00:00:00Z",
                      "retrieved_at_utc":"2028-03-11T00:00:00Z","coverage_through":"2027-12-31",
                      "complete_coverage_reviewed":True,"first_eligible_release_reviewed":True,
                      "source_sha256":digest(self.source),
                      "rows":[{"ccode":c,"label":0} for c in sorted(self.roster)]}
    def run_contract(self,sha=None):
        a,b=raw(self.issue),raw(self.outcome)
        return evaluate(a,sha or digest(a),self.roster,self.pub,b,digest(b),self.now,self.source)
    def test_complete(self):
        r=self.run_contract()
        self.assertEqual(r["status"],"COMPLETE_COHORT_SCORES")
        self.assertAlmostEqual(r["models"]["prior5_constrained"]["brier"],.0025)
        self.assertAlmostEqual(r["models"]["prior5_constrained"]["brier_gain_bounds"][0],.0075)
    def test_missing_not_zero(self):
        self.outcome["rows"][0]["label"]=None
        r=self.run_contract()
        self.assertEqual(r["unknown"],1)
        self.assertIsNone(r["models"]["prior5_constrained"]["brier"])
        a,b=r["models"]["prior5_constrained"]["brier_gain_bounds"]
        self.assertLess(a,b)
        for label in (0,1):
            self.outcome["rows"][0]["label"]=label
            z=self.run_contract()["models"]["prior5_constrained"]["brier_gain_bounds"][0]
            self.assertTrue(a-1e-12<=z<=b+1e-12)
    def test_before_resolution_window(self):
        self.now=datetime(2028,2,28,tzinfo=timezone.utc)
        with self.assertRaises(ValueError): self.run_contract()
    def test_late_publication(self):
        self.pub="2027-01-01T00:00:00Z"
        with self.assertRaises(ValueError): self.run_contract()
    def test_digest(self):
        with self.assertRaises(ValueError): self.run_contract("0"*64)
    def test_missing_roster(self):
        self.outcome["rows"].pop()
        with self.assertRaises(ValueError): self.run_contract()
    def test_unreviewed(self):
        self.outcome["complete_coverage_reviewed"]=False
        with self.assertRaises(ValueError): self.run_contract()
    def test_bad_source_hash(self):
        self.outcome["source_sha256"]="0"*64
        with self.assertRaises(ValueError): self.run_contract()
    def test_boolean_label(self):
        self.outcome["rows"][0]["label"]=True
        with self.assertRaises(ValueError): self.run_contract()
    def test_future_retrieval(self):
        self.outcome["retrieved_at_utc"]="2028-04-02T00:00:00Z"
        with self.assertRaises(ValueError): self.run_contract()

if __name__=="__main__":
    unittest.main()
