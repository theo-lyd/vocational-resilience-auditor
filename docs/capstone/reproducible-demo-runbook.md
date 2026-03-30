# Reproducible Demo Runbook

Audience: reviewer or evaluator with no prior project context.

## Objective
Run the full Vocational Resilience Auditor system end-to-end and validate outputs.

## Prerequisites
- Linux/macOS shell
- Python 3.10+
- Internet access for package installation

## Fast execution options
- One-command runner:
  - `./run_entire_system.sh`
- Clickable launcher (Linux desktop):
  - `Vocational-Resilience-Auditor.desktop`

## Manual verification flow
1. Create and activate virtual environment.
2. Install dependencies.
3. Run orchestrated pipeline.
4. Run dbt models and tests.
5. Run quality gates (ruff, mypy, pytest).
6. Launch dashboard.

## Command sequence
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
python scripts/run_orchestrated_pipeline.py --trigger manual --max-retries 2 --retry-delay-seconds 20
cp profiles.yml.example profiles.yml
dbt run --profiles-dir .
dbt test --profiles-dir .
ruff check .
mypy
pytest -q
streamlit run app.py
```

## Evidence to collect
- Terminal output showing pipeline success with run_id.
- dbt summary with all models/tests passing.
- Quality gate output with zero lint/type/test failures.
- Dashboard opening locally and displaying district rows.

## Troubleshooting shortcuts
- Missing dbt binary:
  - Ensure `.venv` is active.
  - Re-run `pip install -r requirements.txt`.
- Missing raw files:
  - Confirm data is present under `data/raw/`.
- Desktop launcher blocked:
  - `chmod +x Vocational-Resilience-Auditor.desktop`
