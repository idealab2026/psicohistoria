"""Mathematical synthetic tests; NO real or fabricated 2027 outcome records."""
import unittest

from diagnose_geo2027_alert_count_dependence import (
    convolve, describe, diagnose, frechet_zero_bounds, mixture, verify_issued,
)
from diagnose_newconf2027_event_count import (
    poisson_binomial, comonotonic_pmf,
)


class Geo2027AlertDependenceTests(unittest.TestCase):
    def test_independent_and_common_uniform_exact_two_bernoullis(self):
        p = [.2, .4]
        independent = poisson_binomial(p)
        common = comonotonic_pmf(p)
        for got, expected in (
            (independent, [.48,.44,.08]),
            (common, [.6,.2,.2]),
            (mixture(independent,common,.25), [.51,.38,.11]),
        ):
            self.assertEqual(len(got), 3)
            for a,b in zip(got,expected):
                self.assertAlmostEqual(a,b)
            self.assertAlmostEqual(sum(got),1)
            self.assertAlmostEqual(sum(k*mass for k,mass in enumerate(got)),.6)
        bounds = frechet_zero_bounds(p)
        self.assertAlmostEqual(bounds[0],0.4)
        self.assertAlmostEqual(bounds[1],0.6)

    def test_comonotonic_changes_no_marginal_or_mean(self):
        p = [.2]*10
        q = [.3]*5
        r = diagnose(p,q)
        self.assertEqual(r["outcomes_2027_observed"],0)
        self.assertFalse(r["forecast_probabilities_modified"])
        self.assertEqual(r["original_2027_alert_count"],15)
        for key,expected in (("entry",2),("resolution",1.5)):
            x=r["risk_groups"][key]
            self.assertAlmostEqual(x["expected_transitions_under_any_coupling"],expected)
            for scenario in x["dependence_mixture_scenarios"]:
                self.assertAlmostEqual(scenario["expected_transitions"],expected)
                self.assertAlmostEqual(sum(
                    scenario["full_probability_mass_by_count"]),1)
        j=r["joint_15_alerts"]
        self.assertAlmostEqual(j["expected_transitions_under_any_coupling"],3.5)
        for s in j["global_regime_mixtures"]:
            self.assertAlmostEqual(s["expected_transitions"],3.5)
        self.assertAlmostEqual(j["all_independent"]["p_zero"],
                               .8**10 * .7**5)
        self.assertAlmostEqual(j["single_common_uniform_all_15"]["p_zero"],.7)
        self.assertAlmostEqual(
            j["two_group_common_with_independent_group_shocks"]["p_zero"],
            .8 * .7,
        )
        self.assertEqual(j["frechet_p_zero_bounds"],[0,.7])

    def test_invalid_probabilities_and_mixture_refused(self):
        for bad in ([],[float("nan")],[float("inf")],[1.1],[-.1]):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    frechet_zero_bounds(bad)
        with self.assertRaises(ValueError):
            diagnose([.1]*9,[.2]*5)
        with self.assertRaises(ValueError):
            diagnose([.1]*10,[.2]*6)
        for w in (-.1,1.1,float("nan")):
            with self.subTest(weight=w):
                with self.assertRaises(ValueError):
                    mixture([.5,.5],[.4,.6],w)
        with self.assertRaises(ValueError):
            convolve([],[1])
        with self.assertRaises(ValueError):
            describe([.2,.5])

    def test_original_public_15_alerts_verified_from_sha(self):
        entry,resolution=verify_issued()
        self.assertEqual((len(entry),len(resolution)),(10,5))
        self.assertAlmostEqual(sum(entry),1.887984866833)
        self.assertAlmostEqual(sum(resolution),1.71585112391)
        result=diagnose(entry,resolution)
        self.assertEqual(result["outcomes_2027_observed"],0)
        self.assertTrue(
            result["joint_15_alerts"]["single_common_uniform_all_15"]["p_zero"]
            > result["joint_15_alerts"]["all_independent"]["p_zero"]
        )
        self.assertEqual(result["risk_groups"]["entry"]["n_alerts"],10)
        self.assertEqual(result["risk_groups"]["resolution"]["n_alerts"],5)
        for kind in ("entry","resolution"):
            x=result["risk_groups"][kind]
            self.assertAlmostEqual(sum(x["independent"][
                "full_probability_mass_by_count"]),1)
            self.assertAlmostEqual(sum(x["comonotonic_common_uniform"][
                "full_probability_mass_by_count"]),1)


if __name__=="__main__":
    unittest.main()
