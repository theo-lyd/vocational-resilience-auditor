# Phase 4: SCD Type 2 Snapshots

Status: Planned

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
