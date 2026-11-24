# Rolling-origin probability benchmark for first annual GED labels

2026-11-24. Exploratory retrospective protocol, committed before computing new model scores. Existing source outcomes and threshold sensitivities are already known; not a blinded preregistration.

Input: fixed original Candidate Q1 country counts and first annual GED country counts from PRs 151/152, four years 2021, 2022, 2024, 2025, 196 countries. Exact raw SHA pins inherited from PR 154. Exclude 2023 as incompatible Candidate Q1. No Q2/Q3 values are model inputs; no test-year GED or Dyadic features. Restrict each threshold-specific risk set to Q1 count below threshold. Evaluate all thresholds 1,5,10,25 and horizons 30,90 days, no selection after scoring.

Evaluation: origin 2024 trained on 2021/22; origin 2025 trained on 2021/22 only (primary conservative historical availability proxy; first annual GED for 2024 typically comes after April 2025, so exclude it). Annual outcomes must come from years <= target year - 2; no exact historical publication dates have been independently certified. No 2022 fold (no eligible training years). No 2026 evaluation because first annual GED is unavailable. Both folds have same training set; dependence must be reported, no significance claims.

Compare (1) global Laplace probability (successes+1)/(n+2), (2) Q1 binary signal (zero vs positive but subthreshold) with shrinkage k=20 toward global probability, (3) country-history shrinkage k=20 toward global probability, using only eligible past rows for that country. No optimization or model selection. All probabilities strictly interior. Report Brier and natural-log loss, Brier skill against global, per-fold denominators/positives and pooled observation-weighted scores. No annual test label used before prediction. A constant risk estimate may dominate due to rare events. This is not a prospective or as-of-certified benchmark; no newly issued forecasts, no changes to the 620 prior prospective predictions.

Implementation must validate source identity, exactly 196 common unique country IDs each year, nonnegative integer counts, correct folds, and no future labels in training. Reproducible results, tests and institutional privacy audit before merge.

## Post-outcome attribution extension (not a blinded analysis)
After the original scores were observed, decompose the Q1-versus-global Brier improvement by the actual annual binary label, on the identical pooled test rows. Each class contributes sum[(p_global-y)^2 - (p_Q1-y)^2]/N; positive contributions favor Q1, negative contributions favor global. Report class sizes and mean probabilities. Empty classes have null mean probabilities and zero contribution. This is a descriptive diagnostic, never a feature or model-selection criterion. Retain all eight cells.
