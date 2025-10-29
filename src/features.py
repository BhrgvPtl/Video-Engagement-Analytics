"""Feature engineering utilities for short-form video engagement analytics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd


@dataclass
class SessionConfig:
    """Configuration for turning watch events into sessions."""

    session_timeout_minutes: int = 30
    min_events_per_session: int = 1


def load_watch_events(path: str) -> pd.DataFrame:
    """Load watch event logs from CSV.

    The raw schema is expected to include:
    - user_id: unique user identifier
    - video_id: video identifier
    - event_timestamp: ISO timestamp of the watch event
    - watch_time_seconds: how long the user watched
    - completed: boolean flag indicating full watch
    - dropped_at_percent: drop-off percentage position
    """

    df = pd.read_csv(path, parse_dates=["event_timestamp"])
    required_columns: Iterable[str] = [
        "user_id",
        "video_id",
        "event_timestamp",
        "watch_time_seconds",
        "completed",
        "dropped_at_percent",
    ]
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df


def _sessionize(df: pd.DataFrame, config: SessionConfig) -> pd.DataFrame:
    """Assign session identifiers to watch events."""

    df = df.sort_values(["user_id", "event_timestamp"]).copy()
    timeout = pd.Timedelta(minutes=config.session_timeout_minutes)
    df["prev_event"] = df.groupby("user_id")["event_timestamp"].shift(1)
    df["session_break"] = (
        (df["prev_event"].isna())
        | ((df["event_timestamp"] - df["prev_event"]) > timeout)
    )
    df["session_id"] = df.groupby("user_id")["session_break"].cumsum()
    df.drop(columns=["prev_event", "session_break"], inplace=True)
    return df


def build_session_features(
    events: pd.DataFrame, config: SessionConfig | None = None
) -> pd.DataFrame:
    """Aggregate watch events into session-level engagement metrics."""

    config = config or SessionConfig()
    events_with_sessions = _sessionize(events, config)

    aggregations = {
        "watch_time_seconds": "sum",
        "video_id": "nunique",
        "completed": "mean",
        "dropped_at_percent": "mean",
    }

    session_features = (
        events_with_sessions
        .groupby(["user_id", "session_id"], as_index=False)
        .agg(aggregations)
        .rename(
            columns={
                "watch_time_seconds": "session_watch_time_seconds",
                "video_id": "unique_videos",
                "completed": "completion_rate",
                "dropped_at_percent": "avg_drop_off_percent",
            }
        )
    )

    session_features["session_length_minutes"] = (
        session_features["session_watch_time_seconds"] / 60
    )

    session_features = session_features[
        session_features["unique_videos"] >= config.min_events_per_session
    ]

    return session_features


def calculate_kpis(events: pd.DataFrame) -> pd.Series:
    """Compute core retention KPIs from watch events."""

    dau = events.groupby(events["event_timestamp"].dt.date)["user_id"].nunique()
    wau = (
        events.set_index("event_timestamp")
        .groupby("user_id")
        .resample("7D")
        .size()
        .groupby(level=0)
        .mean()
    )
    completion_rate = events["completed"].mean()
    avg_drop_off = events["dropped_at_percent"].mean()

    return pd.Series(
        {
            "dau_mean": dau.mean(),
            "wau_mean": wau.mean(),
            "completion_rate": completion_rate,
            "avg_drop_off_percent": avg_drop_off,
        }
    )


def retention_curves(retention_table: pd.DataFrame, days: Iterable[int] | None = None) -> pd.DataFrame:
    """Reshape retention table to focus on D1/D7/D30."""

    days = list(days or (1, 7, 30))
    available = [column for column in days if column in retention_table.columns]
    if not available:
        raise ValueError("Retention table does not contain requested days")

    return (
        retention_table
        .loc[:, available]
        .rename(columns={day: f"D{day}_retention" for day in available})
    )
