from __future__ import annotations

import duckdb
import pandas as pd

from vra.gold import FORECAST_HORIZON_YEARS, _backtest_models, _build_forecast_records, build_gold_layer


def test_build_forecast_records_contains_baselines() -> None:
    history = pd.DataFrame(
        {
            "ags": ["01001", "01001", "01001", "01002", "01002", "01002"],
            "year": [2020, 2021, 2022, 2020, 2021, 2022],
            "graduates_total": [100.0, 120.0, 140.0, 200.0, 190.0, 210.0],
        }
    )

    forecasts = _build_forecast_records(history, years_ahead=3)

    assert not forecasts.empty
    assert {"ags", "model_name", "forecast_year", "horizon_years", "forecasted_graduates"}.issubset(
        set(forecasts.columns)
    )
    assert {"linear", "naive"}.issubset(set(forecasts["model_name"].unique()))



def test_backtest_models_returns_abs_error() -> None:
    history = pd.DataFrame(
        {
            "ags": ["01001", "01001", "01001", "01001"],
            "year": [2020, 2021, 2022, 2023],
            "graduates_total": [100.0, 110.0, 120.0, 130.0],
        }
    )

    backtest = _backtest_models(history)

    assert not backtest.empty
    assert {"ags", "model_name", "backtest_year", "actual_graduates", "predicted_graduates", "abs_error"}.issubset(
        set(backtest.columns)
    )
    assert (backtest["abs_error"] >= 0).all()



def test_build_gold_layer_creates_forecast_tables(tmp_path) -> None:
    con = duckdb.connect(database=":memory:")

    grads = pd.DataFrame(
        {
            "ags": ["01001", "01001", "01001", "01002", "01002", "01002"],
            "year": [2020, 2021, 2022, 2020, 2021, 2022],
            "graduates_total": [100.0, 120.0, 140.0, 220.0, 210.0, 200.0],
        }
    )
    hospitals = pd.DataFrame(
        {
            "ags": ["01001", "01002"],
            "district_name": ["District A", "District B"],
            "year": [2022, 2022],
            "total_beds": [100.0, 150.0],
        }
    )

    con.register("tmp_grads", grads)
    con.register("tmp_hospitals", hospitals)
    con.execute("create table silver_vocational_graduates_total as select * from tmp_grads")
    con.execute("create table silver_hospital_capacity as select * from tmp_hospitals")

    outputs = build_gold_layer(con, gold_output_dir=tmp_path)

    assert not outputs["district_resilience"].empty
    assert not outputs["forecasts"].empty
    assert "selected_model" in outputs["district_resilience"].columns

    persisted_forecasts = con.execute("select count(*) from fct_vocational_forecasts").fetchone()[0]
    assert persisted_forecasts > 0

    persisted_errors = con.execute("select count(*) from fct_vocational_forecast_errors").fetchone()[0]
    assert persisted_errors >= 0

    forecast_horizon = outputs["district_resilience"]["forecast_year"] - outputs["district_resilience"]["history_last_year"]
    assert (forecast_horizon == FORECAST_HORIZON_YEARS).all()

    model_card = tmp_path / "forecast_model_card.md"
    assert model_card.exists()
