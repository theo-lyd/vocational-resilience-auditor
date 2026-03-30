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
    "Interactive dashboard for district-level vocational-healthcare workforce alignment. "
    "**Powered by forecasting, confidence analysis, and evidence-based policy recommendations.**"
)

output_file = Path("data/gold/dim_district_resilience.csv")
methodology_file = Path("data/gold/resilience_methodology_enriched.csv")

if not output_file.exists():
    st.warning("No gold output found. Run: python scripts/run_pipeline.py")
    st.stop()

df = pd.read_csv(output_file)
if df.empty:
    st.warning("Gold dataset is empty.")
    st.stop()

if methodology_file.exists():
    methodology_df = pd.read_csv(methodology_file)
    df = df.merge(methodology_df[["ags", "confidence_score", "sensitivity_impact", "outlier_flag", "methodology_notes"]], 
                   on="ags", how="left")


tabs = st.tabs(["📊 Overview", "🗺️ Map View", "📈 Trends", "💡 Policy", "📋 Details"])

with tabs[0]:
    st.markdown("## Quick Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Districts", f"{df['ags'].nunique():,}")
    col2.metric("Systemic Risk", int((df["risk_band"] == "Systemic Risk").sum()))
    col3.metric("Watch", int((df["risk_band"] == "Watch").sum()))
    col4.metric("Resilient", int((df["risk_band"] == "Resilient").sum()))

    st.markdown("### Risk Distribution")
    risk_order = ["Systemic Risk", "Watch", "Resilient", "Missing demand baseline"]
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

    st.markdown("### Score Distribution")
    valid_scores = df[df["resilience_score"].notna()]["resilience_score"]
    fig_hist = px.histogram(
        valid_scores,
        nbins=30,
        title="Resilience Score Distribution",
        labels={"value": "Resilience Score", "count": "Number of Districts"},
    )
    st.plotly_chart(fig_hist, use_container_width=True)

with tabs[1]:
    st.markdown("## Geographic Overview")
    st.info(
        "⚠️ **Map visualization requires geographic data integration.** "
        "Consider: (1) merging with GeoJSON district boundaries, (2) using GeoPandas for spatial joins, "
        "(3) deploying via Plotly or Folium for interactive choropleth rendering. "
        "For now, showing tabular geographic summary."
    )

    geo_summary = (
        df.groupby("risk_band")
        .agg(
            district_count=("ags", "count"),
            avg_score=("resilience_score", "mean"),
            median_graduates=("forecasted_graduates", "median"),
        )
        .round(2)
    )
    st.dataframe(geo_summary, use_container_width=True)

with tabs[2]:
    st.markdown("## Forecast & Demand Trends")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### Graduates Forecast by Risk Band")
        trend_data = (
            df.groupby("risk_band")["forecasted_graduates"]
            .agg(["min", "mean", "max"])
            .round(0)
        )
        fig_grad = go.Figure()
        for risk_band in risk_order:
            if risk_band in trend_data.index:
                row = trend_data.loc[risk_band]
                fig_grad.add_trace(
                    go.Bar(
                        x=[f"{risk_band}"],
                        y=[row["mean"]],
                        error_y=dict(
                            type="data",
                            symmetric=False,
                            array=[row["max"] - row["mean"]],
                            arrayminus=[row["mean"] - row["min"]],
                        ),
                        name=risk_band,
                    )
                )
        st.plotly_chart(fig_grad, use_container_width=True)

    with col_right:
        st.markdown("### Total Hospital Beds by Risk Band")
        bed_data = (
            df.groupby("risk_band")["total_beds"]
            .agg(["min", "mean", "max"])
            .round(0)
        )
        fig_beds = go.Figure()
        for risk_band in risk_order:
            if risk_band in bed_data.index:
                row = bed_data.loc[risk_band]
                fig_beds.add_trace(
                    go.Bar(
                        x=[f"{risk_band}"],
                        y=[row["mean"]],
                        error_y=dict(
                            type="data",
                            symmetric=False,
                            array=[row["max"] - row["mean"]],
                            arrayminus=[row["mean"] - row["min"]],
                        ),
                        name=risk_band,
                    )
                )
        st.plotly_chart(fig_beds, use_container_width=True)

with tabs[3]:
    st.markdown("## Policy Recommendations")
    st.markdown(
        "**Evidence-based recommendations with confidence levels and caveats.** "
        "Select a district to see tailored guidance for workforce and healthcare planning."
    )

    selected_ags = st.selectbox(
        "Select District:",
        options=sorted(df["ags"].dropna().unique()),
        format_func=lambda x: f"{x} - {df[df['ags'] == x]['district_name'].iloc[0] if x in df['ags'].values else 'Unknown'}",
    )

    if selected_ags:
        district_row = df[df["ags"] == selected_ags].iloc[0]
        report = generate_district_policy_report(district_row.to_dict())
        st.markdown(report)

        st.markdown("### Methodology Notes")
        st.info(district_row.get("methodology_notes", "No additional notes."))

with tabs[4]:
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
            options=sorted(df["selected_model"].unique()),
            default=sorted(df["selected_model"].unique()),
        )

    filtered_df = df[
        (df["risk_band"].isin(selected_risk)) & 
        (df["selected_model"].isin(selected_models))
    ]

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
    ]
    available_cols = [col for col in show_cols if col in filtered_df.columns]

    st.dataframe(
        filtered_df[available_cols].sort_values(
            ["risk_band", "resilience_score"], na_position="last"
        ),
        use_container_width=True,
    )

    csv_download = filtered_df[available_cols].to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv_download,
        file_name="district_resilience_data.csv",
        mime="text/csv",
    )

