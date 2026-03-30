"""Policy recommendation engine with safety guardrails."""

REJECT_PATTERNS = (
    "should be closed",
    "eliminate",
    "remove all",
    "cut funding entirely",
)
MAX_RECOMMENDATION_LENGTH_CHARS = 500

POLICY_TEMPLATES = {
    "systemic_risk": (
        "Districts with Systemic Risk (score < 1.0) have more vocational graduates than hospital beds. "
        "Consider: (1) expanding vocational training capacity through partnerships, "
        "(2) reviewing hospital staffing efficiency, or (3) analyzing labor market data for placement rates."
    ),
    "watch": (
        "Districts in Watch (score 1.0–2.0) have moderate supply-demand balance. "
        "Monitor: (1) forecast trends, (2) hospital capacity changes, and (3) enrollment trends quarterly."
    ),
    "resilient": (
        "Districts with Resilient status (score ≥ 2.0) have strong supply relative to demand. "
        "Opportunities: (1) benchmark practices for supply-demand alignment, (2) explore workforce migration patterns, "
        "or (3) consider inter-regional collaboration models."
    ),
    "missing_data": (
        "Districts with missing data cannot be scored. Recommend: (1) requesting hospital capacity data from regional authorities, "
        "(2) validating vocational graduate records, or (3) working with health authorities on data sharing agreements."
    ),
}


RISK_BAND_TEMPLATE_MAP = {
    "systemic risk": "systemic_risk",
    "systemic_risk": "systemic_risk",
    "watch": "watch",
    "resilient": "resilient",
    "missing demand baseline": "missing_data",
    "missing data": "missing_data",
    "missing_data": "missing_data",
}


def check_safety(recommendation: str) -> tuple[bool, str | None]:
    """Validate recommendation against guardrails.
    
    Returns:
        (is_safe, error_message)
    """
    if len(recommendation) > MAX_RECOMMENDATION_LENGTH_CHARS:
        return False, f"Recommendation exceeds {MAX_RECOMMENDATION_LENGTH_CHARS} characters."

    for pattern in REJECT_PATTERNS:
        if pattern.lower() in recommendation.lower():
            return False, f"Recommendation contains unsafe language: '{pattern}'."

    return True, None


def _resolve_template_key(risk_band: str) -> str | None:
    if not risk_band:
        return None
    return RISK_BAND_TEMPLATE_MAP.get(risk_band.strip().lower())


def draft_policy_recommendation(
    district_name: str,
    risk_band: str,
    resilience_score: float | None,
    confidence_score: float | None,
    outlier_flag: bool,
    sensitivity_impact: float | None,
) -> dict[str, str]:
    """Draft evidence-based policy recommendation for a district.
    
    Returns dict with 'recommendation', 'confidence', 'caveats'.
    """
    template_key = _resolve_template_key(risk_band)
    if template_key is None:
        return {
            "recommendation": "Unable to generate recommendation: unknown risk band.",
            "confidence": "low",
            "caveats": "Check data quality.",
        }

    base_rec = f"For {district_name}: {POLICY_TEMPLATES[template_key]}"

    caveats = []
    if confidence_score is not None and confidence_score < 0.6:
        caveats.append("Low confidence in score due to incomplete data.")
    if outlier_flag:
        caveats.append("District is flagged as an outlier in its cohort.")
    if sensitivity_impact is not None and abs(sensitivity_impact) > 15:
        caveats.append(
            f"Score is sensitive to hospital bed assumptions ({sensitivity_impact:.1f}% swing)."
        )

    confidence = "high"
    if caveats:
        confidence = "moderate" if len(caveats) == 1 else "low"

    is_safe, error = check_safety(base_rec)
    if not is_safe:
        base_rec = f"Unable to generate recommendation: {error}"
        confidence = "low"

    return {
        "recommendation": base_rec,
        "confidence": confidence,
        "caveats": " ".join(caveats) if caveats else "None identified.",
    }


def generate_district_policy_report(
    row: dict,
) -> str:
    """Generate a markdown-formatted policy report for display."""
    rec = draft_policy_recommendation(
        district_name=row.get("district_name", "Unknown"),
        risk_band=row.get("risk_band", "Unknown"),
        resilience_score=row.get("resilience_score"),
        confidence_score=row.get("confidence_score"),
        outlier_flag=row.get("outlier_flag", False),
        sensitivity_impact=row.get("sensitivity_impact"),
    )

    markdown = (
        f"### {row.get('district_name', 'Unknown District')}\n\n"
        f"**Risk Band:** `{row.get('risk_band', 'N/A')}`\n\n"
        f"**Resilience Score:** {row.get('resilience_score', 'N/A')}\n\n"
        f"**Recommendation:**\n\n{rec['recommendation']}\n\n"
        f"**Confidence:** {rec['confidence']}\n\n"
        f"**Important Caveats:**\n\n{rec['caveats']}\n\n"
    )
    return markdown
