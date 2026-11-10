import unittest
from run_legacy_vintage_holdout import (records_for_study,experiment,score,
    grouped_bootstrap,load_sources,SOURCES,STUDIES)

class VintageCrossReleaseTests(unittest.TestCase):
    def make_dataset(self, first,last):
        return {(year,str(code)):int(code%40==0 and year%3==0)
                for year in range(first,last+1) for code in range(200,360)}

    def sources(self):
        return {
            "19.1":self.make_dataset(2000,2018),
            "23.1":self.make_dataset(2000,2022),
            "25.1":self.make_dataset(2000,2024),
        }

    def test_2019_origin_is_strictly_before_2020_2022_outcomes(self):
        src=self.sources()
        rows,training=records_for_study(src["19.1"],src["23.1"],2018,(2020,2021,2022))
        self.assertEqual(len(rows),480)
        self.assertEqual(training["training_country_years"],19*160)
        self.assertTrue(all(0<r["model"]<1 for r in rows))
        self.assertEqual({r["year"] for r in rows},{2020,2021,2022})

    def test_future_outcomes_cannot_change_training_probabilities(self):
        src=self.sources()
        a,_=records_for_study(src["19.1"],src["23.1"],2018,(2020,2021,2022))
        src["23.1"][(2020,"201")]=1
        b,_=records_for_study(src["19.1"],src["23.1"],2018,(2020,2021,2022))
        self.assertEqual([r["model"] for r in a],[r["model"] for r in b])
        self.assertNotEqual(score(a,"model")["brier"],score(b,"model")["brier"])

    def test_incomplete_origin_universe_fails_closed(self):
        src=self.sources()
        reduced={k:v for k,v in src["23.1"].items() if not (k[0]==2020 and int(k[1])>345)}
        with self.assertRaisesRegex(ValueError,"Insufficient covered"):
            records_for_study(src["19.1"],reduced,2018,(2020,2021,2022))
        with self.assertRaisesRegex(ValueError,"not beyond"):
            records_for_study(src["19.1"],src["23.1"],2018,(2018,))

    def test_official_sha_must_match_allowlisted_vintage(self):
        def fake(url,limit):return b"tampered"
        with self.assertRaisesRegex(ValueError,"Refused altered official edition"):
            load_sources(fake)

    def test_external_experiment_has_both_independent_vintages_and_no_claims(self):
        result=experiment(self.sources())
        self.assertEqual([s["origin_version"] for s in result["studies"]],["19.1","23.1"])
        self.assertEqual([r["year"] for s in result["studies"] for r in s["years"]],[2020,2021,2022,2024])
        self.assertEqual(result["aggregate"]["country_years"],640)
        self.assertFalse(result["historical_release_timing_cryptographically_verified"])
        self.assertEqual(result["prospective_predictions_issued"],0)
        self.assertFalse(result["operational_utility_demonstrated"])
        self.assertNotIn("predictions",result)
        self.assertNotIn("countries",result)
        self.assertTrue(result["aggregate"]["cluster_bootstrap"]["global"]["delta_brier_95pct_interval"][0] <= result["aggregate"]["cluster_bootstrap"]["global"]["delta_brier_95pct_interval"][1])

    def test_cluster_bootstrap_is_deterministic(self):
        src=self.sources()
        rows,_=records_for_study(src["19.1"],src["23.1"],2018,(2020,2021,2022))
        self.assertEqual(grouped_bootstrap(rows,replications=100,seed=14),
                         grouped_bootstrap(rows,replications=100,seed=14))

if __name__=="__main__":
    unittest.main()
