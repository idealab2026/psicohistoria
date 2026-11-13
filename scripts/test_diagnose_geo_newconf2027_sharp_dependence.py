"""Offline exact GEO / NEWCONF dependence-variance, without future labels."""
import copy
import math
import unittest

import build_2027_prospective_registry as issued
import diagnose_geo_newconf2027_sharp_dependence as study


def row(cid,p,q):
    return {"country_id":cid,"p_primary":p,"p_comparator":q}


class CrossEndpointDependenceTests(unittest.TestCase):
    def test_two_country_frechet_max_exact_for_opposing_coefficients(self):
        # Opposite signs require negative correlation between raw Y, while
        # their SIGNED score terms are positively dependent.
        rows=[row(1,.4,.2),row(2,.4,.7)]
        r=.4
        out=study.paired_moments(rows,"primary")
        a1=-2*(.2-.4)/2
        a2=-2*(.7-.4)/2
        v_indep=(a1*a1+a2*a2)*r*(1-r)
        cov_min=max(0,2*r-1)-r*r
        v_max=v_indep+2*a1*a2*cov_min
        self.assertAlmostEqual(out["variance_under_independent_bernoulli_countries"],v_indep,places=13)
        self.assertAlmostEqual(out["sharp_max_variance_under_arbitrary_joint_bernoulli_dependence"],v_max,places=13)
        self.assertGreater(v_max,v_indep)
        self.assertTrue(out["sharp_max_standard_deviation"]>=out["standard_deviation_if_independent"])
        self.assertAlmostEqual(
            out["max_variance_coupling_primary_win_probability_conditional_only"]+
            out["max_variance_coupling_comparator_win_probability_conditional_only"]+
            out["max_variance_coupling_tie_probability_conditional_only"],1)

    def test_perfect_shared_shock_increases_variance_by_exact_factor_n(self):
        rows=[row(i,.6,.8) for i in range(1,197)]
        for world in ("primary","comparator"):
            m=study.paired_moments(rows,world)
            self.assertAlmostEqual(m["variance_multiplier_over_independence"],196,places=8)
            self.assertAlmostEqual(m["mean_paired_brier_comparator_minus_primary"],
                                   .04 if world=="primary" else -.04,places=11)

    def test_no_score_if_all_issued_models_equal(self):
        rows=[row(i,.25,.25) for i in range(1,197)]
        m=study.paired_moments(rows,"primary")
        self.assertAlmostEqual(m["mean_paired_brier_comparator_minus_primary"],0)
        self.assertAlmostEqual(m["sharp_max_variance_under_arbitrary_joint_bernoulli_dependence"],0)
        self.assertIsNone(m["variance_multiplier_over_independence"])
        self.assertAlmostEqual(m["max_variance_coupling_tie_probability_conditional_only"],1)

    def test_source_issued_endpoint_forecast_contract(self):
        docs,manifests=issued.read_issued()
        all_rows=issued.make_registry(docs,manifests)
        result=study.analyze(docs,manifests)
        self.assertEqual(all_rows["n_unique_country_endpoint_rows"],424)
        self.assertEqual(result["original_2027_labels_observed"],0)
        self.assertEqual(result["n_distinct_endpoints_analyzed"],2)
        self.assertTrue(result["GEO_and_NEWCONF_scores_not_pooled_or_compared_across_endpoints"])
        self.assertTrue(result["underlying_country_years_overlap_across_endpoints"])
        self.assertEqual(set(result["per_endpoint"]),{"GEO2027","NEWCONF2027"})
        self.assertEqual(set(result["per_endpoint"]["GEO2027"]["comparisons"]),
                         {"p_global_markov","p_shadow_exploratorio",
                          "p_baseline_global_5y_archival_diagnostic_only"})
        self.assertEqual(set(result["per_endpoint"]["NEWCONF2027"]["comparisons"]),
                         {"p_baseline_global_5y"})
        for key,cohort in result["per_endpoint"].items():
            self.assertEqual(cohort["n_original_issued_country_questions"],196)
            for name,entry in cohort["comparisons"].items():
                self.assertEqual(entry["n_same_endpoint_issued_country_questions"],196)
                self.assertEqual(entry["hypothetical_marginal_worlds"].keys(),
                                 {"primary","comparator"})
                self.assertTrue(
                    entry["archival_only_not_issued_as_registered_comparator"]==
                    name.endswith("_archival_diagnostic_only"))
                w0=entry["hypothetical_marginal_worlds"]["primary"]
                w1=entry["hypothetical_marginal_worlds"]["comparator"]
                self.assertAlmostEqual(
                    w0["mean_paired_brier_comparator_minus_primary"],
                    -w1["mean_paired_brier_comparator_minus_primary"],places=11)
                for w in (w0,w1):
                    self.assertEqual(w["2027_outcomes_used"],0)
                    self.assertGreaterEqual(
                        w["sharp_max_variance_under_arbitrary_joint_bernoulli_dependence"]+1e-11,
                        w["variance_under_independent_bernoulli_countries"])

    def test_reject_tampered_registry_or_unrecognized_world_and_bad_gwno(self):
        docs,manifests=issued.read_issued()
        altered=copy.deepcopy(docs)
        altered["newconf"]["target"]["year"]=2028
        with self.assertRaises(ValueError):
            study.analyze(altered,manifests)
        with self.assertRaisesRegex(ValueError,"truth-world"):
            study.paired_moments([row(1,.4,.2),row(2,.4,.2)],"actual")
        for bad in (
            [row(1,.5,.2),row(1,.5,.2)],
            [row(1,.5,.2),row(True,.5,.2)],
            [row(1,.5,float("nan")),row(2,.5,.4)],
            [row(1,.5,1.0),row(2,.5,.4)],
        ):
            with self.assertRaises(ValueError):
                study.paired_moments(bad,"primary")
        with self.assertRaisesRegex(ValueError,"panel"):
            study.paired_moments([],"primary")


if __name__=="__main__":
    unittest.main()
