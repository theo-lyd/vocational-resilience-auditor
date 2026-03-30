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
- Enhanced Streamlit dashboard (`app.py`) with 5 integrated tabs:
  1. **Overview**: Quick metrics, risk distribution, score histogram
  2. **Map View**: Geographic summary (GeoJSON integration roadmap noted)
  3. **Trends**: Forecast graduates and hospital beds trends by risk band
  4. **Policy**: Interactive district drill-down with tailored recommendations and caveats
  5. **Details**: Filterable data explorer with CSV export
- Added safety guardrails:
  - Rejects unsafe language ("closed", "eliminate", "cut funding entirely")
  - Flags low-confidence recommendations
  - Explains caveats for outliers and sensitive scores
  - Caps recommendation length at 500 characters
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
