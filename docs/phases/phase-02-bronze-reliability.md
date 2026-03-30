# Phase 2: Bronze Reliability (Implemented)

Status: Completed

## 1) Why this phase exists
The project starts with messy raw data. If ingestion is fragile, every downstream model and dashboard can fail.

Business value:
- Reduces operational risk when new statistical releases arrive.
- Improves trust because input files are traceable.

Theory:
- Bronze is the raw, loss-minimized layer of a Medallion architecture.
- Bronze should prioritize completeness and traceability over heavy transformation.

## 2) What was implemented in this repository
- Dynamic source discovery by file pattern for each dataset family.
- Schema-drift-safe union by column name across multiple releases.
- Ingestion metadata generation with checksum and file size.

Technical implementation:
- Source specs and discovery logic in `src/vra/bronze.py`.
- Metadata output file: `data/bronze/ingestion_metadata.parquet` and `.csv`.
- Metadata table load in DuckDB in `src/vra/pipeline.py`.

## 3) How to explain this in presentation
Simple script:
1. "We ingest all matching files, not only one hardcoded filename."
2. "If new columns appear, we union by name so pipeline does not crash."
3. "Every ingested file is logged with checksum and size for auditability."

## 4) Validation performed
- Unit tests: `pytest -q` passed.
- Pipeline still produces Gold outputs and dashboard inputs.

## 5) Deliverables checklist
- [x] Flexible ingestion discovery
- [x] Schema drift tolerance
- [x] Ingestion metadata contract
- [x] Phase documentation
