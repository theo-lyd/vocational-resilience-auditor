from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Vocational Resilience Auditor", layout="wide")
st.title("The Vocational Resilience Auditor")
st.caption("District-level supply-demand signal based on vocational output and hospital capacity")

output_file = Path("data/gold/dim_district_resilience.csv")
if not output_file.exists():
    st.warning("No gold output found. Run: python scripts/run_pipeline.py")
    st.stop()

df = pd.read_csv(output_file)
if df.empty:
    st.warning("Gold dataset is empty.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Districts", f"{df['ags'].nunique():,}")
col2.metric("Median Resilience", f"{df['resilience_score'].median(skipna=True):.2f}")
col3.metric("Systemic Risk Count", int((df['risk_band'] == 'Systemic Risk').sum()))

risk_order = ["Systemic Risk", "Watch", "Resilient", "Missing demand baseline"]
fig = px.histogram(
    df,
    x="risk_band",
    category_orders={"risk_band": risk_order},
    color="risk_band",
    title="District Risk Band Distribution",
)
st.plotly_chart(fig, use_container_width=True)

show_cols = [
    "ags",
    "district_name",
    "selected_model",
    "forecast_year",
    "forecasted_graduates",
    "hospital_year",
    "total_beds",
    "resilience_score",
    "risk_band",
]
st.dataframe(df[show_cols].sort_values(["risk_band", "resilience_score"], na_position="last"), use_container_width=True)
