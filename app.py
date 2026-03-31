from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.vra.policy_engine import generate_district_policy_report

st.set_page_config(page_title="Vocational Resilience Auditor", layout="wide")
st.title("🏥 Vocational Resilience Auditor")
st.caption(
    "Decision-support dashboard for district-level vocational-healthcare resilience. "
    "Includes risk diagnostics, model quality signals, and policy-ready interpretation."
)

output_file = Path("data/gold/dim_district_resilience.csv")
methodology_file = Path("data/gold/resilience_methodology_enriched.csv")
forecast_error_file = Path("data/gold/forecast_error_report.csv")
quality_file = Path("data/gold/quality_sla_events.csv")
pipeline_summary_file = Path("data/gold/pipeline_run_summary.csv")

if not output_file.exists():
    st.warning("No gold output found. Run: python scripts/run_pipeline.py")
    st.stop()

df = pd.read_csv(output_file)
if df.empty:
    st.warning("Gold dataset is empty.")
    st.stop()

if methodology_file.exists():
    methodology_df = pd.read_csv(methodology_file)
    keep_cols = [
        "ags",
        "confidence_score",
        "sensitivity_impact",
        "outlier_flag",
        "methodology_notes",
    ]
    df = df.merge(methodology_df[keep_cols], on="ags", how="left")

if "total_beds" in df.columns and "forecasted_graduates" in df.columns:
    valid_demand = df["total_beds"].where(df["total_beds"] > 0)
    df["coverage_ratio"] = df["forecasted_graduates"] / valid_demand
    df["demand_gap"] = df["total_beds"] - df["forecasted_graduates"]

risk_order = ["Systemic Risk", "Watch", "Resilient", "Missing demand baseline"]

forecast_errors_df = pd.read_csv(forecast_error_file) if forecast_error_file.exists() else pd.DataFrame()
quality_df = pd.read_csv(quality_file) if quality_file.exists() else pd.DataFrame()
pipeline_summary_df = (
    pd.read_csv(pipeline_summary_file) if pipeline_summary_file.exists() else pd.DataFrame()
)


def _fmt_pct(value: float) -> str:
    return f"{value:.1%}"


def _build_top_findings(
    resilience_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    quality_events_df: pd.DataFrame,
) -> list[str]:
    findings: list[str] = []

    total = int(resilience_df["ags"].nunique())
    if total > 0:
        systemic = int((resilience_df["risk_band"] == "Systemic Risk").sum())
        watch = int((resilience_df["risk_band"] == "Watch").sum())
        exposed_share = (systemic + watch) / total
        findings.append(
            f"{_fmt_pct(exposed_share)} of districts are in Systemic Risk or Watch "
            f"({systemic + watch}/{total})."
        )

    if "resilience_score" in resilience_df.columns:
        below_one = int((resilience_df["resilience_score"] < 1.0).sum())
        findings.append(
            f"{below_one} districts are below resilience score 1.0, indicating projected supply shortfall."
        )

    if "demand_gap" in resilience_df.columns and "district_name" in resilience_df.columns:
        gap_df = resilience_df.dropna(subset=["demand_gap"])
        if not gap_df.empty:
            worst = gap_df.sort_values("demand_gap", ascending=False).iloc[0]
            findings.append(
                f"Largest demand gap is in {worst['district_name']} ({worst['ags']}): "
                f"{float(worst['demand_gap']):.0f} beds above projected graduates."
            )

    if "outlier_flag" in resilience_df.columns:
        outlier_share = float(resilience_df["outlier_flag"].fillna(False).astype(bool).mean())
        findings.append(
            f"Outlier share is {_fmt_pct(outlier_share)}; prioritize caution where local behavior is atypical."
        )

    if not forecast_df.empty and "abs_error" in forecast_df.columns:
        model_mae = (
            forecast_df.groupby("model_name", as_index=False)
            .agg(mae=("abs_error", "mean"))
            .sort_values("mae")
        )
        if not model_mae.empty:
            best = model_mae.iloc[0]
            findings.append(
                f"Best backtested model is {best['model_name']} with MAE {float(best['mae']):.2f}."
            )

    if not quality_events_df.empty and "status" in quality_events_df.columns:
        fail_count = int((quality_events_df["status"] == "fail").sum())
        findings.append(f"Current quality/SLA failed checks: {fail_count}.")

    return findings[:5]


def _build_change_notes(
    pipeline_df: pd.DataFrame,
    quality_events_df: pd.DataFrame,
) -> list[str]:
    notes: list[str] = []

    if not pipeline_df.empty and "started_at" in pipeline_df.columns:
        recent = pipeline_df.sort_values("started_at", ascending=False).head(2)
        if len(recent) >= 2:
            latest = recent.iloc[0]
            previous = recent.iloc[1]
            notes.append(
                f"Run status changed from {previous['status']} to {latest['status']} "
                f"(run {latest['run_id']})."
            )
            latest_dur = float(latest.get("duration_seconds", 0.0) or 0.0)
            prev_dur = float(previous.get("duration_seconds", 0.0) or 0.0)
            delta = latest_dur - prev_dur
            direction = "faster" if delta < 0 else "slower"
            notes.append(
                f"Latest pipeline is {abs(delta):.1f}s {direction} than previous run "
                f"({latest_dur:.1f}s vs {prev_dur:.1f}s)."
            )
        else:
            notes.append("Only one pipeline run available; run-over-run comparison not yet available.")

    if not quality_events_df.empty and "checked_at" in quality_events_df.columns:
        quality_recent = quality_events_df.sort_values("checked_at", ascending=False)
        if "status" in quality_recent.columns:
            checkpoints = quality_recent["checked_at"].dropna().unique().tolist()
            if len(checkpoints) >= 2:
                latest_ts, previous_ts = checkpoints[0], checkpoints[1]
                latest_fail = int(
                    (
                        (quality_recent["checked_at"] == latest_ts)
                        & (quality_recent["status"] == "fail")
                    ).sum()
                )
                prev_fail = int(
                    (
                        (quality_recent["checked_at"] == previous_ts)
                        & (quality_recent["status"] == "fail")
                    ).sum()
                )
                diff = latest_fail - prev_fail
                if diff == 0:
                    notes.append("Quality failure count is unchanged since the previous check window.")
                elif diff < 0:
                    notes.append(
                        f"Quality failures improved by {abs(diff)} since previous check window."
                    )
                else:
                    notes.append(f"Quality failures increased by {diff} since previous check window.")

    if not notes:
        notes.append("Insufficient history to compute change narrative yet.")

    return notes


tabs = st.tabs(
    [
        "📊 Executive",
        "🔎 Risk Diagnostics",
        "📈 Model Diagnostics",
        "💡 Policy Drilldown",
        "🛠️ Operations",
        "📋 Data Explorer",
    ]
)

with tabs[0]:
    st.markdown("## Executive Summary")

    total_districts = int(df["ags"].nunique())
    systemic_count = int((df["risk_band"] == "Systemic Risk").sum())
    watch_count = int((df["risk_band"] == "Watch").sum())
    resilient_count = int((df["risk_band"] == "Resilient").sum())

    risk_exposed_share = (systemic_count + watch_count) / total_districts if total_districts else 0.0
    valid_scores = df["resilience_score"].dropna()
    median_score = float(valid_scores.median()) if not valid_scores.empty else 0.0
    p25_score = float(valid_scores.quantile(0.25)) if not valid_scores.empty else 0.0
    p75_score = float(valid_scores.quantile(0.75)) if not valid_scores.empty else 0.0

    st.markdown(
        "This view summarizes system-wide labor resilience and prioritizes where action is needed first. "
        "Interpretation principle: districts below score 1.0 are structurally supply-constrained against "
        "the current demand proxy."
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Districts", f"{total_districts:,}")
    col2.metric("Systemic Risk", systemic_count)
    col3.metric("Watch", watch_count)
    col4.metric("Resilient", resilient_count)

    c5, c6, c7 = st.columns(3)
    c5.metric("Risk-Exposed Share", _fmt_pct(risk_exposed_share))
    c6.metric("Median Resilience Score", f"{median_score:.2f}")
    c7.metric("Score IQR", f"{p25_score:.2f} - {p75_score:.2f}")

    st.info(
        "Key insight: "
        f"{_fmt_pct(risk_exposed_share)} of districts are in Systemic Risk or Watch, "
        "indicating broad pressure on vocational-to-healthcare supply alignment."
    )

    fig_risk = px.histogram(
        df,
        x="risk_band",
        category_orders={"risk_band": risk_order},
        color="risk_band",
        title="Districts by Risk Band",
        color_discrete_map={
            "Systemic Risk": "#d62728",
            "Watch": "#ff7f0e",
            "Resilient": "#2ca02c",
            "Missing demand baseline": "#7f7f7f",
        },
    )
    st.plotly_chart(fig_risk, use_container_width=True)

    st.markdown("### Top 5 Critical Findings")
    top_findings = _build_top_findings(df, forecast_errors_df, quality_df)
    for idx, finding in enumerate(top_findings, start=1):
        st.markdown(f"{idx}. {finding}")

with tabs[1]:
    st.markdown("## Risk Diagnostics")
    st.markdown(
        "This tab explains why districts are risky, how large demand gaps are, and where uncertainty "
        "or outliers may affect interpretation."
    )

    left, right = st.columns(2)

    with left:
        scatter_df = df[df["total_beds"].notna() & df["forecasted_graduates"].notna()].copy()
        size_col = "confidence_score" if "confidence_score" in scatter_df.columns else None
        fig_scatter = px.scatter(
            scatter_df,
            x="forecasted_graduates",
            y="total_beds",
            color="risk_band",
            hover_data=["ags", "district_name", "resilience_score"],
            size=size_col,
            title="Supply vs Demand Proxy by District",
            color_discrete_map={
                "Systemic Risk": "#d62728",
                "Watch": "#ff7f0e",
                "Resilient": "#2ca02c",
                "Missing demand baseline": "#7f7f7f",
            },
        )
        if not scatter_df.empty:
            min_x = float(scatter_df["forecasted_graduates"].min())
            max_x = float(scatter_df["forecasted_graduates"].max())
            fig_scatter.add_trace(
                go.Scatter(
                    x=[min_x, max_x],
                    y=[min_x, max_x],
                    mode="lines",
                    name="Parity Line (Supply = Demand)",
                    line=dict(color="#444", dash="dash"),
                )
            )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with right:
        st.markdown("### Demand Gap Leaderboard")
        gap_cols = [
            "ags",
            "district_name",
            "risk_band",
            "forecasted_graduates",
            "total_beds",
            "demand_gap",
            "resilience_score",
        ]
        show_gap_cols = [c for c in gap_cols if c in df.columns]
        top_gap = df.sort_values("demand_gap", ascending=False).head(15)
        st.dataframe(top_gap[show_gap_cols], use_container_width=True)

    st.markdown("### Confidence and Sensitivity Summary by Risk Band")
    agg_parts: dict[str, str] = {}
    if "confidence_score" in df.columns:
        agg_parts["confidence_score"] = "mean"
    if "sensitivity_impact" in df.columns:
        agg_parts["sensitivity_impact"] = "mean"
    if "outlier_flag" in df.columns:
        agg_parts["outlier_flag"] = "mean"

    if agg_parts:
        risk_diag = df.groupby("risk_band", dropna=False).agg(agg_parts)
        if "outlier_flag" in risk_diag.columns:
            risk_diag = risk_diag.rename(columns={"outlier_flag": "outlier_share"})
        st.dataframe(risk_diag.round(3), use_container_width=True)
    else:
        st.info("No methodology diagnostic columns found for confidence/sensitivity analysis.")

with tabs[2]:
    st.markdown("## Model Diagnostics")
    st.markdown(
        "This tab focuses on forecast quality evidence and model selection reliability, "
        "so users can judge how much trust to place in district-level recommendations."
    )

    if forecast_errors_df.empty:
        st.warning(
            "No forecast error records available. This usually means backtest output is empty "
            "for the current run or horizon setup."
        )
    else:
        model_stats = (
            forecast_errors_df.groupby("model_name", as_index=False)
            .agg(
                districts_evaluated=("ags", "nunique"),
                backtest_rows=("ags", "count"),
                mae=("abs_error", "mean"),
                median_abs_error=("abs_error", "median"),
                p90_abs_error=("abs_error", lambda s: s.quantile(0.9)),
            )
            .sort_values("mae")
        )

        best_model = str(model_stats.iloc[0]["model_name"]) if not model_stats.empty else "n/a"
        best_mae = float(model_stats.iloc[0]["mae"]) if not model_stats.empty else 0.0

        st.success(
            f"Best model by average absolute error in current backtest: {best_model} "
            f"(MAE {best_mae:.2f})."
        )

        fig_mae = px.bar(
            model_stats,
            x="model_name",
            y="mae",
            title="Average Absolute Error (Lower is Better)",
            text_auto=".2f",
        )
        st.plotly_chart(fig_mae, use_container_width=True)
        st.dataframe(model_stats.round(3), use_container_width=True)

    risk_structural = (
        df.groupby("risk_band")
        .agg(
            district_count=("ags", "count"),
            avg_score=("resilience_score", "mean"),
            median_graduates=("forecasted_graduates", "median"),
        )
        .round(2)
    )
    st.markdown("### Risk-Band Structural Summary")
    st.dataframe(risk_structural, use_container_width=True)

with tabs[3]:
    st.markdown("## Policy Drilldown")
    st.markdown(
        "Select a district for contextual recommendations, explicit caveats, and methodology-aware notes."
    )

    selected_ags = st.selectbox(
        "Select District:",
        options=sorted(df["ags"].dropna().unique()),
        format_func=lambda x: (
            f"{x} - {df[df['ags'] == x]['district_name'].iloc[0] if x in df['ags'].values else 'Unknown'}"
        ),
    )

    if selected_ags:
        district_row = df[df["ags"] == selected_ags].iloc[0]

        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Risk Band", str(district_row.get("risk_band", "n/a")))
        a2.metric("Resilience Score", f"{float(district_row.get('resilience_score', 0.0)):.2f}")
        a3.metric("Forecasted Graduates", f"{float(district_row.get('forecasted_graduates', 0.0)):.0f}")
        a4.metric("Hospital Beds", f"{float(district_row.get('total_beds', 0.0)):.0f}")

        report = generate_district_policy_report(district_row.to_dict())
        st.markdown(report)

        st.markdown("### Methodology Notes")
        st.info(str(district_row.get("methodology_notes", "No additional notes.")))

with tabs[4]:
    st.markdown("## Operations and Data Quality")
    st.markdown(
        "Operational confidence is a policy prerequisite. This tab tracks pipeline reliability "
        "and quality/SLA checks from the latest runs."
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Recent Pipeline Runs")
        if pipeline_summary_df.empty:
            st.warning("Pipeline run summary file not found.")
        else:
            recent_runs = pipeline_summary_df.sort_values("started_at", ascending=False).head(10)
            success_rate = recent_runs["status"].eq("success").mean() if not recent_runs.empty else 0.0
            st.metric("Recent Success Rate (last 10)", _fmt_pct(float(success_rate)))
            st.dataframe(recent_runs, use_container_width=True)

    st.markdown("### What Changed Since Last Run")
    change_notes = _build_change_notes(pipeline_summary_df, quality_df)
    for idx, note in enumerate(change_notes, start=1):
        st.markdown(f"{idx}. {note}")

    with c2:
        st.markdown("### Quality and SLA Events")
        if quality_df.empty:
            st.warning("Quality/SLA artifact not found.")
        else:
            latest_checks = quality_df.sort_values("checked_at", ascending=False).head(50)
            fail_count = int((latest_checks["status"] == "fail").sum())
            st.metric("Recent Failed Checks", fail_count)
            status_summary = latest_checks.groupby(["severity", "status"], as_index=False).size()
            fig_quality = px.bar(
                status_summary,
                x="severity",
                y="size",
                color="status",
                title="Quality Check Outcomes by Severity",
                barmode="group",
            )
            st.plotly_chart(fig_quality, use_container_width=True)
            st.dataframe(latest_checks, use_container_width=True)

with tabs[5]:
    st.markdown("## Detailed Data Explorer")

    col_filter_risk, col_filter_model = st.columns(2)
    with col_filter_risk:
        selected_risk = st.multiselect(
            "Filter by Risk Band:",
            options=risk_order,
            default=risk_order,
        )
    with col_filter_model:
        selected_models = st.multiselect(
            "Filter by Forecast Model:",
            options=sorted(df["selected_model"].dropna().unique()),
            default=sorted(df["selected_model"].dropna().unique()),
        )

    filtered_df = df[(df["risk_band"].isin(selected_risk)) & (df["selected_model"].isin(selected_models))]

    show_cols = [
        "ags",
        "district_name",
        "selected_model",
        "forecasted_graduates",
        "total_beds",
        "resilience_score",
        "risk_band",
        "confidence_score",
        "sensitivity_impact",
        "outlier_flag",
        "demand_gap",
        "coverage_ratio",
    ]
    available_cols = [col for col in show_cols if col in filtered_df.columns]

    st.dataframe(
        filtered_df[available_cols].sort_values(["risk_band", "resilience_score"], na_position="last"),
        use_container_width=True,
    )

    csv_download = filtered_df[available_cols].to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv_download,
        file_name="district_resilience_data.csv",
        mime="text/csv",
    )
