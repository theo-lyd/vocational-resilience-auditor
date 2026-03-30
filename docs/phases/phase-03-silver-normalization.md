# Phase 3: Silver Normalization

Status: Planned

## Purpose
Convert Bronze raw values into stable, analytics-ready tables with consistent semantics.

## Business perspective
- Decision makers need comparable district data.
- Normalization avoids false trends caused by formatting differences.

## Technical scope
- Strengthen German numeric and text normalization.
- Add explicit AGS quality rules.
- Create dimension tables for XML code labels.
- Document null/placeholder behavior.

## Key outputs
- Silver data contract
- Extended normalization tests
- Updated data dictionary

## Done criteria
- All Silver models pass tests.
- AGS normalization is deterministic.
- XML code columns are human-readable through mappings.
