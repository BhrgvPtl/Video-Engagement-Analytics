"""Engagement KPI calculations for short-form video analytics."""

from __future__ import annotations

from typing import Dict, Sequence

import pandas as pd


def completion_rate(events: pd.DataFrame) -> float:
    """Average completion rate across all watch events."""

    if events.empty:
        return 0.0
    ratios = (events["watched_seconds"] / events["video_duration"]).clip(0, 1)
    return float(ratios.mean())


def drop_off_positions(events: pd.DataFrame, thresholds: Sequence[float] = (0.25, 0.5, 0.75)) -> Dict[str, float]:
    """Share of plays that drop before each completion threshold."""

    if events.empty:
        return {f"below_{int(th * 100)}": 0.0 for th in thresholds}

    ratios = (events["watched_seconds"] / events["video_duration"]).clip(0, 1)
    return {f"below_{int(th * 100)}": float((ratios < th).mean()) for th in thresholds}


def average_session_duration(session_summary: pd.DataFrame) -> float:
    """Mean session duration in minutes."""

    if session_summary.empty:
        return 0.0
    return float(session_summary["session_duration_minutes"].mean())


def dau_wau_ratio(events: pd.DataFrame) -> Dict[str, float]:
    """Daily active over weekly active user ratio for the most recent day."""

    if events.empty:
        return {"dau": 0.0, "wau": 0.0, "ratio": 0.0}

    df = events.copy()
    df["event_time"] = pd.to_datetime(df["event_time"])
    df["watch_day"] = df["event_time"].dt.floor("D")
    latest_day = df["watch_day"].max()
    dau = df.loc[df["watch_day"] == latest_day, "user_id"].nunique()
    wau_window_start = latest_day - pd.Timedelta(days=6)
    wau = df.loc[(df["watch_day"] >= wau_window_start) & (df["watch_day"] <= latest_day), "user_id"].nunique()
    ratio = dau / wau if wau else 0.0
    return {"dau": float(dau), "wau": float(wau), "ratio": float(ratio)}


def creator_contribution(events: pd.DataFrame, top_n: int = 3) -> pd.DataFrame:
    """Watch-share contribution for top creators."""

    if events.empty:
        return pd.DataFrame(columns=["creator_id", "watch_seconds", "watch_share"])

    totals = (
        events.groupby("creator_id", as_index=False)["watched_seconds"].sum().rename(columns={"watched_seconds": "watch_seconds"})
    )
    total_watch = totals["watch_seconds"].sum()
    totals["watch_share"] = totals["watch_seconds"] / total_watch if total_watch else 0.0
    return totals.sort_values("watch_seconds", ascending=False).head(top_n).reset_index(drop=True)
