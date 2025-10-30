from __future__ import annotations
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Union

import numpy as np
import pandas as pd

from .utils import path_proc, path_raw

# Reproducible randomness
RNG = np.random.default_rng(42)


def _choose_users(n_users: int) -> list[str]:
    return [f"u{100000 + i}" for i in range(n_users)]


def _draw_video_length(rows: int) -> np.ndarray:
    """
    Log-normal seconds, centered around short-form (≈45s median), capped at 300s.
    """
    secs = np.clip(RNG.lognormal(mean=3.8, sigma=0.5, size=rows), 5, 300)
    return secs.astype(int)


def _simulate_day(
    users: list[str],
    videos_df: pd.DataFrame,
    date_dt: Union[date, datetime],
    max_sessions_per_user: int = 3,
) -> pd.DataFrame:
    """Return watch events DataFrame for a single day."""
    if videos_df.empty:
        return pd.DataFrame()

    # Normalize day fields (support both date and datetime)
    if isinstance(date_dt, datetime):
        day_y, day_m, day_d = date_dt.year, date_dt.month, date_dt.day
    else:  # it's a date
        day_y, day_m, day_d = date_dt.year, date_dt.month, date_dt.day

    events: list[dict] = []

    # Sample DAU ~ 35% of user base
    dau_count = max(1, int(len(users) * 0.35))
    active_users = RNG.choice(users, size=dau_count, replace=False)

    # Popularity weights by (views + 1)
    if "views" in videos_df.columns and len(videos_df) > 0:
        weights = (videos_df["views"].to_numpy(dtype=float) + 1.0)
        weights = weights / weights.sum()
    else:
        weights = None

    for u in active_users:
        # sessions_today ∈ [1, max_sessions_per_user]
        sessions_today = int(RNG.integers(low=1, high=max_sessions_per_user + 1))
        for _ in range(sessions_today):
            session_id = str(uuid.uuid4())

            # Start time random during the day (UTC)
            start = datetime(
                day_y,
                day_m,
                day_d,
                int(RNG.integers(0, 24)),
                int(RNG.integers(0, 60)),
                int(RNG.integers(0, 60)),
                tzinfo=timezone.utc,
            )

            # Videos in session 1–5
            k = int(RNG.integers(1, 6))
            seed = int(RNG.integers(0, 1_000_000_000))  # Python int for pandas' random_state
            vids = videos_df.sample(n=k, weights=weights, replace=True, random_state=seed).reset_index(drop=True)
            lengths = _draw_video_length(len(vids))

            # Popularity tier codes by views using qcut → labels=False (ints 0..q-1)
            if "views" in vids.columns and vids["views"].notna().any():
                uniq = int(vids["views"].nunique())
                q = max(1, min(4, uniq))  # 1..4 bins
                tier_codes = pd.qcut(
                    vids["views"].astype(float),
                    q=q,
                    labels=False,
                    duplicates="drop",
                )
                # If qcut collapses to a single bin, fill with zeros
                if isinstance(tier_codes, pd.Series):
                    tier_codes = tier_codes.fillna(0).astype(int)
                else:
                    tier_codes = pd.Series([0] * len(vids), index=vids.index)
            else:
                tier_codes = pd.Series([0] * len(vids), index=vids.index)

            for i in range(len(vids)):
                row = vids.iloc[i]
                vid_id = str(row["video_id"])
                video_len = int(lengths[i])

                # Completion propensity by popularity tier (0..3 → ~0.55..0.85)
                tier = int(tier_codes.iloc[i]) if i < len(tier_codes) else 0
                base_mu = 0.55 + 0.1 * tier
                watch_pct = float(np.clip(RNG.normal(loc=base_mu, scale=0.2), 0.02, 1.0))
                watch_secs = max(1, int(watch_pct * video_len))
                completed = watch_secs >= int(0.9 * video_len)
                drop_pct = min(1.0, watch_secs / max(1, video_len))

                # Event time increments inside session
                ev_time = start + timedelta(seconds=int(i * (video_len * 1.1)))
                events.append(
                    {
                        "user_id": u,
                        "session_id": session_id,
                        "event_time": ev_time,
                        "video_id": vid_id,
                        "watch_seconds": watch_secs,
                        "video_length_seconds": video_len,
                        "completed": completed,
                        "dropoff_position_pct": drop_pct,
                    }
                )

    return pd.DataFrame(events)


def main():
    clean_path = path_proc("videos_clean.parquet")
    if not os.path.exists(clean_path):
        print(f"[simulate] {clean_path} missing. Run clean first.")
        return

    vids = pd.read_parquet(clean_path)
    if vids.empty:
        print("[simulate] videos_clean is empty.")
        return

    # Create (or reuse) users
    users = _choose_users(n_users=2000)

    # Simulate last 30 days
    today = datetime.now(timezone.utc).date()
    start_day = today - timedelta(days=30)

    frames: list[pd.DataFrame] = []
    for d in range(30):
        day = start_day + timedelta(days=d)  # this is a 'date', which our function accepts
        frames.append(_simulate_day(users, vids, day))

    events = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if events.empty:
        print("[simulate] no events were generated.")
        return

    # Persist
    out_csv = path_raw("watch_events.csv")
    out_parq = path_proc("watch_events.parquet")
    events.to_csv(out_csv, index=False)
    events.to_parquet(out_parq, index=False)
    print(f"[simulate] wrote {out_csv} and {out_parq} ({len(events):,} events)")


if __name__ == "__main__":
    main()
