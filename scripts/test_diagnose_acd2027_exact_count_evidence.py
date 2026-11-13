"""Offline exact-combinatorial ACD prospective evidence frontier contracts."""
import copy
from itertools import combinations
import math
import unittest

import build_2027_prospective_registry as registry
import diagnose_acd2027_exact_count_evidence as evidence


def synthetic_rows():
    """Four distinguishable countries + 28 zero-gap countries."""
    rows=[]
    for cid,p,q in ((1,.85,.70),(2,.55,.90),(3,.20,.50),(4,.30,.10)):
        rows.append({"country_id":cid,"p_global_recent5":p,
                     "p_lag1_group":q,"p_country_eb":1-q})
    for cid in range(5,33):
        rows.append({"country_id":cid,"p_global_recent5":.6,
                     "p_lag1_group":.6,"p_country_eb":.6})
    return rows


class ExactCountEvidenceTests(unittest.TestCase):
    def test_all_33_count_bounds_exact_against_brute_force_core(self):
        rows=synthetic_rows()
        pad=set(range(5,33))
        for model in evidence.SECONDARIES:
            report=evidence.sharp_frontier(rows,model)
            self.assertEqual(len(report["k_conditioned_sharp_frontier"]),33)
            self.assertEqual(report["n_hypothetical_binary_outcome_assignments"],2**32)
            for case in report["k_conditioned_sharp_frontier"]:
                k=case["n_2027_countries_with_acd_record_hypothetical"]
                attainable=[]
                for t in range(max(0,k-len(pad)),min(4,k)+1):
                    padding=set(sorted(pad)[:k-t])
                    for combo in combinations((1,2,3,4),t):
                        attainable.append(evidence.compare_labels(
                            rows,model,set(combo)|padding))
                self.assertTrue(attainable)
                self.assertAlmostEqual(
                    case["sharp_min_secondary_minus_primary_brier"],
                    min(attainable),places=14)
                self.assertAlmostEqual(
                    case["sharp_max_secondary_minus_primary_brier"],
                    max(attainable),places=14)
                min_w=set(case["min_witness_recorded_country_gwno"])
                max_w=set(case["max_witness_recorded_country_gwno"])
                self.assertEqual(len(min_w),k)
                self.assertEqual(len(max_w),k)
                self.assertAlmostEqual(
                    evidence.compare_labels(rows,model,min_w),
                    min(attainable),places=14)
                self.assertAlmostEqual(
                    evidence.compare_labels(rows,model,max_w),
                    max(attainable),places=14)
            self.assertEqual(
                report["n_count_values_always_primary"]+
                report["n_count_values_always_secondary"]+
                report["n_count_values_assignment_matters"],33)
            self.assertAlmostEqual(
                report["conditional_expected_secondary_minus_primary_if_primary_true_marginals"],
                report["mean_squared_issued_probability_gap"])
            self.assertAlmostEqual(
                report["conditional_expected_secondary_minus_primary_if_secondary_true_marginals"],
                -report["mean_squared_issued_probability_gap"])
            self.assertEqual(
                report["k_conditioned_sharp_frontier"][0][
                    "sharp_min_secondary_minus_primary_brier"],
                report["k_conditioned_sharp_frontier"][0][
                    "sharp_max_secondary_minus_primary_brier"])

    def test_marginal_identity_requires_no_outcome_independence(self):
        # Perfect dependence: all 32 outcomes are simultaneously 0 or 1.
        # With marginal P(Y=1)=.6 for everyone, E(Brier(q)-Brier(p))
        # is still the sum of the row-wise expectations.
        rows=[{"country_id":cid,"p_global_recent5":.6,
               "p_lag1_group":.8,"p_country_eb":.4}
              for cid in range(1,33)]
        all_ids={r["country_id"] for r in rows}
        conditional=evidence.sharp_frontier(rows,"p_lag1_group")
        expected=.6*evidence.compare_labels(rows,"p_lag1_group",all_ids)+(
            .4*evidence.compare_labels(rows,"p_lag1_group",set()))
        self.assertAlmostEqual(expected,conditional[
            "conditional_expected_secondary_minus_primary_if_primary_true_marginals"])
        self.assertAlmostEqual(expected,.04)

    def test_refuse_missing_duplicate_invalid_and_wrong_comparator(self):
        rows=synthetic_rows()
        for bad in (
            rows[:-1],
            rows[:-1]+[copy.deepcopy(rows[0])],
        ):
            with self.assertRaises(ValueError):
                evidence.sharp_frontier(bad,"p_lag1_group")
        bad=copy.deepcopy(rows)
        bad[2]["p_lag1_group"]=float("nan")
        with self.assertRaisesRegex(ValueError,"probability"):
            evidence.sharp_frontier(bad,"p_lag1_group")
        bad=copy.deepcopy(rows)
        bad[2]["p_global_recent5"]=1
        with self.assertRaisesRegex(ValueError,"probability"):
            evidence.sharp_frontier(bad,"p_lag1_group")
        bad=copy.deepcopy(rows)
        bad[2]["country_id"]=True
        with self.assertRaises(ValueError):
            evidence.sharp_frontier(bad,"p_country_eb")
        with self.assertRaisesRegex(ValueError,"Unregistered"):
            evidence.sharp_frontier(rows,"p_overfit")
        with self.assertRaisesRegex(ValueError,"witness"):
            evidence.compare_labels(rows,"p_lag1_group",{9000})
        with self.assertRaisesRegex(ValueError,"witness"):
            evidence.compare_labels(rows,"p_lag1_group",[])

    def test_first_issued_2027_sha_and_424_records_remain_unobserved(self):
        docs,manifests=registry.read_issued()
        out=evidence.diagnose(docs,manifests)
        self.assertEqual(out["2027_labels_used"],0)
        self.assertEqual(out["n_issued_country_questions"],32)
        self.assertEqual(out["n_issued_country_endpoint_questions_all_cohorts_unchanged"],424)
        self.assertEqual(out["source_acd_first_issue_sha256"],registry.EXPECTED["acd"][1])
        self.assertTrue(out["decision_contract"][
            "single_2027_calendar_year_cannot_establish_independent_generalizable_skill"])
        self.assertTrue(out["decision_contract"][
            "no_automatic_model_switch_or_reissue_based_on_any_2027_result"])
        lag=out["sharp_outcome_count_envelopes"]["p_lag1_group"]
        self.assertGreater(lag["largest_single_country_share_of_sum_squared_probability_gaps"],.96)
        self.assertEqual(lag["five_largest_probability_gap_country_gwno"][0],626)

    def test_rejects_tampered_unobserved_issue(self):
        docs,manifests=registry.read_issued()
        d=copy.deepcopy(docs)
        d["acd"]["2027_outcomes_resolved"]=1
        with self.assertRaises(ValueError):
            evidence.diagnose(d,manifests)
        d=copy.deepcopy(docs)
        d["acd"]["primary_model"]="p_lag1_group"
        with self.assertRaises(ValueError):
            evidence.diagnose(d,manifests)


if __name__=="__main__":
    unittest.main()
