# Phase 8: Data Quality and SLA Controls

Status: Completed

## Purpose
Guarantee data reliability before analytics and dashboard delivery.

## Business perspective
- Reduces risk of incorrect policy recommendations.
- Makes data operations auditable.

## Technical scope
- Add repeatable quality suites in pipeline quality monitor.
- Expand dbt tests for integrity and accepted values.
- Add freshness SLA checks and late-arrival alerts.

## Key outputs
- Quality suites and test artifacts
- SLA monitoring table
- Incident handling guide

## Done criteria
- Critical tests pass in scheduled and CI runs.
- Freshness breaches are visible and actionable.

## What was implemented
- Added pipeline quality monitor in `src/vra/quality.py`.
- Added SLA event table in DuckDB: `quality_sla_events`.
- Exported quality artifacts to:
  - `data/gold/quality_sla_events.parquet`
  - `data/gold/quality_sla_events.csv`
- Added freshness policy checks using `source_last_modified_at` from ingestion metadata.
- Added warning/failure console alerts when SLA breaches appear.
- Expanded dbt tests:
  - accepted values test for enrollment AGS quality flag
  - custom completeness test for hospital `total_beds`

## Incident handling guide (simple runbook)
1. Run pipeline and open `data/gold/quality_sla_events.csv`.
2. Filter rows where `status` is `fail` or `warn`.
3. Prioritize by `severity`:
	- `critical`: block dashboard refresh and investigate source first.
	- `warning`: continue with caution and open follow-up issue.
4. For freshness failures:
	- verify source publication date.
	- verify ingestion file paths in metadata.
	- re-run ingestion after source update.
5. For integrity failures:
	- inspect upstream bronze record quality.
	- tighten normalization or source filters.
6. Log action taken in project notes before closing incident.

## Validation commands
```bash
python scripts/run_pipeline.py
dbt run --profiles-dir . --project-dir .
dbt snapshot --profiles-dir . --project-dir .
dbt test --profiles-dir . --project-dir .
pytest -q
```
