from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4

import duckdb
import pandas as pd

from .bronze import BronzeConfig, write_bronze_outputs
from .errors import (
    ObservabilityWriteError,
    OutputValidationError,
    PipelineConfigurationError,
    PipelineError,
    StageExecutionError,
)
from .gold import build_gold_layer, build_resilience_methodology_report
from .quality import evaluate_quality_and_sla
from .resilience_methodology import enrich_resilience_with_methodology
from .silver import build_silver_layer

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineConfig:
    project_root: Path
    database_path: Path
    stage_retry_max_attempts: int = 2
    stage_retry_delay_seconds: float = 1.0

    @property
    def raw_dir(self) -> Path:
        return self.project_root / "data" / "raw"

    @property
    def bronze_dir(self) -> Path:
        return self.project_root / "data" / "bronze"

    @property
    def gold_dir(self) -> Path:
        return self.project_root / "data" / "gold"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _error_to_text(exc: Exception | None) -> str | None:
    if exc is None:
        return None
    return f"{type(exc).__name__}: {exc}"


def _log_structured(level: int, event: str, **fields: object) -> None:
    payload = {
        "event": event,
        "timestamp": _utc_now_iso(),
        **fields,
    }
    LOGGER.log(level, json.dumps(payload, ensure_ascii=True, sort_keys=True))


def _ensure_observability_tables(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        create table if not exists pipeline_run_summary (
            run_id varchar,
            trigger varchar,
            attempt integer,
            status varchar,
            started_at varchar,
            finished_at varchar,
            duration_seconds double,
            error_message varchar
        )
        """
    )
    con.execute(
        """
        create table if not exists pipeline_run_events (
            run_id varchar,
            stage_name varchar,
            attempt_count integer,
            status varchar,
            started_at varchar,
            finished_at varchar,
            duration_seconds double,
            error_type varchar,
            error_message varchar,
            details_json varchar
        )
        """
    )
    con.execute("alter table pipeline_run_events add column if not exists attempt_count integer")
    con.execute("alter table pipeline_run_events add column if not exists error_type varchar")
    con.execute("alter table pipeline_run_events add column if not exists details_json varchar")


def _execute_stage_with_retry(
    stage_name: str,
    stage_callable: Callable[[], None],
    max_attempts: int,
    retry_delay_seconds: float,
    run_id: str,
) -> dict[str, object]:
    if max_attempts < 1:
        raise PipelineConfigurationError("stage_retry_max_attempts must be >= 1")
    if retry_delay_seconds < 0:
        raise PipelineConfigurationError("stage_retry_delay_seconds must be >= 0")

    stage_started = _utc_now_iso()
    last_exc: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        attempt_started = _utc_now_iso()
        _log_structured(
            logging.INFO,
            "pipeline_stage_attempt_started",
            run_id=run_id,
            stage_name=stage_name,
            attempt=attempt,
            max_attempts=max_attempts,
        )
        try:
            stage_callable()
            stage_finished = _utc_now_iso()
            _log_structured(
                logging.INFO,
                "pipeline_stage_succeeded",
                run_id=run_id,
                stage_name=stage_name,
                attempt=attempt,
                duration_seconds=(
                    datetime.fromisoformat(stage_finished) - datetime.fromisoformat(attempt_started)
                ).total_seconds(),
            )
            return {
                "run_id": run_id,
                "stage_name": stage_name,
                "attempt_count": attempt,
                "status": "success",
                "started_at": stage_started,
                "finished_at": stage_finished,
                "duration_seconds": (
                    datetime.fromisoformat(stage_finished) - datetime.fromisoformat(stage_started)
                ).total_seconds(),
                "error_type": None,
                "error_message": None,
                "details_json": json.dumps({"max_attempts": max_attempts}, ensure_ascii=True),
            }
        except Exception as exc:
            last_exc = exc
            should_retry = attempt < max_attempts
            _log_structured(
                logging.WARNING,
                "pipeline_stage_attempt_failed",
                run_id=run_id,
                stage_name=stage_name,
                attempt=attempt,
                max_attempts=max_attempts,
                error_type=type(exc).__name__,
                error_message=str(exc),
                will_retry=should_retry,
            )
            if should_retry:
                if retry_delay_seconds > 0:
                    time.sleep(retry_delay_seconds)
                continue
            else:
                break

    if last_exc is None:
        raise PipelineError(f"Stage '{stage_name}' did not complete and produced no exception")
    stage_finished = _utc_now_iso()
    stage_error = StageExecutionError(stage_name=stage_name, attempts=max_attempts, original_error=last_exc)
    return {
        "run_id": run_id,
        "stage_name": stage_name,
        "attempt_count": max_attempts,
        "status": "failed",
        "started_at": stage_started,
        "finished_at": stage_finished,
        "duration_seconds": (
            datetime.fromisoformat(stage_finished) - datetime.fromisoformat(stage_started)
        ).total_seconds(),
        "error_type": type(stage_error).__name__,
        "error_message": str(stage_error),
        "details_json": json.dumps(
            {
                "max_attempts": max_attempts,
                "root_error_type": type(last_exc).__name__,
                "root_error_message": str(last_exc),
            },
            ensure_ascii=True,
        ),
        "raised_error": stage_error,
    }


def run_pipeline(
    config: PipelineConfig,
    run_id: str | None = None,
    trigger: str = "manual",
    attempt: int = 1,
) -> dict[str, object]:
    if config.stage_retry_max_attempts < 1:
        raise PipelineConfigurationError("stage_retry_max_attempts must be >= 1")
    if config.stage_retry_delay_seconds < 0:
        raise PipelineConfigurationError("stage_retry_delay_seconds must be >= 0")

    config.bronze_dir.mkdir(parents=True, exist_ok=True)
    config.gold_dir.mkdir(parents=True, exist_ok=True)
    config.database_path.parent.mkdir(parents=True, exist_ok=True)

    effective_run_id = run_id or f"run_{uuid4().hex[:12]}"
    run_started = _utc_now_iso()
    run_status = "success"
    run_error_message: str | None = None
    stage_events: list[dict[str, object]] = []
    pipeline_exception: Exception | None = None
    observability_exception: Exception | None = None

    con = duckdb.connect(str(config.database_path))
    try:
        _ensure_observability_tables(con)

        bronze_outputs: dict[str, Path] | None = None
        metadata_df: pd.DataFrame | None = None
        gold_df: pd.DataFrame | None = None
        forecasts_df: pd.DataFrame | None = None
        forecast_errors_df: pd.DataFrame | None = None
        resilience_methodology_df: pd.DataFrame | None = None
        quality_df: pd.DataFrame | None = None

        def run_stage(stage_name: str, stage_callable: Callable[[], None]) -> None:
            event = _execute_stage_with_retry(
                stage_name=stage_name,
                stage_callable=stage_callable,
                max_attempts=config.stage_retry_max_attempts,
                retry_delay_seconds=config.stage_retry_delay_seconds,
                run_id=effective_run_id,
            )
            stage_events.append({k: v for k, v in event.items() if k != "raised_error"})
            if "raised_error" in event:
                raised = event["raised_error"]
                if not isinstance(raised, Exception):
                    raise PipelineError("Invalid stage failure payload: raised_error is not an exception")
                raise raised

        def stage_bronze_ingest() -> None:
            nonlocal bronze_outputs
            bronze_outputs = write_bronze_outputs(
                BronzeConfig(raw_dir=config.raw_dir, bronze_dir=config.bronze_dir)
            )

        def stage_bronze_load() -> None:
            if bronze_outputs is None:
                raise OutputValidationError("Bronze ingestion outputs are missing before bronze_load stage")
            con.execute(
                "create or replace table bronze_vocational_enrollment as select * from read_parquet(?)",
                [str(bronze_outputs["vocational_enrollment"])],
            )
            con.execute(
                "create or replace table bronze_hospital_capacity as select * from read_parquet(?)",
                [str(bronze_outputs["hospital_capacity"])],
            )
            con.execute(
                "create or replace table bronze_vocational_graduates as select * from read_parquet(?)",
                [str(bronze_outputs["vocational_graduates"])],
            )
            con.execute(
                "create or replace table bronze_ingestion_metadata as select * from read_parquet(?)",
                [str(bronze_outputs["ingestion_metadata"])],
            )

        def stage_silver() -> None:
            build_silver_layer(con)

        def stage_gold_quality() -> None:
            nonlocal gold_df, forecasts_df, forecast_errors_df, resilience_methodology_df, metadata_df, quality_df
            gold_outputs = build_gold_layer(con, gold_output_dir=config.gold_dir)
            gold_df = gold_outputs["district_resilience"]
            forecasts_df = gold_outputs["forecasts"]
            forecast_errors_df = gold_outputs["forecast_errors"]
            resilience_methodology_df = enrich_resilience_with_methodology(gold_df)
            metadata_df = con.execute("select * from bronze_ingestion_metadata").df()
            quality_df = evaluate_quality_and_sla(con)

        run_stage("bronze_ingestion", stage_bronze_ingest)
        run_stage("bronze_load", stage_bronze_load)
        run_stage("silver_transform", stage_silver)
        run_stage("gold_and_quality", stage_gold_quality)

        if (
            gold_df is None
            or forecasts_df is None
            or forecast_errors_df is None
            or resilience_methodology_df is None
            or metadata_df is None
            or quality_df is None
        ):
            raise OutputValidationError("Pipeline stages completed without producing all required outputs")
        gold_df.to_parquet(config.gold_dir / "dim_district_resilience.parquet", index=False)
        gold_df.to_csv(config.gold_dir / "dim_district_resilience.csv", index=False)
        forecasts_df.to_parquet(config.gold_dir / "fct_vocational_forecasts.parquet", index=False)
        forecasts_df.to_csv(config.gold_dir / "fct_vocational_forecasts.csv", index=False)
        forecast_errors_df.to_parquet(config.gold_dir / "forecast_error_report.parquet", index=False)
        forecast_errors_df.to_csv(config.gold_dir / "forecast_error_report.csv", index=False)
        resilience_methodology_df.to_parquet(config.gold_dir / "resilience_methodology_enriched.parquet", index=False)
        resilience_methodology_df.to_csv(config.gold_dir / "resilience_methodology_enriched.csv", index=False)
        metadata_df.to_parquet(config.bronze_dir / "ingestion_metadata.parquet", index=False)
        metadata_df.to_csv(config.bronze_dir / "ingestion_metadata.csv", index=False)
        quality_df.to_parquet(config.gold_dir / "quality_sla_events.parquet", index=False)
        quality_df.to_csv(config.gold_dir / "quality_sla_events.csv", index=False)

        build_resilience_methodology_report(
            resilience_methodology_df,
            output_path=config.gold_dir / "resilience_methodology_spec.md",
        )

        failing = quality_df[quality_df["status"] == "fail"]
        warning = quality_df[quality_df["status"] == "warn"]
        if not failing.empty or not warning.empty:
            print(
                f"Quality monitor: {len(failing)} fail, {len(warning)} warn. "
                "See data/gold/quality_sla_events.csv"
            )
    except Exception as exc:
        run_status = "failed"
        run_error_message = _error_to_text(exc) or str(exc)
        pipeline_exception = exc
        _log_structured(
            logging.ERROR,
            "pipeline_run_failed",
            run_id=effective_run_id,
            trigger=trigger,
            attempt=attempt,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
    finally:
        run_finished = _utc_now_iso()
        run_summary = pd.DataFrame(
            [
                {
                    "run_id": effective_run_id,
                    "trigger": trigger,
                    "attempt": attempt,
                    "status": run_status,
                    "started_at": run_started,
                    "finished_at": run_finished,
                    "duration_seconds": (
                        datetime.fromisoformat(run_finished) - datetime.fromisoformat(run_started)
                    ).total_seconds(),
                    "error_message": run_error_message,
                }
            ]
        )
        run_events = pd.DataFrame(stage_events)

        try:
            con.register("tmp_run_summary", run_summary)
            con.execute("insert into pipeline_run_summary select * from tmp_run_summary")
            if not run_events.empty:
                con.register("tmp_run_events", run_events)
                con.execute(
                    """
                    insert into pipeline_run_events (
                        run_id,
                        stage_name,
                        attempt_count,
                        status,
                        started_at,
                        finished_at,
                        duration_seconds,
                        error_type,
                        error_message,
                        details_json
                    )
                    select
                        run_id,
                        stage_name,
                        attempt_count,
                        status,
                        started_at,
                        finished_at,
                        duration_seconds,
                        error_type,
                        error_message,
                        details_json
                    from tmp_run_events
                    """
                )

            summary_path = str(config.gold_dir / "pipeline_run_summary.csv").replace("'", "''")
            events_path = str(config.gold_dir / "pipeline_run_events.csv").replace("'", "''")
            con.execute(
                f"""
                copy (
                    select *
                    from pipeline_run_summary
                    order by started_at desc
                ) to '{summary_path}' (format csv, header true)
                """
            )
            con.execute(
                f"""
                copy (
                    select *
                    from pipeline_run_events
                    order by started_at desc
                ) to '{events_path}' (format csv, header true)
                """
            )
        except Exception as exc:
            observability_exception = ObservabilityWriteError(
                f"Failed writing observability artifacts: {type(exc).__name__}: {exc}"
            )
            _log_structured(
                logging.ERROR,
                "pipeline_observability_write_failed",
                run_id=effective_run_id,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
        finally:
            con.close()

    if pipeline_exception is not None:
        raise pipeline_exception
    if observability_exception is not None:
        raise observability_exception

    _log_structured(
        logging.INFO,
        "pipeline_run_succeeded",
        run_id=effective_run_id,
        trigger=trigger,
        attempt=attempt,
    )

    return {
        "run_id": effective_run_id,
        "status": run_status,
        "attempt": attempt,
    }
