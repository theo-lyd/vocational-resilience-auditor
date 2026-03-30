# Phase 6: Forecasting with Prophet

Status: Completed

## Purpose
Forecast district-level graduate supply over a 5-year horizon.

## Business perspective
- Enables proactive policy design instead of reactive response.

## Technical scope
- Integrate Prophet model pipeline.
- Keep naive and linear baseline for benchmark.
- Add backtesting and error metrics.

## Key outputs
- Forecast table (`fct_vocational_forecasts`)
- Model card (assumptions, strengths, limits)
- Error report by district

## Done criteria
- Forecast generation is reproducible.
- Performance benchmark documented and explainable.

## What was implemented
- Added a district-level multi-model forecasting engine in the gold layer.
- Implemented three model paths:
	- `naive` baseline (last observed value)
	- `linear` baseline (district trend extrapolation)
	- `prophet` (used automatically when library is available)
- Added district-level backtesting with holdout-year absolute error.
- Added per-district best-model selection based on backtest MAE.
- Added reproducible outputs:
	- `fct_vocational_forecasts` table and CSV/Parquet artifacts
	- `fct_vocational_forecast_errors` table and error report CSV/Parquet
	- model card at `data/gold/forecast_model_card.md`
- Updated resilience scoring to use the selected model at a 5-year horizon.

## Why this matters
- Forecasting is no longer a single-model guess; it is benchmarked and explainable.
- Baselines stay visible, so forecasting quality is auditable for non-technical stakeholders.
- The model card provides transparent assumptions and limits for presentation and governance.

## Validation commands
```bash
python scripts/run_pipeline.py
pytest -q
```
