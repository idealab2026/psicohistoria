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

## Follow-up source discovery and admission protocol (2026-11-27)

COW official catalogue confirms v2024 ends December 2024. The United Nations Dag Hammarskjold Library record https://digitallibrary.un.org/record/4082085?ln=en advertises a dated 17 August 2026 dataset, including names and membership dates; the official guide https://research.un.org/en/unmembers/currentmembers confirms 193 current UN members and ISO/M49 identifiers. The record itself returned HTTP 403 in web retrieval; original CSV bytes and schema not yet obtained. The UKY country-year TXT returned HTTP 404 again. The current maintainers' https://www.globalcoups.com/downloads provides event-level CSV but advertises the country-year, country-month, forecasts and codebook downloads as coming soon. This is the same research lineage, not independent outcome validation.

Admission plan fixed before reading new event outcomes:
1. Preserve the COW v2024 historical target unchanged. Never label an unobserved post-2024 COW membership year as official. Obtain and hash a dated UN source and the pinned COW original. Reconcile all current UN member states to COW codes with a reviewed explicit crosswalk (ISO/M49 not COW). Require a one-to-one mapping for the chosen cohort, no duplicate codes, date inconsistencies or unmatched silent defaults.
2. Report differences in both directions. For non-UN COW members, require separate dated status evidence; do not infer identity or status solely from the difference between 195 and 193. No automatic membership carry-forward or country names as join keys. For 2027 the origin roster must be frozen before target events; distinguish issue-date roster from January 1 membership not yet observed.
3. If an official post-2024 COW vintage is unavailable, an explicitly different fixed-cohort estimand may be used: members at 31 December 2024 under COW v2024, each tracked by its frozen COW code, regardless of subsequent admission changes. This is not a forecast of the dynamic COW state system. Any loss of sovereign executive, successor or ambiguous code after origin requires explicit outcome adjudication; no zero imputation. Before issuance, define and test the same fixed-cohort rule at historical origins, then compare to the dynamic baseline.
4. Freeze source bytes and protocol before calculating new scores. 2025 is retrospective temporal extension (not a genuine as-of forecast; outcomes are already public). No tuning on 2025; keep both calibrated models and recent climatology fixed. For a genuine 2027 prospective issue publish immutable forecasts before 1 January 2027, resolve only after the full year with a complete date-stamped source and preregistered review of coverage. No new or altered forecasts here.

CI repair: add exactly the three new research paths to REPOSITORY, not RELEASE. The initial workflow stopped at the institutional allowlist; it did not reach the bootstrap replay. Do not weaken the gate.
