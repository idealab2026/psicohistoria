# COUP temporal uncertainty — exploratory diagnostic (2026-11-27)

Source: merged COUP calibration, commit eace3f5bf71bbdef2e7066712dcd128413a87719. The 45 annual folds (1980–2024, 8241 country-years, 186 positives) are reused, not held out. Bootstrap applied to frozen rounded annual paired scores, preserving all countries in a sampled year and weighting by annual risk-set size. Circular moving blocks of 1, 3 and 5 years, 20,000 draws each, seed 27012026 reset by length, shared draws across models and metrics, empirical order-statistic interval (indices 499 and 19499 in sorted 20,000 draws). Positive gain means lower loss than comparator. No tuning or fitting.

| Model vs recent | Block length | Brier gain interval | Positive draw fraction |
|---|---:|---|---:|
| country_constrained | 1 | [0.0000027, 0.000529444] | 0.9763 |
| prior5_constrained | 1 | [0.000110291, 0.000589141] | 0.9986 |
| country_constrained | 3 | [-0.00001102, 0.000575229] | 0.97015 |
| prior5_constrained | 3 | [0.000101773, 0.000635508] | 0.9986 |
| country_constrained | 5 | [-0.000041389, 0.000628158] | 0.9519 |
| prior5_constrained | 5 | [0.000093764, 0.000660845] | 0.9986 |

The recurrence candidate has positive Brier intervals at all three block lengths; country-history crosses zero at lengths 3 and 5. Both have positive log-loss intervals vs recent. Direct recurrence vs country-history Brier intervals cross zero; direct log-loss intervals are negative, favoring country-history. Retain both candidates and the baseline. This is post-selection descriptive uncertainty, not a confirmatory test, not a probability of future success, and the circular resampling approximation assumes sufficiently stable dependence despite historical regime changes. Shared data and model development prevent independent confirmation. No new or altered forecasts.

## 2025 source admission

The UKY author site search index advertises country-year data at https://www.uky.edu/~clthyn2/coup_data/powell_thyne_ccode_year.txt but direct retrieval on 2026-11-27 returned HTTP 404 in the available web retrieval, as did https://www.uky.edu/~clthyn2/coup_data/home.htm. No bytes, hash, schema or coverage verified. Do not treat it as admitted or as an independent endpoint. Official COW v2024 explicitly ends December 2024 (https://correlatesofwar.org/data-sets/state-system-membership/). The Powell site warns of tentative coding and planned revisions (https://jonathanmpowell.com/coups/). A separate source-only audit of a dated 2025/2026 risk set and original author bytes is needed before evaluating 2025 or issuing COUP2027. Do not fill the universe by carrying forward all 2024 members without a separately defined and documented estimand.

Reproduce from repository root: `python3 -B scripts/experiment_coup_temporal_uncertainty.py --check`. The initial results were calculated directly from the frozen JSON via an independent JavaScript implementation; Python replay and CI remain to be verified.
