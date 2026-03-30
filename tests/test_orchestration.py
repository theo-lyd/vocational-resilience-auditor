from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_orchestrator_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "run_orchestrated_pipeline.py"
    spec = importlib.util.spec_from_file_location("run_orchestrated_pipeline", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


orchestrator = _load_orchestrator_module()


def test_parse_args_defaults(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["run_orchestrated_pipeline.py"])
    args = orchestrator.parse_args()
    assert args.max_retries == 2
    assert args.retry_delay_seconds == 20
    assert args.trigger == "manual"


def test_parse_args_custom_values(monkeypatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_orchestrated_pipeline.py",
            "--max-retries",
            "4",
            "--retry-delay-seconds",
            "5",
            "--trigger",
            "ci",
        ],
    )
    args = orchestrator.parse_args()
    assert args.max_retries == 4
    assert args.retry_delay_seconds == 5
    assert args.trigger == "ci"


def test_main_success_first_attempt(monkeypatch) -> None:
    monkeypatch.setattr(orchestrator, "parse_args", lambda: type("A", (), {"max_retries": 1, "retry_delay_seconds": 0, "trigger": "manual"})())

    calls = []

    def fake_run_pipeline(config, trigger, attempt):
        calls.append((trigger, attempt))
        return {"run_id": "run_test", "status": "success", "attempt": attempt}

    monkeypatch.setattr(orchestrator, "run_pipeline", fake_run_pipeline)
    orchestrator.main()

    assert calls == [("manual", 1)]