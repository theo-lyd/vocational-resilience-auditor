#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

echo "[1/6] Entering project root: $ROOT_DIR"
cd "$ROOT_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "[2/6] Creating virtual environment"
  python3 -m venv "$VENV_DIR"
else
  echo "[2/6] Virtual environment already exists"
fi

echo "[3/6] Activating virtual environment"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "[4/6] Installing/refreshing dependencies"
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

if [[ ! -f "$ROOT_DIR/profiles.yml" && -f "$ROOT_DIR/profiles.yml.example" ]]; then
  echo "[5/6] Creating profiles.yml from profiles.yml.example"
  cp "$ROOT_DIR/profiles.yml.example" "$ROOT_DIR/profiles.yml"
else
  echo "[5/6] profiles.yml already present"
fi

echo "[6/6] Running full data system"
echo " - Pipeline (with retry-aware runner)"
python scripts/run_orchestrated_pipeline.py --trigger manual --max-retries 2 --retry-delay-seconds 20

echo " - dbt run"
dbt run --profiles-dir .

echo " - dbt test"
dbt test --profiles-dir .

echo " - Launching dashboard"
echo "Dashboard will be available on the local Streamlit URL (usually http://localhost:8501)."
exec streamlit run app.py
