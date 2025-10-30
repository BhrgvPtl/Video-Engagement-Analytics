"""
Video Engagement Analytics Dashboard
------------------------------------
Interactive Streamlit app for exploring engagement, retention, and churn metrics
based on simulated YouTube short-form video data.
"""

import streamlit as st
import pandas as pd
import altair as alt
import os
# Import from your local src package
from src.features import (
    SessionConfig,
    build_session_features,
    calculate_kpis,
    _load_events as load_watch_events,
)
from src.metrics import retention_rates
from src.churn_model import prepare_training_data, train_churn_model
from src.utils import path_proc

# -------------------------------------------------------------------
# Page Configuration
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Short-Form Video Engagement Dashboard",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 Short-Form Video Engagement Analytics Dashboard")
st.markdown(
    """
    This dashboard visualizes engagement patterns, user retention,
    and churn trends simulated from YouTube short-form video data.
    """
)

# -------------------------------------------------------------------
# Load & Display Data
# -------------------------------------------------------------------
st.sidebar.header("📁 Data Controls")

if st.sidebar.button("Rebuild Session Features"):
    build_session_features(SessionConfig())

events = load_watch_events()
if events.empty:
    st.error("No watch events found. Run the data pipeline first (`make build`).")
    st.stop()

# -------------------------------------------------------------------
# KPI Summary
# -------------------------------------------------------------------
kpis = calculate_kpis()

col1, col2, col3, col4 = st.columns(4)
col1.metric("🧭 Retention D1", f"{kpis['retention_d1']*100:.1f}%")
col2.metric("📅 Retention D7", f"{kpis['retention_d7']*100:.1f}%")
col3.metric("📆 Retention D30", f"{kpis['retention_d30']*100:.1f}%")
col4.metric("⏱️ Avg Session Time", f"{kpis['avg_session_time']:.1f} sec")

col5, col6, col7, col8 = st.columns(4)
col5.metric("🎯 Completion Rate", f"{kpis['completion_rate']*100:.1f}%")
col6.metric("📉 Median Drop-off", f"{kpis['median_dropoff_pct']*100:.1f}%")
col7.metric("👤 DAU", f"{kpis['dau']:,}")
col8.metric("👥 WAU", f"{kpis['wau']:,}")

st.divider()

# -------------------------------------------------------------------
# Retention Visualization
# -------------------------------------------------------------------
st.subheader("📈 Retention Curve (D1 / D7 / D30)")

ret = retention_rates(events)
ret_df = pd.DataFrame(
    {
        "Day": ["D1", "D7", "D30"],
        "Retention Rate": [
            ret.get("d1", 0.0),
            ret.get("d7", 0.0),
            ret.get("d30", 0.0),
        ],
    }
)
chart = (
    alt.Chart(ret_df)
    .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color="#4b8bbe")
    .encode(
        x=alt.X("Day:N", title="Retention Window"),
        y=alt.Y("Retention Rate:Q", axis=alt.Axis(format="%")),
        tooltip=["Day", alt.Tooltip("Retention Rate:Q", format=".1%")],
    )
    .properties(height=300)
)
st.altair_chart(chart, use_container_width=True)

# -------------------------------------------------------------------
# Engagement Over Time
# -------------------------------------------------------------------
st.subheader("⏳ Daily Engagement Activity")

events["event_date"] = pd.to_datetime(events["event_time"], utc=True, errors="coerce").dt.date
daily_stats = (
    events.groupby("event_date", as_index=False)
    .agg(
        total_watch_seconds=("watch_seconds", "sum"),
        unique_users=("user_id", "nunique"),
    )
    .sort_values("event_date")
)
line_chart = (
    alt.Chart(daily_stats)
    .transform_fold(
        ["unique_users", "total_watch_seconds"],
        as_=["Metric", "Value"]
    )
    .mark_line(point=True)
    .encode(
        x="event_date:T",
        y="Value:Q",
        color="Metric:N",
        tooltip=["event_date:T", "Metric:N", "Value:Q"],
    )
    .properties(height=320)
)
st.altair_chart(line_chart, use_container_width=True)

# -------------------------------------------------------------------
# Churn Model Training
# -------------------------------------------------------------------
st.subheader("🤖 Churn Model (Placeholder Training)")

if st.button("Train Logistic Model"):
    X, y = prepare_training_data()
    model = train_churn_model(X, y)
    if model is not None:
        st.success(f"✅ Model trained with {len(X)} samples and {X.shape[1]} features.")
    else:
        st.warning("⚠️ Not enough data or classes to train a model.")

# -------------------------------------------------------------------
# Explore Raw / Session Data
# -------------------------------------------------------------------
st.divider()
st.subheader("📊 Explore Data")

tab1, tab2, tab3 = st.tabs(["Watch Events", "Session Features", "KPIs JSON"])

with tab1:
    st.dataframe(events.sample(min(500, len(events))), use_container_width=True)

with tab2:
    feat_path = path_proc("session_features.parquet")
    if os.path.exists(feat_path):
        feats = pd.read_parquet(feat_path)
        st.dataframe(feats.head(500), use_container_width=True)
    else:
        st.info("Session features not found. Run the pipeline first.")

with tab3:
    st.json(kpis)
