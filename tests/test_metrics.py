import pandas as pd

from src import metrics


def sample_events() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "user_id": ["u1", "u2", "u3", "u1"],
            "video_id": ["v1", "v2", "v3", "v2"],
            "creator_id": ["c1", "c2", "c1", "c2"],
            "event_time": pd.to_datetime(
                [
                    "2024-03-01T00:00:00Z",
                    "2024-03-01T00:05:00Z",
                    "2024-03-02T01:00:00Z",
                    "2024-03-07T01:05:00Z",
                ]
            ),
            "watched_seconds": [40, 20, 60, 25],
            "video_duration": [50, 40, 60, 40],
        }
    )


def test_completion_rate_within_bounds():
    rate = metrics.completion_rate(sample_events())
    assert 0.0 <= rate <= 1.0


def test_dau_wau_ratio_computes_counts():
    stats = metrics.dau_wau_ratio(sample_events())
    assert set(stats.keys()) == {"dau", "wau", "ratio"}
    assert stats["wau"] >= stats["dau"]


def test_creator_contribution_returns_top_creators():
    contribution = metrics.creator_contribution(sample_events(), top_n=1)
    assert len(contribution) == 1
    assert "watch_share" in contribution.columns
