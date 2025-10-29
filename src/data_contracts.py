"""Data contracts and schema validation for engagement analytics datasets."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, List

import pandas as pd
from pydantic import BaseModel, Field, ValidationError


class WatchEvent(BaseModel):
    """Canonical schema for user-level watch events."""

    user_id: str
    video_id: str
    creator_id: str
    event_time: datetime
    watched_seconds: float = Field(ge=0)
    video_duration: float = Field(gt=0)


class VideoMetadata(BaseModel):
    """Schema for static video descriptors sourced from YouTube metadata."""

    video_id: str
    creator_id: str
    publish_time: datetime
    category: str


def _records_from_dataframe(df: pd.DataFrame, model: type[BaseModel]) -> List[BaseModel]:
    records: List[BaseModel] = []
    for row in df.itertuples(index=False):
        payload = row._asdict()
        for key, value in payload.items():
            if isinstance(value, pd.Timestamp):
                payload[key] = value.to_pydatetime()
        records.append(model(**payload))
    return records


def load_watch_events(path: str | Path) -> pd.DataFrame:
    """Load and validate watch events from CSV."""

    df = pd.read_csv(path, parse_dates=["event_time"])
    records = _records_from_dataframe(df, WatchEvent)
    return pd.DataFrame([r.dict() for r in records])


def load_video_metadata(path: str | Path) -> pd.DataFrame:
    """Load and validate video metadata from CSV."""

    df = pd.read_csv(path, parse_dates=["publish_time"])
    records = _records_from_dataframe(df, VideoMetadata)
    return pd.DataFrame([r.dict() for r in records])


def validate_payloads(records: Iterable[dict], model: type[BaseModel]) -> None:
    """Raise if any record violates the schema."""

    errors: List[ValidationError] = []
    for payload in records:
        try:
            model(**payload)
        except ValidationError as err:  # pragma: no cover - aggregation is the key path
            errors.append(err)
    if errors:
        message = "\n".join(str(err) for err in errors)
        raise ValidationError(message, model=model)
