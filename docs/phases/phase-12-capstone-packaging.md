# Phase 12: Capstone Packaging and Defense Readiness

Status: Completed

## Purpose
Package the full project for academic and industry presentation.

## Business perspective
- Ensures the project is understandable beyond the engineering team.

## Technical and narrative scope
- Prepare architecture narrative, assumptions, and limitations.
- Build reproducibility checklist and demo script.
- Produce final slide deck and Q&A appendix.

## Key outputs
- Final capstone report bundle
- Reproducible demo runbook
- Defense deck and speaking notes

## Done criteria
- A new reviewer can run, understand, and evaluate the project without hidden context.

## What was implemented
- Final capstone report bundle created at `docs/capstone/capstone-report-bundle.md`.
- Reproducible demo runbook created at `docs/capstone/reproducible-demo-runbook.md`.
- Defense deck outline and speaking notes created at `docs/capstone/defense-deck-outline.md`.
- Q&A appendix created at `docs/capstone/qa-appendix.md`.
- End-user launchability improved with:
	- one-command runner `run_entire_system.sh`,
	- Linux clickable launcher `Vocational-Resilience-Auditor.desktop`,
	- launcher discoverability in README.

## Validation commands
```bash
./run_entire_system.sh
```

Alternative manual path:
```bash
python scripts/run_orchestrated_pipeline.py --trigger manual --max-retries 2 --retry-delay-seconds 20
cp profiles.yml.example profiles.yml
dbt run --profiles-dir .
dbt test --profiles-dir .
streamlit run app.py
```
