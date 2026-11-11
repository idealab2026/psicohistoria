# Q-GEO-01 / NEWCONF — Persistence ablation, 11 Nov 2026

**Status: exploratory post-hoc study; NOT a newly preregistered prospective forecast.**

## Question and fixed candidate

Is the **persistence** of intrastate armed conflict at the prediction origin more informative about a new conflict one or two years later than a binary indicator of active conflict? This experiment fixes **one** additional candidate before executing this new script, and does not optimize windows/thresholds to the outcomes.

- Units: `ANY(newconf=1)` country-years in original UCDP *Intrastate Country Level Multiple Onset*. Repeated conflict episodes are collapsed per country-year.
- Origin and only feature source: **2022**, UCDP/PRIO ACD **23.1**, with all activity years restricted to 2022 or earlier; source ZIP SHA pinned in the repository. Intrastate types 3/4 are already explicitly filtered by `load_activity`.
- Labels for fitting: Multiple Onset **23.1**, only through 2022. Target horizon = 1 or 2 calendar years.
- External comparison labels: Multiple Onset **25.1**, 2023 and 2024, separate release. Both datasets' original byte SHA-256 values are pinned.
- Candidate predictor: 0, 1, or 2+ active years in the three calendar years **[origin−2, origin]**. For each horizon, learn group prevalence smoothed by 20 prior pseudo-observations to the global historical prevalence; country empirical-Bayes mean is then smoothed by 20 to that group prevalence.
- Main comparator: same country empirical-Bayes model, smoothed by 20, but using **binary current-year activity** rather than a three-year activity count. Second comparator: frozen five-year global newconf prevalence.
- Brier, log-loss and country-block bootstrap for Brier difference; both 2023 and 2024 reported, with **no selection of the better horizon or group threshold after scores**.
- All 196 originating countries and 392 evaluated country-years are retained. An unexpected source, changed 2023/24 positive count, missing output or future data causes fail-closed.
- The 2027 NEWCONF and GEO forecast bytes, identifiers, first-public timestamps and evaluation contracts are untouched. Never relabel 2025 activity as a known newconf outcome.

## Interpretation constraints

**The 2023/24 outcomes were already inspected before this hypothesis was formulated**, so even a numerical improvement would be post-hoc exploration rather than confirmatory skill. Three historical external positive country-years are insufficient for a robust performance claim. The country bootstrap does not capture inter-country shared shocks.

The public script `scripts/experiment_newconf_persistence.py` emits aggregate results only: no individual country predictions, labels, or identifiers. Source-frozen comparisons are run in CI; until the check and report are available, **no result or superiority is claimed**.

This ablation concerns national persistence, not a spatial-neighbor effect. A genuine regional-contagion model requires a separately sourced, time-valid geography/border mapping; it must not infer geographic proximity from Gleditsch–Ward IDs.
