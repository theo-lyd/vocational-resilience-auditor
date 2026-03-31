# Phase 10: CI/CD and Documentation Automation

Status: Completed

## Purpose
Make the project maintainable with automated quality gates and docs publishing.

## Business perspective
- Improves confidence that changes are safe.
- Provides a shareable live technical catalog.

## Technical scope
- Slim CI with dbt state artifacts.
- PR checks for tests and model selection.
- Build and publish docs artifacts from CI.

## Key outputs
- Enhanced GitHub Actions workflows
- Documentation publishing pipeline
- Release checklist

## Done criteria
- Every PR runs relevant checks only.
- Latest docs bundle is automatically generated as a workflow artifact.

## What was implemented
- CI relevance filtering in `.github/workflows/ci.yml` via `paths-ignore` for docs-only changes, so heavy code checks run when they are relevant.
- Added docs automation in `.github/workflows/docs-pages.yml`:
	- builds pipeline and dbt artifacts,
	- runs `dbt docs generate`,
	- uploads dbt docs plus project docs as a downloadable CI artifact.
- Added closeout/capstone documentation artifacts under `docs/capstone/` for release-ready documentation coverage.

## Validation commands
```bash
python scripts/run_pipeline.py
cp profiles.yml.example profiles.yml
dbt run --profiles-dir .
dbt docs generate --profiles-dir .
ruff check .
mypy
pytest -q
```
