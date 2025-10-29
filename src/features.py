"""Feature engineering utilities for sessionization and retention analysis."""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd


def _ensure_datetime(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if not np.issubdtype(df[column].dtype, np.datetime64):
        df = df.copy()
        df[column] = pd.to_datetime(df[column])
    return df


def sessionize_events(events: pd.DataFrame, session_gap_minutes: int = 30) -> pd.DataFrame:
    """Assign session identifiers to chronologically ordered events."""

    if events.empty:
        return events.copy()

    df = _ensure_datetime(events, "event_time").sort_values(["user_id", "event_time"]).copy()
    df["completion_ratio"] = (df["watched_seconds"] / df["video_duration"]).clip(0, 1)
    df["watch_day"] = df["event_time"].dt.floor("D")

    prev_time = df.groupby("user_id")["event_time"].shift()
    gap = pd.Timedelta(minutes=session_gap_minutes)
    new_session = (prev_time.isna()) | ((df["event_time"] - prev_time) > gap)
    df["session_index"] = new_session.astype(int).groupby(df["user_id"]).cumsum()
    df["session_id"] = df["user_id"].astype(str) + "-" + df["session_index"].astype(str)
    df["session_start"] = df.groupby("session_id")["event_time"].transform("min")
    return df.drop(columns=["session_index"])


def aggregate_sessions(sessionized_events: pd.DataFrame) -> pd.DataFrame:
    """Summarize session-level metrics from sessionized events."""

    if sessionized_events.empty:
        return pd.DataFrame(
            columns=[
                "session_id",
                "user_id",
                "session_start",
                "session_end",
                "videos_watched",
                "creators_engaged",
                "session_watch_seconds",
                "mean_completion_ratio",
                "session_duration_minutes",
            ]
        )

    df = _ensure_datetime(sessionized_events, "event_time")
    grouped = (
        df.groupby(["session_id", "user_id"], as_index=False)
        .agg(
            session_start=("session_start", "min"),
            session_end=("event_time", "max"),
            videos_watched=("video_id", "nunique"),
            creators_engaged=("creator_id", "nunique"),
            session_watch_seconds=("watched_seconds", "sum"),
            mean_completion_ratio=("completion_ratio", "mean"),
        )
        .sort_values("session_start")
    )
    grouped["session_duration_minutes"] = (
        (grouped["session_end"] - grouped["session_start"]).dt.total_seconds() / 60.0
    )
    return grouped


def retention_curve(events: pd.DataFrame, days: Sequence[int] = (1, 7, 30)) -> pd.DataFrame:
    """Compute retention rates for specified day offsets relative to first watch."""

    if events.empty:
        return pd.DataFrame({"day": days, "retention_rate": [0.0] * len(days)})

    df = sessionize_events(events)
    cohort = df.groupby("user_id")["watch_day"].min()
    cohort_size = float(len(cohort))
    df["day_offset"] = (df["watch_day"] - df["watch_day"].groupby(df["user_id"]).transform("min")).dt.days

    rates = []
    for day in days:
        retained = df.loc[df["day_offset"] == day, "user_id"].nunique()
        rate = retained / cohort_size if cohort_size else 0.0
        rates.append(rate)
    return pd.DataFrame({"day": list(days), "retention_rate": rates})


def creator_watch_share(events: pd.DataFrame) -> pd.DataFrame:
    """Share of watch seconds attributed to each creator."""

    if events.empty:
        return pd.DataFrame(columns=["creator_id", "watch_seconds", "watch_share"])

    totals = (
        events.groupby("creator_id", as_index=False)["watched_seconds"].sum().rename(columns={"watched_seconds": "watch_seconds"})
    )
    total_watch = totals["watch_seconds"].sum()
    totals["watch_share"] = totals["watch_seconds"] / total_watch if total_watch else 0.0
    return totals.sort_values("watch_seconds", ascending=False)


def daily_active_users(events: pd.DataFrame) -> pd.DataFrame:
    """Daily active users derived from watch events."""

    if events.empty:
        return pd.DataFrame(columns=["date", "active_users"])

    df = _ensure_datetime(events, "event_time")
    dau = (
        df.assign(date=df["event_time"].dt.floor("D"))
        .groupby("date", as_index=False)["user_id"].nunique()
        .rename(columns={"user_id": "active_users"})
    )
    return dau
