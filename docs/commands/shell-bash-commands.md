# Shell/Bash Commands (Project Usage)

## `source .venv/bin/activate`
- Who: developer
- What: activate Python virtual environment in current shell
- When: before running Python/dbt/test tools
- Where: repository root (or shell with access to `.venv`)
- Why: ensure correct dependency versions and executables
- How: `source .venv/bin/activate`
- Alternatives: explicit binary paths (e.g., `.venv/bin/python`)

## `chmod +x <file>`
- Who: developer
- What: add executable permission
- When: after creating launcher/shell scripts
- Where: repository root
- Why: allow direct execution and desktop launcher usability
- How: `chmod +x run_entire_system.sh`
- Alternatives: invoke script via `bash script.sh` without executable bit

## `ls -la <path>`
- Who: developer/operator
- What: list files with metadata
- When: output verification and debugging
- Where: any directory
- Why: confirm artifact existence, permissions, and timestamps
- How: `ls -la data/gold`
- Alternatives: `find <path> -type f`, file explorer

## `find <path> -type f`
- Who: developer/operator
- What: recursively list files
- When: inventory and fixture checks
- Where: repository root or target directory
- Why: verify expected project artifacts/files
- How: `find data/raw -maxdepth 3 -type f`
- Alternatives: `ls -R`, IDE file tree

## `grep -RIn "<pattern>" <paths>`
- Who: developer/reviewer
- What: recursive text search with line numbers
- When: documentation/code audit and refactor support
- Where: repository root
- Why: locate stale text or implementation references quickly
- How: `grep -RIn "GitHub Pages" docs README.md`
- Alternatives: `rg` (faster, preferred when available)

## `head -n <N> <file>`
- Who: developer/analyst
- What: show top lines/rows of a file
- When: quick schema/data sanity checks
- Where: repository root
- Why: inspect CSV headers and sample content quickly
- How: `head -n 2 data/gold/dim_district_resilience.csv`
- Alternatives: `sed -n '1,5p'`, spreadsheet viewer

## `timeout <seconds> <command>`
- Who: developer
- What: run command with max duration
- When: smoke tests for long-running services
- Where: shell
- Why: validate startup without hanging terminal
- How: `timeout 15 streamlit run app.py --server.headless true`
- Alternatives: run in background and stop manually
