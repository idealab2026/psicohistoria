"""Pure offline tests for prospective-cohort support and historical temporal slices."""
import copy
import unittest

import diagnose_acd2027_historical_transferability as transfer


def row(cid,year,y,global_p=.8,lag=.7,eb=.6):
    return {"country_id":cid,"target_year":year,"observed_acd":y,
            "models":{"p_global_recent5":global_p,"p_lag1_group":lag,
                      "p_country_eb":eb}}


def fixed_synthetic_137():
    """42 countries, 137 rows, 116 positives, 4 annual targets."""
    rows=[]
    for cid in range(1,43):
        n=4 if cid<=26 else 3 if cid<=32 else 2 if cid<=37 else 1
        for j in range(n):
            y=int(len(rows)>=21)
            rows.append(row(cid,2021+j,y,lag=.7 if cid%2 else .9))
    assert len(rows)==137 and sum(r["observed_acd"] for r in rows)==116
    assert len({r["country_id"] for r in rows})==42
    return rows


class HistoricalTransferabilityTests(unittest.TestCase):
    def test_country_balancing_and_pooled_brier_use_distinct_denominators(self):
        # Two 2021/2022 observations for country 1 and one 2021 obs for 2.
        # Country 1 has repeated unfavorable model differences while 2
        # has one favorable difference: country weighting != row weighting.
        rows=[row(1,2021,1,.8,.4),row(1,2022,1,.8,.4),
              row(2,2021,0,.8,.4)]
        stats=transfer.score(rows)
        d1=(.4-1)**2-(.8-1)**2
        d2=(.4-0)**2-(.8-0)**2
        self.assertAlmostEqual(stats[
            "paired_delta_brier_candidate_minus_global"]["p_lag1_group"],
            (2*d1+d2)/3)
        self.assertAlmostEqual(stats[
            "country_equally_weighted_paired_delta"]["p_lag1_group"],
            (d1+d2)/2)
        self.assertEqual(stats["n_unique_countries"],2)

    def test_prospective_cohort_overlap_does_not_invent_negative_labels(self):
        rows=fixed_synthetic_137()
        ids=set(range(1,31))|{100,101}
        result=transfer.assess(rows,ids)
        self.assertEqual(result["historical_137_country_year_evaluations"],137)
        self.assertEqual(result["historical_116_acd_persistence_positive"],116)
        self.assertEqual(result["historical_unique_countries"],42)
        self.assertEqual(result["issued_acd2027_2025_origin_active_countries"],32)
        self.assertEqual(result["issued_2025_countries_also_scored_historically"],30)
        self.assertEqual(result["issued_2025_countries_without_any_historical_test_row"],2)
        self.assertEqual(result["issued_2025_country_ids_without_historical_test_row"],
                         [100,101])
        self.assertEqual(result["historical_scored_countries_not_in_issued_2025_cohort"],12)
        self.assertEqual(result["issued_2025_country_hist_score_counts"]["0"],2)
        self.assertEqual(result["issued_2025_country_hist_score_counts"]["4"],26)
        self.assertEqual(result["issued_2025_country_hist_score_counts"]["3"],4)
        self.assertTrue(result["temporal_halves_share_country_ids"])
        self.assertTrue(result["2025_membership_used_only_as_posthoc_stratifier"])
        self.assertTrue(result["no_2027_outcomes_or_probabilities_changed"])
        subset=result["temporal_and_2025_cohort_subsets"]
        self.assertEqual(subset["full_historical"]["n_country_years"],137)
        self.assertEqual(
            subset["issued_2025_cohort_historical"]["n_country_years"]+
            subset["historical_not_issued_2025"]["n_country_years"],137)
        self.assertEqual(
            subset["early_2021_2022"]["n_country_years"]+
            subset["late_2023_2024"]["n_country_years"],137)
        self.assertEqual(
            subset["issued_2025_early"]["n_country_years"]+
            subset["other_historical_early"]["n_country_years"],
            subset["early_2021_2022"]["n_country_years"])
        self.assertEqual(
            subset["issued_2025_late"]["n_country_years"]+
            subset["other_historical_late"]["n_country_years"],
            subset["late_2023_2024"]["n_country_years"])

    def test_published_history_cohort_is_fail_closed(self):
        rows=fixed_synthetic_137()
        ids=set(range(1,31))|{100,101}
        for bad in (rows[:-1], rows+[copy.deepcopy(rows[0])]):
            with self.assertRaisesRegex(ValueError,"137 unique"):
                transfer.assess(bad,ids)
        bad=copy.deepcopy(rows)
        bad[0]["observed_acd"]=1
        with self.assertRaisesRegex(ValueError,"benchmark cohort"):
            transfer.assess(bad,ids)
        bad=copy.deepcopy(rows)
        bad[0]["target_year"]=2027
        with self.assertRaisesRegex(ValueError,"137 unique"):
            transfer.assess(bad,ids)
        with self.assertRaisesRegex(ValueError,"32 distinct"):
            transfer.assess(rows,set(range(1,32)))
        with self.assertRaisesRegex(ValueError,"32 distinct"):
            transfer.assess(rows,{True}|set(range(100,131)))

    def test_empty_score_explicitly_has_no_metric(self):
        summary=transfer.score([])
        self.assertEqual(summary["n_country_years"],0)
        self.assertIsNone(summary["brier_by_model"])
        self.assertIsNone(summary["country_equally_weighted_paired_delta"])

    def test_bad_probabilities_and_future_years_rejected(self):
        bad=[row(1,2021,1,global_p=1)]
        with self.assertRaisesRegex(ValueError,"probability"):
            transfer.score(bad)
        bad=[row(1,2027,1)]
        with self.assertRaisesRegex(ValueError,"risk-set"):
            transfer.score(bad)


if __name__=="__main__":
    unittest.main()
