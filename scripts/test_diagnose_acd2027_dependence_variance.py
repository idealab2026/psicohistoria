"""Pure mathematical contracts: unknown country dependence and ACD2027 ranking."""
import copy
import math
import unittest

import build_2027_prospective_registry as issued
import diagnose_acd2027_dependence_variance as dependence


def testrow(cid,p,q,eb=None):
    return {"country_id":cid,
            "p_global_recent5":p,
            "p_lag1_group":q,
            "p_country_eb":q if eb is None else eb}


class DependenceVarianceTests(unittest.TestCase):
    def test_sharp_two_country_maximum_with_same_signed_coefficients(self):
        rows=[testrow(1,.4,.2),testrow(2,.4,.1)]
        c,a=dependence.pair_coefficients(rows,"p_lag1_group")
        r={1:.3,2:.6}
        atoms=dependence.signed_comonotonic_distribution(a,r,c)
        mean=sum(x["probability_mass"]*x["paired_brier_secondary_minus_primary"]
                 for x in atoms)
        var=sum(x["probability_mass"]*(
            x["paired_brier_secondary_minus_primary"]-mean)**2
            for x in atoms)
        indep=sum(a[i]**2*r[i]*(1-r[i]) for i in r)
        max_joint=min(r[1],r[2])
        expected=indep+2*a[1]*a[2]*(max_joint-r[1]*r[2])
        self.assertGreater(expected,indep)
        self.assertAlmostEqual(var,expected,places=14)
        self.assertAlmostEqual(sum(x["probability_mass"] for x in atoms),1)
        self.assertAlmostEqual(mean,c+sum(a[i]*r[i] for i in r))

    def test_sharp_two_country_maximum_with_opposite_signed_coefficients(self):
        rows=[testrow(1,.4,.2),testrow(2,.4,.7)]
        c,a=dependence.pair_coefficients(rows,"p_lag1_group")
        self.assertGreater(a[1],0)
        self.assertLess(a[2],0)
        r={1:.3,2:.6}
        atoms=dependence.signed_comonotonic_distribution(a,r,c)
        mean=sum(x["probability_mass"]*x["paired_brier_secondary_minus_primary"]
                 for x in atoms)
        var=sum(x["probability_mass"]*(
            x["paired_brier_secondary_minus_primary"]-mean)**2
            for x in atoms)
        indep=sum(a[i]**2*r[i]*(1-r[i]) for i in r)
        min_joint=max(0.,r[1]+r[2]-1.)
        expected=indep+2*a[1]*a[2]*(min_joint-r[1]*r[2])
        self.assertAlmostEqual(var,expected,places=14)
        self.assertGreater(var,indep)

    def test_perfectly_shared_world_has_32x_variance_if_equal_weights(self):
        # Same 32 Bernoulli marginals and identical signed score exposures.
        # Independent variance = 1/32 of common-shock variance.
        rows=[testrow(i,.6,.8) for i in range(1,33)]
        s=dependence.moment_report(rows,"p_lag1_group",dependence.PRIMARY)
        self.assertAlmostEqual(s["variance_amplification_vs_independence"],32)
        self.assertAlmostEqual(s["expected_paired_brier_secondary_minus_primary"],.04)
        self.assertAlmostEqual(
            s["max_variance_coupling_probability_primary_wins"]+
            s["max_variance_coupling_probability_secondary_wins"]+
            s["max_variance_coupling_probability_tie"],1)
        self.assertFalse(s["counterfactual_not_estimated_joint_probabilities"] is False)

    def test_independent_lag1_exact_probability_and_expected_mean(self):
        docs,manifests=issued.read_issued()
        rows=docs["acd"]["countries"]
        self.assertEqual(len(rows),32)
        for world in (dependence.PRIMARY,"p_lag1_group"):
            exact=dependence.independent_lag1_rank(rows,world)
            cases=exact["all_64_independent_hypothetical_cells"]
            self.assertEqual(len(cases),64)
            self.assertAlmostEqual(sum(c["probability_if_countries_independent"]
                                       for c in cases),1)
            expected=sum(c["probability_if_countries_independent"]*
                         c["paired_brier_secondary_minus_primary"]
                         for c in cases)
            stats=dependence.moment_report(rows,"p_lag1_group",world)
            self.assertAlmostEqual(
                expected,stats["expected_paired_brier_secondary_minus_primary"],
                places=12)
            self.assertGreaterEqual(
                stats["variance_amplification_vs_independence"],1-1e-10)

    def test_existing_issued_files_not_mutated_or_synthetic_future_injected(self):
        docs,manifests=issued.read_issued()
        report=dependence.diagnose(docs,manifests)
        self.assertEqual(report["2027_outcomes_used"],0)
        self.assertEqual(report["n_frozen_unique_country_endpoint_questions_all_2027"],424)
        self.assertFalse(report["decision_contract"]["actual_country_dependence_estimated"])
        self.assertTrue(report["decision_contract"]["a_single_year_2027_is_only_one_joint_country_panel"])
        for model in dependence.SECONDARIES:
            for scenario in report["models"][model][
                "scenarios_by_hypothetically_true_marginals"].values():
                self.assertAlmostEqual(
                    sum(atom["probability_mass"] for atom in
                        scenario["max_variance_coupling_atoms"]),1,places=12)
                self.assertGreaterEqual(
                    scenario["sharp_maximum_variance_given_exact_marginals"]+1e-12,
                    scenario["variance_if_independent_countries"])

    def test_invalid_cohort_world_probabilities_cannot_enter(self):
        rows=[testrow(1,.6,.8),testrow(2,.7,.9)]
        with self.assertRaisesRegex(ValueError,"incompatible"):
            dependence.signed_comonotonic_distribution({1:.2},{1:.7,2:.4},0.)
        for invalid in (0,1,float("nan"),float("inf"),True):
            bad=copy.deepcopy(rows)
            bad[0]["p_global_recent5"]=invalid
            with self.assertRaises(ValueError):
                dependence.moment_report(bad,"p_lag1_group",dependence.PRIMARY)
        with self.assertRaisesRegex(ValueError,"Hypothetical marginals"):
            dependence.moment_report(rows,"p_lag1_group","p_other")
        with self.assertRaisesRegex(ValueError,"Only original"):
            dependence.independent_lag1_rank(rows,dependence.PRIMARY)
        bad=copy.deepcopy(rows)
        bad[1]["country_id"]=1
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            dependence.pair_coefficients(bad,"p_lag1_group")


if __name__=="__main__":
    unittest.main()
