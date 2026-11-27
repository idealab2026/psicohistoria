# FIN-01C — Market direction and expected monthly return (2026-11-27)

Registered before running the new endpoints. Use frozen December 2024 FIZ monthly factors, SHA-256 fc9e41cc3b66c62fa8f565a01fb4c8c0d7962c777303c46b8ab7102190b98ea2, total return (Mkt-RF+RF)/100, US broad equity market, not S&P 500 or an executable portfolio. Targets: calendar-month total return r and binary indicator r>0 (exact zero is nonpositive). Evaluate same 420 consecutive months Jan 1990–Dec 2024. Expanding train from July 1926; information through target t-3 (primary, operational publication lag), t-2 sensitivity. No authentic historical as-of claim. All historical training feature windows use same lag.

Fixed predictions:
- Global expanding mean return and Laplace-smoothed positive frequency.
- Recent last 120 eligible labels mean return and Laplace-smoothed positive frequency (primary reference).
- Volatility regime (12-month sample SD >=5%) with conditional return mean and positive frequency shrunk to corresponding recent prediction with k=24 equivalent observations.
- Joint volatility/momentum regime (same cutoff plus trailing 3-month compounded return <0), same shrinkage.
- Momentum-only regime (trailing 3-month compounded return <0), same shrinkage.
All conditionals use the same history; no tuning or adaptive model choice. Conditional binary probability shrinks raw conditional successes with recent Laplace probability. Conditional mean shrinks observed returns to recent mean. No economic decision/trading rule; use 0 return predictor as extra MSE-only reference, and 0.5 direction probability as extra Brier/log loss reference. Predictions separate marginal quantities, no joint distribution or consistency with FIN-DIC2026 implied. Primary contrast joint vs recent for Brier (direction), secondary MSE (return); global comparator mandatory. Report MAE, Brier, log loss, MSE, observed positive share and average realized return, predicted averages, and chronological slices. No selection based on observed scores, no investment recommendation, raw source data, prospective issue or claim of profitability. Report negative results too.

## Observed results
CI 46047091011 attempt 2, job 140693817298 succeeded after initial unexpected source redirect; the other failed direction run also succeeded on retry. No protocol change. 420 test targets, 274 positive, mean return 0.9447% monthly. Primary lag-3 joint Brier 0.2299060197 vs recent 0.2300656825 (+0.0694% skill) and global 0.2278731259 (-0.8921% skill). Joint MSE 0.0019583977 vs global 0.0019500760 (-0.4267% skill). Vol regime MSE 0.0019497312 vs global (+0.0177% skill), negligible. Global Brier best; no material evidence of timing skill. Frozen data/fin01-direction.json. No issued forecasts changed.
