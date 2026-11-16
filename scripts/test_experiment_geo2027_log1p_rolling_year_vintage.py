"""Leakage, chronology and nonindependent edition tests for rolling GEO H2."""
from __future__ import annotations

import copy
import json
import math
import unittest

from test_experiment_geo2027_intensity_markov_cross_release import sample
from audit_geo2027_log1p_shadow_issue import (
    ISSUE, MANIFEST, ORIGINAL, audit as audit_issue,
)
from experiment_geo2027_log1p_rolling_year_vintage import (
    ALPHAS, FIRST_OUTER_TARGET, LAST_TARGET, RIDGE,
    historical_ledger, fit_target, year_scores, year_ledger, study,
)


class RollingH2YearVintageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=sample()
        cls.ids=sorted(cls.original)

    def test_no_target_minus_one_or_future_label_in_coefficient_fit(self):
        original=copy.deepcopy(self.original)
        history=historical_ledger(original,2022,self.ids)
        beta,meta=fit_target(history,2019)
        altered=copy.deepcopy(original)
        for cid,h in altered.items():
            h[2018]=0 if cid%3 else 10000
            for y in range(2020,2026):
                h[y]=10000 if (cid+y)%3 else 0
        new_history=historical_ledger(altered,2022,self.ids)
        beta2,meta2=fit_target(new_history,2019)
        self.assertEqual(history[2019],new_history[2019])
        self.assertEqual(beta,beta2)
        self.assertEqual(meta,meta2)
        self.assertEqual(meta["max_supervised_training_label_year"],2017)
        self.assertEqual(meta["max_training_feature_year"],2015)
        self.assertEqual(meta["last_label_year_not_in_model"],2018)
        self.assertEqual(meta["forecast_origin_year"],2017)

    def test_changing_history_below_cutoff_changes_fitted_parameters(self):
        old=historical_ledger(self.original,2022,self.ids)
        modified=copy.deepcopy(self.original)
        for cid,h in modified.items():
            if cid%9==0:
                h[2014]=500 if h[2014]<25 else 0
        new=historical_ledger(modified,2022,self.ids)
        a,_=fit_target(old,2019)
        b,_=fit_target(new,2019)
        self.assertNotEqual(a,b)

    def test_all_years_fit_cutoffs_and_196_country_scores(self):
        ledger=historical_ledger(self.original,2022,self.ids)
        self.assertEqual(len(ledger),11)
        self.assertEqual(len(ledger[2017]),196)
        for target in range(FIRST_OUTER_TARGET,2023):
            beta,meta=fit_target(ledger,target)
            self.assertEqual(meta["forecast_origin_year"],target-2)
            self.assertEqual(meta["max_supervised_training_label_year"],target-2)
            self.assertEqual(meta["max_training_feature_year"],target-4)
            self.assertGreaterEqual(meta["training_n"],4*196)
            self.assertTrue(all(math.isfinite(x) for x in beta))
            metrics,baseline=year_scores(ledger[target],beta)
            self.assertEqual(len(metrics),5)
            self.assertTrue(all(0<x["brier"]<1 for x in metrics.values()))
            self.assertTrue(0<baseline["brier"]<1)

    def test_annual_replay_keeps_four_releases_correlated_not_independent(self):
        revisions={}
        for last,version in ((2022,"23.1"),(2023,"24.1"),
                             (2024,"25.1"),(2025,"26.1")):
            revisions[version]={
                cid:{year:deaths for year,deaths in h.items()
                     if year<=last}
                for cid,h in self.original.items()
            }
        report=year_ledger(revisions,self.ids)
        self.assertEqual(report["n_total_replayed_annual_year_edition_blocks"],30)
        self.assertEqual(report["n_distinct_target_years"],9)
        self.assertEqual(report["n_common_four_edition_years"],6)
        self.assertEqual(report["n_target_years_with_multi_edition_sign_reversal"],0)
        self.assertEqual([row["release_count"] for row in
                          report["same_year_different_edition"]],[4]*6+[3,2,1])
        self.assertEqual(
            [report["by_version"][v]["n_unique_annual_years"] for v in
             ("23.1","24.1","25.1","26.1")],[6,7,8,9])
        self.assertEqual(report["by_version"]["26.1"]["annual"][-1]["target_year"],2025)

    def test_archival_extra_countries_contribute_global_transition_prior(self):
        # Archive may include additional GWNOs not in original issued 196.
        # Keep full global training population, but only score the 196 fixed IDs.
        original=copy.deepcopy(self.original)
        base=historical_ledger(original,2022,self.ids)
        original[max(self.ids)+100]={
            year:(35 if year%3 else 0) for year in
            range(1989,2023)
        }
        changed=historical_ledger(original,2022,self.ids)
        self.assertEqual(len(changed[2019]),196)
        self.assertEqual(
            [r["country_id"] for r in changed[2019]],self.ids)
        self.assertTrue(any(
            a["p_original_binary"]!=b["p_original_binary"]
            for a,b in zip(base[2019],changed[2019])))
        self.assertEqual([r["outcome"] for r in base[2019]],
                         [r["outcome"] for r in changed[2019]])

    def test_empty_risk_cohort_fail_closed(self):
        bad=copy.deepcopy(self.original)
        bad.pop(self.ids[0])
        with self.assertRaisesRegex(ValueError,"196-country"):
            historical_ledger(bad,2022,self.ids)
        with self.assertRaises(ValueError):
            fit_target({},2019)

    def test_issued_2027_shadow_remains_unresolved_and_sha_protected(self):
        result=audit_issue(ISSUE.read_bytes(),MANIFEST.read_bytes(),
                           ORIGINAL.read_bytes())
        self.assertEqual(result["country_n"],196)
        self.assertEqual(result["future_2027_outcomes_resolved"],0)
        self.assertEqual(ALPHAS,(0.0,.25,.5,.75,1.0))
        self.assertEqual(RIDGE,5.0)

    def test_wrong_archival_or_first_issue_provenance_rejected(self):
        with self.assertRaisesRegex(ValueError,"provenance"):
            study({},self.ids,{"schema":"tampered"},{"schema":"tampered"})


if __name__=="__main__":
    unittest.main()
