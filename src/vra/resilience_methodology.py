from __future__ import annotations

from typing import Any, cast

import numpy as np
import pandas as pd

RESILIENCE_SCORE_FORMULA = "forecasted_graduates / total_beds"

THRESHOLDS = {
    "systemic_risk_upper": 1.0,
    "watch_upper": 2.0,
}

CONFIDENCE_RULES = [
    {"data_quality": "all_data_present", "weight": 1.0},
    {"data_quality": "missing_beds", "weight": 0.5},
    {"data_quality": "missing_graduates", "weight": 0.6},
    {"data_quality": "missing_both", "weight": 0.2},
]

OUTLIER_THRESHOLDS = {
    "percentile_low": 5,
    "percentile_high": 95,
}


def classify_resilience_score(ratio: float | None) -> str:
    if ratio is None:
        return "Missing demand baseline"
    if ratio < THRESHOLDS["systemic_risk_upper"]:
        return "Systemic Risk"
    if ratio < THRESHOLDS["watch_upper"]:
        return "Watch"
    return "Resilient"


def compute_confidence_score(
    has_graduates: bool,
    has_beds: bool,
    forecast_model_name: str | None = None,
) -> float:
    if has_graduates and has_beds:
        confidence = 1.0
    elif has_graduates or has_beds:
        confidence = 0.55
    else:
        confidence = 0.2

    if forecast_model_name == "prophet":
        confidence *= 1.1
    elif forecast_model_name == "naive":
        confidence *= 0.9

    return min(confidence, 1.0)


def compute_sensitivity(
    graduates: float | None,
    beds: float | None,
    bed_change_percent: float = 0.1,
) -> float | None:
    if graduates is None or beds is None or beds == 0:
        return None
    if not np.isfinite(graduates) or not np.isfinite(beds):
        return None
    if not np.isfinite(bed_change_percent):
        return None
    if bed_change_percent < 0 or bed_change_percent >= 1:
        return None

    baseline_ratio = graduates / beds
    if baseline_ratio == 0:
        return None

    adjusted_beds = beds * (1 - bed_change_percent)
    if adjusted_beds <= 0:
        return None

    adjusted_ratio = graduates / adjusted_beds
    percent_change = ((adjusted_ratio - baseline_ratio) / baseline_ratio) * 100
    return float(percent_change)


def detect_outliers(series: pd.Series) -> tuple[float, float]:
    valid = series.dropna()
    if len(valid) < 10:
        return float(valid.min()), float(valid.max())
    p5 = valid.quantile(0.05)
    p95 = valid.quantile(0.95)
    return float(p5), float(p95)


def flag_outlier(value: float | None, p5: float, p95: float, risk_band: str) -> bool:
    if value is None:
        return False
    if value < p5 or value > p95:
        return True
    if risk_band == "Systemic Risk" and value > 0.5:
        return True
    if risk_band == "Resilient" and value < 0.5:
        return True
    return False


def enrich_resilience_with_methodology(resilience_df: pd.DataFrame) -> pd.DataFrame:
    result = resilience_df.copy()

    result["has_graduates"] = result["forecasted_graduates"].notna() & (result["forecasted_graduates"] > 0)
    result["has_beds"] = result["total_beds"].notna() & (result["total_beds"] > 0)

    result["confidence_score"] = result.apply(
        lambda row: compute_confidence_score(
            row["has_graduates"],
            row["has_beds"],
            row.get("selected_model", None),
        ),
        axis=1,
    )

    sensitivity_values: list[float | None] = []
    for row in result.itertuples(index=False):
        sensitivity_values.append(
            compute_sensitivity(
                graduates=cast(float | None, cast(Any, row.forecasted_graduates)),
                beds=cast(float | None, cast(Any, row.total_beds)),
                bed_change_percent=0.1,
            )
        )
    result["sensitivity_impact"] = sensitivity_values

    p5, p95 = detect_outliers(result["resilience_score"])

    result["outlier_flag"] = result.apply(
        lambda row: flag_outlier(row["resilience_score"], p5, p95, row["risk_band"]),
        axis=1,
    )

    result["methodology_notes"] = result.apply(
        lambda row: _build_methodology_note(row),
        axis=1,
    )

    return result[
        [
            "ags",
            "district_name",
            "selected_model",
            "forecasted_graduates",
            "total_beds",
            "resilience_score",
            "confidence_score",
            "sensitivity_impact",
            "risk_band",
            "outlier_flag",
            "methodology_notes",
        ]
    ]


def _build_methodology_note(row: pd.Series) -> str:
    notes = []

    if row["resilience_score"] is None:
        notes.append("No resilience score (missing critical data).")
    else:
        if row["confidence_score"] < 0.5:
            notes.append(f"Low confidence ({row['confidence_score']:.2f}).")
        if row["outlier_flag"]:
            notes.append("Outlier detected in district distribution.")
        if row.get("sensitivity_impact") is not None and abs(row["sensitivity_impact"]) > 15:
            notes.append(f"High sensitivity to bed capacity changes ({row['sensitivity_impact']:.1f}%).")

    if not notes:
        notes.append("Score is within normal range with adequate confidence.")

    return " ".join(notes)
