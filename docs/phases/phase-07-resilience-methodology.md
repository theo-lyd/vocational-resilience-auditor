# Phase 7: Resilience Score Methodology

Status: Completed

## Purpose
Formalize the business metric used for policy decisions.

## Business perspective
- Transparent methodology increases trust among public stakeholders.

## Technical scope
- Define exact formula, thresholds, and interpretation.
- Add confidence and sensitivity analysis.
- Add fairness and outlier checks.

## Key outputs
- Metric specification document
- SQL implementation notes
- Validation report

## Done criteria
- Score logic is reproducible and defendable in thesis review.

## What was implemented
- Created `src/vra/resilience_methodology.py` module with:
  - Core formula: `forecasted_graduates / total_beds`
  - Static thresholds: Systemic Risk (<1.0), Watch (1.0–2.0), Resilient (≥2.0)
  - Confidence scoring (0.0–1.0) reflecting data completeness and forecast model choice
  - Sensitivity analysis: ±10% bed capacity change impact on score
  - Outlier detection: flagging districts outside 5–95th percentile range
  - Fair-scoring checks: extreme risk-band mismatches
- Added enrichment function `enrich_resilience_with_methodology()` for output columns:
  - `confidence_score`
  - `sensitivity_impact`
  - `outlier_flag`
  - `methodology_notes` (human-readable explanations)
- Generated automatic `resilience_methodology_spec.md` document during pipeline runs:
  - Includes formula, thresholds, confidence rules, sensitivity rules
  - Validates distribution and flags counts
  - Guidance for policymakers
- Added exports:
  - `data/gold/resilience_methodology_enriched.csv` and `.parquet`
  - `data/gold/resilience_methodology_spec.md` (regenerated each run)
- Added comprehensive tests in `tests/test_resilience_methodology.py`

## Why this matters
- Resilience scoring is now **transparent and reproducible**, not a black box
- **Confidence intervals** show data reliability per district
- **Sensitivity analysis** reveals decision brittleness
- **Outlier flags** guide investigative focus for exceptions
- **Specification document** is audit-ready for thesis and governance reviewers

## Validation commands
```bash
python scripts/run_pipeline.py
pytest -q
```

