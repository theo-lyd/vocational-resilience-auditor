# The Vocational Resilience Auditor

A multi-source analytics engineering framework that transforms heterogeneous Destatis raw files into a district-level resilience signal for workforce policy decisions.

## Why This Project Was Upgraded

The repository originally contained only raw datasets and a short project description. It now includes a runnable baseline that implements the requested Medallion-style flow with:

- Robust ingestion from semicolon CSV and GENESIS XML.
- German numeric normalization and null token handling.
- Structured Bronze, Silver, and Gold outputs in DuckDB and Parquet.
- A first resilience score mart and a simple dashboard.
- dbt model scaffolding, tests, CI workflow, and container/dev setup.

## Current Architecture

### Bronze

- Raw input files from `data/raw` are parsed with encoding fallbacks (`utf-8-sig`, `cp1252`, `latin-1`).
- CSV inputs are converted into typed, tidy tabular records.
- XML `VALUE` nodes are flattened using their coordinate syntax (for example: `JAHR`, `KREISE`, `GES`, `BILAG3`).
- Outputs:
	- `data/bronze/vocational_enrollment.parquet`
	- `data/bronze/hospital_capacity.parquet`
	- `data/bronze/vocational_graduates.parquet`

### Silver

- `silver_vocational_enrollment`
- `silver_vocational_enrollment_totals`
- `silver_hospital_capacity`
- `silver_vocational_graduates`
- `silver_vocational_graduates_total`

These are created in DuckDB after type coercion, AGS normalization, and district-level filtering.

### Gold

- `gold_district_resilience` combines graduate forecast proxies with latest hospital bed capacity.
- A district-level score and `risk_band` are generated:
- A quality/SLA monitor now writes `quality_sla_events` to DuckDB and `data/gold/quality_sla_events.csv` for operational visibility.

$$
	ext{resilience\_score} = \frac{\text{forecasted\_graduates}}{\text{total\_beds}}
$$

This baseline uses district linear trend extrapolation on historical graduate outputs from XML.

## Repository Layout

- `src/vra/bronze.py`: ingestion and flattening logic.
- `src/vra/normalization.py`: German number parsing and coordinate parsing.
- `src/vra/silver.py`: Silver SQL transformations in DuckDB.
- `src/vra/gold.py`: forecasting proxy + resilience score.
- `src/vra/pipeline.py`: orchestration.
- `scripts/run_pipeline.py`: entrypoint.
- `models/`: dbt staging/intermediate/mart models.
- `.github/workflows/ci.yml`: CI pipeline.
- `Dockerfile.pipeline`, `Dockerfile.dashboard`, `docker-compose.yml`: containerized execution.
- `.devcontainer/devcontainer.json`: Codespaces/devcontainer bootstrap.
- `app.py`: Streamlit dashboard.

## Quick Start

## Phase-by-Phase Documentation

- Full beginner-friendly implementation and presentation docs are in `docs/phases/README.md`.

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### 2. Run Pipeline

```bash
python scripts/run_pipeline.py
```

### 3. Launch Dashboard

```bash
streamlit run app.py
```

### 4. Run Tests

```bash
pytest -q
```

## dbt Usage

Create a local profile from the example:

```bash
cp profiles.yml.example profiles.yml
```

Then run:

```bash
dbt run --profiles-dir .
dbt test --profiles-dir .
```

## Docker Usage

```bash
docker compose up --build
```

This runs the pipeline service and then serves the Streamlit dashboard.

## Important Notes and Assumptions

- The XML graduate dataset is currently decoded via coordinate codes. Human-readable codebook mapping can be added in a follow-up step by enriching `VALUE-ASSOC` / key metadata joins.
- Vacancy rate is not directly present in the attached hospital dataset. The current baseline uses hospital bed capacity as the demand denominator.
- Forecasting currently uses a linear proxy to keep runtime and dependencies lightweight. Prophet can be added as an optional model layer with regressors.

## Suggested Next Improvements

1. Add a dedicated codebook dimension for XML classification keys and map `BILAG3` and `GES` codes to labels.
2. Add Prophet or hierarchical time-series models and compare against naive/linear baselines.
3. Add geospatial boundaries and choropleth rendering in the dashboard.
4. Add Great Expectations suites for cross-table logic checks (for example, graduates <= enrolled cohort constraints).
5. Add freshness SLA checks and alert routing for delayed monthly/annual updates.
