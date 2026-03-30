from __future__ import annotations

import pandas as pd

from vra.resilience_methodology import (
    classify_resilience_score,
    compute_confidence_score,
    compute_sensitivity,
    detect_outliers,
    enrich_resilience_with_methodology,
    flag_outlier,
)


def test_classify_resilience_score_returns_risk_bands() -> None:
    assert classify_resilience_score(0.8) == "Systemic Risk"
    assert classify_resilience_score(1.0) == "Watch"
    assert classify_resilience_score(1.5) == "Watch"
    assert classify_resilience_score(2.0) == "Resilient"
    assert classify_resilience_score(3.0) == "Resilient"
    assert classify_resilience_score(None) == "Missing demand baseline"


def test_compute_confidence_score_reflects_data_completeness() -> None:
    full_linear = compute_confidence_score(has_graduates=True, has_beds=True, forecast_model_name="linear")
    assert full_linear == 1.0

    full_naive = compute_confidence_score(has_graduates=True, has_beds=True, forecast_model_name="naive")
    assert full_naive == 0.9

    partial = compute_confidence_score(has_graduates=True, has_beds=False)
    assert partial < full_linear
    assert partial > 0.5

    minimal = compute_confidence_score(has_graduates=False, has_beds=False)
    assert minimal < 0.3


def test_compute_sensitivity_reflects_bed_changes() -> None:
    sensitivity = compute_sensitivity(graduates=100.0, beds=50.0, bed_change_percent=0.1)
    assert sensitivity is not None
    assert sensitivity > 10.0

    no_beds = compute_sensitivity(graduates=100.0, beds=None, bed_change_percent=0.1)
    assert no_beds is None

    invalid_percent = compute_sensitivity(graduates=100.0, beds=50.0, bed_change_percent=1.0)
    assert invalid_percent is None

    negative_percent = compute_sensitivity(graduates=100.0, beds=50.0, bed_change_percent=-0.2)
    assert negative_percent is None

    non_finite = compute_sensitivity(graduates=float("nan"), beds=50.0, bed_change_percent=0.1)
    assert non_finite is None


def test_detect_outliers_returns_percentiles() -> None:
    series = pd.Series([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0] * 2)
    p5, p95 = detect_outliers(series)
    assert p5 >= 0.5
    assert p95 <= 5.0
    assert p5 < p95


def test_flag_outlier_detects_extreme_values() -> None:
    assert flag_outlier(0.3, p5=1.0, p95=4.0, risk_band="Resilient") is True
    assert flag_outlier(2.0, p5=1.0, p95=4.0, risk_band="Watch") is False
    assert flag_outlier(None, p5=1.0, p95=4.0, risk_band="Watch") is False


def test_enrich_resilience_with_methodology_adds_columns() -> None:
    df = pd.DataFrame(
        {
            "ags": ["01001", "01002"],
            "district_name": ["District A", "District B"],
            "forecasted_graduates": [100.0, 200.0],
            "total_beds": [50.0, 100.0],
            "resilience_score": [2.0, 2.0],
            "risk_band": ["Resilient", "Resilient"],
            "selected_model": ["linear", "linear"],
        }
    )

    enriched = enrich_resilience_with_methodology(df)

    assert "confidence_score" in enriched.columns
    assert "sensitivity_impact" in enriched.columns
    assert "outlier_flag" in enriched.columns
    assert "methodology_notes" in enriched.columns
    assert len(enriched) == 2
    assert (enriched["confidence_score"] >= 0.0).all() and (enriched["confidence_score"] <= 1.0).all()
