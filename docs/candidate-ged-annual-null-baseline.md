# PSICOHISTORIA · Retrospective UCDP Candidate/GED label agreement versus the zero rule

**Study date:** 2026-11-24. **Class:** source-label consistency diagnostic only. The eight analyses are computed on already observed and published labels; this is **not blinded, not prospective, not a predictive model backtest and not an as-of-certified evaluation**.

## Research question and fixed design

How much of the apparently high agreement between UCDP Candidate Q3 and first annual GED can be explained by the prevalence of negative outcomes?

Use the same country-year risk set and outcome definitions as the frozen reports #151–#154: 196 GWNO countries, years 2021, 2022, 2024, 2025 (2023 deliberately excluded), origin Q1 Candidate state-based violence strictly below a threshold, Candidate Q3 target and the **first annual GED** for that year. Full evaluation grid: threshold **1, 5, 10, 25 deaths** and fixed target windows **30/90 days**. We do **not** optimize those choices on this result, and risk-set size changes with threshold.

The comparator deliberately predicts **zero GED positives for every country-year in the SAME risk set**, without seeing Candidate Q3. This is a trivial constant classification policy, **not a meaningful deployable predictive baseline**. We are examining retrospective label agreement, not the ability to predict violence.

For each cell, reconcile four exclusive counts from the frozen annual matrices: both positive (TP), Candidate-only (FP), GED-only (FN) and both negative (TN); enforce identical four-year total and SHA-256 of the previous frozen source before calculating any metrics.

- Candidate-to-annual agreement = (TP + TN) / N.
- Always-negative-to-annual agreement = (TN + FP) / N.
- Difference in percentage points = 100 × (TP − FP) / N.
- Positive-label correspondence = TP/(TP+FP); annual-label recall = TP/(TP+FN).
- Additional descriptive controls: specificity, balanced agreement and Matthews correlation. Undefined denominators are `null`, never zero or 100%.
- Explicitly preserve each year's raw confusion counts and **all eight grid cells** to avoid selective reporting.

## Reproducible results

| Threshold (deaths) | Days | Risk country-years | TP | Candidate-only | GED-only | TN | Candidate agreement | Always-negative agreement |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 30 | 598 | 5 | 6 | 2 | 585 | 98.66% | 98.83% |
| 1 | 90 | 598 | 11 | 18 | 2 | 567 | 96.66% | 97.83% |
| 5 | 30 | 642 | 5 | 5 | 0 | 632 | **99.22%** | **99.22%** |
| 5 | 90 | 642 | 10 | 15 | 2 | 615 | **97.35%** | **98.13%** |
| 10 | 30 | 661 | 6 | 1 | 2 | 652 | 99.55% | 98.79% |
| 10 | 90 | 661 | 13 | 9 | 2 | 637 | 98.34% | 97.73% |
| 25 | 30 | 688 | 2 | 1 | 0 | 685 | 99.85% | 99.71% |
| 25 | 90 | 688 | 10 | 2 | 2 | 674 | 99.42% | 98.26% |

**Primary interpretive result:** under the 5-death, 30-day retrospective label criterion, Candidate has 637 agreements out of 642, precisely the same as classifying all 642 observations as annual-GED-negative. For 90 days, Candidate has 625 agreements against 630 with the constant negative rule, a deficit of **0.78 percentage points**. The 30-day positive-label correspondence is just 5/10 and the 90-day correspondence is 10/25; neither is forecast precision. This illustrates the **base-rate illusion**, not proof that Candidate is useless for real-time situational awareness.

**Interpretation boundary:** thresholds have **different Q1 risk sets**, GED and Candidate use different inclusion rules, years and countries are dependent, and GED annual retrospectively uses information not available at Candidate release. Do not promote the seemingly favorable 10/25 thresholds as operational winners: no true out-of-time forecast test was conducted here. In particular, the prospective 620 forecasts for 2027/2028 remain frozen and unrevised. No new 2026 forecast or confirmation is issued.

The official UCDP methodology says GED retains episodes of dyads that have crossed the annual 25-death criterion in *any* year, including their nonactive years, whereas Candidate includes preliminary records with relaxed eligibility criteria. This explains why the two labels are **not interchangeable measurements**. See [official methodology](https://www.uu.se/en/department/peace-and-conflict-research/research/ucdp/ucdp-methodology.html) and [historical editions](https://ucdp.uu.se/downloads/olddw.html).

## Artifacts and integrity

- Input: [frozen four-year source comparison](../data/candidate-ged-2021-22-resolution.json), protected by its exact SHA-256.
- Computation: [8-cell source agreement script](../scripts/audit_candidate_ged_annual_null_baseline.py).
- Results: [frozen 8-cell JSON and four annual strata per cell](../data/candidate-ged-annual-null-baseline-audit.json).
- CI: `--check-report` exact replay, adversarial negative/marginal/empty-denominator tests and institutional publication privacy gate.

**Follow-up decision:** Keep separate labels for (i) provisional Candidate source events, (ii) first annual GED-confirmed eligibility and (iii) genuinely verified prospective forecasts. Future research should assess actual time-available snapshots, prevalence-aware probabilistic skill (Brier/log-loss) and policy costs with independent temporal holdouts. Do **not** calibrate the forecast model from the retrospective agreement diagnostic.
