# Final Acceptance Checklist with Evidence

Date: 2026-03-30

Purpose: formal closeout evidence for complete project delivery (including phases 10 and 12).

## Acceptance Checklist

- [x] A. Pipeline executes end-to-end successfully.
- [x] B. dbt models run successfully.
- [x] C. dbt tests pass successfully.
- [x] D. Lint checks pass (`ruff`).
- [x] E. Type checks pass (`mypy`).
- [x] F. Test suite passes (`pytest`).
- [x] G. Required gold artifacts exist.
- [x] H. Required DuckDB tables exist and are queryable.
- [x] I. Docs automation workflow exists for Pages publishing.
- [x] J. Capstone bundle artifacts exist.
- [x] K. Single-file full-system runner exists and is executable.
- [x] L. Clickable desktop launcher exists and is executable.

## Evidence Log

### A. Pipeline execution
Status: PASS

Command:
```bash
/workspaces/vocational-resilience-auditor/.venv/bin/python scripts/run_pipeline.py
```

Evidence summary:
- Run completed successfully.
- Reported run id: `run_2b34b86c67e8`.
- All pipeline stages succeeded.

### B. dbt run
Status: PASS

Command:
```bash
cp profiles.yml.example profiles.yml
dbt run --profiles-dir .
```

Evidence summary:
- `PASS=6 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=6`
- Note: non-blocking dbt deprecation warnings remain for `accepted_values` argument nesting.

### C. dbt test
Status: PASS

Command:
```bash
dbt test --profiles-dir .
```

Evidence summary:
- `PASS=20 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=20`

### D. Ruff
Status: PASS

Command:
```bash
/workspaces/vocational-resilience-auditor/.venv/bin/ruff check .
```

Evidence summary:
- `All checks passed!`

### E. mypy
Status: PASS

Command:
```bash
/workspaces/vocational-resilience-auditor/.venv/bin/mypy
```

Evidence summary:
- `Success: no issues found in 13 source files`

### F. pytest
Status: PASS

Command:
```bash
/workspaces/vocational-resilience-auditor/.venv/bin/pytest -q
```

Evidence summary:
- `36 passed in 3.94s`
- Coverage gate met: `Required test coverage of 55% reached. Total coverage: 55.98%`

### G. Gold artifacts present
Status: PASS

Command:
```bash
ls -1 data/gold | sort
```

Evidence summary:
- Required outputs found, including:
	- `dim_district_resilience.csv`
	- `fct_vocational_forecasts.csv`
	- `forecast_error_report.csv`
	- `quality_sla_events.csv`
	- `resilience_methodology_enriched.csv`
	- `pipeline_run_summary.csv`
	- `pipeline_run_events.csv`

### H. DuckDB tables present
Status: PASS

Command:
```bash
/workspaces/vocational-resilience-auditor/.venv/bin/python - <<'PY'
import duckdb
con = duckdb.connect('data/warehouse/vra.duckdb')
tables = sorted([row[0] for row in con.execute('show tables').fetchall()])
required = [
		'bronze_vocational_enrollment',
		'bronze_hospital_capacity',
		'bronze_vocational_graduates',
		'silver_vocational_enrollment',
		'silver_hospital_capacity',
		'silver_vocational_graduates_total',
		'gold_district_resilience',
		'fct_vocational_forecasts',
		'fct_vocational_forecast_errors',
		'pipeline_run_summary',
		'pipeline_run_events',
		'quality_sla_events',
]
missing = [t for t in required if t not in tables]
print('TABLE_COUNT', len(tables))
print('MISSING_REQUIRED', missing)
print('REQUIRED_OK', len(missing) == 0)
PY
```

Evidence summary:
- `TABLE_COUNT 23`
- `MISSING_REQUIRED []`
- `REQUIRED_OK True`

### I. Docs automation workflow present
Status: PASS

Evidence summary:
- Workflow file exists: `.github/workflows/docs-pages.yml`
- Workflow behavior:
	- builds pipeline outputs,
	- runs `dbt docs generate`,
	- publishes dbt and project docs via GitHub Pages.

### J. Capstone bundle files present
Status: PASS

Evidence summary:
- Present in `docs/capstone/`:
	- `capstone-report-bundle.md`
	- `reproducible-demo-runbook.md`
	- `defense-deck-outline.md`
	- `qa-appendix.md`
	- `final-acceptance-checklist.md`

### K. Full-system runner present/executable
Status: PASS

Evidence summary:
- File exists and executable: `run_entire_system.sh`
- Purpose: setup/refresh env, run pipeline, dbt run/test, launch dashboard.

### L. Desktop launcher present/executable
Status: PASS

Evidence summary:
- File exists and executable: `Vocational-Resilience-Auditor.desktop`
- Purpose: clickable Linux launcher for full system run.
