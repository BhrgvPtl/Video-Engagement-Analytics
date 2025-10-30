from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Canonical event produced by simulate_watch.py and consumed by features.py
@dataclass(frozen=True)
class WatchEvent:
    user_id: str
    session_id: str
    event_time: datetime
    video_id: str
    watch_seconds: int
    video_length_seconds: int
    completed: bool
    dropoff_position_pct: float  # 0..1

# Aggregated per-session features written by features.py (optional typed view)
@dataclass(frozen=True)
class SessionFeature:
    session_id: str
    user_id: str
    session_start: datetime
    session_end: datetime
    session_duration_seconds: int
    videos_watched: int
    avg_watch_pct: float
    completion_rate: float
    creator_watch_share_top: Optional[str] = None
