"""Engagement KPI calculations for short-form video analytics."""

from __future__ import annotations

from datetime import timedelta
from typing import Dict, List, Sequence

from .data_contracts import WatchEvent
from .features import (
    CreatorWatchShare,
    DailyActiveCount,
    SessionSummary,
    creator_watch_share,
    daily_active_users,
)


def completion_rate(events: Sequence[WatchEvent]) -> float:
    """Average completion rate across all watch events."""

    if not events:
        return 0.0
    ratios = [min(event.watched_seconds / event.video_duration, 1.0) for event in events]
    return sum(ratios) / len(ratios)


def drop_off_positions(
    events: Sequence[WatchEvent], thresholds: Sequence[float] = (0.25, 0.5, 0.75)
) -> Dict[str, float]:
    """Share of plays that drop before each completion threshold."""

    if not events:
        return {f"below_{int(th * 100)}": 0.0 for th in thresholds}

    ratios = [min(event.watched_seconds / event.video_duration, 1.0) for event in events]
    result: Dict[str, float] = {}
    for threshold in thresholds:
        result[f"below_{int(threshold * 100)}"] = sum(1 for ratio in ratios if ratio < threshold) / len(ratios)
    return result


def average_session_duration(session_summary: Sequence[SessionSummary]) -> float:
    """Mean session duration in minutes."""

    if not session_summary:
        return 0.0
    return sum(summary.session_duration_minutes for summary in session_summary) / len(session_summary)


def dau_wau_ratio(events: Sequence[WatchEvent]) -> Dict[str, float]:
    """Daily active over weekly active user ratio for the most recent day."""

    if not events:
        return {"dau": 0.0, "wau": 0.0, "ratio": 0.0}

    active_counts = daily_active_users(events)
    if not active_counts:
        return {"dau": 0.0, "wau": 0.0, "ratio": 0.0}

    latest_day = active_counts[-1].date
    dau_entry = next(
        (entry for entry in active_counts if entry.date == latest_day),
        DailyActiveCount(latest_day, 0),
    )

    wau_window_start = latest_day - timedelta(days=6)
    wau_users: set[str] = set()
    for event in events:
        day = event.event_time.date()
        if wau_window_start <= day <= latest_day:
            wau_users.add(event.user_id)

    wau = len(wau_users)
    ratio = dau_entry.active_users / wau if wau else 0.0
    return {"dau": float(dau_entry.active_users), "wau": float(wau), "ratio": float(ratio)}


def creator_contribution(events: Sequence[WatchEvent], top_n: int = 3) -> List[CreatorWatchShare]:
    """Watch-share contribution for top creators."""

    shares = creator_watch_share(events)
    return shares[:top_n]
