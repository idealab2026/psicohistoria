"""Adversarial synthetic vintage revisions, never simulated 2027 outcomes."""
from __future__ import annotations

import copy
import unittest

from backtest_archived_country_vintages import SOURCES
from diagnose_geo2027_ucdp_vintage_revisions import (
    PAIR_RELEASES, VERSIONS, FOCUS_YEARS, diagnose, drift,
    threshold_scores, validate_records,
)


def synthetic_archives():
    editions={}
    for version in VERSIONS:
        cutoff=SOURCES[version]["last_year"]
        editions[version]={
            cid:{year:0 for year in range(1989,cutoff+1)}
            for cid in range(1,197)
        }
        for cid in range(1,197):
            for year in range(1989,cutoff+1):
                editions[version][cid][year]=int(cid<=37)
        if cutoff>=2024:
            for cid in editions[version]:
                editions[version][cid][2024]=int(cid<=31 or 38<=cid<=41)
        if cutoff>=2025:
            for cid in editions[version]:
                editions[version][cid][2025]=int(cid<=34)
    # Historical threshold reclassification, NOT an actual geopolitical event.
    editions["24.1"][10][2022]=0
    editions["25.1"][10][2022]=0
    editions["26.1"][10][2022]=0
    editions["25.1"][11][2023]=0
    editions["26.1"][11][2023]=0
    # Later 2024 vintage changes three actual country labels in a fixed cohort.
    editions["26.1"][40][2024]=0
    editions["26.1"][50][2024]=1
    editions["26.1"][30][2024]=0
    metadata={version:{"sha256":SOURCES[version]["sha256"]}
              for version in VERSIONS}
    holdout=[]
    for year in (2024,2025):
        origin_version="23.1" if year==2024 else "24.1"
        target_version="25.1" if year==2024 else "26.1"
        for cid in range(1,197):
            origin=editions[origin_version][cid][year-2]
            holdout.append({
                "country_id":cid,
                "target_year":year,
                "origin_state":origin,
                "outcome":editions[target_version][cid][year],
                "p_model":.80 if origin==1 else .05+cid/10000,
                "p_global_markov":.72 if origin==1 else .08,
            })
    assert sum(r["outcome"] for r in holdout)==69
    return editions,metadata,holdout


class UCDPVintageRevisionsTests(unittest.TestCase):
    def test_annual_relabelled_countries_can_preserve_total_event_count(self):
        editions,_,holdout=synthetic_archives()
        ids=list(range(1,197))
        result=drift(editions["25.1"],editions["26.1"],year=2024,cohort=ids)
        self.assertEqual(result["common_country_years"],196)
        self.assertEqual(result["revised_binary_threshold_labels"],3)
        self.assertEqual(result["changed_inactive_to_active"],1)
        self.assertEqual(result["changed_active_to_inactive"],2)
        self.assertEqual(result["later_minus_earlier_active_count_on_common_pairs"],-1)
        self.assertEqual(result["missing_in_later"],0)
        self.assertEqual(result["missing_in_earlier"],0)
        panel=threshold_scores([r for r in holdout if r["target_year"]==2024],{
            cid:editions["26.1"][cid][2024] for cid in ids})
        self.assertEqual(panel["0"]["transitions_from_2022_origin_first_25_1"],4)
        self.assertEqual(panel["0"]["transitions_from_2022_origin_revised_26_1"],4)
        self.assertEqual(panel["1"]["transitions_from_2022_origin_first_25_1"],6)
        self.assertEqual(panel["1"]["transitions_from_2022_origin_revised_26_1"],7)
        self.assertEqual(panel["0"]["country_year_label_changes_first_to_revised"],2)
        self.assertEqual(panel["1"]["country_year_label_changes_first_to_revised"],1)
        self.assertNotEqual(panel["0"]["scoring_identical_frozen_country_probabilities"][
            "p_model"]["delta_brier_revised_minus_first"],0)

    def test_full_four_edition_audit_fails_closed_on_source_change(self):
        sources,meta,rows=synthetic_archives()
        result=diagnose(sources,meta,rows)
        self.assertEqual(result["2024_196_country_original_holdout_later_label_revision"][
            "revised_binary_threshold_labels"],3)
        self.assertEqual(len(result["pairwise_revisions_all_years_and_recent_years"]),
                         len(PAIR_RELEASES))
        self.assertIsNone(result["2025_later_revision_diagnostic"])
        self.assertEqual(result["cross_country_dependence_identification"][
            "maximum_empirical_centered_covariance_rank_with_two_annual_blocks"],1)
        self.assertEqual(result["cross_country_dependence_identification"][
            "unrestricted_pairwise_cross_country_covariances"],19110)
        self.assertFalse(result["cross_country_dependence_identification"][
            "actual_rank_or_correlations_estimated"])
        self.assertFalse(result["prospective_skill_or_independent_dependence_estimated"])
        self.assertFalse(result["original_forecast_modified"])
        self.assertFalse(result["original_shadow_modified"])
        self.assertEqual(result["prospective_2027_outcomes_observed"],0)
        changed=copy.deepcopy(meta)
        changed["25.1"]["sha256"]="corrupted"
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            diagnose(sources,changed,rows)
        damaged=copy.deepcopy(rows)
        damaged.pop()
        with self.assertRaisesRegex(ValueError,"published 2024/25 separated holdout"):
            diagnose(sources,meta,damaged)

    def test_missing_later_label_not_assumed_zero(self):
        old={1:{2024:1},2:{2024:0},3:{2024:1}}
        new={1:{2024:1},2:{2024:1}}
        x=drift(old,new,year=2024,cohort=[1,2,3])
        self.assertEqual(x["common_country_years"],2)
        self.assertEqual(x["missing_in_later"],1)
        self.assertEqual(x["changed_inactive_to_active"],1)
        self.assertEqual(x["revised_binary_threshold_labels"],1)
        self.assertEqual(x["same_inactive"],0)
        self.assertTrue(x["unresolved_later_labels_never_imputed_inactive"])

    def test_invalid_and_duplicate_country_cohorts_rejected(self):
        sources,_,_=synthetic_archives()
        for invalid in ({0:{2024:1}}, {3:{2024:None}}, {3:{2026:1}},
                        {3:{2024:2}}, {3:{2024:True}}):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    validate_records(invalid)
        with self.assertRaisesRegex(ValueError,"Non-unique"):
            drift(sources["25.1"],sources["26.1"],year=2024,cohort=[1,1])
        with self.assertRaisesRegex(ValueError,"Unexpected"):
            drift(sources["25.1"],sources["26.1"],year=2027)
        later={cid:years[2024] for cid,years in sources["26.1"].items()}
        later.pop(100)
        _,_,rows=synthetic_archives()
        with self.assertRaisesRegex(ValueError,"missing"):
            threshold_scores([r for r in rows if r["target_year"]==2024],later)

    def test_historical_revision_not_a_country_transition(self):
        sources,_,_=synthetic_archives()
        x=drift(sources["23.1"],sources["24.1"],year=2022)
        self.assertEqual(x["revised_binary_threshold_labels"],1)
        self.assertEqual(x["changed_active_to_inactive"],1)
        self.assertEqual(x["changed_inactive_to_active"],0)
        self.assertEqual(x["specified_year"],2022)


if __name__=="__main__":
    unittest.main()
