from __future__ import annotations

from pathlib import Path

import pytest

from vra.errors import PipelineConfigurationError, StageExecutionError
from vra.pipeline import PipelineConfig, _execute_stage_with_retry, run_pipeline


def test_execute_stage_with_retry_succeeds_on_second_attempt() -> None:
    calls = {"count": 0}

    def flaky_stage() -> None:
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("transient")

    event = _execute_stage_with_retry(
        stage_name="flaky_stage",
        stage_callable=flaky_stage,
        max_attempts=2,
        retry_delay_seconds=0,
        run_id="run_test",
    )

    assert event["status"] == "success"
    assert event["attempt_count"] == 2
    assert calls["count"] == 2


def test_execute_stage_with_retry_returns_typed_failure_event() -> None:
    def always_fail() -> None:
        raise ValueError("boom")

    event = _execute_stage_with_retry(
        stage_name="always_fail_stage",
        stage_callable=always_fail,
        max_attempts=2,
        retry_delay_seconds=0,
        run_id="run_test",
    )

    assert event["status"] == "failed"
    assert event["attempt_count"] == 2
    assert isinstance(event["raised_error"], StageExecutionError)


def test_run_pipeline_rejects_invalid_stage_retry_config(tmp_path: Path) -> None:
    config = PipelineConfig(
        project_root=tmp_path,
        database_path=tmp_path / "warehouse" / "vra.duckdb",
        stage_retry_max_attempts=0,
    )

    with pytest.raises(PipelineConfigurationError):
        run_pipeline(config)
