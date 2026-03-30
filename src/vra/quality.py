from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import duckdb
import pandas as pd


@dataclass(frozen=True)
class FreshnessPolicy:
    logical_name: str
    max_age_days: int


FRESHNESS_POLICIES = (
    FreshnessPolicy("vocational_enrollment", 550),
    FreshnessPolicy("hospital_capacity", 550),
    FreshnessPolicy("vocational_graduates", 550),
)


def classify_age_days(age_days: float, max_age_days: int) -> str:
    if age_days > max_age_days:
        return "fail"
    if age_days > (0.8 * max_age_days):
        return "warn"
    return "pass"


def classify_ratio(metric_value: float, max_ratio: float) -> str:
    if metric_value > max_ratio:
        return "fail"
    if metric_value > (0.8 * max_ratio):
        return "warn"
    return "pass"


def _severity_for_status(status: str) -> str:
    if status == "fail":
        return "critical"
    if status == "warn":
        return "warning"
    return "info"


def evaluate_quality_and_sla(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    checked_at = datetime.now(timezone.utc).replace(microsecond=0)
    rows: list[dict[str, object]] = []

    row_count_targets = (
        "bronze_vocational_enrollment",
        "bronze_hospital_capacity",
        "bronze_vocational_graduates",
    )
    for table_name in row_count_targets:
        row_count = float(con.execute(f"select count(*) from {table_name}").fetchone()[0])
        status = "pass" if row_count > 0 else "fail"
        rows.append(
            {
                "checked_at": checked_at.isoformat(),
                "check_name": "table_row_count_nonzero",
                "logical_name": table_name,
                "severity": _severity_for_status(status),
                "status": status,
                "metric_value": row_count,
                "threshold_value": 1.0,
                "details": "bronze table should not be empty",
            }
        )

    for table_name in (
        "silver_vocational_enrollment",
        "silver_hospital_capacity",
        "silver_vocational_graduates",
    ):
        invalid_ratio = float(
            con.execute(
                f"""
                select
                    case when count(*) = 0 then 0.0
                    else avg(case when ags_quality_flag = 'invalid_ags' then 1.0 else 0.0 end)
                    end as invalid_ratio
                from {table_name}
                """
            ).fetchone()[0]
        )
        status = classify_ratio(invalid_ratio, max_ratio=0.05)
        rows.append(
            {
                "checked_at": checked_at.isoformat(),
                "check_name": "invalid_ags_ratio",
                "logical_name": table_name,
                "severity": _severity_for_status(status),
                "status": status,
                "metric_value": invalid_ratio,
                "threshold_value": 0.05,
                "details": "invalid AGS ratio should stay below 5%",
            }
        )

    metadata = con.execute(
        """
        select
            logical_name,
            max(try_cast(source_last_modified_at as timestamp)) as latest_source_timestamp
        from bronze_ingestion_metadata
        group by 1
        """
    ).df()
    metadata_map = {
        row["logical_name"]: row["latest_source_timestamp"]
        for _, row in metadata.iterrows()
    }

    for policy in FRESHNESS_POLICIES:
        latest = metadata_map.get(policy.logical_name)
        if latest is None or pd.isna(latest):
            status = "fail"
            age_days = float("inf")
            details = "no source timestamp available"
        else:
            latest_utc = latest.to_pydatetime().replace(tzinfo=timezone.utc)
            age_days = max((checked_at - latest_utc).total_seconds() / 86400.0, 0.0)
            status = classify_age_days(age_days, policy.max_age_days)
            details = "source age in days"

        rows.append(
            {
                "checked_at": checked_at.isoformat(),
                "check_name": "source_freshness_days",
                "logical_name": policy.logical_name,
                "severity": _severity_for_status(status),
                "status": status,
                "metric_value": age_days,
                "threshold_value": float(policy.max_age_days),
                "details": details,
            }
        )

    result = pd.DataFrame(rows)
    con.register("tmp_quality_sla_events", result)
    con.execute("create or replace table quality_sla_events as select * from tmp_quality_sla_events")
    return result