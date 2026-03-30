from __future__ import annotations

import argparse
import time
from pathlib import Path

from vra.pipeline import PipelineConfig, run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run pipeline with retry and observability context")
    parser.add_argument("--max-retries", type=int, default=2, help="Number of retries after first failure")
    parser.add_argument(
        "--retry-delay-seconds",
        type=int,
        default=20,
        help="Wait time between retries",
    )
    parser.add_argument(
        "--trigger",
        type=str,
        default="manual",
        help="Execution trigger metadata: manual, cron, ci, airflow",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    config = PipelineConfig(
        project_root=root,
        database_path=root / "data" / "warehouse" / "vra.duckdb",
    )

    max_attempts = max(1, args.max_retries + 1)
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            result = run_pipeline(config, trigger=args.trigger, attempt=attempt)
            print(
                f"Pipeline run succeeded. run_id={result['run_id']}, "
                f"attempt={result['attempt']}, status={result['status']}"
            )
            return
        except Exception as exc:
            last_error = exc
            print(f"Pipeline run failed on attempt {attempt}/{max_attempts}: {exc}")
            if attempt < max_attempts:
                print(f"Retrying in {args.retry_delay_seconds} seconds...")
                time.sleep(args.retry_delay_seconds)

    raise RuntimeError(f"Pipeline failed after {max_attempts} attempts") from last_error


if __name__ == "__main__":
    main()