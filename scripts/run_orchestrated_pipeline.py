from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

from vra.errors import PipelineError
from vra.pipeline import PipelineConfig, run_pipeline

LOGGER = logging.getLogger(__name__)


def _log_event(level: int, event: str, **fields: object) -> None:
    LOGGER.log(level, json.dumps({"event": event, **fields}, ensure_ascii=True, sort_keys=True))


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
    logging.basicConfig(level=logging.INFO, format="%(message)s")
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
            _log_event(
                logging.INFO,
                "orchestrated_run_attempt_started",
                attempt=attempt,
                max_attempts=max_attempts,
                trigger=args.trigger,
            )
            result = run_pipeline(config, trigger=args.trigger, attempt=attempt)
            print(
                f"Pipeline run succeeded. run_id={result['run_id']}, "
                f"attempt={result['attempt']}, status={result['status']}"
            )
            _log_event(
                logging.INFO,
                "orchestrated_run_succeeded",
                run_id=result["run_id"],
                attempt=result["attempt"],
                status=result["status"],
            )
            return
        except PipelineError as exc:
            last_error = exc
            print(f"Pipeline run failed on attempt {attempt}/{max_attempts}: {exc}")
            _log_event(
                logging.WARNING,
                "orchestrated_run_attempt_failed",
                attempt=attempt,
                max_attempts=max_attempts,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            if attempt < max_attempts:
                print(f"Retrying in {args.retry_delay_seconds} seconds...")
                time.sleep(args.retry_delay_seconds)
        except Exception as exc:
            last_error = exc
            print(f"Pipeline run failed on attempt {attempt}/{max_attempts}: {exc}")
            _log_event(
                logging.ERROR,
                "orchestrated_run_untyped_failure",
                attempt=attempt,
                max_attempts=max_attempts,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            if attempt < max_attempts:
                print(f"Retrying in {args.retry_delay_seconds} seconds...")
                time.sleep(args.retry_delay_seconds)

    raise RuntimeError(f"Pipeline failed after {max_attempts} attempts") from last_error


if __name__ == "__main__":
    main()