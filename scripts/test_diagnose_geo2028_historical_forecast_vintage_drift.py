"""Six ex-post archived edition pairs; ONLY synthetic tests (no 2027/28 labels)."""
from __future__ import annotations

import copy
import unittest

from backtest_archived_country_vintages import SOURCES
import diagnose_geo2028_historical_forecast_vintage_drift as s
from test_forecast_2027_statebased import toy


def synthetic():
    master,names=toy()
    vintages={}
    for version in s.VERSION_ORDER:
        cutoff=SOURCES[version]["last_year"]
        years={cid:{year:state for year,state in history.items()
                    if year<=cutoff}
               for cid,history in master.items()}
        if cutoff>=2023:
            years[3][2019]=1-years[3][2019]  # 23.1 -> 24.1 revised history
        if cutoff>=2024:
            years[8][2022]=1-years[8][2022]  # 24.1 -> 25.1 revision, fixed origin 2022
        if cutoff>=2025:
            years[20][2024]=1-years[20][2024] # 25.1 -> 26.1 revision, fixed origin 2024
        vintages[version]=years
    meta={
        version:{"sha256":SOURCES[version]["sha256"],
                 "last_year":SOURCES[version]["last_year"]}
        for version in s.VERSION_ORDER
    }
    rows,_=s._fit_at_origin(vintages["26.1"],2025)
    original27={
        "countries":[{
            "country_id":cid,
            "last_observed_state_2025":r["origin_state"],
            "p_model":r["p_model_h2"],
            "p_global_markov":r["p_global_markov_h2"],
            "p_baseline_global_5y":r["p_baseline_global_5y"],
        } for cid,r in sorted(rows.items())]
    }
    original28={
        "countries":[{
            "country_id":cid,"country":names[cid],
            "last_observed_state_2025":r["origin_state"],
            "p_model":r["p_model_h3"],
            "p_global_markov_3step":r["p_global_markov_h3"],
            "p_baseline_global_5y":r["p_baseline_global_5y"],
        } for cid,r in sorted(rows.items())]
    }
    return vintages,meta,original27,original28


class HistoricalFixedOriginForecastDriftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v,cls.m,cls.d27,cls.d28=synthetic()

    def test_original_2025_H2_H3_honored_and_six_source_pairs(self):
        d=s.study(self.v,self.m,self.d27,self.d28)
        self.assertEqual(len(d["historical_comparisons"]),6)
        self.assertTrue(d["fully_reconstructed_original_2025_H2_H3"][
            "2025_origin_H2_original_196_exact_model_and_reference_reproduced"])
        self.assertTrue(d["fully_reconstructed_original_2025_H2_H3"][
            "2025_origin_H3_original_196_exact_model_and_reference_reproduced"])
        self.assertEqual(d["n_independent_prospective_tests_contributed"],0)
        self.assertFalse(d["all_six_pairs_statistically_independent"])
        self.assertFalse(d["prospective_2027_2028_skill_demonstrated"])
        self.assertTrue(d["no_historical_2027_or_2028_target_outcomes_used"])
        self.assertFalse(d["country_probabilities_issued_in_2027_2028_changed"])
        self.assertEqual(d["fixed_origins"],[2022,2023,2024])
        self.assertEqual(d["horizons"],[2,3])
        self.assertEqual([x["origin_year_fixed"] for x in d["historical_comparisons"]],
                         [2022,2022,2022,2023,2023,2024])
        for fold in d["historical_comparisons"]:
            self.assertEqual(fold["original_risk_set_n"],196)
            self.assertEqual(fold["revised_risk_set_n"],196)
            self.assertTrue(fold["training_cutoff_exact"])
            self.assertEqual([v["country_count"] for v in fold["horizons"]],[196,196])
            self.assertEqual([v["target_calendar_year_if_issued_then"]
                              for v in fold["horizons"]],
                             [fold["origin_year_fixed"]+2,fold["origin_year_fixed"]+3])
            self.assertTrue(all(v["not_a_confidence_interval_or_skill_estimate"]
                                for v in fold["horizons"]))

    def test_exact_revisions_decompose_into_kernel_and_origin_state(self):
        d=s.study(self.v,self.m,self.d27,self.d28)
        by_key={(f["origin_year_fixed"],f["later_revision_edition"]):f
                for f in d["historical_comparisons"]}
        # Historical 2019 change in 24.1 changes global rates for multiple
        # countries, without changing any 2022 origin-year state.
        f=by_key[2022,"24.1"]
        self.assertEqual(f["fixed_origin_binary_reclassification"][
            "revised_binary_threshold_labels"],0)
        self.assertGreater(f["horizons"][1]["max_absolute_probability_change"],0)
        self.assertEqual(f["horizons"][1][
            "n_2025_or_historical_origin_state_reclassified"],0)
        self.assertEqual(f["horizons"][1]["mean_signed_origin_state_reclassification_component"],0)
        # Change 2022 state in 25.1: state component cannot be zero in H3.
        f=by_key[2022,"25.1"]
        self.assertEqual(f["fixed_origin_binary_reclassification"][
            "revised_binary_threshold_labels"],1)
        self.assertEqual(f["horizons"][1][
            "n_2025_or_historical_origin_state_reclassified"],1)
        row=next(r for r in f["horizons"][1]["largest_ten_named_probability_revisions"]
                 if r["country_id"]==8)
        self.assertNotEqual(row["origin_state_reclassification_component"],0)
        self.assertAlmostEqual(row["delta"],row["kernel_revision_component"]+
                               row["origin_state_reclassification_component"],places=10)
        f=by_key[2024,"26.1"]
        self.assertEqual(f["fixed_origin_binary_reclassification"][
            "revised_binary_threshold_labels"],1)
        self.assertTrue(any(r["country_id"]==20
                            for r in f["horizons"][1]["largest_ten_named_probability_revisions"]))

    def test_later_years_are_never_used_by_a_fixed_earlier_origin(self):
        old,_=s._fit_at_origin(self.v["26.1"],2022)
        revised=copy.deepcopy(self.v["26.1"])
        # Change 2023,2024,2025 completely: source future info must not leak.
        for h in revised.values():
            for y in (2023,2024,2025):
                h[y]=1-h[y]
        same,_=s._fit_at_origin(revised,2022)
        self.assertEqual(old,same)
        # H3 of 2022 is a prediction for 2025, not a score using actual 2025.
        base=s._compare(self.v,2022,"23.1","26.1",names={})
        edited=copy.deepcopy(self.v)
        edited["26.1"]=revised
        changed=s._compare(edited,2022,"23.1","26.1",names={})
        self.assertEqual(base,changed)

    def test_no_revision_means_exactly_zero_probability_drift_in_both_horizons(self):
        # A later edition may contain new target years but no historical
        # revisions: fixed-origin model must remain bitwise identical.
        original=copy.deepcopy(self.v)
        original["24.1"]={cid:{y:z for y,z in h.items() if y<=2023}
                          for cid,h in self.v["23.1"].items()}
        for cid,h in original["24.1"].items():
            h[2023]=self.v["24.1"][cid][2023]
        f=s._compare(original,2022,"23.1","24.1",names={})
        for h in f["horizons"]:
            self.assertEqual(h["max_absolute_probability_change"],0)
            self.assertEqual(h["n_changed_0_5_binary_decision"],0)
            self.assertEqual(h["n_probability_change_ge_1pp"],0)
            self.assertEqual(h["top20_overlap_with_GWNO_tie_break"],20)
        self.assertEqual(f["baseline_probability_revision"],0)

    def test_missing_origin_labels_and_corrupted_sha_fail_closed(self):
        modified=copy.deepcopy(self.v)
        del modified["26.1"][1][2024]
        with self.assertRaisesRegex(ValueError,"cohort not fully observed"):
            s._compare(modified,2024,"25.1","26.1",names={})
        changed=copy.deepcopy(self.m)
        changed["23.1"]["sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"SHA"):
            s.study(self.v,changed,self.d27,self.d28)
        changed=copy.deepcopy(self.d28)
        changed["countries"][0]["p_model"]+=.001
        with self.assertRaisesRegex(ValueError,"NOT reproduced"):
            s.study(self.v,self.m,self.d27,changed)
        changed=copy.deepcopy(self.d27)
        changed["countries"][0]["p_baseline_global_5y"]+=.001
        with self.assertRaisesRegex(ValueError,"NOT reproduced"):
            s.study(self.v,self.m,changed,self.d28)

    def test_rounded_components_are_exact_and_country_names_are_only_labels(self):
        d=s.study(self.v,self.m,self.d27,self.d28)
        for fold in d["historical_comparisons"]:
            for h in fold["horizons"]:
                for row in h["largest_ten_named_probability_revisions"]:
                    self.assertAlmostEqual(
                        row["delta"],row["kernel_revision_component"]+
                        row["origin_state_reclassification_component"],places=10)
                    self.assertTrue(row["country"].startswith("Test_Country_"))
                self.assertLessEqual(h["max_absolute_probability_change"],1)
                self.assertLessEqual(h["p95_absolute_probability_change"],1)
                self.assertEqual(h["country_count"],196)
                self.assertLessEqual(h["n_changed_0_5_binary_decision"],196)
        # These statistics are sensitivity to editorial vintages, not a
        # 2026-origin issue or any 2027/2028 validation.
        self.assertFalse(d["first_2025_origin_newer_27_1_available"])
        self.assertFalse(d["notarized_source_release_dates"])


if __name__=="__main__":
    unittest.main()
