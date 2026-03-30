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

- `gold_district_resilience` combines district forecast outputs with latest hospital bed capacity.
- `fct_vocational_forecasts` stores model-level district forecasts over a 5-year horizon.
- `fct_vocational_forecast_errors` stores district backtest error rows for model benchmarking.
- `forecast_model_card.md` documents assumptions, strengths, limits, and MAE summary.
- A district-level score and `risk_band` are generated:
- A quality/SLA monitor now writes `quality_sla_events` to DuckDB and `data/gold/quality_sla_events.csv` for operational visibility.

$$
	ext{resilience\_score} = \frac{\text{forecasted\_graduates}}{\text{total\_beds}}
$$

The default scoring path now selects the best district model from `naive`, `linear`, and `prophet` (if installed), using holdout-year MAE.

## Repository Layout

- `src/vra/bronze.py`: ingestion and flattening logic.
- `src/vra/normalization.py`: German number parsing and coordinate parsing.
- `src/vra/silver.py`: Silver SQL transformations in DuckDB.
- `src/vra/gold.py`: forecasting proxy + resilience score.
- `src/vra/pipeline.py`: orchestration.
- `scripts/run_pipeline.py`: entrypoint.
- `scripts/run_orchestrated_pipeline.py`: retry-capable orchestration runner.
- `models/`: dbt staging/intermediate/mart models.
- `.github/workflows/ci.yml`: CI pipeline.
- `Dockerfile.pipeline`, `Dockerfile.dashboard`, `docker-compose.yml`: containerized execution.
- `.devcontainer/devcontainer.json`: Codespaces/devcontainer bootstrap.
- `app.py`: Streamlit dashboard.

## Quick Start

- New complete beginner guide: `docs/tutorial-beginner-complete.md`
- In a hurry? Jump straight to the 10-minute fast track: [Quick 10-Minute Path](docs/tutorial-beginner-complete.md#quick-10-minute-path-optional-fast-track)

## Launchers

- One-command full system run (pipeline + dbt + dashboard):

```bash
./run_entire_system.sh
```

- Clickable launcher for Linux desktop environments:
	- `Vocational-Resilience-Auditor.desktop`

Troubleshooting (Linux desktop files):
- If your file manager blocks launching the `.desktop` file as untrusted, right-click it and allow/mark as executable, or run:

```bash
chmod +x Vocational-Resilience-Auditor.desktop
```

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

Orchestrated run with retry and trigger metadata:

```bash
python scripts/run_orchestrated_pipeline.py --trigger cron --max-retries 2 --retry-delay-seconds 30
```

### 3. Launch Dashboard

```bash
streamlit run app.py
```

### 4. Run Tests

```bash
pytest -q
```

### 5. Run Quality Gates

```bash
ruff check .
mypy
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

## Operational Observability

- Run summary artifact: `data/gold/pipeline_run_summary.csv`
- Stage events artifact: `data/gold/pipeline_run_events.csv`
- Quality and SLA artifact: `data/gold/quality_sla_events.csv`
- Forecast artifact: `data/gold/fct_vocational_forecasts.csv`
- Forecast backtest artifact: `data/gold/forecast_error_report.csv`
- Forecast model card: `data/gold/forecast_model_card.md`
- Resilience methodology enriched output: `data/gold/resilience_methodology_enriched.csv`
- Resilience methodology specification: `data/gold/resilience_methodology_spec.md`

## Important Notes and Assumptions

- The XML graduate dataset is currently decoded via coordinate codes. Human-readable codebook mapping can be added in a follow-up step by enriching `VALUE-ASSOC` / key metadata joins.
- Vacancy rate is not directly present in the attached hospital dataset. The current baseline uses hospital bed capacity as the demand denominator.
- The resilience score methodology is formalized for transparency: see `data/gold/resilience_methodology_spec.md` for the complete formula, thresholds, and confidence/sensitivity/fairness rules.
- Forecasting uses benchmarked district models (naive/linear and Prophet when available).

## Data Versioning Policy

- Full raw source files in `data/raw/` are treated as local runtime inputs and are not committed.
- Version-controlled demo fixtures live in `data/raw/samples/`.
- Checksum metadata for local full files is stored in `data/raw/manifest.sha256`.
- Raw data handling details are documented in `data/raw/README.md`.

## Suggested Next Improvements

1. Add a dedicated codebook dimension for XML classification keys and map `BILAG3` and `GES` codes to labels.
2. Add Prophet or hierarchical time-series models and compare against naive/linear baselines.
3. Add geospatial boundaries and choropleth rendering in the dashboard.
4. Add Great Expectations suites for cross-table logic checks (for example, graduates <= enrolled cohort constraints).
5. Add freshness SLA checks and alert routing for delayed monthly/annual updates.
