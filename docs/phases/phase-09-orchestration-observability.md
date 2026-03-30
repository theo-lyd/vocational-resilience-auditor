# Phase 9: Orchestration and Observability

Status: Completed

## Purpose
Operationalize the pipeline with dependable scheduling and monitoring.

## Business perspective
- Guarantees predictable delivery cadence for stakeholders.

## Technical scope
- Build scheduler-ready orchestration entrypoint with retries.
- Add runtime metadata and retry policy.
- Integrate observability equivalent with run and stage telemetry.

## Key outputs
- Orchestrated runner script
- Run logs and stage lineage checks
- Alert routing specification

## Done criteria
- End-to-end scheduled run succeeds with clear monitoring and alert behavior.

## What was implemented
- Added run-level and stage-level observability tables in DuckDB:
	- `pipeline_run_summary`
	- `pipeline_run_events`
- Added CSV observability artifacts:
	- `data/gold/pipeline_run_summary.csv`
	- `data/gold/pipeline_run_events.csv`
- Enhanced `run_pipeline(...)` with runtime context:
	- `run_id`
	- `trigger`
	- `attempt`
	- per-stage status/duration/error capture
- Added orchestration script with retry policy:
	- `scripts/run_orchestrated_pipeline.py`
	- CLI flags: `--max-retries`, `--retry-delay-seconds`, `--trigger`
- Added tests for orchestration CLI and execution path.

## Scheduler examples
```bash
# Manual / local
python scripts/run_orchestrated_pipeline.py --trigger manual

# Cron-like scheduled run
python scripts/run_orchestrated_pipeline.py --trigger cron --max-retries 2 --retry-delay-seconds 30

# CI run context
python scripts/run_orchestrated_pipeline.py --trigger ci --max-retries 1
```

## Alert routing specification
1. If `pipeline_run_summary.status = 'failed'`:
	 - route to `critical` alert channel.
	 - include `run_id`, `attempt`, and `error_message`.
2. If latest `quality_sla_events` has `status = 'fail'`:
	 - route to `data-quality-critical` channel.
3. If latest `quality_sla_events` has `status = 'warn'` and no fail:
	 - route to `data-quality-warning` channel.
4. Include links to:
	 - `data/gold/pipeline_run_summary.csv`
	 - `data/gold/pipeline_run_events.csv`
	 - `data/gold/quality_sla_events.csv`
