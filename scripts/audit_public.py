#!/usr/bin/env python3
"""Fail-closed allowlisted public build gate for an institutional static research site."""
from pathlib import Path
import hashlib
from html.parser import HTMLParser
import json
import re
import sys
sys.dont_write_bytecode = True
from private_disclosure import configured_terms, contains_private_term

ROOT = Path(__file__).resolve().parents[1]
RELEASE = {"idea-lab-brand-icon.svg", "privacidad-icsa.html", "index.html", "trabajo.html", "src/private-notebook.mjs", "src/private-workbench.mjs", "src/country-comparison.mjs", "src/country-comparison-view.mjs", "src/main-country-tree.mjs", "styles.css", "favicon.svg", "logo.svg", "src/site.mjs", "src/visuals.mjs", "src/neural.mjs", "src/markov-svg.mjs", "src/lab-renderers.mjs", "src/metrics.mjs", "src/research.mjs", "src/project-catalog.mjs", "src/project-portfolio.mjs", "src/prospective-registry.mjs", "src/prospective-2028.mjs", "src/future-evaluation-register.mjs", "data/future-evaluation-contracts.json", "data/forecast-2028-geo3.json", "data/forecast-2028-geo3-manifest.json", "data/prospective-2027-registry.json", "data/prospective-2027-registry-manifest.json", "data/demo.json", "data/research.json", "data/projects.json", "data/forecast-2027-ucdp261.json", "data/forecast-2027-manifest.json", "data/forecast-2027-audit.json", "data/forecast-2027-historical-backtest.json", "data/forecast-2027-archival-cross-release.json", "data/forecast-2027-origin-state-diagnostic.json", "data/forecast-2027-entry-comparison.json", "data/onset2-231-251-homogeneous.json", "data/onset2-lagged-origin-ablation.json", "data/onset2-conflict-incidence-ablation.json", "data/ucdp-prio-incidence-vintages.json", "data/onset2-country-riskset-audit.json", "data/country-multiple-onset-source-audit.json", "data/country-multiple-newconf-experiment.json", "data/forecast-2027-newconf.json", "data/forecast-2027-newconf-manifest.json", "data/forecast-2027-newconf-audit.json"}
# Aggregated institutional source audit only; no raw private or victim-level records.
RELEASE |= {"data/candidate-2026q3-source-audit.json"}

REPOSITORY = RELEASE | { "data/geo-ged251-azerbaijan-2021-external-date-review.json", "scripts/audit_geo_ged251_marginal_fatality_interval.py", "scripts/test_audit_geo_ged251_marginal_fatality_interval.py", "data/geo-ged251-marginal-low-best-high-2021-22.json", "docs/geo-ged251-marginal-fatality-interval-and-azerbaijan.md", ".github/workflows/geo-ged251-marginal-fatality-interval.yml", "scripts/audit_geo_togo2022_440185_source_genealogy.py", "scripts/test_audit_geo_togo2022_440185_source_genealogy.py", "data/geo-ged251-togo2022-440185-public-review.json", "data/geo-ged251-togo2022-440185-source-genealogy.json", "docs/geo-ged251-togo2022-pivotal-source-genealogy.md", ".github/workflows/geo-togo2022-ged440185-source-audit.yml", "scripts/audit_geo_ged251_marginal_source_date_lags.py", "scripts/test_audit_geo_ged251_marginal_source_date_lags.py", "data/geo-ged251-marginal-source-publication-lags-2021-22.json", "docs/geo-ged251-near25-source-publication-lag-census.md", ".github/workflows/geo-ged251-marginal-publication-lags.yml", "data/geo-ged251-uganda-2022-december-public-source-review.json", "scripts/audit_geo_uganda2022_december_source_families.py", "scripts/test_audit_geo_uganda2022_december_source_families.py", "data/geo-ged251-uganda-2022-december-source-families.json", "docs/geo-ged251-uganda-december-2022-source-reconciliation.md", ".github/workflows/geo-uganda2022-december-source-families.yml", "scripts/audit_geo_uganda2022_statebased_eligibility.py", "scripts/test_audit_geo_uganda2022_statebased_eligibility.py", "data/geo-ged251-uganda-2022-eligibility-source-genealogy.json", "data/geo-ged251-uganda-2022-eligibility-dyad-stress.json", "docs/geo-ged251-uganda-2022-statebased-eligibility.md", ".github/workflows/geo-uganda2022-statebased-eligibility.yml", "data/geo-ged251-benin-uganda-public-firstparty-review.json", "scripts/audit_geo_ged251_benin_uganda_source_pair.py", "scripts/test_audit_geo_ged251_benin_uganda_source_pair.py", "data/geo-ged251-benin-uganda-2022-source-pair-audit.json", "docs/geo-ged251-benin-uganda-event-source-genealogy.md", ".github/workflows/geo-ged251-benin-uganda-source-pair.yml", "scripts/audit_geo_ged251_near25_countryyear_census.py", "scripts/test_audit_geo_ged251_near25_countryyear_census.py", "data/geo-ged251-near25-2021-22-countryyear-census.json", "docs/geo-ged251-near25-countryyear-census.md", ".github/workflows/geo-ged251-near25-census.yml", "scripts/audit_geo_ged251_candidate_source_threshold.py", "scripts/test_audit_geo_ged251_candidate_source_threshold.py", "data/geo-ged251-candidate-provenance-threshold-triage.json", "docs/geo-ged251-candidate-source-threshold-triage.md", ".github/workflows/geo-ged251-source-threshold-triage.yml", "scripts/audit_geo_ged251_stratified_linkage.py", "scripts/test_audit_geo_ged251_stratified_linkage.py", "data/geo-ged251-2021-22-linkage-sample24.json", "docs/geo-ged251-2021-22-stratified-linkage.md", ".github/workflows/geo-ged251-stratified-linkage.yml", "scripts/audit_geo_burundi_2022_neighbor_event_linkage.py", "scripts/test_audit_geo_burundi_2022_neighbor_event_linkage.py", "data/geo-burundi-2022-neighbor-event-linkage.json", "docs/geo-burundi-2022-neighbor-event-linkage.md", ".github/workflows/geo-burundi-2022-neighbor-event-linkage.yml", "scripts/audit_geo_burundi_2022_institutional_dependency.py", "scripts/test_audit_geo_burundi_2022_institutional_dependency.py", "data/geo-burundi-2022-institutional-source-independence.json", "docs/geo-burundi-2022-institutional-source-independence.md", ".github/workflows/geo-burundi-2022-institutional-independence.yml", "scripts/audit_geo_burundi_2022_source_genealogy.py", "scripts/test_audit_geo_burundi_2022_source_genealogy.py", "data/geo-burundi-2022-source-dependency-evidence.json", "docs/geo-burundi-2022-source-chain-audit.md", ".github/workflows/geo-burundi-2022-source-chain.yml", "scripts/audit_geo_burundi_2022_multiday_event_evidence.py", "scripts/test_audit_geo_burundi_2022_multiday_event_evidence.py", "docs/geo-burundi-2022-multiday-external-evidence.md", "data/geo-burundi-2022-multiday-independent-event-evidence.json", ".github/workflows/geo-burundi-2022-multiday-event-evidence.yml", "scripts/audit_geo_ged_gdelt_independent_media_events.py", "scripts/test_audit_geo_ged_gdelt_independent_media_events.py", "data/geo-ged-gdelt-external-event-footprint-3case.json", "docs/geo-ged-gdelt-independent-event-footprints.md", ".github/workflows/geo-ged-gdelt-media-event-footprints.yml", "scripts/experiment_geo_h2_worldbank_wgi_external_context.py", "scripts/test_experiment_geo_h2_worldbank_wgi_external_context.py", "data/geo-h2-wgi-political-stability-contextual-concordance.json", "docs/geo-h2-worldbank-wgi-external-context.md", ".github/workflows/geo-h2-wgi-external-context.yml", "scripts/experiment_geo_h2_fourstate_observation_identifiability.py", "scripts/test_experiment_geo_h2_fourstate_observation_identifiability.py", "data/geo-h2-fourstate-observation-kernel-latent-bounds-2027.json", "docs/geo-h2-fourstate-observation-latent-identifiability.md", ".github/workflows/geo-h2-fourstate-observation-identifiability.yml", "scripts/experiment_geo_h2_empirical_revision_rate_shadow.py", "scripts/test_experiment_geo_h2_empirical_revision_rate_shadow.py", "data/geo-h2-empirical-origin-revision-rate-2027-shadow.json", "docs/geo-h2-empirical-origin-revision-rate-shadow.md", ".github/workflows/geo-h2-empirical-revision-rate-shadow.yml", "scripts/experiment_geo_h2_fixed_origin_uncertainty_shadow.py", "scripts/test_experiment_geo_h2_fixed_origin_uncertainty_shadow.py", "data/geo-h2-origin-state-10pct-uncertainty-shadow.json", "docs/geo-h2-origin-state-10pct-uncertainty-shadow.md", ".github/workflows/geo-h2-origin-uncertainty-shadow.yml", "scripts/experiment_geo_h2_three_adjacent_vintage_zero_low.py", "scripts/test_experiment_geo_h2_three_adjacent_vintage_zero_low.py", "data/geo-h2-three-adjacent-vintage-zero-low-11-origin.json", "docs/geo-h2-three-adjacent-vintage-zero-low.md", ".github/workflows/geo-h2-three-adjacent-zero-low.yml", "scripts/experiment_geo_h2_11origin_zero_low_source_stress.py", "scripts/test_experiment_geo_h2_11origin_zero_low_source_stress.py", "data/geo-h2-11-origin-zero-low-sensitivity.json", "docs/geo-h2-11-origin-zero-low-source-stress.md", ".github/workflows/geo-h2-11-origin-zero-low-source.yml", "scripts/experiment_geo_h2_196_zero_low_vintage_sensitivity.py", "scripts/test_experiment_geo_h2_196_zero_low_vintage_sensitivity.py", "data/geo-h2-196-zero-low-origin-vintage-sensitivity.json", "docs/geo-h2-196-zero-low-source-sensitivity.md", ".github/workflows/geo-h2-196-zero-low-source-stress.yml", "scripts/experiment_geo_h2_rwanda_four_year_shapley.py", "scripts/test_experiment_geo_h2_rwanda_four_year_shapley.py", "data/geo-h2-rwanda-1996-2021-four-year-shapley.json", "docs/geo-h2-rwanda-four-year-source-shapley.md", ".github/workflows/geo-h2-rwanda-four-year-shapley.yml", "scripts/experiment_geo_h2_rwanda_origin_vintage_shapley.py", "scripts/test_experiment_geo_h2_rwanda_origin_vintage_shapley.py", "data/geo-h2-rwanda-2021-23-24-source-shapley.json", "docs/geo-h2-rwanda-origin-vintage-shapley.md", ".github/workflows/geo-h2-rwanda-origin-vintage-shapley.yml", "data/geo-h2-2023-country-origin-vintage-rank-influence.json", "scripts/experiment_geo_h2_2023_country_origin_vintage_influence.py", "scripts/test_experiment_geo_h2_2023_country_origin_vintage_influence.py", "docs/geo-h2-2023-country-origin-vintage-rank-influence.md", ".github/workflows/geo-h2-2023-country-vintage-influence.yml", "scripts/audit_geo_h2_origin_vintage_only_brier_rank.py", "scripts/test_audit_geo_h2_origin_vintage_only_brier_rank.py", "data/geo-h2-origin-vintage-only-brier-rank.json", "docs/geo-h2-origin-vintage-only-brier-rank.md", ".github/workflows/geo-h2-origin-vintage-brier-rank.yml", "scripts/audit_geo_h2_2526_fixed_brier_ranking.py", "scripts/test_audit_geo_h2_2526_fixed_brier_ranking.py", "docs/geo-h2-2526-fixed-brier-ranking-stability.md", "data/geo-h2-2526-fixed-brier-ranking-stability.json", ".github/workflows/geo-h2-2526-fixed-brier-ranking.yml", "docs/geo-h2-fixed-vector-outcome-revision.md", "scripts/experiment_geo_h2_fixed_vector_outcome_revision.py", "scripts/test_experiment_geo_h2_fixed_vector_outcome_revision.py", ".github/workflows/geo-h2-fixed-vector-outcome-revision.yml", "data/geo-h2-fixed-vector-2526-outcome-revision.json", "docs/geo-ged-revision-fixed-brier-bounds.md", "data/geo-ged-revision-fixed-brier-bounds.json", "scripts/audit_geo_ged_revision_fixed_brier_bounds.py", "scripts/test_audit_geo_ged_revision_fixed_brier_bounds.py", ".github/workflows/geo-ged-revision-fixed-brier-bounds.yml", "docs/geo-tunisia-2017-estimand-identifiability.md", "scripts/audit_geo_ged_transition_revision_impact.py", "scripts/test_audit_geo_ged_transition_revision_impact.py", "data/geo-ged-transition-revision-impact.json", ".github/workflows/geo-ged-transition-revision-impact.yml", "scripts/audit_geo_tunisia_original_2017_exit_vintages.py", "scripts/test_audit_geo_tunisia_original_2017_exit_vintages.py", "docs/geo-tunisia-original-2017-exit-audit.md", ".github/workflows/geo-tunisia-2017-exit-vintages.yml", "data/geo-tunisia-original-2017-exit-vintage-diagnostic.json", "scripts/experiment_geo_ged_tunisia_2013_15_attribution.py", "scripts/test_experiment_geo_ged_tunisia_2013_15_attribution.py", "docs/geo-ged-tunisia-h2-attribution.md", ".github/workflows/geo-ged-tunisia-h2-attribution.yml", "data/geo-ged-tunisia-2013-15-h2-attribution.json", "scripts/audit_geo_ged20_21_coverage_revisions.py", "scripts/test_audit_geo_ged20_21_coverage_revisions.py", "docs/geo-ged-20-21-coverage-revisions.md", ".github/workflows/geo-ged-20-21-coverage-revisions.yml", "data/geo-ged-20-21-coverage-revisions.json", "scripts/audit_geo_legacy_ged_countryyear_bridge.py", "scripts/test_audit_geo_legacy_ged_countryyear_bridge.py", "docs/geo-ged-legacy-countryyear-bridge.md", ".github/workflows/geo-legacy-ged-countryyear-bridge.yml", "data/geo-ged-old-vintage-countryyear-feasibility.json", "scripts/audit_geo_h2_historical_asof_sources.py", "scripts/test_audit_geo_h2_historical_asof_sources.py", "docs/geo-h2-historical-asof-source-eligibility.md", ".github/workflows/geo-h2-historical-asof.yml", "data/geo-h2-2014-2025-temporal-source-eligibility.json", "scripts/experiment_geo_h2_rolling_2014_2025.py", "scripts/test_experiment_geo_h2_rolling_2014_2025.py", "docs/geo-h2-rolling-historical-2014-2025.md", ".github/workflows/geo-h2-rolling-2014-2025.yml", "data/geo-h2-rolling-historical-2014-2025.json", "scripts/experiment_geo_h2_fatality_estimate_brier_sensitivity.py", "scripts/test_experiment_geo_h2_fatality_estimate_brier_sensitivity.py", "docs/geo-h2-fatality-estimate-brier-sensitivity.md", ".github/workflows/geo-h2-fatality-brier-sensitivity.yml", "data/geo2027-h2-fatality-estimate-brier-sensitivity.json", "data/geo2027-ucdp-fatality-vintage-intervals.json", "scripts/audit_geo2027_ucdp_fatality_vintages.py", "scripts/test_audit_geo2027_ucdp_fatality_vintages.py", "docs/geo2027-ucdp-fatality-vintages.md", ".github/workflows/geo2027-ucdp-fatality-vintages.yml", "scripts/audit_geo2027_fatality_intervals.py", "scripts/test_audit_geo2027_fatality_intervals.py", "docs/geo2027-ucdp-fatality-interval-sensitivity.md", ".github/workflows/geo2027-ucdp-fatality-intervals.yml","scripts/private_disclosure.py", "scripts/test_private_disclosure.py", "README.md", "scripts/audit_public.py", "scripts/build_official_countries.py", "scripts/test_build_official_countries.py", "scripts/inspect_ucdp_archives.py", "scripts/test_inspect_ucdp_archives.py", "scripts/run_legacy_vintage_holdout.py", "scripts/test_run_legacy_vintage_holdout.py", "scripts/experiment_recency_onset.py", "scripts/test_experiment_recency_onset.py", "scripts/forecast_2027_statebased.py", "scripts/test_forecast_2027_statebased.py", "scripts/evaluate_2027_official.py", "scripts/test_evaluate_2027_official.py", "scripts/audit_frozen_2027.py", "scripts/test_audit_frozen_2027.py", "scripts/backtest_statebased_2027_spec.py", "scripts/test_backtest_statebased_2027_spec.py", "scripts/probe_ucdp_organized_vintages.py", "scripts/test_probe_ucdp_organized_vintages.py", "scripts/backtest_archived_country_vintages.py", "scripts/test_backtest_archived_country_vintages.py", "scripts/diagnose_2027_origin_state.py", "scripts/test_diagnose_2027_origin_state.py", "scripts/evaluate_2027_new_entries.py", "scripts/test_evaluate_2027_new_entries.py", "scripts/evaluate_homogeneous_onset2.py", "scripts/test_evaluate_homogeneous_onset2.py", "scripts/experiment_onset2_lagged_signals.py", "scripts/test_experiment_onset2_lagged_signals.py", "scripts/probe_ucdp_prio_incidence.py", "scripts/test_probe_ucdp_prio_incidence.py", "scripts/experiment_onset2_conflict_incidence.py", "scripts/test_experiment_onset2_conflict_incidence.py", "scripts/audit_onset2_country_riskset.py", "scripts/test_audit_onset2_country_riskset.py", "scripts/probe_multiple_onset_vintages.py", "scripts/test_probe_multiple_onset_vintages.py", "scripts/experiment_multiple_newconf.py", "scripts/test_experiment_multiple_newconf.py", "scripts/probe_newconf_2027_acd261.py", "scripts/forecast_2027_newconf.py", "scripts/test_forecast_2027_newconf.py", "docs/newconf-2027-protocol.md", "docs/newconf-2027-evaluation-contract.md", "docs/newconf-2027-event-count-diagnostic.md", "docs/newconf-persistence-ablation.md", "scripts/diagnose_geo2027_transition_skill.py", "scripts/test_diagnose_geo2027_transition_skill.py", "docs/geo-2027-transition-attribution.md", "docs/geo2027-transition-alert-ranking.md", "docs/geo2027-exact-alert-null.md", "scripts/diagnose_geo2027_alert_count_dependence.py", "scripts/test_diagnose_geo2027_alert_count_dependence.py", "docs/geo2027-alert-dependence-scenarios.md", "scripts/diagnose_geo2027_historical_count_dispersion.py", "scripts/test_diagnose_geo2027_historical_count_dispersion.py", "docs/geo2027-historical-count-dispersion.md", "scripts/experiment_geo2027_temporal_calibration.py", "scripts/test_experiment_geo2027_temporal_calibration.py", "docs/geo2027-temporal-calibration-ablation.md", "scripts/prepare_geo2027_calibrated_shadow.py", "scripts/test_prepare_geo2027_calibrated_shadow.py", "scripts/audit_issued_geo2027_shadow.py", "scripts/test_audit_issued_geo2027_shadow.py", "docs/geo2027-calibrated-shadow-protocol.md", "scripts/evaluate_geo2027_calibrated_shadow_official.py", "scripts/test_evaluate_geo2027_calibrated_shadow_official.py", "docs/geo2027-shadow-official-evaluation-contract.md", "scripts/diagnose_geo2027_shadow_break_even.py", "scripts/test_diagnose_geo2027_shadow_break_even.py", "docs/geo2027-shadow-break-even-frontier.md", "scripts/diagnose_geo2027_ucdp_vintage_revisions.py", "scripts/test_diagnose_geo2027_ucdp_vintage_revisions.py", "docs/geo2027-ucdp-vintage-revisions.md", "scripts/diagnose_geo2027_postcalibration_count_residuals.py", "scripts/test_diagnose_geo2027_postcalibration_count_residuals.py", "docs/geo2027-postcalibration-count-residuals.md", "scripts/diagnose_ucdp_prio_older_vintages.py", "scripts/test_diagnose_ucdp_prio_older_vintages.py", "docs/ucdp-prio-older-vintage-extension.md", "scripts/backtest_ucdp_prio_retention_four_vintages.py", "scripts/test_backtest_ucdp_prio_retention_four_vintages.py", "docs/ucdp-prio-retention-four-vintage-study.md", "scripts/diagnose_acd_retention_vintage_yearblock.py", "scripts/test_diagnose_acd_retention_vintage_yearblock.py", "docs/acd-retention-vintage-yearblock-robustness.md", "scripts/prepare_acd2027_prospective_retention.py", "scripts/test_prepare_acd2027_prospective_retention.py", "docs/acd2027-prospective-retention-issuance-protocol.md", "scripts/publish_acd2027_named_country_view.py", "scripts/test_publish_acd2027_named_country_view.py", "docs/acd2027-named-country-forecast.md", "scripts/evaluate_acd2027_retention_official.py", "scripts/test_evaluate_acd2027_retention_official.py", "docs/acd2027-first-complete-release-scoring-contract.md", "scripts/build_2027_prospective_registry.py", "scripts/test_build_2027_prospective_registry.py", "docs/prospective-2027-three-cohort-registry.md", "scripts/diagnose_acd2027_brier_pivot.py", "scripts/test_diagnose_acd2027_brier_pivot.py", "docs/acd2027-conditional-brier-pivot.md", "scripts/diagnose_acd_retention_country_influence.py", "scripts/test_diagnose_acd_retention_country_influence.py", "docs/acd-historical-country-influence.md", "scripts/diagnose_acd2027_historical_transferability.py", "scripts/test_diagnose_acd2027_historical_transferability.py", "docs/acd2027-historical-transferability.md", "scripts/diagnose_acd2027_exact_count_evidence.py", "scripts/test_diagnose_acd2027_exact_count_evidence.py", "docs/acd2027-exact-count-prospective-evidence.md", "scripts/diagnose_acd2027_dependence_variance.py", "scripts/test_diagnose_acd2027_dependence_variance.py", "docs/acd2027-dependence-variance-sensitivity.md", "scripts/diagnose_geo_newconf2027_sharp_dependence.py", "scripts/test_diagnose_geo_newconf2027_sharp_dependence.py", "data/geo-newconf2027-sharp-dependence.json", "docs/geo-newconf2027-sharp-dependence.md", "scripts/diagnose_historical_geo_newconf_year_counts.py", "scripts/test_diagnose_historical_geo_newconf_year_counts.py", "data/historical-geo-newconf-annual-residuals.json", "docs/geo-newconf2027-historical-year-count-bias.md", "scripts/prepare_geo2028_three_year.py", "scripts/test_prepare_geo2028_three_year.py", "docs/geo2028-three-year-preregistration.md", "data/forecast-2028-geo3.json", "data/forecast-2028-geo3-manifest.json", "scripts/audit_geo2028_first_public_issue.py", "scripts/test_audit_geo2028_first_public_issue.py", "docs/geo2028-first-issued-forecast.md", "scripts/evaluate_geo2028_first_complete_official.py", "scripts/test_evaluate_geo2028_first_complete_official.py", "docs/geo2028-first-complete-release-scoring-contract.md", "scripts/build_future_evaluation_contract_registry.py", "scripts/test_build_future_evaluation_contract_registry.py", "tests/future-evaluation-register.test.mjs", "docs/unified-future-evaluation-register.md", "scripts/paired_brier_partial_identification.py", "scripts/test_paired_brier_partial_identification.py", "docs/non-iid-2027-evaluation-guards.md", "scripts/prepare_geo2028_origin2026.py", "scripts/test_prepare_geo2028_origin2026.py", "docs/geo2028-origin2026-preregistration.md", "scripts/decompose_geo2028_origin2026_update.py", "scripts/test_decompose_geo2028_origin2026_update.py", "docs/geo2028-2026-origin-update-attribution.md", "scripts/diagnose_geo2028_historical_forecast_vintage_drift.py", "scripts/test_diagnose_geo2028_historical_forecast_vintage_drift.py", "docs/geo2028-historical-forecast-vintage-drift.md", "scripts/diagnose_geo2027_alert_ranking_robustness.py", "scripts/test_diagnose_geo2027_alert_ranking_robustness.py", "docs/geo2027-issued-alert-ranking-robustness.md", "data/geo2027-issued-alert-perturbation-robustness.json", "scripts/diagnose_geo2027_historical_alert_vintage_overlap.py", "scripts/test_diagnose_geo2027_historical_alert_vintage_overlap.py", "docs/geo2027-historical-alert-vintage-overlap.md", "scripts/diagnose_geo2027_indonesia_vintage_attribution.py", "scripts/test_diagnose_geo2027_indonesia_vintage_attribution.py", "docs/geo2027-indonesia-vintage-revision-attribution.md", "scripts/audit_geo2027_indonesia_original_fatalities.py", "scripts/test_audit_geo2027_indonesia_original_fatalities.py", "data/geo2027-indonesia-raw-death-revisions.json", "scripts/experiment_geo2027_intensity_markov_cross_release.py", "scripts/test_experiment_geo2027_intensity_markov_cross_release.py", "docs/geo2027-intensity-markov-cross-release.md", "scripts/experiment_geo2027_log1p_nested_h2.py", "scripts/test_experiment_geo2027_log1p_nested_h2.py", "docs/geo2027-log1p-nested-h2.md", "scripts/prepare_geo2027_log1p_shadow.py", "scripts/test_prepare_geo2027_log1p_shadow.py", "scripts/audit_geo2027_log1p_shadow_issue.py", "scripts/test_audit_geo2027_log1p_shadow_issue.py", "docs/geo2027-log1p-prospective-shadow-protocol.md", "scripts/diagnose_geo2027_log1p_historical_vintage_robustness.py", "scripts/test_diagnose_geo2027_log1p_historical_vintage_robustness.py", "docs/geo2027-log1p-historical-vintage-robustness.md", "scripts/audit_geo2027_log1p_issued_death_stress.py", "scripts/test_audit_geo2027_log1p_issued_death_stress.py", "docs/geo2027-log1p-issued-death-count-stress.md", "scripts/experiment_geo2027_log1p_inactive_attenuation_frontier.py", "scripts/test_experiment_geo2027_log1p_inactive_attenuation_frontier.py", "docs/geo2027-log1p-inactive-attenuation-frontier.md", "scripts/experiment_geo2027_log1p_rolling_year_vintage.py", "scripts/test_experiment_geo2027_log1p_rolling_year_vintage.py", "docs/geo2027-log1p-rolling-year-vintage-stability.md", "scripts/diagnose_geo2027_log1p_annual_country_reversals.py", "scripts/test_diagnose_geo2027_log1p_annual_country_reversals.py", "docs/geo2027-log1p-annual-country-reversals.md", "scripts/experiment_geo2027_log1p_country_block_transfer.py", "scripts/test_experiment_geo2027_log1p_country_block_transfer.py", "docs/geo2027-log1p-subthreshold-country-block-transfer.md", "scripts/experiment_geo2027_log1p_markov_country_history_ablation.py", "scripts/test_experiment_geo2027_log1p_markov_country_history_ablation.py", "docs/geo2027-log1p-markov-country-history-ablation.md", "scripts/experiment_geo2027_log1p_matched_global_only.py", "scripts/test_experiment_geo2027_log1p_matched_global_only.py", "docs/geo2027-log1p-matched-global-only-calibration.md", "scripts/prepare_geo2027_global_only_matched_shadow.py", "scripts/test_prepare_geo2027_global_only_matched_shadow.py", "docs/geo2027-global-only-matched-prospective.md", "scripts/diagnose_geo2027_issued_disagreement.py", "scripts/test_diagnose_geo2027_issued_disagreement.py", "docs/geo2027-global-only-issued-disagreement.md", "scripts/diagnose_geo2027_markov_partial_pooling.py", "scripts/test_diagnose_geo2027_markov_partial_pooling.py", "docs/geo2027-markov-partial-pooling-vintage-stability.md", "scripts/resolve_geo2027_first_complete_official.py", "scripts/test_resolve_geo2027_first_complete_official.py", "docs/geo2027-full196-official-resolution-readiness.md", "scripts/audit_geo2027_ucdp_zero_coding.py", "scripts/test_audit_geo2027_ucdp_zero_coding.py", "docs/geo2027-ucdp-zero-coding-riskset-audit.md", "data/geo2027-ucdp-zero-coding-riskset-audit.json", ".github/workflows/geo2027-ucdp-zero-coding-riskset.yml", "data/geo2027-full196-resolution-readiness.json", ".github/workflows/geo2027-full196-resolution-readiness.yml", "data/geo2027-markov-partial-pooling-vintage-stability.json", ".github/workflows/geo2027-markov-partial-pooling-vintage.yml", "data/geo2027-global-only-issued-disagreement.json", ".github/workflows/geo2027-global-only-issued-disagreement.yml", "data/forecast-2027-global-only-matched-shadow.json", "data/forecast-2027-global-only-matched-manifest.json", "scripts/audit_geo2027_global_only_matched_issue.py", "scripts/test_audit_geo2027_global_only_matched_issue.py", ".github/workflows/geo2027-global-only-matched-prospective.yml", "data/geo2027-log1p-matched-global-only-calibration.json", ".github/workflows/geo2027-log1p-matched-global-only.yml", "data/geo2027-log1p-markov-country-history-ablation.json", ".github/workflows/geo2027-log1p-markov-country-history-ablation.yml", "data/geo2027-log1p-subthreshold-country-block-transfer.json", ".github/workflows/geo2027-log1p-country-block-transfer.yml", "data/geo2027-log1p-country-year-reversal-attribution.json", ".github/workflows/geo2027-log1p-country-reversal.yml", "data/geo2027-log1p-rolling-year-vintage-stability.json", ".github/workflows/geo2027-log1p-rolling-year-vintage.yml", "data/geo2027-log1p-inactive-attenuation-frontier.json", ".github/workflows/geo2027-log1p-inactive-attenuation-frontier.yml", "data/geo2027-log1p-issued-death-count-stress.json", ".github/workflows/geo2027-log1p-issued-death-stress.yml", "data/geo2027-log1p-historical-vintage-robustness.json", ".github/workflows/geo2027-log1p-historical-vintage.yml", "data/forecast-2027-log1p-shadow.json", "data/forecast-2027-log1p-shadow-manifest.json", ".github/workflows/geo2027-log1p-prospective-shadow.yml", "data/geo2027-log1p-nested-h2.json", ".github/workflows/geo2027-log1p-nested-h2.yml", "data/geo2027-intensity-markov-cross-release.json", ".github/workflows/geo2027-intensity-markov-cross-release.yml", ".github/workflows/geo2027-indonesia-raw-deaths.yml", "data/geo2027-indonesia-vintage-revision-attribution.json", ".github/workflows/geo2027-indonesia-source-attribution.yml", "data/geo2027-historical-alert-vintage-overlap.json", "data/geo2028-historical-forecast-vintage-drift.json", "data/acd2027-dependence-variance.json", "data/acd2027-exact-count-evidence.json", "data/acd2027-historical-transferability.json", "data/acd-historical-country-influence.json", "tests/prospective-registry.test.mjs", "tests/prospective-2028.test.mjs", "data/forecast-2027-acd-retention-country-view.json", "data/forecast-2027-acd-retention.json", "data/forecast-2027-acd-retention-manifest.json", "scripts/audit_issued_acd2027_retention.py", "scripts/test_audit_issued_acd2027_retention.py", "data/forecast-2027-acd-retention-audit.json", "data/ucdp-prio-retention-vintage-yearblock-robustness.json", "data/ucdp-prio-2021-2024-retention-four-vintage.json", "data/ucdp-prio-2020-2022-vintages-archival.json", "data/geo2027-postcalibration-count-residuals-archival.json", "data/geo2027-ucdp-vintage-revisions-archival.json", "data/geo2027-shadow-break-even-frontier.json", "data/forecast-2027-geo-shadow.json", "data/forecast-2027-geo-shadow-manifest.json", "data/forecast-2027-geo-shadow-audit.json", "data/geo2027-temporal-calibration-ablation.json", "data/geo2027-historical-count-dispersion-archival.json", "scripts/prepare_geo2027_transition_alerts.py", "scripts/test_prepare_geo2027_transition_alerts.py", "scripts/audit_issued_geo2027_transition_alerts.py", "scripts/test_audit_issued_geo2027_transition_alerts.py", "docs/geo2027-prospective-alert-protocol.md", "scripts/evaluate_geo2027_transition_alerts_official.py", "scripts/test_evaluate_geo2027_transition_alerts_official.py", "docs/geo2027-official-alert-evaluation-contract.md", "data/forecast-2027-transition-alerts.json", "data/forecast-2027-transition-alerts-manifest.json", "data/forecast-2027-transition-alerts-audit.json", "data/geo2027-exact-alert-null-archival.json", "scripts/diagnose_geo2027_exact_alert_null.py", "scripts/test_diagnose_geo2027_exact_alert_null.py", "data/geo2027-transition-alert-ranking-archival.json", "scripts/evaluate_geo2027_transition_alerts.py", "scripts/test_evaluate_geo2027_transition_alerts.py", "data/geo2027-transition-attribution-archival.json", "data/newconf-persistence-2023-24-ablation.json", "scripts/experiment_newconf_persistence.py", "scripts/test_experiment_newconf_persistence.py", "scripts/diagnose_newconf2027_event_count.py", "scripts/test_diagnose_newconf2027_event_count.py", "scripts/audit_frozen_newconf_2027.py", "scripts/test_audit_frozen_newconf_2027.py", "scripts/evaluate_2027_newconf_official.py", "scripts/test_evaluate_2027_newconf_official.py", "docs/forecast-2027-protocol.md", "tests/metrics.test.mjs", "tests/research.test.mjs", "tests/temporal-validation.test.mjs", "src/temporal-validation.mjs", "tests/visuals.test.mjs", "tests/lab-renderers.test.mjs", "tests/project-catalog.test.mjs", "tests/project-portfolio.test.mjs", "tests/public-science-boundary.test.mjs", "tests/private-notebook.test.mjs", "tests/country-comparison.test.mjs", ".github/workflows/pages.yml", ".github/workflows/geo2027-vintage-alert-audit.yml"}
# Public scientific aggregates (not individual records).
RELEASE |= {"data/candidate-q2-q3-vintage-revisions.json"}
REPOSITORY |= {
    "scripts/audit_candidate_q2_q3_vintages.py",
    "scripts/test_audit_candidate_q2_q3_vintages.py",
    "docs/candidate-q2-q3-vintage-revisions.md",
    ".github/workflows/candidate-q2-q3-vintage-revisions.yml",
    "data/candidate-q2-q3-vintage-revisions.json",
}
# Historical-only 30/90-day institutional benchmark; fixed source references and public aggregate vectors.
RELEASE |= {"data/candidate-30-90-baseline-holdout.json"}
REPOSITORY |= {
    "scripts/experiment_candidate_30_90_holdout.py",
    "scripts/test_experiment_candidate_30_90_holdout.py",
    "docs/candidate-30-90-baseline-holdout-protocol.md",
    ".github/workflows/candidate-30-90-baseline-holdout.yml",
    "data/candidate-30-90-baseline-holdout.json",
}
# Data-science revisions, exact historical sources and aggregate rare-onset diagnostics only.
RELEASE |= {"data/candidate-onset-label-revision-ties.json"}
REPOSITORY |= {
    "scripts/audit_candidate_onset_label_stability.py",
    "scripts/test_audit_candidate_onset_label_stability.py",
    "docs/candidate-onset-label-revision-tie-protocol.md",
    ".github/workflows/candidate-onset-label-stability.yml",
    "data/candidate-onset-label-revision-ties.json",
}
# Historical-only Candidate threshold grid and explicit original-source aggregates.
RELEASE |= {"data/candidate-reactivation-threshold-grid.json"}
REPOSITORY |= {
    "scripts/experiment_candidate_reactivation_grid.py",
    "scripts/test_experiment_candidate_reactivation_grid.py",
    "docs/candidate-reactivation-threshold-grid-protocol.md",
    ".github/workflows/candidate-reactivation-threshold-grid.yml",
    "data/candidate-reactivation-threshold-grid.json",
}
# Post-selection sensitivity of previously issued institutional Candidate experiment results only.
RELEASE |= {"data/candidate-may-threshold-vintage-stability.json"}
REPOSITORY |= {
    "scripts/audit_candidate_may_threshold_stability.py",
    "scripts/test_audit_candidate_may_threshold_stability.py",
    "docs/candidate-may-threshold-vintage-stability.md",
    ".github/workflows/candidate-may-threshold-vintage-stability.yml",
    "data/candidate-may-threshold-vintage-stability.json",
}
# Candidate uncertainty sensitivity study, aggregate nation-level observables only.
RELEASE |= {"data/candidate-fatality-uncertainty-code-status.json"}
REPOSITORY |= {
    "scripts/audit_candidate_fatality_uncertainty.py",
    "scripts/test_audit_candidate_fatality_uncertainty.py",
    "docs/candidate-fatality-uncertainty-coding-status.md",
    ".github/workflows/candidate-fatality-uncertainty.yml",
    "data/candidate-fatality-uncertainty-code-status.json",
}
# Two-year official annual GED source-resolution audit, institutionally bounded.
RELEASE |= {"data/candidate-to-annual-ged-resolution.json"}
REPOSITORY |= {
    "scripts/audit_candidate_to_annual_ged.py",
    "scripts/test_audit_candidate_to_annual_ged.py",
    "docs/candidate-to-ged-annual-resolution-protocol.md",
    ".github/workflows/candidate-to-annual-ged.yml",
    "data/candidate-to-annual-ged-resolution.json",
}
# 2021/22 original GED annual label reconciliation, no personal sources.
RELEASE |= {"data/candidate-ged-2021-22-resolution.json"}
REPOSITORY |= {
    "scripts/audit_candidate_ged_2021_22.py",
    "scripts/test_audit_candidate_ged_2021_22.py",
    "docs/candidate-ged-2021-22-annual-resolution.md",
    "data/candidate-ged-2021-22-resolution.json",
    ".github/workflows/candidate-ged-2021-22.yml",
}
# Subsequent annual-release revision study: original ZIPs and CI-frozen public aggregates.
RELEASE |= {"data/ged2024-annual-vintage-drift.json"}
REPOSITORY |= {
    "scripts/audit_ged2024_annual_vintage_drift.py",
    "scripts/test_audit_ged2024_annual_vintage_drift.py",
    "docs/ged2024-annual-vintage-drift-protocol.md",
    ".github/workflows/ged2024-annual-vintage-drift.yml",
    "data/ged2024-annual-vintage-drift.json",
}
# Postselected explanatory strata of source-audited public Candidate vs GED labels.
RELEASE |= {"data/candidate-ged-retention-strata.json"}
REPOSITORY |= {
    "scripts/audit_candidate_ged_retention_strata.py",
    "scripts/test_audit_candidate_ged_retention_strata.py",
    "docs/candidate-ged-retention-strata-protocol.md",
    ".github/workflows/candidate-ged-retention-strata.yml",
    "data/candidate-ged-retention-strata.json",
}
# Candidate event/dyad fate decomposition from official archives only; no raw event IDs published.
RELEASE |= {"data/candidate-ged-event-dyad-fates.json"}
REPOSITORY |= {
    "scripts/audit_candidate_ged_event_dyad_fates.py",
    "scripts/test_audit_candidate_ged_event_dyad_fates.py",
    "docs/candidate-ged-event-dyad-fates-protocol.md",
    ".github/workflows/candidate-ged-event-dyad-fates.yml",
    "data/candidate-ged-event-dyad-fates.json",
}
# Historical UCDP Dyadic annual inclusion study, no event/dyad raw IDs in public reports.
RELEASE |= {"data/ucdp-official-dyadyear-case-resolution.json"}
REPOSITORY |= {
    "scripts/audit_ucdp_dyadic_year_inclusion.py",
    "scripts/test_audit_ucdp_dyadic_year_inclusion.py",
    "docs/ucdp-dyadic-year-inclusion-audit.md",
    "data/ucdp-official-dyadyear-case-resolution.json",
    ".github/workflows/ucdp-dyadic-year-inclusion.yml",
}
# Historical UCDP Candidate/GED labels versus all-negative comparator; zero forecasts.
RELEASE |= {"data/candidate-ged-annual-null-baseline-audit.json"}
REPOSITORY |= {
    "scripts/audit_candidate_ged_annual_null_baseline.py",
    "scripts/test_audit_candidate_ged_annual_null_baseline.py",
    "docs/candidate-ged-annual-null-baseline.md",
    "data/candidate-ged-annual-null-baseline-audit.json",
    ".github/workflows/candidate-ged-annual-null-baseline.yml",
}
# Conservative annual GED probability benchmark; retrospective aggregate results only.
RELEASE |= {"data/annual-ged-rolling-probability.json"}
REPOSITORY |= {
    "scripts/experiment_annual_ged_rolling_probability.py",
    "scripts/test_experiment_annual_ged_rolling_probability.py",
    "docs/annual-ged-rolling-probability-protocol.md",
    "data/annual-ged-rolling-probability.json",
    ".github/workflows/annual-ged-rolling-probability.yml",
}
# Monthly Candidate bridge protocol; aggregate results only.
RELEASE |= {"data/candidate-monthly-bridge-audit.json", "data/candidate-monthly-probability.json"}
REPOSITORY |= {
    "scripts/audit_candidate_monthly_bridge_census.py",
    "scripts/audit_candidate_monthly_bridge.py",
    "scripts/experiment_candidate_monthly_probability.py",
    "scripts/test_experiment_candidate_monthly_probability.py",
    "data/candidate-monthly-bridge-audit.json",
    "data/candidate-monthly-probability.json",
    "scripts/test_audit_candidate_monthly_bridge.py",
    "scripts/test_audit_candidate_monthly_bridge_census.py",
    "docs/candidate-monthly-bridge-protocol.md",
    ".github/workflows/candidate-monthly-bridge-census.yml",
}
# Complementary signal study: aggregate-only public research.
RELEASE |= {"data/candidate-monthly-complementary-signals.json"}
REPOSITORY |= {
    "docs/candidate-monthly-complementary-signals.md",
    "data/candidate-monthly-complementary-signals.json",
    "scripts/experiment_candidate_monthly_complementary_signals.py",
    "scripts/test_experiment_candidate_monthly_complementary_signals.py",
    ".github/workflows/candidate-monthly-complementary-signals.yml",
}
# Operational alert budget research: aggregate outputs only.
RELEASE |= {"data/candidate-monthly-alert-value.json"}
REPOSITORY |= {
    "docs/candidate-monthly-alert-value.md",
    "data/candidate-monthly-alert-value.json",
    "scripts/experiment_candidate_monthly_alert_value.py",
    "scripts/test_experiment_candidate_monthly_alert_value.py",
    ".github/workflows/candidate-monthly-alert-value.yml",
}
# Contemporary October 2026 source observation, not an issuance.
RELEASE |= {"data/candidate-october-2026-source-observation.json"}
REPOSITORY |= {
    "docs/candidate-october-2026-source-observation.md",
    "data/candidate-october-2026-source-observation.json",
    "scripts/audit_candidate_october_source_observation.py",
    "scripts/test_audit_candidate_october_source_observation.py",
    ".github/workflows/candidate-october-source-observation.yml",
}
# DEC2026 pilot protocol and generator only; no issued probabilities yet.
REPOSITORY |= {
    "docs/prospective-short-horizon-pilot-dec2026.md",
    "scripts/generate_dec2026_pilot.py",
    "scripts/test_generate_dec2026_pilot.py",
    ".github/workflows/dec2026-pilot.yml",
}
# DEC2026 experimental forecast: original bytes and publication receipt.
RELEASE |= {"data/forecast-dec2026-pilot.json","data/forecast-dec2026-pilot-manifest.json"}
REPOSITORY |= {
    "data/forecast-dec2026-pilot.json",
    "data/forecast-dec2026-pilot-manifest.json",
    "scripts/check_dec2026_publication.py",
    "scripts/test_check_dec2026_publication.py",
    ".github/workflows/dec2026-publication.yml",
}
RELEASE |= {"src/prospective-dec2026.mjs"}
REPOSITORY |= {"src/prospective-dec2026.mjs","tests/prospective-dec2026.test.mjs"}
# DEC2026 future outcome resolver; no actual outcome data yet.
REPOSITORY |= {
    "docs/dec2026-future-resolution.md",
    "scripts/resolve_dec2026_pilot.py",
    "scripts/test_resolve_dec2026_pilot.py",
    ".github/workflows/dec2026-resolution.yml",
}
# DEC2026 provisional monitoring contract, no actual observations yet.
REPOSITORY |= {
    "docs/dec2026-provisional-monitor.md",
    "scripts/monitor_dec2026_pilot.py",
    "scripts/test_monitor_dec2026_pilot.py",
    ".github/workflows/dec2026-monitor.yml",
}
# COUP source census and reconciliation, institutional references and no raw data.
REPOSITORY |= {"data/coup-mean-constraint.json","docs/coup-mean-constraint.md","scripts/experiment_coup_mean_constraint.py","scripts/test_experiment_coup_mean_constraint.py"}
REPOSITORY |= {"data/coup-rolling-backtest.json","docs/coup-rolling-backtest.md","scripts/experiment_coup_rolling_backtest.py","scripts/test_experiment_coup_rolling_backtest.py"}
REPOSITORY |= {"data/coup-origin-panel.json","docs/coup-origin-panel-protocol.md","scripts/audit_coup_origin_panel.py","scripts/test_audit_coup_origin_panel.py"}
REPOSITORY |= {"data/coup-membership-reconciliation.json","docs/coup-membership-reconciliation.md","scripts/audit_coup_reconciliation.py","scripts/test_audit_coup_reconciliation.py"}
RELEASE |= {"data/coup-source-census.json","data/coup-membership-census.json","data/coup-membership-reconciliation.json"}
REPOSITORY |= {"data/coup-source-census.json","data/coup-membership-census.json","scripts/audit_coup_membership.py","scripts/test_audit_coup_membership.py"}
REPOSITORY |= {"docs/coup-source-census.md","scripts/audit_coup_sources.py","scripts/test_audit_coup_sources.py",".github/workflows/coup-source-census.yml"}
# Short-horizon scientific source gate: institutional-only code, tests and protocol.
REPOSITORY |= {
    "scripts/check_ucdp_candidate_asof.py",
    "scripts/test_check_ucdp_candidate_asof.py",
    "docs/candidate-30-90-day-asof-protocol.md",
    ".github/workflows/candidate-30-90-day-asof.yml",
}

issues = []
# Historical research cells must never be admitted to a public release.
BLOCKED = {"data/scientific-workbook.json", "src/scientific-archive.mjs"}
try:
    private_terms = configured_terms()
except ValueError as error:
    issues.append(str(error))
    private_terms = ()
files = {str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts}
if blocked := sorted(files & BLOCKED):
    issues.append("Private scientific source must not exist in public checkout")
if unknown := sorted(files - REPOSITORY):
    issues.append("Unapproved additional files: " + str(len(unknown)))
if missing := sorted(REPOSITORY - files):
    issues.append("Missing required files: " + str(len(missing)))

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.references=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in ("a","link","img","script"):
            u=a.get("href") or a.get("src")
            if u: self.references.append(u)
if (ROOT/"src/site.mjs").exists():
    site = (ROOT/"src/site.mjs").read_text(encoding="utf8")
    if re.search(r"scientific-workbook\\.json|scientificArchiveTable|verifyScientificArchive", site):
        issues.append("Public client may load private scientific detail")
if (ROOT/"scripts/build_official_countries.py").is_file():
    code=(ROOT/"scripts/build_official_countries.py").read_text(encoding="utf8")
    if "OFFICIAL_URL" not in code or "ucdp.uu.se/downloads/organizedviolencecy/" not in code:
        issues.append("Public official-source generator provenance missing")
if (ROOT/"src/main-country-tree.mjs").is_file():
    source=(ROOT/"src/main-country-tree.mjs").read_text(encoding="utf8")
    if re.search(r"fetch\(|XMLHttpRequest|sendBeacon", source):
        issues.append("Main country tree must not transmit local scientific catalogues")
if (ROOT/"src/country-comparison-view.mjs").is_file():
    content=(ROOT/"src/country-comparison-view.mjs").read_text(encoding="utf8")
    if re.search(r"fetch\(|XMLHttpRequest|sendBeacon", content):
        issues.append("Country comparison must not transmit country-level data")
if (ROOT/"trabajo.html").is_file():
    private_html=(ROOT/"trabajo.html").read_text(encoding="utf8")
    if "connect-src 'none'" not in private_html or "BORRADOR" not in private_html.upper():
        issues.append("Research workbench must remain network-isolated and draft-only")
    if re.search(r"fetch\(|XMLHttpRequest|sendBeacon", (ROOT/"src/private-workbench.mjs").read_text(encoding="utf8")):
        issues.append("Private workbench must not transmit scientific content")
if (ROOT/"index.html").exists():
    links=Links()
    links.feed((ROOT/"index.html").read_text(encoding="utf8"))
    for url in links.references:
        if url.startswith("#"): continue
        if url.startswith("https://"):
            if not (url.startswith("https://idealab2026.github.io/") or url.startswith("https://github.com/idealab2026/")):
                issues.append("Non-institutional external link")
        elif url in ("./?view=futures","./?view=shadow2027","./?view=registry2027","./?view=dec2026"): continue
        elif url.startswith("./"):
            if url[2:].split("?",1)[0] not in RELEASE or ("?" in url and not re.fullmatch(r"v=[a-f0-9]{12}",url.split("?",1)[1])): issues.append("Dependency not on release allowlist")
        else: issues.append("Unexpected link or source type")
for path in sorted(files):
    if path not in REPOSITORY: continue
    source=(ROOT/path).read_text(encoding="utf8")
    if contains_private_term(path+"\n"+source, private_terms):
        issues.append("Private disclosure guard rejected repository content")
    if path in RELEASE or path == "README.md":
        for match in re.finditer(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_-]+)/", source, flags=re.I):
            if match.group(1).lower() != "idealab2026":
                issues.append("Non-institutional repository reference")
        if re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",source):
            issues.append("Email address found in public content")
    if re.search(r"-----BEGIN [^-]+PRIVATE KEY-----|github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{30,}",source):
        issues.append("Credential-like content")
    if re.search(r"https?://(?:localhost|127\.0\.0\.1|[^\s/]*\.workers\.dev)",source,re.I):
        issues.append("Unexpected local or backend reference")
catalogue=ROOT/"data/research.json"
if catalogue.exists():
    try:
        data=json.loads(catalogue.read_text(encoding="utf8"))
        if data.get("class")!="public_research_program" or data.get("forecast_issued")!=1 or data.get("prospective_results_verified")!=0:
            issues.append("Unverified scientific claim in public dataset")
        if len(data.get("programs",[]))!=7:
            issues.append("Incomplete scientific programme")
    except (OSError,ValueError):
        issues.append("Invalid scientific programme")
ideas=ROOT/"data/projects.json"
if ideas.exists():
    try:
        raw=ideas.read_text(encoding="utf8")
        catalog=json.loads(raw)
        projects=catalog.get("projects",[])
        relations=catalog.get("relations",[])
        privacy=catalog.get("privacy") or {}
        coverage=catalog.get("coverage") or {}
        categories=[p.get("category") for p in projects]
        ids=[p.get("id") for p in projects]
        if catalog.get("schema")!="idealab.psico.public-project-catalog.v1" or \
           catalog.get("ok") is not True or \
           catalog.get("status")!="PUBLIC_INSTITUTIONAL_PROJECTION" or \
           catalog.get("forecastIssued")!=0 or \
           catalog.get("verifiedProspectiveResults")!=0 or \
           len(projects)!=9 or len(relations)!=14 or \
           len(set(ids))!=9 or \
           categories.count("Vertiente")!=4 or categories.count("Aplicación")!=3 or \
           sum(p.get("documentation") is not None for p in projects)!=8 or \
           any(p.get("liveOperationalVerification") is not False for p in projects) or \
           any(coverage.get(k)!=n for k,n in
               (("projects",9),("coreTracks",4),("applications",3),
                ("documentationRecords",8),("relations",14))) or \
           any(privacy.get(k) is not False for k in
               ("sourceIdsReused","internalPathsIncluded","historicPrivateNotesIncluded")) or \
           privacy.get("independentPublication") is not True:
            issues.append("Public research project projection is incomplete or claims unsupported operation")
        if re.search(r"https?://|[a-z0-9._%-]+@[a-z0-9.-]+\.[a-z]{2,}|"
                     r"(?:[a-z_-]+/){2,}|\"id\"\s*:\s*\"prj-|"
                     r"(?:PR|issue)\s*#\s*\d+",raw,flags=re.I):
            issues.append("Public project projection reveals legacy identifiers or sources")
        if any(set(p.get("documentation") or {})-
               {"vision","scope","method","validation","limitations"} for p in projects):
            issues.append("Public project projection includes private historical documentation")
        external={x.get("id") for x in catalog.get("externalReferences",[])}
        allowed=set(ids)|external
        if len(external)!=1 or any(r.get("source") not in ids or
           r.get("target") not in allowed for r in relations):
            issues.append("Public project projection has an unresolved relation")
    except (OSError,ValueError,TypeError,AttributeError):
        issues.append("Invalid public project projection")

# A public issue is valid only when all frozen probabilities match the first-public document digest.
issued_file=ROOT/"data/forecast-2027-ucdp261.json"
manifest_file=ROOT/"data/forecast-2027-manifest.json"
if issued_file.exists() and manifest_file.exists():
    try:
        raw=issued_file.read_bytes()
        issue=json.loads(raw.decode("utf8"))
        manifest=json.loads(manifest_file.read_text(encoding="utf8"))
        if hashlib.sha256(raw).hexdigest()!=manifest.get("forecast_sha256") or \
           manifest.get("forecast_sha256")!="5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5" or \
           manifest.get("status")!="ISSUED_PROSPECTIVE_UNRESOLVED" or \
           manifest.get("first_public_forecast_commit")!="3bb3561c8d6182c30624591276c705fb76ce99dc" or \
           manifest.get("canonical_document_commit")!="8b924e0b0c7a07e27977160c9658cfed77940aff" or \
           manifest.get("preregistered_protocol_main_commit")!="87959a117e1b30323392a488c48c9afb1cb0bffc" or \
           manifest.get("outcomes_resolved")!=0 or \
           manifest.get("demonstrated_predictive_skill") is not False or \
           manifest.get("independently_notarized") is not False or \
           issue.get("target",{}).get("year")!=2027 or \
           issue.get("source",{}).get("data_last_year")!=2025 or \
           issue.get("source",{}).get("sha256")!="66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34" or \
           issue.get("protocol",{}).get("skill_not_demonstrated") is not True or \
           len(issue.get("countries",[]))!=196:
            issues.append("Prospective forecast issue is not exactly the preregistered public content")
    except (OSError,ValueError,TypeError,AttributeError):
        issues.append("Invalid prospective issue manifest or document")

sample=ROOT/"data/demo.json"
if sample.exists():
    try:
        if json.loads(sample.read_text(encoding="utf8")).get("meta",{}).get("data_class")!="synthetic":
            issues.append("Dataset not admitted for a public synthetic demonstration")
    except (OSError,ValueError):
        issues.append("Invalid dataset")
if issues:
    print("PUBLIC RELEASE REJECTED:",*sorted(set(issues)),sep="\n- ")
    sys.exit(1)
print("OK: allowlist, source scanning, institutional links and synthetic demonstration")
