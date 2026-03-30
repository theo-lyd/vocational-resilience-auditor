# Capstone Report Bundle

## Executive Summary
The Vocational Resilience Auditor is a reproducible analytics system that ingests heterogeneous German public datasets and produces district-level workforce resilience indicators for policy use.

## Problem Statement
Regional workforce supply-demand mismatches are difficult to monitor when source data is fragmented across formats and reporting standards.

## Solution Overview
The project implements a Medallion-style data architecture:
- Bronze: robust parsing and schema stabilization.
- Silver: AGS normalization, code mapping, and curated district tables.
- Gold: forecast selection, resilience scoring, risk banding, and policy-ready outputs.

## Architecture Narrative
- Ingestion and normalization modules handle CSV/XML and German numeric formats.
- DuckDB serves as the analytical warehouse for transformation and serving layers.
- dbt models enforce modeling consistency and tests.
- Pipeline observability captures run summaries, stage events, and quality SLA outcomes.
- Streamlit dashboard provides stakeholder-accessible views and policy recommendations.

## Core Assumptions
- Hospital bed capacity approximates healthcare demand baseline.
- Historical graduates represent a practical short-horizon supply proxy.
- District-level modeling provides useful local signal despite data constraints.

## Known Limitations
- Vacancy rate is not directly available in current raw sources.
- Some explanatory labels in XML source coding may require future enrichment.
- Forecasting excludes exogenous shocks and policy discontinuities.

## Validation Summary
- Pipeline execution: green.
- dbt run/test/snapshot: green.
- Quality gates (ruff, mypy, pytest with coverage): green.
- Dashboard launch and data rendering: available.

## Deliverables in this bundle
- Reproducible runbook: `docs/capstone/reproducible-demo-runbook.md`
- Defense deck outline: `docs/capstone/defense-deck-outline.md`
- Q&A appendix: `docs/capstone/qa-appendix.md`
- Final acceptance checklist: `docs/capstone/final-acceptance-checklist.md`
