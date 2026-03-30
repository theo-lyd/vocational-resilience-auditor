from __future__ import annotations

from pathlib import Path

from vra.pipeline import PipelineConfig, run_pipeline


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    config = PipelineConfig(
        project_root=root,
        database_path=root / "data" / "warehouse" / "vra.duckdb",
    )
    result = run_pipeline(config, trigger="manual", attempt=1)
    print(
        "Pipeline completed. "
        f"run_id={result['run_id']}. "
        "Outputs written to data/bronze, data/gold, and data/warehouse."
    )
