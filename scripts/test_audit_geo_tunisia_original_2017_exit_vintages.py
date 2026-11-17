"""Synthetic chronology and state-boundary tests for Tunisia's 2017 exit case."""
from __future__ import annotations

import copy
import json
import math
import unittest

from audit_geo2027_global_only_matched_issue import ISSUE
from audit_geo_tunisia_original_2017_exit_vintages import (
    EARLY_ORIGIN,FROZEN_ORIGIN,GED_PATHS,GED_VERSIONS,
    ORIGINAL_ISSUED_COUNTRY_N,OBSERVED_TARGET,SYRIA,TUNISIA,
    _frozen_original_ids,historical_eligible_model,source_annual_counts,analyze,
)


def toy():
    orig=[*range(1,195),TUNISIA,SYRIA]
    cohort=[cid for cid in orig if cid!=SYRIA]
    support={cid:{y:0 for y in range(1989,2023)} for cid in orig}
    # Explicitly include a discontinued historical GWNO to emulate CY panel
    support[900]={y:0 for y in range(1989,2000)}
    counts={}
    for cid in [*orig,900]:
        for y in support[cid]:
            if cid==SYRIA:
                continue
            if (cid+y)%4==0:
                counts[(cid,y)]=35
    counts[(TUNISIA,2014)]=51
    counts[(TUNISIA,2015)]=75
    counts[(TUNISIA,2016)]=38
    counts[(TUNISIA,2017)]=0
    return counts,support,cohort


class TunisiaFirstExit2017Tests(unittest.TestCase):
    def test_only_2017_case_not_2024_case_or_future_2027(self):
        self.assertEqual((EARLY_ORIGIN,FROZEN_ORIGIN,OBSERVED_TARGET),
                         (2014,2016,2017))
        self.assertEqual(GED_VERSIONS,("17.1","18.1","19.1","20.1",
                                       "21.1","22.1","23.1"))
        self.assertEqual(GED_PATHS["17.1"],
                         "https://ucdp.uu.se/downloads/ged/ged171-csv.zip")
        self.assertEqual(GED_PATHS["18.1"],
                         "https://ucdp.uu.se/downloads/ged/ged181-csv.zip")
        issue=json.loads(ISSUE.read_text(encoding="utf8"))
        ids=_frozen_original_ids(issue)
        self.assertEqual(len(ids),ORIGINAL_ISSUED_COUNTRY_N)
        self.assertIn(TUNISIA,ids)
        with self.assertRaises(ValueError):
            manipulated=copy.deepcopy(issue)
            manipulated["official_2027_outcomes_resolved"]=196
            _frozen_original_ids(manipulated)

    def test_event_count_gives_observed_exit_10_only_given_2016_active(self):
        d={(TUNISIA,2016):37,(TUNISIA,2017):7}
        first=source_annual_counts(d,2016)
        second=source_annual_counts(d,2017)
        self.assertEqual((first["active_ge25"],second["active_ge25"]),(1,0))
        self.assertEqual(str(first["active_ge25"])+str(second["active_ge25"]),"10")
        d[(TUNISIA,2017)]=25
        self.assertEqual(source_annual_counts(d,2017)["active_ge25"],1)
        with self.assertRaises(ValueError):
            source_annual_counts({},2027)
        with self.assertRaises(ValueError):
            source_annual_counts({(TUNISIA,2017):-1},2017)

    def test_exit_probability_condition_is_not_initially_low_and_no_postorigin(self):
        ged,support,cohort=toy()
        out=historical_eligible_model(ged,support,cohort,2016)
        self.assertEqual(out["origin_binary_state"],1)
        self.assertEqual(out["training_year_max"],2016)
        self.assertAlmostEqual(
            out["Tunisia_p_exit_next_if_origin_active"],
            1-out["Tunisia_q_active"][1],places=11)
        # The formula for first exit at H3 is a different estimand from H1.
        early=historical_eligible_model(ged,support,cohort,2014)
        self.assertAlmostEqual(
            early["Tunisia_p_first_exit_exactly_origin_plus_3_if_initially_active"],
            early["Tunisia_q_active"][1]**2*(1-early["Tunisia_q_active"][1]),
            places=11)
        changed=copy.deepcopy(ged)
        changed[(1,2017)]=1000000
        changed[(TUNISIA,2017)]=1000000
        self.assertEqual(historical_eligible_model(changed,support,cohort,2016),out)

    def test_revision_of_2014_origin_state_makes_2017_first_exit_unidentified(self):
        ged,support,cohort=toy()
        initial=historical_eligible_model(ged,support,cohort,2014)
        changed=copy.deepcopy(ged)
        changed[(TUNISIA,2014)]=0
        low=historical_eligible_model(changed,support,cohort,2014)
        self.assertEqual(initial["origin_binary_state"],1)
        self.assertEqual(low["origin_binary_state"],0)
        self.assertIsNone(low[
            "Tunisia_p_first_exit_exactly_origin_plus_3_if_initially_active"])
        self.assertIsNone(low["Tunisia_p_exit_next_if_origin_active"])
        self.assertTrue(0<initial[
            "Tunisia_p_at_least_one_exit_within_3_if_initially_active"]<1)

    def test_exclude_documented_syria_source_territory_from_global_pool(self):
        ged,support,cohort=toy()
        old=historical_eligible_model(ged,support,cohort,2016)
        altered=copy.deepcopy(ged)
        for y in range(1989,2017):
            altered[(SYRIA,y)]=1_000_000
        self.assertEqual(old,historical_eligible_model(altered,support,cohort,2016))
        with self.assertRaisesRegex(ValueError,"Invalid fixed-source"):
            historical_eligible_model(ged,support,[*cohort,SYRIA],2016)
        with self.assertRaisesRegex(ValueError,"Invalid fixed-source"):
            historical_eligible_model(ged,support,cohort,2015)

    def test_fail_closed_impossible_official_archive_substitution(self):
        issue=json.loads(ISSUE.read_text(encoding="utf8"))
        with self.assertRaises(ValueError):
            analyze(issue,{}, {}, {}, {})


if __name__=="__main__":
    unittest.main()
