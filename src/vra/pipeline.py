from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4

import duckdb
import pandas as pd

from .bronze import BronzeConfig, write_bronze_outputs
from .gold import build_gold_layer
from .quality import evaluate_quality_and_sla
from .silver import build_silver_layer


@dataclass(frozen=True)
class PipelineConfig:
    project_root: Path
    database_path: Path

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
            status varchar,
            started_at varchar,
            finished_at varchar,
            duration_seconds double,
            error_message varchar
        )
        """
    )


def run_pipeline(
    config: PipelineConfig,
    run_id: str | None = None,
    trigger: str = "manual",
    attempt: int = 1,
) -> dict[str, object]:
    config.bronze_dir.mkdir(parents=True, exist_ok=True)
    config.gold_dir.mkdir(parents=True, exist_ok=True)
    config.database_path.parent.mkdir(parents=True, exist_ok=True)

    effective_run_id = run_id or f"run_{uuid4().hex[:12]}"
    run_started = _utc_now_iso()
    run_status = "success"
    run_error_message: str | None = None
    stage_events: list[dict[str, object]] = []

    con = duckdb.connect(str(config.database_path))
    try:
        _ensure_observability_tables(con)

        bronze_outputs: dict[str, Path] | None = None
        metadata_df: pd.DataFrame | None = None
        gold_df: pd.DataFrame | None = None
        forecasts_df: pd.DataFrame | None = None
        forecast_errors_df: pd.DataFrame | None = None
        quality_df: pd.DataFrame | None = None

        def run_stage(stage_name: str, stage_callable: Callable[[], None]) -> None:
            stage_started = _utc_now_iso()
            stage_status = "success"
            stage_error: str | None = None
            try:
                stage_callable()
            except Exception as exc:
                stage_status = "failed"
                stage_error = str(exc)
                raise
            finally:
                stage_finished = _utc_now_iso()
                stage_events.append(
                    {
                        "run_id": effective_run_id,
                        "stage_name": stage_name,
                        "status": stage_status,
                        "started_at": stage_started,
                        "finished_at": stage_finished,
                        "duration_seconds": (
                            datetime.fromisoformat(stage_finished) - datetime.fromisoformat(stage_started)
                        ).total_seconds(),
                        "error_message": stage_error,
                    }
                )

        def stage_bronze_ingest() -> None:
            nonlocal bronze_outputs
            bronze_outputs = write_bronze_outputs(
                BronzeConfig(raw_dir=config.raw_dir, bronze_dir=config.bronze_dir)
            )

        def stage_bronze_load() -> None:
            assert bronze_outputs is not None
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
            nonlocal gold_df, forecasts_df, forecast_errors_df, metadata_df, quality_df
            gold_outputs = build_gold_layer(con, gold_output_dir=config.gold_dir)
            gold_df = gold_outputs["district_resilience"]
            forecasts_df = gold_outputs["forecasts"]
            forecast_errors_df = gold_outputs["forecast_errors"]
            metadata_df = con.execute("select * from bronze_ingestion_metadata").df()
            quality_df = evaluate_quality_and_sla(con)

        run_stage("bronze_ingestion", stage_bronze_ingest)
        run_stage("bronze_load", stage_bronze_load)
        run_stage("silver_transform", stage_silver)
        run_stage("gold_and_quality", stage_gold_quality)

        assert gold_df is not None
        assert forecasts_df is not None
        assert forecast_errors_df is not None
        assert metadata_df is not None
        assert quality_df is not None
        gold_df.to_parquet(config.gold_dir / "dim_district_resilience.parquet", index=False)
        gold_df.to_csv(config.gold_dir / "dim_district_resilience.csv", index=False)
        forecasts_df.to_parquet(config.gold_dir / "fct_vocational_forecasts.parquet", index=False)
        forecasts_df.to_csv(config.gold_dir / "fct_vocational_forecasts.csv", index=False)
        forecast_errors_df.to_parquet(config.gold_dir / "forecast_error_report.parquet", index=False)
        forecast_errors_df.to_csv(config.gold_dir / "forecast_error_report.csv", index=False)
        metadata_df.to_parquet(config.bronze_dir / "ingestion_metadata.parquet", index=False)
        metadata_df.to_csv(config.bronze_dir / "ingestion_metadata.csv", index=False)
        quality_df.to_parquet(config.gold_dir / "quality_sla_events.parquet", index=False)
        quality_df.to_csv(config.gold_dir / "quality_sla_events.csv", index=False)

        failing = quality_df[quality_df["status"] == "fail"]
        warning = quality_df[quality_df["status"] == "warn"]
        if not failing.empty or not warning.empty:
            print(
                f"Quality monitor: {len(failing)} fail, {len(warning)} warn. "
                "See data/gold/quality_sla_events.csv"
            )
    except Exception as exc:
        run_status = "failed"
        run_error_message = str(exc)
        raise
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

        con.register("tmp_run_summary", run_summary)
        con.execute("insert into pipeline_run_summary select * from tmp_run_summary")
        if not run_events.empty:
            con.register("tmp_run_events", run_events)
            con.execute("insert into pipeline_run_events select * from tmp_run_events")

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
        con.close()

    return {
        "run_id": effective_run_id,
        "status": run_status,
        "attempt": attempt,
    }
