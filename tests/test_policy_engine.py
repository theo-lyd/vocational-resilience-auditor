from __future__ import annotations

from vra.policy_engine import (
    check_safety,
    draft_policy_recommendation,
    generate_district_policy_report,
)


def test_check_safety_rejects_unsafe_patterns() -> None:
    is_safe, error = check_safety("Hospital should be closed completely.")
    assert not is_safe
    assert "unsafe" in error.lower()

    is_safe, error = check_safety("This is a safe recommendation.")
    assert is_safe
    assert error is None


def test_check_safety_rejects_long_text() -> None:
    long_text = "A" * 1000
    is_safe, error = check_safety(long_text)
    assert not is_safe
    assert "exceeds" in error.lower()


def test_draft_policy_recommendation_returns_dict() -> None:
    rec = draft_policy_recommendation(
        district_name="Test District",
        risk_band="Systemic Risk",
        resilience_score=0.5,
        confidence_score=0.8,
        outlier_flag=False,
        sensitivity_impact=5.0,
    )

    assert isinstance(rec, dict)
    assert "recommendation" in rec
    assert "confidence" in rec
    assert "caveats" in rec
    assert rec["confidence"] in ["low", "moderate", "high"]


def test_draft_policy_recommendation_maps_human_risk_band_labels() -> None:
    rec = draft_policy_recommendation(
        district_name="Test District",
        risk_band="Systemic Risk",
        resilience_score=0.8,
        confidence_score=0.9,
        outlier_flag=False,
        sensitivity_impact=5.0,
    )

    assert "unable to generate" not in rec["recommendation"].lower()
    assert "for test district" in rec["recommendation"].lower()


def test_draft_policy_recommendation_flags_low_confidence() -> None:
    rec_low = draft_policy_recommendation(
        district_name="Test District",
        risk_band="Watch",
        resilience_score=1.5,
        confidence_score=0.3,
        outlier_flag=False,
        sensitivity_impact=None,
    )

    assert rec_low["confidence"] in ["moderate", "low"]
    assert "low confidence" in rec_low["caveats"].lower() or "data quality" in rec_low["caveats"].lower()


def test_draft_policy_recommendation_flags_outliers() -> None:
    rec = draft_policy_recommendation(
        district_name="Test District",
        risk_band="Resilient",
        resilience_score=2.5,
        confidence_score=1.0,
        outlier_flag=True,
        sensitivity_impact=None,
    )

    assert "outlier" in rec["caveats"].lower() or rec["confidence"] != "high"


def test_generate_district_policy_report_returns_markdown() -> None:
    row = {
        "district_name": "Berlin-Mitte",
        "risk_band": "Systemic Risk",
        "resilience_score": 0.72,
        "confidence_score": 1.0,
        "outlier_flag": False,
        "sensitivity_impact": 10.0,
    }

    report = generate_district_policy_report(row)

    assert "Berlin-Mitte" in report
    assert "Systemic Risk" in report
    assert "Recommendation" in report
    assert "Confidence" in report
    assert "Caveats" in report
    assert isinstance(report, str)
