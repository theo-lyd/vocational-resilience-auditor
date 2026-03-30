from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb

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


def run_pipeline(config: PipelineConfig) -> None:
    config.bronze_dir.mkdir(parents=True, exist_ok=True)
    config.gold_dir.mkdir(parents=True, exist_ok=True)
    config.database_path.parent.mkdir(parents=True, exist_ok=True)

    bronze_outputs = write_bronze_outputs(
        BronzeConfig(raw_dir=config.raw_dir, bronze_dir=config.bronze_dir)
    )

    con = duckdb.connect(str(config.database_path))
    try:
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

        build_silver_layer(con)
        gold_df = build_gold_layer(con)
        metadata_df = con.execute("select * from bronze_ingestion_metadata").df()
        quality_df = evaluate_quality_and_sla(con)

        gold_df.to_parquet(config.gold_dir / "dim_district_resilience.parquet", index=False)
        gold_df.to_csv(config.gold_dir / "dim_district_resilience.csv", index=False)
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
    finally:
        con.close()
