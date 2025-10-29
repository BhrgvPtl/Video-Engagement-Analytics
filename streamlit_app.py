"""Streamlit dashboard for short-form video engagement analytics."""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from src.churn_model import prepare_training_data, train_churn_model
from src.features import SessionConfig, build_session_features, calculate_kpis, load_watch_events


@st.cache_data(show_spinner=False)
def load_events(path: Path) -> pd.DataFrame:
    return load_watch_events(str(path))


@st.cache_data(show_spinner=False)
def load_sessions(path: Path, session_config: SessionConfig) -> pd.DataFrame:
    events = load_events(path)
    return build_session_features(events, session_config)


def main() -> None:
    st.set_page_config(page_title="Reels Retention Command Center", layout="wide")
    st.title("📈 Short-Form Video Engagement Analytics")
    st.caption("Meta-aligned KPIs with retention, completion, and creator share insights.")

    data_dir = Path("data")
    raw_events_path = data_dir / "raw" / "watch_events_sample.csv"
    processed_sessions_path = data_dir / "processed" / "session_features.parquet"

    st.sidebar.header("Data Inputs")
    st.sidebar.write("Raw events: ", raw_events_path)
    st.sidebar.write("Processed sessions: ", processed_sessions_path)

    session_timeout = st.sidebar.slider("Session timeout (minutes)", 5, 60, 30)
    min_events = st.sidebar.slider("Minimum videos per session", 1, 10, 1)
    session_config = SessionConfig(
        session_timeout_minutes=session_timeout,
        min_events_per_session=min_events,
    )

    if raw_events_path.exists():
        events = load_events(raw_events_path)
        st.subheader("Retention KPIs")
        kpis = calculate_kpis(events)
        st.metric("DAU (mean)", f"{kpis['dau_mean']:.0f}")
        st.metric("WAU (mean)", f"{kpis['wau_mean']:.0f}")
        st.metric("Completion rate", f"{kpis['completion_rate']:.1%}")
        st.metric("Avg. drop-off", f"{kpis['avg_drop_off_percent']:.1f}%")

        st.subheader("Watch Distribution")
        st.dataframe(
            events.groupby("video_id")[["watch_time_seconds", "completed"]]
            .agg({"watch_time_seconds": "sum", "completed": "mean"})
            .sort_values("watch_time_seconds", ascending=False)
            .head(20)
        )
    else:
        st.warning("Upload watch_events_sample.csv to data/raw to view KPIs.")

    if processed_sessions_path.exists():
        if raw_events_path.exists():
            sessions = load_sessions(raw_events_path, session_config)
            st.subheader("Session Overview")
            st.dataframe(
                sessions[
                    [
                        "user_id",
                        "session_id",
                        "session_watch_time_seconds",
                        "unique_videos",
                        "completion_rate",
                        "avg_drop_off_percent",
                    ]
                ].head(50)
            )
        else:
            st.warning(
                "Session overview requires raw events in data/raw/watch_events_sample.csv."
            )

        try:
            training_df = prepare_training_data(str(processed_sessions_path))
            _, metrics = train_churn_model(training_df)
            st.subheader("Churn Model Performance")
            st.json(metrics["weighted avg"])
        except Exception as exc:  # noqa: BLE001
            st.error(f"Unable to train churn model: {exc}")
    else:
        st.info("Processed session features not found. Generate them via the feature engine.")


if __name__ == "__main__":
    main()
