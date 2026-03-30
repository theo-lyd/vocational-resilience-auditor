# Phase 4: SCD Type 2 Snapshots

Status: Completed

## Purpose
Preserve historical truth when school or district attributes change.

## Business perspective
- Policy analysis requires historical consistency.
- Prevents misinterpretation of longitudinal trends.

## Technical scope
- Implement dbt snapshots for changing dimensions.
- Add validity windows (`effective_from`, `effective_to`, `is_current`).
- Add overlap and duplication tests.

## Key outputs
- Snapshot models
- Historical audit views
- Snapshot test suite

## Done criteria
- Historical records are never overwritten.
- Snapshot tests pass in CI.

## What was implemented
- Added dbt snapshot `snp_vocational_enrollment_scd2` with SCD2 history tracking.
- Snapshot strategy uses `check` columns so changes create a new historical version.
- Historical validity windows are available directly from snapshot metadata columns:
	- `dbt_valid_from` (effective start)
	- `dbt_valid_to` (effective end, `null` means current)
- Added historical integrity tests:
	- only one active row per business key
	- no overlapping validity windows for the same business key

## Why this matters
- We can answer: "what did we believe at that time?" without losing old records.
- Longitudinal analysis stays reproducible even if source values are corrected later.

## Runbook
```bash
cp profiles.yml.example profiles.yml
dbt snapshot --profiles-dir . --project-dir .
dbt test --profiles-dir . --project-dir .
```
