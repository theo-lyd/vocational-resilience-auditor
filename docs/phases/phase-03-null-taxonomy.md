# Phase 3 Addendum: Null and Placeholder Taxonomy

Status: Completed

This document explains how placeholder values are interpreted during normalization.

## Why this matters
- Statistical source files use symbols like x and - for missing or suppressed values.
- Without a shared taxonomy, analysts can misread unavailable values as zeros.

## Current normalization behavior

Tokens mapped to null:
- Empty string
- -
- x
- X
- .
- ..
- ...

Numeric handling:
- German decimal comma is converted to dot.
- Thousands separators are removed before numeric parsing.
- K suffix is scaled by 1,000.
- Mio or M suffix is scaled by 1,000,000.

AGS handling:
- 5-digit AGS is district-direct.
- 8-digit AGS is municipality-level and rolled up to first 5 digits.
- Other AGS tokens are treated as invalid and excluded from analytical joins.

## Presentation tip
When presenting to stakeholders, describe null as "value unavailable or not reportable", not "zero".
