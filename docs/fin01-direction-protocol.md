# FIN-01C — Market direction and expected monthly return (2026-11-27)

Registered before running the new endpoints. Use frozen December 2024 FIZ monthly factors, SHA-256 fc9e41cc3b66c62fa8f565a01fb4c8c0d7962c777303c46b8ab7102190b98ea2, total return (Mkt-RF+RF)/100, US broad equity market, not S&P 500 or an executable portfolio. Targets: calendar-month total return r and binary indicator r>0 (exact zero is nonpositive). Evaluate same 420 consecutive months Jan 1990–Dec 2024. Expanding train from July 1926; information through target t-3 (primary, operational publication lag), t-2 sensitivity. No authentic historical as-of claim. All historical training feature windows use same lag.

Fixed predictions:
- Global expanding mean return and Laplace-smoothed positive frequency.
- Recent last 120 eligible labels mean return and Laplace-smoothed positive frequency (primary reference).
- Volatility regime (12-month sample SD >=5%) with conditional return mean and positive frequency shrunk to corresponding recent prediction with k=24 equivalent observations.
- Joint volatility/momentum regime (same cutoff plus trailing 3-month compounded return <0), same shrinkage.
- Momentum-only regime (trailing 3-month compounded return <0), same shrinkage.
All conditionals use the same history; no tuning or adaptive model choice. Conditional binary probability shrinks raw conditional successes with recent Laplace probability. Conditional mean shrinks observed returns to recent mean. No economic decision/trading rule; use 0 return predictor as extra MSE-only reference, and 0.5 direction probability as extra Brier/log loss reference. Predictions separate marginal quantities, no joint distribution or consistency with FIN-DIC2026 implied. Primary contrast joint vs recent for Brier (direction), secondary MSE (return); global comparator mandatory. Report MAE, Brier, log loss, MSE, observed positive share and average realized return, predicted averages, and chronological slices. No selection based on observed scores, no investment recommendation, raw source data, prospective issue or claim of profitability. Report negative results too.
