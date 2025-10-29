import pandas as pd

from src import features


def sample_events() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "user_id": ["u1", "u1", "u2", "u2"],
            "video_id": ["v1", "v2", "v3", "v3"],
            "creator_id": ["c1", "c2", "c1", "c1"],
            "event_time": pd.to_datetime(
                [
                    "2024-03-01T00:00:00Z",
                    "2024-03-01T00:20:00Z",
                    "2024-03-01T01:00:00Z",
                    "2024-03-02T01:05:00Z",
                ]
            ),
            "watched_seconds": [40, 50, 30, 45],
            "video_duration": [60, 60, 45, 45],
        }
    )


def test_sessionize_events_assigns_unique_sessions():
    events = sample_events()
    sessionized = features.sessionize_events(events, session_gap_minutes=15)
    assert sessionized["session_id"].nunique() == 3
    assert sessionized.loc[sessionized["user_id"] == "u1", "session_id"].nunique() == 1


def test_retention_curve_returns_expected_days():
    events = sample_events()
    curve = features.retention_curve(events, days=(1, 7))
    assert list(curve["day"]) == [1, 7]
    assert 0.0 <= curve.loc[curve["day"] == 1, "retention_rate"].iloc[0] <= 1.0


def test_creator_watch_share_normalizes_totals():
    events = sample_events()
    share = features.creator_watch_share(events)
    assert abs(share["watch_share"].sum() - 1.0) < 1e-6
