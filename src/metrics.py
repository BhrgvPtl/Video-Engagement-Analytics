from __future__ import annotations
from typing import Dict
import pandas as pd


def retention_rates(events: pd.DataFrame) -> Dict[str, float]:
    """
    Compute D1/D7/D30 retention using first-seen cohorts.
    """
    if events is None or events.empty:
        return {"d1": 0.0, "d7": 0.0, "d30": 0.0}

    ev = events.copy()
    ev["event_time"] = pd.to_datetime(ev["event_time"], errors="coerce", utc=True)
    ev["day"] = ev["event_time"].dt.floor("D")

    # First day per user
    first_day_df = (
        ev.groupby("user_id", as_index=False)
          .agg(first_day=("day", "min"))
    )
    ev = ev.merge(first_day_df, on="user_id", how="left")

    # Integer day difference from first_seen
    ev["day_delta"] = (ev["day"] - ev["first_day"]).dt.days

    out: Dict[str, float] = {}
    for label, delta in (("d1", 1), ("d7", 7), ("d30", 30)):
        retained_flags = (
            ev.groupby("user_id")["day_delta"]
              .apply(lambda s: bool((s == delta).any()))
        )
        out[label] = float(retained_flags.mean()) if len(retained_flags) else 0.0

    return out


def rolling_active_users(events: pd.DataFrame, window_days: int) -> int:
    """
    Distinct users in the last N days based on the max event_time present.
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

    users_in_window: pd.Series = ev.loc[mask, "user_id"].astype(object)
    return int(users_in_window.nunique())
