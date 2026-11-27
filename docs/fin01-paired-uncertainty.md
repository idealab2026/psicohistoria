# FIN-01 paired temporal uncertainty (2026-11-27)

Exploratory post-benchmark analysis, not a new independent test. Use exactly 35 annual paired average loss rows (1990–2024, 12 months per year) from the frozen downside and volatility reports; reconcile point estimates to pooled losses. Circular moving blocks of 1, 3 and 5 consecutive years, 20,000 draws each, LCG seed 27012026 reset per length, multiplier 1664525, increment 1013904223, 32-bit unsigned state; common index draws for all contrasts. Sample exactly 35 years, truncate final block; order statistics 499 and 19499 (zero-based). Skill=1-sum(model losses)/sum(reference losses). Positive fraction is a bootstrap statistic, not future success probability. Assumptions of stable dependence, limited 35-year history, selection on the same data, no multiplicity correction.

Actual independent JS calculation (60,000 temporal resamples), three-year blocks:
| Contrast | Skill | 95% percentile interval |
|---|---:|---:|
| Downside joint vs recent Brier | +2.3363% | [-2.9467%, +7.0923%] |
| Downside joint vs global Brier | +1.0839% | [-2.3188%, +4.3907%] |
| Downside volatility regime vs recent Brier | +0.4344% | [-4.3614%, +5.0851%] |
| HAR vs trailing12 QLIKE | +1.6166% | [-9.2766%, +17.0406%] |
| HAR vs trailing12 volatility MAE | +10.1321% | [+2.2432%, +16.8578%] |
| EWMA vs trailing12 QLIKE | +3.0188% | [-20.9953%, +16.7292%] |
| EWMA vs trailing12 volatility MAE | -3.9454% | [-18.9673%, +6.0138%] |

HAR MAE remains positive at block length 1 [2.6805%,17.4351%] and 5 [2.4061%,15.9784%]; all other intervals include zero for each length. This is a more promising historical signal for absolute volatility error, not proof of economic utility. Primary QLIKE comparison remains uncertain. No forecast changed, no raw source rows published. Reproduction script experiment_fin01_paired_uncertainty.py with independently computed 3-year interval assertions; CI pending.
