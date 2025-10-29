"""Shared utilities for configuration, paths, and sample processing."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import data_contracts, features


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def data_path(*parts: str) -> Path:
    """Return an absolute path to a data artifact inside the repository."""

    return PROJECT_ROOT.joinpath("data", *parts)


def load_watch_events() -> pd.DataFrame:
    """Convenience loader for bundled watch events."""

    return data_contracts.load_watch_events(data_path("raw", "watch_events.csv"))


def load_video_metadata() -> pd.DataFrame:
    """Convenience loader for bundled video metadata."""

    return data_contracts.load_video_metadata(data_path("raw", "video_metadata.csv"))


def build_sample_outputs() -> None:
    """Generate processed datasets from bundled samples."""

    events = load_watch_events()
    sessionized = features.sessionize_events(events)
    sessions = features.aggregate_sessions(sessionized)
    retention = features.retention_curve(events)
    creator_share = features.creator_watch_share(events)

    processed_dir = data_path("processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    sessions.to_csv(processed_dir / "session_summary.csv", index=False)
    retention.to_csv(processed_dir / "retention_curve.csv", index=False)
    creator_share.to_csv(processed_dir / "creator_watch_share.csv", index=False)


def main() -> None:
    """CLI entrypoint for building processed artifacts."""

    build_sample_outputs()
    print("Processed datasets written to", data_path("processed"))


if __name__ == "__main__":  # pragma: no cover - exercised via Makefile
    main()
