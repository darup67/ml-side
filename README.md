# ml-side
Side project: Chronos2 / Chronos-Bolt / AutoGluon TimeSeries forecasts of MNQ and MES daily excursions
(open→high, open→low, high→low) over 3 years of Yahoo daily bars. `run.py` fits and backtests; results in
`backtest.json` and `forecast.json`. Finding: models barely beat the 3-year average except MNQ daily range.
Setup: python3.11 venv, `pip install autogluon.timeseries` (scipy pinned to 1.14.1 on this Mac).
