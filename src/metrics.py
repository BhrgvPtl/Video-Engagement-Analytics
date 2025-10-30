from __future__ import annotations
<<<<<<< Updated upstream

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
=======
from typing import Dict
import pandas as pd


def retention_rates(events: pd.DataFrame) -> Dict[str, float]:
    """
    Compute D1/D7/D30 retention using first-seen cohorts.
    Uses explicit day-delta ints (no Series+Timedelta arithmetic).
    """
    if events is None or events.empty:
        return {"d1": 0.0, "d7": 0.0, "d30": 0.0}

    ev = events.copy()
    ev["event_time"] = pd.to_datetime(ev["event_time"], errors="coerce", utc=True)
    ev["day"] = ev["event_time"].dt.floor("D")

    # First day per user — use agg to avoid rename ambiguity
    first_day_df = (
        ev.groupby("user_id", as_index=False)
          .agg(first_day=("day", "min"))
    )
    ev = ev.merge(first_day_df, on="user_id", how="left")

    # Integer day difference from first_seen
    ev["day_delta"] = (ev["day"] - ev["first_day"]).dt.days

    out: Dict[str, float] = {}
    for label, delta in (("d1", 1), ("d7", 7), ("d30", 30)):
        # user retained if they have any event with that exact day_delta
        retained_flags = (
            ev.groupby("user_id")["day_delta"]
              .apply(lambda s: bool((s == delta).any()))
        )
        out[label] = float(retained_flags.mean()) if len(retained_flags) else 0.0

    return out


def rolling_active_users(events: pd.DataFrame, window_days: int) -> int:
    """
    Distinct users in the last N days based on max event_time present.
    Casts explicitly to keep type checkers satisfied.
    """
    if events is None or events.empty:
        return 0

    ev = events.copy()
    ev["event_time"] = pd.to_datetime(ev["event_time"], errors="coerce", utc=True)

    max_ts = ev["event_time"].max()
    if pd.isna(max_ts):
        return 0

    window_start = max_ts - pd.Timedelta(days=int(window_days))
    mask: pd.Series = (ev["event_time"] >= window_start) & (ev["event_time"] <= max_ts)

    # Ensure Series type, then cast dtype to object before nunique()
    users_in_window: pd.Series = ev.loc[mask, "user_id"]
    users_in_window = users_in_window.astype(object)

    return int(users_in_window.nunique())
>>>>>>> Stashed changes
