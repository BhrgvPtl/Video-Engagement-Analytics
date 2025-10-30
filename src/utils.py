from __future__ import annotations
import os
from pathlib import Path

# Define base data directories
DATA_RAW = Path("data/raw")
DATA_PROC = Path("data/processed")


def ensure_dirs() -> None:
    """Ensure data/raw and data/processed directories exist."""
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROC.mkdir(parents=True, exist_ok=True)


def path_raw(*parts: str) -> str:
    """Return full path inside data/raw."""
    ensure_dirs()
    return str(DATA_RAW.joinpath(*parts))


def path_proc(*parts: str) -> str:
    """Return full path inside data/processed."""
    ensure_dirs()
    return str(DATA_PROC.joinpath(*parts))
