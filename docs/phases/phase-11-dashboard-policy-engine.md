# Phase 11: Dashboard and Policy Recommendation Layer

Status: Completed

## Purpose
Translate analytics into an explainable decision interface.

## Business perspective
- Helps non-technical stakeholders identify risk districts quickly.

## Technical scope
- Add Germany choropleth map with district drill-down.
- Add forecast and demand trend views.
- Add evidence-based policy recommendation engine with guardrails.

## Key outputs
- Streamlit dashboard v2
- Policy recommendation templates and safety guardrails
- Presentation walkthrough via dashboard tabs

## Done criteria
- Stakeholders can identify high-risk districts and understand recommendations.

## What was implemented
- Created `src/vra/policy_engine.py` module with:
  - Risk-band-specific policy templates (Systemic Risk, Watch, Resilient, Missing Data)
  - Safety guardrails: rejects harmful language, enforces evidence requirements, limits output length
  - Evidence-based recommendations combining risk band, confidence, outlier status, and sensitivity
  - Confidence scoring: uses data completeness and flag status to communicate recommendation reliability
  - Markdown report generation for district drill-down
- Enhanced Streamlit dashboard (`app.py`) with 6 integrated tabs:
  1. **Executive**: headline metrics, risk exposure summary, and auto-generated critical findings
  2. **Risk Diagnostics**: supply-vs-demand diagnostics, demand-gap leaderboard, confidence/sensitivity view
  3. **Model Diagnostics**: backtest quality (MAE) and model reliability comparisons
  4. **Policy Drilldown**: district-level recommendation output with caveats and methodology notes
  5. **Operations**: pipeline run health, quality/SLA checks, and run-over-run change narrative
  6. **Data Explorer**: filterable district table with CSV export
- Added safety guardrails:
  - Rejects unsafe language ("closed", "eliminate", "cut funding entirely")
  - Flags low-confidence recommendations
  - Explains caveats for outliers and sensitive scores
  - Caps recommendation length at 500 characters
- Added narrative insight automation:
  - `Top 5 Critical Findings` generated from latest run metrics
  - `What Changed Since Last Run` generated from pipeline and quality history
- Added comprehensive tests in `tests/test_policy_engine.py`

## Why this matters
- **Non-technical accessibility**: Policy stakeholders see visual dashboard, not raw data.
- **Evidence-based**: Recommendations are tied to methodology (confidence, sensitivity, outliers).
- **Explainability**: Each recommendation includes caveats, so decision-makers understand limits.
- **Safety**: Guardrails prevent harmful or unsupported policy suggestions.

## Future Enhancements
- **Choropleth Integration**: Use GeoPandas + GeoJSON to render interactive Germany district map.
- **LLM Integration**: Optionally integrate Claude API for adaptive policy drafting (with prompt guardrails).
- **Historical Tracking**: Archive recommendations per run for audit trail.

## Validation commands
```bash
python scripts/run_pipeline.py
pytest -q
streamlit run app.py
```
