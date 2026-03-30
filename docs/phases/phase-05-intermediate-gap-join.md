# Phase 5: Intermediate Supply-Demand Gap Join

Status: Completed

## Purpose
Integrate vocational supply and healthcare demand into one analytical layer.

## Business perspective
- Converts siloed datasets into a direct workforce risk signal.

## Technical scope
- Build district-level joins using AGS.
- Create demand and supply feature set.
- Add specialty-level features where available.

## Key outputs
- Intermediate joined mart
- Feature documentation
- Join integrity tests

## Done criteria
- Every district has a deterministic supply-demand record.

## What was implemented
- Rebuilt `int_regional_supply_demand_joined` as a deterministic district feature table.
- Added latest-per-district feature joins for:
	- vocational graduates (`DS_003`, `%TOTAL%`)
	- hospital demand capacity
	- vocational enrollment totals (`school_type = 'Insgesamt'`)
- Added specialty-level hospital features:
	- `beds_surgery`
	- `beds_internal_medicine`
	- `beds_geriatrics`
	- `beds_pediatrics`
	- `beds_neurology`
	- `beds_orthopedics`
	- `beds_psychiatry`
- Added derived features:
	- `supply_demand_gap`
	- `supply_demand_ratio`
	- `psychiatry_capacity_share`
	- `geriatrics_capacity_share`
- Added join integrity controls:
	- unique AGS in intermediate model
	- explicit one-row-per-AGS dbt data test

## Why this matters
- Turns three siloed domains into one district-level analytical surface.
- Creates a stable feature layer for forecasting, policy simulation, and dashboarding.

## Validation commands
```bash
cp profiles.yml.example profiles.yml
dbt run --profiles-dir . --project-dir .
dbt test --profiles-dir . --project-dir .
pytest -q
```
