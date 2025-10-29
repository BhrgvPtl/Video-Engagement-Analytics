"""Feature engineering utilities for sessionization and retention analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List, Mapping, Sequence

try:  # Optional dependency: pandas is not required for core operation.
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover - pandas optional
    pd = None  # type: ignore

from .data_contracts import WatchEvent


def _ensure_watch_events(
    events: Sequence[WatchEvent] | Iterable[Mapping[str, object]]
) -> List[WatchEvent]:
    """Normalize heterogeneous inputs into validated ``WatchEvent`` records."""

    if isinstance(events, Sequence) and all(isinstance(event, WatchEvent) for event in events):
        return list(events)

    if pd is not None and isinstance(events, pd.DataFrame):  # pragma: no cover - optional path
        frame = events.copy()
        frame["event_time"] = pd.to_datetime(frame["event_time"], utc=True)
        records = frame.to_dict("records")
        return _ensure_watch_events(records)

    normalized: List[WatchEvent] = []
    for record in events:
        if isinstance(record, WatchEvent):
            normalized.append(record)
            continue
        if not isinstance(record, Mapping):
            raise TypeError(
                "events must be WatchEvent instances, mappings, or a pandas.DataFrame"
            )
        event_time = record.get("event_time")
        if isinstance(event_time, datetime):
            parsed_time = event_time
        elif event_time is None:
            raise ValueError("event_time is required")
        else:
            parsed_time = datetime.fromisoformat(str(event_time).replace("Z", "+00:00"))
        normalized.append(
            WatchEvent(
                user_id=str(record["user_id"]),
                video_id=str(record["video_id"]),
                creator_id=str(record["creator_id"]),
                event_time=parsed_time,
                watched_seconds=float(record["watched_seconds"]),
                video_duration=float(record["video_duration"]),
            )
        )
    return normalized


@dataclass(frozen=True)
class SessionizedEvent(WatchEvent):
    """Watch event annotated with session identifiers."""

    session_id: str
    session_start: datetime
    completion_ratio: float
    watch_day: date


@dataclass(frozen=True)
class SessionSummary:
    """Aggregated metrics describing a viewing session."""

    session_id: str
    user_id: str
    session_start: datetime
    session_end: datetime
    videos_watched: int
    creators_engaged: int
    session_watch_seconds: float
    mean_completion_ratio: float
    session_duration_minutes: float


@dataclass(frozen=True)
class RetentionPoint:
    """Retention rate for a specific day offset."""

    day: int
    retention_rate: float


@dataclass(frozen=True)
class CreatorWatchShare:
    """Contribution of a creator to total watch time."""

    creator_id: str
    watch_seconds: float
    watch_share: float


@dataclass(frozen=True)
class DailyActiveCount:
    """Active user count for a specific day."""

    date: date
    active_users: int


def sessionize_events(
    events: Sequence[WatchEvent] | Iterable[Mapping[str, object]],
    session_gap_minutes: int = 30,
) -> List[SessionizedEvent]:
    """Assign session identifiers to chronologically ordered events."""

    normalized = _ensure_watch_events(events)

    if not normalized:
        return []

    gap = timedelta(minutes=session_gap_minutes)
    sorted_events = sorted(normalized, key=lambda event: (event.user_id, event.event_time))

    session_counters: Dict[str, int] = {}
    last_event_time: Dict[str, datetime] = {}
    current_session: Dict[str, str] = {}
    session_start: Dict[str, datetime] = {}

    enriched: List[SessionizedEvent] = []
    for event in sorted_events:
        previous = last_event_time.get(event.user_id)
        should_start_new = previous is None or (event.event_time - previous) > gap
        if should_start_new:
            index = session_counters.get(event.user_id, 0) + 1
            session_counters[event.user_id] = index
            session_id = f"{event.user_id}-{index}"
            current_session[event.user_id] = session_id
            session_start[session_id] = event.event_time
        else:
            session_id = current_session[event.user_id]
        last_event_time[event.user_id] = event.event_time
        session_id = current_session[event.user_id]
        start = session_start[session_id]
        completion = min(event.watched_seconds / event.video_duration, 1.0)
        enriched.append(
            SessionizedEvent(
                user_id=event.user_id,
                video_id=event.video_id,
                creator_id=event.creator_id,
                event_time=event.event_time,
                watched_seconds=event.watched_seconds,
                video_duration=event.video_duration,
                session_id=session_id,
                session_start=start,
                completion_ratio=completion,
                watch_day=event.event_time.date(),
            )
        )
    return enriched


def aggregate_sessions(
    sessionized_events: Sequence[SessionizedEvent],
) -> List[SessionSummary]:
    """Summarize session-level metrics from sessionized events."""

    if not sessionized_events:
        return []

    sessions: Dict[str, List[SessionizedEvent]] = {}
    for event in sessionized_events:
        sessions.setdefault(event.session_id, []).append(event)

    summaries: List[SessionSummary] = []
    for session_id, events in sessions.items():
        events_sorted = sorted(events, key=lambda event: event.event_time)
        user_id = events_sorted[0].user_id
        session_start = events_sorted[0].session_start
        session_end = events_sorted[-1].event_time
        videos_watched = len({event.video_id for event in events_sorted})
        creators_engaged = len({event.creator_id for event in events_sorted})
        session_watch_seconds = sum(event.watched_seconds for event in events_sorted)
        mean_completion_ratio = (
            sum(event.completion_ratio for event in events_sorted) / len(events_sorted)
        )
        duration_minutes = (session_end - session_start).total_seconds() / 60.0
        summaries.append(
            SessionSummary(
                session_id=session_id,
                user_id=user_id,
                session_start=session_start,
                session_end=session_end,
                videos_watched=videos_watched,
                creators_engaged=creators_engaged,
                session_watch_seconds=session_watch_seconds,
                mean_completion_ratio=mean_completion_ratio,
                session_duration_minutes=duration_minutes,
            )
        )
    summaries.sort(key=lambda summary: (summary.user_id, summary.session_start))
    return summaries


def retention_curve(
    events: Sequence[WatchEvent] | Iterable[Mapping[str, object]],
    days: Sequence[int] = (1, 7, 30),
) -> List[RetentionPoint]:
    """Compute retention rates for specified day offsets relative to first watch."""

    normalized = _ensure_watch_events(events)

    if not normalized:
        return [RetentionPoint(day=day, retention_rate=0.0) for day in days]

    sessionized = sessionize_events(normalized)
    first_watch: Dict[str, date] = {}
    watch_days_by_user: Dict[str, set[date]] = {}
    for event in sessionized:
        watch_days_by_user.setdefault(event.user_id, set()).add(event.watch_day)
        first_watch.setdefault(event.user_id, event.watch_day)
        if event.watch_day < first_watch[event.user_id]:
            first_watch[event.user_id] = event.watch_day

    cohort_size = len(first_watch)
    rates: List[RetentionPoint] = []
    for day in days:
        retained_users = 0
        for user_id, first_day in first_watch.items():
            target_day = first_day + timedelta(days=day)
            if target_day in watch_days_by_user[user_id]:
                retained_users += 1
        rate = retained_users / cohort_size if cohort_size else 0.0
        rates.append(RetentionPoint(day=day, retention_rate=rate))
    return rates


def creator_watch_share(
    events: Sequence[WatchEvent] | Iterable[Mapping[str, object]]
) -> List[CreatorWatchShare]:
    """Share of watch seconds attributed to each creator."""

    normalized = _ensure_watch_events(events)

    if not normalized:
        return []

    totals: Dict[str, float] = {}
    for event in normalized:
        totals[event.creator_id] = totals.get(event.creator_id, 0.0) + event.watched_seconds
    total_watch = sum(totals.values())
    shares = [
        CreatorWatchShare(
            creator_id=creator_id,
            watch_seconds=watch_seconds,
            watch_share=(watch_seconds / total_watch) if total_watch else 0.0,
        )
        for creator_id, watch_seconds in totals.items()
    ]
    shares.sort(key=lambda share: share.watch_seconds, reverse=True)
    return shares


def daily_active_users(
    events: Sequence[WatchEvent] | Iterable[Mapping[str, object]]
) -> List[DailyActiveCount]:
    """Daily active users derived from watch events."""

    normalized = _ensure_watch_events(events)

    if not normalized:
        return []

    active: Dict[date, set[str]] = {}
    for event in normalized:
        day = event.event_time.date()
        active.setdefault(day, set()).add(event.user_id)
    counts = [DailyActiveCount(date=day, active_users=len(users)) for day, users in active.items()]
    counts.sort(key=lambda item: item.date)
    return counts


def as_dicts(records: Iterable[SessionSummary | RetentionPoint | CreatorWatchShare | DailyActiveCount]) -> List[dict]:
    """Serialize dataclass records to dictionaries."""

    return [asdict(record) for record in records]
