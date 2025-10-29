"""Streamlit dashboard for short-form video engagement analytics."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src import churn_model, features, metrics, utils

st.set_page_config(page_title="Reels Engagement Analytics", layout="wide")
st.title("Reels Engagement Analytics")
st.caption("Monitor retention, session health, and creator contribution from sample watch logs.")

# Load data
watch_events = utils.load_watch_events()
video_metadata = utils.load_video_metadata()

sessionized = features.sessionize_events(watch_events)
session_summary = features.aggregate_sessions(sessionized)
retention = features.retention_curve(watch_events)
creator_share = features.creator_watch_share(watch_events)

# Sidebar controls
st.sidebar.header("Churn Modeling")
st.sidebar.metric("Creators tracked", str(video_metadata['creator_id'].nunique()))
horizon = st.sidebar.selectbox("Retention horizon (days)", options=[1, 7, 30], index=1)

churn_dataset = churn_model.prepare_churn_dataset(watch_events, horizon_days=horizon)
model = churn_model.train_churn_model(churn_dataset)
retention_scores = churn_model.predict_retention(model, churn_dataset.features)

# KPI Tiles
col1, col2, col3 = st.columns(3)
col1.metric("Avg completion", f"{metrics.completion_rate(watch_events)*100:.1f}%")
col2.metric("Avg session duration", f"{metrics.average_session_duration(session_summary):.1f} min")
dau_stats = metrics.dau_wau_ratio(watch_events)
col3.metric("DAU/WAU", f"{dau_stats['ratio']:.2f}", help=f"DAU: {int(dau_stats['dau'])}, WAU: {int(dau_stats['wau'])}")

# Retention Curve
st.subheader("Retention Curve")
retention_chart = px.line(retention, x="day", y="retention_rate", markers=True, labels={"day": "Day", "retention_rate": "Retention"})
retention_chart.update_yaxes(tickformat=",.0%")
st.plotly_chart(retention_chart, use_container_width=True)

# Creator contribution
st.subheader("Creator Contribution")
creator_chart = px.bar(creator_share, x="creator_id", y="watch_share", labels={"watch_share": "Watch Share"})
creator_chart.update_yaxes(tickformat=",.0%")
st.plotly_chart(creator_chart, use_container_width=True)

# Drop-off diagnostics
st.subheader("Drop-off Diagnostics")
drop_stats = metrics.drop_off_positions(watch_events)
st.write(pd.DataFrame([drop_stats]))

# Churn predictions
st.subheader(f"Retention probability (D{horizon})")
st.dataframe(retention_scores.sort_values("retention_probability", ascending=False))

# Session explorer
st.subheader("Session Explorer")
st.dataframe(session_summary.head())

st.sidebar.markdown("---")
st.sidebar.caption("Sample data derived from YouTube Trending and simulated watch logs.")
