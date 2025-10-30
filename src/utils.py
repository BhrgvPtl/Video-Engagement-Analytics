from __future__ import annotations
import os
from pathlib import Path
<<<<<<< Updated upstream
from typing import Iterable, Sequence
import csv

from . import data_contracts, features
from .data_contracts import WatchEvent
=======

DATA_RAW = Path("data/raw")
DATA_PROC = Path("data/processed")

def ensure_dirs():
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROC.mkdir(parents=True, exist_ok=True)
>>>>>>> Stashed changes

def path_raw(*parts) -> str:
    ensure_dirs()
    return str(DATA_RAW.joinpath(*parts))

<<<<<<< Updated upstream
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def data_path(*parts: str) -> Path:
    """Return an absolute path to a data artifact inside the repository."""

    return PROJECT_ROOT.joinpath("data", *parts)


def load_watch_events() -> Sequence[WatchEvent]:
    """Convenience loader for bundled watch events."""

    return data_contracts.load_watch_events(data_path("raw", "watch_events.csv"))


def load_video_metadata() -> Sequence[data_contracts.VideoMetadata]:
    """Convenience loader for bundled video metadata."""

    return data_contracts.load_video_metadata(data_path("raw", "video_metadata.csv"))


def _write_records(path: Path, records: Iterable[dict]) -> None:
    if not records:
        path.write_text("", encoding="utf-8")
        return

    records = list(records)
    fieldnames = list(records[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def build_sample_outputs() -> None:
    """Generate processed datasets from bundled samples."""

    events = load_watch_events()
    sessionized = features.sessionize_events(events)
    sessions = features.aggregate_sessions(sessionized)
    retention = features.retention_curve(events)
    creator_share = features.creator_watch_share(events)

    processed_dir = data_path("processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    _write_records(processed_dir / "session_summary.csv", features.as_dicts(sessions))
    _write_records(processed_dir / "retention_curve.csv", features.as_dicts(retention))
    _write_records(processed_dir / "creator_watch_share.csv", features.as_dicts(creator_share))


def main() -> None:
    """CLI entrypoint for building processed artifacts."""

    build_sample_outputs()
    print("Processed datasets written to", data_path("processed"))


if __name__ == "__main__":  # pragma: no cover - exercised via Makefile
    main()
=======
def path_proc(*parts) -> str:
    ensure_dirs()
    return str(DATA_PROC.joinpath(*parts))
>>>>>>> Stashed changes
