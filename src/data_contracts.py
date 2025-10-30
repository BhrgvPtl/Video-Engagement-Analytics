from __future__ import annotations
<<<<<<< Updated upstream

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Sequence
import csv


@dataclass(frozen=True)
class WatchEvent:
    """Canonical schema for user-level watch events."""
=======
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
>>>>>>> Stashed changes

@dataclass
class WatchEvent:
    user_id: str
    session_id: str
    event_time: datetime
<<<<<<< Updated upstream
    watched_seconds: float
    video_duration: float

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id must be provided")
        if not self.video_id:
            raise ValueError("video_id must be provided")
        if not self.creator_id:
            raise ValueError("creator_id must be provided")
        if self.watched_seconds < 0:
            raise ValueError("watched_seconds must be non-negative")
        if self.video_duration <= 0:
            raise ValueError("video_duration must be positive")


@dataclass(frozen=True)
class VideoMetadata:
    """Schema for static video descriptors sourced from YouTube metadata."""

=======
>>>>>>> Stashed changes
    video_id: str
    watch_seconds: int
    video_length_seconds: int
    completed: bool
    dropoff_position_pct: float  # 0..1

<<<<<<< Updated upstream
    def __post_init__(self) -> None:
        if not self.video_id:
            raise ValueError("video_id must be provided")
        if not self.creator_id:
            raise ValueError("creator_id must be provided")
        if not self.category:
            raise ValueError("category must be provided")


def _parse_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def _coerce_float(value: str) -> float:
    try:
        return float(value)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Could not parse numeric value: {value!r}") from exc


def _load_csv(path: str | Path) -> Iterable[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield row


def load_watch_events(path: str | Path) -> List[WatchEvent]:
    """Load and validate watch events from CSV."""

    records: List[WatchEvent] = []
    for row in _load_csv(path):
        record = WatchEvent(
            user_id=row["user_id"],
            video_id=row["video_id"],
            creator_id=row["creator_id"],
            event_time=_parse_datetime(row["event_time"]),
            watched_seconds=_coerce_float(row["watched_seconds"]),
            video_duration=_coerce_float(row["video_duration"]),
        )
        records.append(record)
    return records


def load_video_metadata(path: str | Path) -> List[VideoMetadata]:
    """Load and validate video metadata from CSV."""

    records: List[VideoMetadata] = []
    for row in _load_csv(path):
        record = VideoMetadata(
            video_id=row["video_id"],
            creator_id=row["creator_id"],
            publish_time=_parse_datetime(row["publish_time"]),
            category=row["category"],
        )
        records.append(record)
    return records


def validate_payloads(records: Iterable[dict], model: type[WatchEvent | VideoMetadata]) -> None:
    """Raise if any record violates the schema."""

    errors: List[str] = []
    for index, payload in enumerate(records):
        try:
            model(**payload)
        except Exception as exc:  # pragma: no cover - validation errors aggregated
            errors.append(f"Row {index}: {exc}")
    if errors:
        message = "\n".join(errors)
        raise ValueError(message)


def events_from_dicts(records: Sequence[dict[str, object]]) -> List[WatchEvent]:
    """Convert dictionaries to validated watch events."""

    return [
        WatchEvent(
            user_id=str(record["user_id"]),
            video_id=str(record["video_id"]),
            creator_id=str(record["creator_id"]),
            event_time=record["event_time"] if isinstance(record["event_time"], datetime) else _parse_datetime(str(record["event_time"])),
            watched_seconds=float(record["watched_seconds"]),
            video_duration=float(record["video_duration"]),
        )
        for record in records
    ]
=======
@dataclass
class SessionFeature:
    session_id: str
    user_id: str
    session_start: datetime
    session_end: datetime
    session_duration_seconds: int
    videos_watched: int
    avg_watch_pct: float
    completion_rate: float
    creator_watch_share_top: Optional[str] = None  # optional enrichment
>>>>>>> Stashed changes
