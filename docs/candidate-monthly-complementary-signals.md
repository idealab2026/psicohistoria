# Monthly complementary signals: fixed exploratory ablation

2026-11-24. Protocol before new scores; historical labels and previous model results already known. This is not blinded, prospectively issued or historically as-of certified.

Reuse PR159 monthly panel (2021, 2022, 2023, 2025; 2024 remains quarantined). Verify source hashes and exact replay of both previous aggregate reports before scoring. Maintain identical risk sets, outcomes, folds (2023 trained on 2021; 2025 trained on 2021/22/23), eight threshold/horizon cells. No test labels in predictors. Compare the original global Laplace, Q1 nonzero and country-history k=20 probabilities with:

- fixed arithmetic mean of Q1 and country-history (50/50, no fitting weights);
- other violence: binary Q1 positive best for GED types 2 or 3 (non-state or one-sided), same date precision 1/2, same fully contained dates, same last-observed ID union before filtering; shrink its group event frequency to global with k=20;
- equal-weight three-signal pool of Q1, country history and other violence.

No hyperparameter search, threshold selection or outcome-dependent weighting. Report all models per fold and pooled, Brier and log loss, relative Brier skill vs global, mean probability among positives/negatives and differences vs Q1. For T1 the Q1 signal is constant within a threshold-specific risk set. Evaluate the other-violence feature even if it is negative evidence. No claim of improvement over the best retrospectively selected baseline. No country-level probabilities or event records published, no changes to previous 620 forecasts. Only two dependent test years, outcomes are annual GED coded fatalities, not probability of war in general. Any future model selection requires independent validation.
