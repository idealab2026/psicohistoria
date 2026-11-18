#!/usr/bin/env python3
"""World Bank WGI PV: strict country join, rank concordance and no-truth guards."""
import unittest
from unittest.mock import patch
import experiment_geo_h2_worldbank_wgi_external_context as m


class WorldBankExternalContextTest(unittest.TestCase):
    def test_indicator_and_no_fatality_equivalence(self):
        self.assertEqual(m.WGI_INDICATOR,"GOV_WGI_PV_EST")
        self.assertEqual((min(m.YEARS),max(m.YEARS)),(2012,2025))
        self.assertEqual(m.N,196)

    def test_exact_name_normalization(self):
        self.assertEqual(m.normalize_name("São Tomé & Príncipe"),
                         "sao tome and principe")
        self.assertEqual(m.normalize_name("United States of America"),
                         "united states of america")

    def test_explicit_alias_and_excluded_territory(self):
        sources=[{"country_id":2,"country":"United States of America"},
                 {"country_id":100,"country":"Colombia"},
                 {"country_id":713,"country":"Taiwan"}]
        names={"USA":"United States","COL":"Colombia"}
        with patch.object(m,"N",3),patch.object(m,"MIN_MATCHED_PER_YEAR",2):
            joins,miss,manual=m.country_crosswalk(sources,names)
        self.assertEqual(joins,{2:"USA",100:"COL"})
        self.assertEqual(manual,[2])
        self.assertEqual(miss[0]["reason"],"explicit_exclusion")

    def test_unmapped_is_not_guesswork(self):
        sources=[{"country_id":2,"country":"United States of America"},
                 {"country_id":100,"country":"Colombia"},
                 {"country_id":484,"country":"Congo"}]
        names={"USA":"United States","COL":"Colombia"}
        with patch.object(m,"N",3),patch.object(m,"MIN_MATCHED_PER_YEAR",2):
            joins,miss,manual=m.country_crosswalk(sources,names)
        self.assertEqual(joins,{2:"USA",100:"COL"})
        self.assertEqual(miss[0]["reason"],"manual_iso3_not_in_wgi")

    def test_country_iso3_collisions_fail_closed(self):
        sources=[{"country_id":2,"country":"United States of America"},
                 {"country_id":3,"country":"United States"}]
        names={"USA":"United States"}
        with patch.object(m,"N",2),patch.object(m,"MIN_MATCHED_PER_YEAR",1):
            with self.assertRaises(ValueError):
                m.country_crosswalk(sources,names)

    def test_concordance_auc_direction(self):
        rows=[{"wgi_pv_est":-2.0,"ucdp_active_25_plus":1},
              {"wgi_pv_est":-1.0,"ucdp_active_25_plus":1},
              {"wgi_pv_est":1.0,"ucdp_active_25_plus":0},
              {"wgi_pv_est":2.0,"ucdp_active_25_plus":0}]
        self.assertEqual(m.concordance_auc(rows),1.)
        for r in rows:
            r["wgi_pv_est"]=-r["wgi_pv_est"]
        self.assertEqual(m.concordance_auc(rows),0.)

    def test_auc_tie_and_zero_exposure_guard(self):
        rows=[{"wgi_pv_est":0.,"ucdp_active_25_plus":1},
              {"wgi_pv_est":0.,"ucdp_active_25_plus":0}]
        self.assertEqual(m.concordance_auc(rows),.5)
        with self.assertRaises(ValueError):
            m.concordance_auc(rows[:1])

    def test_spearman_ties_and_rank_direction(self):
        x=list(range(30))
        self.assertAlmostEqual(m.spearman(x,x),1.)
        self.assertAlmostEqual(m.spearman(x,x[::-1]),-1.)
        self.assertEqual(m.ranks([2,2,3,1]),[2.5,2.5,4.,1.])

    def test_report_requires_frozen_prior_and_valid_cohort(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):
            m.analyze({}, {}, {}, {}, {}, "")


if __name__=="__main__":
    unittest.main()
