# Python Commands (Project Usage)

## `python3 -m venv .venv`
- Who: developer/contributor
- What: create isolated Python environment
- When: first setup in a clone
- Where: repository root
- Why: reproducible dependencies and reduced global conflicts
- How: `python3 -m venv .venv`
- Alternatives: `conda`, `poetry`, `pipenv`

## `python -m pip install --upgrade pip`
- Who: developer
- What: update pip installer in active environment
- When: after venv creation
- Where: activated venv shell
- Why: improve resolver behavior and package install reliability
- How: `python -m pip install --upgrade pip`
- Alternatives: `pip install --upgrade pip`

## `pip install -r requirements.txt`
- Who: developer/CI
- What: install project dependencies
- When: setup and CI install phase
- Where: activated venv
- Why: ensure runtime/tooling package availability
- How: `pip install -r requirements.txt`
- Alternatives: lockfile-driven install if available

## `pip install -e .`
- Who: developer
- What: editable install of local package
- When: after dependency install for local development
- Where: repository root in active venv
- Why: code changes reflect immediately without reinstall
- How: `pip install -e .`
- Alternatives: `pip install .` for non-editable install

## `python scripts/run_pipeline.py`
- Who: analyst/engineer/operator
- What: run full medallion pipeline once
- When: produce fresh outputs for analytics/dashboard
- Where: repository root
- Why: generate bronze/silver/gold artifacts and observability records
- How: `python scripts/run_pipeline.py`
- Alternatives: orchestrated runner with retries

## `python scripts/run_orchestrated_pipeline.py --trigger manual --max-retries 2 --retry-delay-seconds 20`
- Who: operator/engineer
- What: run pipeline with retry and trigger metadata
- When: robust execution in scheduled/manual operations
- Where: repository root
- Why: improve resilience and traceability of runs
- How: command above
- Alternatives: plain pipeline script for simpler local runs

## `streamlit run app.py`
- Who: analyst/stakeholder/demo presenter
- What: start dashboard web app
- When: review and communicate insights
- Where: repository root
- Why: interactive access to metrics, diagnostics, and policy narratives
- How: `streamlit run app.py`
- Alternatives: containerized dashboard startup via docker compose

## `pytest -q`
- Who: developer/CI
- What: run full test suite with concise output
- When: before merge/release and in CI
- Where: repository root
- Why: catch regressions and enforce coverage gate from project config
- How: `pytest -q`
- Alternatives: `pytest -q -x` for stop-on-first-failure

## `mypy`
- Who: developer/CI
- What: static type checking
- When: quality gate before merge
- Where: repository root with configured scope
- Why: catch typing/contract errors early
- How: `mypy`
- Alternatives: Pyright/Pylance strict checks

## `ruff check .`
- Who: developer/CI
- What: lint and style checks
- When: quality gate before merge
- Where: repository root
- Why: maintain code quality and consistency
- How: `ruff check .`
- Alternatives: flake8 + isort + pycodestyle stack
