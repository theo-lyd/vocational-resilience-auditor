# dbt and DuckDB Commands (Project Usage)

## `cp profiles.yml.example profiles.yml`
- Who: developer/analyst running dbt locally
- What: create local dbt profile config from template
- When: first dbt setup in a clone/environment
- Where: repository root
- Why: dbt requires a profile target to connect to DuckDB
- How: `cp profiles.yml.example profiles.yml`
- Alternatives: define profile in global `~/.dbt/profiles.yml`

## `dbt run --profiles-dir .`
- Who: analytics engineer
- What: build dbt models
- When: after pipeline output refresh or model changes
- Where: repository root
- Why: materialize staging/intermediate/mart layers
- How: `dbt run --profiles-dir .`
- Alternatives: `dbt build --profiles-dir .` (run + test + snapshot depending setup)

## `dbt test --profiles-dir .`
- Who: analytics engineer
- What: execute dbt data tests
- When: after model run and before release
- Where: repository root
- Why: validate data contracts and quality assumptions
- How: `dbt test --profiles-dir .`
- Alternatives: `dbt build --select test_type:data`

## `dbt docs generate --profiles-dir .`
- Who: analytics engineer/documentation pipeline
- What: produce dbt manifest/catalog/docs assets
- When: after dbt run for fresh metadata
- Where: repository root
- Why: support lineage docs and metadata publication
- How: `dbt docs generate --profiles-dir .`
- Alternatives: CI workflow-generated docs artifact

## `dbt deps --profiles-dir .`
- Who: analytics engineer
- What: install dbt package dependencies
- When: if project references dbt packages
- Where: repository root
- Why: ensure package macros/models are available
- How: `dbt deps --profiles-dir .`
- Alternatives: omit if no external packages are used

## `dbt ls --select state:modified+ --state target --profiles-dir .`
- Who: CI engineer/analytics engineer
- What: list changed dbt nodes relative to state artifacts
- When: slim CI and scoped runs
- Where: repository root
- Why: reduce CI runtime by targeting modified graph region
- How: `dbt ls --select state:modified+ --state target --profiles-dir .`
- Alternatives: full run/test when state artifacts are unavailable

## DuckDB quick query via Python
- Who: analyst/developer
- What: inspect warehouse tables
- When: debugging transformations and outputs
- Where: repository root
- Why: validate table existence/content quickly
- How:
```bash
python - <<'PY'
import duckdb
con = duckdb.connect('data/warehouse/vra.duckdb')
print(con.execute('show tables').fetchall())
PY
```
- Alternatives: DuckDB CLI, SQL IDE with DuckDB connector
