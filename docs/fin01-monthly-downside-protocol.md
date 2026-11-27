# FIN-01 monthly downside — protocol v1 (2026-11-27)

Registered before downloading or scoring the archive. Endpoint: US broad equity market total return <= -5% in one calendar month, not an intramonth drawdown, SP500 price index, or tradable instrument return. Data: Kenneth French Fama/French 3 Factors monthly legacy December 2024 archive, https://mba.tuck.dartmouth.edu/pages/faculty/Ken.french/data_library_202412_archive.html ; exact official ZIP https://mba.tuck.dartmouth.edu/pages/faculty/Ken.french/ftp_202412/F-F_Research_Data_Factors_CSV.zip ; market definition https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library/f-f_factors.html . Market total return = (Mkt-RF + RF)/100. Copyright belongs to source owners; no raw observations or country/security portfolios redistributed. Record archive hash, byte size, first and last month, schema, and aggregate metrics. Source bytes not yet verified.

## Design

Monthly nonoverlapping labels July 1926–December 2024. Evaluate all 420 months January 1990–December 2024 with expanding training. Historical reconstruction uses one modern archive, not authentic vintage data at each past origin; no as-of claim. Use information through t-2 only (one full calendar month gap before target t), because the monthly research series is released with delay. A gap does not prove availability in historical time. No target t-1 or t used in predictions. No optimizing on evaluation data.

- Global: Laplace-smoothed expanding historical event frequency.
- Recent: Laplace-smoothed last 120 eligible monthly labels (10 years); primary baseline.
- Gaussian volatility: zero-mean normal with sample standard deviation of past 12 monthly returns; probability Phi(-0.05/sigma). Clip to [0.001,0.999] for finite log loss; deliberately simple baseline.
- Empirical volatility regime: fixed cutoff monthly trailing 12-month sample SD >= 5%; regime-specific historical event frequency shrunk to recent rate with k=24 equivalent observations. Training features for each historical label also end at its own t-2. Primary candidate.
- Secondary empirical joint regime: same volatility flag and trailing three-month compounded return < 0; same shrinkage and cutoff, no tuning. Both candidates retained regardless of result.

Score pooled Brier and log loss, Brier skill vs recent, observed and mean forecast probability, yearly summaries and chronological 1990–2004 / 2005–2014 / 2015–2024 slices. Report sensitivity to dropping calendar years, not infer confidence from independent months. No trading backtest, costs, investment recommendation, prospective forecast or economic utility claim. No source raw data published. Future step: exact July-vintage or authentic as-of checks, current edition source and issue receipts, monthly prospective forecasts, executable instrument/decision utility separately. No unrelated project changes.
