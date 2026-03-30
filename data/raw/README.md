# Raw Data Policy

This directory is split into two concerns:

- Local full datasets for pipeline execution (not committed): `data/raw/*.csv`, `data/raw/*.xml`
- Committed lightweight fixtures for demo/tests: `data/raw/samples/`

## How to work with full datasets

1. Download the source files to `data/raw/`.
2. Validate checksums against `manifest.sha256` when available.
3. Run the pipeline normally.

## Why full raw files are ignored

- Large source files create noisy diffs and slow clones.
- Source data can be refreshed externally and is reproducible by checksum.
- Repository history remains focused on code and model logic.

## Tracked sample fixtures

Sample files in `data/raw/samples/` are intentionally small and safe to version.
They are for demonstration and quick validation only, not production analytics.
