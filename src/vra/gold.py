from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


try:
    from prophet import Prophet

    PROPHET_AVAILABLE = True
except Exception:
    Prophet = None
    PROPHET_AVAILABLE = False


FORECAST_HORIZON_YEARS = 5


def _predict_linear(train: pd.DataFrame, target_year: int) -> float | None:
    x = train["year"].to_numpy(dtype=float)
    y = train["graduates_total"].to_numpy(dtype=float)
    if len(train) >= 3 and np.unique(x).size >= 3:
        slope, intercept = np.polyfit(x, y, deg=1)
        return float(intercept + slope * target_year)
    if len(train) >= 1:
        return float(y[-1])
    return None


def _predict_naive(train: pd.DataFrame) -> float | None:
    if train.empty:
        return None
    return float(train.iloc[-1]["graduates_total"])


def _predict_prophet(train: pd.DataFrame, target_year: int) -> float | None:
    if not PROPHET_AVAILABLE or Prophet is None:
        return None
    if len(train) < 4:
        return None

    ds = pd.to_datetime(train["year"].astype(int).astype(str) + "-01-01")
    model_df = pd.DataFrame({"ds": ds, "y": train["graduates_total"].astype(float)})

    model = Prophet(yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)
    model.fit(model_df)

    target = pd.DataFrame({"ds": [pd.Timestamp(year=target_year, month=1, day=1)]})
    forecast = model.predict(target)
    return float(forecast.iloc[0]["yhat"])


def _build_forecast_records(history: pd.DataFrame, years_ahead: int = FORECAST_HORIZON_YEARS) -> pd.DataFrame:
    records: list[dict[str, float | int | str]] = []

    for ags, group in history.groupby("ags"):
        g = group.dropna(subset=["year", "graduates_total"]).sort_values("year")
        if g.empty:
            continue

        last_year = int(g["year"].max())
        for horizon in range(1, years_ahead + 1):
            target_year = last_year + horizon

            linear_pred = _predict_linear(g, target_year)
            naive_pred = _predict_naive(g)
            prophet_pred = _predict_prophet(g, target_year)

            candidates = {
                "linear": linear_pred,
                "naive": naive_pred,
                "prophet": prophet_pred,
            }
            for model_name, prediction in candidates.items():
                if prediction is None:
                    continue
                records.append(
                    {
                        "ags": ags,
                        "model_name": model_name,
                        "history_last_year": last_year,
                        "forecast_year": target_year,
                        "horizon_years": horizon,
                        "forecasted_graduates": max(float(prediction), 0.0),
                    }
                )

    return pd.DataFrame(
        records,
        columns=[
            "ags",
            "model_name",
            "history_last_year",
            "forecast_year",
            "horizon_years",
            "forecasted_graduates",
        ],
    )


def _backtest_models(history: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, float | int | str]] = []

    for ags, group in history.groupby("ags"):
        g = group.dropna(subset=["year", "graduates_total"]).sort_values("year")
        if len(g) < 3:
            continue

        train = g.iloc[:-1]
        holdout = g.iloc[-1]
        actual_year = int(holdout["year"])
        actual_value = float(holdout["graduates_total"])

        model_predictions = {
            "linear": _predict_linear(train, actual_year),
            "naive": _predict_naive(train),
            "prophet": _predict_prophet(train, actual_year),
        }

        for model_name, prediction in model_predictions.items():
            if prediction is None:
                continue
            records.append(
                {
                    "ags": ags,
                    "model_name": model_name,
                    "backtest_year": actual_year,
                    "actual_graduates": actual_value,
                    "predicted_graduates": float(prediction),
                    "abs_error": abs(float(prediction) - actual_value),
                }
            )

    return pd.DataFrame(
        records,
        columns=[
            "ags",
            "model_name",
            "backtest_year",
            "actual_graduates",
            "predicted_graduates",
            "abs_error",
        ],
    )


def _build_model_card(
    forecasts: pd.DataFrame,
    backtest: pd.DataFrame,
    model_metrics: pd.DataFrame,
    output_path: Path,
) -> None:
    available_models = sorted(forecasts["model_name"].unique().tolist()) if not forecasts.empty else []
    backtest_rows = len(backtest)

    if model_metrics.empty:
        metrics_block = "No backtest metrics available (insufficient history)."
    else:
        metrics_lines = []
        for row in model_metrics.sort_values(["model_name"])[["model_name", "districts_evaluated", "mae"]].itertuples(index=False):
            metrics_lines.append(
                f"- {row.model_name}: districts={int(row.districts_evaluated)}, MAE={float(row.mae):.2f}"
            )
        metrics_block = "\n".join(metrics_lines)

    text = (
        "# Forecast Model Card\n\n"
        "## Scope\n"
        f"- Forecast horizon: {FORECAST_HORIZON_YEARS} years ahead\n"
        "- Target variable: district-level vocational graduates\n"
        f"- Available models in this run: {', '.join(available_models) if available_models else 'none'}\n\n"
        "## Assumptions\n"
        "- Historical graduates are a usable proxy for medium-term workforce supply.\n"
        "- District trends are approximately stable over the short to medium term.\n"
        "- Hospital bed capacity remains a valid demand baseline for resilience scoring.\n\n"
        "## Strengths\n"
        "- Includes benchmark baselines (naive and linear) for transparency.\n"
        "- Supports Prophet when installed for non-linear trend capture.\n"
        "- Uses district-level backtesting to pick a best-performing model.\n\n"
        "## Limits\n"
        "- Limited history can reduce forecast reliability.\n"
        "- No external regressors are used (policy shocks are not modeled).\n"
        "- Prophet execution depends on environment availability.\n\n"
        "## Backtest Summary\n"
        f"- Backtest rows: {backtest_rows}\n"
        f"{metrics_block}\n"
    )

    output_path.write_text(text, encoding="utf-8")


def build_gold_layer(con: duckdb.DuckDBPyConnection, gold_output_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    history = con.execute(
        """
        select ags, year, graduates_total
        from silver_vocational_graduates_total
        order by ags, year
        """
    ).df()

    forecast_df = _build_forecast_records(history, years_ahead=FORECAST_HORIZON_YEARS)
    backtest_df = _backtest_models(history)

    if forecast_df.empty:
        con.execute(
            "create or replace table fct_vocational_forecasts as "
            "select * from (select null::varchar as ags) where false"
        )
        con.execute(
            "create or replace table fct_vocational_forecast_errors as "
            "select * from (select null::varchar as ags) where false"
        )
        con.execute("create or replace table gold_district_resilience as select * from (select null::varchar as ags) where false")
        return {
            "district_resilience": pd.DataFrame(),
            "forecasts": pd.DataFrame(),
            "forecast_errors": pd.DataFrame(),
            "model_metrics": pd.DataFrame(),
        }

    if backtest_df.empty:
        model_metrics = pd.DataFrame(columns=["model_name", "districts_evaluated", "mae"])
        district_model_scores = pd.DataFrame(columns=["ags", "model_name", "mae"])
    else:
        district_model_scores = (
            backtest_df.groupby(["ags", "model_name"], as_index=False)
            .agg(mae=("abs_error", "mean"))
        )
        model_metrics = (
            district_model_scores.groupby("model_name", as_index=False)
            .agg(
                districts_evaluated=("ags", "count"),
                mae=("mae", "mean"),
            )
        )

    if district_model_scores.empty:
        fallback_linear = forecast_df[forecast_df["model_name"] == "linear"][["ags"]].drop_duplicates()
        best_models = fallback_linear.assign(model_name="linear")
    else:
        score_order = district_model_scores.assign(
            model_priority=district_model_scores["model_name"].map({"linear": 1, "prophet": 2, "naive": 3}).fillna(9)
        ).sort_values(["ags", "mae", "model_priority"])
        best_models = score_order.drop_duplicates(subset=["ags"], keep="first")[["ags", "model_name"]]

    selected_forecasts = forecast_df.merge(best_models, on=["ags", "model_name"], how="inner")
    selected_horizon = selected_forecasts[selected_forecasts["horizon_years"] == FORECAST_HORIZON_YEARS].copy()

    con.register("tmp_forecasts", forecast_df)
    con.execute("create or replace table fct_vocational_forecasts as select * from tmp_forecasts")
    con.register("tmp_forecast_errors", backtest_df)
    con.execute("create or replace table fct_vocational_forecast_errors as select * from tmp_forecast_errors")

    con.register("tmp_selected_forecast", selected_horizon)

    result = con.execute(
        """
        with latest_hospital as (
            select *
            from (
                select
                    ags,
                    district_name,
                    year,
                    total_beds,
                    row_number() over (partition by ags order by year desc) as rn
                from silver_hospital_capacity
            ) ranked
            where rn = 1
        )
        select
            f.ags,
            h.district_name,
            f.model_name as selected_model,
            f.history_last_year,
            f.forecast_year,
            f.forecasted_graduates,
            h.year as hospital_year,
            h.total_beds,
            case
                when h.total_beds is null or h.total_beds = 0 then null
                else f.forecasted_graduates / h.total_beds
            end as resilience_score,
            case
                when h.total_beds is null or h.total_beds = 0 then 'Missing demand baseline'
                when (f.forecasted_graduates / h.total_beds) < 1.0 then 'Systemic Risk'
                when (f.forecasted_graduates / h.total_beds) < 2.0 then 'Watch'
                else 'Resilient'
            end as risk_band
        from tmp_selected_forecast f
        left join latest_hospital h using (ags)
        """
    ).df()

    con.register("tmp_gold", result)
    con.execute("create or replace table gold_district_resilience as select * from tmp_gold")

    if gold_output_dir is not None:
        gold_output_dir.mkdir(parents=True, exist_ok=True)
        _build_model_card(
            forecasts=forecast_df,
            backtest=backtest_df,
            model_metrics=model_metrics,
            output_path=gold_output_dir / "forecast_model_card.md",
        )

    return {
        "district_resilience": result,
        "forecasts": forecast_df,
        "forecast_errors": backtest_df,
        "model_metrics": model_metrics,
    }
