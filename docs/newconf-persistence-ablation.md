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

## Observed aggregate results (original 23.1 → 25.1 comparison)

Officially reproduced in GitHub Actions, using the sources and frozen external cohort specified above. Exact output is pinned in `data/newconf-persistence-2023-24-ablation.json` and CI now runs the experiment with `--check-report` to reject a byte-level change.

| Candidate | Brier (lower is better) | Log-loss |
|---|---:|---:|
| Country EB + current binary conflict activity | **0.007154106725744002** | **0.033778678521398556** |
| Country EB + 3-year conflict persistence | 0.007183644632859890 | 0.033919852541463960 |
| Global last-five-years prevalence | 0.007600893983553160 | Reference only |

- `Brier(persistence) − Brier(binary) = +0.0000295379071158881`, **against** the added persistence.
- Country bootstrap 95% for this delta: **[-0.00000642701033508, +0.00007471567062404]**, includes zero.
- 2023: persistence Brier `0.009397686976206274` vs binary `0.009358489546916308`; 2024: `0.004969602289513505` vs binary `0.004949723904571695`. Candidate loses in both periods.
- 392 heldout evaluations, only 3 distinct positive country-years; no independent prospective performance certification.

**Predeclared interpretative decision:** retain the simpler binary activity comparator for future research; do not promote persistence on these data. More elaborate thresholds/windows after the fact would constitute exploratory overfitting. This is a legitimate **negative result**. Neither the 2027 forecasts nor their registered comparators are changed.
