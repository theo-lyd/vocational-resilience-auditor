# Complete Beginner Tutorial: Vocational Resilience Auditor

This tutorial is written for someone who is completely new to data engineering projects.

Goal: by the end, you will be able to run the full pipeline, run dbt models/tests, open the dashboard, and verify quality checks without external help.

Time needed:
- First full run: 45-90 minutes (depending on internet speed and machine setup)
- Repeat run after setup: 5-15 minutes

## Quick 10-Minute Path (Optional Fast Track)

Use this if you want the shortest route to a successful local run first, then come back for full explanations.

1. Clone and enter the repo:

```bash
git clone https://github.com/theo-lyd/vocational-resilience-auditor.git
cd vocational-resilience-auditor
```

2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

3. Install dependencies:

```bash
pip install -r requirements.txt
pip install -e .
```

4. Run pipeline:

```bash
python scripts/run_pipeline.py
```

5. Run dbt:

```bash
cp profiles.yml.example profiles.yml
dbt run --profiles-dir .
dbt test --profiles-dir .
```

6. Start dashboard:

```bash
streamlit run app.py
```

7. Run quality checks:

```bash
ruff check .
mypy
pytest -q
```

If every command above succeeds, your replication is complete. Continue with the rest of this document to understand each stage deeply.

---

## 1. What This Project Does (Plain English)

This project combines public data sources and produces one district-level signal called a resilience score.

At a high level:
- Input data: vocational education + hospital capacity data in CSV/XML files.
- Processing: clean/normalize data and model it in a Medallion flow (Bronze -> Silver -> Gold).
- Output: district risk bands (`Systemic Risk`, `Watch`, `Resilient`) and policy-ready tables.
- Presentation: Streamlit dashboard for interactive exploration.

The central database is DuckDB at `data/warehouse/vra.duckdb`.

---

## 2. Prerequisites (Install These First)

You need:
- `git`
- `python` (3.10 or newer; 3.11 recommended)
- `pip`

Optional but useful:
- `docker` and `docker compose`

Check versions:

```bash
git --version
python3 --version
pip3 --version
```

If Python is missing, install Python first, then re-run those checks.

---

## 3. Get the Code

```bash
git clone https://github.com/theo-lyd/vocational-resilience-auditor.git
cd vocational-resilience-auditor
```

Confirm you are on the default branch:

```bash
git branch --show-current
```

Expected: `master`

---

## 4. Create a Clean Python Environment

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Then install dependencies:

```bash
pip install -r requirements.txt
pip install -e .
```

What this does:
- `requirements.txt` installs runtime + tooling dependencies.
- `pip install -e .` installs this project as an editable package (code changes are picked up immediately).

---

## 5. Understand the Project Structure (Minimal Map)

Important folders/files:
- `data/raw/`: local raw inputs.
- `data/bronze/`: first standardized outputs (parquet/csv).
- `data/gold/`: final analytics outputs + observability artifacts.
- `data/warehouse/vra.duckdb`: DuckDB warehouse.
- `src/vra/bronze.py`: raw ingest + parse logic.
- `src/vra/silver.py`: SQL transformations to curated tables.
- `src/vra/gold.py`: forecasts + resilience score + risk banding.
- `src/vra/pipeline.py`: orchestrates complete execution with retries and observability.
- `scripts/run_pipeline.py`: basic runner.
- `scripts/run_orchestrated_pipeline.py`: advanced retry-aware runner.
- `models/`: dbt staging/intermediate/mart layer.
- `app.py`: Streamlit dashboard.
- `tests/`: unit and property-based tests.

---

## 6. Data Policy You Must Know

Raw full source files are intentionally not committed by default.

Rules:
- Full raw files stay local in `data/raw/`.
- Versioned demo fixtures are in `data/raw/samples/`.
- Checksums of local full files are in `data/raw/manifest.sha256`.

Read details:
- `data/raw/README.md`

If you only want to test mechanics, sample files are enough for a lightweight understanding.

---

## 7. Run the Pipeline End-to-End

Basic run:

```bash
python scripts/run_pipeline.py
```

Or retry-capable orchestrated run:

```bash
python scripts/run_orchestrated_pipeline.py --trigger manual --max-retries 2 --retry-delay-seconds 20
```

What happens internally:
1. Bronze ingest from `data/raw/` into parquet artifacts.
2. Bronze parquet loaded into DuckDB tables.
3. Silver transformations produce cleaned district-level tables.
4. Gold logic computes forecasts, resilience score, and risk band.
5. Methodology and quality/SLA artifacts are generated.
6. Run summary/events are stored for observability.

Expected completion message includes a `run_id`.

---

## 8. Verify Outputs (Do Not Skip)

Check that key files exist:

```bash
ls -la data/bronze
ls -la data/gold
ls -la data/warehouse
```

You should see outputs such as:
- `data/gold/dim_district_resilience.csv`
- `data/gold/fct_vocational_forecasts.csv`
- `data/gold/forecast_error_report.csv`
- `data/gold/resilience_methodology_enriched.csv`
- `data/gold/quality_sla_events.csv`
- `data/gold/pipeline_run_summary.csv`
- `data/gold/pipeline_run_events.csv`

Check DuckDB tables quickly:

```bash
python - <<'PY'
import duckdb
con = duckdb.connect('data/warehouse/vra.duckdb')
tables = con.execute("show tables").fetchall()
print('TABLES:', len(tables))
for t in sorted(x[0] for x in tables):
    print('-', t)
PY
```

---

## 9. Run dbt Models and Tests

This project includes dbt models over the warehouse.

### 9.1 Create local dbt profile

```bash
cp profiles.yml.example profiles.yml
```

### 9.2 Run dbt build steps

```bash
dbt run --profiles-dir .
dbt test --profiles-dir .
```

Optional snapshot run (if snapshot path is configured and used):

```bash
dbt snapshot --profiles-dir .
```

If dbt command is missing:
- confirm your venv is active.
- reinstall dependencies with `pip install -r requirements.txt`.

---

## 10. Launch the Dashboard

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit (usually `http://localhost:8501`).

Dashboard tabs explain:
- Executive summary and auto-generated top findings
- Risk diagnostics (supply vs demand and demand-gap leaderboard)
- Model diagnostics (backtest quality and MAE comparison)
- Policy drilldown with district-level recommendation and notes
- Operations health (pipeline/quality checks and run-over-run change notes)
- Detailed downloadable data explorer

If dashboard says gold output is missing:
- run the pipeline first.

---

## 11. Run Quality Gates (Local CI Replica)

Run the same categories checked by CI:

```bash
ruff check .
mypy
pytest -q
```

Coverage is enforced by pytest config in `pyproject.toml`.

If tests fail:
- run `pytest -q -x` to stop at first failure.
- read error trace and fix one issue at a time.

---

## 12. Explain the Medallion Flow Like a Beginner

### Bronze (Raw -> Structured)
- Reads source files as-is.
- Handles encoding issues and parsing differences.
- Outputs parquet files with standardized columns.

### Silver (Structured -> Clean Business-Ready)
- Normalizes AGS district identifiers.
- Filters invalid rows.
- Produces coherent district-level tables for analytics.

### Gold (Clean -> Decision Layer)
- Creates forecasts per district.
- Chooses best model among available options.
- Computes resilience score:

$$
\text{resilience\_score} = \frac{\text{forecasted\_graduates}}{\text{total\_beds}}
$$

- Assigns risk bands for policy interpretation.

---

## 13. Common Errors and How To Fix Them

### Error: `dbt: command not found`
Cause: venv not active or dependencies not installed.
Fix:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Error: pipeline cannot find raw files
Cause: expected files are missing in `data/raw/`.
Fix:
- place required raw source files in `data/raw/`.
- ensure filenames match expected patterns in `src/vra/bronze.py`.
- if full raw files are unavailable, keep versioned fixtures in `data/raw/samples/` (pipeline falls back to samples automatically).

### Error: `ModuleNotFoundError: vra`
Cause: package not installed in editable mode.
Fix:
```bash
pip install -e .
```

### Error: dashboard empty or warning shown
Cause: pipeline not yet run or outputs missing.
Fix:
```bash
python scripts/run_pipeline.py
```

---

## 14. Reproduce from Scratch Checklist

Use this as your no-assistance completion checklist:

1. Clone repo and enter folder.
2. Create/activate `.venv`.
3. Install dependencies and editable package.
4. Run pipeline successfully.
5. Confirm `data/warehouse/vra.duckdb` exists.
6. Confirm key gold artifacts exist.
7. Run `dbt run` and `dbt test` successfully.
8. Run `ruff check .`, `mypy`, and `pytest -q` successfully.
9. Start dashboard and verify it loads district data.
10. Re-run orchestrated pipeline with retries.

If all 10 pass, you can independently replicate and operate this project.

---

## 15. Next Steps After You Master Basics

Suggested progression:
1. Read `src/vra/pipeline.py` and trace each stage function call.
2. Read `src/vra/gold.py` to understand model selection/backtesting.
3. Explore dbt models in `models/staging`, `models/intermediate`, and `models/marts`.
4. Add one new test in `tests/` and run full checks.
5. Add one new dashboard chart in `app.py`.

This sequence builds confidence from operator -> contributor.
