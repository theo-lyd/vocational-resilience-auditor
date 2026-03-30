# Phase 3: Silver Normalization

Status: Completed

## Purpose
Convert Bronze raw values into stable, analytics-ready tables with consistent semantics.

## Business perspective
- Decision makers need comparable district data.
- Normalization avoids false trends caused by formatting differences.

## Technical scope completed
- Added deterministic AGS normalization rules for 5-digit and 8-digit source codes.
- Added AGS quality flags to track direct district values vs municipality rollups.
- Added semantic labels for XML gender and degree codes in Silver and dbt staging.
- Added codebook output model for stakeholder-readable semantics.
- Extended unit tests for AGS normalization behavior.

## Key outputs
- Silver AGS standardization with quality flags.
- Semantic code labels:
	- Gender labels from code values.
	- Degree labels from Destatis code tokens.
- dbt codebook model: dim_vocational_graduates_codebook.
- Extended normalization tests in Python.
- Null taxonomy documentation in a dedicated file.

## Validation status
- Python unit tests pass.
- AGS normalization is deterministic and explicit.
- XML semantic columns are human-readable through labels and codebook model.
